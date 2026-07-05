"""
DCF Math Calculations Domain Rules.
Performs deterministic, unit-testable Discounted Cash Flow valuation.
"""

from typing import Any

from app.domain.exceptions import FinancialCalculationError, InvalidAssumptionError


def calculate_dcf(
    free_cash_flow: float,
    wacc: float,
    short_term_growth: float | list[float],
    terminal_growth: float,
    projection_years: int,
    net_debt: float,
    shares_outstanding: float,
) -> dict[str, Any]:
    """
    Performs a Discounted Cash Flow (DCF) valuation using the Free Cash Flow model.

    Validates that:
    - wacc > terminal_growth (otherwise TV fails to converge).
    - shares_outstanding > 0.
    - wacc > 0.
    """
    # 1. Validation Checks
    if wacc <= 0:
        raise InvalidAssumptionError(
            f"WACC must be strictly positive. Provided: {wacc}"
        )

    if terminal_growth >= wacc:
        raise InvalidAssumptionError(
            f"Terminal growth rate ({terminal_growth}) cannot be greater than or equal to WACC ({wacc})."
        )

    if shares_outstanding <= 0:
        raise InvalidAssumptionError(
            f"Shares outstanding must be positive. Provided: {shares_outstanding}"
        )

    # 2. Setup short-term growth list
    if isinstance(short_term_growth, list):
        growth_rates = short_term_growth
        actual_projection_years = len(short_term_growth)
    else:
        growth_rates = [short_term_growth] * projection_years
        actual_projection_years = projection_years

    # 3. Project Free Cash Flows
    projected_cfs: list[float] = []
    current_cf = free_cash_flow
    for rate in growth_rates:
        current_cf = current_cf * (1.0 + rate)
        projected_cfs.append(current_cf)

    # 4. Calculate Discount Factors and Present Value (PV) of short-term CFs
    pv_cfs: list[float] = []
    for t, cf in enumerate(projected_cfs, start=1):
        discount_factor = (1.0 + wacc) ** t
        pv_cfs.append(cf / discount_factor)

    sum_pv_cfs = sum(pv_cfs)

    # 5. Calculate Terminal Value (TV)
    last_cf = projected_cfs[-1]
    terminal_value = (last_cf * (1.0 + terminal_growth)) / (wacc - terminal_growth)

    # 6. Discount Terminal Value to Present
    pv_terminal_value = terminal_value / ((1.0 + wacc) ** actual_projection_years)

    # 7. Enterprise Value (EV) and Equity Value
    enterprise_value = sum_pv_cfs + pv_terminal_value
    equity_value = enterprise_value - net_debt

    # 8. Intrinsic Value per share
    try:
        intrinsic_value_per_share = equity_value / shares_outstanding
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Division by zero when calculating per share value"
        ) from e

    # 9. Generate Sensitivity Grid (varying WACC and Terminal Growth by +/- 0.5% and 1.0%)
    sensitivity_grid = _generate_sensitivity_grid(
        free_cash_flow=free_cash_flow,
        base_wacc=wacc,
        growth_rates=growth_rates,
        base_terminal_growth=terminal_growth,
        net_debt=net_debt,
        shares_outstanding=shares_outstanding,
    )

    return {
        "projected_cash_flows": projected_cfs,
        "present_value_cash_flows": pv_cfs,
        "sum_pv_cash_flows": sum_pv_cfs,
        "terminal_value": terminal_value,
        "present_value_terminal_value": pv_terminal_value,
        "enterprise_value": enterprise_value,
        "net_debt": net_debt,
        "equity_value": equity_value,
        "intrinsic_value_per_share": intrinsic_value_per_share,
        "sensitivity_grid": sensitivity_grid,
    }


def _generate_sensitivity_grid(
    free_cash_flow: float,
    base_wacc: float,
    growth_rates: list[float],
    base_terminal_growth: float,
    net_debt: float,
    shares_outstanding: float,
) -> dict[str, Any]:
    """Helper to vary WACC and Terminal Growth Rate and calculate resulting values per share."""
    wacc_variations = [-0.01, -0.005, 0.0, 0.005, 0.01]
    tg_variations = [-0.01, -0.005, 0.0, 0.005, 0.01]

    grid: list[list[float]] = []
    wacc_headers = [base_wacc + var for var in wacc_variations]
    tg_headers = [base_terminal_growth + var for var in tg_variations]

    for tg in tg_headers:
        row: list[float] = []
        for wacc in wacc_headers:
            if tg >= wacc or wacc <= 0:
                row.append(0.0)  # Invalid combination
                continue

            # Project
            projected_cfs = []
            current_cf = free_cash_flow
            for rate in growth_rates:
                current_cf = current_cf * (1.0 + rate)
                projected_cfs.append(current_cf)

            # Discount PV
            pv_cfs = []
            for t, cf in enumerate(projected_cfs, start=1):
                pv_cfs.append(cf / ((1.0 + wacc) ** t))

            sum_pv = sum(pv_cfs)
            tv = (projected_cfs[-1] * (1.0 + tg)) / (wacc - tg)
            pv_tv = tv / ((1.0 + wacc) ** len(growth_rates))
            ev = sum_pv + pv_tv
            eq = ev - net_debt
            val_per_share = max(0.0, eq / shares_outstanding)
            row.append(val_per_share)
        grid.append(row)

    return {
        "wacc_axis": wacc_headers,
        "terminal_growth_axis": tg_headers,
        "grid": grid,
    }
