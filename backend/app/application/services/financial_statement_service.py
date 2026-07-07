"""
Application Service coordinating FinancialStatement CRUD, validation, and version history.
"""

from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.domain.entities.financial_statement import (
    FinancialStatement,
    NormalizationAdjustment,
    StatementType,
)
from app.domain.entities.financial_statement_version import (
    FinancialStatementVersion,
)
from app.domain.exceptions import EntityValidationError
from app.domain.interfaces.repositories import FinancialStatementRepository
from app.domain.rules.normalization import NormalizationEngine, NormalizationRule
from app.domain.rules.normalization_rules import apply_normalization_adjustments
from app.domain.rules.validation import ValidationContext, ValidationEngine
from app.domain.value_objects.fiscal_period import FiscalPeriod

# Default mapping rules standardizing alternate input field names
DEFAULT_NORMALIZATION_RULES = [
    # Balance Sheet mappings
    NormalizationRule(
        alias="Cash & Equivalents",
        canonical_name="cash_equivalents",
        statement_type="balance",
        category="assets",
    ),
    NormalizationRule(
        alias="Cash & Cash Equivalents",
        canonical_name="cash_equivalents",
        statement_type="balance",
        category="assets",
    ),
    NormalizationRule(
        alias="Cash and cash equivalents",
        canonical_name="cash_equivalents",
        statement_type="balance",
        category="assets",
    ),
    NormalizationRule(
        alias="Total Current Assets",
        canonical_name="total_current_assets",
        statement_type="balance",
        category="assets",
    ),
    NormalizationRule(
        alias="Total Current Liabilities",
        canonical_name="total_current_liabilities",
        statement_type="balance",
        category="liabilities",
    ),
    NormalizationRule(
        alias="Total Assets",
        canonical_name="total_assets",
        statement_type="balance",
        category="assets",
        required=True,
    ),
    NormalizationRule(
        alias="Total Liabilities",
        canonical_name="total_liabilities",
        statement_type="balance",
        category="liabilities",
        required=True,
    ),
    NormalizationRule(
        alias="Total Equity",
        canonical_name="total_equity",
        statement_type="balance",
        category="equity",
        required=True,
    ),
    # Income Statement mappings
    NormalizationRule(
        alias="Revenues",
        canonical_name="revenue",
        statement_type="income",
        category="revenue",
        required=True,
    ),
    NormalizationRule(
        alias="Revenue",
        canonical_name="revenue",
        statement_type="income",
        category="revenue",
        required=True,
    ),
    NormalizationRule(
        alias="Gross Profit",
        canonical_name="gross_profit",
        statement_type="income",
        category="profitability",
    ),
    NormalizationRule(
        alias="Operating Income",
        canonical_name="operating_income",
        statement_type="income",
        category="profitability",
    ),
    NormalizationRule(
        alias="Net Income",
        canonical_name="net_income",
        statement_type="income",
        category="net_income",
        required=True,
    ),
    # Cash Flow Statement mappings
    NormalizationRule(
        alias="Operating Cash Flow",
        canonical_name="operating_cash_flow",
        statement_type="cashflow",
        category="cash_flow",
        required=True,
    ),
    NormalizationRule(
        alias="Net cash provided by operating activities",
        canonical_name="operating_cash_flow",
        statement_type="cashflow",
        category="cash_flow",
        required=True,
    ),
    NormalizationRule(
        alias="Capital Expenditures",
        canonical_name="capital_expenditures",
        statement_type="cashflow",
        category="investing",
    ),
]


