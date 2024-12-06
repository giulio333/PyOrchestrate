from dataclasses import dataclass
from logging import INFO
import warnings


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
