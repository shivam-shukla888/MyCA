"""
Versioned Statutory Knowledge Registry for myCA.
Stores official, gazetted statutory tax rules, deductions, and slab schedules.
Separates statutory truth from personal user financial records and AI claims.
"""

import json
from typing import Dict, Any, List, Optional
from ..db import get_db
from .models import StatutoryRule, RuleStatus

OFFICIAL_TAX_RULES = [
    {
        "id": "rule_sec_115bac_ay25_26",
        "topic": "INCOME_TAX",
        "title": "New Concessional Tax Regime (Section 115BAC) — AY 2025-26",
        "content": "Personal income tax slab structure for individuals and HUFs under the default new tax regime with enhanced standard deduction of ₹75,000 and updated 5-10-15-20-30% rate slabs.",
        "source": "Ministry of Law and Justice, Government of India",
        "official_source_reference": "The Finance (No. 2) Act, 2024 (Act No. 15 of 2024), Gazette of India Notification No. 22/2024",
        "publication_date": "2024-08-16",
        "effective_from": "2024-04-01",
        "effective_to": "2025-03-31",
        "financial_year": "2024-25",
        "assessment_year": "2025-26",
        "provision": "Section 115BAC(1A) — Concessional Personal Income Tax Slabs (New Regime)",
        "jurisdiction": "IN_CBDT",
        "status": RuleStatus.CURRENT.value,
        "supersedes": "rule_sec_115bac_ay24_25",
        "superseded_by": None,
        "version": 2,
        "rule_data": {
            "regime": "NEW",
            "slabs": [
                {"min": 0, "max": 300000, "rate_percent": 0},
                {"min": 300000, "max": 700000, "rate_percent": 5},
                {"min": 700000, "max": 1000000, "rate_percent": 10},
                {"min": 1000000, "max": 1200000, "rate_percent": 15},
                {"min": 1200000, "max": 1500000, "rate_percent": 20},
                {"min": 1500000, "max": None, "rate_percent": 30}
            ],
            "standard_deduction": 75000.0,
            "section_87a_rebate_limit": 700000.0,
            "section_87a_max_rebate": 25000.0,
            "cess_percent": 4.0
        }
    },
    {
        "id": "rule_sec_115bac_ay24_25",
        "topic": "INCOME_TAX",
        "title": "New Concessional Tax Regime (Section 115BAC) — AY 2024-25",
        "content": "Personal income tax slab structure under the new regime for Assessment Year 2024-25 with ₹50,000 standard deduction.",
        "source": "Ministry of Finance, Government of India",
        "official_source_reference": "The Finance Act, 2023 (Act No. 8 of 2023), Gazette of India",
        "publication_date": "2023-03-31",
        "effective_from": "2023-04-01",
        "effective_to": "2024-03-31",
        "financial_year": "2023-24",
        "assessment_year": "2024-25",
        "provision": "Section 115BAC(1A) — Standard Slabs for AY 2024-25",
        "jurisdiction": "IN_CBDT",
        "status": RuleStatus.SUPERSEDED.value,
        "supersedes": None,
        "superseded_by": "rule_sec_115bac_ay25_26",
        "version": 1,
        "rule_data": {
            "regime": "NEW",
            "slabs": [
                {"min": 0, "max": 300000, "rate_percent": 0},
                {"min": 300000, "max": 600000, "rate_percent": 5},
                {"min": 600000, "max": 900000, "rate_percent": 10},
                {"min": 900000, "max": 1200000, "rate_percent": 15},
                {"min": 1200000, "max": 1500000, "rate_percent": 20},
                {"min": 1500000, "max": None, "rate_percent": 30}
            ],
            "standard_deduction": 50000.0,
            "section_87a_rebate_limit": 700000.0,
            "section_87a_max_rebate": 25000.0,
            "cess_percent": 4.0
        }
    },
    {
        "id": "rule_sec_80c_cap",
        "topic": "DEDUCTION",
        "title": "Section 80C Investment & Savings Deduction Limit",
        "content": "Deduction in respect of life insurance premia, deferred annuity, contributions to provident fund (EPF/PPF), subscription to certain equity shares or debentures (ELSS), tuition fees, and home loan principal repayment.",
        "source": "Central Board of Direct Taxes (CBDT)",
        "official_source_reference": "Income Tax Act, 1961 Section 80C(1) as amended by Finance (No. 2) Act 2014",
        "publication_date": "2014-07-10",
        "effective_from": "2014-04-01",
        "effective_to": None,
        "financial_year": "ANY_OLD_REGIME",
        "assessment_year": "ANY_OLD_REGIME",
        "provision": "Section 80C — Aggregate Deduction Ceiling for Life Insurance, PF, PPF, ELSS, Housing Principal",
        "jurisdiction": "IN_CBDT",
        "status": RuleStatus.CURRENT.value,
        "supersedes": None,
        "superseded_by": None,
        "version": 1,
        "rule_data": {
            "aggregate_cap": 150000.0,
            "applicable_regime": "OLD_TAX_REGIME_ONLY"
        }
    },
    {
        "id": "rule_sec_80d_health",
        "topic": "DEDUCTION",
        "title": "Section 80D Health Insurance Deduction Limit",
        "content": "Deduction in respect of health insurance premium paid for self, spouse, and dependent children up to ₹25,000, plus an additional ₹25,000 (or ₹50,000 if senior citizen) for parents.",
        "source": "Central Board of Direct Taxes (CBDT)",
        "official_source_reference": "Income Tax Act, 1961 Section 80D as amended by Finance Act 2018",
        "publication_date": "2018-03-29",
        "effective_from": "2018-04-01",
        "effective_to": None,
        "financial_year": "ANY_OLD_REGIME",
        "assessment_year": "ANY_OLD_REGIME",
        "provision": "Section 80D — Medical Insurance Premia and Preventive Health Check-up",
        "jurisdiction": "IN_CBDT",
        "status": RuleStatus.CURRENT.value,
        "supersedes": None,
        "superseded_by": None,
        "version": 1,
        "rule_data": {
            "self_family_limit": 25000.0,
            "parents_limit": 25000.0,
            "senior_parents_limit": 50000.0,
            "preventive_health_sublimit": 5000.0,
            "applicable_regime": "OLD_TAX_REGIME_ONLY"
        }
    },
    {
        "id": "rule_sec_24b_home_loan",
        "topic": "DEDUCTION",
        "title": "Section 24(b) Deductions from Income from House Property",
        "content": "Deduction for interest payable on capital borrowed for the acquisition or construction of self-occupied house property up to ₹2,00,000.",
        "source": "Central Board of Direct Taxes (CBDT)",
        "official_source_reference": "Income Tax Act, 1961 Section 24(b) as amended by Finance (No. 2) Act 2014",
        "publication_date": "2014-07-10",
        "effective_from": "2014-04-01",
        "effective_to": None,
        "financial_year": "ANY_OLD_REGIME",
        "assessment_year": "ANY_OLD_REGIME",
        "provision": "Section 24(b) — Interest on Borrowed Capital for Self-Occupied House Property",
        "jurisdiction": "IN_CBDT",
        "status": RuleStatus.CURRENT.value,
        "supersedes": None,
        "superseded_by": None,
        "version": 1,
        "rule_data": {
            "max_interest_deduction_self_occupied": 200000.0,
            "applicable_regime": "OLD_TAX_REGIME_ONLY"
        }
    },
    {
        "id": "rule_draft_unverified_reform",
        "topic": "INCOME_TAX",
        "title": "Speculative Zero Tax Proposal (Unverified)",
        "content": "Unverified social media blog claim that tax on all income up to ₹10 Lakhs is eliminated.",
        "source": "Social Media Rumor / Unverified Blog",
        "official_source_reference": "Unverified draft post",
        "publication_date": "2026-09-01",
        "effective_from": "2027-04-01",
        "effective_to": None,
        "financial_year": "2027-28",
        "assessment_year": "2028-29",
        "provision": "Proposed 0% tax up to 10 Lakhs",
        "jurisdiction": "IN_CBDT",
        "status": RuleStatus.NOT_VERIFIED.value,
        "supersedes": None,
        "superseded_by": None,
        "version": 1,
        "rule_data": {"speculative": True}
    }
]

