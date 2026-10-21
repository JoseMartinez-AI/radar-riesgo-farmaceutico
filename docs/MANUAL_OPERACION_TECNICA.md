# Manual de Operación Técnica (MOT)
## Radar de Riesgo Farmacéutico Perú-FDA
**Documento Técnico Operativo — Farmacovigilancia y Asuntos Regulatorios**  
*Versión: 1.0.0 | Fecha de emisión: Octubre 2026 | Sistema Operativo: Multiplataforma (Windows / Linux)*

---

## 1. Identificación y Alcance del Sistema

### 1.1. Propósito
El **Radar de Riesgo Farmacéutico Perú-FDA** es una plataforma de análisis de datos de farmacovigilancia y minería de señales que procesa datos masivos de reportes espontáneos internacionales de la Food and Drug Administration (**FDA FAERS / openFDA**) y los cruza con el marco regulatorio sanitario peruano emitido por **DIGEMID** (MINSA) y el **Petitorio Nacional Único de Medicamentos Esenciales (PNUME)**.

### 1.2. Destinatarios
- **Ingenieros de Datos / MLOps:** Responsables de ejecutar los pipelines de ingesta, cálculo estadístico y mantenimiento de la base de datos analítica.
- **Especialistas en Farmacovigilancia y Asuntos Regulatorios:** Usuarios analíticos que consumen el dashboard, interpretan señales de desproporcionalidad y descargan fichas de evidencia.
- **Administradores de TI:** Responsables de desplegar la aplicación, gestionar respaldos y asegurar la disponibilidad del servicio.

---

## 2. Requerimientos de Infraestructura y Entorno

### 2.1. Requisitos de Hardware
- **Procesador (CPU):** Mínimo 2 núcleos (Recomendado 4 núcleos a 2.0 GHz o superior para procesamiento en lotes de FAERS).
- **Memoria RAM:** Mínimo 4 GB (Recomendado 8 GB o 16 GB si se ingieren múltiples trimestres de FAERS en memoria).
- **Almacenamiento en Disco:** Mínimo 2 GB libres en disco SSD para entorno virtual y base de datos analítica.

### 2.2. Requisitos de Software
- **Sistema Operativo:** Windows 10/11 Pro, Windows Server, Ubuntu 20.04+ o Debian 11+.
- **Python:** Versión `3.11` o `3.12` (arquitectura x64).
- **Navegador Web:** Google Chrome, Microsoft Edge, Mozilla Firefox o Safari (versiones modernas con soporte ES6 y CSS Flexbox/Grid).
- **Git:** Versión 2.30+ para control de versiones.

---

## 3. Arquitectura de Datos y Estructura de Directorios

El sistema está estructurado bajo el paradigma de **Data Lake (Zona Cruda) + Data Warehouse (Zona Curada)**:

```text
Project-Radar/
├── .gitignore                    # Reglas de exclusión para datos y entornos
├── requirements.txt              # Dependencias fijadas del proyecto
├── README.md                     # Visión general del repositorio
├── MANUAL_OPERACION_TECNICA.md   # Este documento
├── data/
│   ├── raw/                      # Data Lake (Zona cruda)
│   │   ├── faers/                # Archivos ASCII trimestrales de FAERS (DEMO, DRUG, REAC)
│   │   ├── digemid/              # Alertas sanitarias y boletines HTML/PDF de DIGEMID
│   │   └── openfda/              # Respuestas JSON descargadas de drug/label y recalls
│   └── processed/                # Data Warehouse Analítico (SQLite)
│       └── radar_farmacovigilancia.db
├── src/
│   ├── config.py                 # Parámetros globales y umbrales epidemiológicos
│   ├── database/
│   │   └── schema.py             # DDL del esquema en estrella (dimensiones y hechos)
│   ├── mining/
│   │   └── disproportionality.py # Motor estadístico de PRR, ROR y Chi-cuadrado
│   ├── nlp/
│   │   └── extractor.py          # Extracción de texto y términos clínicos MedDRA
│   ├── pipeline/
│   │   ├── ingest_faers.py       # Ingesta y cruce masivo de tablas FAERS
│   │   ├── scraper.py            # Extracción y consulta HTTP de DIGEMID y openFDA
│   │   └── seed_data.py          # Inicializador idempotente y carga de calibración
│   └── reports/
│       └── exporter.py           # Generación de fichas de evidencia técnica en CSV (UTF-8 BOM)
├── app/
│   └── dashboard.py              # Aplicación web analítica Streamlit
└── tests/                        # Suite de 107 pruebas automatizadas con pytest
```

---

## 4. Instalación y Puesta en Marcha

### Paso 1: Clonar o posicionarse en el directorio del proyecto
```bash
cd "c:\Users\admin\Desktop\Project-Radar"
```

