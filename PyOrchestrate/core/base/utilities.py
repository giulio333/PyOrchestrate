from dataclasses import dataclass
from typing import Literal


@dataclass
class LoggerConfig:
    """
    Logger configuration class.

    If not specified, default values will be used.

    Notes:
        If not specified, the log file will be named like the Agent.

    Attributes:
        level (int): Logging level. Defaults to DEBUG.
        filename (str): File name for logging. Defaults to empty string.
    """

    level: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    """
    Logging level. Defaults to DEBUG.
    """

    filename: str = ""
    """
    Log file name. Defaults to empty string.

    If not specified, the log file will be named like the Agent.
    """
