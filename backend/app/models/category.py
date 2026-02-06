"""
Category models for transaction categorization.
Includes categories and user-defined categorization rules.
"""

from enum import Enum
from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CategoryType(str, Enum):
    """Type of category (expense or income)."""
    EXPENSE = "expense"
    INCOME = "income"


class Category(Base):
    """
    Transaction category with optional parent for subcategories.
    Can be user-defined or system default (user_id=None for defaults).
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category_type: Mapped[CategoryType] = mapped_column(
        SQLEnum(CategoryType), default=CategoryType.EXPENSE
    )
    icon: Mapped[str | None] = mapped_column(String(50))  # Icon name or emoji
    color: Mapped[str | None] = mapped_column(String(7))  # Hex color code

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="categories")
    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="category"
    )
    rules: Mapped[list["CategoryRule"]] = relationship(
        "CategoryRule", back_populates="category"
    )


class CategoryRule(Base):
    """
    User-defined rule for automatic transaction categorization.
    Rules are matched against transaction descriptions using pattern matching.
    """

    __tablename__ = "category_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    pattern: Mapped[str] = mapped_column(String(255), nullable=False)  # Regex or keyword pattern
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = matched first

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="category_rules")
    category: Mapped["Category"] = relationship("Category", back_populates="rules")
