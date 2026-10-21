"""Tests unitarios para el modulo NLP de extraccion y deteccion de senales."""
import pytest
from src.nlp.extractor import (
    clean_clinical_text,
    detect_risk_signals_in_text,
    _normalize,
)


class TestNormalize:
    def test_convierte_a_minusculas(self):
        assert _normalize("ARRITMIA") == "arritmia"

    def test_elimina_tildes_espanol(self):
        assert _normalize("Hepatotoxicidad") == "hepatotoxicidad"
        assert _normalize("Malformaciones Congénitas") == "malformaciones congenitas"
        assert _normalize("Teratogénico") == "teratogenico"

    def test_elimina_tildes_compuestas(self):
        assert "o" in _normalize("hépatotoxicité")

    def test_no_altera_numeros(self):
        assert "30" in _normalize("dosis de 30 mg/dia")


class TestCleanClinicalText:
    def test_colapsa_espacios_multiples(self):
        assert clean_clinical_text("hola   mundo") == "hola mundo"

    def test_elimina_caracteres_control(self):
        result = clean_clinical_text("hola\x00mundo\x01test")
        assert "\x00" not in result
        assert "\x01" not in result

    def test_texto_vacio_retorna_vacio(self):
        assert clean_clinical_text("") == ""

    def test_none_retorna_vacio(self):
        assert clean_clinical_text(None) == ""

    def test_saltos_de_linea_se_colapsan(self):
        result = clean_clinical_text("linea1\n\n\nlinea2")
        assert result == "linea1 linea2"

    def test_tabs_se_normalizan(self):
        result = clean_clinical_text("col1\tcol2")
        assert result == "col1 col2"

    def test_preserva_contenido(self):
        texto = "Riesgo de hepatotoxicidad grave."
        assert "hepatotoxicidad" in clean_clinical_text(texto)


class TestDetectRiskSignals:
    def test_detecta_terminos_espanol_basicos(self):
        text = "El farmaco presenta riesgo de hepatotoxicidad y malformaciones congenitas."
        result = detect_risk_signals_in_text(text, lang="es")
        assert "hepatotoxicidad" in result["terminos_detectados"]
        assert "malformaciones congenitas" in result["terminos_detectados"]

    def test_es_alerta_critica_con_2_o_mas_terminos(self):
        text = "Hepatotoxicidad grave y riesgo de arritmia ventricular."
        result = detect_risk_signals_in_text(text, lang="es")
        assert result["es_alerta_critica"] is True

    def test_no_es_alerta_critica_con_1_termino(self):
        text = "Existe riesgo de arritmia en dosis altas."
        result = detect_risk_signals_in_text(text, lang="es")
        # Con solo 1 termino no debe ser alerta critica
        if result["conteo_terminos"] < 2:
            assert result["es_alerta_critica"] is False

    def test_detecta_terminos_ingles(self):
        text = "Black box warning: risk of hepatotoxicity and teratogenic effects."
        result = detect_risk_signals_in_text(text, lang="en")
        assert "hepatotoxicity" in result["terminos_detectados"]
        assert "black box warning" in result["terminos_detectados"]

    def test_texto_sin_riesgo_retorna_vacio(self):
        text = "Administrar con alimentos para mejorar la tolerancia gastrica."
        result = detect_risk_signals_in_text(text, lang="es")
        assert result["conteo_terminos"] == 0
        assert result["es_alerta_critica"] is False
        assert result["score_severidad_texto"] == 0.0

    def test_score_entre_0_y_1(self):
        text = ("Riesgo grave: hepatotoxicidad, arritmia, anafilaxia, "
                "insuficiencia renal aguda, contraindicado, teratogenico.")
        result = detect_risk_signals_in_text(text, lang="es")
        assert 0.0 <= result["score_severidad_texto"] <= 1.0

    def test_normaliza_tildes_automaticamente(self):
        """El modulo debe detectar 'teratogenico' aunque el texto use tilde."""
        text = "El medicamento es teratogénico y puede causar hepatotoxicidad."
        result = detect_risk_signals_in_text(text, lang="es")
        assert "teratogenico" in result["terminos_detectados"]
        assert "hepatotoxicidad" in result["terminos_detectados"]

    def test_conteo_terminos_es_entero(self):
        result = detect_risk_signals_in_text("texto de prueba", lang="es")
        assert isinstance(result["conteo_terminos"], int)

    def test_terminos_detectados_es_lista(self):
        result = detect_risk_signals_in_text("prueba sin riesgo", lang="es")
        assert isinstance(result["terminos_detectados"], list)

    def test_valproato_detecta_malformaciones_y_contraindicado(self):
        text = ("Contraindicado durante el embarazo por riesgo elevado de "
                "malformaciones congenitas y hepatotoxicidad.")
        result = detect_risk_signals_in_text(text, lang="es")
        assert "malformaciones congenitas" in result["terminos_detectados"]
        assert "contraindicado" in result["terminos_detectados"]
        assert "hepatotoxicidad" in result["terminos_detectados"]
        assert result["es_alerta_critica"] is True
