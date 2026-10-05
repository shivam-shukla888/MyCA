"""
myCA Phase 5 Test Suite: Versioned Statutory Knowledge Registry & Deterministic Tax Engine.
Verifies:
- Official legislative source provenance
- Versioning and supersession links (AY 2024-25 -> AY 2025-26)
- Effective date filtering
- NOT_VERIFIED status exclusion
- Ingestion validation guard (rejecting rules without official citations)
- Exact Decimal tax calculations under Section 115BAC (AY 2025-26 slabs and standard deduction)
- Section 87A tax rebate under New and Old regimes
"""

import unittest
from decimal import Decimal
from app.db import init_db, get_db
from app.knowledge.models import RuleStatus
from app.knowledge.tax_registry import (
    seed_statutory_rules,
    get_statutory_rule,
    get_current_rules_for_ay,
    search_rules,
    ingest_verified_rule
)
from app.knowledge.tax_calculator import (
    calculate_new_regime_tax,
    calculate_old_regime_tax
)

class TestKnowledgeRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_statutory_rules()

    def test_01_statutory_rules_seeded_with_official_provenance(self):
        """Official tax rules must have valid publication dates, gazette citations, and legislative references."""
        rule = get_statutory_rule("rule_sec_115bac_ay25_26")
        self.assertIsNotNone(rule)
        self.assertEqual(rule["status"], "CURRENT")
        self.assertEqual(rule["assessment_year"], "2025-26")
        self.assertEqual(rule["financial_year"], "2024-25")
        self.assertIn("The Finance (No. 2) Act, 2024", rule["official_source_reference"])
        self.assertEqual(rule["publication_date"], "2024-08-16")
        self.assertEqual(rule["rule_data"]["standard_deduction"], 75000.0)

    def test_02_supersession_links_preserved(self):
        """AY 2024-25 rule must be marked SUPERSEDED and link to AY 2025-26 rule."""
        rule_old = get_statutory_rule("rule_sec_115bac_ay24_25")
        self.assertIsNotNone(rule_old)
        self.assertEqual(rule_old["status"], "SUPERSEDED")
        self.assertEqual(rule_old["superseded_by"], "rule_sec_115bac_ay25_26")

        rule_new = get_statutory_rule("rule_sec_115bac_ay25_26")
        self.assertEqual(rule_new["supersedes"], "rule_sec_115bac_ay24_25")

    def test_03_get_current_rules_filters_out_superseded_and_unverified(self):
        """get_current_rules_for_ay must only return CURRENT rules, excluding SUPERSEDED and NOT_VERIFIED."""
        rules_25 = get_current_rules_for_ay("2025-26")
        ids = [r["id"] for r in rules_25]
        self.assertIn("rule_sec_115bac_ay25_26", ids)
        self.assertNotIn("rule_sec_115bac_ay24_25", ids)  # Superseded
        self.assertNotIn("rule_draft_unverified_reform", ids)  # Not verified

        for r in rules_25:
            self.assertEqual(r["status"], "CURRENT")

    def test_04_not_verified_rule_quarantined_from_standard_search(self):
        """Rules marked NOT_VERIFIED must never be returned by default rule queries."""
        active_rules = search_rules()
        for r in active_rules:
            self.assertNotEqual(r["status"], "NOT_VERIFIED")

        # Explicit search for unverified rules
        unverified = search_rules(status="NOT_VERIFIED")
        self.assertTrue(any(r["id"] == "rule_draft_unverified_reform" for r in unverified))

    def test_05_ingest_verified_rule_rejects_missing_official_citation(self):
        """Ingestion guard must reject rules lacking legislative authority or mark them NOT_VERIFIED."""
        # Missing required field
        with self.assertRaises(ValueError):
            ingest_verified_rule({
                "id": "invalid_rule_01",
                "source": "Internet Blog"
            })

        # Rule without official legislative reference is forced to NOT_VERIFIED
        res = ingest_verified_rule({
            "id": "rule_blog_claim_10l",
            "source": "Financial Blog",
            "official_source_reference": "Blog post on taxes",
            "publication_date": "2026-10-01",
            "effective_from": "2026-04-01",
            "provision": "Claimed 0% tax",
            "status": "CURRENT",
            "rule_data": {"tax": 0}
        })
        self.assertEqual(res["status"], "NOT_VERIFIED")

        saved = get_statutory_rule("rule_blog_claim_10l")
        self.assertEqual(saved["status"], "NOT_VERIFIED")

    def test_06_new_regime_tax_calculation_ay25_26_exact_math(self):
        """Test exact calculation of New Tax Regime for AY 2025-26 with enhanced standard deduction (₹75k)."""
        # Income = ₹12,00,000
        # Std Deduction = ₹75,000 -> Taxable = ₹11,25,000
        # 0-3L: 0
        # 3-7L (4L @ 5%): 20,000
        # 7-10L (3L @ 10%): 30,000
        # 10-11.25L (1.25L @ 15%): 18,750
        # Total Slab Tax = 68,750
        # 4% Cess = 2,750
        # Total Tax Payable = 71,500.00
        res = calculate_new_regime_tax(1200000.0, assessment_year="2025-26")
        self.assertEqual(res.gross_income, Decimal('1200000.00'))
        self.assertEqual(res.standard_deduction, Decimal('75000.00'))
        self.assertEqual(res.taxable_income, Decimal('1125000.00'))
        self.assertEqual(res.slab_tax, Decimal('68750.00'))
        self.assertEqual(res.rebate_87a, Decimal('0.00'))
        self.assertEqual(res.cess_4_percent, Decimal('2750.00'))
        self.assertEqual(res.total_tax_payable, Decimal('71500.00'))

    def test_07_new_regime_section_87a_full_rebate(self):
        """Income up to ₹7,75,000 under AY 2025-26 has ₹0 net tax after Section 87A rebate."""
        # Gross = ₹7,75,000 -> Std Ded = ₹75,000 -> Taxable = ₹7,00,000
        # Slab Tax on 7L = 20,000
        # Rebate u/s 87A = 20,000
        # Net Tax Payable = 0.00
        res = calculate_new_regime_tax(775000.0, assessment_year="2025-26")
        self.assertEqual(res.taxable_income, Decimal('700000.00'))
        self.assertEqual(res.slab_tax, Decimal('20000.00'))
        self.assertEqual(res.rebate_87a, Decimal('20000.00'))
        self.assertEqual(res.total_tax_payable, Decimal('0.00'))

    def test_08_superseded_ay24_25_calculation_differs_from_ay25_26(self):
        """Verify calculations for AY 2024-25 use historical slabs (₹50k std ded)."""
        # AY 2024-25 on 12L:
        # Gross 12L - Std Ded 50k = Taxable 11.5L
        # Slab Tax = 82,500 + 4% cess (3,300) = 85,800.00
        res_24 = calculate_new_regime_tax(1200000.0, assessment_year="2024-25")
        self.assertEqual(res_24.standard_deduction, Decimal('50000.00'))
        self.assertEqual(res_24.total_tax_payable, Decimal('85800.00'))

        res_25 = calculate_new_regime_tax(1200000.0, assessment_year="2025-26")
        self.assertEqual(res_25.total_tax_payable, Decimal('71500.00'))
        # Tax benefit in AY 2025-26 is ₹14,300
        self.assertEqual(res_24.total_tax_payable - res_25.total_tax_payable, Decimal('14300.00'))

    def test_09_old_regime_statutory_deduction_caps(self):
        """Test Old Regime caps 80C at ₹1,50,000 and 80D at ₹25,000."""
        # User claims 2,50,000 in 80C and 40,000 in 80D
        res = calculate_old_regime_tax(
            gross_income=1200000.0,
            deductions_80c=250000.0,
            deductions_80d=40000.0
        )
        self.assertEqual(res.deductions_80c, Decimal('150000.00'))
        self.assertEqual(res.deductions_80d, Decimal('25000.00'))
        self.assertEqual(res.standard_deduction, Decimal('50000.00'))
        # Total Deductions: 50k + 150k + 25k = 225,000 -> Taxable = 975,000
        self.assertEqual(res.taxable_income, Decimal('975000.00'))

    def test_10_effective_date_boundary_filtering(self):
        """Verify rules can be queried by valid effective date."""
        rules = search_rules(effective_date="2024-10-01")
        rule_ids = [r["id"] for r in rules]
        self.assertIn("rule_sec_115bac_ay25_26", rule_ids)
        self.assertNotIn("rule_sec_115bac_ay24_25", rule_ids)

if __name__ == "__main__":
    unittest.main()
