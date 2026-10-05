"""
Deterministic Tax Calculator for myCA.
Executes cent-exact Decimal computations based on versioned statutory rules.
Zero float inaccuracies. AI does NOT calculate taxes.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from .tax_registry import get_statutory_rule, get_current_rules_for_ay
from .models import TaxCalculationResult, TaxSlabBreakdown

def to_decimal(val: Any) -> Decimal:
    if val is None:
        return Decimal('0.00')
    if isinstance(val, Decimal):
        return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_new_regime_tax(
    gross_income: Any,
    assessment_year: str = "2025-26"
) -> TaxCalculationResult:
    """
    Computes tax under Section 115BAC (New Regime) using exact statutory parameters.
    Default: AY 2025-26 (The Finance (No. 2) Act, 2024).
    """
    gross_dec = to_decimal(gross_income)
    
    # Retrieve authoritative rule
    rule_id = "rule_sec_115bac_ay25_26" if assessment_year == "2025-26" else "rule_sec_115bac_ay24_25"
    rule = get_statutory_rule(rule_id)
    if not rule:
        raise ValueError(f"No verified statutory rule found for AY {assessment_year}")

    rule_data = rule["rule_data"]
    std_ded_dec = to_decimal(rule_data.get("standard_deduction", 75000.0))
    rebate_limit_dec = to_decimal(rule_data.get("section_87a_rebate_limit", 700000.0))
    max_rebate_dec = to_decimal(rule_data.get("section_87a_max_rebate", 25000.0))
    cess_pct = to_decimal(rule_data.get("cess_percent", 4.0))

    # Standard Deduction
    taxable_income = max(Decimal('0.00'), gross_dec - std_ded_dec)

    # Evaluate slabs
    slabs_config = rule_data["slabs"]
    slab_breakdowns: List[TaxSlabBreakdown] = []
    total_slab_tax = Decimal('0.00')

    for s in slabs_config:
        s_min = to_decimal(s["min"])
        s_max = to_decimal(s["max"]) if s["max"] is not None else None
        rate = to_decimal(s["rate_percent"])

        if taxable_income <= s_min:
            continue

        if s_max is None:
            taxable_in_slab = taxable_income - s_min
            slab_label = f"Above ₹{int(s_min):,}"
        else:
            taxable_in_slab = min(taxable_income, s_max) - s_min
            slab_label = f"₹{int(s_min):,} - ₹{int(s_max):,}"

        tax_for_slab = (taxable_in_slab * (rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_slab_tax += tax_for_slab

        slab_breakdowns.append(TaxSlabBreakdown(
            slab_range=slab_label,
            taxable_amount=taxable_in_slab,
            rate_percent=rate,
            tax_amount=tax_for_slab
        ))

    # Section 87A Rebate
    # In New Regime, if taxable income <= 7 Lakhs, tax payable is reduced to zero (up to max rebate)
    rebate_87a = Decimal('0.00')
    if taxable_income <= rebate_limit_dec:
        rebate_87a = min(total_slab_tax, max_rebate_dec)

    tax_after_rebate = max(Decimal('0.00'), total_slab_tax - rebate_87a)

    # 4% Health & Education Cess
    cess_amt = (tax_after_rebate * (cess_pct / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_tax_payable = tax_after_rebate + cess_amt

    effective_rate = Decimal('0.00')
    if gross_dec > Decimal('0.00'):
        effective_rate = ((total_tax_payable / gross_dec) * Decimal('100.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return TaxCalculationResult(
        assessment_year=assessment_year,
        regime="NEW_TAX_REGIME_115BAC",
        gross_income=gross_dec,
        standard_deduction=std_ded_dec,
        deductions_80c=Decimal('0.00'),
        deductions_80d=Decimal('0.00'),
        total_deductions=std_ded_dec,
        taxable_income=taxable_income,
        slab_tax=total_slab_tax,
        rebate_87a=rebate_87a,
        tax_after_rebate=tax_after_rebate,
        cess_4_percent=cess_amt,
        total_tax_payable=total_tax_payable,
        effective_rate_percent=effective_rate,
        slabs_applied=slab_breakdowns,
        rule_reference=f"Section 115BAC, {rule['official_source_reference']}",
        disclaimer="Deterministic statutory calculation under Section 115BAC(1A). Surcharge for income > ₹50L not included."
    )

def calculate_old_regime_tax(
    gross_income: Any,
    deductions_80c: Any = 0,
    deductions_80d: Any = 0,
    home_loan_interest: Any = 0,
    assessment_year: str = "2025-26"
) -> TaxCalculationResult:
    """
    Computes tax under Old Tax Regime with standard deduction (₹50,000) and statutory chapter VI-A deductions.
    Section 80C capped at ₹1,50,000.
    Section 80D capped at ₹25,000 (self/family).
    Section 24(b) capped at ₹2,00,000.
    """
    gross_dec = to_decimal(gross_income)
    std_ded_dec = Decimal('50000.00')

    # Apply statutory deduction ceilings
    c_dec = min(to_decimal(deductions_80c), Decimal('150000.00'))
    d_dec = min(to_decimal(deductions_80d), Decimal('25000.00'))
    hl_dec = min(to_decimal(home_loan_interest), Decimal('200000.00'))

    total_deductions = std_ded_dec + c_dec + d_dec + hl_dec
    taxable_income = max(Decimal('0.00'), gross_dec - total_deductions)

    # Old Regime Slabs for Individuals (<60 yrs):
    # 0 - 2,50,000 : 0%
    # 2,50,000 - 5,00,000 : 5%
    # 5,00,000 - 10,00,000 : 20%
    # Above 10,00,000 : 30%
    slabs_config = [
        {"min": 0, "max": 250000, "rate_percent": 0},
        {"min": 250000, "max": 500000, "rate_percent": 5},
        {"min": 500000, "max": 1000000, "rate_percent": 20},
        {"min": 1000000, "max": None, "rate_percent": 30}
    ]

    slab_breakdowns: List[TaxSlabBreakdown] = []
    total_slab_tax = Decimal('0.00')

    for s in slabs_config:
        s_min = to_decimal(s["min"])
        s_max = to_decimal(s["max"]) if s["max"] is not None else None
        rate = to_decimal(s["rate_percent"])

        if taxable_income <= s_min:
            continue

        if s_max is None:
            taxable_in_slab = taxable_income - s_min
            slab_label = f"Above ₹{int(s_min):,}"
        else:
            taxable_in_slab = min(taxable_income, s_max) - s_min
            slab_label = f"₹{int(s_min):,} - ₹{int(s_max):,}"

        tax_for_slab = (taxable_in_slab * (rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_slab_tax += tax_for_slab

        slab_breakdowns.append(TaxSlabBreakdown(
            slab_range=slab_label,
            taxable_amount=taxable_in_slab,
            rate_percent=rate,
            tax_amount=tax_for_slab
        ))

    # Old Regime 87A rebate: if taxable income <= 5,00,000, max rebate = 12,500
    rebate_87a = Decimal('0.00')
    if taxable_income <= Decimal('500000.00'):
        rebate_87a = min(total_slab_tax, Decimal('12500.00'))

    tax_after_rebate = max(Decimal('0.00'), total_slab_tax - rebate_87a)
    cess_amt = (tax_after_rebate * Decimal('0.04')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_tax_payable = tax_after_rebate + cess_amt

    effective_rate = Decimal('0.00')
    if gross_dec > Decimal('0.00'):
        effective_rate = ((total_tax_payable / gross_dec) * Decimal('100.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return TaxCalculationResult(
        assessment_year=assessment_year,
        regime="OLD_TAX_REGIME",
        gross_income=gross_dec,
        standard_deduction=std_ded_dec,
        deductions_80c=c_dec,
        deductions_80d=d_dec,
        total_deductions=total_deductions,
        taxable_income=taxable_income,
        slab_tax=total_slab_tax,
        rebate_87a=rebate_87a,
        tax_after_rebate=tax_after_rebate,
        cess_4_percent=cess_amt,
        total_tax_payable=total_tax_payable,
        effective_rate_percent=effective_rate,
        slabs_applied=slab_breakdowns,
        rule_reference="Income Tax Act, 1961 Section 80C, Section 80D, Section 24(b)",
        disclaimer="Deterministic calculation under Old Tax Regime with standard deductions."
    )
