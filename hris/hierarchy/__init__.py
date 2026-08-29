"""
Hierarchy resolution, analysis, and cycle detection.
"""

from hris.hierarchy.resolver import resolve_managers
from hris.hierarchy.analyzer import analyze_hierarchy
from hris.hierarchy.cycles import detect_cycles
from hris.domain.results import ManagerResolutionResult

__all__ = [
    "resolve_managers",
    "analyze_hierarchy",
    "detect_cycles",
    "ManagerResolutionResult",
]