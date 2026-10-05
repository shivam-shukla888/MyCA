"""
Fallback parser for unsupported or unclassified documents.
Mandate: Never invent the document type or data. Return status = UNSUPPORTED.
"""

from typing import Dict, Any, List
import fitz
from .base import BaseDocumentParser
from ...financial.models import DataStatus

class UnsupportedDocumentParser(BaseDocumentParser):
    def parse(self, doc: fitz.Document, pages_data: List[Dict[str, Any]], user_id: str, document_id: str) -> Dict[str, Any]:
        msg = "Ye document format abhi directly supported nahi hai. myCA bank statements, salary slips, aur Form 16 ko support karta hai."
        return {
            "doc_type": "unsupported",
            "account": None,
            "transactions": [],
            "reconciliation": {
                "is_valid": False,
                "status": DataStatus.UNSUPPORTED.value,
                "opening_balance": 0.0,
                "total_credits": 0.0,
                "total_debits": 0.0,
                "net_savings": 0.0,
                "calculated_closing": 0.0,
                "reported_closing": 0.0,
                "discrepancy": 0.0,
                "message": msg
            },
            "status": DataStatus.UNSUPPORTED.value,
            "message": msg
        }
