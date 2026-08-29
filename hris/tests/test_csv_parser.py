"""
Tests for CSV parser.
"""
import io
import unittest

from hris.importers.csv_parser import parse_csv, parse_csv_to_list
from hris.domain.errors import CSVStructureError


class TestCSVParser(unittest.TestCase):
    def test_basic_parsing(self):
        """Test basic CSV parsing with all required headers."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
        )
        file_obj = io.BytesIO(csv_content.encode("utf-8"))
        rows = parse_csv_to_list(file_obj)

        self.assertEqual(len(rows), 1)
        row_number, row = rows[0]
        self.assertEqual(row_number, 2)
        self.assertEqual(row["employee_id"], "DIV-001")
        self.assertEqual(row["employee_name"], "John Doe")
        self.assertEqual(row["email"], "john@example.com")

    def test_quoted_name_with_comma(self):
        """Test quoted employee name containing a comma is parsed as one field."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            'DIV-001,"Doe, John",john@example.com,,,\n'
        )
        file_obj = io.BytesIO(csv_content.encode("utf-8"))
        rows = parse_csv_to_list(file_obj)

        self.assertEqual(len(rows), 1)
        _, row = rows[0]
        self.assertEqual(row["employee_name"], "Doe, John")

    def test_utf8_bom_handled(self):
        """Test UTF-8 BOM does not become part of first header."""
        csv_content = (
            "\ufeffemployee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
        )
        file_obj = io.BytesIO(csv_content.encode("utf-8"))
        rows = parse_csv_to_list(file_obj)

        self.assertEqual(len(rows), 1)
        _, row = rows[0]
        self.assertEqual(row["employee_id"], "DIV-001")

    def test_headers_any_order(self):
        """Test headers can appear in any order."""
        csv_content = (
            "email,employee_id,department,employee_name,manager_email,manager_id\n"
            "john@example.com,DIV-001,Engineering,John Doe,,\n"
        )
        file_obj = io.BytesIO(csv_content.encode("utf-8"))
        rows = parse_csv_to_list(file_obj)

        self.assertEqual(len(rows), 1)
        _, row = rows[0]
        self.assertEqual(row["employee_id"], "DIV-001")
        self.assertEqual(row["email"], "john@example.com")

    def test_missing_required_header_raises(self):
        """Test missing required header raises CSVStructureError."""
        csv_content = "employee_id,employee_name,email\nDIV-001,John Doe,john@example.com\n"
        file_obj = io.BytesIO(csv_content.encode("utf-8"))

        with self.assertRaises(CSVStructureError) as ctx:
            parse_csv_to_list(file_obj)

        self.assertIn("Missing required headers", str(ctx.exception))
        self.assertIn("manager_id", str(ctx.exception))

    def test_empty_csv_raises(self):
        """Test empty CSV raises CSVStructureError."""
        file_obj = io.BytesIO(b"")
        with self.assertRaises(CSVStructureError):
            parse_csv_to_list(file_obj)

    def test_invalid_utf8_raises(self):
        """Test invalid UTF-8 raises CSVStructureError."""
        file_obj = io.BytesIO(b"\xff\xfe")  # Invalid UTF-8
        with self.assertRaises(CSVStructureError):
            parse_csv_to_list(file_obj)

    def test_row_numbers_start_at_2(self):
        """Test row numbers: header=1, first data=2."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
            "DIV-002,Jane Smith,jane@example.com,,,\n"
        )
        file_obj = io.BytesIO(csv_content.encode("utf-8"))
        rows = parse_csv_to_list(file_obj)

        self.assertEqual(rows[0][0], 2)  # First data row
        self.assertEqual(rows[1][0], 3)  # Second data row

    def test_whitespace_preserved_in_values(self):
        """Test that raw values preserve internal whitespace (trimming happens in normalizer)."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            'DIV-001,"  John  Doe  ",john@example.com,,,\n'
        )
        file_obj = io.BytesIO(csv_content.encode("utf-8"))
        rows = parse_csv_to_list(file_obj)

        _, row = rows[0]
        # Parser strips header names but not values - normalizer handles value trimming
        self.assertEqual(row["employee_name"], "  John  Doe  ")


if __name__ == "__main__":
    unittest.main()