"""
Transaction router for managing financial transactions.
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[TransactionResponse])
async def list_transactions(
    account_id: int | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get transactions for the current user with optional filters.
    Returns transactions sorted by date (newest first).
    """
    # Build query with user's accounts
    query = (
        select(Transaction, Category.name.label("category_name"))
        .join(Account, Transaction.account_id == Account.id)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(Account.user_id == current_user.id)
    )

    # Apply filters
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    # Order by date descending and apply pagination
    query = query.order_by(Transaction.date.desc(), Transaction.id.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # Convert to response models with category name
    transactions = []
    for row in rows:
        trans = row[0]
        trans_dict = {
            "id": trans.id,
            "account_id": trans.account_id,
            "category_id": trans.category_id,
            "date": trans.date,
            "description": trans.description,
            "amount": trans.amount,
            "is_income": trans.is_income,
            "merchant": trans.merchant,
            "notes": trans.notes,
            "import_hash": trans.import_hash,
            "created_at": trans.created_at,
            "category_name": row[1],  # category_name from join
        }
        transactions.append(TransactionResponse(**trans_dict))

    return transactions


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new transaction."""
    # Verify account belongs to user
    result = await db.execute(
        select(Account).where(
            Account.id == transaction_data.account_id,
            Account.user_id == current_user.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Verify category if provided
    if transaction_data.category_id:
        result = await db.execute(
            select(Category).where(
                Category.id == transaction_data.category_id,
                (Category.user_id == current_user.id) | (Category.user_id.is_(None))
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    transaction = Transaction(
        account_id=transaction_data.account_id,
        date=transaction_data.date,
        description=transaction_data.description,
        amount=transaction_data.amount,
        category_id=transaction_data.category_id,
        is_income=transaction_data.is_income,
        merchant=transaction_data.merchant,
        notes=transaction_data.notes,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    # Get category name for response
    category_name = None
    if transaction.category_id:
        cat_result = await db.execute(
            select(Category.name).where(Category.id == transaction.category_id)
        )
        category_name = cat_result.scalar_one_or_none()

    return TransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        category_id=transaction.category_id,
        date=transaction.date,
        description=transaction.description,
        amount=transaction.amount,
        is_income=transaction.is_income,
        merchant=transaction.merchant,
        notes=transaction.notes,
        import_hash=transaction.import_hash,
        created_at=transaction.created_at,
        category_name=category_name,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific transaction by ID."""
    result = await db.execute(
        select(Transaction, Category.name.label("category_name"))
        .join(Account, Transaction.account_id == Account.id)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.id == transaction_id,
            Account.user_id == current_user.id
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    trans = row[0]
    return TransactionResponse(
        id=trans.id,
        account_id=trans.account_id,
        category_id=trans.category_id,
        date=trans.date,
        description=trans.description,
        amount=trans.amount,
        is_income=trans.is_income,
        merchant=trans.merchant,
        notes=trans.notes,
        import_hash=trans.import_hash,
        created_at=trans.created_at,
        category_name=row[1],
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing transaction."""
    result = await db.execute(
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(
            Transaction.id == transaction_id,
            Account.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Verify category if being updated
    if transaction_data.category_id is not None:
        cat_result = await db.execute(
            select(Category).where(
                Category.id == transaction_data.category_id,
                (Category.user_id == current_user.id) | (Category.user_id.is_(None))
            )
        )
        if not cat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Update only provided fields
    update_data = transaction_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)

    await db.commit()
    await db.refresh(transaction)

    # Get category name for response
    category_name = None
    if transaction.category_id:
        cat_result = await db.execute(
            select(Category.name).where(Category.id == transaction.category_id)
        )
        category_name = cat_result.scalar_one_or_none()

    return TransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        category_id=transaction.category_id,
        date=transaction.date,
        description=transaction.description,
        amount=transaction.amount,
        is_income=transaction.is_income,
        merchant=transaction.merchant,
        notes=transaction.notes,
        import_hash=transaction.import_hash,
        created_at=transaction.created_at,
        category_name=category_name,
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a transaction."""
    result = await db.execute(
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(
            Transaction.id == transaction_id,
            Account.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    await db.delete(transaction)
    await db.commit()


@router.post("/bulk-categorize", response_model=dict)
async def bulk_categorize(
    transaction_ids: list[int],
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk update category for multiple transactions."""
    # Verify category exists and belongs to user
    cat_result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            (Category.user_id == current_user.id) | (Category.user_id.is_(None))
        )
    )
    if not cat_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Update all transactions that belong to user
    result = await db.execute(
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(
            Transaction.id.in_(transaction_ids),
            Account.user_id == current_user.id
        )
    )
    transactions = result.scalars().all()

    updated_count = 0
    for trans in transactions:
        trans.category_id = category_id
        updated_count += 1

    await db.commit()
    return {"updated": updated_count}
