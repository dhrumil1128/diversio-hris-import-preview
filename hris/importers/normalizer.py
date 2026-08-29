"""
Normalization helpers for HRIS CSV fields.

This module provides pure functions for normalizing parsed CSV row values
according to the assessment specification.
"""

from typing import Dict, Optional


def normalize_value(value: Optional[str]) -> Optional[str]:
    """
    Trim surrounding whitespace from a string value.

    Returns None if the input is None or becomes empty after stripping.
    """
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def normalize_email(value: Optional[str]) -> Optional[str]:
    """
    Normalize an email field: trim whitespace and lowercase.

    Returns None if the input is None or becomes empty after stripping.
    """
    if value is None:
        return None
    stripped = value.strip().lower()
    return stripped if stripped else None


def normalize_row(raw_row: Dict[str, str]) -> Dict[str, Optional[str]]:
    """
    Normalize a parsed CSV row according to HRIS import rules.

    Normalization rules:
    - All fields: trim surrounding whitespace
    - email: lowercase after trimming
    - manager_email: lowercase after trimming
    - employee_id: trim only, PRESERVE CASE
    - manager_id: trim only, PRESERVE CASE
    - employee_name: trim only, preserve internal whitespace
    - department: trim only, preserve internal whitespace

    Empty strings after trimming become None.

    Args:
        raw_row: Dictionary mapping header names to raw string values.

    Returns:
        Dictionary with normalized values (None for empty/blank fields).
    """
    return {
        "employee_id": normalize_value(raw_row.get("employee_id")),
        "employee_name": normalize_value(raw_row.get("employee_name")),
        "email": normalize_email(raw_row.get("email")),
        "manager_id": normalize_value(raw_row.get("manager_id")),
        "manager_email": normalize_email(raw_row.get("manager_email")),
        "department": normalize_value(raw_row.get("department")),
    }