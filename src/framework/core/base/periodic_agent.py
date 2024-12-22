from abc import abstractmethod
from typing import final
from dataclasses import dataclass

from framework.core.base.looping_agent import LoopingProcessAgent, LoopingThreadAgent
from framework.utilities.periodic_timer import PeriodicTimer


class PeriodicProcessAgent(LoopingProcessAgent):

    @dataclass
    class Config(LoopingProcessAgent.Config):
        """
        Configuration parameters for the PeriodicProcessAgent.

        Attributes:
            interval (float): the interval between two consecutive
            compensate_delay (bool): compensate the delay in the execution
        """

        interval: float = 1
        compensate_delay: bool = False

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

        self.interval = self.config.interval
        self.compensate_delay = self.config.compensate_delay

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

    def __init__(
        self, name: str, interval: float, compensate_delay: bool, *args, **kwargs
    ):
        super().__init__(name=name, *args, **kwargs)
        self.interval = interval
        self.compensate_delay = compensate_delay

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
