"""
Exchange value object representing trading exchanges.
"""

import re
from typing import Any

from app.domain.exceptions import EntityValidationError


class Exchange:
    """
    An immutable value object representing a stock exchange (e.g., NYSE, NASDAQ).
    """

    EXCHANGE_PATTERN = re.compile(r"^[A-Z0-9.\-]{2,15}$")

    def __init__(self, name: str) -> None:
        if not name:
            raise EntityValidationError("Exchange name cannot be empty")

        name_upper = name.upper().strip()
        if not self.EXCHANGE_PATTERN.match(name_upper):
            raise EntityValidationError(f"Invalid exchange name format: '{name}'")

        self._name = name_upper

    @property
    def name(self) -> str:
        """The validated exchange name."""
        return self._name

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Exchange):
            return False
        return self._name == other.name

    def __repr__(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name
