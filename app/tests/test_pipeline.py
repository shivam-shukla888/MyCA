import unittest
import os
import io
from app.db import init_db, get_db
from app.ingestion.validator import validate_uploaded_file, DocumentValidationError
from app.ingestion.extractor import extract_pdf_data
from app.ingestion.validator_layer import reconcile_statement_numbers
from app.ingestion.pipeline import process_pdf_document
from app.security import create_session_token
from app.server import app

class TestFinancialPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()
        cls.token_aarav = create_session_token("usr_aarav_01")
        cls.token_priya = create_session_token("usr_priya_02")
        cls.valid_pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads", "HDFC_Bank_Statement_Oct2024.pdf")
        with open(cls.valid_pdf_path, "rb") as f:
            cls.valid_pdf_bytes = f.read()

    def test_01_valid_bank_statement_ingestion(self):
        """Test valid multi-page bank statement parsing, reconciliation, and metric computation."""
        res = process_pdf_document(self.valid_pdf_bytes, "HDFC_Valid.pdf", "usr_aarav_01", allow_duplicate=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "READY")
        self.assertEqual(res["num_pages"], 4)
        self.assertEqual(res["reconciliation"]["opening_balance"], 45500.0)
        self.assertEqual(res["reconciliation"]["total_credits"], 82000.0)
        self.assertEqual(res["reconciliation"]["total_debits"], 54300.0)
        self.assertEqual(res["reconciliation"]["net_savings"], 27700.0)
        self.assertEqual(res["reconciliation"]["calculated_closing"], 73200.0)
        self.assertEqual(res["reconciliation"]["discrepancy"], 0.0)

    def test_02_duplicate_statement_detection(self):
        """Test duplicate detection prevents double-counting and notifies user."""
        # First upload
        process_pdf_document(self.valid_pdf_bytes, "HDFC_Dup_Test.pdf", "usr_aarav_01", allow_duplicate=True)
        # Second upload with allow_duplicate=False
        dup_res = process_pdf_document(self.valid_pdf_bytes, "HDFC_Dup_Test.pdf", "usr_aarav_01", allow_duplicate=False)
        self.assertFalse(dup_res["success"])
        self.assertTrue(dup_res["is_duplicate"])
        self.assertEqual(dup_res["message"], "Ye document pehle se add hai.")

    def test_03_malformed_and_empty_pdf(self):
        """Test graceful rejection of corrupted or empty files with localized user message."""
        # Empty file
        with self.assertRaises(DocumentValidationError):
            validate_uploaded_file(b"", "empty.pdf")
        
        # Corrupted header
        with self.assertRaises(DocumentValidationError):
            validate_uploaded_file(b"This is not a real PDF file content", "corrupted.pdf")

    def test_04_calculation_mismatch_and_no_silent_correction(self):
        """Test that arithmetic mismatch is flagged as NEEDS_REVIEW and never silently corrected."""
        dummy_txs = [
            {"amount": 82000.0, "type": "CREDIT"},
            {"amount": 54300.0, "type": "DEBIT"}
        ]
        # Real opening 45,500 + 82,000 - 54,300 = 73,200.
        # Reported closing balance is deliberately altered to 70,000.0
        audit = reconcile_statement_numbers(45500.0, 70000.0, dummy_txs)
        self.assertFalse(audit["is_valid"])
        self.assertEqual(audit["status"], "NEEDS_REVIEW")
        self.assertEqual(audit["discrepancy"], 3200.0)
        self.assertIn("Is statement ka balance match nahi ho raha", audit["message"])

    def test_05_multi_tenant_user_isolation(self):
        """CRITICAL: User B must NEVER be able to see or access User A's documents, accounts, or transactions."""
        # Upload statement as User Aarav
        aarav_upload = process_pdf_document(self.valid_pdf_bytes, "Aarav_Private_Ledger.pdf", "usr_aarav_01", allow_duplicate=True)
        doc_id = aarav_upload["document_id"]

        # Attempt to access Aarav's document details as Priya
        priya_headers = {"Authorization": f"Bearer {self.token_priya}"}
        res = self.client.get(f"/api/documents/{doc_id}", headers=priya_headers)
        self.assertEqual(res.status_code, 404)

        # Attempt to download Aarav's raw PDF file as Priya
        res_file = self.client.get(f"/api/documents/{doc_id}/file", headers=priya_headers)
        self.assertEqual(res_file.status_code, 404)

        # Check Priya's profile (should be empty / isolated)
        res_priya_prof = self.client.get("/api/user/profile", headers=priya_headers).get_json()
        self.assertFalse(res_priya_prof["has_data"])
        self.assertEqual(res_priya_prof["metrics"]["monthly_income"], "Unknown")
        self.assertEqual(len(res_priya_prof["accounts"]), 0)

        # Check Priya's transactions list (must be 0 transactions)
        res_priya_tx = self.client.get("/api/transactions", headers=priya_headers).get_json()
        self.assertEqual(len(res_priya_tx["transactions"]), 0)

    def test_06_ask_myca_grounded_citations(self):
        """Test Ask myCA answers strictly from extracted statement data with page citations."""
        aarav_headers = {"Authorization": f"Bearer {self.token_aarav}"}
        res = self.client.post("/api/advisory/ask", json={"query": "Mera paisa sabse zyada kahan ja raha hai?"}, headers=aarav_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("rent", data["answer"].lower())
        self.assertTrue(len(data["sources"]) > 0)
        self.assertEqual(data["sources"][0]["page"], 4)

if __name__ == "__main__":
    unittest.main()
