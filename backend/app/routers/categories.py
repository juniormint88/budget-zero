"""
Category router for managing transaction categories and rules.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.category import Category, CategoryRule
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    CategoryRuleCreate, CategoryRuleResponse
)
from app.routers.auth import get_current_user

router = APIRouter()


# Default categories to seed for new users
DEFAULT_CATEGORIES = [
    {"name": "Subscriptions", "icon": "repeat", "color": "#9333ea"},
    {"name": "Mortgage/Rent", "icon": "home", "color": "#dc2626"},
    {"name": "Utilities", "icon": "zap", "color": "#f59e0b"},
    {"name": "Groceries", "icon": "shopping-cart", "color": "#22c55e"},
    {"name": "Dining", "icon": "utensils", "color": "#f97316"},
    {"name": "Transportation", "icon": "car", "color": "#3b82f6"},
    {"name": "Entertainment", "icon": "film", "color": "#ec4899"},
    {"name": "Healthcare", "icon": "heart", "color": "#ef4444"},
    {"name": "Shopping", "icon": "shopping-bag", "color": "#8b5cf6"},
    {"name": "Insurance", "icon": "shield", "color": "#06b6d4"},
    {"name": "Personal Care", "icon": "user", "color": "#14b8a6"},
    {"name": "Travel", "icon": "plane", "color": "#0ea5e9"},
    {"name": "Education", "icon": "book", "color": "#6366f1"},
    {"name": "Gifts/Donations", "icon": "gift", "color": "#d946ef"},
    {"name": "Fees/Charges", "icon": "credit-card", "color": "#64748b"},
    {"name": "Other", "icon": "more-horizontal", "color": "#94a3b8"},
]


async def ensure_user_categories(user_id: int, db: AsyncSession):
    """
    Ensure user has default categories.
    Called when user first accesses categories.
    """
    # Check if user already has categories
    result = await db.execute(
        select(Category).where(Category.user_id == user_id).limit(1)
    )
    if result.scalar_one_or_none():
        return  # User already has categories

    # Create default categories for user
    for cat_data in DEFAULT_CATEGORIES:
        category = Category(
            user_id=user_id,
            name=cat_data["name"],
            icon=cat_data["icon"],
            color=cat_data["color"],
        )
        db.add(category)
    await db.commit()


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all categories for the current user including defaults."""
    # Ensure user has default categories
    await ensure_user_categories(current_user.id, db)

    result = await db.execute(
        select(Category)
        .where(
            or_(
                Category.user_id == current_user.id,
                Category.user_id.is_(None)  # System defaults
            )
        )
        .order_by(Category.name)
    )
    return result.scalars().all()


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category for the current user."""
    # Verify parent category if provided
    if category_data.parent_id:
        result = await db.execute(
            select(Category).where(
                Category.id == category_data.parent_id,
                or_(
                    Category.user_id == current_user.id,
                    Category.user_id.is_(None)
                )
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )

    category = Category(
        user_id=current_user.id,
        name=category_data.name,
        parent_id=category_data.parent_id,
        category_type=category_data.category_type,
        icon=category_data.icon,
        color=category_data.color,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by ID."""
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            or_(
                Category.user_id == current_user.id,
                Category.user_id.is_(None)
            )
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing category (user-owned only)."""
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id  # Can only edit own categories
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or cannot be modified"
        )

    # Update only provided fields
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a category (user-owned only)."""
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or cannot be deleted"
        )

    await db.delete(category)
    await db.commit()


# Category Rules endpoints

@router.get("/rules/", response_model=list[CategoryRuleResponse])
async def list_category_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all category rules for the current user."""
    result = await db.execute(
        select(CategoryRule)
        .where(CategoryRule.user_id == current_user.id)
        .order_by(CategoryRule.priority.desc())
    )
    return result.scalars().all()


@router.post("/rules/", response_model=CategoryRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_category_rule(
    rule_data: CategoryRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new category rule."""
    # Verify category exists and belongs to user
    result = await db.execute(
        select(Category).where(
            Category.id == rule_data.category_id,
            or_(
                Category.user_id == current_user.id,
                Category.user_id.is_(None)
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    rule = CategoryRule(
        user_id=current_user.id,
        pattern=rule_data.pattern,
        category_id=rule_data.category_id,
        priority=rule_data.priority,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a category rule."""
    result = await db.execute(
        select(CategoryRule).where(
            CategoryRule.id == rule_id,
            CategoryRule.user_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rule not found"
        )

    await db.delete(rule)
    await db.commit()
