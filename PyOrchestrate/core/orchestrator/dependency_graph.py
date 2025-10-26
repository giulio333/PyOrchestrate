"""Dependency graph management for agent dependencies."""

from collections import defaultdict, deque


class DependencyGraph:
    """
    Manages dependency relationships between agents.

    This class handles the dependency graph for agents, providing methods to:
    - Add dependencies between agents
    - Validate the graph for correctness (no cycles, valid nodes)
    - Compute topological sort order for agent startup

    Example:
        >>> graph = DependencyGraph()
        >>> graph.add_dependency("agent_a", ["agent_b"])
        >>> graph.validate({"agent_a", "agent_b"})
        >>> order = graph.topological_sort({"agent_a", "agent_b"})
        >>> print(order)  # ['agent_b', 'agent_a']
    """

    def __init__(self):
        """Initialize an empty dependency graph."""
        self.dependencies: dict[str, list[str]] = defaultdict(list)
        self._validated = False

    def add_dependency(self, agent_name: str, depends_on: list[str]) -> None:
        """
        Add dependency: agent_name depends on depends_on agents.

        Args:
            agent_name: Name of the dependent agent
            depends_on: List of agent names that must start before agent_name
        """
        self.dependencies[agent_name].extend(depends_on)
        self._validated = False  # Invalidate cached validation

    def validate(self, valid_agent_names: set[str]) -> None:
        """
        Validate the dependency graph.

        Checks:
        1. All referenced agent names exist in valid_agent_names
        2. No circular dependencies exist

        Args:
            valid_agent_names: Set of all registered agent names

        Raises:
            ValueError: If validation fails (missing agents or cycles detected)
        """
        # Check all agents exist
        for agent, deps in self.dependencies.items():
            if agent not in valid_agent_names:
                raise ValueError(f"Agent '{agent}' not registered")
            for dep in deps:
                if dep not in valid_agent_names:
                    raise ValueError(
                        f"Dependency '{dep}' for agent '{agent}' not registered"
                    )

        # Check for cycles using DFS
        self._detect_cycles()
        self._validated = True

    def _detect_cycles(self) -> None:
        """
        Detect circular dependencies using DFS.

        Raises:
            ValueError: If a cycle is detected
        """
        visited = set()
        stack = set()

        def visit(node: str):
            """Visit a node in the dependency graph."""
            if node in stack:
                raise ValueError(
                    f"Detected a dependency cycle: {node} is part of a cycle."
                )
            if node not in visited:
                stack.add(node)
                for neighbor in self.dependencies.get(node, []):
                    visit(neighbor)
                stack.remove(node)
                visited.add(node)

        for agent in self.dependencies.keys():
            if agent not in visited:
                visit(agent)

    def topological_sort(self, agent_names: set[str]) -> list[str]:
        """
        Compute topological ordering of agents respecting dependencies.

        Uses Kahn's algorithm (BFS) to compute the ordering.
        Agents with no dependencies come first, followed by their dependents.

        Args:
            agent_names: Set of all agent names to order

        Returns:
            list[str]: Agents in topological order (dependencies before dependents)

        Raises:
            ValueError: If graph has not been validated or contains cycles
        """
        if not self._validated:
            raise ValueError("Graph must be validated before sorting")

        # Ensure all agents are in the graph (even with no dependencies)
        for agent in agent_names:
            if agent not in self.dependencies:
                self.dependencies[agent] = []

        # Compute in-degree for each agent
        in_degree = {agent: 0 for agent in agent_names}
        for agent, deps in self.dependencies.items():
            for dep in deps:
                in_degree[agent] += 1

        # BFS: start with agents having no dependencies
        queue = deque(agent for agent in agent_names if in_degree[agent] == 0)
        topo_order = []

        while queue:
            node = queue.popleft()
            topo_order.append(node)

            # Reduce in-degree for dependents
            for child, deps in self.dependencies.items():
                if node in deps:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)

        if len(topo_order) != len(agent_names):
            raise ValueError("Cannot compute topological order (cycle detected)")

        return topo_order

    def get_dependencies(self, agent_name: str) -> list[str]:
        """
        Get list of dependencies for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            list[str]: List of agent names this agent depends on
        """
        return self.dependencies.get(agent_name, [])

    def has_dependencies(self) -> bool:
        """
        Check if any dependencies are defined.

        Returns:
            bool: True if at least one dependency exists, False otherwise
        """
        return bool(self.dependencies)
