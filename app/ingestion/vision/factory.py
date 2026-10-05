"""
Vision Provider Factory.
Provides decoupled resolution of the active vision provider.
"""

import os
from typing import Optional
from .provider import DocumentVisionProvider
from .local import LocalVisionEngine
from .gemini import GeminiVisionProvider
from .models import VisionExtractionResult, ImageQualityAssessment, VisionProcessingStatus

class MockFailureVisionProvider(DocumentVisionProvider):
    """Used in unit & integration tests to simulate AI provider failure / timeout."""
    def assess_quality(self, image_bytes: bytes, filename: str = "") -> ImageQualityAssessment:
        return ImageQualityAssessment(is_acceptable=False, score=0.0, issues=["PROVIDER_TIMEOUT"])

    def analyze_document(self, file_bytes: bytes, mime_type: str, filename: str = "", doc_type_hint: Optional[str] = None) -> VisionExtractionResult:
        return VisionExtractionResult(
            document_type="UNKNOWN",
            confidence=0.0,
            validation_status=VisionProcessingStatus.FAILED.value,
            status_message="Provider timeout or service unavailable. Please retry later."
        )

    def analyze_multiple_pages(self, pages, doc_type_hint=None):
        return VisionExtractionResult(
            document_type="UNKNOWN",
            confidence=0.0,
            validation_status=VisionProcessingStatus.FAILED.value,
            status_message="Provider timeout on multi-page analysis."
        )

def get_vision_provider(provider_type: Optional[str] = None) -> DocumentVisionProvider:
    """
    Returns the configured vision provider instance.
    Checks environment for API keys, else provides LocalVisionEngine.
    """
    if provider_type == "mock_failure":
        return MockFailureVisionProvider()
    elif provider_type == "gemini":
        return GeminiVisionProvider()
    elif provider_type == "local":
        return LocalVisionEngine()

    # Default auto-discovery
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return GeminiVisionProvider(api_key=api_key)
    return LocalVisionEngine()
