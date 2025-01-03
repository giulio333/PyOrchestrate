from abc import abstractmethod
from typing import final, TypeVar

from .exceptions import RecoverableException, NonRecoverableException
from .base_agent import BaseAgent

T = TypeVar('T', bound="LoopingAgent.Config")


class LoopingAgent(BaseAgent[T]):
    class Config(BaseAgent.Config):
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

    def __init__(self, name: str, config: T, **kwargs):
        super().__init__(name=name, config=config, **kwargs)

    @final
    def execute(self):
        """
        Execute the agent cycle method in a loop.

        If the limit is set, the loop will stop after reaching that, otherwise it will run indefinitely.
        """
        super().execute()

        # without limit
        if self.config.limit is None:
            while not self._stop_event.is_set():
                self.safe_cycle()

        # with limit
        else:
            limit_reached = True
            for _ in range(self.config.limit):
                if self._stop_event.is_set():
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
            self._stop_event.set()

    @abstractmethod
    def cycle(self):
        """Define the agent's cycle logic to be executed in each iteration of the loop."""

    def setup(self):
        super().setup()

    @abstractmethod
    def _info(self):
        super()._info()
        self.logger.debug(f"Config: limit: {self.config.limit}")
