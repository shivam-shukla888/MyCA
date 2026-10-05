"""
myCA AI Vision & Document Ingestion Pipeline.
Architecture:
USER -> PDF / PHOTO / MULTIPLE PHOTOS -> SECURE VALIDATION -> PRIVATE STORAGE ->
AI VISION UNDERSTANDING -> STRUCTURED EXTRACTION -> SCHEMA VALIDATION ->
DETERMINISTIC FINANCIAL ENGINE -> NORMALIZATION -> DEDUPLICATION -> PERSISTENCE ->
FINANCIAL PROFILE -> SOVEREIGN LEDGER UI / ASK MYCA.

Core Principles:
1. AI READS.
2. DETERMINISTIC ENGINE CALCULATES.
3. VALIDATION DECIDES WHETHER THE DATA IS TRUSTWORTHY.
4. AI EXTRACTION != VERIFICATION.
"""

import uuid
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from ..db import get_db
from ..security import DEFAULT_STORAGE
from ..audit import log_audit_event
from .validator import validate_uploaded_file, DocumentValidationError
from .duplicate import check_duplicate_document
from .vision import get_vision_provider, VisionProcessingStatus, VisionDocumentType
from ..financial.duplicate import detect_overlapping_transactions
from ..financial.calculations import compute_financial_profile_deterministic
from ..financial.money import to_decimal, format_inr
from ..financial.models import DataStatus

