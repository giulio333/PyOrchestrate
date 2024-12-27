from abc import abstractmethod
from typing import final, cast
from dataclasses import dataclass

from .looping_agent import LoopingAgent
from ...utilities.periodic_timer import PeriodicTimer


class PeriodicAgent(LoopingAgent):
    """
    Periodic agent class.

    This agent executes a process periodically, with a fixed interval.

    Notes:
        Derived classes must implement the `runner` method to define the logic to be executed. You can also implement the
        `setup` method to initialize some agent attributes before the cycle method (use super().setup()).

    Warnings:
        The `cycle` method must not be implemented in the derived class.

    Methods:
        runner: The method to be executed periodically. This method must be implemented in the derived class.
        setup: Setup method to initialize the agent. This method is called once before the agent cycle method.
        cycle: The method that defines the agent's work to be done in each iteration of the loop.
            This method must be implemented in the derived class.
    """

    class Config(LoopingAgent.Config):
        """
        PeriodicProcessAgent configuration class.

        Attributes:
            execution_interval (float): The interval between two consecutive executions.
            delay_compensation (bool): Compensate the delay in the execution.
            limit (int): The maximum number of iterations.
            logger (LoggerConfig): Logger configuration.
        """

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
