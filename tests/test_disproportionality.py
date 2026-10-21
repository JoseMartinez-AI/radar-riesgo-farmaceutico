"""Tests unitarios para el motor de mineria de datos de desproporcionalidad.
Cubre PRR, ROR, Chi2 de Yates, evaluacion de nivel de riesgo, IC95% y metricas compuestas.
"""
import pytest
from src.mining.disproportionality import (
    calculate_prr,
    calculate_ror,
    calculate_chi_square_yates,
    evaluate_risk_level,
    compute_signal_metrics,
    prr_confidence_interval,
)


class TestCalculatePRR:
    def test_alto_riesgo_valproato(self):
        """Valproato + malformaciones congenitas -> PRR > 2.0 (documentado)."""
        prr = calculate_prr(890, 15000, 2400, 450000)
        assert prr > 2.0, f"PRR esperado > 2.0, obtenido: {prr:.4f}"

    def test_alto_riesgo_isotretinoina(self):
        prr = calculate_prr(1200, 11000, 2090, 450000)
        assert prr > 2.0

    def test_bajo_riesgo_metformina(self):
        prr = calculate_prr(420, 35000, 31000, 450000)
        assert prr < 2.0

    def test_denominador_ab_cero_retorna_cero(self):
        assert calculate_prr(0, 0, 10, 100) == 0.0

    def test_denominador_cd_cero_retorna_cero(self):
        assert calculate_prr(5, 100, 0, 0) == 0.0

    def test_c_igual_cero_retorna_cero(self):
        assert calculate_prr(10, 100, 0, 500) == 0.0

    def test_todos_cero_retorna_cero(self):
        assert calculate_prr(0, 0, 0, 0) == 0.0

    def test_retorna_float(self):
        assert isinstance(calculate_prr(100, 500, 200, 5000), float)

    def test_prr_mayor_uno_cuando_sobrerrepresentado(self):
        # a/(a+b) > c/(c+d) => PRR > 1
        prr = calculate_prr(100, 100, 10, 1000)
        assert prr > 1.0


class TestCalculateROR:
    def test_ror_clozapina_agranulocitosis(self):
        """Clozapina tiene ROR extremadamente alto (> 100 esperado)."""
        ror = calculate_ror(1850, 8000, 950, 452800)
        assert ror > 100

    def test_ror_domperidona_arritmia(self):
        ror = calculate_ror(310, 8500, 7200, 450000)
        assert ror > 0

    def test_b_cero_retorna_cero(self):
        assert calculate_ror(10, 0, 5, 100) == 0.0

    def test_c_cero_retorna_cero(self):
        assert calculate_ror(10, 5, 0, 100) == 0.0

    def test_ror_positivo_con_valores_validos(self):
        ror = calculate_ror(100, 500, 200, 10000)
        assert ror > 0

    def test_retorna_float(self):
        assert isinstance(calculate_ror(50, 200, 100, 3000), float)


class TestChiSquareYates:
    def test_caso_alto_riesgo_supera_umbral(self):
        chi2 = calculate_chi_square_yates(890, 15000, 2400, 450000)
        assert chi2 >= 4.0

    def test_todos_cero_retorna_cero(self):
        assert calculate_chi_square_yates(0, 0, 0, 0) == 0.0

    def test_resultado_nunca_negativo(self):
        casos = [(1, 1, 1, 1), (0, 5, 3, 100), (50, 50, 50, 50), (0, 0, 0, 10)]
        for a, b, c, d in casos:
            assert calculate_chi_square_yates(a, b, c, d) >= 0.0

    def test_retorna_float(self):
        chi2 = calculate_chi_square_yates(310, 8500, 7200, 450000)
        assert isinstance(chi2, float)

    def test_domperidona_genera_senal(self):
        chi2 = calculate_chi_square_yates(310, 8500, 7200, 450000)
        assert chi2 > 0


