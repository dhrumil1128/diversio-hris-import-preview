"""
CSV import pipeline: parsing, normalization, validation.

Public API:
- parse_csv: Parse uploaded CSV file into structured rows with row numbers
- normalize_row: Normalize a single parsed row
- validate_identities: Validate identity fields and detect duplicates
"""

from hris.importers.csv_parser import parse_csv, parse_csv_to_list
from hris.importers.normalizer import normalize_row
from hris.importers.validator import validate_identities, ValidationResult

__all__ = [
    "parse_csv",
    "parse_csv_to_list",
    "normalize_row",
    "validate_identities",
    "ValidationResult",
]