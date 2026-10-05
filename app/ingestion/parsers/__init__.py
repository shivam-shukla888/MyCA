"""
Parsers Package Index.
Provides get_parser_for_document_type factory function.
"""

from typing import Type
from .base import BaseDocumentParser
from .bank_statement import BankStatementParser
from .salary_slip import SalarySlipParser
from .form_16 import Form16Parser
from .unsupported import UnsupportedDocumentParser
from ..classifier import DocumentType

def get_parser_for_document_type(doc_type: DocumentType) -> BaseDocumentParser:
    """Returns the dedicated parser adapter for the classified document type."""
    if doc_type == DocumentType.BANK_STATEMENT:
        return BankStatementParser()
    elif doc_type == DocumentType.SALARY_SLIP:
        return SalarySlipParser()
    elif doc_type == DocumentType.FORM_16:
        return Form16Parser()
    else:
        return UnsupportedDocumentParser()

__all__ = [
    "BaseDocumentParser",
    "BankStatementParser",
    "SalarySlipParser",
    "Form16Parser",
    "UnsupportedDocumentParser",
    "get_parser_for_document_type"
]
