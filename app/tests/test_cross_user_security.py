import unittest
import os
import json
from app.db import init_db, get_db
from app.server import app
from app.security import create_session_token, create_signed_doc_token, verify_session_token
from app.ingestion.pipeline import process_pdf_document

class TestCrossUserSecurityIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

        # Seed two users
        cls.user_a = "usr_aarav_01"
        cls.user_b = "usr_priya_02"

        # Generate HMAC session tokens
        cls.token_a = create_session_token(cls.user_a)
        cls.token_b = create_session_token(cls.user_b)

        # Ingest document for User A
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads", "HDFC_Bank_Statement_Oct2024.pdf")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        res_a = process_pdf_document(pdf_bytes, "Aarav_Private_HDFC.pdf", cls.user_a, allow_duplicate=True)
        assert res_a["success"], f"Failed to ingest for user A: {res_a}"
        cls.doc_a_id = res_a["document_id"]

        # User B starts with 0 documents
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM transactions WHERE user_id = ?", (cls.user_a,))
        row = cursor.fetchone()
        cls.tx_a_id = row["id"] if row else None
        conn.close()

    def test_01_token_verification_and_unauthorized_access(self):
        """Unauthenticated requests must be rejected with 401."""
        res = self.client.get("/api/user/profile")
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data.get("code"), "AUTH_REQUIRED")

        # Tampered token
        tampered_token = self.token_a[:-5] + "XXXXX"
        res_tampered = self.client.get("/api/user/profile", headers={"Authorization": f"Bearer {tampered_token}"})
        self.assertEqual(res_tampered.status_code, 401)
        self.assertEqual(res_tampered.get_json().get("code"), "INVALID_TOKEN")

    def test_02_user_b_cannot_read_user_a_profile_and_summary(self):
        """User B session must only return User B data, not User A financial summaries."""
        # User A summary
        res_a = self.client.get("/api/financial/summary", headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.get_json()
        self.assertTrue(data_a["has_data"])
        self.assertEqual(data_a["user"]["id"], self.user_a)

        # User B summary (clean profile)
        res_b = self.client.get("/api/financial/summary", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.get_json()
        self.assertFalse(data_b["has_data"])
        self.assertEqual(data_b["user"]["id"], self.user_b)
        self.assertEqual(data_b["metrics"]["monthly_savings"], "Unknown")

    def test_03_user_b_cannot_read_user_a_documents_list(self):
        """User B listing documents must never return User A documents."""
        res_b = self.client.get("/api/documents", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.get_json()
        self.assertEqual(data_b["total"], 0)
        self.assertEqual(len(data_b["documents"]), 0)

        # User A listing documents has document
        res_a = self.client.get("/api/documents", headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.get_json()
        self.assertGreaterEqual(data_a["total"], 1)
        doc_ids = [d["id"] for d in data_a["documents"]]
        self.assertIn(self.doc_a_id, doc_ids)

    def test_04_user_b_cannot_access_user_a_document_detail_or_pages(self):
        """User B cannot fetch User A document pages or metadata by ID."""
        res_b = self.client.get(f"/api/documents/{self.doc_a_id}/pages", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res_b.status_code, 404)
        data_b = res_b.get_json()
        self.assertIn("error", data_b)

    def test_05_user_b_cannot_stream_or_download_user_a_pdf(self):
        """User B cannot download User A raw PDF via direct endpoint or spoofing."""
        # Direct download attempt with User B token
        res_b = self.client.get(f"/api/documents/{self.doc_a_id}/file", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res_b.status_code, 404)

        # Unauthenticated direct download attempt
        res_anon = self.client.get(f"/api/documents/{self.doc_a_id}/file")
        self.assertEqual(res_anon.status_code, 401)

    def test_06_user_b_cannot_mint_signed_url_for_user_a_document(self):
        """User B cannot obtain signed URL for User A's document."""
        res = self.client.get(f"/api/documents/{self.doc_a_id}/signed-url", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res.status_code, 404)

    def test_07_tampered_or_cross_user_signed_token_rejected(self):
        """A signed URL minted for User A cannot be accessed with User B identity or modified token."""
        # Mint valid signed token for User A
        res_a = self.client.get(f"/api/documents/{self.doc_a_id}/signed-url", headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(res_a.status_code, 200)
        signed_token = res_a.get_json()["token"]

        # Valid signed token works without headers (browser iframe mode)
        res_stream = self.client.get(f"/api/documents/{self.doc_a_id}/file?token={signed_token}")
        self.assertEqual(res_stream.status_code, 200)
        self.assertEqual(res_stream.mimetype, "application/pdf")
        res_stream.close()

        # Forged/tampered token fails
        bad_token = signed_token[:-4] + "FFFF"
        res_bad = self.client.get(f"/api/documents/{self.doc_a_id}/file?token={bad_token}")
        self.assertEqual(res_bad.status_code, 401)

    def test_08_user_b_cannot_read_user_a_transactions(self):
        """User B querying transactions receives 0 transactions."""
        res_b = self.client.get("/api/financial/transactions", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.get_json()
        self.assertEqual(data_b["total"], 0)
        self.assertEqual(len(data_b["transactions"]), 0)

    def test_09_user_b_cannot_read_user_a_accounts(self):
        """User B querying accounts receives 0 accounts."""
        res_b = self.client.get("/api/financial/accounts", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.get_json()
        self.assertEqual(data_b["total"], 0)
        self.assertEqual(len(data_b["accounts"]), 0)

    def test_10_user_b_cannot_modify_user_a_transaction_category(self):
        """User B cannot alter transaction category of User A's transaction."""
        if not self.tx_a_id:
            self.skipTest("No transaction for User A available to test modification.")

        res_patch = self.client.patch(
            f"/api/transactions/{self.tx_a_id}/category",
            headers={"Authorization": f"Bearer {self.token_b}"},
            json={"category": "INVESTMENT"}
        )
        self.assertEqual(res_patch.status_code, 404)
        data = res_patch.get_json()
        self.assertFalse(data.get("success", False))

    def test_11_user_b_cannot_delete_user_a_document(self):
        """User B cannot delete User A's document."""
        res_del = self.client.delete(f"/api/documents/{self.doc_a_id}", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res_del.status_code, 404)

        # Verify doc still exists for User A
        res_check = self.client.get(f"/api/documents/{self.doc_a_id}/pages", headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(res_check.status_code, 200)

    def test_12_user_b_cannot_reprocess_user_a_document(self):
        """User B cannot trigger reprocessing on User A's document."""
        res_rep = self.client.post(f"/api/documents/{self.doc_a_id}/reprocess", headers={"Authorization": f"Bearer {self.token_b}"})
        self.assertEqual(res_rep.status_code, 404)

    def test_13_ask_myca_context_is_isolated(self):
        """User B asking advisory questions receives answers based only on User B's context."""
        res_b = self.client.post(
            "/api/ask",
            headers={"Authorization": f"Bearer {self.token_b}"},
            json={"query": "What was my salary or income last month?"}
        )
        self.assertEqual(res_b.status_code, 200)
        data_b = res_b.get_json()
        self.assertIn("enough information nahi hai", data_b["answer"])
        self.assertEqual(len(data_b["sources"]), 0)

        # User A has grounded context
        res_a = self.client.post(
            "/api/ask",
            headers={"Authorization": f"Bearer {self.token_a}"},
            json={"query": "What was my salary or income last month?"}
        )
        self.assertEqual(res_a.status_code, 200)
        data_a = res_a.get_json()
        self.assertIn("82,000", data_a["answer"])
        self.assertGreaterEqual(len(data_a["sources"]), 1)

    def test_14_user_cannot_spoof_via_query_or_body(self):
        """Passing another user's ID in body or query parameters must be ignored; session identity is authoritative."""
        # User B sends body with user_id = user_a
        res = self.client.post(
            "/api/ask",
            headers={"Authorization": f"Bearer {self.token_b}"},
            json={"query": "salary kitni hai?", "user_id": self.user_a, "tenant_id": self.user_a}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        # Must still evaluate under User B (no info), ignoring injected user_a
        self.assertIn("enough information nahi hai", data["answer"])

    def test_15_audit_log_captures_unauthorized_attempts(self):
        """Audit log records access denials and security events."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT event_type, user_id FROM audit_events WHERE event_type LIKE '%UNAUTHORIZED%' ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        self.assertGreater(len(rows), 0)

if __name__ == "__main__":
    unittest.main()
