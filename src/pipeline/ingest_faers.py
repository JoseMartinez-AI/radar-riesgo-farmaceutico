"""
Modulo de ingesta de archivos ASCII trimestrales de FAERS.
Flujo: descomprimir ZIP -> leer tablas -> deduplicar -> calcular contingencia -> insertar DW.
"""
from __future__ import annotations
import zipfile
import logging
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd
from sqlalchemy import text

from src.config import RAW_FAERS_DIR
from src.database.schema import get_engine, init_database
from src.mining.disproportionality import compute_signal_metrics

logger = logging.getLogger(__name__)

FAERS_DELIMITER = "$"
FAERS_ENCODING  = "latin-1"


def extract_zip(zip_path: Path, target_dir: Path) -> Path:
    """Descomprime un ZIP trimestral de FAERS."""
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(target_dir)
    logger.info("ZIP extraido en: %s", target_dir)
    return target_dir


def read_faers_table(folder: Path, table_name: str) -> pd.DataFrame:
    """Lee una tabla FAERS desde la carpeta extraida."""
    for ext in (".txt", ".TXT"):
        candidates = list(folder.rglob(f"{table_name}{ext}"))
        if candidates:
            df = pd.read_csv(
                candidates[0], delimiter=FAERS_DELIMITER,
                encoding=FAERS_ENCODING, low_memory=False, on_bad_lines="skip",
            )
            df.columns = df.columns.str.lower().str.strip()
            logger.info("Leido %s: %d filas", table_name, len(df))
            return df
    logger.warning("Tabla %s no encontrada en %s", table_name, folder)
    return pd.DataFrame()


def deduplicate_faers(demo: pd.DataFrame) -> pd.DataFrame:
    """Retiene el primaryid mas reciente por caseid (criterio FDA)."""
    if demo.empty or "caseid" not in demo.columns:
        return demo
    demo = demo.copy()
    if "fda_dt" in demo.columns:
        demo["fda_dt"] = pd.to_numeric(demo["fda_dt"], errors="coerce")
        demo = demo.sort_values("fda_dt", ascending=False)
    return demo.drop_duplicates(subset=["caseid"], keep="first").reset_index(drop=True)


def normalize_drug_name(name: str) -> str:
    """Normaliza nombre de farmaco a mayusculas."""
    return name.strip().upper() if isinstance(name, str) else ""


def build_contingency_table(
    drug: pd.DataFrame, reac: pd.DataFrame,
    target_drug: str, target_reaction: str,
) -> dict:
    """Construye la tabla 2x2 para el par (farmaco, reaccion)."""
    if drug.empty or reac.empty:
        return {"a": 0, "b": 0, "c": 0, "d": 0}
    target_drug = normalize_drug_name(target_drug)
    target_reaction = target_reaction.strip().upper()
    drug_norm = drug.copy()
    drug_norm["drugname"] = drug_norm["drugname"].apply(normalize_drug_name)
    reac_norm = reac.copy()
    reac_norm["pt"] = reac_norm["pt"].str.strip().str.upper()
    with_drug = set(drug_norm[drug_norm["drugname"] == target_drug]["primaryid"].unique())
    with_reac = set(reac_norm[reac_norm["pt"] == target_reaction]["primaryid"].unique())
    all_cases = set(drug_norm["primaryid"].unique())
    a = len(with_drug & with_reac)
    b = len(with_drug - with_reac)
    c = len((all_cases - with_drug) & with_reac)
    d = len((all_cases - with_drug) - with_reac)
    return {"a": a, "b": b, "c": c, "d": d}


def ingest_faers_quarter(
    zip_path: Path,
    anio: int,
    trimestre: str,
    target_pairs: List[Tuple[str, str]],
    db_path: Optional[Path] = None,
) -> None:
    """Pipeline completo de ingesta de un trimestre FAERS."""
    from src.config import SQLITE_DB_PATH as default_db
    path = db_path or default_db
    engine = init_database(path)
    periodo = f"{anio}-{trimestre}"
    folder = RAW_FAERS_DIR / periodo
    extract_zip(zip_path, folder)
    demo = deduplicate_faers(read_faers_table(folder, "DEMO"))
    drug = read_faers_table(folder, "DRUG")
    reac = read_faers_table(folder, "REAC")
    with engine.begin() as conn:
        conn.execute(
            text("INSERT OR IGNORE INTO dim_tiempo (anio, trimestre, periodo_etiqueta) VALUES (:a,:t,:p)"),
            {"a": anio, "t": trimestre, "p": periodo},
        )
        t_id = conn.execute(
            text("SELECT tiempo_id FROM dim_tiempo WHERE periodo_etiqueta=:p"), {"p": periodo}
        ).scalar()
        for drug_name, reac_name in target_pairs:
            ct = build_contingency_table(drug, reac, drug_name, reac_name)
            if ct["a"] == 0:
                continue
            metrics = compute_signal_metrics(ct["a"], ct["b"], ct["c"], ct["d"])
            conn.execute(text("INSERT OR IGNORE INTO dim_farmaco (principio_activo) VALUES (:pa)"), {"pa": drug_name})
            f_id = conn.execute(text("SELECT farmaco_id FROM dim_farmaco WHERE principio_activo=:pa"), {"pa": drug_name}).scalar()
            conn.execute(text("INSERT OR IGNORE INTO dim_reaccion (termino_preferido) VALUES (:pt)"), {"pt": reac_name})
            r_id = conn.execute(text("SELECT reaccion_id FROM dim_reaccion WHERE termino_preferido=:pt"), {"pt": reac_name}).scalar()
            conn.execute(
                text("INSERT OR REPLACE INTO fact_senales_riesgo "
                     "(farmaco_id,reaccion_id,tiempo_id,casos_farmaco_reaccion,casos_farmaco_otras_reac,"
                     "casos_otros_farmacos_reac,casos_otros_farmacos_otras_reac,total_reportes_graves,"
                     "prr,ror,chi_cuadrado,nivel_riesgo) "
                     "VALUES (:f,:r,:t,:a,:b,:c,:d,0,:prr,:ror,:chi2,:nivel)"),
                {"f":f_id,"r":r_id,"t":t_id,"a":ct["a"],"b":ct["b"],"c":ct["c"],"d":ct["d"],
                 "prr":metrics["prr"],"ror":metrics["ror"],"chi2":metrics["chi_cuadrado"],"nivel":metrics["nivel_riesgo"]},
            )
    logger.info("Ingesta completada para %s.", periodo)
