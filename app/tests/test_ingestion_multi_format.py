"""
Phase 4 Multi-Format Document Ingestion & Verification Test Suite.
Tests:
- Structural document classification (Bank, Salary Slip, Form 16, Unsupported)
- Salary Slip extraction, provenance & mathematical invariant check
- Form 16 extraction, provenance & tax calculation invariant check
- Scanned PDF local OCR fallback & status tracking (NEEDS_REVIEW)
- Password-protected rejection (PASSWORD_PROTECTED)
- Corrupted PDF rejection (CORRUPTED_PDF)
- Unsupported document handling (UNSUPPORTED)
- Deduplication refinement (distinct refs vs confirmed duplicates)
- Provenance and source page traceability
- Cross-user tenant isolation across multi-format documents
"""

import unittest
import os
from decimal import Decimal
from app.db import init_db, get_db
from app.server import app
from app.security import create_session_token
from app.ingestion.pipeline import process_pdf_document
from app.ingestion.validator import validate_uploaded_file, DocumentValidationError
from app.ingestion.classifier import classify_document, DocumentType
from app.financial.duplicate import detect_overlapping_transactions
from app.tests.fixtures.golden_statements import (
    GOLDEN_SALARY_SLIP_VALID,
    GOLDEN_SALARY_SLIP_MISMATCH,
    GOLDEN_FORM_16_VALID,
    GOLDEN_FORM_16_MISMATCH,
    create_salary_slip_pdf,
    create_form_16_pdf,
    create_scanned_pdf,
    create_encrypted_pdf,
    create_unsupported_pdf
)

