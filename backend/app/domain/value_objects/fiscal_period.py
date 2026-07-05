"""
FiscalPeriod value object representing standard financial reporting periods.
"""

from typing import Any, ClassVar

from app.domain.exceptions import EntityValidationError


class FiscalPeriod:
    """
    An immutable value object representing a reporting period (e.g. Q1, FY) and year.
    """

    ALLOWED_PERIODS: ClassVar[set[str]] = {"Q1", "Q2", "Q3", "Q4", "FY"}

    def __init__(self, period: str, year: int) -> None:
        period_upper = period.upper().strip()
        if period_upper not in self.ALLOWED_PERIODS:
            raise EntityValidationError(
                f"Invalid fiscal period: '{period}'. Must be one of {self.ALLOWED_PERIODS}"
            )

        if not isinstance(year, int) or year < 1800 or year > 2100:
            raise EntityValidationError(f"Invalid fiscal year: {year}")

        self._period = period_upper
        self._year = year

    @property
    def period(self) -> str:
        """The reporting period segment (e.g., Q1, FY)."""
        return self._period

    @property
    def year(self) -> int:
        """The calendar year of the fiscal period."""
        return self._year

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FiscalPeriod):
            return False
        return self._period == other.period and self._year == other.year

    def __repr__(self) -> str:
        return f"{self._period} {self._year}"

    def __str__(self) -> str:
        return f"{self._period}-{self._year}"
