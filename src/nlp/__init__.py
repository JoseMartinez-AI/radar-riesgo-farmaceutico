"""
Subpaquete NLP para procesamiento de datos no estructurados.

Exporta las funciones más usadas:
    from src.nlp import clean_clinical_text, detect_risk_signals_in_text
"""
from src.nlp.extractor import clean_clinical_text, detect_risk_signals_in_text

__all__ = ["clean_clinical_text", "detect_risk_signals_in_text"]
