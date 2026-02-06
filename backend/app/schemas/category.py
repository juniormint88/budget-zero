"""
Category and category rule schemas.
"""

from pydantic import BaseModel

from app.models.category import CategoryType


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""
    name: str
    parent_id: int | None = None
    category_type: CategoryType = CategoryType.EXPENSE
    icon: str | None = None
    color: str | None = None


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: str | None = None
    parent_id: int | None = None
    category_type: CategoryType | None = None
    icon: str | None = None
    color: str | None = None


class CategoryResponse(BaseModel):
    """Schema for category response data."""
    id: int
    user_id: int | None
    name: str
    parent_id: int | None
    category_type: CategoryType
    icon: str | None
    color: str | None

    class Config:
        from_attributes = True


class CategoryRuleCreate(BaseModel):
    """Schema for creating a category rule."""
    pattern: str
    category_id: int
    priority: int = 0


class CategoryRuleResponse(BaseModel):
    """Schema for category rule response data."""
    id: int
    user_id: int
    pattern: str
    category_id: int
    priority: int

    class Config:
        from_attributes = True