class TestIngestionMultiFormat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()
        cls.user_aarav = "usr_aarav_01"
        cls.user_priya = "usr_priya_02"
        cls.token_aarav = create_session_token(cls.user_aarav)
        cls.token_priya = create_session_token(cls.user_priya)

    def test_01_classification_accuracy(self):
        """Test structural document classification across various financial document types."""
        # 1. Bank statement
        dt, conf, _ = classify_document("HDFC Bank Statement of Account Opening Balance 45500 Closing Balance 73200", "statement.pdf")
        self.assertEqual(dt, DocumentType.BANK_STATEMENT)
        self.assertGreaterEqual(conf, 0.90)

        # 2. Salary slip
        dt, conf, _ = classify_document("SALARY SLIP Infosys Limited Payslip for October 2024 Gross Salary 115000 Net Pay 82000", "salary_slip.pdf")
        self.assertEqual(dt, DocumentType.SALARY_SLIP)
        self.assertGreaterEqual(conf, 0.90)

        # 3. Form 16
        dt, conf, _ = classify_document("FORM NO. 16 Certificate under section 203 of the Income-tax Act, 1961 Assessment Year 2024-25", "form16.pdf")
        self.assertEqual(dt, DocumentType.FORM_16)
        self.assertGreaterEqual(conf, 0.95)

        # 4. Credit card
        dt, conf, _ = classify_document("Credit Card Statement Total Amount Due Minimum Amount Due Available Credit Limit", "cc_statement.pdf")
        self.assertEqual(dt, DocumentType.CREDIT_CARD_STATEMENT)

        # 5. Loan statement
        dt, conf, _ = classify_document("Loan Account Statement Principal Outstanding Term Loan EMI Schedule", "loan.pdf")
        self.assertEqual(dt, DocumentType.LOAN_STATEMENT)

        # 6. Demat statement
        dt, conf, _ = classify_document("Statement of Holding Demat Account Depository Participant NSDL CDSL ISIN", "demat.pdf")
        self.assertEqual(dt, DocumentType.DEMAT_STATEMENT)

        # 7. Unsupported / Unknown
        dt, conf, _ = classify_document("Cooking Italian Pasta with fresh basil and tomatoes", "recipe.pdf")
        self.assertEqual(dt, DocumentType.UNKNOWN)
        self.assertLess(conf, 0.50)

    def test_02_salary_slip_valid_ingestion(self):
        """Test valid salary slip extraction, invariant check (Gross - Deductions == Net), and persistence."""
        pdf_bytes = create_salary_slip_pdf(
            employer=GOLDEN_SALARY_SLIP_VALID["employer"],
            period=GOLDEN_SALARY_SLIP_VALID["pay_period"],
            gross=GOLDEN_SALARY_SLIP_VALID["gross_salary"],
            deductions=GOLDEN_SALARY_SLIP_VALID["total_deductions"],
            net=GOLDEN_SALARY_SLIP_VALID["net_salary"]
        )

        res = process_pdf_document(pdf_bytes, "Salary_Slip_Oct2024.pdf", self.user_aarav, allow_duplicate=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "READY")
        self.assertEqual(res["doc_type"], "salary_slip")
        self.assertEqual(res["reconciliation"]["discrepancy"], 0.0)

        # Verify database persistence in income_records
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM income_records WHERE source_document_id = ?", (res["document_id"],))
        inc = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(inc)
        self.assertEqual(inc["source"], "Infosys Limited")
        self.assertEqual(float(inc["amount"]), 82000.0)
        self.assertEqual(inc["status"], "READY")

    def test_03_salary_slip_arithmetic_mismatch_needs_review(self):
        """Test salary slip with arithmetic mismatch is marked NEEDS_REVIEW and never silently corrected."""
        pdf_bytes = create_salary_slip_pdf(
            employer=GOLDEN_SALARY_SLIP_MISMATCH["employer"],
            period=GOLDEN_SALARY_SLIP_MISMATCH["pay_period"],
            gross=GOLDEN_SALARY_SLIP_MISMATCH["gross_salary"],
            deductions=GOLDEN_SALARY_SLIP_MISMATCH["total_deductions"],
            net=GOLDEN_SALARY_SLIP_MISMATCH["reported_net"]  # 75,000 instead of 82,000
        )

        res = process_pdf_document(pdf_bytes, "Salary_Slip_Mismatch.pdf", self.user_aarav, allow_duplicate=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["reconciliation"]["discrepancy"], 7000.0)
        self.assertIn("arithmetic mismatch", res["message"].lower())

    def test_04_form_16_valid_ingestion(self):
        """Test Form 16 extraction, invariant check, and persistence in tax_documents table."""
        pdf_bytes = create_form_16_pdf(
            employer=GOLDEN_FORM_16_VALID["employer"],
            ay=GOLDEN_FORM_16_VALID["assessment_year"],
            pan=GOLDEN_FORM_16_VALID["employee_pan"],
            gross=GOLDEN_FORM_16_VALID["gross_salary"],
            deductions=GOLDEN_FORM_16_VALID["deductions"],
            taxable=GOLDEN_FORM_16_VALID["taxable_income"],
            tds=GOLDEN_FORM_16_VALID["tax_deducted"]
        )

        res = process_pdf_document(pdf_bytes, "Form_16_AY2024-25.pdf", self.user_aarav, allow_duplicate=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "READY")
        self.assertEqual(res["doc_type"], "form_16")
        self.assertEqual(res["reconciliation"]["discrepancy"], 0.0)

        # Verify database persistence in tax_documents
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tax_documents WHERE source_document_id = ?", (res["document_id"],))
        tax = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(tax)
        self.assertEqual(tax["assessment_year"], "2024-25")
        self.assertEqual(float(tax["total_tax_paid"]), 110000.0)

    def test_05_form_16_tax_mismatch_needs_review(self):
        """Test Form 16 with tax calculation mismatch is flagged as NEEDS_REVIEW."""
        pdf_bytes = create_form_16_pdf(
            employer=GOLDEN_FORM_16_MISMATCH["employer"],
            ay=GOLDEN_FORM_16_MISMATCH["assessment_year"],
            pan=GOLDEN_FORM_16_MISMATCH["employee_pan"],
            gross=GOLDEN_FORM_16_MISMATCH["gross_salary"],
            deductions=GOLDEN_FORM_16_MISMATCH["deductions"],
            taxable=GOLDEN_FORM_16_MISMATCH["reported_taxable"],  # Discrepancy of 1,50,000
            tds=GOLDEN_FORM_16_MISMATCH["tax_deducted"]
        )

        res = process_pdf_document(pdf_bytes, "Form_16_Mismatch.pdf", self.user_aarav, allow_duplicate=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "NEEDS_REVIEW")
        self.assertEqual(res["reconciliation"]["discrepancy"], 150000.0)

    def test_06_scanned_pdf_ocr_fallback_needs_review(self):
        """Scanned image-only PDFs must trigger OCR fallback and NEVER be automatically verified as READY."""
        scanned_bytes = create_scanned_pdf()
        res = process_pdf_document(scanned_bytes, "Scanned_Invoice.pdf", self.user_aarav, allow_duplicate=True)
        self.assertTrue(res["success"])
        self.assertTrue(res["is_scanned"])
        self.assertIn(res["status"], ["NEEDS_REVIEW", "UNSUPPORTED"])
        self.assertNotEqual(res["status"], "READY")

    def test_07_password_protected_pdf_rejection(self):
        """Password-protected PDFs must be rejected with PASSWORD_PROTECTED code."""
        encrypted_bytes = create_encrypted_pdf("secret123")
        with self.assertRaises(DocumentValidationError) as cm:
            validate_uploaded_file(encrypted_bytes, "protected.pdf")
        self.assertEqual(cm.exception.code, "PASSWORD_PROTECTED")

        # In pipeline
        res = process_pdf_document(encrypted_bytes, "protected.pdf", self.user_aarav)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "PASSWORD_PROTECTED")

    def test_08_corrupted_pdf_rejection(self):
        """Corrupted PDFs must be rejected with CORRUPTED_PDF code."""
        bad_bytes = b"%PDF-corrupted-bytes-not-a-valid-pdf"
        with self.assertRaises(DocumentValidationError) as cm:
            validate_uploaded_file(bad_bytes, "corrupt.pdf")
        self.assertEqual(cm.exception.code, "CORRUPTED_PDF")

        # In pipeline
        res = process_pdf_document(bad_bytes, "corrupt.pdf", self.user_aarav)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_code"], "CORRUPTED_PDF")

    def test_09_unsupported_document_graceful_handling(self):
        """Unsupported document formats must be classified as UNSUPPORTED without inventing financial data."""
        recipe_bytes = create_unsupported_pdf()
        res = process_pdf_document(recipe_bytes, "Pasta_Recipe.pdf", self.user_aarav, allow_duplicate=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "UNSUPPORTED")
        self.assertEqual(res["transaction_count"], 0)

    def test_10_repeated_legitimate_transactions_with_distinct_refs(self):
        """Two identical transactions on the same day with different references must be treated as UNIQUE."""
        tx1 = {
            "id": "tx_rep_01",
            "date_iso": "2024-10-15",
            "amount": 150.00,
            "direction": "DEBIT",
            "cleaned_merchant": "STARBUCKS COFFEE",
            "account_id": "acc_01",
            "ref_no": "UPI-REF-001",
            "balance": 45000.00
        }
        tx2 = {
            "id": "tx_rep_02",
            "date_iso": "2024-10-15",
            "amount": 150.00,
            "direction": "DEBIT",
            "cleaned_merchant": "STARBUCKS COFFEE",
            "account_id": "acc_01",
            "ref_no": "UPI-REF-002",
            "balance": 44850.00
        }

        # Deduplicate batch
        deduped = detect_overlapping_transactions([tx1, tx2], existing_fingerprints={})
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["duplicate_status"], "UNIQUE")
        self.assertEqual(deduped[1]["duplicate_status"], "UNIQUE")

    def test_11_provenance_and_source_evidence(self):
        """Every parsed page and extraction must maintain document provenance and source page."""
        pdf_bytes = create_salary_slip_pdf()
        res = process_pdf_document(pdf_bytes, "Salary_Slip_Provenance.pdf", self.user_aarav, allow_duplicate=True)
        doc_id = res["document_id"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM document_pages WHERE document_id = ?", (doc_id,))
        pages = cursor.fetchall()
        self.assertGreaterEqual(len(pages), 1)
        self.assertEqual(pages[0]["page_number"], 1)
        self.assertIn("Gross Salary", pages[0]["raw_text"])

        cursor.execute("SELECT * FROM document_extractions WHERE document_id = ?", (doc_id,))
        extractions = cursor.fetchall()
        self.assertGreaterEqual(len(extractions), 1)
        conn.close()

    def test_12_cross_user_data_isolation_multi_format(self):
        """User B must not be able to view User A's salary slip or tax records."""
        # Ingest salary slip for User A
        pdf_bytes = create_salary_slip_pdf()
        res_a = process_pdf_document(pdf_bytes, "Aarav_Private_Salary.pdf", self.user_aarav, allow_duplicate=True)
        doc_a_id = res_a["document_id"]

        # User B attempts to access document pages
        res_b_pages = self.client.get(
            f"/api/documents/{doc_a_id}/pages",
            headers={"Authorization": f"Bearer {self.token_priya}"}
        )
        self.assertEqual(res_b_pages.status_code, 404)

        # User B attempts to access document file download
        res_b_file = self.client.get(
            f"/api/documents/{doc_a_id}/file",
            headers={"Authorization": f"Bearer {self.token_priya}"}
        )
        self.assertEqual(res_b_file.status_code, 404)
