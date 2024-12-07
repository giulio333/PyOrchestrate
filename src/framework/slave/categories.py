from framework.slave import SlaveProcess, SlaveConfig
from typing import TypeVar, Generic
from threading import Event
from time import sleep

OneShotSlaveConfigType = TypeVar("OneShotSlaveConfigType", bound=SlaveConfig)


class OneShotSlaveProcess(
    SlaveProcess[OneShotSlaveConfigType], Generic[OneShotSlaveConfigType]
):
    """
    Classe base per tutti gli Slave che eseguono un'unica operazione e poi terminano.
    """

    def __init__(self, config: OneShotSlaveConfigType) -> None:
        super().__init__(config=config)

    def work(self) -> None:
        """
        Metodo principale eseguito nel processo.
        Deve essere implementato nelle sottoclassi.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )


PeriodicSlaveConfigType = TypeVar("PeriodicSlaveConfigType", bound=SlaveConfig)


class PeriodicSlave(SlaveProcess[PeriodicSlaveConfigType]):
    def __init__(self, config: PeriodicSlaveConfigType) -> None:
        super().__init__(config=config)
        self.interval = 1

    def work(self) -> None:

        self.stop_event = Event()

        self.logger.info(
            f"PeriodicSlave avviato con intervallo di {self.interval} secondi."
        )

        while not self.stop_event.is_set():
            self.runner()
            sleep(self.interval)

    def runner(self):
        """
        Implementa qui la logica che deve essere eseguita periodicamente.
        """
        self.logger.info("Esecuzione del task periodico.")
