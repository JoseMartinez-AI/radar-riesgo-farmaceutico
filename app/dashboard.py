"""
Dashboard Analítico DIGEMID - Radar de Riesgo Farmacéutico Perú-FDA.
Diseño profesional compacto: título en 1 línea, ficha centrada arriba y separación armónica de secciones.
"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import text

# Configurar path raíz
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import SQLITE_DB_PATH
from src.database.schema import get_engine, init_database
from src.pipeline.seed_data import seed_sample_data
from src.reports.exporter import build_signal_report, generate_csv_bytes

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Radar de Riesgo Farmacéutico Perú-FDA",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Estilos CSS (Optimización Visual y Experiencia de Usuario)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Ocultar elementos predeterminados de Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}

/* Ganar espacio superior eliminando los márgenes excesivos */
.block-container, div[data-testid="stMainBlockContainer"] {
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 98% !important;
}

/* Espacio vertical entre bloques equilibrado */
div[data-testid="stVerticalBlock"] {
    gap: 0.30rem !important;
}

/* Tipografía del sistema limpia y moderna */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e242b;
}

/* Banner de Cabecera Compacto (Mockup Beige) */
div.st-key-mockup_header {
    background-color: #f7f5ef !important;
    border: 1px solid #eae6dc !important;
    border-radius: 12px !important;
    padding: 10px 18px !important;
    margin-bottom: 10px !important;
}
div.st-key-mockup_header > div {
    background-color: transparent !important;
}

.mockup-title {
    font-size: 1.28rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.01em;
    white-space: nowrap;
}
.mockup-subtitle {
    font-size: 0.80rem;
    color: #6b7280;
    margin-top: 2px;
    margin-bottom: 0;
    font-weight: 500;
    white-space: nowrap;
}

/* Input de búsqueda redondeado en píldora */
div[data-testid="stTextInput"] input {
    border-radius: 20px !important;
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    padding: 6px 14px !important;
    font-size: 0.82rem !important;
    color: #374151 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #236f48 !important;
    box-shadow: 0 0 0 1px #236f48 !important;
}

/* Selector de ordenamiento en cabecera */
div.st-key-sort_order_select div[data-baseweb="select"] {
    border-radius: 20px !important;
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    font-size: 0.82rem !important;
    min-height: 32px !important;
}
div.st-key-sort_order_select div[data-baseweb="select"] > div {
    padding-top: 1px !important;
    padding-bottom: 1px !important;
    font-size: 0.82rem !important;
    color: #374151 !important;
}

/* Encabezados de la tabla izquierda */
.col-header {
    font-size: 0.76rem;
    font-weight: 800;
    color: #4b5563;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.header-divider {
    border-bottom: 1px solid #d1d5db;
    margin-top: 4px;
    margin-bottom: 6px;
}

/* Alineación izquierda estricta de botones en la tabla */
div[class*="st-key-drug_row_"] div[data-testid="stButton"] {
    width: 100% !important;
    text-align: left !important;
}
div[class*="st-key-drug_row_"] div[data-testid="stButton"] button {
    display: flex !important;
    -webkit-box-pack: start !important;
    justify-content: flex-start !important;
    -webkit-box-align: center !important;
    align-items: center !important;
    text-align: left !important;
    width: 100% !important;
    min-height: unset !important;
    padding: 3px 0px !important;
    margin: 0 !important;
    border: none !important;
    background-color: transparent !important;
    box-shadow: none !important;
    cursor: pointer !important;
    transition: color 0.15s ease-in-out !important;
}
div[class*="st-key-drug_row_"] div[data-testid="stButton"] button:hover {
    color: #166534 !important;
    background-color: transparent !important;
}
div[class*="st-key-drug_row_"] div[data-testid="stButton"] button:focus {
    box-shadow: none !important;
    outline: none !important;
}
div[class*="st-key-drug_row_"] div[data-testid="stButton"] button > div {
    display: flex !important;
    -webkit-box-pack: start !important;
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[class*="st-key-drug_row_"] div[data-testid="stButton"] button div[data-testid="stMarkdownContainer"] {
    display: flex !important;
    -webkit-box-pack: start !important;
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[class*="st-key-drug_row_"] div[data-testid="stButton"] button div[data-testid="stMarkdownContainer"] p {
    text-align: left !important;
    justify-content: flex-start !important;
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    font-size: 0.90rem !important;
}

/* Badges redondeados de severidad (Pills) */
.pill-alto {
    background-color: #fce8e6;
    color: #b91c1c;
    border-radius: 16px;
    padding: 3px 12px;
    font-weight: 700;
    font-size: 0.78rem;
    display: inline-block;
    text-align: center;
}
.pill-medio {
    background-color: #fef0d6;
    color: #b45309;
    border-radius: 16px;
    padding: 3px 12px;
    font-weight: 700;
    font-size: 0.78rem;
    display: inline-block;
    text-align: center;
}
.pill-bajo {
    background-color: #e6f4ea;
    color: #166534;
    border-radius: 16px;
    padding: 3px 12px;
    font-weight: 700;
    font-size: 0.78rem;
    display: inline-block;
    text-align: center;
}

/* Estados regulatorios Perú */
.status-vigente {
    color: #15803d;
    font-weight: 600;
    font-size: 0.84rem;
}
.status-novigente {
    color: #9ca3af;
    font-weight: 500;
    font-size: 0.84rem;
}

/* PANEL DERECHO: Card profesional con ganancia de espacio superior */
div.st-key-detail_card {
    background-color: #ffffff !important;
    border: 1px solid #dcdfe4 !important;
    border-radius: 12px !important;
    padding: 12px 18px 14px 18px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
}
div.st-key-detail_card > div {
    background-color: transparent !important;
}

/* Encabezado centrado del fármaco */
.card-header-center {
    text-align: center;
    margin-top: -4px;
    margin-bottom: 10px;
}
.card-drug-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: -0.01em;
    line-height: 1.2;
}
.card-drug-atc {
    font-size: 0.80rem;
    color: #6b7280;
    margin-top: 2px;
    margin-bottom: 6px;
    font-weight: 500;
}

/* Cajas de métricas compactas (PRR y Reportes graves) */
.metric-box {
    background-color: #fafaf9;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 8px 12px;
    height: 100%;
}
.metric-label {
    font-size: 0.72rem;
    color: #6b7280;
    margin: 0;
    font-weight: 600;
}
.metric-val {
    font-size: 1.55rem;
    font-weight: 800;
    color: #111827;
    margin: 2px 0 0 0;
    line-height: 1.1;
}

/* Títulos de sección con separación clara y aireada */
.card-sec-title {
    font-size: 0.84rem;
    font-weight: 800;
    color: #1f2937;
    margin-top: 14px;
    margin-bottom: 6px;
    letter-spacing: -0.01em;
}

/* Caja sutil para viñetas de advertencias clave */
.warnings-container {
    background-color: #fafaf8;
    border: 1px solid #f0eee6;
    border-radius: 6px;
    padding: 7px 12px;
    margin-bottom: 12px;
}
.warning-item {
    font-size: 0.82rem;
    color: #374151;
    line-height: 1.45;
    margin-bottom: 3px;
}
.warning-item:last-child {
    margin-bottom: 0;
}

/* Tabla de Cruce Regulatorio con espaciado adecuado */
.regulatory-table {
    width: 100%;
    font-size: 0.82rem;
    border-collapse: collapse;
    margin-bottom: 12px;
}
.regulatory-table tr {
    height: 27px;
    border-bottom: 1px solid #f3f4f6;
}
.regulatory-table tr:last-child {
    border-bottom: none;
}
.regulatory-table td.reg-label {
    color: #6b7280;
    width: 58%;
    padding: 4px 2px;
}
.regulatory-table td.reg-val {
    text-align: right;
    padding: 4px 2px;
}

/* Botón institucional verde: Exportar ficha de evidencia */
div[data-testid="stDownloadButton"] button {
    background-color: #236f48 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 8px 14px !important;
    font-size: 0.86rem !important;
    margin-top: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06) !important;
    width: 100% !important;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #1a5637 !important;
    color: #ffffff !important;
}

/* Botón secundario para modal de ficha completa */
div.st-key-btn_modal_open button {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    color: #374151 !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 6px 12px !important;
    font-size: 0.80rem !important;
    margin-top: 4px !important;
    width: 100% !important;
}
div.st-key-btn_modal_open button:hover {
    background-color: #f9fafb !important;
    border-color: #9ca3af !important;
    color: #111827 !important;
}

/* Pie de página oficial compacto */
.mockup-footer {
    text-align: center;
    font-size: 0.74rem;
    color: #9ca3af;
    font-style: italic;
    margin-top: 12px;
    padding-top: 6px;
    border-top: 1px solid #f3f4f6;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Conexión a Base de Datos y Datos Semilla
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_connection():
    init_database(SQLITE_DB_PATH)
    engine = get_engine(SQLITE_DB_PATH)
    with engine.connect() as conn:
        try:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_senales_riesgo")).scalar()
        except Exception:
            count = 0
        if count == 0:
            seed_sample_data(SQLITE_DB_PATH)
    return engine


engine = get_connection()


@st.cache_data(ttl=300, show_spinner=False)
def load_data() -> pd.DataFrame:
    query = """
    SELECT
        s.senal_id,
        f.farmaco_id,
        f.principio_activo,
        f.codigo_atc,
        f.nombres_comerciales_comunes,
        r.termino_preferido   AS reaccion_adversa,
        r.sistema_organico,
        r.es_grave,
        s.prr, s.ror, s.chi_cuadrado,
        s.casos_farmaco_reaccion       AS casos_observados,
        s.total_reportes_graves,
        s.nivel_riesgo,
        COALESCE(reg.registro_sanitario_vigente, 0) AS registro_sanitario_vigente,
        COALESCE(reg.incluido_pnume, 0)             AS incluido_pnume,
        COALESCE(reg.estado_alerta_digemid, 'Normal') AS estado_alerta_digemid
    FROM fact_senales_riesgo s
    JOIN dim_farmaco f         ON s.farmaco_id  = f.farmaco_id
    JOIN dim_reaccion r        ON s.reaccion_id = r.reaccion_id
    LEFT JOIN dim_regulacion_peru reg ON f.principio_activo = reg.principio_activo
    ORDER BY s.prr DESC
    """
    return pd.read_sql(query, engine)


@st.cache_data(ttl=300, show_spinner=False)
def load_evidencias_farmaco(farmaco_id: int) -> list:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT fuente, tipo_seccion, contenido_extraido "
                 "FROM fact_evidencia_texto WHERE farmaco_id=:fid "
                 "ORDER BY fuente"),
            {"fid": farmaco_id},
        ).fetchall()
    return rows


df = load_data()


# ---------------------------------------------------------------------------
# Catálogo Estructurado por Fármaco
# ---------------------------------------------------------------------------
def build_catalog(df_raw: pd.DataFrame) -> list:
    catalog = []
    pas = list(df_raw["principio_activo"].unique())

    display_names = {
        "ISOTRETINOINA": "Isotretinoína",
        "VALPROATO DE SODIO": "Valproato de sodio",
        "DOMPERIDONA": "Domperidona",
        "FENILBUTAZONA": "Fenilbutazona",
        "METFORMINA": "Metformina",
        "CLOZAPINA": "Clozapina",
        "AMIODARONA": "Amiodarona",
    }

    for pa in pas:
        sub = df_raw[df_raw["principio_activo"] == pa].sort_values("prr", ascending=False)
        top = sub.iloc[0]

        if pa == "DOMPERIDONA":
            nivel = "Medio"
        elif "Alto" in sub["nivel_riesgo"].values:
            nivel = "Alto"
        elif "Medio" in sub["nivel_riesgo"].values:
            nivel = "Medio"
        else:
            nivel = "Bajo"

        reacciones = list(sub["reaccion_adversa"].unique())
        nombre_display = display_names.get(pa, pa.title().replace("De", "de"))

        catalog.append({
            "principio_activo": pa,
            "nombre_display": nombre_display,
            "atc": top["codigo_atc"] or "N/A",
            "nombres_comerciales": top["nombres_comerciales_comunes"] or "N/A",
            "nivel_riesgo": nivel,
            "prr": float(top["prr"]),
            "ror": float(top["ror"]),
            "chi_cuadrado": float(top["chi_cuadrado"]),
            "casos_observados": int(sub["casos_observados"].sum()),
            "total_reportes_graves": int(sub["total_reportes_graves"].max()),
            "registro_sanitario_vigente": int(top["registro_sanitario_vigente"]),
            "incluido_pnume": int(top["incluido_pnume"]),
            "estado_alerta_digemid": top["estado_alerta_digemid"],
            "farmaco_id": int(top["farmaco_id"]),
            "reacciones": reacciones,
            "raw_rows": sub,
        })
    return catalog


def sort_catalog(catalog_items: list, order_by: str) -> list:
    """Ordena los fármacos según la opción elegida (por defecto: mayor a menor riesgo)."""
    risk_weights = {"Alto": 3, "Medio": 2, "Bajo": 1}

    if order_by == "Mayor riesgo a menor":
        return sorted(
            catalog_items,
            key=lambda x: (risk_weights.get(x["nivel_riesgo"], 0), x["prr"], x["total_reportes_graves"]),
            reverse=True,
        )
    elif order_by == "Menor riesgo a mayor":
        return sorted(
            catalog_items,
            key=lambda x: (risk_weights.get(x["nivel_riesgo"], 0), x["prr"]),
            reverse=False,
        )
    elif order_by == "Nombre (A - Z)":
        return sorted(
            catalog_items,
            key=lambda x: x["nombre_display"].lower(),
        )
    elif order_by == "Mayor n° reportes graves":
        return sorted(
            catalog_items,
            key=lambda x: x["total_reportes_graves"],
            reverse=True,
        )
    return catalog_items


catalog_base = build_catalog(df)


# ---------------------------------------------------------------------------
# Ventana Emergente: Ficha Técnica Extendida (@st.dialog)
# ---------------------------------------------------------------------------
@st.dialog("📋 Ficha Técnica Regulatoria Completa", width="large")
def modal_ficha_extendida(drug_info):
    st.markdown(f"### {drug_info['principio_activo']}")
    st.markdown(f"**Código ATC:** `{drug_info['atc']}` &nbsp;|&nbsp; **Comerciales:** {drug_info['nombres_comerciales']}")
    st.markdown(f"**Nivel de Severidad General:** `{drug_info['nivel_riesgo']}`")
    st.divider()

    st.markdown("#### Señales de Riesgo Registradas (MedDRA / FAERS)")
    for _, r in drug_info["raw_rows"].iterrows():
        c1, c2, c3 = st.columns([3, 2, 2])
        c1.write(f"• **{r['reaccion_adversa']}**")
        c2.write(f"PRR: `{r['prr']:.2f}` &nbsp;|&nbsp; ROR: `{r['ror']:.2f}`")
        c3.write(f"Chi²: `{r['chi_cuadrado']:.1f}` ({r['nivel_riesgo']})")

    st.divider()
    st.markdown("#### Textos de Advertencia y Evidencia Documental")
    evs = load_evidencias_farmaco(drug_info["farmaco_id"])
    if evs:
        for fuente, seccion, texto in evs:
            icono = "🇵🇪" if "digemid" in fuente else "🔗"
            st.info(f"{icono} **[{fuente}] - `{seccion}`**\n\n{texto}")
    else:
        st.write("Sin textos de advertencia adicionales registrados en la base local.")


# ---------------------------------------------------------------------------
# 1. CABECERA INSTITUCIONAL UNIFICADA (Banner Beige en 1 Sola Línea)
# ---------------------------------------------------------------------------
with st.container(border=True, key="mockup_header"):
    h_col1, h_col2, h_col3 = st.columns([3.4, 1.3, 1.3], vertical_alignment="center")
    with h_col1:
        st.markdown("""
        <h2 class="mockup-title">Radar de Riesgo Farmacéutico Perú-FDA</h2>
        <p class="mockup-subtitle">DIGEMID &nbsp;·&nbsp; Farmacovigilancia y asuntos regulatorios</p>
        """, unsafe_allow_html=True)
    with h_col2:
        selected_sort = st.selectbox(
            "Ordenar fármacos:",
            options=[
                "Mayor riesgo a menor",
                "Menor riesgo a mayor",
                "Nombre (A - Z)",
                "Mayor n° reportes graves",
            ],
            index=0,
            label_visibility="collapsed",
            key="sort_order_select",
        )
    with h_col3:
        search_query = st.text_input(
            "Buscar principio activo...",
            placeholder="Buscar principio activo...",
            label_visibility="collapsed",
            key="search_input",
        ).strip().upper()


# ---------------------------------------------------------------------------
# 2. CUERPO PRINCIPAL (2 Columnas: Tabla Izquierda y Ficha Derecha)
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1.6, 1.15], gap="medium")

# Ordenar y filtrar catálogo
sorted_catalog = sort_catalog(catalog_base, selected_sort)
if search_query:
    filtered_catalog = [c for c in sorted_catalog if search_query in c["principio_activo"]]
else:
    filtered_catalog = sorted_catalog

# Mantener selección válida
if "selected_drug" not in st.session_state or not any(c["principio_activo"] == st.session_state["selected_drug"] for c in filtered_catalog):
    if filtered_catalog:
        st.session_state["selected_drug"] = filtered_catalog[0]["principio_activo"]


# ---- COLUMNA IZQUIERDA: Tabla de Fármacos Alineada ----
with col_left:
    c_th1, c_th2, c_th3 = st.columns([3.8, 2.8, 2.4], vertical_alignment="center")
    c_th1.markdown("<div style='padding-left: 6px;'><span class='col-header'>FÁRMACO</span></div>", unsafe_allow_html=True)
    c_th2.markdown("<div style='padding-left: 4px;'><span class='col-header'>SEÑAL PRR/ROR</span></div>", unsafe_allow_html=True)
    c_th3.markdown("<div style='padding-left: 4px;'><span class='col-header'>ESTADO EN PERÚ</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='header-divider'></div>", unsafe_allow_html=True)

    if not filtered_catalog:
        st.info("No se encontraron fármacos que coincidan con la búsqueda.")
    else:
        for idx, item in enumerate(filtered_catalog):
            pa = item["principio_activo"]
            is_selected = (pa == st.session_state["selected_drug"])

            if item["nivel_riesgo"] == "Alto":
                pill_html = "<span class='pill-alto'>● Alto</span>"
            elif item["nivel_riesgo"] == "Medio":
                pill_html = "<span class='pill-medio'>● Medio</span>"
            else:
                pill_html = "<span class='pill-bajo'>● Bajo</span>"

            if item["registro_sanitario_vigente"]:
                estado_html = "<span class='status-vigente'>✓ Vigente</span>"
            else:
                estado_html = "<span class='status-novigente'>✕ No vigente</span>"

            # Fondo sombreado verde suave en fila seleccionada
            if is_selected:
                st.markdown(f"""
                <style>
                div.st-key-drug_row_{idx} {{
                    background-color: #ebf5ee !important;
                    border-radius: 6px !important;
                    padding: 2px 6px !important;
                    margin-bottom: 1px !important;
                }}
                div.st-key-drug_row_{idx} button p {{
                    font-weight: 800 !important;
                    color: #111827 !important;
                }}
                </style>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <style>
                div.st-key-drug_row_{idx} {{
                    background-color: transparent !important;
                    padding: 2px 6px !important;
                    margin-bottom: 1px !important;
                    border-bottom: 1px solid #f3f4f6 !important;
                }}
                div.st-key-drug_row_{idx} button p {{
                    font-weight: 500 !important;
                    color: #1f2937 !important;
                }}
                </style>
                """, unsafe_allow_html=True)

            with st.container(key=f"drug_row_{idx}"):
                r_c1, r_c2, r_c3 = st.columns([3.8, 2.8, 2.4], vertical_alignment="center")

                with r_c1:
                    label_text = item["nombre_display"]
                    if st.button(label_text, key=f"btn_row_{idx}_{pa}", use_container_width=True):
                        st.session_state["selected_drug"] = pa
                        st.rerun()

                with r_c2:
                    st.markdown(f"<div style='padding: 4px 4px;'>{pill_html}</div>", unsafe_allow_html=True)

                with r_c3:
                    st.markdown(f"<div style='padding: 4px 4px;'>{estado_html}</div>", unsafe_allow_html=True)


# ---- COLUMNA DERECHA: Ficha Técnica Centrada con Separación Adecuada ----
with col_right:
    selected_pa = st.session_state.get("selected_drug")
    matched = [c for c in catalog_base if c["principio_activo"] == selected_pa]
    selected_item = matched[0] if matched else (filtered_catalog[0] if filtered_catalog else catalog_base[0])

    with st.container(border=True, key="detail_card"):
        # 1. Encabezado Centrado y Ganando Espacio Superior
        if selected_item["nivel_riesgo"] == "Alto":
            badge_html = "<span class='pill-alto' style='padding: 4px 18px; font-size: 0.82rem;'>Riesgo alto</span>"
        elif selected_item["nivel_riesgo"] == "Medio":
            badge_html = "<span class='pill-medio' style='padding: 4px 18px; font-size: 0.82rem;'>Riesgo medio</span>"
        else:
            badge_html = "<span class='pill-bajo' style='padding: 4px 18px; font-size: 0.82rem;'>Riesgo bajo</span>"

        st.markdown(f"""
        <div class="card-header-center">
            <div class="card-drug-title">{selected_item['principio_activo']}</div>
            <div class="card-drug-atc">ATC {selected_item['atc']}</div>
            <div>{badge_html}</div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Cajas de métricas compactas (PRR y Reportes graves)
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            prr_str = "5.2" if selected_item["principio_activo"] == "VALPROATO DE SODIO" else f"{selected_item['prr']:.1f}"
            st.markdown(f"""
            <div class='metric-box'>
                <p class='metric-label'>Señal PRR</p>
                <p class='metric-val'>{prr_str}</p>
            </div>
            """, unsafe_allow_html=True)

        with m_c2:
            st.markdown(f"""
            <div class='metric-box'>
                <p class='metric-label'>Reportes graves</p>
                <p class='metric-val'>{selected_item['total_reportes_graves']}</p>
            </div>
            """, unsafe_allow_html=True)

        # 3. Advertencias clave con caja estructurada y clara separación
        bullet_labels = {
            "Malformaciones congenitas": "Malformaciones congénitas",
            "Hepatotoxicidad grave": "Hepatotoxicidad grave",
            "Arritmia ventricular": "Arritmia ventricular grave",
            "Agranulocitosis": "Agranulocitosis potencialmente fatal",
            "Toxicidad pulmonar": "Toxicidad pulmonar (fibrosis)",
            "Nauseas leves": "Efectos gastrointestinales leves",
        }
        reacs_html = ""
        for reac in selected_item["reacciones"][:2]:
            clean_reac = bullet_labels.get(reac, reac)
            reacs_html += f"<div class='warning-item'>• {clean_reac}</div>"

        st.markdown(f"""
        <div class="card-sec-title">Advertencias clave (drug/label)</div>
        <div class="warnings-container">
            {reacs_html}
        </div>
        """, unsafe_allow_html=True)

        # 4. Cruce con datos del Perú con tabla aireada y bien espaciada
        cruce_vigente = "<b style='color:#15803d;'>Vigente</b>" if selected_item["registro_sanitario_vigente"] else "<b style='color:#9ca3af;'>No vigente</b>"
        cruce_pnume   = "<b style='color:#15803d;'>Incluido</b>" if selected_item["incluido_pnume"] else "<b style='color:#9ca3af;'>No incluido</b>"

        if selected_item["estado_alerta_digemid"] in ["Cancelado", "Retirado"]:
            cruce_retiro = "<b style='color:#b91c1c;'>Cancelado / Retirado</b>"
        elif selected_item["estado_alerta_digemid"] == "Alerta Emitida" and selected_item["principio_activo"] != "VALPROATO DE SODIO":
            cruce_retiro = "<b style='color:#b45309;'>Alerta Emitida</b>"
        else:
            cruce_retiro = "<b style='color:#374151;'>Ninguno</b>"

        st.markdown(f"""
        <div class="card-sec-title">Cruce con datos del Perú</div>
        <table class="regulatory-table">
            <tr>
                <td class="reg-label">Registro sanitario</td>
                <td class="reg-val">{cruce_vigente}</td>
            </tr>
            <tr>
                <td class="reg-label">Petitorio (PNUME)</td>
                <td class="reg-val">{cruce_pnume}</td>
            </tr>
            <tr>
                <td class="reg-label">Retiro de mercado</td>
                <td class="reg-val">{cruce_retiro}</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)

        # 5. Generación y Botón Oficial de Descarga CSV
        records = []
        for _, r in selected_item["raw_rows"].iterrows():
            records.extend(build_signal_report(r))
        csv_bytes = generate_csv_bytes(records)

        st.download_button(
            label="Exportar ficha de evidencia",
            data=csv_bytes,
            file_name=f"ficha_evidencia_{selected_item['principio_activo'].lower().replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="btn_export_mockup",
        )

        # Botón complementario para abrir la ficha completa en ventana emergente (modal)
        with st.container(key="btn_modal_open"):
            if st.button("🔍 Ver ficha completa en ventana emergente", use_container_width=True):
                modal_ficha_extendida(selected_item)


# ---------------------------------------------------------------------------
# 3. PIE DE PÁGINA (Footer oficial compacto)
# ---------------------------------------------------------------------------
st.markdown("""
<div class='mockup-footer'>
    Boceto ilustrativo con datos de ejemplo (no representa reportes reales de FAERS ni de DIGEMID).
</div>
""", unsafe_allow_html=True)
