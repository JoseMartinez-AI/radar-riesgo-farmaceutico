"""
Configuracion central del proyecto Radar de Riesgo Farmaceutico Peru-FDA.
"""
from pathlib import Path

# Raiz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas de Almacenamiento (Data Lake / Data Warehouse)
DATA_DIR = BASE_DIR / "data"

# Zona Cruda (Data Lake)
RAW_DATA_DIR    = DATA_DIR / "raw"
RAW_FAERS_DIR   = RAW_DATA_DIR / "faers"
RAW_DIGEMID_DIR = RAW_DATA_DIR / "digemid"
RAW_OPENFDA_DIR = RAW_DATA_DIR / "openfda"

# Zona Procesada / Curada (Data Warehouse)
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SQLITE_DB_PATH     = PROCESSED_DATA_DIR / "radar_farmacovigilancia.db"

# Umbrales epidemiologicos estandar PRR/ROR (Evans et al. / FDA / WHO)
PRR_THRESHOLD_HIGH  = 2.0
PRR_THRESHOLD_MED   = 1.5
CHI2_THRESHOLD_HIGH = 4.0
CHI2_THRESHOLD_MED  = 3.0
MIN_CASES_HIGH      = 3
MIN_CASES_MED       = 2

# Endpoints oficiales de openFDA
OPENFDA_LABEL_URL       = "https://api.fda.gov/drug/label.json"
OPENFDA_ENFORCEMENT_URL = "https://api.fda.gov/drug/enforcement.json"

# Asegurar directorios de datos al importar
for _dir in [
    RAW_FAERS_DIR, RAW_DIGEMID_DIR, RAW_OPENFDA_DIR,
    PROCESSED_DATA_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)
