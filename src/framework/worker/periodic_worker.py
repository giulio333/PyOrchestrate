from typing import Type, TypeVar, Generic, final
from threading import Event
import time
from abc import abstractmethod

from framework.base_process.base import BaseConfig
from framework.worker import (
    WorkerThread,
    WorkerConfig,
    LoopingWorkerConfig,
    LoopingWorker,
)
from framework.base_process.exceptions import TerminateProcess
from framework.utilities.periodic_timer import PeriodicTimer


class PeriodicWorkerConfig(LoopingWorkerConfig):
    """
    PeriodicSlave configuration.

    Attributes:
        interval (int): Interval in seconds between each execution
        compensate_delay (bool): If True, the process will try to compensate the delay between the executions
        check_config (CheckConfig): Configurazioni thread di controllo del Master.
        logger (LoggerConfig): Configurazioni del `logger`.

    Methods:
        validate: Metodo per validare i parametri di configurazione.
    """

    interval: float = 5
    """Interval in seconds between each execution"""
    compensate_delay: bool = True
    """If True, the process will try to compensate the delay between the executions"""


PeriodicWorkerConfigType = TypeVar(
    "PeriodicWorkerConfigType", bound=PeriodicWorkerConfig
)


class PeriodicWorker(LoopingWorker[PeriodicWorkerConfigType]):
    """
    Theese processes are executed periodically.

    Usage:
        Override the `setup` and `runner` method with the logic to be executed.
        First the `setup` method is called (only once) and then the `runner` method will be called periodically.

        When you want to terminate the process, call the `stop` method or raise `TerminateProcess`.
    """

    def __init__(self, config: PeriodicWorkerConfigType) -> None:
        super().__init__(config=config)

        self.interval: float = config.interval
        self.compensate_delay: bool = config.compensate_delay

    def setup(self):

        self.timer = PeriodicTimer(
            logger=self.logger,
            interval=self.interval,
            compensate_delay=self.compensate_delay,
        )

    @final
    def cycle(self) -> None:

        try:
            self.runner()
        except TerminateProcess as e:
            raise e

        if self.timer.wait(self.stop_event):
            # stopping the process
            return

    @final
    def stop(self):
        """
        Stops the process.
        """
        self.stop_event.set()

    @abstractmethod
    def runner(self):
        """
        Here you have to implement the logic to be executed periodically.
        """
        pass

    def check_worker_config(
        self, config_class: type[BaseConfig] = PeriodicWorkerConfig
    ):
        return super().check_worker_config(config_class)
