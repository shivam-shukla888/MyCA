import os
import json
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from .db import get_db, init_db
from .security import (
    require_auth,
    create_session_token,
    create_signed_doc_token,
    verify_signed_doc_token,
    verify_session_token,
    DEFAULT_STORAGE
)
from .audit import log_audit_event
from .ingestion.pipeline import process_pdf_document
from .financial.calculations import compute_financial_profile_deterministic
from .knowledge.tax_registry import get_current_rules_for_ay, get_statutory_rule, seed_statutory_rules
from .knowledge.tax_calculator import calculate_new_regime_tax, calculate_old_regime_tax
from .advisory import GroundedAdvisoryEngine

app = Flask(__name__, static_folder="../static", static_url_path="")
CORS(app)

_advisory_engine = GroundedAdvisoryEngine()

# ================= AUTHENTICATION & SESSION MANAGEMENT =================
@app.route("/api/auth/token", methods=["POST"])
def issue_session_token():
    """
    Issues a cryptographically signed HMAC-SHA256 session token.
    Enforces identity boundary without client header spoofing.
    """
    data = request.json or {}
    requested_user = data.get("user_id", "usr_aarav_01").strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role FROM users WHERE id = ?", (requested_user,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        log_audit_event("anonymous", "AUTH_LOGIN_FAILED", None, {"requested_user": requested_user})
        return jsonify({"error": "User does not exist", "code": "USER_NOT_FOUND"}), 404

    token = create_session_token(user["id"])
    log_audit_event(user["id"], "AUTH_LOGIN_SUCCESS", None, {"email": user["email"]})

    return jsonify({
        "success": True,
        "token": token,
        "user": dict(user)
    })

