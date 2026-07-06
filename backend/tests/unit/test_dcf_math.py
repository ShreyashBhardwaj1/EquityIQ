"""
Unit tests for DCF Math calculations.
"""

import pytest

from app.domain.exceptions import InvalidAssumptionError
from app.domain.rules.dcf_math import calculate_dcf


def test_dcf_known_answer() -> None:
    """
    Test the DCF calculation engine using a known-answer test fixture.
    Fixture parameters:
    - Base FCF: 100.00
    - WACC: 10% (0.10)
    - Short-term Growth: 5% (0.05)
    - Terminal Growth: 2% (0.02)
    - Projection Years: 5
    - Net Debt: 200.00
    - Shares Outstanding: 10

    Hand-calculated values:
    - Year 1 FCF = 105.00, PV = 95.4545
    - Year 2 FCF = 110.25, PV = 91.1157
    - Year 3 FCF = 115.76, PV = 86.9741
    - Year 4 FCF = 121.55, PV = 83.0207
    - Year 5 FCF = 127.63, PV = 79.2471
    - Sum PV of CFs = 435.8122
    - Terminal Value = (127.6282 * 1.02) / 0.08 = 1627.2592
    - PV of Terminal Value = 1627.2592 / (1.10^5) = 1010.4000
    - Enterprise Value = 435.8122 + 1010.4000 = 1446.2122
    - Equity Value = 1446.2122 - 200.00 = 1246.2122
    - Value per Share = 1246.2122 / 10 = 124.6212
    """
    res = calculate_dcf(
        free_cash_flow=100.00,
        wacc=0.10,
        short_term_growth=0.05,
        terminal_growth=0.02,
        projection_years=5,
        net_debt=200.00,
        shares_outstanding=10.0,
    )

    # Check intermediate calculations
    assert res["projected_cash_flows"][0] == pytest.approx(105.00, rel=1e-4)
    assert res["projected_cash_flows"][4] == pytest.approx(127.6282, rel=1e-4)
    assert res["present_value_cash_flows"][0] == pytest.approx(95.4545, rel=1e-4)
    assert res["present_value_cash_flows"][4] == pytest.approx(79.2471, rel=1e-4)
    assert res["sum_pv_cash_flows"] == pytest.approx(435.8122, rel=1e-4)
    assert res["terminal_value"] == pytest.approx(1627.2592, rel=1e-4)
    assert res["present_value_terminal_value"] == pytest.approx(1010.4000, rel=1e-4)

    # Check final outputs
    assert res["enterprise_value"] == pytest.approx(1446.2122, rel=1e-4)
    assert res["equity_value"] == pytest.approx(1246.2122, rel=1e-4)
    assert res["intrinsic_value_per_share"] == pytest.approx(124.6212, rel=1e-4)


def test_dcf_growth_rates_list() -> None:
    """Test DCF calculation using variable growth rates in a list."""
    res = calculate_dcf(
        free_cash_flow=100.00,
        wacc=0.10,
        short_term_growth=[0.08, 0.06, 0.04],  # Variable growth
        terminal_growth=0.02,
        projection_years=3,
        net_debt=100.00,
        shares_outstanding=10.0,
    )
    # Check that projection_years is inferred from list length (3 years)
    assert len(res["projected_cash_flows"]) == 3
    assert res["projected_cash_flows"][0] == pytest.approx(108.00)
    assert res["projected_cash_flows"][1] == pytest.approx(114.48)
    assert res["projected_cash_flows"][2] == pytest.approx(119.0592)


def test_dcf_invalid_assumptions_raise() -> None:
    """Test validation errors for invalid DCF assumptions."""
    # 1. WACC <= 0
    with pytest.raises(InvalidAssumptionError):
        calculate_dcf(100.0, 0.0, 0.05, 0.02, 5, 100.0, 10.0)

    # 2. Terminal growth >= WACC
    with pytest.raises(InvalidAssumptionError):
        calculate_dcf(100.0, 0.08, 0.05, 0.08, 5, 100.0, 10.0)

    # 3. Shares outstanding <= 0
    with pytest.raises(InvalidAssumptionError):
        calculate_dcf(100.0, 0.08, 0.05, 0.02, 5, 100.0, 0.0)


def test_dcf_sensitivity_grid() -> None:
    """Test that sensitivity grid outputs have the correct shapes."""
    res = calculate_dcf(
        free_cash_flow=100.00,
        wacc=0.10,
        short_term_growth=0.05,
        terminal_growth=0.02,
        projection_years=5,
        net_debt=200.00,
        shares_outstanding=10.0,
    )

    grid_info = res["sensitivity_grid"]
    assert len(grid_info["wacc_axis"]) == 5
    assert len(grid_info["terminal_growth_axis"]) == 5
    assert len(grid_info["grid"]) == 5  # 5 rows for terminal growth
    assert len(grid_info["grid"][0]) == 5  # 5 columns for WACC
