"""
Tests for hierarchy analysis.
"""
import unittest

from hris.domain.entities import Employee
from hris.hierarchy.resolver import resolve_managers
from hris.hierarchy.analyzer import analyze_hierarchy
from hris.domain.results import ManagerResolutionResult


class TestHierarchy(unittest.TestCase):
    def _make_emp(self, emp_id, name, email, manager_id=None, manager_email=None, dept=""):
        return Employee(
            employee_id=emp_id,
            employee_name=name,
            email=email,
            manager_id=manager_id,
            manager_email=manager_email,
            department=dept,
        )

    def _resolve_and_analyze(self, employees):
        """Helper to run full resolution + analysis pipeline."""
        row_numbers = {e.employee_id: i + 2 for i, e in enumerate(employees)}
        resolution = resolve_managers(tuple(employees), row_numbers)
        roots, managers = analyze_hierarchy(resolution)
        return resolution, roots, managers

    def test_genuine_no_manager_is_root(self):
        """A genuine no-manager employee is identified as a root."""
        employees = [
            self._make_emp("DIV-001", "Root", "root@example.com"),
            self._make_emp("DIV-002", "Report", "report@example.com", manager_id="DIV-001"),
        ]
        _, roots, _ = self._resolve_and_analyze(employees)

        self.assertEqual(roots, ("DIV-001",))

    def test_manager_error_employee_not_root(self):
        """An employee with a manager error is NOT identified as a root."""
        employees = [
            self._make_emp("DIV-001", "Report", "report@example.com", manager_id="DIV-9999"),
        ]
        _, roots, _ = self._resolve_and_analyze(employees)

        self.assertEqual(roots, ())

    def test_direct_report_counts_correct(self):
        """Direct-report counts are correct for a manager with multiple reports."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Report A", "report_a@example.com", manager_id="DIV-001"),
            self._make_emp("DIV-003", "Report B", "report_b@example.com", manager_id="DIV-001"),
            self._make_emp("DIV-004", "Report C", "report_c@example.com", manager_id="DIV-001"),
        ]
        _, _, managers = self._resolve_and_analyze(employees)

        self.assertEqual(len(managers), 1)
        self.assertEqual(managers[0].employee_id, "DIV-001")
        self.assertEqual(managers[0].name, "Manager")
        self.assertEqual(managers[0].direct_report_count, 3)

    def test_invalid_manager_relationships_no_count(self):
        """Invalid manager relationships do not affect direct-report counts."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Valid Report", "valid@example.com", manager_id="DIV-001"),
            self._make_emp("DIV-003", "Invalid Report", "invalid@example.com", manager_id="DIV-9999"),
        ]
        _, _, managers = self._resolve_and_analyze(employees)

        self.assertEqual(len(managers), 1)
        self.assertEqual(managers[0].direct_report_count, 1)  # Only valid report counts

    def test_relationship_valid_even_in_cycle(self):
        """A relationship remains valid even if it participates in a cycle."""
        # A -> B, B -> C, C -> A forms a cycle
        employees = [
            self._make_emp("DIV-001", "A", "a@example.com", manager_id="DIV-003"),
            self._make_emp("DIV-002", "B", "b@example.com", manager_id="DIV-001"),
            self._make_emp("DIV-003", "C", "c@example.com", manager_id="DIV-002"),
        ]
        _, _, managers = self._resolve_and_analyze(employees)

        # All three should have direct report counts (cycle detection is separate)
        counts = {m.employee_id: m.direct_report_count for m in managers}
        self.assertEqual(counts.get("DIV-001"), 1)
        self.assertEqual(counts.get("DIV-002"), 1)
        self.assertEqual(counts.get("DIV-003"), 1)

    def test_manager_summaries_correct_fields(self):
        """Manager summaries contain correct manager ID, name, and count."""
        employees = [
            self._make_emp("DIV-001", "Alice Manager", "alice@example.com"),
            self._make_emp("DIV-002", "Bob Report", "bob@example.com", manager_id="DIV-001"),
        ]
        _, _, managers = self._resolve_and_analyze(employees)

        self.assertEqual(len(managers), 1)
        m = managers[0]
        self.assertEqual(m.employee_id, "DIV-001")
        self.assertEqual(m.name, "Alice Manager")
        self.assertEqual(m.direct_report_count, 1)

    def test_deterministic_output_order(self):
        """Output ordering is deterministic based on accepted employee order."""
        # Manager appears AFTER reports in the list
        employees = [
            self._make_emp("DIV-002", "Report", "report@example.com", manager_id="DIV-001"),
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
        ]
        _, _, managers = self._resolve_and_analyze(employees)

        # Manager should still appear in summaries (order follows accepted order)
        self.assertEqual(len(managers), 1)
        self.assertEqual(managers[0].employee_id, "DIV-001")

    def test_only_managers_with_reports_in_summaries(self):
        """Only employees with at least one direct report appear in manager summaries."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Lonely Employee", "lonely@example.com"),  # no manager, no reports
            self._make_emp("DIV-003", "Report", "report@example.com", manager_id="DIV-001"),
        ]
        _, _, managers = self._resolve_and_analyze(employees)

        self.assertEqual(len(managers), 1)
        self.assertEqual(managers[0].employee_id, "DIV-001")

    def test_manager_error_excluded_from_counts(self):
        """Manager-error employee does not contribute to any manager's count."""
        employees = [
            self._make_emp("DIV-001", "Manager", "manager@example.com"),
            self._make_emp("DIV-002", "Valid Report", "valid@example.com", manager_id="DIV-001"),
            self._make_emp("DIV-003", "Error Report", "error@example.com", manager_id="DIV-9999"),
        ]
        _, _, managers = self._resolve_and_analyze(employees)

        self.assertEqual(managers[0].direct_report_count, 1)

    def test_empty_hierarchy(self):
        """Empty employee list produces empty results."""
        _, roots, managers = self._resolve_and_analyze([])

        self.assertEqual(roots, ())
        self.assertEqual(managers, ())

    def test_single_employee_no_manager(self):
        """Single employee with no manager is a root, not a manager."""
        employees = [
            self._make_emp("DIV-001", "Solo", "solo@example.com"),
        ]
        _, roots, managers = self._resolve_and_analyze(employees)

        self.assertEqual(roots, ("DIV-001",))
        self.assertEqual(managers, ())

    def test_multiple_roots(self):
        """Multiple genuine no-manager employees are all roots."""
        employees = [
            self._make_emp("DIV-001", "Root A", "root_a@example.com"),
            self._make_emp("DIV-002", "Root B", "root_b@example.com"),
            self._make_emp("DIV-003", "Report", "report@example.com", manager_id="DIV-001"),
        ]
        _, roots, _ = self._resolve_and_analyze(employees)

        self.assertEqual(set(roots), {"DIV-001", "DIV-002"})


if __name__ == "__main__":
    unittest.main()