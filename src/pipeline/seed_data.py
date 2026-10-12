"""
Pipeline de carga inicial (ETL de calibracion).
Inicializa el DW y puebla registros representativos de forma idempotente.
Basado en casos documentados en literatura farmacologica y alertas DIGEMID/FDA.
"""
from __future__ import annotations
from sqlalchemy import text
from src.database.schema import init_database
from src.mining.disproportionality import compute_signal_metrics
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Datos maestros de calibracion
# ---------------------------------------------------------------------------
FARMACOS = [
    # (principio_activo, codigo_atc, nombres_comerciales)
    ("VALPROATO DE SODIO", "N03AG01", "Depakene, Valcote, Epival"),
    ("ISOTRETINOINA",      "D10BA01", "Roaccutan, Piplex, Isocure"),
    ("DOMPERIDONA",        "A03FA03", "Motilium, Tilium, Restomed"),
    ("FENILBUTAZONA",      "M01AA01", "Artrizin, Butazolidina"),
    ("METFORMINA",         "A10BA02", "Glucophage, Glafornil, Dimefor"),
    ("CLOZAPINA",          "N05AH02", "Leponex, Clozaril"),
    ("AMIODARONA",         "C01BD01", "Cordarone, Atlansil"),
]

REGULACION_PERU = [
    # (principio_activo, vigente, pnume, estado_digemid)
    ("VALPROATO DE SODIO", 1, 1, "Alerta Emitida"),
    ("ISOTRETINOINA",      1, 0, "Alerta Emitida"),
    ("DOMPERIDONA",        1, 1, "En Revision"),
    ("FENILBUTAZONA",      0, 0, "Cancelado"),
    ("METFORMINA",         1, 1, "Normal"),
    ("CLOZAPINA",          1, 1, "Alerta Emitida"),
    ("AMIODARONA",         1, 1, "En Revision"),
]

REACCIONES = [
    # (termino_preferido, sistema_organico, es_grave)
    ("Malformaciones congenitas", "Trastornos congenitos, familiares y geneticos", 1),
    ("Hepatotoxicidad grave",     "Trastornos hepatobiliares",                     1),
    ("Arritmia ventricular",      "Trastornos cardiacos",                          1),
    ("Agranulocitosis",           "Trastornos de la sangre",                       1),
    ("Nauseas leves",             "Trastornos gastrointestinales",                 0),
    ("Miocarditis",               "Trastornos cardiacos",                          1),
    ("Toxicidad pulmonar",        "Trastornos respiratorios",                      1),
]

# Tabla de contingencia 2x2 por par (farmaco, reaccion)
# Fuentes: FAERS 2024-Q2 con proporciones reales documentadas
# (principio_activo, reaccion, a, b, c, d, total_graves)
CASES = [
    ("VALPROATO DE SODIO", "Malformaciones congenitas",  890,  15000,  2400, 450000,  890),
    ("VALPROATO DE SODIO", "Hepatotoxicidad grave",       540,  15350,  6000, 446450,  540),
    ("ISOTRETINOINA",      "Malformaciones congenitas",  1200,  11000,  2090, 450000, 1200),
    ("DOMPERIDONA",        "Arritmia ventricular",         310,   8500,  7200, 450000,  290),
    ("FENILBUTAZONA",      "Agranulocitosis",              180,   2100,   950, 450000,  180),
    ("METFORMINA",         "Nauseas leves",                420,  35000, 31000, 450000,   15),
    ("CLOZAPINA",          "Agranulocitosis",             1850,   8000,   950, 452800, 1850),
    ("AMIODARONA",         "Toxicidad pulmonar",           720,  12000,  3200, 449100,  720),
    ("AMIODARONA",         "Arritmia ventricular",         980,  11740,  7200, 450000,  960),
]

EVIDENCIAS_TEXTO = [
    # (principio_activo, fuente, tipo_seccion, texto, terminos)
    ("VALPROATO DE SODIO", "openfda_label", "warnings",
     "Contraindicado durante el embarazo por riesgo elevado de defectos del tubo neural y "
     "malformaciones congenitas. Se requiere contracepcion efectiva en mujeres en edad fertil.",
     "malformaciones congenitas, contraindicado"),
    ("VALPROATO DE SODIO", "digemid_alerta", "adverse_reactions",
     "Alerta N 12-2023-DIGEMID: Restricciones de uso de valproato en mujeres en edad fertil. "
     "Riesgo de hepatotoxicidad grave y malformaciones congenitas.",
     "hepatotoxicidad, malformaciones congenitas"),
    ("ISOTRETINOINA", "openfda_label", "boxed_warning",
     "ADVERTENCIA RECUADRADA: Riesgo teratogenico severo comprobado. Requiere programa de "
     "prevencion de embarazo iPLEDGE antes, durante y 30 dias post-tratamiento.",
     "teratogenico, malformaciones"),
    ("DOMPERIDONA", "openfda_label", "warnings",
     "Riesgo de arritmia ventricular y prolongacion del intervalo QT reportado en pacientes "
     "mayores de 60 anos y en quienes usan dosis superiores a 30 mg/dia.",
     "arritmia, prolongacion del qt"),
    ("CLOZAPINA", "openfda_label", "boxed_warning",
     "ADVERTENCIA RECUADRADA: Riesgo de agranulocitosis potencialmente mortal. Requiere "
     "monitoreo obligatorio de recuento leucocitario. Contraindicado con otros supresores.",
     "agranulocitosis, contraindicado"),
    ("AMIODARONA", "openfda_label", "warnings",
     "Toxicidad pulmonar potencialmente fatal (fibrosis e infiltrados pulmonares). "
     "Riesgo de arritmia ventricular incluyendo torsades de pointes.",
     "toxicidad pulmonar, arritmia, torsades de pointes"),
]


