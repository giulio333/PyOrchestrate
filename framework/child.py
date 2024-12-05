from framework.base import BaseProcess, Config, BaseConfig
from typing import TypeVar, Generic
from logging import Logger


class ChildConfig(BaseConfig):
    """
    Configurazioni di un ChildProcess.

    Attributes:
        autorestart (bool): Flag per abilitare il riavvio del processo in caso di errore.
        to_monitor (bool): Flag per abilitare il monitoraggio dello stato di salute del processo.
        logger (LoggerConfig): Configurazioni del `logger`.
    """

    to_monitor: bool = False
    """Se True, verrà monitorato lo stato di salute del processo."""
    autorestart: bool = False
    """Se True, il processo verrà riavviato in caso di errore."""


ChildConfigType = TypeVar("ChildConfigType", bound=ChildConfig)


class ChildProcess(BaseProcess[ChildConfigType], Generic[ChildConfigType]):
    """
    Classe base ChildProcess.

    Il metodo `work` deve essere implementato nelle sottoclassi per definire il lavoro da svolgere.

    Attributes:
        name (str): Nome del processo.
        config (Config): Configurazioni del processo.
    """

    def __init__(
        self,
        config: ChildConfigType,
    ) -> None:
        """
        Inizializza un'istanza di ChildProcess.

        Args:
            name (str): Nome del processo.
            config (Config): Configurazioni del processo.
        """
        super().__init__(config)

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )
