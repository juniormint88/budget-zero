"""
Auto-categorization engine for transactions.
Uses keyword matching, user-defined rules, and merchant learning.
"""

import hashlib
import re
from decimal import Decimal
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryRule
from app.models.transaction import Transaction
from app.schemas.transaction import ImportResult
from app.services.parser import ParsedTransaction


# Built-in keyword patterns for auto-categorization
# Maps category names to lists of keywords (case-insensitive)
BUILT_IN_PATTERNS = {
    "Subscriptions": [
        "netflix", "spotify", "hulu", "disney+", "disney plus", "amazon prime",
        "youtube", "apple music", "hbo", "paramount", "peacock", "audible",
        "dropbox", "icloud", "google one", "adobe", "microsoft 365", "github"
    ],
    "Groceries": [
        "kroger", "walmart", "target", "costco", "whole foods", "trader joe",
        "aldi", "publix", "safeway", "wegmans", "sprouts", "h-e-b", "heb",
        "food lion", "giant", "stop & shop", "meijer", "market basket"
    ],
    "Utilities": [
        "electric", "gas company", "water bill", "internet", "comcast", "att",
        "verizon", "t-mobile", "tmobile", "spectrum", "cox", "xfinity",
        "duke energy", "pg&e", "utility", "power company"
    ],
    "Dining": [
        "restaurant", "doordash", "ubereats", "uber eats", "grubhub", "mcdonald",
        "starbucks", "chipotle", "chick-fil-a", "wendys", "burger king", "taco bell",
        "subway", "panera", "dominos", "pizza hut", "olive garden", "applebees",
        "ihop", "denny", "waffle house", "postmates", "seamless", "caviar"
    ],
    "Transportation": [
        "shell", "exxon", "chevron", "bp", "mobil", "speedway", "wawa",
        "uber", "lyft", "parking", "toll", "gas station", "fuel",
        "metro", "transit", "railway", "amtrak", "bus"
    ],
    "Mortgage/Rent": [
        "mortgage", "rent", "hoa", "homeowner", "property management",
        "apartment", "lease"
    ],
    "Entertainment": [
        "amc", "regal", "cinemark", "movie", "theatre", "theater",
        "concert", "ticketmaster", "stubhub", "eventbrite", "bowling",
        "arcade", "golf", "gym", "fitness"
    ],
    "Healthcare": [
        "pharmacy", "cvs", "walgreens", "rite aid", "hospital", "doctor",
        "medical", "dental", "vision", "optometrist", "clinic", "urgent care",
        "labcorp", "quest diagnostics"
    ],
    "Shopping": [
        "amazon", "ebay", "etsy", "best buy", "home depot", "lowes",
        "ikea", "wayfair", "overstock", "macys", "nordstrom", "kohls",
        "tj maxx", "marshalls", "ross", "old navy", "gap", "nike", "adidas"
    ],
    "Insurance": [
        "insurance", "geico", "progressive", "state farm", "allstate",
        "liberty mutual", "usaa", "nationwide"
    ],
    "Personal Care": [
        "salon", "barber", "spa", "massage", "nail", "beauty",
        "ulta", "sephora", "bath & body"
    ],
    "Travel": [
        "airline", "delta", "united", "american airlines", "southwest",
        "jetblue", "hotel", "marriott", "hilton", "airbnb", "vrbo",
        "expedia", "booking.com", "kayak", "travelocity"
    ],
    "Education": [
        "university", "college", "school", "tuition", "coursera",
        "udemy", "skillshare", "masterclass", "books", "textbook"
    ],
    "Gifts/Donations": [
        "charity", "donation", "gift", "nonprofit", "red cross",
        "gofundme", "patreon"
    ],
    "Fees/Charges": [
        "fee", "charge", "interest", "late fee", "overdraft",
        "atm fee", "service charge", "annual fee"
    ],
}


