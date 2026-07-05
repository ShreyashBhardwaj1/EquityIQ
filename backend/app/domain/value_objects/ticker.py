"""
Ticker value object representing financial listing ticker symbols.
"""

import re
from typing import Any

from app.domain.exceptions import EntityValidationError


class Ticker:
    """
    An immutable value object representing a stock ticker symbol.
    """

    # Alphanumeric with optional dot or dash (e.g. BRK.A, RDS-B, AAPL)
    TICKER_PATTERN = re.compile(r"^[A-Z0-9.\-]{1,10}$")

    def __init__(self, symbol: str) -> None:
        if not symbol:
            raise EntityValidationError("Ticker symbol cannot be empty")

        symbol_upper = symbol.upper().strip()
        if not self.TICKER_PATTERN.match(symbol_upper):
            raise EntityValidationError(f"Invalid ticker format: '{symbol}'")

        self._symbol = symbol_upper

    @property
    def symbol(self) -> str:
        """The cleaned ticker symbol."""
        return self._symbol

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Ticker):
            return False
        return self._symbol == other.symbol

    def __repr__(self) -> str:
        return self._symbol

    def __str__(self) -> str:
        return self._symbol