def process_document_pipeline(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    allow_duplicate: bool = False,
    doc_type_hint: Optional[str] = None,
    preferred_vision_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified end-to-end ingestion pipeline for PDFs and single photos (JPG, PNG, WEBP).
    """
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Step 1: Secure File Validation (Untrusted Input)
        val_result = validate_uploaded_file(file_bytes, filename)
        file_hash = val_result["file_hash"]
        num_pages = val_result["page_count"]
        file_size = val_result["file_size"]
        mime_type = val_result["mime_type"]

        # Step 2: Cost Control & Duplicate Check
        if not allow_duplicate:
            dup_check = check_duplicate_document(user_id, file_hash)
            if dup_check["is_duplicate"]:
                conn.close()
                log_audit_event(user_id, "DUPLICATE_UPLOAD_BLOCKED", dup_check["existing_document_id"], {
                    "filename": filename,
                    "file_hash": file_hash
                })
                return {
                    "success": False,
                    "is_duplicate": True,
                    "message": "Ye document pehle se add hai.",
                    "existing_document_id": dup_check["existing_document_id"],
                    "existing_filename": dup_check["existing_filename"],
                    "existing_status": dup_check["existing_status"],
                    "uploaded_at": dup_check["uploaded_at"]
                }

        # Step 3: Secure Private Storage Abstraction
        safe_filepath = DEFAULT_STORAGE.store_document(user_id, doc_id, filename, file_bytes)

        # Initial Document Record (UPLOADED)
        cursor.execute("""
            INSERT INTO documents (id, user_id, filename, file_path, file_hash, file_size, mime_type, num_pages, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'UPLOADED')
        """, (doc_id, user_id, filename, safe_filepath, file_hash, file_size, mime_type, num_pages))

        # Job Record
        cursor.execute("""
            INSERT INTO document_processing_jobs (id, document_id, user_id, step, status, progress_percent, message)
            VALUES (?, ?, ?, 'UPLOADED', 'RUNNING', 10, 'Document read ho raha hai...')
        """, (job_id, doc_id, user_id))
        conn.commit()

        log_audit_event(user_id, "DOCUMENT_UPLOADED", doc_id, {
            "filename": filename,
            "mime_type": mime_type,
            "file_size": file_size,
            "num_pages": num_pages
        })

        # Step 4: AI Vision Document Understanding
        cursor.execute("""
            UPDATE document_processing_jobs
            SET step = 'VISION_UNDERSTANDING', progress_percent = 35, message = 'AI document ko read kar raha hai...'
            WHERE id = ?
        """, (job_id,))
        cursor.execute("UPDATE documents SET status = 'PROCESSING' WHERE id = ?", (doc_id,))
        conn.commit()

        vision_provider = get_vision_provider(preferred_vision_provider)
        vision_result = vision_provider.analyze_document(file_bytes, mime_type, filename, doc_type_hint)

        # Record prompt injection audit if detected in document data
        if vision_result.prompt_injection_detected:
            log_audit_event(user_id, "PROMPT_INJECTION_DETECTED", doc_id, {
                "message": "Adversarial instructions in document ignored as inert data."
            })

        # Check Image Quality Assessment
        quality = vision_result.quality_assessment
        is_poor_quality = not quality.is_acceptable
        quality_message = quality.message

        classified_type = vision_result.document_type.lower()
        cursor.execute("UPDATE documents SET doc_type = ? WHERE id = ?", (classified_type, doc_id))

        # Record document page(s)
        pages_to_record = vision_result.pages_data if vision_result.pages_data else [
            {"page_number": 1, "raw_text": f"Document: {filename} [{classified_type}]", "has_images": True, "is_scanned": "image" in mime_type}
        ]
        for p_info in pages_to_record:
            page_id = f"pg_{uuid.uuid4().hex[:10]}"
            cursor.execute("""
                INSERT INTO document_pages (id, document_id, page_number, raw_text, has_images, is_scanned)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (page_id, doc_id, p_info["page_number"], p_info.get("raw_text", ""), int(p_info.get("has_images", True)), int(p_info.get("is_scanned", False))))

        num_pages = len(pages_to_record)
        cursor.execute("UPDATE documents SET num_pages = ? WHERE id = ?", (num_pages, doc_id))

        # Step 5: Schema Validation & Deterministic Financial Validation
        cursor.execute("""
            UPDATE document_processing_jobs
            SET step = 'VALIDATING', progress_percent = 70, message = 'Numbers check kiye ja rahe hain...'
            WHERE id = ?
        """, (job_id,))
        conn.commit()

        account = vision_result.account
        raw_txs = vision_result.transactions
        salary_rec = vision_result.salary_record
        tax_rec = vision_result.tax_record

        # Initial Status
        final_status = "READY"
        final_message = "Document ready hai."
        reconciliation_info: Dict[str, Any] = {
            "is_valid": True,
            "status": "READY",
            "discrepancy": 0.0,
            "message": "Document verified."
        }

        # Check if provider explicitly returned failure (e.g. timeout / outage)
        if vision_result.validation_status == VisionProcessingStatus.FAILED.value:
            final_status = "FAILED"
            final_message = vision_result.status_message
            reconciliation_info = {
                "is_valid": False,
                "status": "FAILED",
                "discrepancy": 0.0,
                "message": final_message
            }
        # Quality Gating Check
        elif is_poor_quality:
            final_status = "NEEDS_REVIEW"
            final_message = quality_message
            reconciliation_info = {
                "is_valid": False,
                "status": "NEEDS_REVIEW",
                "discrepancy": 0.0,
                "message": quality_message
            }

        elif classified_type in ("unknown", "unsupported", "receipt", "invoice", "credit_card_statement", "loan_statement", "demat_statement", "mutual_fund_statement"):
            if classified_type == "unknown":
                final_status = "UNSUPPORTED"
                final_message = "Ye document format abhi directly supported nahi hai."
            else:
                final_status = "UNSUPPORTED"
                final_message = f"Ye document format ({classified_type}) abhi directly supported nahi hai."
            reconciliation_info = {
                "is_valid": False,
                "status": "UNSUPPORTED",
                "discrepancy": 0.0,
                "message": final_message
            }

        elif classified_type == "bank_statement":
            # Deterministic reconciliation: Opening + Credits - Debits == Closing
            from ..financial.reconciliation import reconcile_bank_statement
            rec = reconcile_bank_statement(
                opening_balance_input=vision_result.opening_balance or Decimal('0.00'),
                closing_balance_input=vision_result.closing_balance or Decimal('0.00'),
                transactions=raw_txs
            )
            reconciliation_info = rec
            if not rec.get("is_valid", False):
                final_status = "NEEDS_REVIEW"
                final_message = f"Calculation mismatch: Discrepancy of {format_inr(to_decimal(rec.get('discrepancy', 0.0)))}."
            else:
                final_status = "READY"
                final_message = rec.get("message", "Bank statement verified.")

        elif classified_type == "salary_slip":
            # Deterministic check: Gross - Deductions == Net
            if salary_rec:
                gross = to_decimal(salary_rec.get("gross_salary", Decimal('0.00')))
                ded = to_decimal(salary_rec.get("total_deductions", Decimal('0.00')))
                net = to_decimal(salary_rec.get("net_salary", Decimal('0.00')))
                calc_net = gross - ded
                disc = abs(calc_net - net)

                is_valid = (disc == Decimal('0.00')) and (gross > Decimal('0.00'))
                final_status = "READY" if is_valid else "NEEDS_REVIEW"
                final_message = (
                    f"Salary slip verified: Gross {format_inr(gross)} - Deductions {format_inr(ded)} = Net {format_inr(net)}."
                    if is_valid
                    else f"Salary slip arithmetic mismatch: Discrepancy of {format_inr(disc)}."
                )
                reconciliation_info = {
                    "is_valid": is_valid,
                    "status": final_status,
                    "discrepancy": float(disc),
                    "message": final_message
                }
            else:
                final_status = "NEEDS_REVIEW"
                final_message = "Salary details complete nahi hain."

        elif classified_type == "form_16":
            # Deterministic check: Gross - Chapter VI-A == Taxable
            if tax_rec:
                gross = to_decimal(tax_rec.get("gross_salary", Decimal('0.00')))
                ded = to_decimal(tax_rec.get("deductions", Decimal('0.00')))
                taxable = to_decimal(tax_rec.get("taxable_income", Decimal('0.00')))
                calc_taxable = gross - ded
                disc = abs(calc_taxable - taxable) if taxable > Decimal('0.00') else Decimal('0.00')

                is_valid = (disc == Decimal('0.00')) and (gross > Decimal('0.00'))
                final_status = "READY" if is_valid else "NEEDS_REVIEW"
                final_message = (
                    f"Form 16 verified for AY {tax_rec.get('assessment_year', '2024-25')}."
                    if is_valid
                    else f"Form 16 arithmetic check flagged: Discrepancy of {format_inr(disc)}."
                )
                reconciliation_info = {
                    "is_valid": is_valid,
                    "status": final_status,
                    "discrepancy": float(disc),
                    "message": final_message
                }
            else:
                final_status = "NEEDS_REVIEW"
                final_message = "Form 16 details complete nahi hain."

        # Step 6: Deduplication & Persistence
        if account:
            acc_id = account.get("id") or f"acc_{uuid.uuid4().hex[:10]}"
            cursor.execute("""
                INSERT OR REPLACE INTO financial_accounts (
                    id, user_id, institution, account_type, masked_account_number,
                    opening_balance, closing_balance, currency, source_document_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                acc_id, user_id, account.get("bank_name", "Bank"),
                account.get("account_type", "Savings"),
                account.get("masked_account_number", "XXXX0000"),
                vision_result.opening_balance or 0.0,
                vision_result.closing_balance or 0.0,
                "INR", doc_id
            ))

        cursor.execute("SELECT fingerprint, id FROM transactions WHERE user_id = ? AND fingerprint IS NOT NULL", (user_id,))
        existing_fingerprints = {r["fingerprint"]: r["id"] for r in cursor.fetchall()}

        transactions = detect_overlapping_transactions(raw_txs, existing_fingerprints)

        for tx in transactions:
            tx_id = tx.get("id") or f"tx_{uuid.uuid4().hex[:12]}"
            cursor.execute("""
                INSERT INTO transactions (
                    id, user_id, account_id, date, date_iso, description, amount, type,
                    direction, category, balance, source_document_id, source_page, source_text,
                    status, confidence, fingerprint, duplicate_status, duplicate_of_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tx_id, user_id, tx.get("account_id"), tx["date"], tx.get("date_iso", tx["date"]),
                tx["description"], tx["amount"], tx["type"], tx.get("direction", tx["type"]),
                tx.get("category", "Miscellaneous"), tx.get("balance"), doc_id,
                tx.get("source_page", 1), tx.get("source_text", ""), final_status,
                tx.get("confidence", 1.0), tx.get("fingerprint"), tx.get("duplicate_status", "UNIQUE"),
                tx.get("duplicate_of_id")
            ))

        if salary_rec:
            sal_id = f"sal_{uuid.uuid4().hex[:10]}"
            cursor.execute("""
                INSERT INTO income_records (
                    id, user_id, source, date, amount, type, source_document_id, source_page, status
                ) VALUES (?, ?, ?, ?, ?, 'SALARY', ?, 1, ?)
            """, (
                sal_id, user_id, salary_rec.get("employer", "Employer"),
                salary_rec.get("pay_period", "Current Period"),
                salary_rec.get("net_salary", 0.0), doc_id, final_status
            ))

        if tax_rec:
            t_id = f"tax_{uuid.uuid4().hex[:10]}"
            cursor.execute("""
                INSERT INTO tax_documents (
                    id, user_id, doc_type, assessment_year, total_tax_paid, source_document_id
                ) VALUES (?, ?, 'form_16', ?, ?, ?)
            """, (
                t_id, user_id, tax_rec.get("assessment_year", "2024-25"),
                tax_rec.get("total_tax_paid", 0.0), doc_id
            ))

        # Record AI Extraction provenance
        ext_id = f"ext_{uuid.uuid4().hex[:10]}"
        cursor.execute("""
            INSERT INTO document_extractions (id, document_id, extraction_type, raw_data_json, confidence, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ext_id, doc_id, f"AI_VISION_{classified_type.upper()}",
            json.dumps({
                "provider": vision_result.provider_name,
                "model": vision_result.model_name,
                "confidence": vision_result.confidence,
                "quality_score": quality.score,
                "quality_issues": quality.issues,
                "transaction_count": len(transactions),
                "reconciliation": reconciliation_info
            }),
            vision_result.confidence,
            final_status
        ))

        # Scanned document review gating: never automatically verify scanned content as READY
        is_scanned_doc = vision_result.is_scanned or ("image" in mime_type)
        if is_scanned_doc and final_status == "READY":
            final_status = "NEEDS_REVIEW"
            final_message = "Scanned document read via local vision. Kripya numbers verify karein."

        # Update Document and Job final states
        cursor.execute("""
            UPDATE documents
            SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (final_status, final_message if final_status in ("NEEDS_REVIEW", "UNSUPPORTED") else None, doc_id))

        cursor.execute("""
            UPDATE document_processing_jobs
            SET step = 'COMPLETED', status = 'SUCCESS', progress_percent = 100, message = ?
            WHERE id = ?
        """, (final_message, job_id))

        conn.commit()

        log_audit_event(user_id, "DOCUMENT_PROCESSED_VISION", doc_id, {
            "status": final_status,
            "doc_type": classified_type,
            "provider": vision_result.provider_name,
            "model": vision_result.model_name,
            "quality_issues": quality.issues
        })

        # Recompute user's deterministic financial profile
        cursor.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        user_all_txs = [dict(r) for r in cursor.fetchall()]
        metrics = compute_financial_profile_deterministic(user_all_txs)

        conn.close()

        return {
            "success": True,
            "document_id": doc_id,
            "filename": filename,
            "status": final_status,
            "doc_type": classified_type,
            "message": final_message,
            "num_pages": num_pages,
            "is_scanned": is_scanned_doc,
            "quality": {
                "is_acceptable": quality.is_acceptable,
                "score": quality.score,
                "issues": quality.issues
            },
            "reconciliation": reconciliation_info,
            "metrics": metrics,
            "transaction_count": len(transactions),
            "transactions": transactions
        }

    except DocumentValidationError as dve:
        conn.rollback()
        conn.close()
        log_audit_event(user_id, "DOCUMENT_VALIDATION_FAILED", None, {
            "error_code": dve.code,
            "message": dve.message
        })
        return {
            "success": False,
            "error_code": dve.code,
            "message": dve.message,
            "can_retry": True
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        log_audit_event(user_id, "DOCUMENT_PROCESSING_FAILED", None, {
            "error": str(e)
        })
        return {
            "success": False,
            "error_code": "PROCESSING_ERROR",
            "message": f"Document processing mein error: {str(e)}",
            "can_retry": True
        }

def process_multi_image_document(
    files: List[Dict[str, Any]],  # each item: {"bytes": b"...", "filename": str, "mime_type": str}
    doc_title: str,
    user_id: str,
    allow_duplicate: bool = False,
    preferred_vision_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Combines multiple uploaded photos (Page 1, Page 2, Page 3) representing ONE financial document
    into a single consolidated document entity.
    """
    if not files or len(files) == 0:
        return {
            "success": False,
            "error_code": "EMPTY_FILE_LIST",
            "message": "Koi photo select nahi ki gayi."
        }

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    num_pages = len(files)
    total_size = sum(len(f["bytes"]) for f in files)

    # Combined hash of all images
    hasher = hashlib.sha256()
    for f in files:
        hasher.update(f["bytes"])
    composite_hash = hasher.hexdigest()

    conn = get_db()
    cursor = conn.cursor()

    try:
        if not allow_duplicate:
            dup_check = check_duplicate_document(user_id, composite_hash)
            if dup_check["is_duplicate"]:
                conn.close()
                return {
                    "success": False,
                    "is_duplicate": True,
                    "message": "Ye multi-photo document pehle se add hai.",
                    "existing_document_id": dup_check["existing_document_id"]
                }

        # Store primary document representation
        primary_file = files[0]
        safe_path = DEFAULT_STORAGE.store_document(user_id, doc_id, doc_title, primary_file["bytes"])

        cursor.execute("""
            INSERT INTO documents (id, user_id, filename, file_path, file_hash, file_size, mime_type, num_pages, status)
            VALUES (?, ?, ?, ?, ?, ?, 'image/composite', ?, 'UPLOADED')
        """, (doc_id, user_id, doc_title, safe_path, composite_hash, total_size, num_pages))

        # Store each page
        for idx, f in enumerate(files):
            page_num = idx + 1
            p_id = f"pg_{uuid.uuid4().hex[:10]}"
            cursor.execute("""
                INSERT INTO document_pages (id, document_id, page_number, raw_text, has_images, is_scanned)
                VALUES (?, ?, ?, ?, 1, 1)
            """, (p_id, doc_id, page_num, f"Photo {page_num}: {f['filename']}"))

        cursor.execute("""
            INSERT INTO document_processing_jobs (id, document_id, user_id, step, status, progress_percent, message)
            VALUES (?, ?, ?, 'VISION_MULTI_PAGE', 'RUNNING', 30, 'Multiple photos ko consolidate kiya ja raha hai...')
        """, (job_id, doc_id, user_id))
        conn.commit()

        # Dispatch to vision provider
        vision_provider = get_vision_provider(preferred_vision_provider)
        vision_pages = []
        for idx, f in enumerate(files):
            vision_pages.append({
                "page_num": idx + 1,
                "bytes": f["bytes"],
                "mime_type": f.get("mime_type", "image/jpeg"),
                "filename": f["filename"]
            })

        vision_result = vision_provider.analyze_multiple_pages(vision_pages)
        classified_type = vision_result.document_type.lower()
        cursor.execute("UPDATE documents SET doc_type = ? WHERE id = ?", (classified_type, doc_id))

        quality = vision_result.quality_assessment
        final_status = "READY" if quality.is_acceptable else "NEEDS_REVIEW"
        final_message = "Document ready hai." if quality.is_acceptable else quality.message

        account = vision_result.account
        raw_txs = vision_result.transactions

        # Deduplicate transactions
        cursor.execute("SELECT fingerprint, id FROM transactions WHERE user_id = ? AND fingerprint IS NOT NULL", (user_id,))
        existing_fps = {r["fingerprint"]: r["id"] for r in cursor.fetchall()}
        transactions = detect_overlapping_transactions(raw_txs, existing_fps)

        for tx in transactions:
            tx_id = tx.get("id") or f"tx_{uuid.uuid4().hex[:12]}"
            cursor.execute("""
                INSERT INTO transactions (
                    id, user_id, account_id, date, date_iso, description, amount, type,
                    direction, category, balance, source_document_id, source_page, source_text,
                    status, confidence, fingerprint, duplicate_status, duplicate_of_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tx_id, user_id, tx.get("account_id"), tx["date"], tx.get("date_iso", tx["date"]),
                tx["description"], tx["amount"], tx["type"], tx.get("direction", tx["type"]),
                tx.get("category", "Miscellaneous"), tx.get("balance"), doc_id,
                tx.get("source_page", 1), tx.get("source_text", ""), final_status,
                tx.get("confidence", 1.0), tx.get("fingerprint"), tx.get("duplicate_status", "UNIQUE"),
                tx.get("duplicate_of_id")
            ))

        cursor.execute("""
            UPDATE documents
            SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (final_status, final_message if final_status == "NEEDS_REVIEW" else None, doc_id))

        cursor.execute("""
            UPDATE document_processing_jobs
            SET step = 'COMPLETED', status = 'SUCCESS', progress_percent = 100, message = ?
            WHERE id = ?
        """, (final_message, job_id))

        conn.commit()

        # Recompute profile
        cursor.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        user_all_txs = [dict(r) for r in cursor.fetchall()]
        metrics = compute_financial_profile_deterministic(user_all_txs)

        conn.close()

        return {
            "success": True,
            "document_id": doc_id,
            "filename": doc_title,
            "status": final_status,
            "doc_type": classified_type,
            "num_pages": num_pages,
            "message": final_message,
            "quality": {
                "is_acceptable": quality.is_acceptable,
                "score": quality.score,
                "issues": quality.issues
            },
            "transaction_count": len(transactions),
            "transactions": transactions,
            "metrics": metrics
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {
            "success": False,
            "error_code": "MULTI_IMAGE_PROCESSING_ERROR",
            "message": f"Multi-photo processing mein error: {str(e)}"
        }

def process_pdf_document(file_bytes: bytes, filename: str, user_id: str, allow_duplicate: bool = False):
    """
    Backwards-compatible wrapper preserving existing Phase 2 & 3 test contracts.
    """
    return process_document_pipeline(file_bytes, filename, user_id, allow_duplicate=allow_duplicate)
