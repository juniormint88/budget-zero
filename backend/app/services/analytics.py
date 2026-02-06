"""
Analytics service for dashboard calculations and reporting.
"""

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account, AccountType
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.income import IncomeSource, Asset, IncomeFrequency


class AnalyticsService:
    """
    Service for computing financial analytics and reports.
    Provides methods for calculating summaries, trends, and projections.
    """

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    async def get_account_ids(self) -> list[int]:
        """Get all account IDs for the current user."""
        result = await self.db.execute(
            select(Account.id).where(Account.user_id == self.user_id)
        )
        return [row[0] for row in result.all()]

    async def calculate_monthly_income(self) -> Decimal:
        """
        Calculate total expected monthly income from all sources.
        Normalizes all income frequencies to monthly amounts.
        """
        result = await self.db.execute(
            select(IncomeSource)
            .where(
                IncomeSource.user_id == self.user_id,
                IncomeSource.is_active == True
            )
        )
        sources = result.scalars().all()

        total_monthly = Decimal("0")
        for source in sources:
            monthly_amount = self._normalize_to_monthly(source.amount, source.frequency)
            total_monthly += monthly_amount

        return total_monthly

    def _normalize_to_monthly(self, amount: Decimal, frequency: IncomeFrequency) -> Decimal:
        """Convert any frequency amount to monthly equivalent."""
        multipliers = {
            IncomeFrequency.WEEKLY: Decimal("4.33"),      # ~52 weeks / 12 months
            IncomeFrequency.BIWEEKLY: Decimal("2.17"),    # ~26 periods / 12 months
            IncomeFrequency.MONTHLY: Decimal("1"),
            IncomeFrequency.QUARTERLY: Decimal("0.33"),   # 4 per year / 12 months
            IncomeFrequency.ANNUAL: Decimal("0.0833"),    # 1 per year / 12 months
            IncomeFrequency.ONETIME: Decimal("0"),        # One-time doesn't count for monthly
        }
        return amount * multipliers.get(frequency, Decimal("1"))

    async def calculate_spending_trend(
        self,
        category_id: int | None = None,
        months: int = 6
    ) -> list[dict]:
        """
        Calculate spending trend over time for a category or all categories.
        Returns monthly totals for charting.
        """
        account_ids = await self.get_account_ids()
        if not account_ids:
            return []

        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        query = (
            select(
                func.to_char(Transaction.date, 'YYYY-MM').label("month"),
                func.sum(func.abs(Transaction.amount)).label("total")
            )
            .where(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.is_income == False,
                Transaction.amount < 0
            )
            .group_by(func.to_char(Transaction.date, 'YYYY-MM'))
            .order_by(func.to_char(Transaction.date, 'YYYY-MM'))
        )

        if category_id:
            query = query.where(Transaction.category_id == category_id)

        result = await self.db.execute(query)
        return [{"month": row[0], "total": row[1]} for row in result.all()]

    async def calculate_average_spending(
        self,
        category_id: int | None = None,
        months: int = 3
    ) -> Decimal:
        """
        Calculate average monthly spending for budgeting purposes.
        Uses last N months of data.
        """
        account_ids = await self.get_account_ids()
        if not account_ids:
            return Decimal("0")

        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        query = (
            select(func.sum(func.abs(Transaction.amount)))
            .where(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.is_income == False,
                Transaction.amount < 0
            )
        )

        if category_id:
            query = query.where(Transaction.category_id == category_id)

        result = await self.db.execute(query)
        total = result.scalar() or Decimal("0")

        return total / months

    async def get_top_merchants(
        self,
        limit: int = 10,
        months: int = 3
    ) -> list[dict]:
        """Get top merchants by total spending."""
        account_ids = await self.get_account_ids()
        if not account_ids:
            return []

        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        result = await self.db.execute(
            select(
                Transaction.description,
                func.sum(func.abs(Transaction.amount)).label("total"),
                func.count(Transaction.id).label("count")
            )
            .where(
                Transaction.account_id.in_(account_ids),
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.is_income == False,
                Transaction.amount < 0
            )
            .group_by(Transaction.description)
            .order_by(func.sum(func.abs(Transaction.amount)).desc())
            .limit(limit)
        )

        return [
            {
                "merchant": row[0],
                "total": row[1],
                "transaction_count": row[2]
            }
            for row in result.all()
        ]

    async def get_uncategorized_count(self) -> int:
        """Get count of uncategorized transactions."""
        account_ids = await self.get_account_ids()
        if not account_ids:
            return 0

        result = await self.db.execute(
            select(func.count(Transaction.id))
            .where(
                Transaction.account_id.in_(account_ids),
                Transaction.category_id.is_(None)
            )
        )
        return result.scalar() or 0

    async def calculate_net_worth_history(self, months: int = 12) -> list[dict]:
        """
        Calculate net worth at end of each month.
        Note: This is a simplified calculation based on current values.
        True historical tracking would require storing balance snapshots.
        """
        # For now, return current net worth
        # TODO: Implement balance history tracking for true historical net worth

        # Get current assets
        asset_result = await self.db.execute(
            select(func.sum(Asset.value))
            .where(Asset.user_id == self.user_id)
        )
        total_assets = asset_result.scalar() or Decimal("0")

        # Add positive account balances
        balance_result = await self.db.execute(
            select(func.sum(Account.balance))
            .where(
                Account.user_id == self.user_id,
                Account.balance > 0,
                Account.account_type.in_([
                    AccountType.CHECKING,
                    AccountType.SAVINGS,
                    AccountType.INVESTMENT
                ])
            )
        )
        total_assets += balance_result.scalar() or Decimal("0")

        # Get liabilities
        liability_result = await self.db.execute(
            select(func.sum(func.abs(Account.balance)))
            .where(
                Account.user_id == self.user_id,
                Account.account_type.in_([AccountType.CREDIT, AccountType.LOAN])
            )
        )
        total_liabilities = liability_result.scalar() or Decimal("0")

        net_worth = total_assets - total_liabilities

        # Return current value (historical tracking not yet implemented)
        return [{
            "date": date.today().isoformat(),
            "assets": total_assets,
            "liabilities": total_liabilities,
            "net_worth": net_worth
        }]
