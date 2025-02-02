import threading
from abc import abstractmethod, ABC
from typing import final, TypeVar
import multiprocessing

from .looping_agent import LoopingAgent, LoopingAgentConfig
from ...utilities.periodic_timer import PeriodicTimer


class PeriodicAgentConfig(LoopingAgentConfig):
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
        Creating a custom configuration for a PeriodicAgent:

        >>> class PeriodicAgentConfig(PeriodicAgent.Config):
        ...     execution_interval = 2  # Default execution interval
        ...     delay_compensation = True  # Default delay compensation
        ...     limit = 10  # Default limit for the number of iterations

        >>> # Default configuration
        >>> default_periodic_config = PeriodicAgentConfig()

        >>> # Custom configuration
        >>> custom_periodic_config = PeriodicAgentConfig(
        ...     execution_interval=0.5,
        ...     delay_compensation=False,
        ...     limit=5
        ... )
    """

    execution_interval: float = 1
    delay_compensation: bool = False

    def __init__(
        self,
        execution_interval: float | None = None,
        delay_compensation: bool | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if execution_interval is not None:
            self.execution_interval = execution_interval

        if delay_compensation is not None:
            self.delay_compensation = delay_compensation

    def validate(self):
        super().validate()
        if self.execution_interval <= 0:
            raise ValueError("Execution interval must be greater than 0.")
        if not isinstance(self.delay_compensation, bool):
            raise ValueError("Delay compensation must be a boolean.")


T = TypeVar("T", bound=PeriodicAgentConfig)


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

    Config = PeriodicAgentConfig

    def __init__(self, name: str, config: T, **kwargs):
        super().__init__(name=name, config=config, **kwargs)

        self._timer = None
        self.interval = self.config.execution_interval
        self.compensate_delay = self.config.delay_compensation

    def setup(self):
        super().setup()
        self._timer = PeriodicTimer(
            logger=self.logger,
            interval=self.interval,
            compensate_delay=self.compensate_delay,
        )

    @final
    def cycle(self):
        """
        Execute the agent cycle method in a loop.

        Raises:
            ValueError: _description_
        """

        self.runner()

        if self.timer.wait(self.control_events.stop_event):
            # stopping the process
            return

    @abstractmethod
    def runner(self):
        """
        Here you have to implement the logic to be executed periodically.
        """
        pass

    def _info(self):
        super()._info()
        self.logger.debug(f"Config: execution_interval: {self.interval}")
        self.logger.debug(f"Config: delay_compensation: {self.compensate_delay}")

    @property
    def timer(self) -> PeriodicTimer:
        if not self._timer:
            raise RuntimeError(
                "Timer is not initialized. Did you forget to call setup()?"
            )

        return self._timer

    @timer.setter
    def timer(self, value):
        self._timer: PeriodicTimer | None = value


class PeriodicProcessAgent(PeriodicAgent[T], multiprocessing.Process, ABC):
    a_type: str = "process"

    def __init__(self, name: str, config: T, **kwargs):
        multiprocessing.Process.__init__(self, name=name)
        PeriodicAgent.__init__(
            self, name=name, config=config, a_type=self.a_type, **kwargs
        )


class PeriodicThreadAgent(PeriodicAgent[T], threading.Thread, ABC):
    a_type: str = "thread"

    def __init__(self, name: str, config: T, **kwargs):
        threading.Thread.__init__(self, name=name)
        PeriodicAgent.__init__(
            self, name=name, config=config, a_type=self.a_type, **kwargs
        )
