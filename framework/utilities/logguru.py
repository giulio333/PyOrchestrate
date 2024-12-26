"""
Questo modulo definisce la classe `LoggerFactory`, che facilita la creazione e la gestione di logger personalizzati utilizzando Loguru.

**Loguru** è una libreria di logging per Python che semplifica notevolmente la gestione dei log. 
Uno dei concetti fondamentali in Loguru è il *sink*, che rappresenta una destinazione per i messaggi di log, come file, console o altri flussi. 
I sink permettono di definire dove e come i messaggi di log vengono emessi, supportando funzionalità come la rotazione dei file, 
la compressione, i filtri e la formattazione personalizzata.

La classe `LoggerFactory` utilizza questi concetti per:

- Rimuovere il logger predefinito e aggiungere un sink per la console con un formato specifico.
- Gestire sink file individuali per diversi identificatori di log, con meccanismi di rotazione e compressione.
- Fornire un metodo thread-safe per creare e recuperare logger configurati per diversi componenti dell'applicazione.
"""

from loguru import logger
import sys
from typing import Dict, Any, Optional
import threading
from time import sleep
from pathlib import Path


class LoggerFactory:
    """
    Factory per creare e gestire logger personalizzati utilizzando Loguru.

    Attributes:
        _sinks (Dict[str, int]): Mappa dei sink ID.
        _initialized (bool): Flag per indicare se il logger è stato inizializzato.
        _lock (threading.Lock): Lock per garantire l'accesso thread-safe ai sink.
        rotation_default (str): Frequenza di rotazione dei file di log di default.
        retention_default (str): Durata di retention dei file di log di default.
        compression_default (str): Tipo di compressione dei file di log di default.
        log_path_default (Path | str | None): Percorso di default in cui salvare i file di log.
    """

    _sinks: Dict[str, int] = {}
    _initialized: bool = False
    _lock = threading.Lock()

    prod_format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<level><cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan></level> - "
        "<level>{elapsed}</level> | "
        "{extra[name]} | "
        "<level>{message}</level>"
    )

    dev_format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "{extra[name]} | "
        "<level>{message}</level>"
    )

    rotation_default: str = "00:00"
    retention_default: str = "7 days"
    compression_default: str = "zip"
    log_path_default: Path | str | None = None

    @classmethod
    def set_defaults(
            cls,
            rotation: str | None = None,
            retention: str | None = None,
            compression: str | None = None,
            log_path: str | Path | None = None,
    ):
        """
        Imposta i valori di default per rotation, retention, compression e log_path.
        """
        if rotation is not None:
            cls.rotation_default = rotation
        if retention is not None:
            cls.retention_default = retention
        if compression is not None:
            cls.compression_default = compression
        if log_path is not None:
            cls.log_path_default = log_path

    @classmethod
    def create_logger(
            cls,
            log_identifier: str,
            logger_name: str,
            level: str = "INFO",
            rotation: str | None = None,
            retention: str | None = None,
            compression: str | None = None,
            log_path: str | Path | None = None,
    ):
        """
        Crea o restituisce un `logger` esistente.

        Args:
            log_identifier (str): Identificatore univoco per il logger (es. nome del `thread`).
            logger_name (str): Nome del logger, verrà incluso nel formato dei messaggi.
            level (str): Livello di log.
            rotation (str): Frequenza di rotazione dei file di log.
            retention (str): Durata di retention dei file di log.
            compression (str): Tipo di compressione dei file di log.
            log_path (str | Path): Percorso in cui salvare i file di log.
        Returns:
            Logger configurato.
        """

        with cls._lock:
            if not cls._initialized:
                # Rimuove il logger predefinito
                logger.remove()
                # Aggiunge un sink console
                logger.add(
                    sys.stderr,
                    format=cls.dev_format,
                    level=level,
                    colorize=True,
                    backtrace=True,
                    diagnose=True,
                )
                cls._initialized = True

            if log_identifier in cls._sinks:
                return logger.bind(file=log_identifier, name=logger_name)

            if log_path:
                file_name = Path(log_path) / f"{log_identifier}.log"
            elif cls.log_path_default:
                file_name = Path(cls.log_path_default) / f"{log_identifier}.log"
            else:
                logs_dir = Path(__file__).resolve().parent.parent / "logs"
                file_name = logs_dir / f"{log_identifier}.log"

            try:
                sink_id = logger.add(
                    file_name,
                    rotation=rotation or cls.rotation_default,
                    retention=retention or cls.retention_default,
                    compression=compression or cls.compression_default,
                    filter=lambda record: record["extra"].get("file") == log_identifier,
                    format=cls.dev_format,
                    level=level,
                )
                cls._sinks[log_identifier] = sink_id
            except Exception as e:
                logger.error(f"Failed to add sink for {log_identifier}: {e}")
                raise

            return logger.bind(
                file=log_identifier,
                name=logger_name,
                backtrace=True,
                diagnose=True,
            )

    @classmethod
    def close_all(cls) -> None:
        """
        Chiude tutti i `sink`.
        """
        with cls._lock:
            logger.remove()
            cls._sinks.clear()
            cls._initialized = False


# Esempio di utilizzo
def task(log_identifier: str, logger_name: str):
    path = Path(__file__).parent / "logs"

    # LoggerFactory.set_defaults(log_path=path)

    task_logger = LoggerFactory.create_logger(
        log_identifier, logger_name, log_path=path
    )

    while True:
        task_logger.info(f"Starting task {logger_name}")
        # Simulazione di operazioni
        task_logger.success(f"End of task {logger_name}")
        sleep(1)


if __name__ == "__main__":
    # Esegui i thread di esempio
    main_thread = threading.Thread(target=task, args=("Engine", "Engine"))
    thread1 = threading.Thread(target=task, args=("Worker1", "Worker1"))
    thread2 = threading.Thread(target=task, args=("Worker2", "Worker2"))

    main_thread.start()
    thread1.start()
    thread2.start()

    main_thread.join()
    thread1.join()
    thread2.join()

    # Chiude tutti i sink prima della chiusura dell'applicazione
    LoggerFactory.close_all()
