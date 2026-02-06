"""
Income source and asset models for tracking net worth.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IncomeFrequency(str, Enum):
    """How often income is received."""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ONETIME = "onetime"


class IncomeType(str, Enum):
    """Source type of income."""
    SALARY = "salary"
    FREELANCE = "freelance"
    INVESTMENT = "investment"
    RENTAL = "rental"
    OTHER = "other"


class AssetType(str, Enum):
    """Type of asset."""
    STOCK = "stock"
    BOND = "bond"
    RETIREMENT = "retirement"  # 401k, IRA, etc.
    SAVINGS = "savings"
    PROPERTY = "property"
    VEHICLE = "vehicle"
    CRYPTO = "crypto"
    OTHER = "other"


class IncomeSource(Base):
    """
    Expected income source for budgeting and projections.
    Tracks salary, side income, investments, etc.
    """

    __tablename__ = "income_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    income_type: Mapped[IncomeType] = mapped_column(
        SQLEnum(IncomeType), default=IncomeType.SALARY
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    frequency: Mapped[IncomeFrequency] = mapped_column(
        SQLEnum(IncomeFrequency), default=IncomeFrequency.MONTHLY
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="income_sources")


class Asset(Base):
    """
    Asset for net worth tracking.
    Manually updated values for investments, property, etc.
    """

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(
        SQLEnum(AssetType), default=AssetType.SAVINGS
    )
    value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="assets")
