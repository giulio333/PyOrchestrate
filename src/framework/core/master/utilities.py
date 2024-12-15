from dataclasses import dataclass
from logging import INFO
import warnings


@dataclass
class HealthCheckConfig:
    """
    Configurazione per il monitoraggio dello stato di salute.

    Attributes:
        enabled (bool): Abilita o disabilita il monitoraggio dello stato di salute.
        check_interval (int): Intervallo in secondi tra un controllo e l'altro.
    """

    enabled: bool = False
    check_interval: int = 2
