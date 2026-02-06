"""
Dashboard and analytics schemas.
"""

from decimal import Decimal
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Summary statistics for dashboard cards."""
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal


class SpendingByCategory(BaseModel):
    """Spending breakdown by category for pie chart."""
    category_id: int
    category_name: str
    amount: Decimal
    percentage: float
    color: str | None


class MonthlyTrend(BaseModel):
    """Monthly income vs expenses for trend chart."""
    month: str  # Format: YYYY-MM
    income: Decimal
    expenses: Decimal
    net: Decimal