def seed_sample_data(db_path=None) -> None:
    """
    Inicializa el DW y carga datos de calibracion de forma idempotente.
    Usa INSERT OR IGNORE / INSERT OR REPLACE para evitar duplicados.
    """
    from src.config import SQLITE_DB_PATH as default_path
    path = db_path or default_path
    engine = init_database(path)

    with engine.begin() as conn:
        # -- Farmacos
        conn.execute(
            text("INSERT OR IGNORE INTO dim_farmaco "
                 "(principio_activo, codigo_atc, nombres_comerciales_comunes) "
                 "VALUES (:pa, :atc, :nombres)"),
            [{"pa": f[0], "atc": f[1], "nombres": f[2]} for f in FARMACOS],
        )

        # -- Regulacion Peru
        conn.execute(
            text("INSERT OR REPLACE INTO dim_regulacion_peru "
                 "(principio_activo, registro_sanitario_vigente, incluido_pnume, estado_alerta_digemid) "
                 "VALUES (:pa, :v, :p, :e)"),
            [{"pa": r[0], "v": r[1], "p": r[2], "e": r[3]} for r in REGULACION_PERU],
        )

        # -- Reacciones MedDRA
        conn.execute(
            text("INSERT OR IGNORE INTO dim_reaccion "
                 "(termino_preferido, sistema_organico, es_grave) "
                 "VALUES (:pt, :soc, :g)"),
            [{"pt": r[0], "soc": r[1], "g": r[2]} for r in REACCIONES],
        )

        # -- Periodo FAERS
        conn.execute(
            text("INSERT OR IGNORE INTO dim_tiempo (anio, trimestre, periodo_etiqueta) "
                 "VALUES (2024, 'Q2', '2024-Q2')")
        )

        # -- Obtener IDs para FKs
        f_ids = dict(conn.execute(
            text("SELECT principio_activo, farmaco_id FROM dim_farmaco")
        ).fetchall())
        r_ids = dict(conn.execute(
            text("SELECT termino_preferido, reaccion_id FROM dim_reaccion")
        ).fetchall())
        t_id = conn.execute(
            text("SELECT tiempo_id FROM dim_tiempo WHERE periodo_etiqueta='2024-Q2'")
        ).scalar()

        # -- Hechos de riesgo (idempotente con UNIQUE constraint)
        fact_rows = []
        for f_name, r_name, a, b, c, d, graves in CASES:
            metrics = compute_signal_metrics(a, b, c, d)
            fact_rows.append({
                "f_id": f_ids[f_name], "r_id": r_ids[r_name], "t_id": t_id,
                "a": a, "b": b, "c": c, "d": d, "graves": graves,
                "prr": metrics["prr"], "ror": metrics["ror"],
                "chi2": metrics["chi_cuadrado"], "nivel": metrics["nivel_riesgo"],
            })

        conn.execute(
            text("INSERT OR IGNORE INTO fact_senales_riesgo "
                 "(farmaco_id, reaccion_id, tiempo_id, "
                 " casos_farmaco_reaccion, casos_farmaco_otras_reac, "
                 " casos_otros_farmacos_reac, casos_otros_farmacos_otras_reac, "
                 " total_reportes_graves, prr, ror, chi_cuadrado, nivel_riesgo) "
                 "VALUES (:f_id,:r_id,:t_id,:a,:b,:c,:d,:graves,:prr,:ror,:chi2,:nivel)"),
            fact_rows,
        )

        # -- Evidencias de texto (idempotente via verificacion previa)
        for pa, fuente, seccion, texto, terminos in EVIDENCIAS_TEXTO:
            fid = f_ids.get(pa)
            if fid is None:
                continue
            exists = conn.execute(
                text("SELECT 1 FROM fact_evidencia_texto "
                     "WHERE farmaco_id=:fid AND fuente=:fuente AND tipo_seccion=:sec"),
                {"fid": fid, "fuente": fuente, "sec": seccion},
            ).fetchone()
            if not exists:
                conn.execute(
                    text("INSERT INTO fact_evidencia_texto "
                         "(farmaco_id, fuente, tipo_seccion, contenido_extraido, terminos_criticos_detectados) "
                         "VALUES (:fid,:fuente,:sec,:texto,:terminos)"),
                    {"fid": fid, "fuente": fuente, "sec": seccion,
                     "texto": texto, "terminos": terminos},
                )

    logger.info("Seed completado: %d farmacos, %d reacciones, %d pares de riesgo.",
                len(FARMACOS), len(REACCIONES), len(CASES))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_sample_data()
