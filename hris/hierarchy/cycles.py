"""
Cycle detection in reporting hierarchy.

This module identifies employees who are MEMBERS of directed reporting cycles.

Algorithm: Iterative DFS with three-state coloring (WHITE/GRAY/BLACK).

Each employee has at most one outgoing edge (to their manager), forming a
functional graph / directed pseudoforest.  We traverse from each unvisited
node, following the manager chain.  When we encounter a GRAY node (currently
on the traversal stack), we've found a cycle.  The cycle members are exactly
the nodes from that GRAY node onwards in the current path.

Key invariant:
- WHITE (0): unvisited
- GRAY (1): currently on the DFS stack (being visited)
- BLACK (2): completely processed (no cycle reachable from here)

This correctly distinguishes cycle members from nodes that merely report
into a cycle (those will be marked BLACK without being part of the cycle).

Time: O(n) - each node/edge visited once
Space: O(n) - state map + recursion stack (iterative, no recursion depth risk)
"""

from typing import Dict, List, Set, Tuple


def detect_cycles(
    relationships: Tuple[Tuple[str, str], ...],
    employee_order: List[str],
) -> Tuple[str, ...]:
    """
    Detect cycle members in the reporting hierarchy.

    Args:
        relationships: Tuple of (employee_id, manager_id) pairs representing
                       valid reporting relationships. Each employee appears
                       at most once as the first element.
        employee_order: List of employee_ids in the desired output order
                        (e.g., accepted employee order) for deterministic results.

    Returns:
        Tuple of employee_ids that are members of at least one cycle,
        ordered according to employee_order.
    """
    # Build adjacency map: employee_id -> manager_id
    # Each node has at most one outgoing edge
    adjacency: Dict[str, str] = {}
    for emp_id, mgr_id in relationships:
        adjacency[emp_id] = mgr_id

    # State: 0 = WHITE (unvisited), 1 = GRAY (visiting), 2 = BLACK (processed)
    state: Dict[str, int] = {}
    cycle_members: Set[str] = set()

    # Initialize all nodes as WHITE
    for emp_id in adjacency:
        state[emp_id] = 0

    # Also include manager nodes that might not have outgoing edges
    for mgr_id in adjacency.values():
        if mgr_id not in state:
            state[mgr_id] = 0

    # Iterative DFS from each unvisited node
    for start_node in adjacency:
        if state[start_node] != 0:
            continue

        # Stack for iterative DFS: (node, iterator_state)
        # iterator_state = 0 means we just arrived at this node
        # iterator_state = 1 means we're returning from the child
        stack: List[Tuple[str, int]] = [(start_node, 0)]
        path: List[str] = []  # current traversal path

        while stack:
            node, iterator_state = stack.pop()

            if iterator_state == 0:
                # First time visiting this node
                if state[node] == 1:
                    # Found a cycle! node is GRAY - it's already on our path
                    # Cycle members are from this node to end of path
                    try:
                        cycle_start_idx = path.index(node)
                        for cycle_node in path[cycle_start_idx:]:
                            cycle_members.add(cycle_node)
                    except ValueError:
                        # Should not happen if state tracking is correct
                        pass
                    continue

                if state[node] == 2:
                    # Already fully processed, nothing to do
                    continue

                # Mark as GRAY (visiting)
                state[node] = 1
                path.append(node)

                # Push return state
                stack.append((node, 1))

                # Follow the manager edge
                if node in adjacency:
                    next_node = adjacency[node]
                    stack.append((next_node, 0))

            else:
                # Returning from child traversal (iterator_state == 1)
                # Mark as BLACK (processed)
                state[node] = 2
                path.pop()

    # Return cycle members in deterministic order (following employee_order)
    return tuple(eid for eid in employee_order if eid in cycle_members)