class FinancialStatementService:
    """
    Coordinates financial statement CRUD, validation guards, and historical revisions.
    """

    def __init__(
        self,
        statement_repo: FinancialStatementRepository,
        normalization_engine: NormalizationEngine | None = None,
        validation_engine: ValidationEngine | None = None,
    ) -> None:
        """
        Initializes FinancialStatementService.
        """
        self.statement_repo = statement_repo
        self.normalization_engine = (
            normalization_engine
            if normalization_engine
            else NormalizationEngine(DEFAULT_NORMALIZATION_RULES)
        )
        self.validation_engine = (
            validation_engine if validation_engine else ValidationEngine()
        )

    async def create_statement(
        self,
        workspace_id: UUID,
        company_id: UUID,
        document_id: UUID,
        statement_type_str: str,
        fiscal_period_str: str,
        line_items: dict[str, float],
    ) -> FinancialStatement:
        """
        Creates, validates, and normalizes a new financial statement record.
        """
        # Validate formatting of types
        try:
            statement_type = StatementType(statement_type_str.lower().strip())
        except ValueError as e:
            raise EntityValidationError(
                f"Unsupported statement type: {statement_type_str}"
            ) from e

        parts = fiscal_period_str.split("-")
        period = parts[0]
        year = int(parts[1]) if len(parts) > 1 else 2000
        fiscal_period = FiscalPeriod(period, year)

        # Apply mapping normalization to line items
        normalized_raw = self.normalization_engine.normalize(
            line_items, statement_type.value
        )

        # Build initial statement entity (no adjustments initially)
        statement = FinancialStatement(
            id=uuid4(),
            company_id=company_id,
            document_id=document_id,
            statement_type=statement_type,
            fiscal_period=fiscal_period,
            line_items=normalized_raw,  # Persist cleaned/canonical raw keys
            normalized_line_items=normalized_raw.copy(),  # Identical since adjustments list is empty
            normalization_adjustments=[],
            extraction_confidence={},
        )

        # Load existing statements in the workspace for company validation checks
        existing = await self.statement_repo.list_by_company(
            company_id=company_id, workspace_id=workspace_id
        )
        context = ValidationContext(existing_statements=existing)

        # Run validations
        self.validation_engine.validate(statement, context)

        # Save to database
        return await self.statement_repo.save(statement)

    async def get_statement(
        self, workspace_id: UUID, statement_id: UUID
    ) -> FinancialStatement:
        """
        Retrieves a financial statement by ID with workspace isolation.
        """
        statement = await self.statement_repo.get(statement_id=statement_id, workspace_id=workspace_id)
        if not statement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial statement not found in this workspace.",
            )
        return statement

    async def list_company_statements(
        self, workspace_id: UUID, company_id: UUID
    ) -> list[FinancialStatement]:
        """
        Lists statements associated with a company in a workspace.
        """
        return await self.statement_repo.list_by_company(company_id=company_id, workspace_id=workspace_id)

    async def update_statement(
        self,
        workspace_id: UUID,
        statement_id: UUID,
        changed_by: UUID,
        change_reason: str,
        line_items: dict[str, float] | None = None,
        adjustments: list[NormalizationAdjustment] | None = None,
    ) -> FinancialStatement:
        """
        Partially updates a statement (line items or adjustments) and logs revision audits.
        """
        # Fetch current statement
        statement = await self.get_statement(workspace_id, statement_id)

        # Retrieve existing version count to compute version increment index
        versions = await self.statement_repo.list_versions(statement_id=statement_id)
        next_ver_index = len(versions) + 1

        # Create Version entry of the OLD state
        old_version = FinancialStatementVersion(
            id=uuid4(),
            statement_id=statement.id,
            version=next_ver_index,
            line_items=statement.line_items,
            normalized_line_items=statement.normalized_line_items,
            normalization_adjustments=statement.normalization_adjustments,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        await self.statement_repo.save_version(version=old_version)

        # Prepare new raw line items
        updated_line_items = statement.line_items
        if line_items is not None:
            # Map raw items using the normalization mapping aliases
            updated_line_items = self.normalization_engine.normalize(
                line_items, statement.statement_type.value
            )

        # Prepare adjustments
        updated_adjustments = statement.normalization_adjustments
        if adjustments is not None:
            updated_adjustments = adjustments

        # Recalculate normalized values: normalized = raw + adjustments
        updated_normalized = apply_normalization_adjustments(
            updated_line_items, updated_adjustments
        )

        # Build updated statement entity
        updated_statement = FinancialStatement(
            id=statement.id,
            company_id=statement.company_id,
            document_id=statement.document_id,
            statement_type=statement.statement_type,
            fiscal_period=statement.fiscal_period,
            line_items=updated_line_items,
            normalized_line_items=updated_normalized,
            normalization_adjustments=updated_adjustments,
            extraction_confidence=statement.extraction_confidence,
        )

        # Run validations
        existing = await self.statement_repo.list_by_company(
            company_id=statement.company_id, workspace_id=workspace_id
        )
        context = ValidationContext(existing_statements=existing)
        self.validation_engine.validate(updated_statement, context)

        # Save to database
        return await self.statement_repo.save(updated_statement)

    async def delete_statement(
        self, workspace_id: UUID, statement_id: UUID
    ) -> None:
        """
        Deletes a statement from a workspace context.
        """
        # Verify exists first
        await self.get_statement(workspace_id, statement_id)
        await self.statement_repo.delete(statement_id=statement_id, workspace_id=workspace_id)

    async def list_statement_versions(
        self, workspace_id: UUID, statement_id: UUID
    ) -> list[FinancialStatementVersion]:
        """
        Lists historical versions of a financial statement.
        """
        # Verify statement access first
        await self.get_statement(workspace_id, statement_id)
        return await self.statement_repo.list_versions(statement_id=statement_id)
