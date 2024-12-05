from dataclasses import dataclass


@dataclass
class LoggerConfig:
    """
    Configurazione per il logger.
    """

    level: int | None = None
    filename: str | None = None
    # format: str | None = None
    # datefmt: str | None = None
