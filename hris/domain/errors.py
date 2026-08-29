"""
Error types for HRIS import processing.

Only a small set of domain‑level exceptions are defined.  Expected validation
failures are represented as data (:class:`hris.domain.entities.ValidationError`)
rather than raised as exceptions.
"""

from typing import Optional


class DomainError(Exception):
    """Base class for unexpected domain‑layer errors (programmer errors)."""
    pass


class CSVStructureError(DomainError):
    """
    Raised when the uploaded file cannot be parsed as a CSV with the expected
    header columns.  This signals a structural problem (missing header, wrong
    delimiter, encoding issues) rather than row‑level data errors.
    """
    def __init__(self, message: str, *, line_number: Optional[int] = None):
        super().__init__(message)
        self.line_number = line_number


class DuplicateEmployeeIdError(DomainError):
    """
    Raised when the same ``employee_id`` appears more than once in the source
    data.  The assessment treats this as a structural error that aborts the
    import before hierarchy analysis.
    """
    def __init__(self, employee_id: str):
        super().__init__(f"Duplicate employee_id: {employee_id}")
        self.employee_id = employee_id