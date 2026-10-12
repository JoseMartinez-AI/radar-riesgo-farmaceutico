# Radar de Riesgo Farmacéutico Perú-FDA
> **Sistema de priorización de señales de riesgo farmacológico para DIGEMID (MINSA)**  
> *Proyecto Productivo (PP) - Arquitectura de Datos Empresariales (Nivel Quinto / EFSRT IV)*

---

## 📌 1. Descripción del Proyecto
El **Radar de Riesgo Farmacéutico Perú-FDA** es una plataforma de análisis de Big Data y Minería de Datos que cruza automáticamente las señales de eventos adversos notificadas a la Food and Drug Administration (**FAERS / openFDA**) con el estado regulatorio nacional peruano (**DIGEMID - MINSA** y el **PNUME**).

El sistema prioriza objetivamente qué principios activos vigentes y de uso masivo en el sistema de salud peruano presentan un riesgo desproporcionado no advertido o crítico a nivel internacional.

---

## 🏗️ 2. Arquitectura del Repositorio

```text
Project-Radar/
├── .gitignore                    # Reglas de exclusión para datos y entornos
├── requirements.txt              # Dependencias de Python
├── README.md                     # Documentación técnica del proyecto
├── data/
│   ├── raw/                      # Data Lake (Zona cruda)
│   │   ├── faers/                # Archivos ASCII trimestrales FAERS (DEMO, DRUG, REAC...)
│   │   ├── digemid/              # Alertas y boletines PDF/HTML de DIGEMID
│   │   └── openfda/              # Respuestas JSON de drug/label y drug/enforcement
│   └── processed/                # Data Warehouse (Zona curada / SQLite o DuckDB)
│       └── radar_farmacovigilancia.db
├── src/
│   ├── config.py                 # Rutas, umbrales epidemiológicos y constantes
│   ├── database/
│   │   └── schema.py             # DDL del esquema en estrella (dimensiones y hechos)
│   ├── mining/
│   │   └── disproportionality.py # Algoritmos de PRR, ROR y Chi2 de Yates
│   ├── nlp/
│   │   └── extractor.py          # Extracción de PDF con pdfplumber y NLP
│   └── pipeline/
│       ├── seed_data.py          # Script de calibración y datos iniciales
│       └── ingest_faers.py       # Ingesta y joins masivos de FAERS
├── app/
│   └── dashboard.py              # Interfaz analítica en Streamlit
└── tests/                        # Suite de pruebas automatizadas (107 tests)
```

---

## ⚙️ 3. Algoritmos y Metodología de Minería de Datos

### 3.1. Señales de Desproporcionalidad (PRR & ROR)
A partir de la tabla de contingencia 2x2:
* **PRR (Proportional Reporting Ratio):**
  $$\text{PRR} = \frac{a / (a + b)}{c / (c + d)}$$
* **ROR (Reporting Odds Ratio):**
  $$\text{ROR} = \frac{a \times d}{b \times c}$$
* **Chi-cuadrado ($\chi^2$) con corrección de Yates:** Criterio de significancia estadística mínima para mitigar sesgos de reporte.

### 3.2. Criterio de Priorización Regulatoria
* **Riesgo Alto:** $\text{PRR} \ge 2.0$, $\chi^2 \ge 4.0$ y $a \ge 3$ casos reportados.
* **Riesgo Medio:** $\text{PRR} \ge 1.5$ o $\chi^2 \ge 3.0$ con $a \ge 2$ casos.
* **Cruce Perú:** Cruza la severidad del riesgo con la condición de **Vigente** en el Registro Sanitario de DIGEMID y su presencia en el **PNUME** (medicamentos esenciales de consumo masivo en hospitales públicos).

---

## 🚀 4. Instalación y Ejecución Local

### Paso 1: Configurar el entorno virtual
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate
```

### Paso 2: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Inicializar la Base de Datos y Sembrar Datos
```bash
python -m src.pipeline.seed_data
```

### Paso 4: Ejecutar la Suite de Pruebas Automatizadas
```bash
python -m pytest tests/ -v
```

### Paso 5: Levantar el Dashboard de DIGEMID
```bash
streamlit run app/dashboard.py
```

---

## 📊 5. Stack Tecnológico (100% Open Source y Local)
* **Lenguaje:** Python 3.11+
* **Almacenamiento Analítico:** SQLite / DuckDB (Esquema en estrella)
* **Big Data & Procesamiento:** pandas, DuckDB / PySpark local
* **NLP & Extracción:** `pdfplumber`, `spaCy` (modelo `es_core_news_md`)
* **Minería de Datos:** `scikit-learn`, `numpy`, `scipy`
* **Dashboard y Visualización:** `Streamlit`, `Plotly`
* **Testing:** `pytest` (98 tests automatizados)
