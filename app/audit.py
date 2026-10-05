import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request
from .db import get_db

def sanitize_audit_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strips raw sensitive content (passwords, tokens, raw file contents, full account numbers)
    from audit records to prevent log poisoning or PII leaks.
    """
    clean = {}
    for k, v in details.items():
        k_lower = k.lower()
        if any(term in k_lower for term in ["password", "secret", "token", "raw_bytes", "file_bytes"]):
            clean[k] = "[REDACTED]"
        elif "account_number" in k_lower and isinstance(v, str):
            clean[k] = f"XXXX{v[-4:]}" if len(v) >= 4 else "XXXX"
        elif isinstance(v, (str, int, float, bool, list, dict)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean

def log_audit_event(
    user_id: str,
    event_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """
    Appends a security audit event to the persistent audit_events ledger.
    """
    clean_details = sanitize_audit_details(details or {})
    event_id = f"aud_{uuid.uuid4().hex[:12]}"
    
    if not ip_address and request:
        try:
            ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        except Exception:
            ip_address = "127.0.0.1"

    try:
        conn = get_db()
        cursor = conn.cursor()
        # Ensure user exists for foreign key constraint or insert fallback
        if user_id in ["anonymous", "system"]:
            cursor.execute("INSERT OR IGNORE INTO users (id, name, email, role) VALUES (?, ?, ?, 'system')",
                           (user_id, user_id.capitalize(), f"{user_id}@sovereign.local"))
        cursor.execute("""
            INSERT INTO audit_events (id, user_id, event_type, resource_id, details_json, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            user_id,
            event_type,
            resource_id,
            json.dumps(clean_details),
            ip_address or "127.0.0.1"
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        # Fallback console warning without crashing primary thread
        print(f"[AUDIT LOGGING ERROR]: {e}")
