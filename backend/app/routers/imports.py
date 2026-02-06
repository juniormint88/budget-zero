"""
Import router for handling CSV and OFX file uploads.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.schemas.transaction import ImportResult
from app.routers.auth import get_current_user
from app.services.parser import parse_csv, parse_ofx
from app.services.categorizer import Categorizer

router = APIRouter()


@router.post("/csv", response_model=ImportResult)
async def import_csv(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import transactions from a CSV file.
    Supports common bank export formats (Chase, Capital One, Discover, etc.)
    """
    # Verify account belongs to user
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Read file content
    content = await file.read()
    try:
        content_str = content.decode("utf-8")
    except UnicodeDecodeError:
        # Try with latin-1 encoding as fallback
        content_str = content.decode("latin-1")

    # Parse CSV file
    try:
        transactions_data = parse_csv(content_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Initialize categorizer
    categorizer = Categorizer(db, current_user.id)
    await categorizer.load_rules()

    # Import transactions
    import_result = await categorizer.import_transactions(
        account_id=account_id,
        transactions=transactions_data,
    )

    return import_result


@router.post("/ofx", response_model=ImportResult)
async def import_ofx(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import transactions from an OFX/QFX file.
    Standard format used by many financial institutions.
    """
    # Verify account belongs to user
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Read file content
    content = await file.read()

    # Parse OFX file
    try:
        transactions_data = parse_ofx(content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Initialize categorizer
    categorizer = Categorizer(db, current_user.id)
    await categorizer.load_rules()

    # Import transactions
    import_result = await categorizer.import_transactions(
        account_id=account_id,
        transactions=transactions_data,
    )

    return import_result


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported import file formats and banks."""
    return {
        "csv": {
            "description": "Comma-separated values file",
            "supported_banks": [
                "Chase",
                "Capital One",
                "Discover",
                "Synovus",
                "Associated Credit Union",
                "Generic (Date, Description, Amount columns)",
            ],
            "tips": [
                "Export your transactions as CSV from your bank's website",
                "The parser will auto-detect the format based on headers",
                "Ensure the file contains Date, Description, and Amount columns",
            ]
        },
        "ofx": {
            "description": "Open Financial Exchange format (OFX/QFX)",
            "supported_banks": [
                "Most major banks support OFX downloads",
                "Also known as QFX (Quicken) or Microsoft Money format",
            ],
            "tips": [
                "OFX files contain standardized transaction data",
                "Usually available as 'Download for Quicken' option",
            ]
        }
    }
