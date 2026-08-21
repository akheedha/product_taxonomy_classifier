"""
Custom domain exceptions for taxonomy classification, import, and processing.
"""


class ProductClassificationException(Exception):
    """Base exception for classification errors."""
    pass


class CatalogImportError(ProductClassificationException):
    """Raised when parsing or validating an import spreadsheet fails."""
    pass


class ImageDownloadError(ProductClassificationException):
    """Raised when downloading or pre-processing a product image fails."""
    pass


class TaxonomyNotFoundError(ProductClassificationException):
    """Raised when category or attribute taxonomy is missing from the database."""
    pass


class ProcessingJobError(ProductClassificationException):
    """Raised when a batch job fails or encounters an unrecoverable state."""
    pass
