"""
Unit tests for Domain Value Objects.
"""

from decimal import Decimal
import pytest
from app.domain.exceptions import EntityValidationError
from app.domain.value_objects.money import Money
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.domain.value_objects.ticker import Ticker
from app.domain.value_objects.exchange import Exchange


def test_money_creation_and_properties() -> None:
    """Test valid instantiation and operations of Money value object."""
    m1 = Money("100.50", "USD")
    assert m1.amount == Decimal("100.50")
    assert m1.currency == "USD"

    m2 = Money(150, "eur")
    assert m2.amount == Decimal("150.00")
    assert m2.currency == "EUR"


def test_money_invalid_inputs() -> None:
    """Test exception raising for invalid Money values."""
    with pytest.raises(EntityValidationError):
        Money("invalid_decimal", "USD")

    with pytest.raises(EntityValidationError):
        Money(100, "US")  # Too short

    with pytest.raises(EntityValidationError):
        Money(100, "USDT")  # Too long


def test_money_operations() -> None:
    """Test addition, subtraction, and multiplication of Money value objects."""
    m1 = Money("100", "USD")
    m2 = Money("50", "USD")

    # Addition
    added = m1 + m2
    assert added == Money("150", "USD")

    # Subtraction
    subtracted = m1 - m2
    assert subtracted == Money("50", "USD")

    # Multiplication
    multiplied = m1 * 2.5
    assert multiplied == Money("250", "USD")

    # Non-Money equality
    assert m1 != "100 USD"
    assert repr(m1) == "100 USD"


def test_money_operation_currency_mismatch() -> None:
    """Test that arithmetic on mismatched currencies raises a ValidationError."""
    m1 = Money("100", "USD")
    m2 = Money("100", "EUR")

    with pytest.raises(EntityValidationError):
        _ = m1 + m2

    with pytest.raises(EntityValidationError):
        _ = m1 - m2


def test_fiscal_period_creation_and_properties() -> None:
    """Test valid FiscalPeriod instances and string representation."""
    fp1 = FiscalPeriod("Q1", 2024)
    assert fp1.period == "Q1"
    assert fp1.year == 2024
    assert str(fp1) == "Q1-2024"
    assert repr(fp1) == "Q1 2024"
    assert fp1 != "Q1-2024"

    fp2 = FiscalPeriod("fy", 2025)
    assert fp2.period == "FY"
    assert fp2.year == 2025


def test_fiscal_period_invalid() -> None:
    """Test that invalid periods or years raise a ValidationError."""
    with pytest.raises(EntityValidationError):
        FiscalPeriod("Q5", 2024)  # Invalid period

    with pytest.raises(EntityValidationError):
        FiscalPeriod("Q1", 1799)  # Year too early

    with pytest.raises(EntityValidationError):
        FiscalPeriod("FY", 2101)  # Year too far in future


def test_ticker_validation() -> None:
    """Test Ticker symbol validation rules."""
    t1 = Ticker("aapl")
    assert t1.symbol == "AAPL"
    assert Ticker("BRK.A").symbol == "BRK.A"
    assert Ticker("RDS-B").symbol == "RDS-B"
    assert t1 != "AAPL"
    assert repr(t1) == "AAPL"
    assert str(t1) == "AAPL"


def test_ticker_invalid() -> None:
    """Test invalid ticker structures raise a ValidationError."""
    with pytest.raises(EntityValidationError):
        Ticker("")  # Empty

    with pytest.raises(EntityValidationError):
        Ticker("TOOLONGTICKER")  # >10 chars

    with pytest.raises(EntityValidationError):
        Ticker("AAP$L")  # Special chars


def test_exchange_validation() -> None:
    """Test Exchange validation rules."""
    e1 = Exchange("nasdaq")
    assert e1.name == "NASDAQ"
    assert Exchange("NYSE").name == "NYSE"
    assert e1 != "NASDAQ"
    assert repr(e1) == "NASDAQ"
    assert str(e1) == "NASDAQ"


def test_exchange_invalid() -> None:
    """Test invalid exchange names raise validation errors."""
    with pytest.raises(EntityValidationError):
        Exchange("")  # Empty

    with pytest.raises(EntityValidationError):
        Exchange("N")  # Too short (pattern is 2 to 15 chars)

    with pytest.raises(EntityValidationError):
        Exchange("A" * 16)  # Too long

    with pytest.raises(EntityValidationError):
        Exchange("NY$E")  # Special chars


