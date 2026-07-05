"""
Domain-specific exceptions for EquityIQ.
"""


class DomainException(Exception):
    """Base class for all domain-related exceptions."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EntityValidationError(DomainException):
    """Raised when domain entity data fails validation rules."""


class InvalidAssumptionError(DomainException):
    """Raised when financial assumptions (e.g., WACC <= Terminal Growth) are invalid."""


class FinancialCalculationError(DomainException):
    """Raised when a mathematical or financial calculation fails."""


class NormalizationError(DomainException):
    """Raised when statement normalization adjustments fail validation."""
