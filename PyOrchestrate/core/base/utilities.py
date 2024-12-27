from dataclasses import dataclass


@dataclass
class LoggerConfig:
    """
    Process logger configurations.

    If not specified, default values will be used.

    Notes:
        If not specified, the log file will be named like the Agent.

    Attributes:
        level (int): Logging level. Defaults to DEBUG.
        filename (str): File name for logging. Defaults to empty string.
    """

    level: str = "DEBUG"
    """
    Logging level. Defaults to DEBUG.
    """

    filename: str = ""
    """
    Log file name. Defaults to empty string.

    If not specified, the log file will be named like the Agent.
    """
