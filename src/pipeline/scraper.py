"""
Modulo de recoleccion para fuentes no estructuradas:
1. openFDA API Scraper: extrae advertencias (warnings, boxed_warning, contraindications)
   y motivos de retiro (drug/enforcement) desde los endpoints de openFDA.
2. Analisis de alertas de farmacovigilancia de DIGEMID: analiza alertas HTML ya descargadas
   y descarga PDFs cuando se conoce su URL. No descubre boletines de forma automatica.

Uso por linea de comandos:
    python -m src.pipeline.scraper --farmacos clozapine "valproic acid"
"""
from __future__ import annotations
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

from src.config import (
    OPENFDA_LABEL_URL,
    OPENFDA_ENFORCEMENT_URL,
    RAW_OPENFDA_DIR,
    RAW_DIGEMID_DIR,
)

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


# ============================================================================
# 1. SCRAPER DE openFDA (API REST y Texto Libre)
# ============================================================================

def scrape_openfda_label(drug_name: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Extrae secciones de texto no estructurado desde openFDA drug/label:
    - boxed_warning (Advertencias recuadradas)
    - warnings (Advertencias generales)
    - contraindications (Contraindicaciones)
    - adverse_reactions (Reacciones adversas registradas)
    """
    clean_name = drug_name.strip()
    params = {
        "search": f'openfda.substance_name:"{clean_name}" OR openfda.generic_name:"{clean_name}"',
        "limit": 1,
    }
    try:
        resp = requests.get(OPENFDA_LABEL_URL, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return {"encontrado": False, "farmaco": clean_name}

            first_label = results[0]
            boxed = " ".join(first_label.get("boxed_warning", []))
            warnings = " ".join(first_label.get("warnings", []))
            contra = " ".join(first_label.get("contraindications", []))
            adverse = " ".join(first_label.get("adverse_reactions", []))

            return {
                "encontrado": True,
                "farmaco": clean_name,
                "boxed_warning": boxed.strip(),
                "warnings": warnings.strip(),
                "contraindications": contra.strip(),
                "adverse_reactions": adverse.strip(),
                "fuente": "openfda_label"
            }
        elif resp.status_code == 404:
            logger.info("Farmaco '%s' no encontrado en openFDA drug/label", clean_name)
            return {"encontrado": False, "farmaco": clean_name, "motivo": "No encontrado (404)"}
        else:
            logger.warning("Error de respuesta en openFDA (%d): %s", resp.status_code, resp.text[:200])
            return {"encontrado": False, "farmaco": clean_name, "error": f"HTTP {resp.status_code}"}
    except Exception as exc:
        logger.error("Error al consultar openFDA para '%s': %s", clean_name, exc)
        return {"encontrado": False, "farmaco": clean_name, "error": str(exc)}


def scrape_openfda_recalls(drug_name: str, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Extrae motivos textuales de retiros del mercado desde openFDA drug/enforcement.
    """
    clean_name = drug_name.strip()
    params = {
        "search": f'product_description:"{clean_name}"',
        "limit": 3,
    }
    recalls = []
    try:
        resp = requests.get(OPENFDA_ENFORCEMENT_URL, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("results", []):
                recalls.append({
                    "recall_number": item.get("recall_number", ""),
                    "reason_for_recall": item.get("reason_for_recall", ""),
                    "status": item.get("status", ""),
                    "classification": item.get("classification", ""),
                    "distribution_pattern": item.get("distribution_pattern", ""),
                })
    except Exception as exc:
        logger.error("Error en openFDA recalls para '%s': %s", clean_name, exc)
    return recalls


# ============================================================================
# 2. ANALISIS DE HTML PARA ALERTAS DE FARMACOVIGILANCIA (DIGEMID)
# ============================================================================

def parse_html_alert(html_content: str) -> Dict[str, Any]:
    """
    Extrae de forma estructurada los campos clave de una alerta sanitaria en HTML:
    - Titulo del boletin / alerta
    - Texto descriptivo y advertencias
    - Enlaces a documentos adjuntos (PDFs)
    """
    if not html_content:
        return {"titulo": "", "contenido": "", "pdf_urls": []}

    soup = BeautifulSoup(html_content, "html.parser")

    # Extraer encabezado principal con prioridad h1 > h2 > h3 > title
    title_tag = soup.find(["h1", "h2", "h3"]) or soup.find("title")
    titulo = title_tag.get_text(strip=True) if title_tag else ""

    # Extraer parrafos y contenido descriptivo
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    contenido = "\n".join(paragraphs)

    # Extraer enlaces a PDFs adjuntos
    pdf_urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            pdf_urls.append(href)

    return {
        "titulo": titulo,
        "contenido": contenido,
        "pdf_urls": pdf_urls,
        "num_parrafos": len(paragraphs)
    }


def download_alert_pdf(pdf_url: str, save_path: Path, timeout: int = 15) -> bool:
    """
    Descarga un PDF de alerta de farmacovigilancia a la carpeta local.
    """
    try:
        resp = requests.get(pdf_url, headers=DEFAULT_HEADERS, timeout=timeout, stream=True)
        if resp.status_code == 200 and "application/pdf" in resp.headers.get("Content-Type", ""):
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("PDF descargado correctamente en: %s", save_path)
            return True
        else:
            logger.warning("No se pudo descargar PDF (%d): %s", resp.status_code, pdf_url)
            return False
    except Exception as exc:
        logger.error("Error al descargar PDF desde '%s': %s", pdf_url, exc)
        return False


# ============================================================================
# 3. PUNTO DE ENTRADA POR LINEA DE COMANDOS
# ============================================================================

def main(argv: Optional[List[str]] = None) -> None:
    """Analiza las alertas HTML locales y consulta openFDA, guardando las respuestas en disco."""
    parser = argparse.ArgumentParser(description="Analiza alertas HTML de DIGEMID y consulta openFDA")
    parser.add_argument("--farmacos", nargs="*", default=[],
                        help="Nombres de farmacos en ingles para consultar openFDA")
    parser.add_argument("--html-dir", type=Path, default=RAW_DIGEMID_DIR,
                        help="Carpeta con alertas HTML de DIGEMID descargadas")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    html_files = sorted(args.html_dir.glob("*.html"))
    logger.info("Alertas HTML locales encontradas en %s: %d", args.html_dir, len(html_files))
    for p in html_files:
        r = parse_html_alert(p.read_text(encoding="utf-8", errors="ignore"))
        logger.info("Alerta %s | titulo=%r | parrafos=%d | pdfs=%d | caracteres=%d",
                    p.name, r["titulo"], r.get("num_parrafos", 0), len(r["pdf_urls"]), len(r["contenido"]))

    RAW_OPENFDA_DIR.mkdir(parents=True, exist_ok=True)
    for f in args.farmacos:
        lab = scrape_openfda_label(f)
        logger.info("openFDA label %s | encontrado=%s | boxed_warning=%d caracteres",
                    f, lab.get("encontrado"), len(lab.get("boxed_warning", "")))
        stem = f.lower().replace(" ", "_")
        (RAW_OPENFDA_DIR / f"label_{stem}_live.json").write_text(
            json.dumps(lab, ensure_ascii=False, indent=2), encoding="utf-8")
        rec = scrape_openfda_recalls(f)
        logger.info("openFDA enforcement %s | retiros=%d", f, len(rec))
        (RAW_OPENFDA_DIR / f"recalls_{stem}_live.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()