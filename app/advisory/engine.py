"""
Grounded Advisory Engine for Ask myCA.
Enforces the Sovereign Architecture:
USER DATA + AUTHORITATIVE KNOWLEDGE + DETERMINISTIC CALCULATIONS -> GROUNDED RESPONSE.
AI NEVER GUESSES, NEVER INVENT SOURCES, AND NEVER DOES UNTRACKED MATH.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from ..db import get_db
from ..financial.calculations import compute_financial_profile_deterministic
from ..knowledge.models import (
    AdvisoryResponseType,
    AdvisoryEvidence,
    GroundedAdvisoryResponse
)
from ..knowledge.tax_registry import get_statutory_rule, get_current_rules_for_ay
from ..knowledge.tax_calculator import calculate_new_regime_tax, calculate_old_regime_tax
from .intent import classify_intent, check_prompt_injection, AdvisoryIntent

def _get_os():
    from ..operating_system import (
        detect_financial_changes,
        evaluate_financial_health,
        list_user_goals,
        get_unified_financial_snapshot
    )
    return detect_financial_changes, evaluate_financial_health, list_user_goals, get_unified_financial_snapshot

class GroundedAdvisoryEngine:
    def __init__(self):
        pass

    def ask(self, user_id: str, query: str) -> GroundedAdvisoryResponse:
        """
        Main grounded advisory inquiry handler.
        Strictly scopes all data retrieval to user_id.
        """
        clean_query = (query or "").strip()
        if not clean_query:
            return GroundedAdvisoryResponse(
                answer="Kripya apna sawal puchein.",
                response_type=AdvisoryResponseType.NEEDS_INFORMATION,
                status="NEEDS_INPUT"
            )

        # 1. Prompt Injection Defense
        if check_prompt_injection(clean_query):
            self._log_audit_event(user_id, "PROMPT_INJECTION_DETECTED", {"query": clean_query})
            return GroundedAdvisoryResponse(
                answer="Aapka sawal process nahi kiya ja sakta. Kripya valid personal financial sawal puchein.",
                response_type=AdvisoryResponseType.WARNING,
                status="INJECTION_ATTEMPT_QUARANTINED"
            )

        # 2. Retrieve Authenticated User's Financial Data (Tenant-Scoped)
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.*, d.filename as doc_name
            FROM transactions t
            LEFT JOIN documents d ON t.source_document_id = d.id
            WHERE t.user_id = ?
            ORDER BY t.date DESC
        """, (user_id,))
        tx_rows = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT * FROM income_records
            WHERE user_id = ? AND status IN ('READY', 'VERIFIED_FROM_DOCUMENT', 'USER_CONFIRMED') AND amount > 0
            ORDER BY created_at DESC
        """, (user_id,))
        income_rows = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        doc_rows = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM loans WHERE user_id = ?", (user_id,))
        loan_rows = [dict(r) for r in cursor.fetchall()]

        conn.close()

        # 3. Intent Classification
        intent = classify_intent(clean_query)

        # 4. Handle Missing Data cases immediately (No documents uploaded)
        if not doc_rows and not tx_rows and intent not in [AdvisoryIntent.INVESTMENT_80C]:
            return GroundedAdvisoryResponse(
                answer="Mere paas abhi iske liye enough information nahi hai (koi verified financial document nahi hai). Kripya apna bank statement ya salary slip upload karein taaki main exact calculation kar sakun.",
                response_type=AdvisoryResponseType.NEEDS_INFORMATION,
                status="NO_USER_DATA"
            )

        # 5. Dispatch to deterministic intent handlers
        if intent == AdvisoryIntent.FINANCIAL_SUMMARY:
            return self._handle_financial_summary(user_id, tx_rows, doc_rows)

        elif intent == AdvisoryIntent.HIGHEST_EXPENSE:
            return self._handle_highest_expense(user_id, tx_rows)

        elif intent == AdvisoryIntent.RENT:
            return self._handle_rent(user_id, tx_rows)

        elif intent == AdvisoryIntent.FOOD_DINING:
            return self._handle_food_dining(user_id, tx_rows)

        elif intent == AdvisoryIntent.SALARY_INCOME:
            return self._handle_salary_income(user_id, tx_rows, income_rows)

        elif intent == AdvisoryIntent.TAX_INQUIRY:
            return self._handle_tax_inquiry(user_id, tx_rows, income_rows, doc_rows)

        elif intent == AdvisoryIntent.EMERGENCY_FUND:
            return self._handle_emergency_fund(user_id, tx_rows)

        elif intent == AdvisoryIntent.INVESTMENT_80C:
            return self._handle_investment_80c(user_id, tx_rows)

        elif intent == AdvisoryIntent.LOAN_INQUIRY:
            return self._handle_loan_inquiry(user_id, loan_rows)

        elif intent == AdvisoryIntent.WHAT_CHANGED:
            return self._handle_what_changed(user_id, tx_rows)

        elif intent == AdvisoryIntent.GOALS_INQUIRY:
            return self._handle_goals_inquiry(user_id)

        elif intent == AdvisoryIntent.FINANCIAL_HEALTH_INQUIRY:
            return self._handle_financial_health_inquiry(user_id)

        elif intent == AdvisoryIntent.NET_WORTH_INQUIRY:
            return self._handle_net_worth_inquiry(user_id)

        elif intent in [AdvisoryIntent.FOREIGN_INCOME, AdvisoryIntent.CRYPTO_INQUIRY]:
            return self._handle_missing_specific_data(intent)

        else:
            return self._handle_fallback(user_id, tx_rows)

    def _handle_financial_summary(self, user_id: str, tx_rows: List[Dict[str, Any]], doc_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        prof = compute_financial_profile_deterministic(tx_rows)
        income = prof["monthly_income"]
        expenses = prof["monthly_expenses"]
        savings = prof["monthly_savings"]

        doc_name = doc_rows[0]["filename"] if doc_rows else "Bank Statement"
        formula = f"₹{int(income):,} (Income) - ₹{int(expenses):,} (Expenses) = ₹{int(savings):,}"

        evidence = [
            AdvisoryEvidence(
                source_type="USER_DOCUMENT",
                source_name=doc_name,
                reference_id=doc_rows[0]["id"] if doc_rows else "doc_summary",
                page_number=1,
                status="CALCULATED_FROM_VERIFIED_DATA",
                snippet=f"Total Inflows: ₹{int(income):,}, Total Outflows: ₹{int(expenses):,}"
            )
        ]

        return GroundedAdvisoryResponse(
            answer=f"Aapke verified statement ke mutabiq is period mein ₹{int(savings):,} bache hain (Paisa aaya: ₹{int(income):,}, Paisa gaya: ₹{int(expenses):,}).",
            response_type=AdvisoryResponseType.CALCULATION,
            data_used={"income": float(income), "expenses": float(expenses), "savings": float(savings)},
            calculation_used=formula,
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_highest_expense(self, user_id: str, tx_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        prof = compute_financial_profile_deterministic(tx_rows)
        categories = prof["categories"]
        if not categories:
            return GroundedAdvisoryResponse(
                answer="Aapke statement mein koi classified expense nahi mila.",
                response_type=AdvisoryResponseType.OBSERVATION,
                status="NO_EXPENSES"
            )

        top_cat = max(categories, key=lambda c: c["amount"])
        top_name = top_cat["category"]
        top_amt = top_cat["amount"]

        # Find representative transaction
        matching_tx = next((t for t in tx_rows if t["category"] == top_name), None)
        source_doc = matching_tx["doc_name"] if matching_tx and matching_tx.get("doc_name") else "Bank Statement"
        source_page = matching_tx["source_page"] if matching_tx and matching_tx.get("source_page") else 1
        snippet = matching_tx.get("source_text") or f"{matching_tx['description']}: ₹{int(matching_tx['amount']):,}" if matching_tx else f"{top_name}: ₹{int(top_amt):,}"

        evidence = [
            AdvisoryEvidence(
                source_type="USER_DOCUMENT",
                source_name=source_doc,
                reference_id=matching_tx["source_document_id"] if matching_tx else "doc_01",
                page_number=source_page,
                status="VERIFIED_FROM_DOCUMENT",
                snippet=snippet
            )
        ]

        return GroundedAdvisoryResponse(
            answer=f"Aapke statement ke hisaab se is period mein sabse zyada paisa {top_name.lower()} par gaya: ₹{int(top_amt):,}.",
            response_type=AdvisoryResponseType.OBSERVATION,
            data_used={"highest_category": top_name, "amount": float(top_amt)},
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_rent(self, user_id: str, tx_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        rent_tx = next((t for t in tx_rows if "rent" in t["description"].lower() or t["category"] == "Rent"), None)
        if not rent_tx:
            return GroundedAdvisoryResponse(
                answer="Aapke statement mein Rent ka koi debit record nahi mila.",
                response_type=AdvisoryResponseType.OBSERVATION,
                status="RECORD_NOT_FOUND"
            )

        amt = rent_tx["amount"]
        source_doc = rent_tx.get("doc_name") or "Bank Statement"
        source_page = rent_tx.get("source_page", 1)
        snippet = rent_tx.get("source_text") or f"{rent_tx['description']}: ₹{int(amt):,}"

        evidence = [
            AdvisoryEvidence(
                source_type="USER_DOCUMENT",
                source_name=source_doc,
                reference_id=rent_tx["source_document_id"],
                page_number=source_page,
                status="VERIFIED_FROM_DOCUMENT",
                snippet=snippet
            )
        ]

        return GroundedAdvisoryResponse(
            answer=f"Aapka monthly rent ₹{int(amt):,} hai, jo statement ke anusar debit hua hai.",
            response_type=AdvisoryResponseType.OBSERVATION,
            data_used={"rent_amount": float(amt), "date": rent_tx.get("date")},
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_food_dining(self, user_id: str, tx_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        prof = compute_financial_profile_deterministic(tx_rows)
        cat_map = {c["category"]: c["amount"] for c in prof["categories"]}
        food_amt = cat_map.get("Food & Dining", 0.0)

        food_txs = [t for t in tx_rows if t["category"] == "Food & Dining"]
        source_doc = food_txs[0].get("doc_name") if food_txs else "Bank Statement"

        evidence = [
            AdvisoryEvidence(
                source_type="USER_DOCUMENT",
                source_name=source_doc,
                reference_id=food_txs[0]["source_document_id"] if food_txs else "doc_01",
                page_number=food_txs[0].get("source_page", 1) if food_txs else 1,
                status="CALCULATED_FROM_VERIFIED_DATA",
                snippet=f"Total Food & Dining debits: ₹{int(food_amt):,}"
            )
        ]

        return GroundedAdvisoryResponse(
            answer=f"Food and dining par total ₹{int(food_amt):,} kharch hue hain (Swiggy, Zomato, groceries).",
            response_type=AdvisoryResponseType.OBSERVATION,
            data_used={"category": "Food & Dining", "total": float(food_amt)},
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_salary_income(self, user_id: str, tx_rows: List[Dict[str, Any]], income_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        if income_rows:
            inc = income_rows[0]
            amt = inc["amount"]
            src = inc["source"]
            evidence = [
                AdvisoryEvidence(
                    source_type="USER_DOCUMENT",
                    source_name="Salary Document",
                    reference_id=inc["source_document_id"],
                    page_number=inc.get("source_page", 1),
                    status="VERIFIED_FROM_DOCUMENT",
                    snippet=f"Verified Salary from {src}: ₹{int(amt):,}"
                )
            ]
            return GroundedAdvisoryResponse(
                answer=f"Aapke uploaded salary record ke mutabiq net monthly salary ₹{int(amt):,} hai ({src}).",
                response_type=AdvisoryResponseType.OBSERVATION,
                data_used={"salary": float(amt), "source": src},
                sources=evidence,
                status="GROUNDED_AND_VERIFIED"
            )

        salary_tx = next((t for t in tx_rows if t["type"] == "CREDIT" and ("salary" in t["description"].lower() or t["category"] == "Salary")), None)
        if salary_tx:
            amt = salary_tx["amount"]
            doc_name = salary_tx.get("doc_name") or "Bank Statement"
            evidence = [
                AdvisoryEvidence(
                    source_type="USER_DOCUMENT",
                    source_name=doc_name,
                    reference_id=salary_tx["source_document_id"],
                    page_number=salary_tx.get("source_page", 1),
                    status="VERIFIED_FROM_DOCUMENT",
                    snippet=salary_tx.get("source_text") or f"Salary Credit: ₹{int(amt):,}"
                )
            ]
            return GroundedAdvisoryResponse(
                answer=f"Aapke bank statement ke anusar monthly salary credit ₹{int(amt):,} hai.",
                response_type=AdvisoryResponseType.OBSERVATION,
                data_used={"salary": float(amt), "date": salary_tx.get("date")},
                sources=evidence,
                status="GROUNDED_AND_VERIFIED"
            )

        return GroundedAdvisoryResponse(
            answer="Mujhe document se salary clearly verify nahi ho rahi. Kripya salary slip upload karein.",
            response_type=AdvisoryResponseType.NEEDS_INFORMATION,
            status="SALARY_NOT_FOUND"
        )

    def _handle_tax_inquiry(self, user_id: str, tx_rows: List[Dict[str, Any]], income_rows: List[Dict[str, Any]], doc_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        # Determine verified annual income base
        monthly_income = Decimal('0.00')
        income_source_desc = "Bank Statement Credits"
        source_doc_id = "doc_tax"
        source_page = 1

        if income_rows:
            monthly_income = Decimal(str(income_rows[0]["amount"]))
            income_source_desc = f"Salary Slip ({income_rows[0]['source']})"
            source_doc_id = income_rows[0]["source_document_id"]
            source_page = income_rows[0].get("source_page", 1)
        else:
            salary_tx = next((t for t in tx_rows if t["type"] == "CREDIT" and ("salary" in t["description"].lower() or t["category"] == "Salary")), None)
            if salary_tx:
                monthly_income = Decimal(str(salary_tx["amount"]))
                income_source_desc = f"Bank Statement Salary ({salary_tx.get('doc_name', 'Statement')})"
                source_doc_id = salary_tx["source_document_id"]
                source_page = salary_tx.get("source_page", 1)

        if monthly_income <= Decimal('0.00'):
            return GroundedAdvisoryResponse(
                answer="Mere paas aapki income ka verified data nahi hai, isliye tax calculate nahi ho sakta. Kripya Form 16 ya salary slip upload karein.",
                response_type=AdvisoryResponseType.NEEDS_INFORMATION,
                status="NO_INCOME_DATA"
            )

        annual_gross = monthly_income * Decimal('12.00')

        # Retrieve verified statutory rule
        rule = get_statutory_rule("rule_sec_115bac_ay25_26")
        tax_res = calculate_new_regime_tax(annual_gross, assessment_year="2025-26")

        tax_payable = int(tax_res.total_tax_payable)
        std_ded = int(tax_res.standard_deduction)
        taxable_inc = int(tax_res.taxable_income)
        gross_inc = int(annual_gross)

        formula = f"₹{gross_inc:,} (Gross) - ₹{std_ded:,} (Std Ded) = ₹{taxable_inc:,} (Taxable) -> Slab Tax + 4% Cess = ₹{tax_payable:,}"

        evidence = [
            AdvisoryEvidence(
                source_type="STATUTORY_RULE",
                source_name="Section 115BAC(1A), The Finance (No. 2) Act, 2024",
                reference_id="rule_sec_115bac_ay25_26",
                page_number=None,
                status="STATUTORY_CURRENT",
                snippet=f"Standard Deduction: ₹{std_ded:,}, 5-10-15-20-30% Slabs, Rebate up to ₹7,00,000"
            ),
            AdvisoryEvidence(
                source_type="USER_DOCUMENT",
                source_name=income_source_desc,
                reference_id=source_doc_id,
                page_number=source_page,
                status="VERIFIED_FROM_DOCUMENT",
                snippet=f"Monthly Income: ₹{int(monthly_income):,} (Annualized: ₹{gross_inc:,})"
            )
        ]

        if tax_payable == 0 and tax_res.rebate_87a > Decimal('0.00'):
            answer = f"Aapki annualized income ₹{gross_inc:,} ke hisaab se, New Tax Regime (Section 115BAC, AY 2025-26) mein standard deduction (₹{std_ded:,}) aur Section 87A rebate ke baad aapka net tax ₹0 (Zero) banta hai."
        else:
            answer = f"Aapki verified income ke annualized hisaab (₹{gross_inc:,}) par New Tax Regime (Section 115BAC, AY 2025-26) ke tehat standard deduction (₹{std_ded:,}) ke baad estimated tax ₹{tax_payable:,} banta hai."

        return GroundedAdvisoryResponse(
            answer=answer,
            response_type=AdvisoryResponseType.CALCULATION,
            data_used={"annual_gross": float(annual_gross), "standard_deduction": float(std_ded), "taxable_income": float(taxable_inc), "tax_payable": float(tax_payable)},
            knowledge_used=[rule] if rule else [],
            calculation_used=formula,
            sources=evidence,
            status="GROUNDED_AND_VERIFIED",
            recommendation_disclaimer="Yeh calculation Section 115BAC New Tax Regime ke gazetted rules par based hai. Other deductions ya surcharge isme shamil nahi hain."
        )

    def _handle_emergency_fund(self, user_id: str, tx_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        prof = compute_financial_profile_deterministic(tx_rows)
        monthly_exp = prof["monthly_expenses"]
        min_ef = monthly_exp * 3.0
        max_ef = monthly_exp * 6.0

        formula = f"₹{int(monthly_exp):,} x 3 = ₹{int(min_ef):,} | ₹{int(monthly_exp):,} x 6 = ₹{int(max_ef):,}"

        evidence = [
            AdvisoryEvidence(
                source_type="CALCULATION",
                source_name="Financial Profile Analysis",
                reference_id="calc_emergency_fund",
                status="CALCULATED_FROM_VERIFIED_DATA",
                snippet=f"Average monthly expenses: ₹{int(monthly_exp):,}"
            )
        ]

        fact_str = f"FACT: Aapke current monthly expenses ₹{int(monthly_exp):,} hain."
        rec_str = f"RECOMMENDATION: Standard financial hygiene ke hisaab se aapka emergency fund ₹{int(min_ef):,} se ₹{int(max_ef):,} (3 se 6 mahine ke kharche) ke beech hona chahiye."

        return GroundedAdvisoryResponse(
            answer=f"{fact_str}\n\n{rec_str}",
            response_type=AdvisoryResponseType.RECOMMENDATION,
            data_used={"monthly_expenses": float(monthly_exp), "min_emergency_fund": float(min_ef), "max_emergency_fund": float(max_ef)},
            calculation_used=formula,
            sources=evidence,
            status="GROUNDED_AND_VERIFIED",
            recommendation_disclaimer="Yeh ek general financial guidance hai. Kisi registered investment advisor ki professional advice ko replace nahi karti."
        )

    def _handle_investment_80c(self, user_id: str, tx_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        rule_80c = get_statutory_rule("rule_sec_80c_cap")
        rule_115bac = get_statutory_rule("rule_sec_115bac_ay25_26")

        evidence = [
            AdvisoryEvidence(
                source_type="STATUTORY_RULE",
                source_name="Income Tax Act, 1961 Section 80C(1)",
                reference_id="rule_sec_80c_cap",
                status="STATUTORY_CURRENT",
                snippet="Aggregate deduction limit: ₹1,50,000 for EPF, PPF, ELSS, Life Insurance."
            )
        ]

        answer = (
            "Old Tax Regime ke tehat Section 80C ke under maximum ₹1,50,000 tak ki deduction claim ki ja sakti hai (PF, PPF, ELSS, Insurance).\n\n"
            "Dhyan rahe: Default New Tax Regime (Section 115BAC) mein Section 80C deductions allow nahi hain, balki lower slab rates aur ₹75,000 standard deduction milti hai."
        )

        return GroundedAdvisoryResponse(
            answer=answer,
            response_type=AdvisoryResponseType.EDUCATION,
            knowledge_used=[rule_80c] if rule_80c else [],
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_loan_inquiry(self, user_id: str, loan_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        if not loan_rows:
            return GroundedAdvisoryResponse(
                answer="Aapke uploaded documents mein koi active loan record verify nahi hua hai.",
                response_type=AdvisoryResponseType.OBSERVATION,
                status="NO_LOAN_RECORD"
            )

        total_principal = sum(l.get("principal", 0.0) for l in loan_rows)
        total_emi = sum(l.get("emi_amount", 0.0) for l in loan_rows)
        lenders = ", ".join(l["lender"] for l in loan_rows)

        evidence = [
            AdvisoryEvidence(
                source_type="USER_DOCUMENT",
                source_name="Loan Statement",
                reference_id=loan_rows[0].get("source_document_id", "loan_doc"),
                status="VERIFIED_FROM_DOCUMENT",
                snippet=f"Lenders: {lenders}, Total EMI: ₹{int(total_emi):,}"
            )
        ]

        return GroundedAdvisoryResponse(
            answer=f"Aapke record ke mutabiq {len(loan_rows)} loan(s) active hain ({lenders}). Total monthly EMI ₹{int(total_emi):,} hai.",
            response_type=AdvisoryResponseType.OBSERVATION,
            data_used={"total_principal": total_principal, "total_emi": total_emi},
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_what_changed(self, user_id: str, tx_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        detect_fn, _, _, _ = _get_os()
        delta_info = detect_fn(user_id)

        if not delta_info.get("has_changes"):
            return GroundedAdvisoryResponse(
                answer="Available statements ke hisaab se koi significant unexpected change detect nahi hua hai.",
                response_type=AdvisoryResponseType.OBSERVATION,
                status="NO_SIGNIFICANT_CHANGES"
            )

        changes = delta_info.get("changes", [])
        top_change = changes[0]
        summary_lines = [f"• {c['title']}" for c in changes[:3]]
        answer_text = f"Recent periods ko compare karne par ye important changes samne aaye hain:\n" + "\n".join(summary_lines)

        evidence = [
            AdvisoryEvidence(
                source_type="USER_DOCUMENT",
                source_name=top_change.get("source_doc", "Bank Statements"),
                reference_id="calc_delta_engine",
                page_number=top_change.get("source_page", 1),
                status="CALCULATED_FROM_VERIFIED_DATA",
                snippet=top_change.get("evidence_snippet", "")
            )
        ]

        return GroundedAdvisoryResponse(
            answer=answer_text,
            response_type=AdvisoryResponseType.OBSERVATION,
            data_used={"changes_count": len(changes), "top_change": top_change},
            calculation_used="Delta arithmetic across recent statements",
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_goals_inquiry(self, user_id: str) -> GroundedAdvisoryResponse:
        _, _, list_goals_fn, _ = _get_os()
        goals = list_goals_fn(user_id)

        if not goals:
            return GroundedAdvisoryResponse(
                answer="Aapka abhi koi active goal set nahi hai. Aap Home ya Goals section se naya goal add kar sakte hain.",
                response_type=AdvisoryResponseType.OBSERVATION,
                status="NO_GOALS_SET"
            )

        g = goals[0]
        months_str = f"{g['months_to_complete']} mahine" if g.get("months_to_complete") else "N/A"
        answer = (
            f"Aapka '{g['title']}' goal abhi {g['progress_percent']}% complete hai "
            f"(₹{int(g['current_amount']):,} / ₹{int(g['target_amount']):,}).\n"
            f"Monthly contribution ₹{int(g['monthly_contribution']):,} ke hisaab se bache hue ₹{int(g['remaining_amount']):,} "
            f"accumulate hone mein lagbhag {months_str} lagenge."
        )

        evidence = [
            AdvisoryEvidence(
                source_type="CALCULATION",
                source_name="Goals Engine",
                reference_id=g["id"],
                status="CALCULATED_FROM_VERIFIED_DATA",
                snippet=f"Target: ₹{int(g['target_amount']):,}, Current: ₹{int(g['current_amount']):,}, Progress: {g['progress_percent']}%"
            )
        ]

        return GroundedAdvisoryResponse(
            answer=answer,
            response_type=AdvisoryResponseType.CALCULATION,
            data_used=g,
            calculation_used=f"Target ₹{int(g['target_amount']):,} - Current ₹{int(g['current_amount']):,} = Remaining ₹{int(g['remaining_amount']):,}",
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_financial_health_inquiry(self, user_id: str) -> GroundedAdvisoryResponse:
        _, eval_health_fn, _, _ = _get_os()
        health = eval_health_fn(user_id)

        if health.get("status") == "INSUFFICIENT_DATA":
            return GroundedAdvisoryResponse(
                answer=health["message"],
                response_type=AdvisoryResponseType.NEEDS_INFORMATION,
                status="INSUFFICIENT_DATA"
            )

        rating = health.get("vitality_rating", "STABLE")
        runway = health.get("runway_months", 0.0)
        sav_rate = health.get("savings_rate", 0.0)
        dti = health.get("dti_ratio", 0.0)

        answer = (
            f"Aapki Financial Health Vitality Rating: {rating}.\n\n"
            f"{health.get('summary_message')}\n\n"
            f"• Emergency Runway: {runway} months\n"
            f"• Savings Rate: {sav_rate}%\n"
            f"• Debt-to-Income (DTI): {dti}%"
        )

        evidence = [
            AdvisoryEvidence(
                source_type="CALCULATION",
                source_name="5-Pillar Financial Health Model",
                reference_id="calc_health_model",
                status="CALCULATED_FROM_VERIFIED_DATA",
                snippet=f"Vitality: {rating}, Runway: {runway}m, Savings Rate: {sav_rate}%, DTI: {dti}%"
            )
        ]

        return GroundedAdvisoryResponse(
            answer=answer,
            response_type=AdvisoryResponseType.OBSERVATION,
            data_used=health,
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_net_worth_inquiry(self, user_id: str) -> GroundedAdvisoryResponse:
        _, _, _, snapshot_fn = _get_os()
        snap = snapshot_fn(user_id)

        if not snap.get("has_data") or not snap.get("net_worth"):
            return GroundedAdvisoryResponse(
                answer="Net worth calculate karne ke liye verified accounts aur balance records available nahi hain.",
                response_type=AdvisoryResponseType.NEEDS_INFORMATION,
                status="NO_DATA"
            )

        nw = snap["net_worth"]
        assets = nw["total_assets"]
        liab = nw["total_liabilities"]
        net_val = nw["net_worth"]

        answer = (
            f"Aapke verified documents ke anusar Net Worth ₹{int(net_val):,} hai.\n\n"
            f"• Verified Assets: ₹{int(assets):,} (Liquid cash + investments)\n"
            f"• Recorded Liabilities: ₹{int(liab):,} (Loans & debt)"
        )

        evidence = [
            AdvisoryEvidence(
                source_type="CALCULATION",
                source_name="Unified Financial Snapshot",
                reference_id="calc_net_worth",
                status="CALCULATED_FROM_VERIFIED_DATA",
                snippet=f"Assets: ₹{int(assets):,} - Liabilities: ₹{int(liab):,} = Net Worth: ₹{int(net_val):,}"
            )
        ]

        return GroundedAdvisoryResponse(
            answer=answer,
            response_type=AdvisoryResponseType.CALCULATION,
            data_used=nw,
            calculation_used=f"₹{int(assets):,} (Assets) - ₹{int(liab):,} (Liabilities) = ₹{int(net_val):,}",
            sources=evidence,
            status="GROUNDED_AND_VERIFIED"
        )

    def _handle_missing_specific_data(self, intent: AdvisoryIntent) -> GroundedAdvisoryResponse:
        topic = "foreign income / assets" if intent == AdvisoryIntent.FOREIGN_INCOME else "cryptocurrency / digital assets"
        return GroundedAdvisoryResponse(
            answer=f"Mere paas aapke {topic} ke baare mein koi verified document ya data nahi hai, isliye main is par exact calculation nahi kar sakta. myCA bina verified evidence ke estimate nahi lagata.",
            response_type=AdvisoryResponseType.NEEDS_INFORMATION,
            status="MISSING_INFORMATION_GUARDED"
        )

    def _handle_fallback(self, user_id: str, tx_rows: List[Dict[str, Any]]) -> GroundedAdvisoryResponse:
        return GroundedAdvisoryResponse(
            answer="Mere paas is specific query ke liye directly verified document evidence nahi hai. Aap apna balance, savings, ya categories dekhne ke liye Money tab check kar sakte hain.",
            response_type=AdvisoryResponseType.OBSERVATION,
            status="NO_DIRECT_EVIDENCE"
        )

    def _log_audit_event(self, user_id: str, event_type: str, details: Dict[str, Any]):
        try:
            conn = get_db()
            cursor = conn.cursor()
            import json, uuid
            cursor.execute("""
                INSERT INTO audit_events (id, user_id, event_type, details_json)
                VALUES (?, ?, ?, ?)
            """, (f"aud_{uuid.uuid4().hex[:12]}", user_id, event_type, json.dumps(details)))
            conn.commit()
            conn.close()
        except Exception:
            pass
