from framework.base import BaseProcess, Config
from typing import TypeVar, Generic
from logging import Logger


class ChildProcess(BaseProcess[Config]):
    """
    Classe base ChildProcess.

    Il metodo `work` deve essere implementato nelle sottoclassi per definire il lavoro da svolgere.

    Attributes:
        name (str): Nome del processo.
        config (Config): Configurazioni del processo.
    """

    def __init__(self, name: str, config: Config) -> None:
        """
        Inizializza un'istanza di ChildProcess.

        Args:
            name (str): Nome del processo.
            config (Config): Configurazioni del processo.
        """
        super().__init__(name, config)

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )
