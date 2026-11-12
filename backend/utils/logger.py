# logger.py
# Purpose: one shared logging setup for the whole backend.
# Logs go to a FILE, so technical details stay with the developer
# and are never shown to the chat user.

import logging
import os

UTILS_FOLDER = os.path.dirname(os.path.abspath(__file__))
BACKEND_FOLDER = os.path.dirname(UTILS_FOLDER)
LOG_FOLDER = os.path.join(BACKEND_FOLDER, "logs")
LOG_FILE_PATH = os.path.join(LOG_FOLDER, "app.log")


def get_logger(logger_name):
    """Return a logger with the given name (call once per file)."""
    logger = logging.getLogger(logger_name)

    # Already set up? Return it, to avoid duplicate log lines.
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    os.makedirs(LOG_FOLDER, exist_ok=True)

    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger