"""
Tests for the application import service.
"""
import io
import unittest

from hris.services.import_service import run_import_pipeline
from hris.domain.errors import CSVStructureError


class TestImportService(unittest.TestCase):
    def _run(self, csv_content: str):
        """Helper to run pipeline on CSV content."""
        file_obj = io.BytesIO(csv_content.encode("utf-8"))
        return run_import_pipeline(file_obj)

    def test_valid_sample_csv_produces_result(self):
        """Valid sample CSV produces an AnalysisResult with all sections."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,Avery Morgan,avery@example.com,,,\n"
            "DIV-002,Jordan Kim,jordan@example.com,DIV-001,avery@example.com,\n"
        )
        result = self._run(csv_content)

        self.assertEqual(result.analysis.total_source_rows, 2)
        self.assertEqual(len(result.analysis.accepted_employees), 2)
        self.assertEqual(len(result.analysis.validation_errors), 0)
        self.assertEqual(result.analysis.root_employee_ids, ("DIV-001",))
        self.assertEqual(len(result.analysis.manager_summaries), 1)
        self.assertEqual(result.analysis.cyclic_employee_ids, ())

    def test_missing_required_header_raises(self):
        """Missing required header raises CSVStructureError."""
        csv_content = "employee_id,employee_name,email\nDIV-001,John,john@example.com\n"
        file_obj = io.BytesIO(csv_content.encode("utf-8"))

        with self.assertRaises(CSVStructureError):
            run_import_pipeline(file_obj)

    def test_final_validation_errors_include_both_identity_and_manager(self):
        """Final validation errors include both identity and manager errors."""
        # Duplicate identity + missing manager
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,Alice,alice@example.com,,,\n"
            "DIV-001,Bob,bob@example.com,,,\n"  # duplicate ID
            "DIV-002,Carol,carol@example.com,DIV-9999,,\n"  # missing manager
        )
        result = self._run(csv_content)

        error_messages = [e.message for e in result.analysis.validation_errors]
        # Should have duplicate ID errors (2 rows) + missing manager error
        self.assertTrue(any("duplicate employee_id" in m for m in error_messages))
        self.assertTrue(any("could not be found" in m for m in error_messages))

    def test_cycle_results_included_in_analysis(self):
        """Cycle results are included in the final AnalysisResult."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,A,A@example.com,DIV-003,,\n"
            "DIV-002,B,B@example.com,DIV-001,,\n"
            "DIV-003,C,C@example.com,DIV-002,,\n"
        )
        result = self._run(csv_content)

        self.assertEqual(set(result.analysis.cyclic_employee_ids), {"DIV-001", "DIV-002", "DIV-003"})

    def test_employee_name_lookup_available(self):
        """Employee name lookup is provided for UI."""
        csv_content = (
            "employee_id,employee_name,email,manager_id,manager_email,department\n"
            "DIV-001,Avery Morgan,avery@example.com,,,\n"
        )
        result = self._run(csv_content)

        self.assertIn("DIV-001", result.employee_name_lookup)
        self.assertEqual(result.employee_name_lookup["DIV-001"], "Avery Morgan")


if __name__ == "__main__":
    unittest.main()