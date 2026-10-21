"""
Configuración central del proyecto Radar de Riesgo Farmacéutico Perú-FDA.

Carga variables de entorno desde un archivo .env (si existe) mediante python-dotenv.
Los valores en .env sobreescriben los defaults aquí definidos.
"""
from __future__ import annotations
import os
import logging
from pathlib import Path

# Intentar cargar .env si existe (no falla si no está presente)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except ImportError:
    pass  # python-dotenv opcional en entornos CI

# ---------------------------------------------------------------------------
# Rutas base del proyecto
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Zona Cruda — Data Lake
DATA_DIR        = BASE_DIR / "data"
RAW_DATA_DIR    = DATA_DIR / "raw"
RAW_FAERS_DIR   = RAW_DATA_DIR / "faers"
RAW_DIGEMID_DIR = RAW_DATA_DIR / "digemid"
RAW_OPENFDA_DIR = RAW_DATA_DIR / "openfda"

# Zona Procesada — Data Warehouse
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Base de datos SQLite (sobreescribible vía variable de entorno)
_db_env = os.getenv("SQLITE_DB_PATH")
SQLITE_DB_PATH = Path(_db_env) if _db_env else PROCESSED_DATA_DIR / "radar_farmacovigilancia.db"

# ---------------------------------------------------------------------------
# Umbrales epidemiológicos estándar PRR/ROR (Evans et al. / FDA / WHO)
# ---------------------------------------------------------------------------
PRR_THRESHOLD_HIGH  = float(os.getenv("PRR_THRESHOLD_HIGH",  "2.0"))
PRR_THRESHOLD_MED   = float(os.getenv("PRR_THRESHOLD_MED",   "1.5"))
CHI2_THRESHOLD_HIGH = float(os.getenv("CHI2_THRESHOLD_HIGH", "4.0"))
CHI2_THRESHOLD_MED  = float(os.getenv("CHI2_THRESHOLD_MED",  "3.0"))
MIN_CASES_HIGH      = int(os.getenv("MIN_CASES_HIGH", "3"))
MIN_CASES_MED       = int(os.getenv("MIN_CASES_MED",  "2"))

# ---------------------------------------------------------------------------
# Endpoints oficiales de openFDA
# ---------------------------------------------------------------------------
OPENFDA_LABEL_URL       = "https://api.fda.gov/drug/label.json"
OPENFDA_ENFORCEMENT_URL = "https://api.fda.gov/drug/enforcement.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ---------------------------------------------------------------------------
# Inicialización: garantizar que los directorios de datos existan al importar
# ---------------------------------------------------------------------------
for _d in (RAW_FAERS_DIR, RAW_DIGEMID_DIR, RAW_OPENFDA_DIR, PROCESSED_DATA_DIR):
    _d.mkdir(parents=True, exist_ok=True)
