from abc import abstractmethod, ABC
from typing import final, List
import multiprocessing
import threading

from PyOrchestrate.core.base.exceptions import (
    RecoverableException,
    NonRecoverableException,
)
from PyOrchestrate.core.agent.base_agent import BaseAgent
from PyOrchestrate.core.utilities.validation import ValidationResult, ValidationSeverity


class LoopingAgentConfig(BaseAgent.Config):
    """
    Looping agent configuration class.

    Class attributes store default values for configuration parameters. These values can be
    overridden either in derived classes or through constructor arguments.

    User-defined attributes follow the same pattern, they can be set via constructor
    arguments or overridden in derived classes.

    Attributes:
        limit (int): The maximum number of iterations, defaults to -1 (infinite).
        logger_config (LoggerConfig): Logger configuration.

    Examples:
        Creating a custom configuration for a ChatAgent:

        >>> class ChatAgentConfig(LoopingAgent.Config):
        ...     limit: int = 10               # Default limit for the number of iterations
        ...     model_name = "gpt-3.5-turbo"  # Default model name
        ...     max_tokens = 1000             # Default maximum tokens per request
        ...     temperature = 0.7             # Default temperature for sampling

        >>> # Create Default configuration
        >>> default_chat_config = ChatAgentConfig()

        >>> # Create Custom configuration
        >>> custom_chat_config = ChatAgentConfig(
        ...     limit=5,
        ...     model_name="gpt-4",
        ...     max_tokens=2000,
        ...     temperature=0.9
        ... )
    """

    limit: int = -1
    """
    The maximum number of iterations, defaults to -1 (infinite).
    """

    def __init__(self, limit: int | None = None, **kwargs):
        super().__init__(**kwargs)

        if limit is not None:
            self.limit = limit

    def validate(self) -> List[ValidationResult]:
        """
        Perform LoopingAgent-specific validation.

        Returns:
            List[ValidationResult]: List of validation results.
        """
        results = super().validate()

        if self.limit < -1:
            results.append(
                ValidationResult(
                    field="limit",
                    message="Limit must be greater than or equal to -1.",
                    severity=ValidationSeverity.CRITICAL,
                )
            )

        return results


class LoopingAgent(BaseAgent):
    """
    LoopingAgent class.

    This class provides a common interface for agents that execute a cycle method in a loop.

    Each agent manages two types of events:

    - state_events: For managing the agent's internal state
    - control_events: For handling external commands

    Warnings:
        When overriding methods, always call the parent implementation using super().

    Notes:
        Derived classes must implement the `cycle` method to define their core logic.
        The `setup` method can be optionally overridden to perform initialization
        before the execution cycle begins.

    Attributes:
        state_events (StateEvents): Events for internal state management.
        control_events (ControlEvents): Events for external command handling.

    Methods:
        execute: Executes the agent's core logic in a loop.
        safe_cycle: Executes the agent's cycle method in a try-except block.
        cycle: Defines the agent's core logic to be executed in each iteration of the loop.
        _info: Logs the agent's configuration.
    """

    Config = LoopingAgentConfig

    def __init__(self, name: str | None = None, **kwargs):
        super().__init__(name=name, **kwargs)

    @final
    def execute(self) -> None:
        """
        @final

        Execute the agent cycle method in a loop.

        If the limit is set, the loop will stop after reaching that, otherwise it will run indefinitely.

        Warnings:
            Do not override this method.

        Notes:
            This method is a wrapper around the `safe_cycle` method that runs the agent's cycle logic in a loop.
            It is used to ensure that the agent continues running even if well wknown exceptions are raised.
        """
        super().execute()

        # without limit
        if self.config.limit == -1:
            while not self.control_events.stop_event.is_set():
                self.safe_cycle()

        # with limit
        else:
            limit_reached = True
            for _ in range(self.config.limit):
                if self.control_events.stop_event.is_set():
                    limit_reached = False
                    break
                self.safe_cycle()

            if limit_reached:
                self.logger.debug(f"Reached limit ({self.config.limit}).")

    @final
    def safe_cycle(self) -> None:
        """
        @final

        Execute the agent's cycle logic to be executed in each iteration of
        the loop in a try-except block.

        Warning:
            Do not override this method.

        Notes:
            This method is a wrapper around the `cycle` method that catches exceptions and logs them.
            It is used to ensure that the agent continues running even if an exception is raised.
            If a `RecoverableException` is raised, it will be logged as an error and the agent will continue.
            If a `NonRecoverableException` is raised, it will be logged as an error and the agent will stop

        Returns:
            None
        """
        try:
            self.cycle()
        except RecoverableException as e:
            self.logger.error(f"Recoverable error: {e}")
        except NonRecoverableException as e:
            self.logger.error(f"Non-recoverable error: {e}")
            self.control_events.stop_event.set()

    @abstractmethod
    def cycle(self) -> None:
        """
        @abstractmethod

        Define the agent's cycle logic to be executed in each iteration of the loop.

        Warnings:
            This method must be implemented in derived classes.

        Notes:
            This method must be implemented in derived classes.

        Returns:
            None
        """

    def _info(self) -> None:
        """
        Logs the agent's configuration.

        Warnings:
            This method must be implemented in derived classes.

        Returns:
            None
        """
        super()._info()
        self.logger.debug(f"Config: limit: {self.config.limit}")


class LoopingProcessAgent(LoopingAgent, multiprocessing.Process, ABC):
    """
    LoopingProcessAgent class.

    This class provides a common interface for agents that execute a cycle method in a loop using a separate process.

    Args:
        LoopingAgent (_type_): LoopingAgent class.
        multiprocessing (_type_): multiprocessing module.
        ABC (_type_): ABC module.
    """

    def __init__(self, name: str | None = None, **kwargs):
        """
        Initialize a new LoopingProcessAgent.

        Args:
            name (str): The agent's name. Defaults to None.
        """
        multiprocessing.Process.__init__(self, name=name)
        LoopingAgent.__init__(self, name=name, a_type="process", **kwargs)


class LoopingThreadAgent(LoopingAgent, threading.Thread, ABC):
    """
    LoopingThreadAgent class.

    This class provides a common interface for agents that execute a cycle method in a loop using a separate thread.

    Args:
        LoopingAgent (_type_): LoopingAgent class.
        threading (_type_): threading module.
        ABC (_type_): ABC module.
    """

    def __init__(self, name: str | None = None, **kwargs):
        """
        Initialize a new LoopingThreadAgent.

        Args:
            name (str): The agent's name. Defaults to None.
        """
        threading.Thread.__init__(self, name=name)
        LoopingAgent.__init__(self, name=name, a_type="thread", **kwargs)