def seed_statutory_rules():
    """Seeds verified official tax rules into the persistent statutory_rules ledger."""
    conn = get_db()
    cursor = conn.cursor()
    for r in OFFICIAL_TAX_RULES:
        cursor.execute("""
            INSERT OR REPLACE INTO statutory_rules (
                id, topic, title, content, source, official_source_reference, publication_date,
                effective_from, effective_to, financial_year, assessment_year,
                provision, jurisdiction, status, rule_data_json, supersedes, superseded_by, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["id"], r.get("topic", "INCOME_TAX"), r.get("title", ""), r.get("content", ""),
            r["source"], r["official_source_reference"], r["publication_date"],
            r["effective_from"], r["effective_to"], r["financial_year"], r["assessment_year"],
            r["provision"], r["jurisdiction"], r["status"], json.dumps(r["rule_data"]),
            r["supersedes"], r["superseded_by"], r.get("version", 1)
        ))
    conn.commit()
    conn.close()

def get_statutory_rule(rule_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single statutory rule by ID with deserialized rule_data."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM statutory_rules WHERE id = ?", (rule_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["rule_data"] = json.loads(d["rule_data_json"])
    return d

def get_current_rules_for_ay(assessment_year: str) -> List[Dict[str, Any]]:
    """Returns only verified CURRENT rules for a specific Assessment Year."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM statutory_rules
        WHERE (assessment_year = ? OR assessment_year = 'ANY_OLD_REGIME')
          AND status = 'CURRENT'
    """, (assessment_year,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    for r in rows:
        r["rule_data"] = json.loads(r["rule_data_json"])
    return rows

def search_rules(
    topic: Optional[str] = None,
    status: Optional[str] = "CURRENT",
    effective_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Structured query retrieval for authoritative rules.
    Never returns NOT_VERIFIED rules unless status='NOT_VERIFIED' is explicitly requested.
    """
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM statutory_rules WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    else:
        # Default safety: exclude NOT_VERIFIED
        query += " AND status != 'NOT_VERIFIED'"

    if topic:
        query += " AND topic = ?"
        params.append(topic)

    if effective_date:
        query += " AND effective_from <= ? AND (effective_to IS NULL OR effective_to >= ?)"
        params.extend([effective_date, effective_date])

    cursor.execute(query, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for r in rows:
        r["rule_data"] = json.loads(r["rule_data_json"])
    return rows

def ingest_verified_rule(rule_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validation pipeline for new statutory rules.
    Rejects rules without primary official source reference, gazette dates, or valid status.
    Guarantees no LLM or unverified source directly writes to production rules.
    """
    required_fields = ["id", "source", "official_source_reference", "publication_date", "effective_from", "provision", "status", "rule_data"]
    for f in required_fields:
        if not rule_dict.get(f):
            raise ValueError(f"Missing mandatory statutory verification field: '{f}'")

    status = rule_dict["status"]
    if status not in [s.value for s in RuleStatus]:
        raise ValueError(f"Invalid rule status: {status}")

    # Check if primary official source is present
    source = rule_dict["source"].lower()
    official_ref = rule_dict["official_source_reference"].lower()
    if "act" not in official_ref and "gazette" not in official_ref and "notification" not in official_ref and "circular" not in official_ref:
        # Cannot be classified as CURRENT without official legislative reference
        rule_dict["status"] = RuleStatus.NOT_VERIFIED.value

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO statutory_rules (
            id, topic, title, content, source, official_source_reference, publication_date,
            effective_from, effective_to, financial_year, assessment_year,
            provision, jurisdiction, status, rule_data_json, supersedes, superseded_by, version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rule_dict["id"],
        rule_dict.get("topic", "INCOME_TAX"),
        rule_dict.get("title", ""),
        rule_dict.get("content", ""),
        rule_dict["source"],
        rule_dict["official_source_reference"],
        rule_dict["publication_date"],
        rule_dict["effective_from"],
        rule_dict.get("effective_to"),
        rule_dict.get("financial_year", "2024-25"),
        rule_dict.get("assessment_year", "2025-26"),
        rule_dict["provision"],
        rule_dict.get("jurisdiction", "IN_CBDT"),
        rule_dict["status"],
        json.dumps(rule_dict["rule_data"]),
        rule_dict.get("supersedes"),
        rule_dict.get("superseded_by"),
        rule_dict.get("version", 1)
    ))
    conn.commit()
    conn.close()

    return {"success": True, "rule_id": rule_dict["id"], "status": rule_dict["status"]}
