# Radar de Riesgo Farmacéutico Perú-FDA
> **Sistema de priorización de señales de riesgo farmacológico para DIGEMID (MINSA)**  
> *Proyecto Productivo (PP) — Arquitectura de Datos Empresariales*

---

## 📌 Descripción del Proyecto
El **Radar de Riesgo Farmacéutico Perú-FDA** es una plataforma de análisis de Big Data y Minería de Datos que cruza automáticamente las señales de eventos adversos notificadas a la Food and Drug Administration (**FAERS / openFDA**) con el estado regulatorio nacional peruano (**DIGEMID - MINSA** y el **PNUME**).

El sistema prioriza objetivamente qué principios activos vigentes y de uso masivo en el sistema de salud peruano presentan un riesgo desproporcionado no advertido o crítico a nivel internacional.

---

## 🏗️ Arquitectura del Repositorio

```text
Project-Radar/
├── .env.example                  # Plantilla de variables de entorno (copiar a .env)
├── .gitignore                    # Reglas de exclusión para datos y entornos
├── pyproject.toml                # Metadatos del proyecto, deps y config de pytest
├── requirements.txt              # Dependencias pip (alternativa a pyproject.toml)
├── README.md                     # Documentación técnica del proyecto
│
├── data/                         # ── CAPA DE DATOS (no versionada) ──────────────
│   ├── raw/                      # Data Lake — Zona cruda
│   │   ├── faers/                # Archivos ASCII trimestrales de FAERS (ZIP/TXT)
│   │   ├── digemid/              # Alertas y boletines PDF/HTML de DIGEMID
│   │   └── openfda/              # Respuestas JSON de drug/label y enforcement
│   └── processed/                # Data Warehouse — Zona curada
│       └── radar_farmacovigilancia.db  # SQLite (esquema en estrella)
│
├── src/                          # ── CÓDIGO FUENTE ───────────────────────────────
│   ├── __init__.py
│   ├── config.py                 # Rutas, umbrales y constantes (soporte .env)
│   ├── database/
│   │   ├── __init__.py           # Re-exporta get_engine, init_database
│   │   └── schema.py             # DDL del esquema dimensional (dim/fact)
│   ├── mining/
│   │   ├── __init__.py           # Re-exporta compute_signal_metrics
│   │   └── disproportionality.py # Algoritmos PRR, ROR, Chi2 de Yates, IC95%
│   ├── nlp/
│   │   ├── __init__.py           # Re-exporta clean_clinical_text, detect_risk_signals
│   │   └── extractor.py          # Extracción de PDF, NLP y detección de señales
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── ingest_faers.py       # Ingesta de archivos ASCII trimestrales de FAERS
│   │   ├── scraper.py            # Recolección desde openFDA API y HTML de DIGEMID
│   │   ├── load_evidence.py      # Carga de evidencias de texto al Data Warehouse
│   │   └── seed_data.py          # ETL de calibración con datos iniciales
│   ├── reports/
│   │   ├── __init__.py           # Re-exporta generate_csv_bytes, build_signal_report
│   │   └── exporter.py           # Generación de reportes CSV (UTF-8-BOM)
│   └── utils/
│       ├── __init__.py           # Re-exporta setup_logging, get_logger
│       └── logging_setup.py      # Configuración centralizada de logging
│
├── app/
│   ├── __init__.py
│   └── dashboard.py              # Interfaz analítica en Streamlit
│
├── tests/                        # ── SUITE DE PRUEBAS ────────────────────────────
│   ├── conftest.py               # Fixtures globales y configuración de sys.path
│   ├── __init__.py
│   ├── test_database.py          # Tests de integración del Data Warehouse
│   ├── test_disproportionality.py # Tests unitarios de PRR/ROR/Chi2
│   ├── test_exporter.py          # Tests del exportador CSV
│   ├── test_nlp_extractor.py     # Tests del módulo NLP
│   └── test_scraper.py           # Tests del scraper
│
└── docs/                         # ── DOCUMENTACIÓN ───────────────────────────────
    ├── MANUAL_OPERACION_TECNICA.md
    ├── informe/
    │   ├── Informe_de_Proyecto.docx
    │   └── Anexo_2A_-_Bitácora_de_Actividades.xlsx
    ├── scripts_exploratorios/    # Scripts de validación usados durante desarrollo
    ├── evidencias_ejecucion/     # Logs de salida de ejecuciones documentadas
    └── datos_sinteticos/         # ZIPs con datos sintéticos de prueba
```

---

## ⚙️ Algoritmos y Metodología de Minería de Datos

### Señales de Desproporcionalidad (PRR & ROR)
A partir de la tabla de contingencia 2×2:

| | Reacción de Interés | Otras Reacciones |
|---|---|---|
| **Fármaco de Interés** | a | b |
| **Otros Fármacos** | c | d |

- **PRR:** `a/(a+b) ÷ c/(c+d)` — señal de sobrerrepresentación de la reacción
- **ROR:** `(a×d) / (b×c)` — odds ratio de reporte
- **Chi²** con corrección de Yates — significancia estadística mínima

### Criterio de Priorización Regulatoria
| Nivel | PRR | Chi² | Casos (a) |
|---|---|---|---|
| **Alto** | ≥ 2.0 | ≥ 4.0 | ≥ 3 |
| **Medio** | ≥ 1.5 | ≥ 3.0 | ≥ 2 |
| **Bajo** | < 1.5 | — | — |

---

## 🚀 Instalación y Ejecución Local

### 1. Configurar entorno virtual
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno (opcional)
```bash
cp .env.example .env
# Editar .env con los valores locales deseados
```

### 4. Inicializar la Base de Datos con datos de calibración
```bash
python -m src.pipeline.seed_data
```

### 5. Ejecutar la Suite de Pruebas Automatizadas
```bash
python -m pytest tests/ -v
# Con cobertura:
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### 6. Levantar el Dashboard de DIGEMID
```bash
streamlit run app/dashboard.py
```

### 7. Ingesta de un trimestre real de FAERS (opcional)
```bash
python -m src.pipeline.ingest_faers \
    data/raw/faers/2024Q2.zip 2024 Q2 \
    --pares "VALPROATO DE SODIO:MALFORMACIONES CONGENITAS" "CLOZAPINA:AGRANULOCITOSIS"
```

---

## 📊 Stack Tecnológico (100% Open Source y Local)

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11+ |
| Data Warehouse | SQLite (esquema en estrella) |
| Procesamiento | pandas, numpy |
| NLP & Extracción | pdfplumber, BeautifulSoup4 |
| Minería de Datos | scipy, scikit-learn |
| Dashboard | Streamlit, Plotly |
| Testing | pytest, pytest-cov |
| Configuración | python-dotenv, pyproject.toml |

---

## 🔬 Fármacos Monitoreados (Calibración Inicial)

| Principio Activo | ATC | Nivel de Riesgo | Estado DIGEMID |
|---|---|---|---|
| Valproato de Sodio | N03AG01 | **Alto** | Alerta Emitida |
| Isotretinoína | D10BA01 | **Alto** | Alerta Emitida |
| Clozapina | N05AH02 | **Alto** | Alerta Emitida |
| Amiodarona | C01BD01 | **Alto** | En Revisión |
| Domperidona | A03FA03 | **Medio** | En Revisión |
| Fenilbutazona | M01AA01 | **Bajo** | Cancelado |
| Metformina | A10BA02 | **Bajo** | Normal |

---

*Sistema de análisis regulatorio basado en datos de FAERS / openFDA / DIGEMID. Los datos de calibración son representativos y no constituyen reportes clínicos oficiales.*
