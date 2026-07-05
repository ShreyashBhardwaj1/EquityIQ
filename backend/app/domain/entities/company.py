"""
Company entity representing a tracked corporation.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects.exchange import Exchange
from app.domain.value_objects.ticker import Ticker


class Company(BaseModel):
    """
    Company domain entity representing a publicly traded corporation.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: UUID = Field(description="Unique identifier for the company")
    ticker: Ticker = Field(description="Stock ticker symbol value object")
    exchange: Exchange = Field(description="Listing exchange value object")
    name: str = Field(min_length=1, description="Official company name")
    sector: str = Field(min_length=1, description="Macro economic sector")
    industry: str = Field(min_length=1, description="Micro industry classification")
    fiscal_year_end: str = Field(
        pattern=r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$",
        description="Fiscal year end date in MM-DD format",
    )
    currency: str = Field(
        min_length=3, max_length=3, description="ISO 4217 reporting currency code"
    )
