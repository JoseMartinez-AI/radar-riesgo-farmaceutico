"""
Carga de evidencias de texto al Data Warehouse.
Fuentes: alertas HTML de DIGEMID (data/raw/digemid) y respuestas de openFDA (data/raw/openfda/*_live.json).
Cada texto se limpia, se clasifica con el modulo NLP y se inserta en fact_evidencia_texto.

Uso:
    python -m src.pipeline.load_evidence --db data\\processed\\radar_validacion.db
"""
from __future__ import annotations
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from sqlalchemy import text

from src.config import RAW_DIGEMID_DIR, RAW_OPENFDA_DIR, SQLITE_DB_PATH
from src.database.schema import init_database
from src.nlp.extractor import clean_clinical_text, detect_risk_signals_in_text
from src.pipeline.scraper import parse_html_alert

logger = logging.getLogger(__name__)

# Palabra clave del nombre de archivo -> principio activo en dim_farmaco
ALERTAS = {"valproato": "VALPROATO DE SODIO", "ketoconazol": "KETOCONAZOL"}
LABELS = {"clozapine": "CLOZAPINA", "valproic_acid": "VALPROATO DE SODIO"}
SECCIONES_LABEL = ("boxed_warning", "warnings", "contraindications")


def _farmaco_id(conn, nombre: str) -> int:
    conn.execute(text("INSERT OR IGNORE INTO dim_farmaco (principio_activo) VALUES (:pa)"), {"pa": nombre})
    return conn.execute(text("SELECT farmaco_id FROM dim_farmaco WHERE principio_activo=:pa"), {"pa": nombre}).scalar()


def _insertar(conn, farmaco: str, fuente: str, tipo: str, contenido: str, lang: str) -> bool:
    """Inserta una evidencia si no existe. Devuelve True si inserto."""
    contenido = clean_clinical_text(contenido)
    if not contenido:
        return False
    f_id = _farmaco_id(conn, farmaco)
    existe = conn.execute(
        text("SELECT 1 FROM fact_evidencia_texto WHERE farmaco_id=:f AND fuente=:s "
             "AND tipo_seccion=:t AND contenido_extraido=:c"),
        {"f": f_id, "s": fuente, "t": tipo, "c": contenido},
    ).first()
    if existe:
        return False
    res = detect_risk_signals_in_text(contenido, lang=lang)
    terminos = ", ".join(res.get("terminos_detectados", []))
    score = float(res.get("score_severidad_texto", 0.0))
    conn.execute(
        text("INSERT INTO fact_evidencia_texto "
             "(farmaco_id, fuente, tipo_seccion, contenido_extraido, sentimiento_riesgo, terminos_criticos_detectados) "
             "VALUES (:f,:s,:t,:c,:score,:term)"),
        {"f": f_id, "s": fuente, "t": tipo, "c": contenido, "score": score, "term": terminos},
    )
    logger.info("Insertado: %s | %s | %s | %d caracteres | score=%.3f | terminos=[%s]",
                farmaco, fuente, tipo, len(contenido), score, terminos)
    return True


def cargar_evidencias(db_path: Optional[Path] = None) -> dict:
    engine = init_database(db_path or SQLITE_DB_PATH)
    insertados = omitidos = 0
    with engine.begin() as conn:
        for p in sorted(RAW_DIGEMID_DIR.glob("*.html")):
            clave = next((k for k in ALERTAS if k in p.name.lower()), None)
            if clave is None:
                logger.warning("Alerta %s sin farmaco asociado en ALERTAS: se omite", p.name)
                omitidos += 1
                continue
            alerta = parse_html_alert(p.read_text(encoding="utf-8", errors="ignore"))
            ok = _insertar(conn, ALERTAS[clave], "DIGEMID", "alerta_html", alerta["contenido"], "es")
            insertados += ok
            omitidos += not ok
        for p in sorted(RAW_OPENFDA_DIR.glob("label_*_live.json")):
            clave = next((k for k in LABELS if f"label_{k}_live" == p.stem), None)
            if clave is None:
                logger.warning("Label %s sin farmaco asociado en LABELS: se omite", p.name)
                omitidos += 1
                continue
            datos = json.loads(p.read_text(encoding="utf-8"))
            if not datos.get("encontrado"):
                omitidos += 1
                continue
            for seccion in SECCIONES_LABEL:
                ok = _insertar(conn, LABELS[clave], "openFDA label", seccion, datos.get(seccion, ""), "en")
                insertados += ok
                omitidos += not ok
        total = conn.execute(text("SELECT COUNT(*) FROM fact_evidencia_texto")).scalar()
    logger.info("Carga completada. Insertados: %d | Omitidos o duplicados: %d | Total en tabla: %d",
                insertados, omitidos, total)
    return {"insertados": insertados, "omitidos": omitidos, "total": total}


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Carga evidencias de texto a fact_evidencia_texto")
    parser.add_argument("--db", type=Path, default=None, help="Ruta de la base SQLite (opcional)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cargar_evidencias(args.db)


if __name__ == "__main__":
    main()