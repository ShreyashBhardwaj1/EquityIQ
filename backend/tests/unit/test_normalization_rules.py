"""
Unit tests for Normalization Rules.
"""

from uuid import uuid4

from app.domain.entities.financial_statement import NormalizationAdjustment
from app.domain.rules.normalization_rules import (
    apply_normalization_adjustments,
    detect_line_item_swings,
)


def test_apply_normalization_adjustments() -> None:
    """Test applying adjustments to statement line items."""
    raw_items = {
        "revenue": 1000.0,
        "operating_income": 150.0,
        "net_income": 100.0,
    }

    doc_id = uuid4()
    adjustments = [
        # Restructuring charge (add back to operating and net income)
        NormalizationAdjustment(
            line_item="operating_income",
            adjustment=30.0,
            reason="One-time restructuring charge",
            source_document_id=doc_id,
            source_page=45,
        ),
        NormalizationAdjustment(
            line_item="net_income",
            adjustment=30.0,
            reason="One-time restructuring charge",
            source_document_id=doc_id,
            source_page=45,
        ),
        # Abnormal insurance recovery (subtract from net income)
        NormalizationAdjustment(
            line_item="net_income",
            adjustment=-10.0,
            reason="One-time insurance payout receipt",
            source_document_id=doc_id,
            source_page=47,
        ),
    ]

    normalized = apply_normalization_adjustments(raw_items, adjustments)

    # Reconciled expectations:
    # revenue: 1000.0 (no adjustments)
    # operating_income: 150.0 + 30.0 = 180.0
    # net_income: 100.0 + 30.0 - 10.0 = 120.0
    assert normalized["revenue"] == 1000.0
    assert normalized["operating_income"] == 180.0
    assert normalized["net_income"] == 120.0


def test_detect_line_item_swings() -> None:
    """Test detection of significant quarter-over-quarter swings (>15%)."""
    prior = {
        "revenue": 1000.0,
        "cogs": 600.0,
        "marketing": 100.0,
        "other": 50.0,
        "stable": 100.0,
    }

    current = {
        "revenue": 1200.0,  # 20% swing (Flag)
        "cogs": 680.0,  # 13.3% swing (No Flag)
        "marketing": 80.0,  # -20% swing (Flag)
        "other": 10.0,  # -80% swing (Flag)
        "stable": 100.0,  # 0% swing (No Flag)
        "new_item": 50.0,  # New item (Flag)
    }

    # Swing detection (using default 15% threshold)
    swings = detect_line_item_swings(current, prior)

    assert "revenue" in swings
    assert "marketing" in swings
    assert "other" in swings
    assert "new_item" in swings
    assert "cogs" not in swings
    assert "stable" not in swings


def test_detect_line_item_swings_custom_threshold() -> None:
    """Test swing detection with a custom swing threshold."""
    prior = {"revenue": 1000.0}
    current = {"revenue": 1060.0}  # 6% swing

    # 5% threshold: should flag
    assert "revenue" in detect_line_item_swings(current, prior, threshold=0.05)

    # 10% threshold: should not flag
    assert "revenue" not in detect_line_item_swings(current, prior, threshold=0.10)