### Paso 2: Crear y activar el entorno virtual aislado (`.venv`)
*En Windows (PowerShell):*
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```
*En Linux / macOS (Bash):*
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar las dependencias oficiales
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Inicializar la base de datos analítica
Ejecuta el script de inicialización y calibración. Este comando creará el esquema en estrella y poblará las tablas con datos base de forma idempotente (sin duplicados):
```bash
python -m src.pipeline.seed_data
```
*Salida esperada:*
```text
Iniciando carga de datos de calibracion en ...\radar_farmacovigilancia.db
Base de datos inicializada correctamente.
  Farmacos insertados: 7
  Reacciones insertadas: 7
  Senales de riesgo calculadas: 9
  Textos de evidencia insertados: 6
  Regulaciones Peru insertadas: 7
Carga completada exitosamente.
```

### Paso 5: Validar la integridad del sistema (Testing)
Ejecuta la suite de pruebas unitarias e integración:
```bash
python -m pytest tests/ -v
```
*Resultado requerido:* `107 passed` (100% de pruebas aprobadas).

### Paso 6: Iniciar el Dashboard Analítico
```bash
streamlit run app/dashboard.py
```
El servidor se iniciará y estará accesible de forma local en:
👉 **`http://localhost:8501`**

---

## 5. Configuración y Calibración de Parámetros

Todos los parámetros operativos y epidemiológicos se configuran de manera centralizada en **`src/config.py`**.

### 5.1. Umbrales Epidemiológicos para Señales de Alerta
Para ajustar la sensibilidad del motor estadístico ante reportes de eventos adversos:

| Parámetro en `src/config.py` | Valor por Defecto | Descripción Técnica |
| :--- | :---: | :--- |
| `PRR_THRESHOLD_HIGH` | `2.0` | Umbral de Razón de Notificación Proporcional para clasificar señal de riesgo **Alto** (Criterio Evans et al. / FDA / OMS). |
| `PRR_THRESHOLD_MED` | `1.5` | Umbral de PRR para nivel **Medio** ($1.5 \le PRR < 2.0$). |
| `CHI2_THRESHOLD_HIGH` | `4.0` | Valor crítico de $\chi^2$ con corrección de Yates ($\alpha = 0.05, 1\text{ g.l.}$). Exige significancia estadística para riesgo **Alto**. |
| `CHI2_THRESHOLD_MED` | `3.0` | Valor crítico de $\chi^2$ para riesgo **Medio**. |
| `MIN_CASES_HIGH` | `3` | Número mínimo de reportes observados ($a \ge 3$) para evitar falsos positivos por muestras pequeñas. |
| `MIN_CASES_MED` | `2` | Mínimo de reportes para riesgo medio ($a \ge 2$). |

### 5.2. Rutas de Datos y Endpoints
- `SQLITE_DB_PATH`: Ruta absoluta/relativa a la base de datos analítica SQLite (`data/processed/radar_farmacovigilancia.db`).
- `RAW_FAERS_DIR`: Carpeta donde se depositan los archivos trimestrales de FAERS (`DEMO`, `DRUG`, `REAC`).
- `OPENFDA_LABEL_URL`: URL oficial de la API de openFDA para prospectos (`https://api.fda.gov/drug/label.json`).
- `OPENFDA_ENFORCEMENT_URL`: URL para retiros de mercado de la FDA (`https://api.fda.gov/drug/enforcement.json`).

---

## 6. Procedimientos Operativos del Pipeline de Datos

### 6.1. Procedimiento de Ingesta Masiva FAERS
1. Descargar el paquete ASCII trimestral oficial de FDA FAERS (ej. `faers_ascii_2024q2.zip`).
2. Extraer los archivos `DEMO24Q2.txt`, `DRUG24Q2.txt` y `REAC24Q2.txt` dentro de `data/raw/faers/2024-Q2/`.
3. Ejecutar el módulo de ingesta en lotes:
   ```bash
   python -m src.pipeline.ingest_faers
   ```
4. El proceso realiza:
   - Lectura optimizada por chunks (por defecto $50,000$ filas) con codificación `latin-1`.
   - Limpieza y estandarización a mayúsculas de los principios activos.
   - Normalización de términos de reacciones MedDRA.
   - Construcción de las tablas de contingencia $2 \times 2$.
   - Cálculo automático de $PRR$, $ROR$, $IC_{95\%}$ y $\chi^2$ de Yates.
   - Carga transaccional en `fact_senales_riesgo`.

### 6.2. Procedimiento de Extracción de Alertas Sanitarias DIGEMID
1. Ejecutar el scraper de alertas regulatorias:
   ```bash
   python -m src.pipeline.scraper
   ```
2. El script consulta los boletines de farmacovigilancia de DIGEMID, descarga los documentos PDF/HTML a `data/raw/digemid/`, procesa el contenido mediante el módulo de NLP (`src/nlp/extractor.py`) y actualiza `dim_regulacion_peru` y `fact_evidencia_texto`.

