"""
This module defines the `LoggerFactory` class, which creates and manages
custom loggers built on Loguru.

**Loguru** is a Python logging library that considerably simplifies log
handling. One of its core concepts is the *sink*, a destination for log
messages such as a file, the console or another stream. Sinks define where and
how messages are emitted, and support features like file rotation,
compression, filters and custom formatting.

`LoggerFactory` uses those concepts to:

- Remove the default logger and add a console sink with a specific format.
- Manage individual file sinks per log identifier, with rotation and
  compression.
- Provide a thread-safe way to create and retrieve loggers configured for the
  different components of an application.
"""

from loguru import logger
import sys
from typing import Dict
import threading
from pathlib import Path


class LoggerFactory:
    """
    Factory that creates and manages custom loggers using Loguru.

    Attributes:
        _sinks (Dict[str, int]): Map of sink IDs.
        _initialized (bool): Whether the logger has been initialized.
        _lock (threading.Lock): Lock guaranteeing thread-safe access to sinks.
        rotation_default (str): Default rotation frequency for log files.
        retention_default (str): Default retention period for log files.
        compression_default (str): Default compression type for log files.
        log_path_default (Path | str | None): Default directory for log files.
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
        Sets the default values for rotation, retention, compression and log_path.
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
        Creates a new `logger`, or returns an existing one.

        Args:
            log_identifier (str): Unique identifier for the logger (for example
                the `thread` name).
            logger_name (str): Logger name, included in the message format.
            level (str): Log level.
            rotation (str): Rotation frequency for log files.
            retention (str): Retention period for log files.
            compression (str): Compression type for log files.
            log_path (str | Path): Directory where log files are written.

        Returns:
            The configured logger.
        """

        with cls._lock:
            if not cls._initialized:
                # Drop the default logger
                logger.remove()
                # Add a console sink
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
                logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
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
        Closes every `sink`.
        """
        with cls._lock:
            logger.remove()
            cls._sinks.clear()
            cls._initialized = False
