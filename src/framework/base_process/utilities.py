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
