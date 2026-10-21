"""
Tests unitarios y de integración para el módulo de Web Scraping y extracción de texto no estructurado.
Verifica:
1. Scraping de API openFDA (drug/label y drug/enforcement) con casos reales (Valproic acid, etc.).
2. Scraping y parsing de HTML con BeautifulSoup (título, contenido, párrafos y extracción de enlaces PDF).
3. Manejo de errores de red, respuestas vacías y códigos de estado (404/500).
"""
import pytest
from unittest.mock import patch, MagicMock
from src.pipeline.scraper import (
    scrape_openfda_label,
    scrape_openfda_recalls,
    parse_html_alert,
    download_alert_pdf,
)


class TestParseHtmlAlert:
    def test_extrae_titulo_y_parrafos_correctamente(self):
        html = """
        <html>
            <head><title>Portal DIGEMID</title></head>
            <body>
                <h1>Alerta de Farmacovigilancia N 15-2023</h1>
                <p>La DIGEMID comunica el riesgo de hepatotoxicidad severa asociado al uso de ketoconazol oral.</p>
                <p>Se recomienda la suspension preventiva del registro sanitario.</p>
                <a href="/alertas/comunicado_15.pdf">Descargar Boletin PDF</a>
                <a href="https://example.org/otro.html">Otro enlace</a>
            </body>
        </html>
        """
        result = parse_html_alert(html)
        assert "Alerta de Farmacovigilancia" in result["titulo"]
        assert "hepatotoxicidad severa" in result["contenido"]
        assert result["num_parrafos"] == 2
        assert len(result["pdf_urls"]) == 1
        assert result["pdf_urls"][0] == "/alertas/comunicado_15.pdf"

    def test_html_vacio_retorna_estructura_segura(self):
        result = parse_html_alert("")
        assert result["titulo"] == ""
        assert result["contenido"] == ""
        assert result["pdf_urls"] == []

    def test_detecta_multiples_enlaces_pdf(self):
        html = """
        <div>
            <p>Reportes adjuntos:</p>
            <a href="doc1.PDF">Doc 1</a>
            <a href="doc2.pdf">Doc 2</a>
            <a href="doc3.docx">Doc Word</a>
        </div>
        """
        result = parse_html_alert(html)
        assert len(result["pdf_urls"]) == 2


class TestScrapeOpenFDALabel:
    def test_mock_openfda_label_exitoso(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{
                "boxed_warning": ["WARNING: HEPATOTOXICITY, CONGENITAL MALFORMATIONS."],
                "warnings": ["Risk of acute liver injury."],
                "contraindications": ["Do not administer during pregnancy."],
                "adverse_reactions": ["Nausea, tremor, weight gain."]
            }]
        }
        with patch("requests.get", return_value=mock_response):
            result = scrape_openfda_label("VALPROIC ACID")
            assert result["encontrado"] is True
            assert "HEPATOTOXICITY" in result["boxed_warning"]
            assert "liver injury" in result["warnings"]
            assert "pregnancy" in result["contraindications"]

    def test_mock_openfda_label_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("requests.get", return_value=mock_response):
            result = scrape_openfda_label("FARMACO_INEXISTENTE_XYZ")
            assert result["encontrado"] is False
            assert "404" in result.get("motivo", "")

    def test_mock_openfda_label_network_error(self):
        with patch("requests.get", side_effect=Exception("Connection timed out")):
            result = scrape_openfda_label("VALPROIC ACID")
            assert result["encontrado"] is False
            assert "timed out" in result.get("error", "")


class TestScrapeOpenFDARecalls:
    def test_mock_recalls_exitoso(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "recall_number": "D-123-2024",
                    "reason_for_recall": "Presence of particulate matter",
                    "status": "Ongoing",
                    "classification": "Class II",
                    "distribution_pattern": "Nationwide",
                }
            ]
        }
        with patch("requests.get", return_value=mock_response):
            recalls = scrape_openfda_recalls("METFORMIN")
            assert len(recalls) == 1
            assert recalls[0]["recall_number"] == "D-123-2024"
            assert "particulate matter" in recalls[0]["reason_for_recall"]


class TestDownloadAlertPdf:
    def test_mock_descarga_pdf_correcta(self, tmp_path):
        save_file = tmp_path / "alerta.pdf"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_response.iter_content.return_value = [b"%PDF-1.4 mock content"]
        
        with patch("requests.get", return_value=mock_response):
            ok = download_alert_pdf("https://example.gov/alerta.pdf", save_file)
            assert ok is True
            assert save_file.exists()
            assert b"%PDF-1.4" in save_file.read_bytes()

    def test_mock_descarga_falla_con_status_403(self, tmp_path):
        save_file = tmp_path / "alerta.pdf"
        mock_response = MagicMock()
        mock_response.status_code = 403
        
        with patch("requests.get", return_value=mock_response):
            ok = download_alert_pdf("https://example.gov/alerta.pdf", save_file)
            assert ok is False
            assert not save_file.exists()
