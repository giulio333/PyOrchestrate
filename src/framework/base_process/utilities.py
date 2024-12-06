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
        level (int): Livello di logging. Defaults to INFO.
        filename (str): Percorso del file di log. Defaults to "".
    """

    level: int = INFO
    """Livello di logging. Defaults to INFO."""
    filename: str = ""
    """Nome del file di log. Defaults to ""."""
    # format: str | None = None
    # datefmt: str | None = None
