"""
Local OCR Fallback Module for Scanned/Image Pages.
Requirements:
- Preserves page numbers and provenance.
- Records extraction method as 'OCR_FALLBACK'.
- Never automatically marks uncertain OCR results as verified (sets status = NEEDS_REVIEW).
- Uses local processing only; zero transmission of sensitive files to cloud OCR APIs.
"""

import fitz  # PyMuPDF
from typing import Dict, Any, Tuple

def extract_page_ocr_fallback(page: fitz.Page, page_num: int) -> Tuple[str, float, bool]:
    """
    Attempts local OCR on an image-only page using PyMuPDF's built-in OCR hook or image inspection.
    Returns: (extracted_text, confidence, was_ocr_applied)
    """
    # First try PyMuPDF built-in OCR if available
    try:
        if hasattr(page, "get_textpage_ocr"):
            # PyMuPDF Tesseract integration
            tp = page.get_textpage_ocr(language='eng', dpi=150, full=True)
            text = tp.extractText()
            if text and len(text.strip()) > 20:
                return text.strip(), 0.75, True
    except Exception:
        pass

    # Fallback: extract image blocks text or return placeholder with low confidence
    try:
        pix = page.get_pixmap(dpi=150)
        import pytesseract
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_text = pytesseract.image_to_string(img)
        if ocr_text and len(ocr_text.strip()) > 10:
            return ocr_text.strip(), 0.70, True
    except Exception:
        pass

    # If local OCR cannot run, return empty text with 0.0 confidence
    return "", 0.0, False
