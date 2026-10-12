"""
Modulo de exportacion de reportes CSV para el Dashboard de DIGEMID.
Genera fichas tecnicas de evidencia regulatoria con compatibilidad Excel (BOM UTF-8).
"""
from __future__ import annotations
import io
import csv
from typing import Any, Dict, List


def generate_csv_bytes(records: List[Dict[str, Any]]) -> bytes:
    """
    Genera bytes de CSV en memoria con BOM UTF-8 (compatible con Excel en Windows).

    Args:
        records: Lista de diccionarios con los datos a exportar.

    Returns:
        Bytes del CSV codificado en UTF-8-BOM, o b"" si la lista esta vacia.
    """
    if not records:
        return b""
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(records[0].keys()),
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()
    writer.writerows(records)
    return buffer.getvalue().encode("utf-8-sig")


def build_signal_report(df_row) -> List[Dict[str, Any]]:
    """
    Construye la ficha tecnica regulatoria para exportar.
    Acepta pandas Series o dict ordinario.

    Args:
        df_row: Fila del DataFrame (pandas Series o dict).

    Returns:
        Lista de un diccionario con todos los campos de la ficha.
    """
    # Normalizar a dict para compatibilidad con pandas Series y dicts planos
    row = dict(df_row) if hasattr(df_row, "items") else df_row
    v = row.get("registro_sanitario_vigente")
    p = row.get("incluido_pnume")
    return [{
        "Principio Activo":          row.get("principio_activo", ""),
        "Codigo ATC":                row.get("codigo_atc", ""),
        "Reaccion Adversa (MedDRA)": row.get("reaccion_adversa", ""),
        "Sistema Organico":          row.get("sistema_organico", ""),
        "PRR":                       row.get("prr", ""),
        "ROR":                       row.get("ror", ""),
        "Chi2 (Yates)":              row.get("chi_cuadrado", ""),
        "Nivel de Riesgo":           row.get("nivel_riesgo", ""),
        "Casos Observados":          row.get("casos_observados", ""),
        "Total Reportes Graves":     row.get("total_reportes_graves", ""),
        "Registro Sanitario Vigente": "Si" if v else "No",
        "Incluido PNUME":            "Si" if p else "No",
        "Estado Alerta DIGEMID":     row.get("estado_alerta_digemid", ""),
        "Periodo FAERS":             "2024-Q2",
        "Fuente":                    "FAERS / openFDA / DIGEMID",
    }]
