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

        Duplicate edges are ignored: declaring the same dependency twice (either
        by calling this method again or by repeating a name in ``depends_on``)
        leaves the graph unchanged.

        An empty ``depends_on`` adds nothing: the agent would otherwise become a
        node of the graph without having declared a single dependency.

        Args:
            agent_name: Name of the dependent agent
            depends_on: List of agent names that must start before agent_name
        """
        if not depends_on:
            return

        existing = self.dependencies[agent_name]
        for dep in depends_on:
            if dep not in existing:
                existing.append(dep)
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

        Notes:
            The graph is left untouched: sorting reads it through a local view of
            the agents it was asked to order.

        Args:
            agent_names: Set of all agent names to order

        Returns:
            list[str]: Agents in topological order (dependencies before dependents)

        Raises:
            ValueError: If graph has not been validated or contains cycles
        """
        if not self._validated:
            raise ValueError("Graph must be validated before sorting")

        # Local view of the agents to order, including those with no
        # dependencies. Writing them into self.dependencies instead made a
        # query report every registered agent as a node of the graph.
        dependencies = {
            agent: self.dependencies.get(agent, []) for agent in agent_names
        }

        # Compute in-degree for each agent
        in_degree = {agent: 0 for agent in agent_names}
        for agent, deps in dependencies.items():
            for dep in deps:
                in_degree[agent] += 1

        # BFS: start with agents having no dependencies
        queue = deque(agent for agent in agent_names if in_degree[agent] == 0)
        topo_order = []

        while queue:
            node = queue.popleft()
            topo_order.append(node)

            # Reduce in-degree for dependents
            for child, deps in dependencies.items():
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
        # An agent mapped to an empty list is not a dependency: reading the
        # keys alone answered True for a graph that holds no edge at all.
        return any(self.dependencies.values())
