from typing import TypeVar, Generic
from logging import Logger

from framework.base_process.base import BaseProcess, Config, BaseConfig
from framework.child.utilities import CheckConfig


class ChildConfig(BaseConfig):
    """
    Configurazioni di un ChildProcess.

    Attributes:
        check_config (CheckConfig): Configurazioni thread di controllo del Master.
        logger (LoggerConfig): Configurazioni del `logger`.
    """

    check_config = CheckConfig()


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
        super().__init__(name=self.__class__.__name__, config=config)

    def work(self) -> None:
        """
        Metodo principale da implementare nelle sottoclassi.
        """
        raise NotImplementedError(
            f"La classe '{self.__class__.__name__}' deve implementare il metodo `work`."
        )
