"""
Ratio Formulas Domain Rules.
Provides pure-python deterministic financial ratios calculations.
"""

from app.domain.exceptions import FinancialCalculationError


def calculate_current_ratio(current_assets: float, current_liabilities: float) -> float:
    """
    Calculates the Current Ratio (Liquidity).
    Formula: Current Assets / Current Liabilities
    """
    try:
        return float(current_assets) / float(current_liabilities)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Current Liabilities cannot be zero when calculating Current Ratio"
        ) from e


def calculate_quick_ratio(
    cash_and_equivs: float,
    marketable_securities: float,
    receivables: float,
    current_liabilities: float,
) -> float:
    """
    Calculates the Quick Ratio (Acid-Test Liquidity).
    Formula: (Cash + Marketable Securities + Receivables) / Current Liabilities
    """
    try:
        liquid_assets = (
            float(cash_and_equivs) + float(marketable_securities) + float(receivables)
        )
        return liquid_assets / float(current_liabilities)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Current Liabilities cannot be zero when calculating Quick Ratio"
        ) from e


def calculate_gross_margin(gross_profit: float, revenue: float) -> float:
    """
    Calculates Gross Profit Margin (Profitability).
    Formula: Gross Profit / Revenue
    """
    try:
        return float(gross_profit) / float(revenue)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Revenue cannot be zero when calculating Gross Margin"
        ) from e


def calculate_operating_margin(operating_income: float, revenue: float) -> float:
    """
    Calculates Operating Profit Margin (Profitability).
    Formula: Operating Income / Revenue
    """
    try:
        return float(operating_income) / float(revenue)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Revenue cannot be zero when calculating Operating Margin"
        ) from e


def calculate_net_margin(net_income: float, revenue: float) -> float:
    """
    Calculates Net Profit Margin (Profitability).
    Formula: Net Income / Revenue
    """
    try:
        return float(net_income) / float(revenue)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Revenue cannot be zero when calculating Net Margin"
        ) from e


def calculate_debt_to_equity(total_debt: float, total_equity: float) -> float:
    """
    Calculates Debt-to-Equity ratio (Solvency).
    Formula: Total Debt / Total Equity
    """
    try:
        return float(total_debt) / float(total_equity)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Total Equity cannot be zero when calculating Debt to Equity Ratio"
        ) from e


def calculate_return_on_equity(net_income: float, total_equity: float) -> float:
    """
    Calculates Return on Equity (ROE) (Efficiency).
    Formula: Net Income / Total Equity
    """
    try:
        return float(net_income) / float(total_equity)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Total Equity cannot be zero when calculating Return on Equity (ROE)"
        ) from e


def calculate_return_on_assets(net_income: float, total_assets: float) -> float:
    """
    Calculates Return on Assets (ROA) (Efficiency).
    Formula: Net Income / Total Assets
    """
    try:
        return float(net_income) / float(total_assets)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Total Assets cannot be zero when calculating Return on Assets (ROA)"
        ) from e


def calculate_pe_ratio(price: float, eps: float) -> float:
    """
    Calculates Price-to-Earnings (PE) Ratio (Valuation).
    Formula: Price / Earnings Per Share
    """
    try:
        return float(price) / float(eps)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Earnings Per Share (EPS) cannot be zero when calculating PE Ratio"
        ) from e


def calculate_price_to_book(market_cap: float, total_equity: float) -> float:
    """
    Calculates Price-to-Book (PB) Ratio (Valuation).
    Formula: Market Capitalization / Total Equity
    """
    try:
        return float(market_cap) / float(total_equity)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "Total Equity cannot be zero when calculating PB Ratio"
        ) from e


def calculate_ev_to_ebitda(enterprise_value: float, ebitda: float) -> float:
    """
    Calculates Enterprise Value to EBITDA (EV/EBITDA) Ratio (Valuation).
    Formula: Enterprise Value / EBITDA
    """
    try:
        return float(enterprise_value) / float(ebitda)
    except ZeroDivisionError as e:
        raise FinancialCalculationError(
            "EBITDA cannot be zero when calculating EV/EBITDA Ratio"
        ) from e
