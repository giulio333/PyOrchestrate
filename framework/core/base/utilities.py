from dataclasses import dataclass
from logging import INFO
import warnings


@dataclass
class LoggerConfig:
    """
    Process logger configurations.

    If not specified, default values will be used.

    Notes:
        If not specified, the log file will be named like the agent.

    Attributes:
        level (int): Logging level. Defaults to DEBUG.
        filename (str): File name for logging. Defaults to empty string.
    """

    level: str = "DEBUG"
    """
    Livello di logging. Defaults to DEBUG.
    """

    filename: str = ""
    """
    Nome del file di log. Defaults to empty string.

    Se non specificato, verrà utilizzato il nome del processo.
    """
