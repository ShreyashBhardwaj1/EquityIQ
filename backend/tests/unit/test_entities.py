"""
Unit tests for Domain Entities.
"""

from uuid import uuid4

import pytest

from app.domain.entities.company import Company
from app.domain.entities.document import Document, DocumentType, ParsingStatus
from app.domain.entities.financial_statement import (
    FinancialStatement,
    NormalizationAdjustment,
    StatementType,
)
from app.domain.entities.ratio import Ratio
from app.domain.entities.recommendation import Recommendation, RecommendationType
from app.domain.entities.valuation import (
    ComparableCompanyAssumptions,
    DCFAssumptions,
    Valuation,
    ValuationMethod,
)
from app.domain.exceptions import EntityValidationError
from app.domain.value_objects.exchange import Exchange
from app.domain.value_objects.fiscal_period import FiscalPeriod
from app.domain.value_objects.ticker import Ticker


def test_company_creation() -> None:
    """Test valid instantiation and pattern validation of Company entity."""
    comp = Company(
        id=uuid4(),
        workspace_id=uuid4(),
        ticker=Ticker("AAPL"),
        exchange=Exchange("NASDAQ"),
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        country="US",
        fiscal_year_end="09-30",
        currency="USD",
    )
    assert comp.name == "Apple Inc."
    assert comp.ticker.symbol == "AAPL"
    assert comp.fiscal_year_end == "09-30"


def test_document_creation() -> None:
    """Test valid instantiation of Document entity."""
    doc = Document(
        id=uuid4(),
        workspace_id=uuid4(),
        company_id=uuid4(),
        doc_type=DocumentType.TEN_K,
        fiscal_period=FiscalPeriod("FY", 2024),
        storage_path="s3://bucket/filings/aapl-10k-2024.pdf",
        uploaded_by=uuid4(),
    )
    assert doc.doc_type == DocumentType.TEN_K
    assert doc.parsing_status == ParsingStatus.PENDING


def test_financial_statement_valid_balance_sheet() -> None:
    """Test accounting identity validation on a valid balance sheet."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.BALANCE,
        fiscal_period=FiscalPeriod("FY", 2024),
        line_items={
            "total_assets": 1000.0,
            "total_liabilities": 600.0,
            "total_equity": 400.0,
        },
    )
    # Assets = Liabilities + Equity (1000 = 600 + 400). Should not raise error.
    stmt.validate_accounting_identity()


def test_financial_statement_invalid_balance_sheet() -> None:
    """Test accounting identity validation raises on an invalid balance sheet."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.BALANCE,
        fiscal_period=FiscalPeriod("FY", 2024),
        line_items={
            "total_assets": 1000.0,
            "total_liabilities": 600.0,
            "total_equity": 390.0,  # 10.0 discrepancy
        },
    )
    with pytest.raises(EntityValidationError):
        stmt.validate_accounting_identity()


def test_financial_statement_balance_sheet_with_adjustments() -> None:
    """Test identity validation on a balance sheet normalized via adjustments."""
    # Raw items are out of balance: Assets=1000, Liab=600, Eq=390
    # Adjustment adds 10.0 to equity
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.BALANCE,
        fiscal_period=FiscalPeriod("FY", 2024),
        line_items={
            "total_assets": 1000.0,
            "total_liabilities": 600.0,
            "total_equity": 390.0,
        },
        normalization_adjustments=[
            NormalizationAdjustment(
                line_item="total_equity",
                adjustment=10.0,
                reason="Reclassify non-controlling interest",
                source_document_id=uuid4(),
                source_page=12,
            )
        ],
        normalized_line_items={
            "total_assets": 1000.0,
            "total_liabilities": 600.0,
            "total_equity": 400.0,
        },
    )
    # Should validate against normalized_line_items successfully
    stmt.validate_accounting_identity()


def test_financial_statement_non_balance_sheet_validation() -> None:
    """Test that validation skips non-balance sheet statements."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.INCOME,
        fiscal_period=FiscalPeriod("FY", 2024),
        line_items={"revenue": 1000.0, "net_income": 100.0},
    )
    # Should exit early without validation checks.
    stmt.validate_accounting_identity()


def test_financial_statement_identity_missing_keys() -> None:
    """Test that validation raises an error if balance sheet keys are missing."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.BALANCE,
        fiscal_period=FiscalPeriod("FY", 2024),
        line_items={"total_assets": 1000.0},  # missing liab and equity
    )
    with pytest.raises(EntityValidationError):
        stmt.validate_accounting_identity()


def test_financial_statement_alternative_key_names() -> None:
    """Test accounting identity with alternative key names (assets, liabilities, equity)."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.BALANCE,
        fiscal_period=FiscalPeriod("FY", 2024),
        line_items={
            "assets": 1000.0,
            "liabilities": 600.0,
            "equity": 400.0,
        },
    )
    # Assets = Liabilities + Equity (1000 = 600 + 400).
    stmt.validate_accounting_identity()


def test_ratio_creation() -> None:
    """Test Ratio entity properties."""
    ratio = Ratio(
        id=uuid4(),
        company_id=uuid4(),
        fiscal_period=FiscalPeriod("Q1", 2025),
        ratio_name="current_ratio",
        value=2.15,
        formula_version="1.0.0",
    )
    assert ratio.ratio_name == "current_ratio"
    assert ratio.value == 2.15


def test_valuation_creation() -> None:
    """Test Valuation entity properties with strongly typed assumptions."""
    dcf_assumptions = DCFAssumptions(
        wacc=0.08,
        terminal_growth=0.02,
        projection_years=5,
        net_debt=200.0,
        shares_outstanding=10.0,
    )
    val = Valuation(
        id=uuid4(),
        company_id=uuid4(),
        method=ValuationMethod.DCF,
        assumptions=dcf_assumptions,
        result={"intrinsic_value_per_share": 145.20},
    )
    assert val.method == ValuationMethod.DCF
    assert isinstance(val.assumptions, DCFAssumptions)
    assert val.assumptions.wacc == 0.08
    assert val.result["intrinsic_value_per_share"] == 145.20

    comps_assumptions = ComparableCompanyAssumptions(
        peers=["MSFT", "GOOGL"],
        multiples=["P/E", "EV/EBITDA"],
    )
    val_comps = Valuation(
        id=uuid4(),
        company_id=uuid4(),
        method=ValuationMethod.COMPS,
        assumptions=comps_assumptions,
        result={"valuation_multiple_median": 25.5},
    )
    assert val_comps.method == ValuationMethod.COMPS
    assert isinstance(val_comps.assumptions, ComparableCompanyAssumptions)
    assert "MSFT" in val_comps.assumptions.peers


def test_recommendation_creation() -> None:
    """Test Recommendation entity properties."""
    rec = Recommendation(
        id=uuid4(),
        company_id=uuid4(),
        recommendation=RecommendationType.BUY,
        composite_score=8.5,
        rationale="Strong balance sheet and 25% upside to DCF.",
    )
    assert rec.recommendation == RecommendationType.BUY
    assert rec.composite_score == 8.5
