"""
Hierarchy analysis: root detection, direct-report counting, manager summaries.
"""

from collections import defaultdict
from typing import Dict, List, Tuple

from hris.domain.entities import Employee, ManagerSummary
from hris.domain.results import ManagerResolutionResult


def analyze_hierarchy(resolution: ManagerResolutionResult) -> Tuple[Tuple[str, ...], Tuple[ManagerSummary, ...]]:
    """
    Analyze the reporting hierarchy from resolved manager relationships.

    Calculates:
    - Root employees (those with genuinely no manager reference)
    - Direct-report counts for each manager
    - Manager summaries for the final UI

    Args:
        resolution: Result from manager resolution containing accepted employees,
                    valid relationships, and no-manager/error employee sets.

    Returns:
        Tuple of (root_employee_ids, manager_summaries)
        Both tuples are deterministically ordered by employee source order.
    """
    # Build employee lookup for name retrieval
    employees_by_id: Dict[str, Employee] = {
        emp.employee_id: emp for emp in resolution.accepted_employees
    }

    # Count direct reports from valid relationships only
    direct_report_counts: Dict[str, int] = defaultdict(int)
    for emp_id, manager_id in resolution.relationships:
        direct_report_counts[manager_id] += 1

    # Root employees: only those with genuinely no manager reference
    # (not those with failed manager resolution)
    root_employee_ids = tuple(resolution.no_manager_employee_ids)

    # Build manager summaries deterministically ordered by source order
    # Filter to managers with at least one direct report
    manager_summaries = _build_manager_summaries(
        employees_by_id=employees_by_id,
        direct_report_counts=direct_report_counts,
        accepted_order=[emp.employee_id for emp in resolution.accepted_employees],
    )

    return root_employee_ids, manager_summaries


def _build_manager_summaries(
    employees_by_id: Dict[str, Employee],
    direct_report_counts: Dict[str, int],
    accepted_order: List[str],
) -> Tuple[ManagerSummary, ...]:
    """
    Build ManagerSummary objects for managers with direct reports.

    Ordered by the original accepted employee order for determinism.
    Only includes managers who have at least one valid direct report.
    """
    summaries: List[ManagerSummary] = []

    for emp_id in accepted_order:
        count = direct_report_counts.get(emp_id, 0)
        if count > 0:
            emp = employees_by_id[emp_id]
            summaries.append(ManagerSummary(
                employee_id=emp.employee_id,
                name=emp.employee_name,
                direct_report_count=count,
            ))

    return tuple(summaries)