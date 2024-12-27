from abc import abstractmethod
from typing import final

from .exceptions import RecoverableException, NonRecoverableException
from ..base.base import AbstractBaseAgent


class LoopingAgent(AbstractBaseAgent):
    class Config(AbstractBaseAgent.Config):
        """
        PeriodicProcessAgent configuration class.

        Attributes:
            execution_interval (float): The interval between two consecutive executions.
            delay_compensation (bool): Compensate the delay in the execution.
            limit (int): The maximum number of iterations.
            logger (LoggerConfig): Logger configuration.
        """
        execution_interval: float = 1
        delay_compensation: bool = False
        limit: int | None = None

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

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
