"""
Transaction schemas for financial transactions.
"""

from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    account_id: int
    date: date
    description: str
    amount: Decimal
    category_id: int | None = None
    is_income: bool = False
    merchant: str | None = None
    notes: str | None = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    date: date | None = None
    description: str | None = None
    amount: Decimal | None = None
    category_id: int | None = None
    is_income: bool | None = None
    merchant: str | None = None
    notes: str | None = None


class TransactionResponse(BaseModel):
    """Schema for transaction response data."""
    id: int
    account_id: int
    category_id: int | None
    date: date
    description: str
    amount: Decimal
    is_income: bool
    merchant: str | None
    notes: str | None
    import_hash: str | None
    created_at: datetime
    category_name: str | None = None  # Populated from join

    class Config:
        from_attributes = True


class TransactionImport(BaseModel):
    """Schema for importing transactions from file."""
    date: date
    description: str
    amount: Decimal
    is_income: bool = False


class ImportResult(BaseModel):
    """Result of a transaction import operation."""
    total: int
    imported: int
    skipped: int  # Duplicates
    errors: list[str]
