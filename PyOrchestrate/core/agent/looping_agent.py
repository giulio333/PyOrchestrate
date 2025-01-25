from abc import abstractmethod, ABC
from typing import final, TypeVar, Type
import multiprocessing
import threading

from ..base.exceptions import RecoverableException, NonRecoverableException
from .base_agent import BaseAgent


class LoopingAgentConfig(BaseAgent.Config):
    """
    Looping agent configuration class.

    Class attributes store default values for configuration parameters. These values can be
    overridden either in derived classes or through constructor arguments.

    User-defined attributes follow the same pattern, they can be set via constructor
    arguments or overridden in derived classes.

    Attributes:
        limit (int): The maximum number of iterations, defaults to -1 (infinite).
        logger (LoggerConfig): Logger configuration.

    Examples:
        Creating a custom configuration for a ChatAgent:

        >>> class ChatAgentConfig(LoopingAgent.Config):
        ...     limit: int = 10               # Default limit for the number of iterations
        ...     model_name = "gpt-3.5-turbo"  # Default model name
        ...     max_tokens = 1000             # Default maximum tokens per request
        ...     temperature = 0.7             # Default temperature for sampling

        >>> # Default configuration
        >>> default_chat_config = ChatAgentConfig()

        >>> # Custom configuration
        >>> custom_chat_config = ChatAgentConfig(
        ...     limit=5,
        ...     model_name="gpt-4",
        ...     max_tokens=2000,
        ...     temperature=0.9
        ... )
    """

    limit: int = -1

    def __init__(self, limit: int | None = None, **kwargs):
        super().__init__(**kwargs)

        if limit is not None:
            self.limit = limit

    def validate(self):
        super().validate()
        if self.limit < -1:
            raise ValueError("Limit must be greater than 0 or equal to -1.")


T = TypeVar("T", bound=LoopingAgentConfig)


class LoopingAgent(BaseAgent[T]):
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

    def __init__(self, name: str, config: T, **kwargs):
        super().__init__(name=name, config=config, **kwargs)

    @final
    def execute(self):
        """
        Execute the agent cycle method in a loop.

        If the limit is set, the loop will stop after reaching that, otherwise it will run indefinitely.

        Warnings:
            Do not override this method. If you need to implement custom logic when the agent is started, you can
            override the `setup` and `cycle` methods.
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
    def safe_cycle(self):
        """
        Execute the agent's cycle logic to be executed in each iteration of the loop in a try-except block.

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
    def cycle(self):
        """
        Define the agent's cycle logic to be executed in each iteration of the loop.

        Notes:

        """

    @abstractmethod
    def _info(self):
        super()._info()
        self.logger.debug(f"Config: limit: {self.config.limit}")


class LoopingProcessAgent(LoopingAgent[T], multiprocessing.Process, ABC):
    a_type: str = "process"

    def __init__(self, name: str, config: T, **kwargs):
        multiprocessing.Process.__init__(self, name=name)
        LoopingAgent.__init__(
            self, name=name, config=config, a_type="process", **kwargs
        )


class LoopingThreadAgent(LoopingAgent[T], threading.Thread, ABC):
    a_type: str = "thread"

    def __init__(self, name: str, config: T, **kwargs):
        threading.Thread.__init__(self, name=name)
        LoopingAgent.__init__(self, name=name, config=config, a_type="thread", **kwargs)
