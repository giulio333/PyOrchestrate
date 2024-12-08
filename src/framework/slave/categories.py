from framework.slave import SlaveProcess, SlaveConfig
from typing import TypeVar, Generic, final
from threading import Event
from time import sleep
from abc import abstractmethod

OneShotSlaveConfigType = TypeVar("OneShotSlaveConfigType", bound=SlaveConfig)


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


PeriodicSlaveConfigType = TypeVar("PeriodicSlaveConfigType", bound=SlaveConfig)


class PeriodicSlave(SlaveProcess[PeriodicSlaveConfigType]):
    """
    Theese processes are executed periodically.

    Usage:
        Override the `runner` method with the logic to be executed.

        When you want to terminate the process, call the `stop` method.
    """

    def __init__(self, config: PeriodicSlaveConfigType) -> None:
        super().__init__(config=config)
        self.interval = 1

    @final
    def work(self) -> None:

        self.stop_event = Event()

        self.logger.info(
            f"PeriodicSlave avviato con intervallo di {self.interval} secondi."
        )

        while not self.stop_event.is_set():
            self.runner()
            sleep(self.interval)

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
