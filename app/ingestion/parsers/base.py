"""
Base Document Parser Interface.
Every format parser implements extract_and_normalize.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import fitz

class BaseDocumentParser(ABC):
    @abstractmethod
    def parse(self, doc: fitz.Document, pages_data: List[Dict[str, Any]], user_id: str, document_id: str) -> Dict[str, Any]:
        """
        Parses document-specific data, performs mathematical validation,
        and returns structured normalized models.
        """
        pass
