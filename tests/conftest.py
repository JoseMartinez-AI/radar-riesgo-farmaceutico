"""
conftest.py — Fixtures y configuración global de pytest para el proyecto
Radar de Riesgo Farmacéutico Perú-FDA.

Este archivo es descubierto automáticamente por pytest; no necesita importarse.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Garantizar que el directorio raíz esté en sys.path para todos los tests,
# independientemente de desde dónde se ejecute pytest.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
