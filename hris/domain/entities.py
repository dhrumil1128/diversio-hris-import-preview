"""
Entity definitions for HRIS data (employees, relationships, etc.).

This module contains pure domain data structures with no framework dependencies.
All objects are immutable (frozen dataclasses) and suitable for use in
stand-alone unit tests.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Employee:
    """
    Normalized employee record.

    Fields are expected to be pre‑processed by the import layer:
    - `employee_id` retains original case (case‑sensitive key).
    - `email` and `manager_email` are lower‑cased.
    - All string fields have surrounding whitespace stripped.
    """
    employee_id: str
    employee_name: str
    email: str
    manager_id: Optional[str] = None
    manager_email: Optional[str] = None
    department: str = ""


@dataclass(frozen=True, slots=True)
class ValidationError:
    """
    Row‑level validation error preserving source location for UI feedback.

    `row_number` is 1‑based and counts the header as row 1, matching the
    typical CSV line numbering used by spreadsheet tools.
    """
    row_number: int
    message: str


@dataclass(frozen=True, slots=True)
class ManagerSummary:
    """
    Presentation‑ready summary of a manager for the final UI.

    Only the count of direct reports is stored; the full list of reports is
    intentionally omitted to keep the object lightweight.
    """
    employee_id: str
    name: str
    direct_report_count: int