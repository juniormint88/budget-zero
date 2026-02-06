"""
File parsing service for CSV and OFX transaction files.
Handles multiple bank formats and normalizes data to a common schema.
"""

import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import NamedTuple

try:
    from ofxparse import OfxParser
except ImportError:
    OfxParser = None


class ParsedTransaction(NamedTuple):
    """Normalized transaction data from file import."""
    date: date
    description: str
    amount: Decimal
    is_income: bool


# Common date formats used by various banks
DATE_FORMATS = [
    "%m/%d/%Y",      # 01/15/2024 (most common)
    "%Y-%m-%d",      # 2024-01-15 (ISO)
    "%m-%d-%Y",      # 01-15-2024
    "%d/%m/%Y",      # 15/01/2024 (international)
    "%m/%d/%y",      # 01/15/24
    "%Y/%m/%d",      # 2024/01/15
    "%b %d, %Y",     # Jan 15, 2024
    "%B %d, %Y",     # January 15, 2024
]


# Header mappings for different banks - maps bank column names to standard fields
# Keys are normalized (lowercase, stripped) versions of column headers
HEADER_MAPPINGS = {
    # Date column names
    "date": "date",
    "transaction date": "date",
    "trans date": "date",
    "posting date": "date",
    "post date": "date",
    "trans. date": "date",

    # Description column names
    "description": "description",
    "memo": "description",
    "payee": "description",
    "name": "description",
    "merchant": "description",
    "transaction description": "description",
    "original description": "description",

    # Amount column names (single amount column)
    "amount": "amount",
    "transaction amount": "amount",
    "trans amount": "amount",

    # Debit/Credit separate columns (need special handling)
    "debit": "debit",
    "credit": "credit",
    "withdrawal": "debit",
    "deposit": "credit",
    "withdrawals": "debit",
    "deposits": "credit",
}


def parse_date(date_str: str) -> date:
    """
    Parse a date string trying multiple formats.
    Returns a date object or raises ValueError if no format matches.
    """
    date_str = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")


def parse_amount(amount_str: str) -> Decimal:
    """
    Parse an amount string, handling various formats.
    Removes currency symbols, commas, and handles parentheses for negatives.
    """
    if not amount_str or not amount_str.strip():
        return Decimal("0")

    amount_str = amount_str.strip()

    # Handle parentheses for negative (accounting format)
    if amount_str.startswith("(") and amount_str.endswith(")"):
        amount_str = "-" + amount_str[1:-1]

    # Remove currency symbols and commas
    amount_str = re.sub(r"[$€£,]", "", amount_str)

    # Handle double negatives
    amount_str = amount_str.replace("--", "")

    try:
        return Decimal(amount_str)
    except InvalidOperation:
        raise ValueError(f"Could not parse amount: {amount_str}")


def detect_csv_format(headers: list[str]) -> dict[str, int]:
    """
    Detect which CSV format is being used based on headers.
    Returns a mapping of standard field names to column indices.
    """
    # Normalize headers
    normalized = [h.lower().strip() for h in headers]

    field_map = {}
    for idx, header in enumerate(normalized):
        if header in HEADER_MAPPINGS:
            field_name = HEADER_MAPPINGS[header]
            # Don't overwrite if already found (prefer first match)
            if field_name not in field_map:
                field_map[field_name] = idx

    # Validate required fields
    if "date" not in field_map:
        raise ValueError("CSV must contain a date column")
    if "description" not in field_map:
        raise ValueError("CSV must contain a description column")
    if "amount" not in field_map and "debit" not in field_map:
        raise ValueError("CSV must contain an amount column (or debit/credit columns)")

    return field_map


def parse_csv(content: str) -> list[ParsedTransaction]:
    """
    Parse a CSV file and return normalized transaction data.
    Auto-detects format based on headers and handles various bank formats.
    """
    # Handle potential BOM (byte order mark)
    content = content.lstrip("\ufeff")

    # Parse CSV
    reader = csv.reader(io.StringIO(content))

    # Get headers
    try:
        headers = next(reader)
    except StopIteration:
        raise ValueError("CSV file is empty")

    # Detect format
    field_map = detect_csv_format(headers)

    # Parse rows
    transactions = []
    errors = []

    for row_num, row in enumerate(reader, start=2):
        # Skip empty rows
        if not row or all(not cell.strip() for cell in row):
            continue

        try:
            # Extract date
            trans_date = parse_date(row[field_map["date"]])

            # Extract description
            description = row[field_map["description"]].strip()

            # Extract amount
            if "amount" in field_map:
                # Single amount column
                amount = parse_amount(row[field_map["amount"]])
            else:
                # Separate debit/credit columns
                debit = parse_amount(row[field_map.get("debit", len(row))] if field_map.get("debit", len(row)) < len(row) else "0")
                credit = parse_amount(row[field_map.get("credit", len(row))] if field_map.get("credit", len(row)) < len(row) else "0")
                # Credits are positive (income), debits are negative (expense)
                amount = credit - debit if credit else -debit

            # Skip zero-amount transactions
            if amount == 0:
                continue

            # Determine if income (positive amount)
            is_income = amount > 0

            transactions.append(ParsedTransaction(
                date=trans_date,
                description=description,
                amount=amount,
                is_income=is_income,
            ))
        except (ValueError, IndexError) as e:
            errors.append(f"Row {row_num}: {str(e)}")
            continue

    if not transactions and errors:
        raise ValueError(f"Failed to parse any transactions. Errors: {'; '.join(errors[:5])}")

    return transactions


def parse_ofx(content: bytes) -> list[ParsedTransaction]:
    """
    Parse an OFX/QFX file and return normalized transaction data.
    Uses ofxparse library for standard OFX format parsing.
    """
    if OfxParser is None:
        raise ValueError("OFX parsing requires the ofxparse library")

    try:
        ofx = OfxParser.parse(io.BytesIO(content))
    except Exception as e:
        raise ValueError(f"Failed to parse OFX file: {str(e)}")

    transactions = []

    # OFX files can have multiple accounts
    for account in ofx.accounts:
        for trans in account.statement.transactions:
            # Get transaction date
            trans_date = trans.date.date() if hasattr(trans.date, 'date') else trans.date

            # Get description (payee or memo)
            description = trans.payee or trans.memo or "Unknown"

            # Get amount
            amount = Decimal(str(trans.amount))

            # Skip zero amounts
            if amount == 0:
                continue

            # Determine if income
            is_income = amount > 0

            transactions.append(ParsedTransaction(
                date=trans_date,
                description=description,
                amount=amount,
                is_income=is_income,
            ))

    return transactions
