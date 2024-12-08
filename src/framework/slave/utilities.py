from dataclasses import dataclass
from logging import INFO
import warnings


@dataclass
class CheckConfig:
    """
    Configurazioni thread di controllo del Master.

    Attributes:
        to_monitor (bool): Se True, verrà monitorato lo stato di salute del processo.
        autorestart (bool): Se True, il processo verrà riavviato in caso di errore o terminazione.
        interval (int): Intervallo di controllo in secondi.
    """

    to_monitor: bool = False
    """Se True, verrà monitorato lo stato di salute del processo."""

    autorestart: bool = False
    """Se True, il processo verrà riavviato in caso di errore o terminazione."""

    def __post_init__(self):

        if not self.to_monitor and self.autorestart:
            raise ValueError(
                "Non è possibile riavviare un processo non monitorato. Impostare `autorestart=False`."
            )
