"""
Account schemas for bank accounts and credit cards.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.models.account import AccountType


class AccountCreate(BaseModel):
    """Schema for creating a new account."""
    name: str
    account_type: AccountType = AccountType.CHECKING
    institution: str | None = None
    balance: Decimal = Decimal("0.00")


class AccountUpdate(BaseModel):
    """Schema for updating an account."""
    name: str | None = None
    account_type: AccountType | None = None
    institution: str | None = None
    balance: Decimal | None = None


class AccountResponse(BaseModel):
    """Schema for account response data."""
    id: int
    user_id: int
    name: str
    account_type: AccountType
    institution: str | None
    balance: Decimal
    last_synced: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
