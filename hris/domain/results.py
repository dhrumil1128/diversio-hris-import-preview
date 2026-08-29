"""
Result containers for validation, hierarchy analysis, and cycle detection.

This module defines the top‑level analysis result object.  It is kept separate
from :mod:`hris.domain.entities` to emphasise the distinction between
primitive domain values and the aggregate result returned by the import
pipeline.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

from hris.domain.entities import Employee, ValidationError, ManagerSummary


@dataclass(frozen=True, slots=True)
class ManagerResolutionResult:
    """
    Intermediate result of manager resolution.

    Contains the identity-valid employees, their valid reporting relationships,
    and manager-related validation errors.  This is distinct from the final
    AnalysisResult because root/cycle/direct-report analysis has not yet been
    performed.

    The key distinction preserved here is between:
    - Employees with no manager reference (genuine root candidates)
    - Employees with an invalid manager reference (manager error, NOT a root)
    """
    accepted_employees: Tuple[Employee, ...]
    manager_errors: Tuple[ValidationError, ...]
    # Valid reporting relationships: employee_id -> manager_id
    relationships: Tuple[Tuple[str, str], ...]
    # Employees with no manager reference (neither manager_id nor manager_email)
    no_manager_employee_ids: Tuple[str, ...]
    # Employees with manager errors (invalid manager reference)
    manager_error_employee_ids: Tuple[str, ...]

    def get_relationship_map(self) -> Dict[str, str]:
        """Return relationships as a dict for O(1) lookups."""
        return dict(self.relationships)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """
    Complete result of an HRIS import analysis.

    The fields are kept separate to reflect the distinct concepts required by
    the assessment.  An employee can be "accepted" yet still have a manager
    error; such employees are excluded from the reporting graph (no root,
    no relationship, no cycle participation).
    """
    total_source_rows: int
    accepted_employees: Tuple[Employee, ...]
    validation_errors: Tuple[ValidationError, ...]
    root_employee_ids: Tuple[str, ...]
    manager_summaries: Tuple[ManagerSummary, ...]
    cyclic_employee_ids: Tuple[str, ...]