"""Unit tests for DependencyGraph class."""

import unittest
from PyOrchestrate.core.orchestrator.dependency_graph import DependencyGraph


class TestDependencyGraph(unittest.TestCase):
    """Test cases for DependencyGraph class."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = DependencyGraph()

    def test_initialization(self):
        """Test graph initializes empty."""
        self.assertEqual(len(self.graph.dependencies), 0)
        self.assertFalse(self.graph._validated)
        self.assertFalse(self.graph.has_dependencies())

    def test_add_single_dependency(self):
        """Test adding a single dependency."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        self.assertEqual(self.graph.get_dependencies("agent_a"), ["agent_b"])
        self.assertTrue(self.graph.has_dependencies())

    def test_add_multiple_dependencies(self):
        """Test adding multiple dependencies for same agent."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        self.graph.add_dependency("agent_a", ["agent_c"])
        deps = self.graph.get_dependencies("agent_a")
        self.assertEqual(len(deps), 2)
        self.assertIn("agent_b", deps)
        self.assertIn("agent_c", deps)

    def test_add_duplicate_dependency_repeated_call(self):
        """Test the same edge declared by two calls is stored once."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        self.graph.add_dependency("agent_a", ["agent_b"])

        self.assertEqual(self.graph.get_dependencies("agent_a"), ["agent_b"])

    def test_add_duplicate_dependency_repeated_element(self):
        """Test a name repeated inside depends_on is stored once."""
        self.graph.add_dependency("agent_a", ["agent_b", "agent_b"])

        self.assertEqual(self.graph.get_dependencies("agent_a"), ["agent_b"])

    def test_topological_sort_with_duplicate_dependency(self):
        """Test a duplicate edge is not mistaken for a cycle."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        self.graph.add_dependency("agent_a", ["agent_b"])
        valid_agents = {"agent_a", "agent_b"}
        self.graph.validate(valid_agents)

        order = self.graph.topological_sort(valid_agents)

        self.assertEqual(order, ["agent_b", "agent_a"])

    def test_topological_sort_with_duplicate_in_depends_on(self):
        """Test a repeated element in depends_on is not mistaken for a cycle."""
        self.graph.add_dependency("agent_a", ["agent_b", "agent_b"])
        valid_agents = {"agent_a", "agent_b"}
        self.graph.validate(valid_agents)

        order = self.graph.topological_sort(valid_agents)

        self.assertEqual(order, ["agent_b", "agent_a"])

    def test_validate_success(self):
        """Test validation succeeds with valid graph."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        valid_agents = {"agent_a", "agent_b"}

        # Should not raise
        self.graph.validate(valid_agents)
        self.assertTrue(self.graph._validated)

    def test_validate_missing_dependent_agent(self):
        """Test validation fails when dependent agent not registered."""
        self.graph.add_dependency("agent_x", ["agent_b"])
        valid_agents = {"agent_b"}  # agent_x not registered

        with self.assertRaises(ValueError) as ctx:
            self.graph.validate(valid_agents)
        self.assertIn("agent_x", str(ctx.exception))
        self.assertIn("not registered", str(ctx.exception))

    def test_validate_missing_dependency(self):
        """Test validation fails when dependency not registered."""
        self.graph.add_dependency("agent_a", ["agent_y"])
        valid_agents = {"agent_a"}  # agent_y not registered

        with self.assertRaises(ValueError) as ctx:
            self.graph.validate(valid_agents)
        self.assertIn("agent_y", str(ctx.exception))
        self.assertIn("not registered", str(ctx.exception))

    def test_detect_simple_cycle(self):
        """Test cycle detection for simple A->B->A cycle."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        self.graph.add_dependency("agent_b", ["agent_a"])
        valid_agents = {"agent_a", "agent_b"}

        with self.assertRaises(ValueError) as ctx:
            self.graph.validate(valid_agents)
        self.assertIn("cycle", str(ctx.exception).lower())

    def test_detect_complex_cycle(self):
        """Test cycle detection for A->B->C->A cycle."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        self.graph.add_dependency("agent_b", ["agent_c"])
        self.graph.add_dependency("agent_c", ["agent_a"])
        valid_agents = {"agent_a", "agent_b", "agent_c"}

        with self.assertRaises(ValueError) as ctx:
            self.graph.validate(valid_agents)
        self.assertIn("cycle", str(ctx.exception).lower())

    def test_topological_sort_simple(self):
        """Test topological sort with simple dependency."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        valid_agents = {"agent_a", "agent_b"}
        self.graph.validate(valid_agents)

        order = self.graph.topological_sort(valid_agents)

        # agent_b must come before agent_a
        self.assertEqual(len(order), 2)
        idx_a = order.index("agent_a")
        idx_b = order.index("agent_b")
        self.assertLess(idx_b, idx_a, "agent_b should come before agent_a")

    def test_topological_sort_chain(self):
        """Test topological sort with chain: C->B->A."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        self.graph.add_dependency("agent_b", ["agent_c"])
        valid_agents = {"agent_a", "agent_b", "agent_c"}
        self.graph.validate(valid_agents)

        order = self.graph.topological_sort(valid_agents)

        # Verify ordering: C before B before A
        idx_a = order.index("agent_a")
        idx_b = order.index("agent_b")
        idx_c = order.index("agent_c")
        self.assertLess(idx_c, idx_b, "agent_c should come before agent_b")
        self.assertLess(idx_b, idx_a, "agent_b should come before agent_a")

    def test_topological_sort_tree(self):
        """Test topological sort with tree structure: B,C depend on A."""
        self.graph.add_dependency("agent_b", ["agent_a"])
        self.graph.add_dependency("agent_c", ["agent_a"])
        valid_agents = {"agent_a", "agent_b", "agent_c"}
        self.graph.validate(valid_agents)

        order = self.graph.topological_sort(valid_agents)

        # agent_a must come first
        self.assertEqual(order[0], "agent_a")
        # agent_b and agent_c can be in any order after agent_a
        self.assertIn("agent_b", order[1:])
        self.assertIn("agent_c", order[1:])

    def test_topological_sort_no_dependencies(self):
        """Test topological sort with no dependencies."""
        valid_agents = {"agent_a", "agent_b", "agent_c"}
        self.graph.validate(valid_agents)

        order = self.graph.topological_sort(valid_agents)

        # All agents should be present, order doesn't matter
        self.assertEqual(len(order), 3)
        self.assertEqual(set(order), valid_agents)

    def test_topological_sort_without_validation(self):
        """Test topological sort fails if graph not validated."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        valid_agents = {"agent_a", "agent_b"}

        # Don't call validate()
        with self.assertRaises(ValueError) as ctx:
            self.graph.topological_sort(valid_agents)
        self.assertIn("must be validated", str(ctx.exception))

    def test_validation_invalidated_on_add(self):
        """Test validation flag reset when dependency added."""
        self.graph.add_dependency("agent_a", ["agent_b"])
        valid_agents = {"agent_a", "agent_b"}
        self.graph.validate(valid_agents)

        self.assertTrue(self.graph._validated)

        # Adding new dependency should invalidate
        self.graph.add_dependency("agent_c", ["agent_a"])
        self.assertFalse(self.graph._validated)

    def test_get_dependencies_empty(self):
        """Test getting dependencies for agent with none."""
        deps = self.graph.get_dependencies("agent_x")
        self.assertEqual(deps, [])

    def test_complex_dag(self):
        """Test complex DAG structure validation and sorting."""
        # Build a diamond DAG: D depends on B,C; B,C depend on A
        self.graph.add_dependency("agent_b", ["agent_a"])
        self.graph.add_dependency("agent_c", ["agent_a"])
        self.graph.add_dependency("agent_d", ["agent_b", "agent_c"])

        valid_agents = {"agent_a", "agent_b", "agent_c", "agent_d"}
        self.graph.validate(valid_agents)

        order = self.graph.topological_sort(valid_agents)

        # Verify constraints
        idx_a = order.index("agent_a")
        idx_b = order.index("agent_b")
        idx_c = order.index("agent_c")
        idx_d = order.index("agent_d")

        self.assertLess(idx_a, idx_b, "A before B")
        self.assertLess(idx_a, idx_c, "A before C")
        self.assertLess(idx_b, idx_d, "B before D")
        self.assertLess(idx_c, idx_d, "C before D")


if __name__ == "__main__":
    unittest.main()
