"""
Esquema dimensional en estrella (Data Warehouse) en SQLite.
Tablas: dim_farmaco, dim_reaccion, dim_regulacion_peru, dim_tiempo,
        fact_senales_riesgo, fact_evidencia_texto.
"""
from sqlalchemy import create_engine, text
from src.config import SQLITE_DB_PATH
import logging

logger = logging.getLogger(__name__)

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS dim_farmaco (
        farmaco_id                INTEGER PRIMARY KEY AUTOINCREMENT,
        principio_activo          TEXT UNIQUE NOT NULL,
        codigo_atc                TEXT,
        nombres_comerciales_comunes TEXT,
        fecha_registro            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_reaccion (
        reaccion_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        termino_preferido TEXT UNIQUE NOT NULL,
        sistema_organico  TEXT,
        es_grave          INTEGER DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_regulacion_peru (
        regulacion_id              INTEGER PRIMARY KEY AUTOINCREMENT,
        principio_activo           TEXT UNIQUE NOT NULL,
        registro_sanitario_vigente INTEGER DEFAULT 0,
        incluido_pnume             INTEGER DEFAULT 0,
        estado_alerta_digemid      TEXT    DEFAULT 'Normal',
        fecha_actualizacion        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_tiempo (
        tiempo_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        anio             INTEGER NOT NULL,
        trimestre        TEXT    NOT NULL,
        periodo_etiqueta TEXT    UNIQUE NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_senales_riesgo (
        senal_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        farmaco_id  INTEGER NOT NULL,
        reaccion_id INTEGER NOT NULL,
        tiempo_id   INTEGER NOT NULL,
        casos_farmaco_reaccion          INTEGER NOT NULL,
        casos_farmaco_otras_reac        INTEGER NOT NULL,
        casos_otros_farmacos_reac       INTEGER NOT NULL,
        casos_otros_farmacos_otras_reac INTEGER NOT NULL,
        total_reportes_graves           INTEGER DEFAULT 0,
        prr          REAL NOT NULL,
        ror          REAL,
        chi_cuadrado REAL,
        nivel_riesgo TEXT NOT NULL,
        UNIQUE(farmaco_id, reaccion_id, tiempo_id),
        FOREIGN KEY (farmaco_id)  REFERENCES dim_farmaco(farmaco_id),
        FOREIGN KEY (reaccion_id) REFERENCES dim_reaccion(reaccion_id),
        FOREIGN KEY (tiempo_id)   REFERENCES dim_tiempo(tiempo_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_evidencia_texto (
        evidencia_id               INTEGER PRIMARY KEY AUTOINCREMENT,
        farmaco_id                 INTEGER NOT NULL,
        fuente                     TEXT NOT NULL,
        tipo_seccion               TEXT,
        contenido_extraido         TEXT NOT NULL,
        sentimiento_riesgo         REAL,
        terminos_criticos_detectados TEXT,
        fecha_publicacion          DATE,
        FOREIGN KEY (farmaco_id) REFERENCES dim_farmaco(farmaco_id)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_senales_farmaco   ON fact_senales_riesgo(farmaco_id);",
    "CREATE INDEX IF NOT EXISTS idx_senales_riesgo    ON fact_senales_riesgo(nivel_riesgo);",
    "CREATE INDEX IF NOT EXISTS idx_evidencia_farmaco ON fact_evidencia_texto(farmaco_id);",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_senales_farmaco_reac_tiempo ON fact_senales_riesgo(farmaco_id, reaccion_id, tiempo_id);",
]


def get_engine(db_path=SQLITE_DB_PATH):
    """Devuelve un engine SQLAlchemy reutilizable."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_database(db_path=SQLITE_DB_PATH):
    """Crea las tablas del Data Warehouse si no existen. Retorna el engine."""
    engine = get_engine(db_path)
    with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            conn.execute(text(stmt))
    logger.info("Data Warehouse inicializado: %s", db_path)
    return engine


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
