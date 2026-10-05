import os
import hmac
import hashlib
import time
import secrets
from functools import wraps
from flask import request, jsonify, g
from abc import ABC, abstractmethod

# Secret Key Management
SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", ".secret_key")

def get_server_secret() -> bytes:
    env_secret = os.environ.get("MYCA_SECRET_KEY")
    if env_secret:
        return env_secret.encode("utf-8")
    
    os.makedirs(os.path.dirname(SECRET_FILE), exist_ok=True)
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "rb") as f:
            return f.read().strip()
    else:
        new_secret = secrets.token_bytes(32)
        with open(SECRET_FILE, "wb") as f:
            f.write(new_secret)
        return new_secret

SERVER_SECRET = get_server_secret()

# ================= CRYPTOGRAPHIC SESSION TOKENS =================
# Format: <user_id>.<timestamp>.<hmac_signature>
SESSION_VALIDITY_SECONDS = 86400 * 7  # 7 days

def create_session_token(user_id: str) -> str:
    """Generate a tamper-proof HMAC-SHA256 signed session token."""
    ts = str(int(time.time()))
    payload = f"{user_id}.{ts}".encode("utf-8")
    sig = hmac.new(SERVER_SECRET, payload, hashlib.sha256).hexdigest()
    return f"{user_id}.{ts}.{sig}"

def verify_session_token(token: str) -> str:
    """
    Verifies token signature and expiration.
    Returns user_id if valid; raises ValueError if invalid or expired.
    """
    if not token or not isinstance(token, str):
        raise ValueError("Missing session token")
    
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed session token")
    
    user_id, ts_str, sig = parts
    try:
        ts = int(ts_str)
    except ValueError:
        raise ValueError("Invalid session timestamp")
    
    now = int(time.time())
    if now - ts > SESSION_VALIDITY_SECONDS or ts > now + 300:
        raise ValueError("Session token expired")
    
    payload = f"{user_id}.{ts_str}".encode("utf-8")
    expected_sig = hmac.new(SERVER_SECRET, payload, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Invalid session signature")
    
    return user_id

# ================= SIGNED SHORT-LIVED DOCUMENT ACCESS TOKENS =================
# Format: <doc_id>.<user_id>.<expires_at>.<hmac_signature>
DOC_ACCESS_VALIDITY_SECONDS = 300  # 5 minutes

def create_signed_doc_token(doc_id: str, user_id: str, expires_in: int = DOC_ACCESS_VALIDITY_SECONDS) -> str:
    """Generate a tamper-proof short-lived signed token for private document streaming."""
    exp = str(int(time.time()) + expires_in)
    payload = f"{doc_id}.{user_id}.{exp}".encode("utf-8")
    sig = hmac.new(SERVER_SECRET, payload, hashlib.sha256).hexdigest()
    return f"{doc_id}.{user_id}.{exp}.{sig}"

def verify_signed_doc_token(token: str, expected_doc_id: str, expected_user_id: str) -> bool:
    """Verifies that the signed document token is valid, unexpired, and belongs to the requested document and user."""
    if not token or not isinstance(token, str):
        return False
    
    parts = token.split(".")
    if len(parts) != 4:
        return False
    
    doc_id, user_id, exp_str, sig = parts
    if doc_id != expected_doc_id or user_id != expected_user_id:
        return False
    
    try:
        exp = int(exp_str)
    except ValueError:
        return False
    
    if int(time.time()) > exp:
        return False  # Expired
    
    payload = f"{doc_id}.{user_id}.{exp_str}".encode("utf-8")
    expected_sig = hmac.new(SERVER_SECRET, payload, hashlib.sha256).hexdigest()
    
    return hmac.compare_digest(sig, expected_sig)

# ================= AUTHENTICATION DECORATOR =================
def require_auth(f):
    """
    Enforces authentication on API endpoints.
    Resolves identity exclusively from verified session tokens.
    Never trusts request body, query params, or client headers.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif "myca_session" in request.cookies:
            token = request.cookies.get("myca_session")
        elif request.headers.get("X-Session-Token"):
            token = request.headers.get("X-Session-Token").strip()

        if not token:
            return jsonify({
                "error": "Authentication required",
                "code": "AUTH_REQUIRED",
                "message": "Aapka session invalid ya expired hai. Please log in karein."
            }), 401

        try:
            user_id = verify_session_token(token)
            g.user_id = user_id
            g.session_token = token
        except ValueError as e:
            return jsonify({
                "error": "Invalid or expired session",
                "code": "INVALID_TOKEN",
                "message": str(e)
            }), 401

        return f(*args, **kwargs)
    return decorated

# ================= DOCUMENT STORAGE ABSTRACTION =================
class DocumentStorageInterface(ABC):
    @abstractmethod
    def store_document(self, user_id: str, doc_id: str, filename: str, data: bytes) -> str:
        """Stores file bytes privately and returns storage path / key."""
        pass

    @abstractmethod
    def retrieve_document(self, storage_key: str) -> bytes:
        """Retrieves raw bytes from private storage."""
        pass

    @abstractmethod
    def delete_document(self, storage_key: str) -> bool:
        """Deletes document from storage."""
        pass

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Checks document existence."""
        pass

class LocalPrivateStorage(DocumentStorageInterface):
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)

    def _get_user_dir(self, user_id: str) -> str:
        # Prevent path traversal
        clean_user = "".join(c for c in user_id if c.isalnum() or c in ("_", "-"))
        path = os.path.join(self.base_dir, clean_user)
        os.makedirs(path, exist_ok=True)
        return path

    def store_document(self, user_id: str, doc_id: str, filename: str, data: bytes) -> str:
        user_dir = self._get_user_dir(user_id)
        clean_filename = "".join(c for c in os.path.basename(filename) if c.isalnum() or c in (".", "_", "-", " "))
        safe_name = f"{doc_id}_{clean_filename}"
        full_path = os.path.join(user_dir, safe_name)
        with open(full_path, "wb") as f:
            f.write(data)
        return full_path

    def retrieve_document(self, storage_key: str) -> bytes:
        if not os.path.exists(storage_key):
            raise FileNotFoundError("Document not found in storage")
        with open(storage_key, "rb") as f:
            return f.read()

    def delete_document(self, storage_key: str) -> bool:
        if os.path.exists(storage_key):
            try:
                os.remove(storage_key)
                return True
            except OSError:
                return False
        return False

    def exists(self, storage_key: str) -> bool:
        return os.path.exists(storage_key)

# Global Storage Instance
DEFAULT_STORAGE = LocalPrivateStorage(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "uploads")
)
