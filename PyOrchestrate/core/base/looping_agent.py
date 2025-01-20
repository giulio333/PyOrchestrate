from abc import abstractmethod, ABC
from typing import final, TypeVar, Type
import multiprocessing
import threading

from .exceptions import RecoverableException, NonRecoverableException
from .base_agent import BaseAgent


class LoopingAgentConfig(BaseAgent.Config):
    """
    Looping agent configuration class.

    Attributes:
        limit (int): The maximum number of iterations.
        logger (LoggerConfig): Logger configuration.

    Notes:
        Class attributes store default values for the configuration parameters. If you want to change the default
        values, you can override them in the derived class or pass them as arguments to the constructor.

        User-defined attributes follow the same pattern. They can be passed as arguments to the constructor or
        overridden in the derived class.

    Examples:
        You can create a custom configuration class by inheriting from the LoopingAgent.Config class and overriding the
        desired attributes.

        >>> class Config(LoopingAgent.Config):
        ...     limit = 10
        >>> default_config = Config()
        >>> custom_config = Config(limit=5)
    """

    limit: int | None = None

    def __init__(self, limit: int | None = None, **kwargs):
        super().__init__(**kwargs)

        if limit is not None:
            self.limit: int = limit

    def validate(self):
        super().validate()
        if self.limit is not None and self.limit <= 0:
            raise ValueError("Limit must be greater than 0.")


T = TypeVar("T", bound=LoopingAgentConfig)


class LoopingAgent(BaseAgent[T]):

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
        if self.config.limit is None:
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
            self.events.stop_event.set()

    @abstractmethod
    def cycle(self):
        """
        Define the agent's cycle logic to be executed in each iteration of the loop.

        Notes:

        """

    def setup(self):
        super().setup()

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
