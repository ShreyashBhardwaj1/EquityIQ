"""
Registry-driven ratio definitions.
Defines calculation functions, required fields, and assumptions for all deterministic ratios.
"""

from typing import ClassVar

from app.domain.entities.financial_intelligence import RatioCategory, RatioDefinition


def calculate_current_ratio(items: dict[str, float]) -> float:
    return items["total_current_assets"] / items["total_current_liabilities"]


def calculate_quick_ratio(items: dict[str, float]) -> float:
    cash = items.get("cash_equivalents", 0.0)
    securities = items.get("marketable_securities", 0.0)
    receivables = items.get("accounts_receivable", 0.0)
    return (cash + securities + receivables) / items["total_current_liabilities"]


def calculate_cash_ratio(items: dict[str, float]) -> float:
    cash = items.get("cash_equivalents", 0.0)
    return cash / items["total_current_liabilities"]


def calculate_debt_to_equity(items: dict[str, float]) -> float:
    return items["total_debt"] / items["total_equity"]


def calculate_debt_ratio(items: dict[str, float]) -> float:
    return items["total_debt"] / items["total_assets"]


def calculate_interest_coverage(items: dict[str, float]) -> float:
    ebit = items.get("operating_income", 0.0)
    return ebit / items["interest_expense"]


def calculate_gross_margin(items: dict[str, float]) -> float:
    return items.get("gross_profit", 0.0) / items["revenue"]


def calculate_operating_margin(items: dict[str, float]) -> float:
    return items.get("operating_income", 0.0) / items["revenue"]


def calculate_net_margin(items: dict[str, float]) -> float:
    return items.get("net_income", 0.0) / items["revenue"]


def calculate_roa(items: dict[str, float]) -> float:
    return items.get("net_income", 0.0) / items["total_assets"]


def calculate_roe(items: dict[str, float]) -> float:
    return items.get("net_income", 0.0) / items["total_equity"]


def calculate_asset_turnover(items: dict[str, float]) -> float:
    return items.get("revenue", 0.0) / items["total_assets"]


def calculate_inventory_turnover(items: dict[str, float]) -> float:
    return items.get("cost_of_goods_sold", 0.0) / items["inventory"]


def calculate_receivable_turnover(items: dict[str, float]) -> float:
    return items.get("revenue", 0.0) / items["accounts_receivable"]


def calculate_operating_cf_margin(items: dict[str, float]) -> float:
    return items.get("operating_cash_flow", 0.0) / items["revenue"]


def calculate_free_cash_flow(items: dict[str, float]) -> float:
    return items.get("operating_cash_flow", 0.0) - items.get(
        "capital_expenditures", 0.0
    )


def calculate_cash_conversion_cycle(items: dict[str, float]) -> float:
    revenue = items.get("revenue", 0.0)
    cogs = items.get("cost_of_goods_sold", 0.0)
    ar = items.get("accounts_receivable", 0.0)
    inv = items.get("inventory", 0.0)
    ap = items.get("accounts_payable", 0.0)

    dso = (ar / revenue * 365.0) if revenue != 0.0 else 0.0
    dio = (inv / cogs * 365.0) if cogs != 0.0 else 0.0
    dpo = (ap / cogs * 365.0) if cogs != 0.0 else 0.0

    return dso + dio - dpo


