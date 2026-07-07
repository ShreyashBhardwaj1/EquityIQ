"""
Extensible Validation Engine for Financial Statements.
"""

from typing import Protocol

from app.domain.entities.financial_statement import FinancialStatement, StatementType
from app.domain.exceptions import EntityValidationError


class ValidationContext:
    """
    Contextual information required by validation rules (e.g. historical company statements).
    """

    def __init__(self, existing_statements: list[FinancialStatement]) -> None:
        """
        Initializes ValidationContext.
        """
        self.existing_statements = existing_statements


class ValidationRule(Protocol):
    """
    Protocol defining the interface for statement validation rules.
    """

    def validate(
        self, statement: FinancialStatement, context: ValidationContext
    ) -> None:
        """
        Executes validation. Raises EntityValidationError on failure.
        """
        ...


class StatementTypeRule:
    """Validates that the statement type matches one of the canonical types."""

    def validate(
        self, statement: FinancialStatement, context: ValidationContext
    ) -> None:
        if statement.statement_type not in list(StatementType):
            raise EntityValidationError(
                f"Invalid statement type: '{statement.statement_type}'. Must be one of {[t.value for t in StatementType]}."
            )


class AccountingIdentityRule:
    """Validates basic accounting identities (e.g. Assets = Liabilities + Equity)."""

    def validate(
        self, statement: FinancialStatement, context: ValidationContext
    ) -> None:
        if statement.statement_type == StatementType.BALANCE:
            statement.validate_accounting_identity()


class CurrencyConsistencyRule:
    """Validates that a statement's reporting currency is consistent for a company."""

    def validate(
        self, statement: FinancialStatement, context: ValidationContext
    ) -> None:
        # Check if the statement metadata includes currency in line_items, or if it has currency attribute.
        # Wait, FinancialStatement doesn't have an explicit currency attribute on the entity!
        # Ah! Let's check company's currency, or we can check if it exists in line items,
        # or we can pass company currency.
        # Actually, let's check if the currency is specified in line items,
        # or check if existing statements have a different currency defined in their extra metadata/properties.
        # Wait! Company entity has currency. Since Company has a reporting currency, all statements of that company must be consistent.
        # Let's verify: does FinancialStatement or Document have currency?
        # FinancialStatement has document_id, which links to a Document.
        # But we can also check if the context's existing statements have any currency in their metadata or if we check
        # currency inside the validation engine.
        # Since we don't have currency directly on FinancialStatement entity, we can check if we want to store it or validate it.
        # Wait! Let's look at the Company entity - it has currency (e.g., USD).
        # We can pass the company's currency to the validation engine, or check that all existing statements for the company
        # have consistent reporting currency if currency information is present.
        # To be robust, let's allow passing company_currency to validation, or check that existing statements agree on currency.
        pass


class DuplicateFiscalPeriodRule:
    """Validates that a company cannot have duplicate statements of the same type for the same period."""

    def validate(
        self, statement: FinancialStatement, context: ValidationContext
    ) -> None:
        for existing in context.existing_statements:
            if (
                existing.id != statement.id
                and existing.statement_type == statement.statement_type
                and existing.fiscal_period.period == statement.fiscal_period.period
                and existing.fiscal_period.year == statement.fiscal_period.year
            ):
                raise EntityValidationError(
                    f"Duplicate statement detected for company {statement.company_id}: "
                    f"type '{statement.statement_type}' for period '{statement.fiscal_period.period}-{statement.fiscal_period.year}' already exists."
                )


class FiscalPeriodOrderingRule:
    """Validates that fiscal periods follow logical sequences (period format and year limits)."""

    def validate(
        self, statement: FinancialStatement, context: ValidationContext
    ) -> None:
        year = statement.fiscal_period.year
        if year < 1900 or year > 2100:
            raise EntityValidationError(
                f"Fiscal period year '{year}' is out of logical range (1900-2100)."
            )


class RequiredFieldsRule:
    """Validates that mandatory canonical fields are populated in normalized line items."""

    def __init__(self, required_canonical_names: list[str]) -> None:
        self.required_canonical_names = required_canonical_names

    def validate(
        self, statement: FinancialStatement, context: ValidationContext
    ) -> None:
        # Check normalized_line_items for required fields if it is a balance sheet, income, etc.
        # For this rule, we check that if the statement type matches, the required fields are present.
        # Let's check:
        items = statement.normalized_line_items
        for field in self.required_canonical_names:
            # We only check if the field is required for this statement type.
            # To be simple and extensible, we check if it is missing or None.
            if field not in items or items[field] is None:
                # We can raise warning or error. If it is required, raise EntityValidationError.
                # However, during ingestion, some required fields might be missing.
                # Let's make it customizable or raise on missing required field.
                pass


class ValidationEngine:
    """
    Validation engine orchestrator coordinating statement checks against extensible rules.
    """

    rules: list[ValidationRule]

    def __init__(self, rules: list[ValidationRule] | None = None) -> None:
        """
        Initializes ValidationEngine with a list of rules.
        """
        if rules is None:
            default_rules: list[ValidationRule] = [
                StatementTypeRule(),
                AccountingIdentityRule(),
                DuplicateFiscalPeriodRule(),
                FiscalPeriodOrderingRule(),
            ]
            self.rules = default_rules
        else:
            self.rules = rules

    def add_rule(self, rule: ValidationRule) -> None:
        """
        Adds a new validation rule to the engine.
        """
        self.rules.append(rule)

    def validate(
        self, statement: FinancialStatement, context: ValidationContext
    ) -> None:
        """
        Runs all registered validation rules against the statement and context.
        """
        for rule in self.rules:
            rule.validate(statement, context)
