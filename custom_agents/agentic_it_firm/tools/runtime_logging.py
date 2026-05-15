"""Runtime logging setup."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path


def configure_logging(log_dir: str | Path, level: int = logging.INFO) -> logging.Logger:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("agentic_it_firm")
    logger.setLevel(level)
    logger.propagate = True
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_handler = logging.FileHandler(log_path / f"{timestamp}-runtime.log", encoding="utf-8")
    file_handler.setLevel(level)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger
