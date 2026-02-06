"""
Pydantic schemas for request/response validation.
"""

from app.schemas.user import UserCreate, UserResponse, Token, TokenData
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    CategoryRuleCreate, CategoryRuleResponse
)
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from app.schemas.income import (
    IncomeSourceCreate, IncomeSourceUpdate, IncomeSourceResponse,
    AssetCreate, AssetUpdate, AssetResponse
)
from app.schemas.dashboard import DashboardSummary, SpendingByCategory, MonthlyTrend

__all__ = [
    "UserCreate", "UserResponse", "Token", "TokenData",
    "AccountCreate", "AccountUpdate", "AccountResponse",
    "CategoryCreate", "CategoryUpdate", "CategoryResponse",
    "CategoryRuleCreate", "CategoryRuleResponse",
    "TransactionCreate", "TransactionUpdate", "TransactionResponse",
    "IncomeSourceCreate", "IncomeSourceUpdate", "IncomeSourceResponse",
    "AssetCreate", "AssetUpdate", "AssetResponse",
    "DashboardSummary", "SpendingByCategory", "MonthlyTrend",
]
