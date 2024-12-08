from typing import TypeVar, Generic, final
from threading import Event
from time import sleep
from abc import abstractmethod

from framework.slave import SlaveProcess, SlaveConfig
from framework.base_process.exceptions import TerminateProcess


class OneShotSlaveConfig(SlaveConfig):
    pass


OneShotSlaveConfigType = TypeVar("OneShotSlaveConfigType", bound=OneShotSlaveConfig)


class OneShotSlaveProcess(
    SlaveProcess[OneShotSlaveConfigType], Generic[OneShotSlaveConfigType]
):
    """
    Theese processes are executed only once.

    Usage:
        Override the `work` method with the logic to be executed.
    """

    def __init__(self, config: OneShotSlaveConfigType) -> None:
        super().__init__(config=config)

    @abstractmethod
    def work(self) -> None:
        """
        Here you have to implement the logic to be executed only once.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )


class PeriodicSlaveConfig(SlaveConfig):
    """
    PeriodicSlave configuration.

    Attributes:
        interval (int): Interval in seconds between each execution
    """

    interval: float = 5
    """Interval in seconds between each execution"""


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
        self.interval = config.interval

    @final
    def work(self) -> None:
        self.stop_event = Event()

        self.logger.info(
            f"PeriodicSlave avviato con intervallo di {self.interval} secondi."
        )

        try:

            self.setup()

        except Exception as e:
            self.logger.exception(f"Error during setup: {e}")
            self.stop_event.set()

        while not self.stop_event.is_set():

            try:

                self.runner()

            except TerminateProcess as e:
                raise e

            except Exception as e:
                self.logger.exception(f"Error during runner: {e}")
                self.stop_event.set()
                break

            if self.stop_event.wait(timeout=self.interval):
                self.logger.info("Evento di stop rilevato. Terminazione del ciclo.")
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
