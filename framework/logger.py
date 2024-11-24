import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, log_file: str = "framework.log", level: int = logging.INFO):
    """
    Configura un logger con rotazione automatica dei file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Formatter per messaggi di log
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler per la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Handler per il file (con rotazione)
    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)

    # Aggiunta degli handler al logger
    if not logger.hasHandlers():
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
