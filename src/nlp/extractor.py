"""
Modulo NLP para procesamiento de datos no estructurados:
- Extraccion de texto desde boletines PDF de DIGEMID (pdfplumber)
- Deteccion de terminos criticos de farmacovigilancia (ES/EN)
- Normalizacion de texto (tildes, caracteres de control)
- Calculo de score de severidad textual
"""
from __future__ import annotations
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List
import logging

try:
    import pdfplumber
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

# Terminos clinicos de alarma regulatoria (espanol e ingles)
HIGH_RISK_KEYWORDS: Dict[str, List[str]] = {
    "es": [
        "hepatotoxicidad", "malformaciones congenitas", "defectos del tubo neural",
        "insuficiencia renal aguda", "muerte subita", "sindrome de stevens-johnson",
        "necrolisis epidermica toxica", "arritmia", "prolongacion del qt",
        "infarto agudo", "contraindicado", "retiro del mercado", "teratogenico",
        "alerta sanitaria", "reaccion adversa grave", "anafilaxia",
        "agranulocitosis", "aplasia medular", "torsades de pointes",
        "hipertension pulmonar", "falla hepatica fulminante",
    ],
    "en": [
        "hepatotoxicity", "congenital malformations", "neural tube defects",
        "acute kidney injury", "sudden death", "stevens-johnson syndrome",
        "toxic epidermal necrolysis", "arrhythmia", "qt prolongation",
        "myocardial infarction", "contraindicated", "black box warning",
        "market withdrawal", "teratogenic", "serious adverse reaction",
        "anaphylaxis", "agranulocytosis", "aplastic anemia",
        "torsades de pointes", "pulmonary hypertension", "fulminant hepatic failure",
    ],
}


def _normalize(text: str) -> str:
    """Normaliza a minusculas sin tildes ni caracteres especiales (diacriticos)."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrae texto de todas las paginas de un PDF (requiere pdfplumber)."""
    if not _PDF_AVAILABLE:
        logger.warning("pdfplumber no instalado. Instale con: pip install pdfplumber")
        return ""
    pages: List[str] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    pages.append(txt)
        return "\n".join(pages)
    except Exception as exc:
        logger.error("Error al leer PDF %s: %s", pdf_path, exc)
        return ""


def clean_clinical_text(text: str) -> str:
    """Colapsa espacios multiples y elimina caracteres de control."""
    if not text:
        return ""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_risk_signals_in_text(
    text: str,
    lang: str = "es",
) -> Dict[str, Any]:
    """
    Detecta terminos de alto riesgo en texto clinico/regulatorio.

    Args:
        text: Texto libre de boletines DIGEMID u openFDA.
        lang: Idioma del diccionario ('es' o 'en').

    Returns:
        Dict con terminos_detectados, conteo_terminos,
        score_severidad_texto (0.0-1.0) y es_alerta_critica.
    """
    norm = _normalize(clean_clinical_text(text))
    keywords = HIGH_RISK_KEYWORDS.get(lang, HIGH_RISK_KEYWORDS["es"])
    matches = [kw for kw in keywords if kw in norm]
    score = min(1.0, len(matches) / max(len(keywords), 1))
    return {
        "terminos_detectados":   matches,
        "conteo_terminos":        len(matches),
        "score_severidad_texto": round(score, 3),
        "es_alerta_critica":     len(matches) >= 2,
    }


def process_digemid_pdf(pdf_path: Path, lang: str = "es") -> Dict[str, Any]:
    """
    Pipeline completo para un PDF de alerta DIGEMID:
    extraccion -> limpieza -> deteccion de senales.
    """
    raw_text   = extract_text_from_pdf(pdf_path)
    clean_text = clean_clinical_text(raw_text)
    signals    = detect_risk_signals_in_text(clean_text, lang)
    signals["contenido_limpio"] = clean_text[:2000]  # preview 2 KB
    return signals
