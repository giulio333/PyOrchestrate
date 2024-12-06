from dataclasses import dataclass
from logging import INFO
import warnings


@dataclass
class LoggerConfig:
    """
    Configurazione per il logger.

    Gli attributi sono impostati a `None`.
    Se non vengono specificati, verranno utilizzati i valori di default.

    Attributes:
        level (int): Livello di log.
        filename (str): Nome del file di log. Lasciare vuoto per utilizzare il nome del processo.
    """

    level: int = INFO
    filename: str = ""
    # format: str | None = None
    # datefmt: str | None = None


@dataclass
class CheckConfig:
    """
    Configurazioni thread di controllo del Master.

    Attributes:
        to_monitor (bool): Se True, verrà monitorato lo stato di salute del processo.
        autorestart (bool): Se True, il processo verrà riavviato in caso di errore.
        interval (int): Intervallo di controllo in secondi.
    """

    to_monitor: bool = True
    """Se True, verrà monitorato lo stato di salute del processo."""

    autorestart: bool = True
    """Se True, il processo verrà riavviato in caso di errore."""

    interval: int = 5
    """Intervallo di controllo in secondi."""

    def __post_init__(self):

        if not self.to_monitor and self.autorestart:
            raise ValueError(
                "Non è possibile riavviare un processo non monitorato. Impostare `autorestart=False`."
            )
