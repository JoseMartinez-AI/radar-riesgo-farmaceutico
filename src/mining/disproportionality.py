"""
Motor estadistico de mineria de datos para deteccion de senales de
desproporcionalidad en Farmacovigilancia.

Implementa:
  - PRR  (Proportional Reporting Ratio)
  - ROR  (Reporting Odds Ratio)
  - Chi2 (Chi-cuadrado con correccion de continuidad de Yates)
  - IC95% del PRR en escala logaritmica

Tabla de contingencia 2x2 estandar:
+-------------------+------------------------+------------------+
|                   | Reaccion de Interes    | Otras Reacciones |
+-------------------+------------------------+------------------+
| Farmaco de Interes|         a              |        b         |
| Otros Farmacos    |         c              |        d         |
+-------------------+------------------------+------------------+

Referencia: Evans SJW et al. (2001). Use of proportional reporting
            ratios (PRRs) for signal generation from spontaneous
            adverse drug reaction reports. Pharmacoepidemiology
            and Drug Safety, 10(6), 483-486.
"""
from __future__ import annotations
from typing import Dict, Any, Tuple
import math
from src.config import (
    PRR_THRESHOLD_HIGH, PRR_THRESHOLD_MED,
    CHI2_THRESHOLD_HIGH, CHI2_THRESHOLD_MED,
    MIN_CASES_HIGH, MIN_CASES_MED,
)


def calculate_prr(a: int, b: int, c: int, d: int) -> float:
    """
    PRR = [a/(a+b)] / [c/(c+d)]
    Retorna 0.0 ante denominador nulo o c==0.
    """
    if (a + b) == 0 or (c + d) == 0 or c == 0:
        return 0.0
    return float((a / (a + b)) / (c / (c + d)))


def calculate_ror(a: int, b: int, c: int, d: int) -> float:
    """
    ROR = (a*d) / (b*c)
    Retorna 0.0 ante denominador nulo.
    """
    if b == 0 or c == 0:
        return 0.0
    return float((a * d) / (b * c))


def calculate_chi_square_yates(a: int, b: int, c: int, d: int) -> float:
    """
    Chi2 con correccion de continuidad de Yates:
    Chi2 = N * (|ad - bc| - N/2)^2 / [(a+b)(c+d)(a+c)(b+d)]
    """
    n = a + b + c + d
    denom = (a + b) * (c + d) * (a + c) * (b + d)
    if denom == 0 or n == 0:
        return 0.0
    adj = abs(a * d - b * c) - (n / 2.0)
    if adj < 0:
        adj = 0.0
    return float(n * adj ** 2 / denom)


def prr_confidence_interval(
    a: int, b: int, c: int, d: int, z: float = 1.96
) -> Tuple[float, float]:
    """
    Intervalo de confianza (95%) del PRR en escala logaritmica.
    ln(PRR) +/- z * sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d))
    """
    if a == 0 or c == 0 or (a + b) == 0 or (c + d) == 0:
        return (0.0, 0.0)
    prr = calculate_prr(a, b, c, d)
    if prr <= 0:
        return (0.0, 0.0)
    se = math.sqrt(1/a - 1/(a + b) + 1/c - 1/(c + d))
    log_prr = math.log(prr)
    return (round(math.exp(log_prr - z * se), 3), round(math.exp(log_prr + z * se), 3))


def evaluate_risk_level(prr: float, chi2: float, cases: int) -> str:
    """
    Clasifica la senal de riesgo segun criterios regulatorios (Evans et al., FDA).
    - Alto : PRR >= 2.0, Chi2 >= 4.0, casos >= 3
    - Medio: PRR >= 1.5 y Chi2 >= 3.0 con casos >= 2 (o PRR >= 1.5 con casos >= 2)
    - Bajo : PRR < 1.5 o no supera umbrales minimos
    Nota: PRR debe ser >= 1.0 para representar un incremento en el reporte de riesgo.
    """
    if cases >= MIN_CASES_HIGH and prr >= PRR_THRESHOLD_HIGH and chi2 >= CHI2_THRESHOLD_HIGH:
        return "Alto"
    if cases >= MIN_CASES_MED and prr >= PRR_THRESHOLD_MED and chi2 >= CHI2_THRESHOLD_MED:
        return "Medio"
    return "Bajo"


def compute_signal_metrics(a: int, b: int, c: int, d: int) -> Dict[str, Any]:
    """
    Calcula el perfil completo de senales para un par (farmaco, reaccion).

    Returns:
        Dict con prr, ror, chi_cuadrado, ic95_lo, ic95_hi,
        nivel_riesgo y casos_observados.
    """
    prr  = calculate_prr(a, b, c, d)
    ror  = calculate_ror(a, b, c, d)
    chi2 = calculate_chi_square_yates(a, b, c, d)
    ic_lo, ic_hi = prr_confidence_interval(a, b, c, d)
    nivel = evaluate_risk_level(prr, chi2, a)
    return {
        "prr":              round(prr,  2),
        "ror":              round(ror,  2),
        "chi_cuadrado":     round(chi2, 2),
        "ic95_lo":          ic_lo,
        "ic95_hi":          ic_hi,
        "nivel_riesgo":     nivel,
        "casos_observados": a,
    }
