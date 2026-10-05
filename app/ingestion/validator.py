import os
import io
import hashlib
import fitz  # PyMuPDF
from PIL import Image

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

class DocumentValidationError(Exception):
    def __init__(self, message, code="INVALID_DOCUMENT"):
        super().__init__(message)
        self.message = message
        self.code = code

def calculate_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def detect_file_mime_type(file_bytes: bytes, filename: str = "") -> str:
    """Detects MIME type from magic bytes and filename."""
    if file_bytes.startswith(b'%PDF-'):
        return "application/pdf"
    elif file_bytes.startswith(b'\xff\xd8\xff'):
        return "image/jpeg"
    elif file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image/png"
    elif file_bytes.startswith(b'RIFF') and b'WEBP' in file_bytes[:16]:
        return "image/webp"

    fn = filename.lower()
    if fn.endswith('.pdf'):
        return "application/pdf"
    elif fn.endswith(('.jpg', '.jpeg')):
        return "image/jpeg"
    elif fn.endswith('.png'):
        return "image/png"
    elif fn.endswith('.webp'):
        return "image/webp"

    return "application/octet-stream"

def validate_uploaded_file(file_bytes: bytes, filename: str, client_mime: str = ""):
    """
    Validates file type (PDF, JPG, PNG, WEBP), size, magic bytes, and integrity.
    Never trusts client filename or client-provided MIME type alone.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise DocumentValidationError("Ye document khali hai (empty file). Please review karein.", "EMPTY_FILE")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise DocumentValidationError(f"File size limit exceeds 25MB (Current: {len(file_bytes) / (1024*1024):.1f}MB).", "FILE_TOO_LARGE")

    detected_mime = detect_file_mime_type(file_bytes, filename)

    if detected_mime == "application/pdf":
        if not file_bytes.startswith(b'%PDF-'):
            raise DocumentValidationError("Ye document read nahi ho pa raha. (Invalid PDF header).", "CORRUPTED_PDF")

        # Readability and page check using PyMuPDF
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception:
            raise DocumentValidationError("Ye document read nahi ho pa raha. File corrupted ho sakti hai.", "CORRUPTED_PDF")

        try:
            if doc.is_encrypted:
                raise DocumentValidationError("Ye PDF password protected hai. Please bina password wala document upload karein.", "PASSWORD_PROTECTED")

            page_count = len(doc)
            if page_count < 1:
                raise DocumentValidationError("Ye document read nahi ho pa raha. Zero pages found.", "ZERO_PAGES")
        finally:
            doc.close()

    elif detected_mime in ("image/jpeg", "image/png", "image/webp"):
        try:
            im = Image.open(io.BytesIO(file_bytes))
            im.verify()
            page_count = 1
        except Exception:
            raise DocumentValidationError("Ye photo read nahi ho pa rahi. File corrupted ho sakti hai.", "CORRUPTED_IMAGE")
    else:
        raise DocumentValidationError("Ye file format supported nahi hai. Kripya PDF ya image (JPG, PNG, WEBP) upload karein.", "CORRUPTED_PDF")

    file_hash = calculate_sha256(file_bytes)

    return {
        "valid": True,
        "page_count": page_count,
        "file_hash": file_hash,
        "file_size": len(file_bytes),
        "mime_type": detected_mime
    }
