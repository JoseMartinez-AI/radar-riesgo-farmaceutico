"""Tests unitarios para el modulo de exportacion de reportes CSV."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.reports.exporter import generate_csv_bytes, build_signal_report


class TestGenerateCsvBytes:
    def test_retorna_bytes(self):
        records = [{"col1": "val1", "col2": "val2"}]
        result = generate_csv_bytes(records)
        assert isinstance(result, bytes)

    def test_lista_vacia_retorna_bytes_vacios(self):
        assert generate_csv_bytes([]) == b""

    def test_contiene_encabezados(self):
        records = [{"Principio Activo": "METFORMINA", "PRR": 0.8}]
        csv_text = generate_csv_bytes(records).decode("utf-8-sig")
        assert "Principio Activo" in csv_text
        assert "PRR" in csv_text

    def test_contiene_datos(self):
        records = [{"farmaco": "VALPROATO", "nivel": "Alto"}]
        csv_text = generate_csv_bytes(records).decode("utf-8-sig")
        assert "VALPROATO" in csv_text
        assert "Alto" in csv_text

    def test_bom_utf8_para_compatibilidad_excel(self):
        """El CSV debe comenzar con BOM UTF-8 (0xEF 0xBB 0xBF)."""
        records = [{"col": "val"}]
        result = generate_csv_bytes(records)
        assert result.startswith(b"\xef\xbb\xbf")

    def test_multiples_registros(self):
        records = [
            {"farmaco": "VALPROATO", "nivel": "Alto"},
            {"farmaco": "METFORMINA", "nivel": "Bajo"},
        ]
        csv_text = generate_csv_bytes(records).decode("utf-8-sig")
        assert "VALPROATO" in csv_text
        assert "METFORMINA" in csv_text

    def test_separador_es_coma(self):
        records = [{"col1": "a", "col2": "b"}]
        csv_text = generate_csv_bytes(records).decode("utf-8-sig")
        # La segunda linea debe tener coma como separador
        lines = csv_text.strip().split("\r\n")
        assert len(lines) == 2
        assert "," in lines[1]


class TestBuildSignalReport:
    def setup_method(self):
        """Simula una fila del DataFrame del dashboard."""
        self.mock_row = {
            "principio_activo": "VALPROATO DE SODIO",
            "codigo_atc": "N03AG01",
            "reaccion_adversa": "Malformaciones congenitas",
            "sistema_organico": "Trastornos congenitos",
            "prr": 11.46,
            "ror": 13.37,
            "chi_cuadrado": 3245.0,
            "nivel_riesgo": "Alto",
            "casos_observados": 890,
            "total_reportes_graves": 890,
            "registro_sanitario_vigente": 1,
            "incluido_pnume": 1,
            "estado_alerta_digemid": "Alerta Emitida",
        }

    def test_retorna_lista_con_un_elemento(self):
        result = build_signal_report(self.mock_row)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_campos_obligatorios_presentes(self):
        result = build_signal_report(self.mock_row)[0]
        campos_obligatorios = [
            "Principio Activo", "Codigo ATC", "Reaccion Adversa (MedDRA)",
            "PRR", "ROR", "Chi2 (Yates)", "Nivel de Riesgo",
            "Casos Observados", "Total Reportes Graves",
            "Registro Sanitario Vigente", "Incluido PNUME",
            "Estado Alerta DIGEMID", "Periodo FAERS", "Fuente",
        ]
        for campo in campos_obligatorios:
            assert campo in result, f"Campo faltante en reporte: {campo}"

    def test_vigente_se_muestra_como_si(self):
        result = build_signal_report(self.mock_row)[0]
        assert result["Registro Sanitario Vigente"] == "Si"

    def test_no_vigente_se_muestra_como_no(self):
        row = dict(self.mock_row)
        row["registro_sanitario_vigente"] = 0
        result = build_signal_report(row)[0]
        assert result["Registro Sanitario Vigente"] == "No"

    def test_pnume_incluido_se_muestra_como_si(self):
        result = build_signal_report(self.mock_row)[0]
        assert result["Incluido PNUME"] == "Si"

    def test_pnume_no_incluido_se_muestra_como_no(self):
        row = dict(self.mock_row)
        row["incluido_pnume"] = 0
        result = build_signal_report(row)[0]
        assert result["Incluido PNUME"] == "No"

    def test_prr_en_resultado_es_correcto(self):
        result = build_signal_report(self.mock_row)[0]
        assert result["PRR"] == 11.46

    def test_nivel_riesgo_es_correcto(self):
        result = build_signal_report(self.mock_row)[0]
        assert result["Nivel de Riesgo"] == "Alto"

    def test_fuente_menciona_faers_y_digemid(self):
        result = build_signal_report(self.mock_row)[0]
        assert "FAERS" in result["Fuente"]
        assert "DIGEMID" in result["Fuente"]

    def test_csv_round_trip_sin_perdida(self):
        """Verifica que CSV generado contiene el principio activo."""
        result = build_signal_report(self.mock_row)
        csv_bytes = generate_csv_bytes(result)
        csv_text = csv_bytes.decode("utf-8-sig")
        assert "VALPROATO DE SODIO" in csv_text
        assert "Alto" in csv_text
        assert "11.46" in csv_text
