"""
Application-level orchestration for HRIS import preview.

Coordinates the complete analysis pipeline:
CSV parsing → normalization → identity validation → manager resolution
→ hierarchy analysis → cycle detection → final AnalysisResult
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from hris.domain.entities import Employee, ValidationError
from hris.domain.results import AnalysisResult, ManagerResolutionResult
from hris.domain.errors import CSVStructureError
from hris.importers import parse_csv_to_list, validate_identities
from hris.hierarchy.resolver import resolve_managers
from hris.hierarchy.analyzer import analyze_hierarchy
from hris.hierarchy.cycles import detect_cycles


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Complete result of an HRIS import analysis request."""
    analysis: AnalysisResult
    # Additional presentation helpers
    employee_name_lookup: Dict[str, str]


def run_import_pipeline(file_obj) -> ImportResult:
    """
    Execute the complete HRIS import analysis pipeline.

    Args:
        file_obj: Django UploadedFile or similar file-like object.

    Returns:
        ImportResult containing AnalysisResult and presentation helpers.

    Raises:
        CSVStructureError: If the CSV structure is invalid (missing headers, encoding, etc.)
    """
    # 1. Parse CSV (handles UTF-8, BOM, header validation)
    parsed_rows = parse_csv_to_list(file_obj)
    total_source_rows = len(parsed_rows)

    # 2. Identity validation (normalization + required fields + duplicate detection)
    validation_result = validate_identities(parsed_rows)

    # 3. Build row number map for manager resolution errors
    row_numbers: Dict[str, int] = {}
    for row_number, raw_row in parsed_rows:
        emp_id = raw_row.get("employee_id", "").strip()
        if emp_id:
            row_numbers[emp_id] = row_number

    # 4. Manager resolution
    manager_resolution = resolve_managers(
        validation_result.accepted_employees,
        row_numbers,
    )

    # 5. Combine identity errors + manager errors
    all_validation_errors = tuple(
        list(validation_result.validation_errors) + list(manager_resolution.manager_errors)
    )

    # 6. Hierarchy analysis (roots + direct-report counts)
    root_employee_ids, manager_summaries = analyze_hierarchy(manager_resolution)

    # 7. Cycle detection
    employee_order = [emp.employee_id for emp in validation_result.accepted_employees]
    cyclic_employee_ids = detect_cycles(manager_resolution.relationships, employee_order)

    # 8. Build employee name lookup for UI
    employee_name_lookup = {
        emp.employee_id: emp.employee_name
        for emp in validation_result.accepted_employees
    }

    # 9. Construct final AnalysisResult
    analysis = AnalysisResult(
        total_source_rows=total_source_rows,
        accepted_employees=validation_result.accepted_employees,
        validation_errors=all_validation_errors,
        root_employee_ids=root_employee_ids,
        manager_summaries=manager_summaries,
        cyclic_employee_ids=cyclic_employee_ids,
    )

    return ImportResult(
        analysis=analysis,
        employee_name_lookup=employee_name_lookup,
    )