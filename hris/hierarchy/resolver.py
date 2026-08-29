"""
Manager resolution: map manager_id and manager_email to employee records.

This module resolves manager references for identity-valid employees into
valid reporting relationships, producing manager validation errors where
references cannot be resolved or conflict.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from hris.domain.entities import Employee, ValidationError
from hris.domain.results import ManagerResolutionResult


@dataclass(frozen=True, slots=True)
class _ManagerResolutionState:
    """Internal state for building the resolution result."""
    employees_by_id: Dict[str, Employee]
    employees_by_email: Dict[str, Employee]
    relationships: List[Tuple[str, str]]
    manager_errors: List[ValidationError]
    no_manager_employee_ids: List[str]
    manager_error_employee_ids: List[str]


def resolve_managers(
    accepted_employees: Tuple[Employee, ...],
    row_numbers: Dict[str, int],
) -> ManagerResolutionResult:
    """
    Resolve manager references for identity-valid employees.

    Builds lookup indexes from the accepted employees and resolves each
    employee's manager_id and/or manager_email.  Produces valid relationships
    and manager validation errors.

    Args:
        accepted_employees: Employees that passed identity validation.
        row_numbers: Mapping from employee_id to source row number (for errors).

    Returns:
        ManagerResolutionResult with relationships and errors.
    """
    # Build lookup indexes
    employees_by_id: Dict[str, Employee] = {}
    employees_by_email: Dict[str, Employee] = {}

    for emp in accepted_employees:
        employees_by_id[emp.employee_id] = emp
        employees_by_email[emp.email] = emp

    state = _ManagerResolutionState(
        employees_by_id=employees_by_id,
        employees_by_email=employees_by_email,
        relationships=[],
        manager_errors=[],
        no_manager_employee_ids=[],
        manager_error_employee_ids=[],
    )

    # Resolve each employee's manager reference(s)
    for emp in accepted_employees:
        _resolve_employee_manager(emp, state, row_numbers)

    return ManagerResolutionResult(
        accepted_employees=accepted_employees,
        manager_errors=tuple(state.manager_errors),
        relationships=tuple(state.relationships),
        no_manager_employee_ids=tuple(state.no_manager_employee_ids),
        manager_error_employee_ids=tuple(state.manager_error_employee_ids),
    )


def _resolve_employee_manager(
    emp: Employee,
    state: _ManagerResolutionState,
    row_numbers: Dict[str, int],
) -> None:
    """Resolve a single employee's manager reference(s)."""
    manager_id = emp.manager_id
    manager_email = emp.manager_email

    # Case 1: No manager references at all
    if manager_id is None and manager_email is None:
        state.no_manager_employee_ids.append(emp.employee_id)
        return

    # Case 2: Only manager_id provided
    if manager_id is not None and manager_email is None:
        _resolve_by_id(emp, manager_id, state, row_numbers)
        return

    # Case 3: Only manager_email provided
    if manager_id is None and manager_email is not None:
        _resolve_by_email(emp, manager_email, state, row_numbers)
        return

    # Case 4: Both manager_id and manager_email provided
    _resolve_both(emp, manager_id, manager_email, state, row_numbers)


def _resolve_by_id(
    emp: Employee,
    manager_id: str,
    state: _ManagerResolutionState,
    row_numbers: Dict[str, int],
) -> None:
    """Resolve manager by employee_id only."""
    # Self-management check
    if manager_id == emp.employee_id:
        _add_manager_error(
            emp,
            f"employee cannot manage themselves",
            state,
            row_numbers,
        )
        return

    manager = state.employees_by_id.get(manager_id)
    if manager is None:
        _add_manager_error(
            emp,
            f"manager_id '{manager_id}' could not be found",
            state,
            row_numbers,
        )
        return

    # Valid relationship
    state.relationships.append((emp.employee_id, manager.employee_id))


def _resolve_by_email(
    emp: Employee,
    manager_email: str,
    state: _ManagerResolutionState,
    row_numbers: Dict[str, int],
) -> None:
    """Resolve manager by manager_email only."""
    # Self-management check
    if manager_email == emp.email:
        _add_manager_error(
            emp,
            f"employee cannot manage themselves",
            state,
            row_numbers,
        )
        return

    manager = state.employees_by_email.get(manager_email)
    if manager is None:
        _add_manager_error(
            emp,
            f"manager_email '{manager_email}' could not be found",
            state,
            row_numbers,
        )
        return

    # Valid relationship
    state.relationships.append((emp.employee_id, manager.employee_id))


def _resolve_both(
    emp: Employee,
    manager_id: str,
    manager_email: str,
    state: _ManagerResolutionState,
    row_numbers: Dict[str, int],
) -> None:
    """Resolve manager when both manager_id and manager_email are provided."""
    # Self-management checks
    if manager_id == emp.employee_id or manager_email == emp.email:
        _add_manager_error(
            emp,
            f"employee cannot manage themselves",
            state,
            row_numbers,
        )
        return

    manager_by_id = state.employees_by_id.get(manager_id)
    manager_by_email = state.employees_by_email.get(manager_email)

    # Check if both references are found
    if manager_by_id is None:
        _add_manager_error(
            emp,
            f"manager_id '{manager_id}' could not be found",
            state,
            row_numbers,
        )
        return

    if manager_by_email is None:
        _add_manager_error(
            emp,
            f"manager_email '{manager_email}' could not be found",
            state,
            row_numbers,
        )
        return

    # Both found - must be the same employee
    if manager_by_id.employee_id != manager_by_email.employee_id:
        _add_manager_error(
            emp,
            f"manager_id and manager_email refer to different employees",
            state,
            row_numbers,
        )
        return

    # Valid relationship
    state.relationships.append((emp.employee_id, manager_by_id.employee_id))


def _add_manager_error(
    emp: Employee,
    message: str,
    state: _ManagerResolutionState,
    row_numbers: Dict[str, int],
) -> None:
    """Add a manager error and track the employee as having a manager error."""
    row_number = row_numbers.get(emp.employee_id, 0)
    state.manager_errors.append(
        ValidationError(row_number=row_number, message=message)
    )
    state.manager_error_employee_ids.append(emp.employee_id)