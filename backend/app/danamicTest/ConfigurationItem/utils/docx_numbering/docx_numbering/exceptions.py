"""
Custom exceptions for the docx_numbering package.
"""


class DocxNumberingError(Exception):
    """Base exception for docx_numbering package."""
    pass


class InvalidDocxFileError(DocxNumberingError):
    """Raised when the DOCX file is invalid or cannot be read."""
    pass


class NumberingNotFoundError(DocxNumberingError):
    """Raised when no numbering information is found in the document."""
    pass


class NumberFormatError(DocxNumberingError):
    """Raised when there's an error formatting a number."""
    pass


class UnsupportedFormatError(DocxNumberingError):
    """Raised when an unsupported numbering format is encountered."""
    pass