"""
Income source and asset schemas.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.models.income import IncomeType, IncomeFrequency, AssetType


class IncomeSourceCreate(BaseModel):
    """Schema for creating an income source."""
    name: str
    income_type: IncomeType = IncomeType.SALARY
    amount: Decimal
    frequency: IncomeFrequency = IncomeFrequency.MONTHLY
    is_active: bool = True


class IncomeSourceUpdate(BaseModel):
    """Schema for updating an income source."""
    name: str | None = None
    income_type: IncomeType | None = None
    amount: Decimal | None = None
    frequency: IncomeFrequency | None = None
    is_active: bool | None = None


class IncomeSourceResponse(BaseModel):
    """Schema for income source response data."""
    id: int
    user_id: int
    name: str
    income_type: IncomeType
    amount: Decimal
    frequency: IncomeFrequency
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AssetCreate(BaseModel):
    """Schema for creating an asset."""
    name: str
    asset_type: AssetType = AssetType.SAVINGS
    value: Decimal


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""
    name: str | None = None
    asset_type: AssetType | None = None
    value: Decimal | None = None


class AssetResponse(BaseModel):
    """Schema for asset response data."""
    id: int
    user_id: int
    name: str
    asset_type: AssetType
    value: Decimal
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True
