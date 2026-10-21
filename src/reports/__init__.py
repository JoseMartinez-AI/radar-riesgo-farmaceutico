"""
Subpaquete de exportación de reportes para el Dashboard.

Exporta las funciones de generación de reportes:
    from src.reports import generate_csv_bytes, build_signal_report
"""
from src.reports.exporter import generate_csv_bytes, build_signal_report

__all__ = ["generate_csv_bytes", "build_signal_report"]
