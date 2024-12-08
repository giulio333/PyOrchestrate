from typing import Type, TypeVar, Generic, final
from threading import Event
import time
from abc import abstractmethod

from framework.base_process.base import BaseConfig
from framework.slave import SlaveProcess, SlaveConfig
from framework.base_process.exceptions import TerminateProcess
from framework.utilities.periodic_timer import PeriodicTimer


class PeriodicSlaveConfig(SlaveConfig):
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


PeriodicSlaveConfigType = TypeVar("PeriodicSlaveConfigType", bound=PeriodicSlaveConfig)


class PeriodicSlave(SlaveProcess[PeriodicSlaveConfigType]):
    """
    Theese processes are executed periodically.

    Usage:
        Override the `setup` and `runner` method with the logic to be executed.
        First the `setup` method is called (only once) and then the `runner` method will be called periodically.


        When you want to terminate the process, call the `stop` method or raise `TerminateProcess`.
    """

    def __init__(self, config: PeriodicSlaveConfigType) -> None:
        super().__init__(config=config)

        self.interval: float = config.interval
        self.compensate_delay: bool = config.compensate_delay

    @final
    def work(self) -> None:

        self.stop_event = Event()

        self.timer = PeriodicTimer(
            logger=self.logger,
            interval=self.interval,
            compensate_delay=self.compensate_delay,
        )

        self.logger.info(
            f"PeriodicSlave avviato con intervallo di {self.interval} secondi."
        )

        self.setup()

        while not self.stop_event.is_set():

            try:
                self.runner()
            except TerminateProcess as e:
                raise e

            if self.timer.wait(self.stop_event):
                # stopping the process
                break

    @final
    def stop(self):
        """
        Stops the process.
        """
        self.stop_event.set()

    @abstractmethod
    def setup(self):
        """
        Here you can implement the setup logic.

        This method is called once before the runner loop method.
        """
        pass

    @abstractmethod
    def runner(self):
        """
        Here you have to implement the logic to be executed periodically.
        """
        pass

    def check_process_config(
        self, config_class: type[BaseConfig] = PeriodicSlaveConfig
    ):
        return super().check_process_config(config_class)
