# Diversio HRIS Import Preview

A Django application for previewing HRIS CSV imports with validation, hierarchy analysis, and cycle detection.

## Overview
This project implements the Diversio Engineer I technical assessment (Stage 1). It provides a server‑rendered UI to upload a CSV file, parse and normalize the data, validate identities, resolve manager relationships, analyze the reporting hierarchy, and detect cycles.

## Setup Instructions

### Prerequisites
- Python 3.10+
- pip

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd diversio-hris-preview

# Create and activate virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Run Django development server
python manage.py runserver

# Open browser to http://127.0.0.1:8000/
```

### Running Tests
```bash
# Run all tests
python manage.py test

# Run with verbose output
python manage.py test -v 2

# Run specific test module
python manage.py test hris.tests.test_csv_parser
```

### Django System Check
```bash
python manage.py check
```

## How to Use the Application
1. Start the development server: `python manage.py runserver`
2. Open http://127.0.0.1:8000/ in your browser
3. Click "Choose File" and select a CSV file exported from your HRIS
4. Click "Upload & Preview"
5. Review the analysis results:
   - **Summary**: Total rows, accepted employees, validation error count
   - **Validation Errors**: Row-level errors with source line numbers
   - **Root Employees**: Employees with genuinely no manager reference
   - **Managers / Direct Reports**: Manager names with direct report counts
   - **Reporting Cycles**: Employees who are members of reporting cycles

The application includes `sample_data/sample_hris.csv` for testing.

## CSV Format Requirements
The uploaded CSV must contain these six columns (order does not matter):
- `employee_id` - Unique identifier (case-sensitive)
- `employee_name` - Employee name
- `email` - Email address (normalized to lowercase, must be unique)
- `manager_id` - Manager's employee_id (optional)
- `manager_email` - Manager's email (optional)
- `department` - Department name (optional)

Quoted values containing commas are supported. UTF-8 and UTF-8 with BOM are supported.

## Architecture

### Project Structure
```
diversio-hris-preview/
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
├── hris/                   # Main application
│   ├── domain/             # Pure domain entities (no Django dependencies)
│   │   ├── entities.py     # Employee, ValidationError, ManagerSummary
│   │   ├── errors.py       # CSVStructureError, DuplicateEmployeeIdError
│   │   └── results.py      # AnalysisResult, ManagerResolutionResult
│   ├── importers/          # CSV parsing, normalization, identity validation
│   │   ├── csv_parser.py
│   │   ├── normalizer.py
│   │   └── validator.py
│   ├── hierarchy/          # Manager resolution, hierarchy analysis, cycle detection
│   │   ├── resolver.py
│   │   ├── analyzer.py
│   │   └── cycles.py
│   ├── services/           # Application orchestration
│   │   └── import_service.py
│   ├── views.py            # Thin Django views
│   ├── forms.py            # Upload form
│   ├── urls.py             # URL routing
│   ├── templates/hris/     # Django templates
│   │   ├── upload.html
│   │   └── results.html
│   └── tests/              # Unit tests
├── sample_data/
│   └── sample_hris.csv
├── manage.py
├── requirements.txt
└── README.md
```

### Data Flow
```
Uploaded CSV
    ↓
CSV Parser (csv_parser.py)          →  Validates headers, handles UTF-8/BOM, yields rows with line numbers
    ↓
Normalizer (normalizer.py)          →  Trims whitespace, lowercases emails, preserves ID case
    ↓
Identity Validator (validator.py)   →  Required fields, duplicate ID/email detection (O(n))
    ↓
Manager Resolver (resolver.py)      →  Builds ID/email indexes, resolves references (O(n))
    ↓
Hierarchy Analyzer (analyzer.py)    →  Roots, direct-report counts, manager summaries (O(n))
    ↓
Cycle Detector (cycles.py)          →  Iterative DFS, exact cycle membership (O(n))
    ↓
Import Service (import_service.py)  →  Orchestrates pipeline, builds AnalysisResult
    ↓
Django View (views.py)              →  Thin adapter, renders templates
```

### Key Design Decisions
- **Pure domain layer**: No Django/database dependencies in `hris/domain/`, `hris/importers/`, `hris/hierarchy/`
- **Immutable dataclasses**: All domain objects use `frozen=True, slots=True` for memory efficiency
- **Two-pass validation**: Normalize → index → validate duplicates → build accepted set
- **Index-based manager resolution**: O(n) using dictionaries, not O(n²) scanning
- **Deterministic output**: Results ordered by source employee order
- **Exact cycle membership**: Three-state iterative DFS distinguishes cycle members from incoming reporters
- **No database persistence**: Analysis is in-memory per request (import preview)
- **Thin views**: Business logic in service layer, views only handle HTTP

## Assumptions
1. Employee IDs are case-sensitive (per assessment: "DIV-100" ≠ "div-100")
2. Emails are compared case-insensitively after normalization to lowercase
3. Duplicate employee IDs or emails invalidate ALL rows sharing that identity
4. Self-management (employee managing themselves) is a manager error
5. Conflicting manager_id and manager_email (pointing to different employees) is an error
6. Employees with manager errors are accepted but: no relationship, not a root, no cycle participation
7. Manager rows may appear before or after reports in CSV
8. Only valid relationships contribute to direct-report counts
9. Cycle detection identifies only cycle members, not employees reporting into cycles

## Known Limitations
1. No authentication or authorization
2. No database persistence of import results (preview only)
3. No pagination for large results (assumes manageable display size)
4. No async processing for very large files
5. Email format validation is not performed (only presence and uniqueness after normalization)
6. Single-threaded processing

## Complexity Analysis
For approximately 100,000 employees:
- **Time**: O(n) overall - each stage processes each employee/edge a bounded number of times
- **Space**: O(n) - dictionaries for indexes, adjacency maps, state tracking
- **Parsing**: O(n) - single pass through CSV
- **Normalization**: O(n) - per-field transformations
- **Identity validation**: O(n) - two passes with dict/set indexes
- **Manager resolution**: O(n) - dict lookups for each employee
- **Hierarchy analysis**: O(n) - single pass through relationships + employees
- **Cycle detection**: O(n) - iterative DFS visits each node/edge once

## Implementation & Testing Time
**Note**: This implementation was developed during local preparation phase. The official 90-minute assessment clock has NOT started. Implementation and testing time will be recorded during the official assessment.

## AI Tools Used
AI assistance was used during development for code generation, review, and debugging across all implementation stages.

## License
Assessment project for Diversio Engineer I technical evaluation.