"""
Subpaquete de base de datos y esquema dimensional (Data Warehouse).

Exporta las funciones más usadas para simplicidad de importación:
    from src.database import get_engine, init_database
"""
from src.database.schema import get_engine, init_database

__all__ = ["get_engine", "init_database"]
