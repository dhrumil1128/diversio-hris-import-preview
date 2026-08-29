"""
Tests for cycle detection.
"""
import unittest

from hris.hierarchy.cycles import detect_cycles


class TestCycles(unittest.TestCase):
    def test_simple_cycle_three_nodes(self):
        """A → B, B → C, C → A"""
        relationships = (
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
        )
        employee_order = ["A", "B", "C"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ("A", "B", "C"))

    def test_two_node_cycle(self):
        """A → B, B → A"""
        relationships = (
            ("A", "B"),
            ("B", "A"),
        )
        employee_order = ["A", "B"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ("A", "B"))

    def test_cycle_with_incoming_non_cycle(self):
        """A → B, B → C, C → B, D → B
        Expected: B, C only. D is NOT cyclic."""
        relationships = (
            ("A", "B"),
            ("B", "C"),
            ("C", "B"),
            ("D", "B"),
        )
        employee_order = ["A", "B", "C", "D"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ("B", "C"))
        self.assertNotIn("D", result)

    def test_longer_incoming_chain(self):
        """A → B, B → C, C → B, D → A, E → D
        Expected: B, C only."""
        relationships = (
            ("A", "B"),
            ("B", "C"),
            ("C", "B"),
            ("D", "A"),
            ("E", "D"),
        )
        employee_order = ["A", "B", "C", "D", "E"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ("B", "C"))
        self.assertNotIn("A", result)
        self.assertNotIn("D", result)
        self.assertNotIn("E", result)

    def test_acyclic_hierarchy(self):
        """A → B, B → C, C → None (no outgoing edge)"""
        relationships = (
            ("A", "B"),
            ("B", "C"),
        )
        employee_order = ["A", "B", "C"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ())

    def test_longer_acyclic_chain(self):
        """A → B, B → C, C → D, D → None"""
        relationships = (
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
        )
        employee_order = ["A", "B", "C", "D"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ())

    def test_multiple_independent_cycles(self):
        """A → B, B → A
        C → D, D → E, E → C
        Expected: A, B, C, D, E"""
        relationships = (
            ("A", "B"),
            ("B", "A"),
            ("C", "D"),
            ("D", "E"),
            ("E", "C"),
        )
        employee_order = ["A", "B", "C", "D", "E"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(set(result), {"A", "B", "C", "D", "E"})
        # Verify deterministic order
        self.assertEqual(result, ("A", "B", "C", "D", "E"))

    def test_disconnected_acyclic_and_cyclic(self):
        """Acyclic component: A → B, B → C
        Cyclic component: D → E, E → D
        Expected: D, E"""
        relationships = (
            ("A", "B"),
            ("B", "C"),
            ("D", "E"),
            ("E", "D"),
        )
        employee_order = ["A", "B", "C", "D", "E"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ("D", "E"))

    def test_self_loop(self):
        """A → A"""
        relationships = (("A", "A"),)
        employee_order = ["A"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ("A",))

    def test_manager_only_not_in_cycle(self):
        """A → B, B → C, C → D (D is manager with no outgoing edge)
        D should not be marked cyclic just because others report to it."""
        relationships = (
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
        )
        employee_order = ["A", "B", "C", "D"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ())

    def test_cycle_member_also_has_incoming_reports(self):
        """B is in a cycle (B→C→B) and also has A reporting to it.
        A should NOT be cyclic."""
        relationships = (
            ("A", "B"),
            ("B", "C"),
            ("C", "B"),
        )
        employee_order = ["A", "B", "C"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ("B", "C"))

    def test_deterministic_ordering(self):
        """Output order follows employee_order regardless of traversal order."""
        relationships = (
            ("C", "A"),
            ("A", "B"),
            ("B", "C"),
        )
        # Different order than natural traversal
        employee_order = ["A", "B", "C"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ("A", "B", "C"))

    def test_empty_relationships(self):
        """Empty relationships produce no cycles."""
        relationships = ()
        employee_order = []
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ())

    def test_single_employee_no_cycle(self):
        """Single employee with no manager relationship."""
        relationships = ()
        employee_order = ["A"]
        result = detect_cycles(relationships, employee_order)
        self.assertEqual(result, ())


if __name__ == "__main__":
    unittest.main()