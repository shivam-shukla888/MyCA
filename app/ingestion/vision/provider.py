"""
Document Vision Provider Interface.
Mandate:
- Pluggable provider architecture (Gemini, LocalVisionEngine, Mock).
- Never hardcode the entire application around one model vendor.
- Clear operations: analyze_document, analyze_multiple_pages, assess_quality.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import VisionExtractionResult, ImageQualityAssessment

class DocumentVisionProvider(ABC):
    """Abstract interface for vision-capable document understanding engines."""

    @abstractmethod
    def assess_quality(self, image_bytes: bytes, filename: str = "") -> ImageQualityAssessment:
        """Assesses image clarity, focus, and illumination."""
        pass

    @abstractmethod
    def analyze_document(
        self,
        file_bytes: bytes,
        mime_type: str,
        filename: str = "",
        doc_type_hint: Optional[str] = None
    ) -> VisionExtractionResult:
        """Analyzes a single document (PDF or single image) and extracts structured financial data."""
        pass

    @abstractmethod
    def analyze_multiple_pages(
        self,
        pages: List[Dict[str, Any]],  # each item: {"bytes": b"...", "mime_type": "...", "page_num": int, "filename": str}
        doc_type_hint: Optional[str] = None
    ) -> VisionExtractionResult:
        """Analyzes multiple uploaded images belonging to ONE financial document."""
        pass
