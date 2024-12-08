from typing import TypeVar, Generic
from logging import Logger

from framework.slave.slave import SlaveProcess, SlaveConfig


class PeriodicSlaveConfig(SlaveConfig):
    interval: float = 5.0  # Intervallo in secondi tra le esecuzioni


PeriodicSlaveConfigType = TypeVar("PeriodicSlaveConfigType", bound=PeriodicSlaveConfig)


class PeriodicSlaveProcess(
    SlaveProcess[PeriodicSlaveConfigType], Generic[PeriodicSlaveConfigType]
):
    """
    Classe base PeriodicSlaveProcess.

    Il metodo `work` deve essere implementato nelle sottoclassi per definire il lavoro da svolgere.

    Attributes:
        name (str): Nome del processo.
        config (Config): Configurazioni del processo.
    """

    def __init__(self, config: PeriodicSlaveConfigType, *args, **kwargs) -> None:
        """
        Inizializza un'istanza di PeriodicSlaveProcess.

        Args:
            name (str): Nome del processo.
            config (Config): Configurazioni del processo.
        """
        super().__init__(name=self.__class__.__name__, config=config)

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )
