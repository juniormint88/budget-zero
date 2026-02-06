"""
Tests for the auto-categorization service.
"""

import pytest
from decimal import Decimal
from datetime import date

from app.services.categorizer import Categorizer, BUILT_IN_PATTERNS
from app.services.parser import parse_csv, ParsedTransaction


class TestBuiltInPatterns:
    """Tests for built-in keyword matching."""

    def test_subscription_patterns(self):
        """Test subscription services are detected."""
        # Verify Netflix pattern exists
        assert "netflix" in BUILT_IN_PATTERNS["Subscriptions"]
        assert "spotify" in BUILT_IN_PATTERNS["Subscriptions"]

    def test_grocery_patterns(self):
        """Test grocery stores are detected."""
        assert "kroger" in BUILT_IN_PATTERNS["Groceries"]
        assert "walmart" in BUILT_IN_PATTERNS["Groceries"]

    def test_dining_patterns(self):
        """Test restaurants are detected."""
        assert "doordash" in BUILT_IN_PATTERNS["Dining"]
        assert "starbucks" in BUILT_IN_PATTERNS["Dining"]


class TestCSVParser:
    """Tests for CSV file parsing."""

    def test_parse_standard_csv(self):
        """Test parsing a standard CSV with Date, Description, Amount columns."""
        csv_content = """Date,Description,Amount
01/15/2024,NETFLIX.COM,-15.99
01/16/2024,KROGER GROCERY,-125.50
01/17/2024,DIRECT DEPOSIT,2500.00"""

        transactions = parse_csv(csv_content)
        assert len(transactions) == 3

        # Check first transaction (Netflix)
        assert transactions[0].date == date(2024, 1, 15)
        assert "NETFLIX" in transactions[0].description
        assert transactions[0].amount == Decimal("-15.99")
        assert transactions[0].is_income is False

        # Check income transaction
        assert transactions[2].amount == Decimal("2500.00")
        assert transactions[2].is_income is True

    def test_parse_debit_credit_columns(self):
        """Test parsing CSV with separate Debit and Credit columns."""
        csv_content = """Date,Description,Debit,Credit
01/15/2024,PAYMENT RECEIVED,,500.00
01/16/2024,AMAZON PURCHASE,75.00,"""

        transactions = parse_csv(csv_content)
        assert len(transactions) == 2

        # Credit (income)
        assert transactions[0].amount == Decimal("500.00")
        assert transactions[0].is_income is True

        # Debit (expense)
        assert transactions[1].amount == Decimal("-75.00")
        assert transactions[1].is_income is False

    def test_parse_with_bom(self):
        """Test parsing CSV with BOM (byte order mark)."""
        csv_content = "\ufeffDate,Description,Amount\n01/15/2024,Test,-10.00"
        transactions = parse_csv(csv_content)
        assert len(transactions) == 1

    def test_parse_empty_rows_skipped(self):
        """Test that empty rows are skipped."""
        csv_content = """Date,Description,Amount
01/15/2024,TEST,-10.00

01/16/2024,TEST2,-20.00
"""
        transactions = parse_csv(csv_content)
        assert len(transactions) == 2

    def test_parse_zero_amounts_skipped(self):
        """Test that zero-amount transactions are skipped."""
        csv_content = """Date,Description,Amount
01/15/2024,ZERO BALANCE,0.00
01/16/2024,REAL CHARGE,-10.00"""
        transactions = parse_csv(csv_content)
        assert len(transactions) == 1

    def test_parse_various_date_formats(self):
        """Test parsing different date formats."""
        # ISO format
        csv_content = """Date,Description,Amount
2024-01-15,TEST,-10.00"""
        transactions = parse_csv(csv_content)
        assert transactions[0].date == date(2024, 1, 15)

    def test_parse_parentheses_negative(self):
        """Test parsing amounts with parentheses for negative."""
        csv_content = """Date,Description,Amount
01/15/2024,DEBIT,(50.00)"""
        transactions = parse_csv(csv_content)
        assert transactions[0].amount == Decimal("-50.00")

    def test_parse_currency_symbols(self):
        """Test parsing amounts with currency symbols."""
        csv_content = """Date,Description,Amount
01/15/2024,CHARGE,-$25.50"""
        transactions = parse_csv(csv_content)
        assert transactions[0].amount == Decimal("-25.50")

    def test_parse_missing_date_column_error(self):
        """Test that missing date column raises error."""
        csv_content = """Description,Amount
TEST,-10.00"""
        with pytest.raises(ValueError, match="date column"):
            parse_csv(csv_content)

    def test_parse_empty_file_error(self):
        """Test that empty file raises error."""
        with pytest.raises(ValueError, match="empty"):
            parse_csv("")


class TestImportHash:
    """Tests for duplicate detection via hashing."""

    def test_hash_uniqueness(self):
        """Test that different transactions produce different hashes."""
        from app.services.categorizer import Categorizer

        trans1 = ParsedTransaction(
            date=date(2024, 1, 15),
            description="NETFLIX",
            amount=Decimal("-15.99"),
            is_income=False,
        )
        trans2 = ParsedTransaction(
            date=date(2024, 1, 16),
            description="NETFLIX",
            amount=Decimal("-15.99"),
            is_income=False,
        )

        # Create a mock categorizer just to use the hash method
        class MockCategorizer(Categorizer):
            def __init__(self):
                pass

        cat = MockCategorizer()
        hash1 = cat._generate_import_hash(trans1)
        hash2 = cat._generate_import_hash(trans2)

        # Same amount and description but different date = different hash
        assert hash1 != hash2

    def test_hash_consistency(self):
        """Test that same transaction produces same hash."""
        from app.services.categorizer import Categorizer

        trans = ParsedTransaction(
            date=date(2024, 1, 15),
            description="NETFLIX",
            amount=Decimal("-15.99"),
            is_income=False,
        )

        class MockCategorizer(Categorizer):
            def __init__(self):
                pass

        cat = MockCategorizer()
        hash1 = cat._generate_import_hash(trans)
        hash2 = cat._generate_import_hash(trans)

        assert hash1 == hash2
