import logging
from logging.handlers import RotatingFileHandler
from colorama import init as colorama_init
import os
from ..settings import LOG_FOLDER

# Inizializza colorama per garantire la compatibilità dei colori su Windows
colorama_init(autoreset=True)

# Crea la cartella dei log se non esiste
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)


class ColoredFormatter(logging.Formatter):
    """
    Formatter che aggiunge colori ai messaggi di log in base al livello.
    """

    # Definizione dei codici di colore ANSI
    COLOR_CODES = {
        logging.DEBUG: "\033[34m",  # Blu
        logging.INFO: "\033[32m",  # Verde
        logging.WARNING: "\033[33m",  # Giallo
        logging.ERROR: "\033[31m",  # Rosso
        logging.CRITICAL: "\033[41m",  # Sfondo Rosso
    }
    RESET_CODE = "\033[0m"

    def format(self, record):
        color_code = self.COLOR_CODES.get(record.levelno, self.RESET_CODE)
        formatted = super().format(record)
        return f"{color_code}{formatted}{self.RESET_CODE}"


def setup_logger(name: str, log_file: str = "framework.log", level: int = logging.INFO):
    """
    Configura un logger con rotazione automatica dei file e output colorato sulla console.

    :param name: Nome del logger.
    :param log_file: Percorso del file di log.
    :param level: Livello di logging.
    :return: Logger configurato.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Verifica se il logger ha già degli handler configurati
    if not logger.hasHandlers():
        # Formatter standard per i file di log
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Formatter colorato per la console
        console_formatter = ColoredFormatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Handler per la console con il formatter colorato
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)

        # Handler per il file con il formatter standard e rotazione
        log_file_path = os.path.join(LOG_FOLDER, log_file)
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=1_000_000, backupCount=3
        )
        file_handler.setFormatter(file_formatter)

        # Aggiunta degli handler al logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# Esempio di utilizzo
if __name__ == "__main__":
    logger = setup_logger("Launcher")

    logger.debug("Questo è un messaggio di debug.")
    logger.info("Health_check...")
    logger.warning("Questo è un messaggio di avviso.")
    logger.error("Questo è un messaggio di errore.")
    logger.critical("Questo è un messaggio critico.")
