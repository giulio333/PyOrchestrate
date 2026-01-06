"""Agent lifecycle management for registration, startup, and termination."""

import time
from PyOrchestrate.core.orchestrator.memory import OMemory, AgentEntry
from PyOrchestrate.core.base.base import BaseClass
from PyOrchestrate.core.agent.base_agent import BaseAgent, AgentProtocol
from PyOrchestrate.core.utilities.messaging import MessageChannel


class AgentLifecycleManager:
    """
    Manages the complete lifecycle of agents.

    This class handles:
    - Agent registration with validation
    - Agent startup with timeout protection
    - Agent termination (individual and bulk)
    - Configuration injection and validation

    Example:
        >>> manager = AgentLifecycleManager(memory, config, logger)
        >>> entry = manager.register_agent(MyAgent, "agent1", custom_config=config)
        >>> success = manager.start_agent("agent1")
        >>> manager.stop_agent("agent1")
    """

    def __init__(self, memory: OMemory, config: BaseClass.Config, logger):
        """
        Initialize the lifecycle manager.

        Args:
            memory: OMemory instance for agent storage
            config: Orchestrator configuration
            logger: Logger instance
        """
        self.memory = memory
        self.config = config
        self.logger = logger

    def register_agent(
        self,
        agent_class: type[AgentProtocol],
        name: str,
        custom_config: BaseClass.Config | None = None,
        custom_plugin: BaseClass.Plugin | None = None,
        control_events: BaseAgent.ControlEvents | None = None,
        state_events: BaseAgent.StateEvents | None = None,
        msg_channel: MessageChannel | None = None,
        **kwargs,
    ) -> AgentEntry:
        """
        Register an agent with the orchestrator.

        Args:
            agent_class: The agent class to instantiate
            name: Unique name for the agent
            custom_config: Optional custom configuration
            custom_plugin: Optional custom plugin
            control_events: Control events for the agent
            state_events: State events for the agent
            msg_channel: Message channel for agent communication
            **kwargs: Additional arguments passed to agent

        Returns:
            AgentEntry: The registered agent entry

        Raises:
            ValueError: If agent name is not unique
            ConfigValidationError: If agent config is invalid
        """
        agent_entry: AgentEntry = self.memory.add_agent(
            agent_class=agent_class,
            name=name,
            custom_config=custom_config,
            custom_plugin=custom_plugin,
            control_events=control_events,
            state_events=state_events,
            msg_channel=msg_channel,
            **kwargs,
        )

        self.logger.debug(f"Agent '{name}' registered.")
        return agent_entry

    def start_agent(self, agent_name: str) -> bool:
        """
        Start an agent with timeout protection.

        Waits for agent.state_events.start_event with configured timeout.
        If timeout is exceeded, attempts to stop the agent and returns False.

        Args:
            agent_name: Name of the agent to start

        Returns:
            bool: True if agent started successfully, False if timeout occurred

        Raises:
            ValueError: If agent not found
            Exception: If agent.start() fails critically
        """
        agent = self.memory.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found.")

        # Initialize agent
        try:
            agent.initialize_agent()
        except Exception as e:
            self.logger.error(f"Failed to initialize agent '{agent_name}': {e}")
            raise

        # Start agent with timeout protection
        try:
            start_time = time.time()
            agent.start()

            # Wait for agent to actually start (with timeout)
            if agent.state_events and agent.state_events.start_event:
                if not agent.state_events.start_event.wait(
                    timeout=self.config.agent_start_timeout
                ):
                    elapsed = time.time() - start_time
                    self.logger.error(
                        f"Agent '{agent_name}' failed to start within timeout "
                        f"({elapsed:.1f}s > {self.config.agent_start_timeout}s)"
                    )

                    # Try to stop the agent to clean up
                    try:
                        agent.stop()
                    except Exception as stop_error:
                        self.logger.error(
                            f"Failed to stop timed-out agent '{agent_name}': {stop_error}"
                        )

                    return False

            self.logger.info(f"Agent '{agent_name}' started successfully.")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start agent '{agent_name}': {e}")
            raise

    def stop_agent(self, agent_name: str) -> None:
        """
        Stop a specific agent.

        Args:
            agent_name: Name of the agent to stop

        Raises:
            ValueError: If agent not found
        """
        agent = self.memory.get_agent(agent_name)

        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found.")

        agent.stop()
        self.logger.info(f"Agent '{agent_name}' stopped.")

    def stop_all(self) -> None:
        """Stop all registered agents."""
        for agent in self.memory.agents:
            agent.stop()
            self.logger.info(f"Stopping agent '{agent.name}'.")

    def get_agent(self, agent_name: str) -> AgentEntry:
        """
        Retrieve an agent entry by name.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentEntry: The agent entry

        Raises:
            ValueError: If agent not found
        """
        a = self.memory.get_agent(agent_name)
        if not a:
            raise ValueError(f"Agent '{agent_name}' not found.")
        return a

    def get_all_agents(self) -> list[AgentEntry]:
        """
        Get all registered agents.

        Returns:
            list[AgentEntry]: List of all agent entries
        """
        return self.memory.agents