class RatioRegistry:
    """
    Registry of all supported financial ratios.
    """

    DEFINITIONS: ClassVar[dict[str, RatioDefinition]] = {
        "current_ratio": RatioDefinition(
            name="current_ratio",
            category=RatioCategory.LIQUIDITY,
            formula="total_current_assets / total_current_liabilities",
            required_line_items=["total_current_assets", "total_current_liabilities"],
            calculate_fn=calculate_current_ratio,
            assumptions="Requires total current assets and liabilities to be reported.",
            validation_rules=[lambda val: val >= 0.0],
        ),
        "quick_ratio": RatioDefinition(
            name="quick_ratio",
            category=RatioCategory.LIQUIDITY,
            formula="(cash_equivalents + marketable_securities + accounts_receivable) / total_current_liabilities",
            required_line_items=["total_current_liabilities"],
            calculate_fn=calculate_quick_ratio,
            assumptions="Defaults missing cash equivalents, marketable securities, or accounts receivable to 0.0.",
            validation_rules=[lambda val: val >= 0.0],
        ),
        "cash_ratio": RatioDefinition(
            name="cash_ratio",
            category=RatioCategory.LIQUIDITY,
            formula="cash_equivalents / total_current_liabilities",
            required_line_items=["total_current_liabilities"],
            calculate_fn=calculate_cash_ratio,
            assumptions="Defaults missing cash equivalents to 0.0.",
            validation_rules=[lambda val: val >= 0.0],
        ),
        "debt_to_equity": RatioDefinition(
            name="debt_to_equity",
            category=RatioCategory.LEVERAGE,
            formula="total_debt / total_equity",
            required_line_items=["total_debt", "total_equity"],
            calculate_fn=calculate_debt_to_equity,
            assumptions="Requires total debt and equity values.",
            validation_rules=[lambda val: val >= 0.0],
        ),
        "debt_ratio": RatioDefinition(
            name="debt_ratio",
            category=RatioCategory.LEVERAGE,
            formula="total_debt / total_assets",
            required_line_items=["total_debt", "total_assets"],
            calculate_fn=calculate_debt_ratio,
            assumptions="Requires total debt and total assets.",
            validation_rules=[lambda val: val >= 0.0],
        ),
        "interest_coverage": RatioDefinition(
            name="interest_coverage",
            category=RatioCategory.LEVERAGE,
            formula="operating_income / interest_expense",
            required_line_items=["interest_expense"],
            calculate_fn=calculate_interest_coverage,
            assumptions="Operating income defaults to 0.0 if not present.",
        ),
        "gross_margin": RatioDefinition(
            name="gross_margin",
            category=RatioCategory.PROFITABILITY,
            formula="gross_profit / revenue",
            required_line_items=["revenue"],
            calculate_fn=calculate_gross_margin,
            assumptions="Gross profit defaults to 0.0 if not present.",
        ),
        "operating_margin": RatioDefinition(
            name="operating_margin",
            category=RatioCategory.PROFITABILITY,
            formula="operating_income / revenue",
            required_line_items=["revenue"],
            calculate_fn=calculate_operating_margin,
            assumptions="Operating income defaults to 0.0 if not present.",
        ),
        "net_margin": RatioDefinition(
            name="net_margin",
            category=RatioCategory.PROFITABILITY,
            formula="net_income / revenue",
            required_line_items=["revenue"],
            calculate_fn=calculate_net_margin,
            assumptions="Net income defaults to 0.0 if not present.",
        ),
        "roa": RatioDefinition(
            name="roa",
            category=RatioCategory.PROFITABILITY,
            formula="net_income / total_assets",
            required_line_items=["total_assets"],
            calculate_fn=calculate_roa,
            assumptions="Net income defaults to 0.0 if not present.",
        ),
        "roe": RatioDefinition(
            name="roe",
            category=RatioCategory.PROFITABILITY,
            formula="net_income / total_equity",
            required_line_items=["total_equity"],
            calculate_fn=calculate_roe,
            assumptions="Net income defaults to 0.0 if not present.",
        ),
        "asset_turnover": RatioDefinition(
            name="asset_turnover",
            category=RatioCategory.EFFICIENCY,
            formula="revenue / total_assets",
            required_line_items=["total_assets"],
            calculate_fn=calculate_asset_turnover,
            assumptions="Revenue defaults to 0.0 if not present.",
            validation_rules=[lambda val: val >= 0.0],
        ),
        "inventory_turnover": RatioDefinition(
            name="inventory_turnover",
            category=RatioCategory.EFFICIENCY,
            formula="cost_of_goods_sold / inventory",
            required_line_items=["inventory"],
            calculate_fn=calculate_inventory_turnover,
            assumptions="Cost of goods sold defaults to 0.0 if not present.",
            validation_rules=[lambda val: val >= 0.0],
        ),
        "receivable_turnover": RatioDefinition(
            name="receivable_turnover",
            category=RatioCategory.EFFICIENCY,
            formula="revenue / accounts_receivable",
            required_line_items=["accounts_receivable"],
            calculate_fn=calculate_receivable_turnover,
            assumptions="Revenue defaults to 0.0 if not present.",
            validation_rules=[lambda val: val >= 0.0],
        ),
        "operating_cf_margin": RatioDefinition(
            name="operating_cf_margin",
            category=RatioCategory.CASH_FLOW,
            formula="operating_cash_flow / revenue",
            required_line_items=["revenue"],
            calculate_fn=calculate_operating_cf_margin,
            assumptions="Operating cash flow defaults to 0.0 if not present.",
        ),
        "free_cash_flow": RatioDefinition(
            name="free_cash_flow",
            category=RatioCategory.CASH_FLOW,
            formula="operating_cash_flow - capital_expenditures",
            required_line_items=[],
            calculate_fn=calculate_free_cash_flow,
            assumptions="Defaults operating cash flow and capital expenditures to 0.0.",
        ),
        "cash_conversion_cycle": RatioDefinition(
            name="cash_conversion_cycle",
            category=RatioCategory.CASH_FLOW,
            formula="DSO + DIO - DPO",
            required_line_items=[],
            calculate_fn=calculate_cash_conversion_cycle,
            assumptions="Computes DSO, DIO, DPO defaults missing values to 0.0.",
        ),
    }

    @classmethod
    def calculate_ratios(cls, items: dict[str, float]) -> dict[str, float | None]:
        """
        Calculates all registered ratios given a dictionary of line items.
        """
        results: dict[str, float | None] = {}
        for name, defn in cls.DEFINITIONS.items():
            # Check if required line items are present and non-empty
            missing = [item for item in defn.required_line_items if item not in items]
            if missing:
                results[name] = None
                continue
            try:
                val = defn.calculate_fn(items)
                # Run validation rules if any
                is_valid = True
                if hasattr(defn, "validation_rules") and defn.validation_rules:
                    for rule in defn.validation_rules:
                        if not rule(val):
                            is_valid = False
                            break
                results[name] = val if is_valid else None
            except Exception:
                results[name] = None
        return results


def classify_ratio_status(ratio_name: str, value: float) -> str:
    """
    Qualitatively classifies a ratio value into: Excellent, Healthy, Watch, Weak, Critical.
    Driven entirely by boundaries in centralized configuration.
    """
    from app.core.financial_config import financial_config

    bounds = financial_config.scoring_boundaries

    high_key = f"{ratio_name}_high"
    low_key = f"{ratio_name}_low"

    if high_key not in bounds or low_key not in bounds:
        return "Healthy"

    high = bounds[high_key]
    low = bounds[low_key]

    # Ratios where lower is better (negative correlation)
    is_negative = ratio_name in ["debt_to_equity", "debt_ratio"]

    if not is_negative:
        if value >= high:
            return "Excellent"
        elif value >= (high + low) / 2:
            return "Healthy"
        elif value >= low:
            return "Watch"
        elif value >= low / 2:
            return "Weak"
        else:
            return "Critical"
    else:
        # Lower is better (e.g. debt_to_equity)
        if value <= low:
            return "Excellent"
        elif value <= (high + low) / 2:
            return "Healthy"
        elif value <= high:
            return "Watch"
        elif value <= high * 1.5:
            return "Weak"
        else:
            return "Critical"