# ================= USER PROFILE & FINANCIAL SUMMARY =================
def _get_user_financial_profile(user_id: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None

    # Fetch user transactions (Strict tenant isolation)
    cursor.execute("""
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    tx_rows = [dict(r) for r in cursor.fetchall()]

    # Fetch user accounts
    cursor.execute("""
        SELECT * FROM financial_accounts
        WHERE user_id = ?
    """, (user_id,))
    accounts = [dict(r) for r in cursor.fetchall()]

    # Fetch documents count & status
    cursor.execute("""
        SELECT status, count(*) as count
        FROM documents
        WHERE user_id = ?
        GROUP BY status
    """, (user_id,))
    doc_counts = {r["status"]: r["count"] for r in cursor.fetchall()}

    conn.close()

    has_data = len(tx_rows) > 0
    if has_data:
        metrics = compute_financial_profile_deterministic(tx_rows)
    else:
        metrics = {
            "monthly_income": "Unknown",
            "monthly_expenses": "Unknown",
            "monthly_savings": "Unknown",
            "savings_rate": 0,
            "categories": [],
            "top_expenses": {
                "rent": 0,
                "food": 0,
                "shopping": 0,
                "loans": 0
            },
            "next_step": {
                "title": "Document Upload Karein",
                "description": "Apna pehla bank statement upload karein taaki myCA aapka real financial profile generate kar sake.",
                "action_label": "Upload",
                "action_payload": {"type": "UPLOAD_TRIGGER"}
            }
        }

    return {
        "user": dict(user),
        "has_data": has_data,
        "metrics": metrics,
        "accounts": accounts,
        "doc_counts": doc_counts
    }

@app.route("/api/user/profile", methods=["GET"])
@require_auth
def get_user_profile():
    profile = _get_user_financial_profile(g.user_id)
    if not profile:
        return jsonify({"error": "User not found"}), 404
    return jsonify(profile)

# API Contract Alias: GET /api/financial/summary
@app.route("/api/financial/summary", methods=["GET"])
@require_auth
def get_financial_summary_contract():
    profile = _get_user_financial_profile(g.user_id)
    if not profile:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "user": profile["user"],
        "summary": profile["metrics"],
        "metrics": profile["metrics"],
        "has_data": profile["has_data"],
        "accounts_count": len(profile["accounts"])
    })

# ================= DOCUMENTS API =================
@app.route("/api/documents", methods=["GET"])
@require_auth
def list_documents():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, filename, file_size, num_pages, doc_type, status, error_message, created_at
        FROM documents
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (g.user_id,))
    docs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"documents": docs, "total": len(docs)})

def _handle_document_upload(user_id: str):
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Koi file upload nahi ki gayi.", "can_retry": True}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "File select nahi ki gayi.", "can_retry": True}), 400

    filename = file.filename
    allow_dup = request.form.get("allow_duplicate", "false").lower() == "true"
    file_bytes = file.read()

    result = process_pdf_document(file_bytes, filename, user_id, allow_duplicate=allow_dup)
    status_code = 200 if result.get("success", False) or result.get("is_duplicate", False) else 400
    return jsonify(result), status_code

@app.route("/api/documents/upload", methods=["POST"])
@require_auth
def upload_document_legacy():
    return _handle_document_upload(g.user_id)

# API Contract Blueprint: POST /api/documents
@app.route("/api/documents", methods=["POST"])
@require_auth
def upload_document_contract():
    return _handle_document_upload(g.user_id)

@app.route("/api/documents/upload-multiple", methods=["POST"])
@require_auth
def upload_multiple_photos():
    """
    Combines multiple uploaded photos representing ONE financial document.
    """
    files = request.files.getlist("files") or request.files.getlist("files[]")
    if not files:
        return jsonify({"success": False, "message": "Koi photos select nahi ki gayi.", "can_retry": True}), 400

    doc_title = request.form.get("title", f"Multi-Photo Document ({len(files)} pages)")
    allow_dup = request.form.get("allow_duplicate", "false").lower() == "true"

    prepared_files = []
    for f in files:
        if f.filename != '':
            prepared_files.append({
                "bytes": f.read(),
                "filename": f.filename,
                "mime_type": f.mimetype or "image/jpeg"
            })

    if not prepared_files:
        return jsonify({"success": False, "message": "Valid photos nahi mili.", "can_retry": True}), 400

    from .ingestion.pipeline import process_multi_image_document
    result = process_multi_image_document(prepared_files, doc_title, g.user_id, allow_duplicate=allow_dup)
    status_code = 200 if result.get("success", False) or result.get("is_duplicate", False) else 400
    return jsonify(result), status_code

@app.route("/api/documents/<doc_id>/confirm", methods=["POST"])
@require_auth
def confirm_document_review_endpoint(doc_id):
    """
    Allows user to review, confirm, or provide corrections for a document in NEEDS_REVIEW.
    Sets status to READY or USER_CONFIRMED.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ? AND user_id = ?", (doc_id, g.user_id))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        return jsonify({"error": "Document not found"}), 404

    cursor.execute("""
        UPDATE documents
        SET status = 'READY', error_message = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (doc_id,))

    cursor.execute("""
        UPDATE transactions
        SET status = 'USER_CONFIRMED'
        WHERE source_document_id = ? AND user_id = ?
    """, (doc_id, g.user_id))

    conn.commit()
    conn.close()

    log_audit_event(g.user_id, "DOCUMENT_USER_CONFIRMED", doc_id)
    return jsonify({"success": True, "message": "Document confirmed by user.", "status": "READY"})

@app.route("/api/documents/<doc_id>", methods=["GET"])
@require_auth
def get_document_details(doc_id):
    conn = get_db()
    cursor = conn.cursor()

    # Strict multi-tenant authorization
    cursor.execute("SELECT * FROM documents WHERE id = ? AND user_id = ?", (doc_id, g.user_id))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        log_audit_event(g.user_id, "UNAUTHORIZED_DOCUMENT_ACCESS", doc_id, {"action": "view_details"})
        return jsonify({"error": "Document not found or unauthorized access"}), 404

    # Pages
    cursor.execute("SELECT id, page_number, is_scanned, has_images FROM document_pages WHERE document_id = ? ORDER BY page_number ASC", (doc_id,))
    pages = [dict(r) for r in cursor.fetchall()]

    # Transactions for this document
    cursor.execute("SELECT * FROM transactions WHERE source_document_id = ? AND user_id = ? ORDER BY date ASC", (doc_id, g.user_id))
    transactions = [dict(r) for r in cursor.fetchall()]

    # Income records for this document
    cursor.execute("SELECT * FROM income_records WHERE source_document_id = ? AND user_id = ?", (doc_id, g.user_id))
    income_records = [dict(r) for r in cursor.fetchall()]

    # Tax records for this document
    cursor.execute("SELECT * FROM tax_documents WHERE source_document_id = ? AND user_id = ?", (doc_id, g.user_id))
    tax_records = [dict(r) for r in cursor.fetchall()]

    # Extractions for this document
    cursor.execute("SELECT * FROM document_extractions WHERE document_id = ? ORDER BY created_at DESC", (doc_id,))
    extractions = [dict(r) for r in cursor.fetchall()]

    # Jobs
    cursor.execute("SELECT * FROM document_processing_jobs WHERE document_id = ? ORDER BY created_at ASC", (doc_id,))
    jobs = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "document": dict(doc),
        "pages": pages,
        "transactions": transactions,
        "income_records": income_records,
        "tax_records": tax_records,
        "extractions": extractions,
        "jobs": jobs
    })

@app.route("/api/documents/<doc_id>/pages", methods=["GET"])
@require_auth
def get_document_pages(doc_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM documents WHERE id = ? AND user_id = ?", (doc_id, g.user_id))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        log_audit_event(g.user_id, "UNAUTHORIZED_DOCUMENT_PAGES_ACCESS", doc_id)
        return jsonify({"error": "Document not found or unauthorized access"}), 404

    cursor.execute("SELECT * FROM document_pages WHERE document_id = ? ORDER BY page_number ASC", (doc_id,))
    pages = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"document_id": doc_id, "pages": pages, "total": len(pages)})

# Signed Access URL generation endpoint
@app.route("/api/documents/<doc_id>/signed-url", methods=["GET"])
@require_auth
def get_signed_document_url(doc_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM documents WHERE id = ? AND user_id = ?", (doc_id, g.user_id))
    doc = cursor.fetchone()
    conn.close()

    if not doc:
        log_audit_event(g.user_id, "UNAUTHORIZED_SIGNED_URL_REQUEST", doc_id)
        return jsonify({"error": "Unauthorized"}), 404

    token = create_signed_doc_token(doc_id, g.user_id, expires_in=300)
    signed_url = f"/api/documents/{doc_id}/file?token={token}"
    return jsonify({
        "success": True,
        "signed_url": signed_url,
        "token": token,
        "expires_in_seconds": 300
    })

@app.route("/api/documents/<doc_id>/file", methods=["GET"])
def stream_document_file(doc_id):
    """
    Streams private document bytes.
    Requires either:
    1. A valid, unexpired short-lived signed access token (?token=...)
    OR
    2. A valid Bearer session token identifying the document owner.
    """
    token = request.args.get("token", "").strip()
    session_user_id = None

    # Check Bearer auth header if present
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            session_user_id = verify_session_token(auth_header[7:].strip())
        except ValueError:
            pass

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, filename, user_id FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    conn.close()

    if not doc:
        return jsonify({"error": "Document not found"}), 404

    doc_owner = doc["user_id"]

    # Authorization Check
    authorized = False
    if session_user_id and session_user_id == doc_owner:
        authorized = True
    elif token and verify_signed_doc_token(token, doc_id, doc_owner):
        authorized = True

    if not authorized:
        log_audit_event(session_user_id or "anonymous", "DOCUMENT_STREAM_REJECTED", doc_id)
        if not session_user_id and not token:
            return jsonify({"error": "Authentication required to access document"}), 401
        if token and not verify_signed_doc_token(token, doc_id, doc_owner):
            return jsonify({"error": "Invalid or expired document access token"}), 401
        # When authenticated as User B trying to access User A's doc, return 404 to avoid enumeration
        return jsonify({"error": "Document not found"}), 404

    file_path = doc["file_path"]
    if not os.path.exists(file_path):
        return jsonify({"error": "File storage missing"}), 404

    log_audit_event(doc_owner, "DOCUMENT_VIEWED", doc_id, {"filename": doc["filename"]})
    return send_file(file_path, mimetype="application/pdf", download_name=doc["filename"], as_attachment=False)

def _reprocess_document_handler(doc_id: str, user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, filename FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id))
    doc = cursor.fetchone()
    conn.close()

    if not doc:
        return jsonify({"error": "Document not found or unauthorized"}), 404

    with open(doc["file_path"], "rb") as f:
        file_bytes = f.read()

    # Delete existing transactions and re-run with allow_duplicate
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE source_document_id = ?", (doc_id,))
    c.execute("DELETE FROM income_records WHERE source_document_id = ?", (doc_id,))
    c.execute("DELETE FROM expense_records WHERE source_document_id = ?", (doc_id,))
    c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    result = process_pdf_document(file_bytes, doc["filename"], user_id, allow_duplicate=True)
    log_audit_event(user_id, "DOCUMENT_REPROCESSED", doc_id)
    return jsonify(result)

@app.route("/api/documents/<doc_id>/reprocess", methods=["POST"])
@require_auth
def reprocess_document(doc_id):
    return _reprocess_document_handler(doc_id, g.user_id)

# API Contract Blueprint: POST /api/documents/:id/process
@app.route("/api/documents/<doc_id>/process", methods=["POST"])
@require_auth
def process_document_contract(doc_id):
    return _reprocess_document_handler(doc_id, g.user_id)

@app.route("/api/documents/<doc_id>", methods=["DELETE"])
@require_auth
def delete_document(doc_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, filename FROM documents WHERE id = ? AND user_id = ?", (doc_id, g.user_id))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        log_audit_event(g.user_id, "UNAUTHORIZED_DELETE_ATTEMPT", doc_id)
        return jsonify({"error": "Document not found or unauthorized"}), 404

    file_path = doc["file_path"]
    cursor.execute("DELETE FROM documents WHERE id = ? AND user_id = ?", (doc_id, g.user_id))
    conn.commit()
    conn.close()

    DEFAULT_STORAGE.delete_document(file_path)
    log_audit_event(g.user_id, "DOCUMENT_DELETED", doc_id, {"filename": doc["filename"]})

    return jsonify({"success": True, "message": "Document deleted successfully."})

# ================= TRANSACTIONS & ACCOUNTS API =================
def _fetch_transactions_list(user_id: str):
    search = request.args.get("search", "").lower().strip()
    category = request.args.get("category", "").strip()
    tx_type = request.args.get("type", "").upper().strip()

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT t.*, d.filename as document_name
        FROM transactions t
        LEFT JOIN documents d ON t.source_document_id = d.id
        WHERE t.user_id = ?
    """
    params = [user_id]

    if search:
        query += " AND (LOWER(t.description) LIKE ? OR LOWER(t.category) LIKE ? OR LOWER(t.source_text) LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if category and category != "All":
        query += " AND t.category = ?"
        params.append(category)

    if tx_type and tx_type != "ALL":
        query += " AND t.type = ?"
        params.append(tx_type)

    query += " ORDER BY t.date DESC"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.route("/api/transactions", methods=["GET"])
@require_auth
def get_transactions():
    rows = _fetch_transactions_list(g.user_id)
    return jsonify({"transactions": rows})

# API Contract Blueprint: GET /api/financial/transactions
@app.route("/api/financial/transactions", methods=["GET"])
@require_auth
def get_financial_transactions_contract():
    rows = _fetch_transactions_list(g.user_id)
    return jsonify({"transactions": rows, "count": len(rows), "total": len(rows)})

@app.route("/api/transactions/<tx_id>/category", methods=["PATCH"])
@require_auth
def update_transaction_category(tx_id):
    data = request.json or {}
    new_cat = data.get("category", "").strip()
    if not new_cat:
        return jsonify({"error": "Category required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE transactions
        SET category = ?, status = 'USER_CONFIRMED'
        WHERE id = ? AND user_id = ?
    """, (new_cat, tx_id, g.user_id))
    modified = cursor.rowcount
    conn.commit()
    conn.close()

    if modified == 0:
        log_audit_event(g.user_id, "UNAUTHORIZED_CATEGORY_UPDATE_ATTEMPT", tx_id)
        return jsonify({"error": "Transaction not found or unauthorized", "success": False}), 404

    log_audit_event(g.user_id, "CATEGORY_UPDATED", tx_id, {"new_category": new_cat})
    return jsonify({"success": True, "message": "Category updated."})

def _fetch_accounts_list(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, d.filename as source_document_name
        FROM financial_accounts a
        LEFT JOIN documents d ON a.source_document_id = d.id
        WHERE a.user_id = ?
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.route("/api/accounts", methods=["GET"])
@require_auth
def get_accounts():
    rows = _fetch_accounts_list(g.user_id)
    return jsonify({"accounts": rows, "total": len(rows)})

# API Contract Blueprint: GET /api/financial/accounts
@app.route("/api/financial/accounts", methods=["GET"])
@require_auth
def get_financial_accounts_contract():
    rows = _fetch_accounts_list(g.user_id)
    return jsonify({"accounts": rows, "total": len(rows)})

# ================= ASK myCA ADVISORY ENGINE =================
def _execute_advisory_inquiry(user_id: str, query: str):
    res = _advisory_engine.ask(user_id, query)
    return res.to_dict()

@app.route("/api/advisory/ask", methods=["POST"])
@require_auth
def ask_myca_advisory():
    data = request.json or {}
    query = (data.get("query") or "").strip()
    res = _execute_advisory_inquiry(g.user_id, query)
    return jsonify(res)

# API Contract Blueprint: POST /api/ask
@app.route("/api/ask", methods=["POST"])
@require_auth
def ask_myca_contract():
    data = request.json or {}
    query = (data.get("query") or "").strip()
    res = _execute_advisory_inquiry(g.user_id, query)
    return jsonify(res)

@app.route("/api/advisory/tax-estimate", methods=["GET"])
@require_auth
def get_tax_estimate_endpoint():
    ay = request.args.get("ay", "2025-26").strip()
    gross = request.args.get("gross")
    if gross:
        try:
            gross_val = float(gross)
        except ValueError:
            return jsonify({"error": "Invalid gross income format"}), 400
    else:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT amount FROM income_records
            WHERE user_id = ? AND status IN ('READY', 'VERIFIED_FROM_DOCUMENT', 'USER_CONFIRMED') AND amount > 0
            ORDER BY created_at DESC LIMIT 1
        """, (g.user_id,))
        row = cursor.fetchone()
        if row:
            gross_val = float(row["amount"]) * 12.0
        else:
            cursor.execute("SELECT amount FROM transactions WHERE user_id = ? AND type = 'CREDIT' AND (category = 'Salary' OR description LIKE '%salary%') ORDER BY date DESC LIMIT 1", (g.user_id,))
            s_row = cursor.fetchone()
            gross_val = float(s_row["amount"]) * 12.0 if s_row else 0.0
        conn.close()

    if gross_val <= 0:
        return jsonify({
            "has_data": False,
            "message": "Verified income data not available. Upload a salary slip or Form 16."
        })

    tax_res = calculate_new_regime_tax(gross_val, assessment_year=ay)
    return jsonify({
        "has_data": True,
        "assessment_year": ay,
        "gross_income": float(tax_res.gross_income),
        "standard_deduction": float(tax_res.standard_deduction),
        "taxable_income": float(tax_res.taxable_income),
        "slab_tax": float(tax_res.slab_tax),
        "rebate_87a": float(tax_res.rebate_87a),
        "tax_after_rebate": float(tax_res.tax_after_rebate),
        "cess_4_percent": float(tax_res.cess_4_percent),
        "total_tax_payable": float(tax_res.total_tax_payable),
        "effective_rate_percent": float(tax_res.effective_rate_percent),
        "rule_reference": tax_res.rule_reference,
        "disclaimer": tax_res.disclaimer
    })

# ================= VERSIONED STATUTORY TAX RULES API =================
@app.route("/api/statutory/rules", methods=["GET"])
@require_auth
def get_statutory_rules_endpoint():
    ay = request.args.get("ay", "2025-26").strip()
    rules = get_current_rules_for_ay(ay)
    return jsonify({"assessment_year": ay, "rules": rules})

# ================= INITIAL SEED =================
def seed_default_hdfc_statement_if_empty():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) as count FROM documents WHERE user_id = 'usr_aarav_01'")
    row = cursor.fetchone()
    conn.close()

    if row["count"] == 0:
        pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "uploads", "HDFC_Bank_Statement_Oct2024.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                process_pdf_document(f.read(), "HDFC_Bank_Statement_Oct2024.pdf", "usr_aarav_01", allow_duplicate=True)

# Main route serves index.html
@app.route("/")
def serve_index():
    return send_file(os.path.join(app.static_folder, "index.html"))

if __name__ == "__main__":
    init_db()
    seed_statutory_rules()
    seed_default_hdfc_statement_if_empty()
    app.run(host="127.0.0.1", port=5000, debug=True)
