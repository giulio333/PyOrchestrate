from dataclasses import dataclass
from logging import INFO
import warnings


@dataclass
class LoggerConfig:
    """
    Process logger configurations.

    If not specified, default values will be used.

    Attributes:
        level (int): Logging level. Defaults to INFO.
        filename (str): File name for logging. Defaults to empty string.
    """

    level: str = "INFO"
    """
    Livello di logging. Defaults to INFO.
    """

    filename: str = ""
    """
    Nome del file di log. Defaults to empty string.

    Se non specificato, verrà utilizzato il nome del processo.
    """
