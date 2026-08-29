"""
Tests for manager resolution.
"""
import unittest

from hris.domain.entities import Employee
from hris.hierarchy.resolver import resolve_managers
from hris.domain.results import ManagerResolutionResult


class TestManagerResolution(unittest.TestCase):
    def _make_emp(self, emp_id, name, email, manager_id=None, manager_email=None, dept=""):
        return Employee(
            employee_id=emp_id,
            employee_name=name,
            email=email,
            manager_id=manager_id,
            manager_email=manager_email,
            department=dept,
        )

    def _resolve(self, employees):
        """Helper to run resolver with row numbers."""
        row_numbers = {e.employee_id: i + 2 for i, e in enumerate(employees)}
        return resolve_managers(tuple(employees), row_numbers)

    def test_resolve_by_employee_id(self):
        """Manager resolved successfully by employee_id."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Report", "report@example.com", manager_id="DIV-001"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 1)
        self.assertEqual(result.relationships[0], ("DIV-002", "DIV-001"))
        self.assertEqual(len(result.manager_errors), 0)
        self.assertIn("DIV-001", result.no_manager_employee_ids)

    def test_resolve_by_manager_email(self):
        """Manager resolved successfully by manager_email."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Report", "report@example.com", manager_email="manager@example.com"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 1)
        self.assertEqual(result.relationships[0], ("DIV-002", "DIV-001"))
        self.assertEqual(len(result.manager_errors), 0)

    def test_both_references_same_employee(self):
        """Both manager_id and manager_email identify the same employee."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp(
                "DIV-002", "Report", "report@example.com",
                manager_id="DIV-001", manager_email="manager@example.com"
            ),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 1)
        self.assertEqual(result.relationships[0], ("DIV-002", "DIV-001"))
        self.assertEqual(len(result.manager_errors), 0)

    def test_conflicting_references_error(self):
        """Conflicting manager_id and manager_email produce error, no relationship."""
        employees = [
            self._make_emp("DIV-001", "Manager A", "manager_a@example.com"),
            self._make_emp("DIV-002", "Manager B", "manager_b@example.com"),
            self._make_emp(
                "DIV-003", "Report", "report@example.com",
                manager_id="DIV-001", manager_email="manager_b@example.com"
            ),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 0)
        self.assertEqual(len(result.manager_errors), 1)
        self.assertIn("refer to different employees", result.manager_errors[0].message)
        self.assertIn("DIV-003", result.manager_error_employee_ids)

    def test_missing_manager_id_error(self):
        """Missing manager_id produces error, no relationship."""
        employees = [
            self._make_emp("DIV-001", "Report", "report@example.com", manager_id="DIV-9999"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 0)
        self.assertEqual(len(result.manager_errors), 1)
        self.assertIn("could not be found", result.manager_errors[0].message)
        self.assertIn("DIV-9999", result.manager_errors[0].message)
        self.assertIn("DIV-001", result.manager_error_employee_ids)

    def test_missing_manager_email_error(self):
        """Missing manager_email produces error, no relationship."""
        employees = [
            self._make_emp("DIV-001", "Report", "report@example.com", manager_email="missing@example.com"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 0)
        self.assertEqual(len(result.manager_errors), 1)
        self.assertIn("could not be found", result.manager_errors[0].message)
        self.assertIn("missing@example.com", result.manager_errors[0].message)
        self.assertIn("DIV-001", result.manager_error_employee_ids)

    def test_self_management_by_id_error(self):
        """Self-management by manager_id produces error, no relationship."""
        employees = [
            self._make_emp("DIV-001", "Self Manager", "self@example.com", manager_id="DIV-001"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 0)
        self.assertEqual(len(result.manager_errors), 1)
        self.assertIn("cannot manage themselves", result.manager_errors[0].message)
        self.assertIn("DIV-001", result.manager_error_employee_ids)

    def test_self_management_by_email_error(self):
        """Self-management by manager_email produces error, no relationship."""
        employees = [
            self._make_emp("DIV-001", "Self Manager", "self@example.com", manager_email="self@example.com"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 0)
        self.assertEqual(len(result.manager_errors), 1)
        self.assertIn("cannot manage themselves", result.manager_errors[0].message)
        self.assertIn("DIV-001", result.manager_error_employee_ids)

    def test_manager_error_employee_not_root_candidate(self):
        """Manager-error employee is marked as NOT eligible to be a root."""
        employees = [
            self._make_emp("DIV-001", "Report", "report@example.com", manager_id="DIV-9999"),
        ]
        result = self._resolve(employees)

        self.assertIn("DIV-001", result.manager_error_employee_ids)
        self.assertNotIn("DIV-001", result.no_manager_employee_ids)

    def test_manager_rows_after_reports_still_resolve(self):
        """Manager rows appearing after reports still resolve correctly."""
        # Report appears before manager in the list
        employees = [
            self._make_emp("DIV-002", "Report", "report@example.com", manager_id="DIV-001"),
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 1)
        self.assertEqual(result.relationships[0], ("DIV-002", "DIV-001"))

    def test_no_manager_reference_is_root_candidate(self):
        """Employee with no manager reference is a root candidate."""
        employees = [
            self._make_emp("DIV-001", "Root", "root@example.com"),
        ]
        result = self._resolve(employees)

        self.assertIn("DIV-001", result.no_manager_employee_ids)
        self.assertNotIn("DIV-001", result.manager_error_employee_ids)

    def test_multiple_reports_to_same_manager(self):
        """Multiple reports can resolve to the same manager."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Report A", "report_a@example.com", manager_id="DIV-001"),
            self._make_emp("DIV-003", "Report B", "report_b@example.com", manager_id="DIV-001"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 2)
        rel_map = dict(result.relationships)
        self.assertEqual(rel_map["DIV-002"], "DIV-001")
        self.assertEqual(rel_map["DIV-003"], "DIV-001")

    def test_manager_email_case_insensitive(self):
        """Manager email lookup uses normalized (lowercase) email."""
        # Emails are already normalized to lowercase by the importer
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Report", "report@example.com", manager_email="manager@example.com"),
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 1)
        self.assertEqual(result.relationships[0], ("DIV-002", "DIV-001"))

    def test_employee_id_case_sensitive(self):
        """Manager ID lookup is case-sensitive."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Report", "report@example.com", manager_id="div-001"),  # lowercase
        ]
        result = self._resolve(employees)

        self.assertEqual(len(result.relationships), 0)
        self.assertEqual(len(result.manager_errors), 1)
        self.assertIn("could not be found", result.manager_errors[0].message)


if __name__ == "__main__":
    unittest.main()