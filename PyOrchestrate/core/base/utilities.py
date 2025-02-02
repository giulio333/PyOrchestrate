from dataclasses import dataclass
from typing import Literal


@dataclass
class LoggerConfig:
    """
    Logger configuration class.

    This class defines the configuration settings for the logger component.

    Notes:
        - If not specified, default values will be used.
        - If not specified, the log file will be named like the Agent.

    Attributes:
        level (int): Logging level. Defaults to DEBUG.
        filename (str): File name for logging. Defaults to empty string.
    """

    level: Literal[
        "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
    ] = "DEBUG"
    """
    Logging level. Defaults to DEBUG.
    """

    filename: str = ""
    """
    Log file name. Defaults to empty string.

    If not specified, the log file will be named like the Agent.
    """
