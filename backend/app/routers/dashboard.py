"""
Dashboard router for analytics and summary data.
"""

from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.account import Account, AccountType
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.income import Asset
from app.schemas.dashboard import DashboardSummary, SpendingByCategory, MonthlyTrend
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    months: int = Query(1, ge=1, le=12, description="Number of months to include"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics for the dashboard.
    Includes income, expenses, net cash flow, and net worth.
    """
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)

    # Get user's account IDs
    account_result = await db.execute(
        select(Account.id).where(Account.user_id == current_user.id)
    )
    account_ids = [row[0] for row in account_result.all()]

    if not account_ids:
        return DashboardSummary(
            total_income=Decimal("0.00"),
            total_expenses=Decimal("0.00"),
            net_cash_flow=Decimal("0.00"),
            total_assets=Decimal("0.00"),
            total_liabilities=Decimal("0.00"),
            net_worth=Decimal("0.00"),
        )

    # Calculate total income (positive amounts marked as income)
    income_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_income == True
        )
    )
    total_income = income_result.scalar() or Decimal("0.00")

    # Calculate total expenses (negative amounts or not marked as income)
    expense_result = await db.execute(
        select(func.coalesce(func.sum(func.abs(Transaction.amount)), 0))
        .where(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_income == False,
            Transaction.amount < 0
        )
    )
    total_expenses = expense_result.scalar() or Decimal("0.00")

    # Net cash flow
    net_cash_flow = total_income - total_expenses

    # Get total assets
    asset_result = await db.execute(
        select(func.coalesce(func.sum(Asset.value), 0))
        .where(Asset.user_id == current_user.id)
    )
    total_assets = asset_result.scalar() or Decimal("0.00")

    # Add account balances that are positive (checking, savings)
    positive_balance_result = await db.execute(
        select(func.coalesce(func.sum(Account.balance), 0))
        .where(
            Account.user_id == current_user.id,
            Account.balance > 0,
            Account.account_type.in_([AccountType.CHECKING, AccountType.SAVINGS, AccountType.INVESTMENT])
        )
    )
    total_assets += positive_balance_result.scalar() or Decimal("0.00")

    # Get total liabilities (credit card debt, loans)
    liability_result = await db.execute(
        select(func.coalesce(func.sum(func.abs(Account.balance)), 0))
        .where(
            Account.user_id == current_user.id,
            Account.account_type.in_([AccountType.CREDIT, AccountType.LOAN])
        )
    )
    total_liabilities = liability_result.scalar() or Decimal("0.00")

    # Net worth
    net_worth = total_assets - total_liabilities

    return DashboardSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net_cash_flow=net_cash_flow,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth,
    )


@router.get("/spending-by-category", response_model=list[SpendingByCategory])
async def get_spending_by_category(
    months: int = Query(1, ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get spending breakdown by category for pie chart."""
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)

    # Get user's account IDs
    account_result = await db.execute(
        select(Account.id).where(Account.user_id == current_user.id)
    )
    account_ids = [row[0] for row in account_result.all()]

    if not account_ids:
        return []

    # Query spending by category
    result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.color,
            func.sum(func.abs(Transaction.amount)).label("total")
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_income == False,
            Transaction.amount < 0
        )
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(func.abs(Transaction.amount)).desc())
    )
    rows = result.all()

    if not rows:
        return []

    # Calculate percentages
    total_spending = sum(row[3] for row in rows)
    categories = []
    for row in rows:
        amount = row[3]
        percentage = float(amount / total_spending * 100) if total_spending else 0
        categories.append(SpendingByCategory(
            category_id=row[0],
            category_name=row[1],
            amount=amount,
            percentage=round(percentage, 1),
            color=row[2],
        ))

    return categories


@router.get("/monthly-trend", response_model=list[MonthlyTrend])
async def get_monthly_trend(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get monthly income vs expenses trend for line chart."""
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)

    # Get user's account IDs
    account_result = await db.execute(
        select(Account.id).where(Account.user_id == current_user.id)
    )
    account_ids = [row[0] for row in account_result.all()]

    if not account_ids:
        return []

    # Query monthly totals
    result = await db.execute(
        select(
            func.to_char(Transaction.date, 'YYYY-MM').label("month"),
            func.sum(
                func.case(
                    (Transaction.is_income == True, Transaction.amount),
                    else_=Decimal("0")
                )
            ).label("income"),
            func.sum(
                func.case(
                    ((Transaction.is_income == False) & (Transaction.amount < 0),
                     func.abs(Transaction.amount)),
                    else_=Decimal("0")
                )
            ).label("expenses"),
        )
        .where(
            Transaction.account_id.in_(account_ids),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
        )
        .group_by(func.to_char(Transaction.date, 'YYYY-MM'))
        .order_by(func.to_char(Transaction.date, 'YYYY-MM'))
    )
    rows = result.all()

    trends = []
    for row in rows:
        income = row[1] or Decimal("0")
        expenses = row[2] or Decimal("0")
        trends.append(MonthlyTrend(
            month=row[0],
            income=income,
            expenses=expenses,
            net=income - expenses,
        ))

    return trends


@router.get("/recent-transactions", response_model=list[dict])
async def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get most recent transactions for quick view."""
    result = await db.execute(
        select(
            Transaction.id,
            Transaction.date,
            Transaction.description,
            Transaction.amount,
            Transaction.is_income,
            Category.name.label("category_name"),
            Category.color.label("category_color"),
            Account.name.label("account_name"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(Account.user_id == current_user.id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(limit)
    )
    rows = result.all()

    return [
        {
            "id": row[0],
            "date": row[1].isoformat(),
            "description": row[2],
            "amount": str(row[3]),
            "is_income": row[4],
            "category_name": row[5],
            "category_color": row[6],
            "account_name": row[7],
        }
        for row in rows
    ]
