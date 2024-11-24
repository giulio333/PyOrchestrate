from framework.base import BaseProcess, TConfig
from typing import TypeVar, Generic
from logging import Logger

class ChildProcess(BaseProcess[TConfig]):
    """
    Classe base ChildProcess.

    Il metodo `work` deve essere implementato nelle sottoclassi per definire il lavoro da svolgere.

    Attributes:
    name (str): Nome del processo.
    config (TConfig): Configurazioni del processo.
    logger (Logger): Logger del processo.
    """

    def __init__(self, name: str, config: TConfig) -> None:
        """
        Inizializza un'istanza di ChildProcess.

        Args:
        name (str): Nome del processo.
        config (TConfig): Configurazioni del processo.
        """
        super().__init__(name, config)

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )
