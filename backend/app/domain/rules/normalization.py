"""
Deterministic Rules-based Normalization Engine.
"""

from pydantic import BaseModel, Field


class NormalizationRule(BaseModel):
    """
    Rule definition for standardizing a raw financial line item key.
    """

    alias: str = Field(description="Raw string name found in filings/data sources")
    canonical_name: str = Field(description="Standardized name inside the system")
    statement_type: str | None = Field(
        default=None, description="Optional restriction to statement type (e.g. balance)"
    )
    category: str | None = Field(
        default=None, description="Optional classification category (e.g. current_assets)"
    )
    required: bool = Field(
        default=False, description="Flag indicating if this item must be present"
    )
    priority: int = Field(
        default=0, description="Precedence priority order when applying mapping rules"
    )


class NormalizationEngine:
    """
    Enforces deterministic normalization of raw line items using mapping rules.
    """

    def __init__(self, rules: list[NormalizationRule]) -> None:
        """
        Initializes the NormalizationEngine.
        """
        self.rules = rules

    def normalize(
        self, raw_items: dict[str, float], statement_type: str | None = None
    ) -> dict[str, float]:
        """
        Standardizes raw input keys into canonical internal representations.
        Unmapped keys are preserved as-is.
        """
        normalized_items: dict[str, float] = {}

        # Build lookup mapping: lowercase alias -> canonical name
        alias_mapping: dict[str, str] = {}
        # Sort rules by priority desc so higher priority rules override lower ones
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        for rule in sorted_rules:
            # Filter by statement type if both are specified
            if (
                rule.statement_type is None
                or statement_type is None
                or rule.statement_type.lower().strip()
                == statement_type.lower().strip()
            ):
                alias_mapping[rule.alias.lower().strip()] = rule.canonical_name

        for key, value in raw_items.items():
            key_clean = key.lower().strip()
            if key_clean in alias_mapping:
                canonical = alias_mapping[key_clean]
                normalized_items[canonical] = value
            else:
                normalized_items[key] = value

        return normalized_items

    def check_required_fields(
        self, normalized_items: dict[str, float], statement_type: str | None = None
    ) -> list[str]:
        """
        Checks if any required fields are missing in the normalized items.
        Returns a list of missing canonical required fields.
        """
        missing: list[str] = []
        for rule in self.rules:
            if rule.required:
                if (
                    rule.statement_type is None
                    or statement_type is None
                    or rule.statement_type.lower().strip()
                    == statement_type.lower().strip()
                ):
                    if rule.canonical_name not in normalized_items:
                        missing.append(rule.canonical_name)
        return missing
