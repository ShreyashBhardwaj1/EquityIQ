"""
Unit tests for the financial statement validation engine.
"""

from uuid import uuid4

import pytest

from app.domain.entities.financial_statement import FinancialStatement, StatementType
from app.domain.exceptions import EntityValidationError
from app.domain.rules.validation import (
    AccountingIdentityRule,
    DuplicateFiscalPeriodRule,
    FiscalPeriodOrderingRule,
    StatementTypeRule,
    ValidationContext,
    ValidationEngine,
)
from app.domain.value_objects.fiscal_period import FiscalPeriod


def test_statement_type_rule_success():
    """Verify StatementTypeRule passes on valid statement types."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.BALANCE,
        fiscal_period=FiscalPeriod("Q1", 2024),
        line_items={},
        normalization_adjustments=[],
        normalized_line_items={},
    )
    context = ValidationContext(existing_statements=[])
    rule = StatementTypeRule()
    # Should not raise exception
    rule.validate(stmt, context)


def test_accounting_identity_rule_balance_sheet_success():
    """Verify AccountingIdentityRule passes on a balanced sheet."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.BALANCE,
        fiscal_period=FiscalPeriod("FY", 2024),
        line_items={
            "total_assets": 100.0,
            "total_liabilities": 60.0,
            "total_equity": 40.0,
        },
        normalization_adjustments=[],
        normalized_line_items={
            "total_assets": 100.0,
            "total_liabilities": 60.0,
            "total_equity": 40.0,
        },
    )
    context = ValidationContext(existing_statements=[])
    rule = AccountingIdentityRule()
    rule.validate(stmt, context)


def test_accounting_identity_rule_balance_sheet_mismatch():
    """Verify AccountingIdentityRule raises EntityValidationError on imbalanced sheet."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.BALANCE,
        fiscal_period=FiscalPeriod("FY", 2024),
        line_items={
            "total_assets": 100.0,
            "total_liabilities": 50.0,
            "total_equity": 40.0,
        },
        normalization_adjustments=[],
        normalized_line_items={
            "total_assets": 100.0,
            "total_liabilities": 50.0,
            "total_equity": 40.0,
        },
    )
    context = ValidationContext(existing_statements=[])
    rule = AccountingIdentityRule()

    with pytest.raises(EntityValidationError, match="Balance sheet identity violation"):
        rule.validate(stmt, context)


def test_duplicate_fiscal_period_rule():
    """Verify DuplicateFiscalPeriodRule flags duplicate statement types for same period."""
    comp_id = uuid4()
    stmt1 = FinancialStatement(
        id=uuid4(),
        company_id=comp_id,
        document_id=uuid4(),
        statement_type=StatementType.INCOME,
        fiscal_period=FiscalPeriod("Q1", 2024),
        line_items={"revenue": 100.0},
        normalization_adjustments=[],
        normalized_line_items={"revenue": 100.0},
    )
    stmt2 = FinancialStatement(
        id=uuid4(),
        company_id=comp_id,
        document_id=uuid4(),
        statement_type=StatementType.INCOME,
        fiscal_period=FiscalPeriod("Q1", 2024),
        line_items={"revenue": 120.0},
        normalization_adjustments=[],
        normalized_line_items={"revenue": 120.0},
    )

    context = ValidationContext(existing_statements=[stmt1])
    rule = DuplicateFiscalPeriodRule()

    with pytest.raises(EntityValidationError, match="Duplicate statement detected"):
        rule.validate(stmt2, context)


def test_fiscal_period_ordering_rule():
    """Verify year bounds validation on FiscalPeriodOrderingRule."""
    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.INCOME,
        fiscal_period=FiscalPeriod("Q1", 1850),
        line_items={},
        normalization_adjustments=[],
        normalized_line_items={},
    )
    context = ValidationContext(existing_statements=[])
    rule = FiscalPeriodOrderingRule()

    with pytest.raises(EntityValidationError, match="out of logical range"):
        rule.validate(stmt, context)


def test_custom_rule_extension():
    """Verify that a custom ValidationRule can be registered and executed in ValidationEngine."""

    class CustomNonNegativeRevenueRule:
        def validate(
            self, statement: FinancialStatement, context: ValidationContext
        ) -> None:
            revenue = statement.normalized_line_items.get("revenue", 0.0)
            if revenue < 0.0:
                raise EntityValidationError("Revenue cannot be negative.")

    engine = ValidationEngine()
    engine.add_rule(CustomNonNegativeRevenueRule())

    stmt = FinancialStatement(
        id=uuid4(),
        company_id=uuid4(),
        document_id=uuid4(),
        statement_type=StatementType.INCOME,
        fiscal_period=FiscalPeriod("Q1", 2024),
        line_items={"revenue": -10.0},
        normalization_adjustments=[],
        normalized_line_items={"revenue": -10.0},
    )
    context = ValidationContext(existing_statements=[])

    with pytest.raises(EntityValidationError, match=r"Revenue cannot be negative\."):
        engine.validate(stmt, context)
