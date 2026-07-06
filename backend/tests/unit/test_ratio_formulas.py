"""
Unit tests for Financial Ratio Formulas.
"""

import pytest

from app.domain.exceptions import FinancialCalculationError
from app.domain.rules.ratio_formulas import (
    calculate_current_ratio,
    calculate_debt_to_equity,
    calculate_ev_to_ebitda,
    calculate_gross_margin,
    calculate_net_margin,
    calculate_operating_margin,
    calculate_pe_ratio,
    calculate_price_to_book,
    calculate_quick_ratio,
    calculate_return_on_assets,
    calculate_return_on_equity,
)


def test_liquidity_ratios() -> None:
    """Test current and quick ratios math."""
    # Current Ratio: 200 / 100 = 2.0
    assert calculate_current_ratio(200.0, 100.0) == 2.0

    # Quick Ratio: (50 + 20 + 30) / 100 = 1.0
    assert calculate_quick_ratio(50.0, 20.0, 30.0, 100.0) == 1.0


def test_profitability_ratios() -> None:
    """Test margins profitability calculations."""
    # Gross Margin: 400 / 1000 = 0.4 (40%)
    assert calculate_gross_margin(400.0, 1000.0) == 0.4

    # Operating Margin: 150 / 1000 = 0.15 (15%)
    assert calculate_operating_margin(150.0, 1000.0) == 0.15

    # Net Margin: 100 / 1000 = 0.10 (10%)
    assert calculate_net_margin(100.0, 1000.0) == 0.10


def test_solvency_and_efficiency_ratios() -> None:
    """Test leverage, ROE, and ROA calculations."""
    # Debt to Equity: 500 / 250 = 2.0
    assert calculate_debt_to_equity(500.0, 250.0) == 2.0

    # Return on Equity (ROE): 50 / 250 = 0.20 (20%)
    assert calculate_return_on_equity(50.0, 250.0) == 0.20

    # Return on Assets (ROA): 50 / 1000 = 0.05 (5%)
    assert calculate_return_on_assets(50.0, 1000.0) == 0.05


def test_valuation_multiples() -> None:
    """Test standard multiple valuations."""
    # P/E: 150 / 10 = 15.0
    assert calculate_pe_ratio(150.0, 10.0) == 15.0

    # P/B: 1500 / 500 = 3.0
    assert calculate_price_to_book(1500.0, 500.0) == 3.0

    # EV/EBITDA: 1200 / 300 = 4.0
    assert calculate_ev_to_ebitda(1200.0, 300.0) == 4.0


def test_division_by_zero_raises() -> None:
    """Test that divide-by-zero invokes FinancialCalculationError."""
    with pytest.raises(FinancialCalculationError):
        calculate_current_ratio(100.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_quick_ratio(10.0, 10.0, 10.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_gross_margin(100.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_operating_margin(100.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_net_margin(100.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_debt_to_equity(100.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_return_on_equity(100.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_return_on_assets(100.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_pe_ratio(10.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_price_to_book(1000.0, 0.0)

    with pytest.raises(FinancialCalculationError):
        calculate_ev_to_ebitda(1000.0, 0.0)
