"""
Tests for normalization logic.
"""
import unittest

from hris.importers.normalizer import normalize_row, normalize_email, normalize_value


class TestNormalizer(unittest.TestCase):
    def test_trim_whitespace_all_fields(self):
        """Test surrounding whitespace is trimmed from all fields."""
        raw = {
            "employee_id": " DIV-001 ",
            "employee_name": "  John Doe  ",
            "email": "  JOHN@EXAMPLE.COM  ",
            "manager_id": " DIV-002 ",
            "manager_email": "  MANAGER@EXAMPLE.COM  ",
            "department": "  Engineering  ",
        }
        normalized = normalize_row(raw)

        self.assertEqual(normalized["employee_id"], "DIV-001")
        self.assertEqual(normalized["employee_name"], "John Doe")
        self.assertEqual(normalized["email"], "john@example.com")
        self.assertEqual(normalized["manager_id"], "DIV-002")
        self.assertEqual(normalized["manager_email"], "manager@example.com")
        self.assertEqual(normalized["department"], "Engineering")

    def test_employee_id_case_preserved(self):
        """Test employee_id case is preserved (not lowercased)."""
        raw = {"employee_id": " Div-001 ", "employee_name": "John", "email": "john@example.com",
               "manager_id": "", "manager_email": "", "department": ""}
        normalized = normalize_row(raw)
        self.assertEqual(normalized["employee_id"], "Div-001")

    def test_manager_id_case_preserved(self):
        """Test manager_id case is preserved (not lowercased)."""
        raw = {"employee_id": "DIV-001", "employee_name": "John", "email": "john@example.com",
               "manager_id": " Div-002 ", "manager_email": "", "department": ""}
        normalized = normalize_row(raw)
        self.assertEqual(normalized["manager_id"], "Div-002")

    def test_email_lowercased(self):
        """Test email is lowercased after trimming."""
        raw = {"employee_id": "DIV-001", "employee_name": "John", "email": "  JOHN@EXAMPLE.COM  ",
               "manager_id": "", "manager_email": "", "department": ""}
        normalized = normalize_row(raw)
        self.assertEqual(normalized["email"], "john@example.com")

    def test_manager_email_lowercased(self):
        """Test manager_email is lowercased after trimming."""
        raw = {"employee_id": "DIV-001", "employee_name": "John", "email": "john@example.com",
               "manager_id": "", "manager_email": "  MGR@EXAMPLE.COM  ", "department": ""}
        normalized = normalize_row(raw)
        self.assertEqual(normalized["manager_email"], "mgr@example.com")

    def test_blank_values_become_none(self):
        """Test blank/empty values become None."""
        raw = {"employee_id": "", "employee_name": "", "email": "",
               "manager_id": "   ", "manager_email": "\t", "department": ""}
        normalized = normalize_row(raw)

        self.assertIsNone(normalized["employee_id"])
        self.assertIsNone(normalized["employee_name"])
        self.assertIsNone(normalized["email"])
        self.assertIsNone(normalized["manager_id"])
        self.assertIsNone(normalized["manager_email"])
        self.assertIsNone(normalized["department"])

    def test_none_input_handled(self):
        """Test None values are handled gracefully."""
        raw = {"employee_id": None, "employee_name": None, "email": None,
               "manager_id": None, "manager_email": None, "department": None}
        normalized = normalize_row(raw)

        for v in normalized.values():
            self.assertIsNone(v)

    def test_internal_whitespace_preserved(self):
        """Test meaningful internal whitespace is preserved."""
        raw = {"employee_id": "DIV-001", "employee_name": "John  Doe", "email": "john@example.com",
               "manager_id": "", "manager_email": "", "department": "Product  Engineering"}
        normalized = normalize_row(raw)

        self.assertEqual(normalized["employee_name"], "John  Doe")
        self.assertEqual(normalized["department"], "Product  Engineering")

    def test_normalize_email_standalone(self):
        """Test standalone normalize_email function."""
        self.assertEqual(normalize_email("  TEST@EXAMPLE.COM  "), "test@example.com")
        self.assertEqual(normalize_email(""), None)
        self.assertEqual(normalize_email("   "), None)
        self.assertEqual(normalize_email(None), None)

    def test_normalize_value_standalone(self):
        """Test standalone normalize_value function."""
        self.assertEqual(normalize_value("  hello  "), "hello")
        self.assertEqual(normalize_value(""), None)
        self.assertEqual(normalize_value("   "), None)
        self.assertEqual(normalize_value(None), None)


if __name__ == "__main__":
    unittest.main()