"""
Unit tests for the rules-based financial normalization pipeline.
"""

from app.domain.rules.normalization import NormalizationEngine, NormalizationRule


def test_normalization_aliases():
    """Verify raw aliases standardise to canonical names."""
    rules = [
        NormalizationRule(
            alias="Cash & Equivalents",
            canonical_name="cash_equivalents",
            statement_type="balance",
            category="assets",
        ),
        NormalizationRule(
            alias="Total Assets",
            canonical_name="total_assets",
            statement_type="balance",
            category="assets",
        ),
    ]

    engine = NormalizationEngine(rules)

    raw_items = {
        "Cash & Equivalents": 100.0,
        "Total Assets": 1000.0,
        "Operating Income": 150.0,  # Unmapped field
    }

    normalized = engine.normalize(raw_items, statement_type="balance")

    assert normalized["cash_equivalents"] == 100.0
    assert normalized["total_assets"] == 1000.0
    assert normalized["Operating Income"] == 150.0  # Keep unmapped fields as-is


def test_normalization_filtering_by_statement_type():
    """Verify normalization rules only apply to the matching statement type."""
    rules = [
        NormalizationRule(
            alias="Revenue",
            canonical_name="revenue",
            statement_type="income",
        ),
        NormalizationRule(
            alias="Revenue",
            canonical_name="unrelated_balance_key",
            statement_type="balance",
        ),
    ]

    engine = NormalizationEngine(rules)

    raw_items = {"Revenue": 500.0}

    # Normalize as income statement
    normalized_income = engine.normalize(raw_items, statement_type="income")
    assert normalized_income["revenue"] == 500.0
    assert "unrelated_balance_key" not in normalized_income

    # Normalize as balance sheet
    normalized_balance = engine.normalize(raw_items, statement_type="balance")
    assert normalized_balance["unrelated_balance_key"] == 500.0
    assert "revenue" not in normalized_balance


def test_required_fields_check():
    """Verify that required fields helper flags missing elements."""
    rules = [
        NormalizationRule(
            alias="Total Assets",
            canonical_name="total_assets",
            statement_type="balance",
            required=True,
        ),
        NormalizationRule(
            alias="Cash",
            canonical_name="cash",
            statement_type="balance",
            required=False,
        ),
    ]

    engine = NormalizationEngine(rules)

    # Assets is missing
    items1 = {"cash": 50.0}
    missing1 = engine.check_required_fields(items1, statement_type="balance")
    assert "total_assets" in missing1

    # Assets is present
    items2 = {"total_assets": 100.0, "cash": 50.0}
    missing2 = engine.check_required_fields(items2, statement_type="balance")
    assert len(missing2) == 0
