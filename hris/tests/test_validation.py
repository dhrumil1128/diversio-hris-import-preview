"""
Tests for identity validation logic.
"""
import io
import unittest

from hris.importers.csv_parser import parse_csv_to_list
from hris.importers.validator import validate_identities
from hris.domain.entities import ValidationError


class TestValidation(unittest.TestCase):
    def _parse(self, csv_content: str):
        """Helper to parse CSV content."""
        file_obj = io.BytesIO(csv_content.encode("utf-8"))
        return parse_csv_to_list(file_obj)

    def test_valid_single_employee(self):
        """Test single valid employee passes validation."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        self.assertEqual(len(result.accepted_employees), 1)
        self.assertEqual(len(result.validation_errors), 0)
        emp = result.accepted_employees[0]
        self.assertEqual(emp.employee_id, "DIV-001")
        self.assertEqual(emp.email, "john@example.com")

    def test_blank_employee_id_produces_error(self):
        """Test blank employee_id produces row-level validation error."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            ",John Doe,john@example.com,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        self.assertEqual(len(result.accepted_employees), 0)
        self.assertEqual(len(result.validation_errors), 1)
        error = result.validation_errors[0]
        self.assertEqual(error.row_number, 2)
        self.assertEqual(error.message, "employee_id is required")

    def test_blank_email_produces_error(self):
        """Test blank email produces row-level validation error."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        self.assertEqual(len(result.accepted_employees), 0)
        self.assertEqual(len(result.validation_errors), 1)
        error = result.validation_errors[0]
        self.assertEqual(error.row_number, 2)
        self.assertEqual(error.message, "email is required")

    def test_duplicate_employee_id_invalidates_all_rows(self):
        """Test duplicate employee_id invalidates ALL rows sharing that ID."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
            "DIV-001,Jane Smith,jane@example.com,,,\n"
            "DIV-002,Bob Wilson,bob@example.com,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        # Only DIV-002 should be accepted
        self.assertEqual(len(result.accepted_employees), 1)
        self.assertEqual(result.accepted_employees[0].employee_id, "DIV-002")

        # Two duplicate errors for DIV-001 (rows 2 and 3)
        dup_errors = [e for e in result.validation_errors if "duplicate employee_id" in e.message]
        self.assertEqual(len(dup_errors), 2)
        self.assertEqual(dup_errors[0].row_number, 2)
        self.assertEqual(dup_errors[1].row_number, 3)

    def test_employee_id_case_sensitive(self):
        """Test employee_id duplicate detection is case-sensitive."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
            "div-001,Jane Smith,jane@example.com,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        # Both should be accepted (different case)
        self.assertEqual(len(result.accepted_employees), 2)
        self.assertEqual(len(result.validation_errors), 0)

    def test_duplicate_normalized_email_invalidates_all_rows(self):
        """Test duplicate normalized email invalidates ALL rows sharing that email."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,JOHN@EXAMPLE.COM,,,\n"
            "DIV-002,Jane Smith,john@example.com,,,\n"
            "DIV-003,Bob Wilson,bob@example.com,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        # Only DIV-003 should be accepted
        self.assertEqual(len(result.accepted_employees), 1)
        self.assertEqual(result.accepted_employees[0].employee_id, "DIV-003")

        # Two duplicate email errors (rows 2 and 3)
        dup_errors = [e for e in result.validation_errors if "duplicate email" in e.message]
        self.assertEqual(len(dup_errors), 2)
        self.assertEqual(dup_errors[0].row_number, 2)
        self.assertEqual(dup_errors[1].row_number, 3)

    def test_both_duplicate_id_and_email_on_same_row(self):
        """Test row with both duplicate ID and email produces both errors."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
            "DIV-001,Jane Smith,john@example.com,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        self.assertEqual(len(result.accepted_employees), 0)
        # Should have 4 errors: 2 for duplicate ID + 2 for duplicate email
        self.assertEqual(len(result.validation_errors), 4)

    def test_invalid_rows_excluded_from_accepted(self):
        """Test identity-invalid rows are excluded from accepted employees."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
            "DIV-001,Jane Smith,jane@example.com,,,\n"
            "DIV-002,Bob Wilson,bob@example.com,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        accepted_ids = {e.employee_id for e in result.accepted_employees}
        self.assertEqual(accepted_ids, {"DIV-002"})
        self.assertNotIn("DIV-001", accepted_ids)

    def test_row_numbers_preserved_in_errors(self):
        """Test validation errors preserve original CSV row numbers."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,John Doe,john@example.com,,,\n"
            ",Jane Smith,jane@example.com,,,\n"
            "DIV-001,Bob Wilson,bob@example.com,,,\n"
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        # Row 2: duplicate employee_id (shares with row 4)
        # Row 3: missing employee_id
        # Row 4: duplicate employee_id
        error_rows = {e.row_number for e in result.validation_errors}
        self.assertEqual(error_rows, {2, 3, 4})

    def test_valid_employees_retain_all_fields(self):
        """Test accepted employees retain all normalized fields."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            ' DIV-001 , John Doe , JOHN@EXAMPLE.COM , DIV-002 , MGR@EXAMPLE.COM , Engineering \n'
        )
        parsed = self._parse(csv_content)
        result = validate_identities(parsed)

        self.assertEqual(len(result.accepted_employees), 1)
        emp = result.accepted_employees[0]
        self.assertEqual(emp.employee_id, "DIV-001")
        self.assertEqual(emp.employee_name, "John Doe")
        self.assertEqual(emp.email, "john@example.com")
        self.assertEqual(emp.manager_id, "DIV-002")
        self.assertEqual(emp.manager_email, "mgr@example.com")
        self.assertEqual(emp.department, "Engineering")


if __name__ == "__main__":
    unittest.main()