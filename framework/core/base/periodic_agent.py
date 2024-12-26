from abc import abstractmethod
from typing import final
from dataclasses import dataclass

from ..base.looping_agent import LoopingProcessAgent, LoopingThreadAgent
from ...utilities.periodic_timer import PeriodicTimer


class PeriodicProcessAgent(LoopingProcessAgent):
    @dataclass
    class Config(LoopingProcessAgent.Config):
        """
        Periodic agent configuration class.

        Attributes:
            execution_interval (float): The interval between two consecutive executions.
            delay_compensation (bool): Compensate the delay in the execution.
            logger (LoggerConfig): Logger configuration.
        """

        execution_interval: float = 1
        delay_compensation: bool = False

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        self.timer = None
        self.interval = self.config.execution_interval
        self.compensate_delay = self.config.delay_compensation

    def setup(self):
        self.timer = PeriodicTimer(
            logger=self.logger,
            interval=self.interval,
            compensate_delay=self.compensate_delay,
        )

    @final
    def cycle(self):
        self.runner()

        if self.timer.wait(self._stop_event):
            # stopping the process
            return

    @abstractmethod
    def runner(self):
        """
        Here you have to implement the logic to be executed
        periodically.
        """
        pass


class PeriodicThreadAgent(LoopingThreadAgent):
    @dataclass
    class Config(LoopingProcessAgent.Config):
        """
        Periodic agent configuration class.

        Attributes:
            execution_interval (float): The interval between two consecutive executions.
            delay_compensation (bool): Compensate the delay in the execution.
            logger (LoggerConfig): Logger configuration.
        """

        execution_interval: float = 1
        delay_compensation: bool = False

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

        self.timer = None
        self.interval = self.config.execution_interval
        self.compensate_delay = self.config.delay_compensation

    def setup(self):
        self.timer = PeriodicTimer(
            logger=self.logger,
            interval=self.interval,
            compensate_delay=self.compensate_delay,
        )

    @final
    def cycle(self):
        self.runner()

        if self.timer.wait(self._stop_event):
            # stopping the process
            return

    @abstractmethod
    def runner(self):
        """
        Here you have to implement the logic to be executed
        periodically.
        """
        pass
