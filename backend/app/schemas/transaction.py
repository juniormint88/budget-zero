"""
Transaction schemas for financial transactions.
"""

from datetime import datetime
from datetime import date as date_type
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    account_id: int
    date: date_type
    description: str
    amount: Decimal
    category_id: Optional[int] = None
    is_income: bool = False
    merchant: Optional[str] = None
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    date: Optional[date_type] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    category_id: Optional[int] = None
    is_income: Optional[bool] = None
    merchant: Optional[str] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    """Schema for transaction response data."""
    id: int
    account_id: int
    category_id: Optional[int]
    date: date_type
    description: str
    amount: Decimal
    is_income: bool
    merchant: Optional[str]
    notes: Optional[str]
    import_hash: Optional[str]
    created_at: datetime
    category_name: Optional[str] = None  # Populated from join

    class Config:
        from_attributes = True


class TransactionImport(BaseModel):
    """Schema for importing transactions from file."""
    date: date_type
    description: str
    amount: Decimal
    is_income: bool = False


class ImportResult(BaseModel):
    """Result of a transaction import operation."""
    total: int
    imported: int
    skipped: int  # Duplicates
    errors: list[str]
