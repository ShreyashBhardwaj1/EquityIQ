"""
FinancialStatementVersion entity representing historical versions of financial statements.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.financial_statement import NormalizationAdjustment


class FinancialStatementVersion(BaseModel):
    """
    Tracks versions of financial statement line items and adjustments over time.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Unique identifier for the version record")
    statement_id: UUID = Field(description="Associated financial statement ID")
    version: int = Field(ge=1, description="Version increment number")
    line_items: dict[str, float] = Field(
        default_factory=dict, description="Historical raw line items"
    )
    normalized_line_items: dict[str, float] = Field(
        default_factory=dict, description="Historical normalized line items"
    )
    normalization_adjustments: list[NormalizationAdjustment] = Field(
        default_factory=list, description="Historical normalization adjustments"
    )
    changed_by: UUID = Field(description="UUID of user initiating change")
    change_reason: str = Field(min_length=1, description="Reason for update")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