class TestEvaluateRiskLevel:
    def test_nivel_alto_todos_criterios(self):
        assert evaluate_risk_level(prr=5.0, chi2=150.0, cases=50) == "Alto"

    def test_nivel_alto_umbral_exacto(self):
        assert evaluate_risk_level(prr=2.0, chi2=4.0, cases=3) == "Alto"

    def test_nivel_medio_criterio_combinado(self):
        assert evaluate_risk_level(prr=1.6, chi2=3.5, cases=3) == "Medio"

    def test_nivel_bajo_cuando_prr_menor_uno(self):
        # Incluso si chi2 es alto, si PRR < 1 no hay senal de riesgo (esta subrepresentado)
        assert evaluate_risk_level(prr=0.5, chi2=10.0, cases=10) == "Bajo"

    def test_nivel_bajo_sin_umbral(self):
        assert evaluate_risk_level(prr=0.8, chi2=1.0, cases=10) == "Bajo"

    def test_prr_alto_pero_casos_insuficientes_para_alto(self):
        # PRR>=2 y chi2>=4 pero solo 2 casos -> Medio
        assert evaluate_risk_level(prr=10.0, chi2=50.0, cases=2) == "Medio"

    def test_un_solo_caso_siempre_bajo(self):
        # Solo 1 caso no alcanza ni Medio (MIN_CASES_MED=2)
        assert evaluate_risk_level(prr=10.0, chi2=50.0, cases=1) == "Bajo"

    def test_nivel_bajo_prr_cero(self):
        assert evaluate_risk_level(prr=0.0, chi2=0.0, cases=0) == "Bajo"


class TestComputeSignalMetrics:
    def test_estructura_del_resultado(self):
        result = compute_signal_metrics(890, 15000, 2400, 450000)
        campos = ["prr", "ror", "chi_cuadrado", "nivel_riesgo", "casos_observados",
                  "ic95_lo", "ic95_hi"]
        for campo in campos:
            assert campo in result, f"Campo faltante: {campo}"

    def test_nivel_alto_valproato_malformaciones(self):
        result = compute_signal_metrics(890, 15000, 2400, 450000)
        assert result["nivel_riesgo"] == "Alto"
        assert result["prr"] > 2.0

    def test_nivel_alto_clozapina_agranulocitosis(self):
        result = compute_signal_metrics(1850, 8000, 950, 452800)
        assert result["nivel_riesgo"] == "Alto"

    def test_nivel_bajo_metformina_nauseas(self):
        result = compute_signal_metrics(420, 35000, 31000, 450000)
        assert result["nivel_riesgo"] == "Bajo"

    def test_casos_cero_devuelve_bajo(self):
        result = compute_signal_metrics(0, 100, 50, 1000)
        assert result["nivel_riesgo"] == "Bajo"

    def test_valores_redondeados_a_2_decimales(self):
        result = compute_signal_metrics(100, 500, 200, 5000)
        for campo in ["prr", "ror", "chi_cuadrado"]:
            assert round(result[campo], 2) == result[campo]

    def test_casos_observados_es_a(self):
        result = compute_signal_metrics(890, 15000, 2400, 450000)
        assert result["casos_observados"] == 890


class TestPRRConfidenceInterval:
    def test_ic95_es_valido_para_senal_alta(self):
        lo, hi = prr_confidence_interval(890, 15000, 2400, 450000)
        assert lo > 0
        assert hi > lo

    def test_ic95_contiene_prr(self):
        """El IC95% debe siempre contener el valor del PRR."""
        a, b, c, d = 310, 8500, 7200, 450000
        prr = calculate_prr(a, b, c, d)
        lo, hi = prr_confidence_interval(a, b, c, d)
        assert lo <= prr <= hi

    def test_a_cero_retorna_cero_cero(self):
        lo, hi = prr_confidence_interval(0, 100, 50, 1000)
        assert lo == 0.0 and hi == 0.0

    def test_c_cero_retorna_cero_cero(self):
        lo, hi = prr_confidence_interval(10, 100, 0, 500)
        assert lo == 0.0 and hi == 0.0

    def test_retorna_tupla_de_floats(self):
        lo, hi = prr_confidence_interval(100, 500, 200, 5000)
        assert isinstance(lo, float)
        assert isinstance(hi, float)
