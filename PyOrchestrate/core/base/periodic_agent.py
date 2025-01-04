from abc import abstractmethod
from typing import final, TypeVar

from .looping_agent import LoopingAgent
from ...utilities.periodic_timer import PeriodicTimer

T = TypeVar('T', bound="PeriodicAgent.Config")


class PeriodicAgent(LoopingAgent[T]):
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
        Periodic agent configuration class.

        Attributes:
            execution_interval (float): The interval between two consecutive executions.
            delay_compensation (bool): Compensate the delay in the execution.
            limit (int): The maximum number of iterations.
            logger (LoggerConfig): Logger configuration.

        Notes:
            Class attributes store default values for the configuration parameters. If you want to change the default
            values, you can override them in the derived class or pass them as arguments to the constructor.

            User-defined attributes follow the same pattern. They can be passed as arguments to the constructor or
            overridden in the derived class.

        Examples:
            You can create a custom configuration class by inheriting from the PeriodicAgent.Config class and overriding the
            desired attributes.

            >>> class Config(PeriodicAgent.Config):
            ...     execution_interval = 2
            ...     delay_compensation = True
            >>> default_config = Config()
            >>> custom_config = Config(execution_interval=.2)
        """
        execution_interval: float = 1
        delay_compensation: bool = False

        def __init__(self, execution_interval: float | None = None, delay_compensation: bool | None = None, **kwargs):
            super().__init__(**kwargs)

            if execution_interval is not None:
                self.execution_interval: float = execution_interval

            if delay_compensation is not None:
                self.delay_compensation: bool = delay_compensation

    def __init__(self, name: str, config: T, **kwargs):
        super().__init__(name=name, config=config, **kwargs)

        self.timer = None
        self.interval = self.config.execution_interval
        self.compensate_delay = self.config.delay_compensation

    def setup(self):
        super().setup()
        self.timer = PeriodicTimer(
            logger=self.logger,
            interval=self.interval,
            compensate_delay=self.compensate_delay,
        )

    @final
    def cycle(self):
        self.runner()

        if self.timer.wait(self.control_events.stop_event):
            # stopping the process
            return

    @abstractmethod
    def runner(self):
        """
        Here you have to implement the logic to be executed
        periodically.
        """
        pass

    def _info(self):
        super()._info()
        self.logger.debug(f"Config: execution_interval: {self.interval}")
        self.logger.debug(f"Config: delay_compensation: {self.compensate_delay}")
