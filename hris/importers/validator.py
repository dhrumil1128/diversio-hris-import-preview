"""
Validation logic for HRIS employee identity.

This module validates required identity fields and detects duplicate
employee IDs and emails after normalization.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from hris.domain.entities import Employee, ValidationError
from hris.importers.normalizer import normalize_row


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Result of identity validation pass.

    Contains accepted employees and validation errors.
    Invalid rows are excluded from accepted_employees.
    """
    accepted_employees: Tuple[Employee, ...]
    validation_errors: Tuple[ValidationError, ...]


def validate_identities(
    parsed_rows: Sequence[Tuple[int, Dict[str, str]]]
) -> ValidationResult:
    """
    Validate employee identity fields and detect duplicates.

    Performs two-pass validation:
    1. First pass: normalize all rows, collect required-field errors,
       build identity indexes for duplicate detection
    2. Second pass: mark rows with duplicate identities as invalid

    Args:
        parsed_rows: Sequence of (row_number, raw_row_dict) from csv_parser.

    Returns:
        ValidationResult with accepted employees and all validation errors.

    Duplicate semantics:
    - employee_id is case-sensitive: "DIV-100" != "div-100"
    - email is case-insensitive (normalized to lowercase)
    - ALL rows sharing a duplicated identity are invalid
    - Invalid rows are excluded from accepted_employees
    """
    # First pass: normalize, check required fields, build indexes
    normalized_rows: List[Tuple[int, Dict[str, Optional[str]]]] = []
    id_to_rows: Dict[str, List[int]] = defaultdict(list)
    email_to_rows: Dict[str, List[int]] = defaultdict(list)
    required_field_errors: List[ValidationError] = []

    for row_number, raw_row in parsed_rows:
        normalized = normalize_row(raw_row)
        normalized_rows.append((row_number, normalized))

        emp_id = normalized.get("employee_id")
        email = normalized.get("email")

        # Required field validation
        if emp_id is None:
            required_field_errors.append(
                ValidationError(row_number=row_number, message="employee_id is required")
            )
        else:
            id_to_rows[emp_id].append(row_number)

        if email is None:
            required_field_errors.append(
                ValidationError(row_number=row_number, message="email is required")
            )
        else:
            email_to_rows[email].append(row_number)

    # Identify duplicate identities
    duplicate_ids: Set[str] = {eid for eid, rows in id_to_rows.items() if len(rows) > 1}
    duplicate_emails: Set[str] = {em for em, rows in email_to_rows.items() if len(rows) > 1}

    # Second pass: build accepted employees and collect duplicate errors
    accepted: List[Employee] = []
    duplicate_errors: List[ValidationError] = []

    for row_number, normalized in normalized_rows:
        emp_id = normalized.get("employee_id")
        email = normalized.get("email")

        # Skip rows that already have required field errors
        has_required_error = any(
            e.row_number == row_number for e in required_field_errors
        )
        if has_required_error:
            continue

        # Check for duplicate identities
        is_dup_id = emp_id in duplicate_ids
        is_dup_email = email in duplicate_emails

        if is_dup_id:
            duplicate_errors.append(
                ValidationError(
                    row_number=row_number,
                    message=f"duplicate employee_id: {emp_id}"
                )
            )
        if is_dup_email:
            duplicate_errors.append(
                ValidationError(
                    row_number=row_number,
                    message=f"duplicate email: {email}"
                )
            )

        # Only accept if no identity errors
        if not is_dup_id and not is_dup_email:
            accepted.append(Employee(
                employee_id=emp_id,  # type: ignore[arg-type]  # validated not None
                employee_name=normalized.get("employee_name") or "",
                email=email,  # type: ignore[arg-type]  # validated not None
                manager_id=normalized.get("manager_id"),
                manager_email=normalized.get("manager_email"),
                department=normalized.get("department") or "",
            ))

    all_errors = tuple(required_field_errors + duplicate_errors)
    return ValidationResult(
        accepted_employees=tuple(accepted),
        validation_errors=all_errors,
    )