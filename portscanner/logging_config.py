"""Central logging configuration for the port scanner application."""

from __future__ import annotations

import logging

from portscanner.config import (
    LOG_DATE_FORMAT,
    LOG_FILE_ENCODING,
    LOG_FILE_PATH,
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_ROOT_LOGGER_NAME,
    LOG_DIRECTORY,
)


def setup_logging() -> logging.Logger:
    """Configure application logging and return the root package logger."""
    logger = logging.getLogger(LOG_ROOT_LOGGER_NAME)

    if logger.handlers:
        return logger

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding=LOG_FILE_ENCODING)
    file_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    file_handler.setFormatter(
        logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    )

    logger.addHandler(file_handler)
    logger.propagate = False

    return logger


def get_logger(module: str) -> logging.Logger:
    """Return a namespaced logger for *module* under the application root."""
    return logging.getLogger(f"{LOG_ROOT_LOGGER_NAME}.{module}")