---

## 7. Guía de Operación del Dashboard de Usuario

Al ingresar a `http://localhost:8501`, el usuario interactúa con los siguientes componentes:

### 7.1. Cabecera Institucional (Banner Superior)
- **Título:** *Radar de Riesgo Farmacéutico Perú-FDA* (DIGEMID / Farmacovigilancia).
- **Selector de Ordenamiento:** Permite ordenar la tabla principal bajo 4 criterios:
  1. *Mayor riesgo a menor* (Predeterminado por severidad y $PRR$).
  2. *Menor riesgo a mayor*.
  3. *Nombre (A - Z)*.
  4. *Mayor n° reportes graves*.
- **Buscador en tiempo real:** Permite filtrar inmediatamente por principio activo escribiendo en el campo *Buscar principio activo...*.

### 7.2. Tabla de Fármacos (Columna Izquierda)
- Muestra el listado de principios activos priorizados con su badge de severidad (`● Alto`, `● Medio`, `● Bajo`) y su condición regulatoria en Perú (`✓ Vigente`, `✕ No vigente`).
- **Interacción:** Al hacer clic sobre cualquier fármaco, la fila se resalta con fondo verde suave (`#ebf5ee`) y actualiza instantáneamente el panel derecho.

### 7.3. Ficha Técnica Regulatoria (Columna Derecha)
- **Identificación:** Nombre del principio activo en mayúsculas, código ATC oficial y etiqueta de riesgo.
- **Métricas Epidemiológicas:** Cajas directas de `Señal PRR` y `Reportes graves`.
- **Advertencias Clave:** Lista sintetizada de reacciones adversas críticas extraídas de la literatura y fichas de openFDA/DIGEMID.
- **Cruce con Datos del Perú:** Estado del registro sanitario, inclusión en el PNUME y condición de alertas o retiro del mercado.
- **Exportar Ficha de Evidencia:** Botón verde institucional que genera y descarga al instante un archivo CSV codificado con UTF-8 BOM, garantizando compatibilidad total con Microsoft Excel sin distorsión de tildes o caracteres especiales.
- **Ver Ficha Completa en Ventana Emergente:** Abre una ventana flotante (`@st.dialog`) con el desglose matemático exhaustivo (Chi-cuadrado, Intervalos de Confianza al 95%, ROR) y el texto completo de las alertas oficiales.

---

## 8. Mantenimiento, Respaldo y Solución de Problemas (Troubleshooting)

### 8.1. Respaldo de la Base de Datos
La base de datos analítica es un único archivo SQLite autocontenido. Para respaldarla:
```powershell
# En Windows PowerShell
Copy-Item "data\processed\radar_farmacovigilancia.db" "data\processed\backup_radar_$(Get-Date -Format 'yyyyMMdd').db"
```

### 8.2. Diagnóstico de Problemas Frecuentes

#### Problema 1: `database is locked` en SQLite
- **Causa:** Hay un proceso previo de Python o Streamlit que mantiene una transacción abierta o no liberó el descriptor del archivo.
- **Solución:**
  1. Detener procesos huérfanos:
     ```powershell
     Get-Process -Name python | Stop-Process -Force
     ```
  2. Verificar que el archivo de base de datos no esté abierto en visores externos como DB Browser for SQLite en modo exclusivo.

#### Problema 2: Error de puerto ocupado `Port 8501 is already in use`
- **Causa:** Otra instancia de Streamlit está corriendo en segundo plano.
- **Solución:**
  1. Identificar el PID que escucha en el puerto 8501:
     ```powershell
     netstat -ano | findstr 8501
     ```
  2. Finalizar el proceso por su PID o arrancar Streamlit en un puerto alternativo:
     ```bash
     streamlit run app/dashboard.py --server.port 8502
     ```

#### Problema 3: Error de codificación al procesar archivos FAERS (`UnicodeDecodeError`)
- **Causa:** Los archivos FAERS oficiales de la FDA están codificados en `latin-1` (ISO-8859-1), no en `utf-8`.
- **Solución:** Asegurarse de que el script de lectura especifique `encoding='latin-1'` y delimitador `sep='$'`, tal como está implementado en `src/pipeline/ingest_faers.py`.

---

## 9. Registro de Pruebas y Control de Calidad

Para validar cualquier cambio antes de pasar a producción:
```bash
# 1. Validación de sintaxis
python -m py_compile app/dashboard.py
python -m py_compile src/config.py

# 2. Ejecución completa del banco de pruebas
python -m pytest tests/ --durations=10
```

Todas las pruebas deben concluir exitosamente (`107 passed`). Si algún test falla, revisar el reporte detallado arrojado por `pytest` antes de realizar despliegues.
