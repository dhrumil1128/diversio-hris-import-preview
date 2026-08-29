"""
CSV parsing utilities for HRIS import.

This module handles parsing of uploaded CSV files into structured row data
with preserved source row numbers for validation error reporting.
"""

import csv
import io
from typing import Iterator, List, Tuple

from hris.domain.errors import CSVStructureError

REQUIRED_HEADERS = frozenset([
    "employee_id",
    "employee_name",
    "email",
    "manager_id",
    "manager_email",
    "department",
])


def parse_csv(file_obj) -> Iterator[Tuple[int, dict]]:
    """
    Parse a CSV file object yielding (row_number, row_dict) pairs.

    Row numbering convention:
    - CSV header = row 1
    - First employee/data row = row 2
    - Row numbers correspond to physical CSV source rows

    Args:
        file_obj: A file-like object (e.g., Django UploadedFile) positioned at start.

    Yields:
        Tuple of (row_number, row_dict) where row_dict maps header names to values.

    Raises:
        CSVStructureError: If required headers are missing or CSV is malformed.
    """
    # Read and decode the file content
    try:
        raw_content = file_obj.read()
        if isinstance(raw_content, bytes):
            content = raw_content.decode("utf-8-sig")  # Handles UTF-8 BOM automatically
        else:
            content = raw_content
    except UnicodeDecodeError as e:
        raise CSVStructureError(f"Invalid UTF-8 encoding: {e}") from e

    # Use StringIO for csv module
    text_stream = io.StringIO(content)

    # Sniff dialect to handle different delimiters, but enforce comma
    try:
        dialect = csv.Sniffer().sniff(text_stream.read(1024), delimiters=",")
        text_stream.seek(0)
    except csv.Error:
        # Fall back to default excel dialect if sniffing fails
        dialect = csv.excel
        text_stream.seek(0)

    reader = csv.DictReader(text_stream, dialect=dialect)

    # Validate headers
    if reader.fieldnames is None:
        raise CSVStructureError("CSV file is empty or has no headers", line_number=1)

    fieldnames = [name.strip() for name in reader.fieldnames]
    reader.fieldnames = fieldnames  # Update reader with stripped names

    missing = REQUIRED_HEADERS - set(fieldnames)
    if missing:
        raise CSVStructureError(
            f"Missing required headers: {', '.join(sorted(missing))}",
            line_number=1,
        )

    # Yield rows with row numbers (header is row 1, first data row is row 2)
    for row_number, row in enumerate(reader, start=2):
        # Keep raw values; normalization (trimming) happens in normalizer
        yield row_number, dict(row)


def parse_csv_to_list(file_obj) -> List[Tuple[int, dict]]:
    """
    Parse CSV and return all rows as a list.

    Convenience function for cases where the full list is needed upfront
    (e.g., for validation passes that require multiple iterations).

    Args:
        file_obj: A file-like object positioned at start.

    Returns:
        List of (row_number, row_dict) tuples.

    Raises:
        CSVStructureError: If required headers are missing or CSV is malformed.
    """
    return list(parse_csv(file_obj))