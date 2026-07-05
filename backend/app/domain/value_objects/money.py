"""
Money value object representing financial values with specific currencies.
"""

import decimal
from decimal import Decimal
from typing import Any

from app.domain.exceptions import EntityValidationError


class Money:
    """
    An immutable value object representing monetary values.
    Enforces exact operations and prevents cross-currency errors.
    """

    def __init__(self, amount: Decimal | float | int | str, currency: str) -> None:
        try:
            self._amount = Decimal(str(amount))
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            raise EntityValidationError(f"Invalid monetary amount: {amount}") from e

        if not currency or len(currency) != 3:
            raise EntityValidationError(f"Invalid ISO 4217 currency: '{currency}'")

        self._currency = currency.upper()

    @property
    def amount(self) -> Decimal:
        """The monetary amount."""
        return self._amount

    @property
    def currency(self) -> str:
        """The currency code (e.g., USD, EUR)."""
        return self._currency

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return False
        return self._amount == other.amount and self._currency == other.currency

    def __add__(self, other: "Money") -> "Money":
        if self._currency != other.currency:
            raise EntityValidationError(
                f"Cannot add money of different currencies: {self._currency} and {other.currency}"
            )
        return Money(self._amount + other.amount, self._currency)

    def __sub__(self, other: "Money") -> "Money":
        if self._currency != other.currency:
            raise EntityValidationError(
                f"Cannot subtract money of different currencies: {self._currency} and {other.currency}"
            )
        return Money(self._amount - other.amount, self._currency)

    def __mul__(self, factor: int | float | Decimal) -> "Money":
        return Money(self._amount * Decimal(str(factor)), self._currency)

    def __repr__(self) -> str:
        return f"{self._amount} {self._currency}"