class Categorizer:
    """
    Transaction categorization engine.
    Applies rules in priority order:
    1. User-defined rules (highest priority)
    2. Previous merchant matches (learning from user categorization)
    3. Built-in keyword patterns
    4. Uncategorized (returns None)
    """

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.user_rules: list[tuple[str, int, int]] = []  # (pattern, category_id, priority)
        self.category_name_to_id: dict[str, int] = {}

    async def load_rules(self):
        """Load user-defined rules and category mappings from database."""
        # Load user's category rules
        result = await self.db.execute(
            select(CategoryRule)
            .where(CategoryRule.user_id == self.user_id)
            .order_by(CategoryRule.priority.desc())
        )
        rules = result.scalars().all()
        self.user_rules = [(r.pattern, r.category_id, r.priority) for r in rules]

        # Load category name to ID mapping
        result = await self.db.execute(
            select(Category)
            .where(
                or_(
                    Category.user_id == self.user_id,
                    Category.user_id.is_(None)
                )
            )
        )
        categories = result.scalars().all()
        self.category_name_to_id = {c.name: c.id for c in categories}

    def _normalize_description(self, description: str) -> str:
        """
        Normalize transaction description for matching.
        Removes extra spaces, converts to lowercase.
        """
        # Remove extra whitespace
        normalized = " ".join(description.lower().split())
        # Remove common noise words and numbers that don't help categorization
        normalized = re.sub(r"\d{4,}", "", normalized)  # Remove long numbers
        return normalized.strip()

    def _match_user_rules(self, description: str) -> int | None:
        """Check if description matches any user-defined rule."""
        normalized = self._normalize_description(description)
        for pattern, category_id, _ in self.user_rules:
            try:
                if re.search(pattern.lower(), normalized, re.IGNORECASE):
                    return category_id
            except re.error:
                # Invalid regex - treat as literal string match
                if pattern.lower() in normalized:
                    return category_id
        return None

    def _match_built_in_patterns(self, description: str) -> int | None:
        """Check if description matches any built-in pattern."""
        normalized = self._normalize_description(description)
        for category_name, keywords in BUILT_IN_PATTERNS.items():
            for keyword in keywords:
                if keyword.lower() in normalized:
                    # Get category ID from our mapping
                    if category_name in self.category_name_to_id:
                        return self.category_name_to_id[category_name]
        return None

    def categorize(self, description: str) -> int | None:
        """
        Categorize a transaction description.
        Returns category_id or None if no match found.
        """
        # 1. Check user-defined rules first (highest priority)
        category_id = self._match_user_rules(description)
        if category_id:
            return category_id

        # 2. Check built-in patterns
        category_id = self._match_built_in_patterns(description)
        if category_id:
            return category_id

        # 3. No match found
        return None

    def _generate_import_hash(self, trans: ParsedTransaction) -> str:
        """
        Generate a unique hash for transaction deduplication.
        Combines date, description, and amount.
        """
        hash_input = f"{trans.date.isoformat()}|{trans.description}|{trans.amount}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    async def import_transactions(
        self,
        account_id: int,
        transactions: list[ParsedTransaction]
    ) -> ImportResult:
        """
        Import transactions with auto-categorization and deduplication.
        Returns import statistics.
        """
        imported = 0
        skipped = 0
        errors = []

        for trans in transactions:
            try:
                # Generate hash for deduplication
                import_hash = self._generate_import_hash(trans)

                # Check if transaction already exists
                result = await self.db.execute(
                    select(Transaction).where(Transaction.import_hash == import_hash)
                )
                if result.scalar_one_or_none():
                    skipped += 1
                    continue

                # Auto-categorize
                category_id = self.categorize(trans.description)

                # Create transaction
                transaction = Transaction(
                    account_id=account_id,
                    date=trans.date,
                    description=trans.description,
                    amount=trans.amount,
                    is_income=trans.is_income,
                    category_id=category_id,
                    import_hash=import_hash,
                )
                self.db.add(transaction)
                imported += 1

            except Exception as e:
                errors.append(f"Failed to import '{trans.description}': {str(e)}")

        await self.db.commit()

        return ImportResult(
            total=len(transactions),
            imported=imported,
            skipped=skipped,
            errors=errors,
        )
