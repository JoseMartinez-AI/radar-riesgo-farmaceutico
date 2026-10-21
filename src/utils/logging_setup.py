"""
Configuración centralizada de logging para el proyecto.

Uso:
    from src.utils.logging_setup import setup_logging, get_logger

    setup_logging()                       # configura el logger raíz
    logger = get_logger(__name__)         # logger del módulo actual
"""
from __future__ import annotations
import logging
import sys
from typing import Optional


_FMT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: Optional[str] = None,
    stream=None,
) -> None:
    """
    Configura el logger raíz de la aplicación.

    Args:
        level: Nivel de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR').
               Si es None, se lee de ``src.config.LOG_LEVEL`` (por defecto 'INFO').
        stream: Stream de salida (por defecto sys.stdout).
    """
    from src.config import LOG_LEVEL as _default_level

    effective_level = (level or _default_level).upper()
    logging.basicConfig(
        level=effective_level,
        stream=stream or sys.stdout,
        format=_FMT,
        datefmt=_DATE_FMT,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Retorna un logger con el nombre indicado."""
    return logging.getLogger(name)
