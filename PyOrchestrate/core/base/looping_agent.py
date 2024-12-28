from abc import abstractmethod
from typing import final, TypeVar

from .exceptions import RecoverableException, NonRecoverableException
from .base_agent import BaseAgent


class LoopingAgentConfig(BaseAgent.Config):

    def __init__(self, limit: int | None = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.limit: int | None = limit


T = TypeVar('T', bound=LoopingAgentConfig)


class LoopingAgent(BaseAgent[T]):
    class Config(LoopingAgentConfig):
        """
        PeriodicProcessAgent configuration class.

        Attributes:
            limit (int): The maximum number of iterations.
            logger (LoggerConfig): Logger configuration.
        """
        pass

    def __init__(self, name: str, config: T, **kwargs):
        super().__init__(name=name, config=config, **kwargs)

    @final
    def execute(self):
        """Execute the agent cycle method in a loop.
        If the limit is set, the loop will stop after reaching that, otherwise it will run indefinitely.
        """

        self.setup()

        # without limit
        if self.config.limit is None:
            while not self._stop_event.is_set():
                self.safe_cycle()

        # with limit
        else:
            for _ in range(self.config.limit):
                if self._stop_event.is_set():
                    break
                self.safe_cycle()
            self.logger.debug(f"Reached limit ({self.config.limit}).")

    def safe_cycle(self):
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
        """
        Abstract method to be implemented in derived classes: Agent setup logic.

        Notes:
            Here you can implement the setup logic.
            This method is called once before the Agent cycle method.
        """
        self._info()
        pass

    @abstractmethod
    def _info(self):
        super()._info()
        self.logger.debug(f"limit: {self.config.limit}")
