"""
app.py — Mikpho BI
───────────────────
Orquestador principal. ~120 líneas.
Responsabilidades:
  - Landing gate
  - Configuración de página y CSS
  - Sidebar
  - Carga y procesamiento de archivos
  - Definición de pestañas
  - Llamada a cada vista
  - Persistencia de session_state
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# ── config.py PRIMERO — fija matplotlib.use('Agg') antes de cualquier import ──
from config import (
    CSS_GLOBAL,
    AREA_DEFAULT_1,
    AREA_DEFAULT_2,
    FILA_HEADER_DEFAULT,
    MIN_PORCENTAJE_DEFAULT,
)

from landing import mostrar_landing
from utils.parser import obtener_hojas, procesar_proyecto, construir_df_tiempos
from vistas.tab_analisis    import mostrar_tab_analisis
from vistas.tab_comparacion import mostrar_tab_comparacion
from vistas.tab_gantt       import mostrar_tab_gantt
from vistas.tab_avance      import mostrar_tab_avance
from vistas.tab_curva_s     import mostrar_tab_curva_s


# ── LANDING GATE ──────────────────────────────────────────────────────────────
if "mostrar_app" not in st.session_state:
    st.session_state["mostrar_app"] = False

if not st.session_state["mostrar_app"]:
    mostrar_landing()
    st.stop()


# ── CONFIGURACIÓN DE PÁGINA ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Mikpho Intelligence System",
    layout="wide",
    page_icon="🏗️",
)
st.markdown(CSS_GLOBAL, unsafe_allow_html=True)
st.title("🏗️ Mikpho Construcciones — Sistema de Control y BI")
st.markdown("---")


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Parámetros Base")
    area_1 = st.number_input("Área Proyecto 1 (m²)", min_value=1.0, value=AREA_DEFAULT_1)
    area_2 = st.number_input("Área Proyecto 2 (m²)", min_value=1.0, value=AREA_DEFAULT_2)
    st.markdown("---")
    st.subheader("🔧 Calibrador de Datos")
    fila_encabezado = st.number_input(
        "Fila de títulos en Excel",
        min_value=0,
        value=FILA_HEADER_DEFAULT,
        step=1,
    )


# ── CARGA DE ARCHIVOS ─────────────────────────────────────────────────────────
st.markdown("### 📂 Carga de Presupuestos")
archivos_subidos = st.file_uploader(
    "Arrastra 1 o 2 Presupuestos (.xlsx)",
    type=["xlsx"],
    accept_multiple_files=True,
)

if not archivos_subidos:
    st.info("👆 Sube al menos un archivo Excel para comenzar el análisis.")
    st.stop()


# ── DETECCIÓN DE HOJAS Y MAPEO DE COLUMNAS ────────────────────────────────────
hojas_disponibles = obtener_hojas(archivos_subidos[0])

if len(hojas_disponibles) > 1:
    st.info(f"📋 Se detectaron **{len(hojas_disponibles)} hojas**. Selecciona cuál usar:")
    hoja_seleccionada = st.selectbox("Hoja activa:", options=hojas_disponibles, index=0)
else:
    hoja_seleccionada = hojas_disponibles[0]

# Cargar solo encabezados para el mapeo de columnas
import pandas as pd
try:
    df_base = pd.read_excel(
        archivos_subidos[0],
        sheet_name=hoja_seleccionada,
        header=fila_encabezado,
        nrows=0,
    )
except ValueError:
    st.error(
        f"❌ La hoja **'{hoja_seleccionada}'** no tiene suficientes filas. "
        f"Ajusta el **Calibrador de Datos** en el sidebar a un valor menor."
    )
    st.stop()

with st.expander("🛠️ Mapeo de Columnas (aplica para todos los archivos)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        col_cap = st.selectbox(
            "Columna de Capítulos:",
            df_base.columns,
            index=1 if len(df_base.columns) > 1 else 0,
        )
    with c2:
        col_val = st.selectbox(
            "Columna de Costos:",
            df_base.columns,
            index=len(df_base.columns) - 1,
        )


# ── PROCESAMIENTO DE ARCHIVOS ─────────────────────────────────────────────────
datos_proyectos = []
areas = [area_1, area_2]

for i, archivo in enumerate(archivos_subidos[:2]):
    hojas_arch = obtener_hojas(archivo)
    hoja_arch  = hoja_seleccionada if hoja_seleccionada in hojas_arch else hojas_arch[0]

    resultado = procesar_proyecto(
        archivo         = archivo,
        hoja            = hoja_arch,
        fila_encabezado = fila_encabezado,
        col_cap         = col_cap,
        col_val         = col_val,
        area            = areas[i],
        nombre          = archivo.name,
    )

    if resultado is None:
        st.error(
            f"❌ Las columnas **'{col_cap}'** o **'{col_val}'** no se encontraron "
            f"en **{archivo.name}**. Revisa el mapeo."
        )
    else:
        datos_proyectos.append(resultado)

if not datos_proyectos:
    st.error("❌ No se pudo procesar ningún archivo. Verifica la fila de encabezado y el mapeo.")
    st.stop()

p1 = datos_proyectos[0]


# ── SIDEBAR: RESUMEN DE PROYECTOS CARGADOS ────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.subheader("📋 Resumen Cargado")
    for p in datos_proyectos:
        nombre_s = p['nombre'].replace(".xlsx", "").replace(".xls", "").strip()
        st.markdown(f"""
        <div style="background-color:#1f2937; padding:12px; border-radius:8px;
                    border-left: 4px solid #00f2fe; margin-bottom:12px;">
            <p style="color:#00f2fe; font-weight:bold; margin:0; font-size:13px">
                🏗️ {nombre_s}
            </p>
            <p style="color:#d1d5db; margin:4px 0 0 0; font-size:12px">
                💰 <b>$ {p['total']:,.0f}</b>
            </p>
            <p style="color:#d1d5db; margin:2px 0 0 0; font-size:12px">
                📐 <b>$ {p['m2']:,.0f} / m²</b>
            </p>
            <p style="color:#d1d5db; margin:2px 0 0 0; font-size:12px">
                🏢 <b>{p['area']:,.0f} m²</b>
            </p>
            <p style="color:#d1d5db; margin:2px 0 0 0; font-size:12px">
                📦 <b>{len(p['df_grp'])} capítulos</b>
            </p>
        </div>
        """, unsafe_allow_html=True)


# ── SLIDER DE RELEVANCIA ──────────────────────────────────────────────────────
min_porcentaje = st.slider(
    "Filtro de Relevancia (%):",
    0.0, 5.0,
    MIN_PORCENTAJE_DEFAULT,
    0.1,
)


# ── CRONOGRAMA BASE (session_state) ───────────────────────────────────────────
df_tiempos = construir_df_tiempos(p1['df_grp'], col_cap, col_val, min_porcentaje)

if "datos_editados" not in st.session_state:
    st.session_state["datos_editados"] = df_tiempos.copy()
else:
    caps_actuales  = set(df_tiempos[col_cap].tolist())
    caps_guardadas = set(
        st.session_state["datos_editados"][col_cap].tolist()
        if col_cap in st.session_state["datos_editados"].columns
        else []
    )
    if caps_actuales != caps_guardadas:
        st.session_state["datos_editados"] = df_tiempos.copy()

datos_editados = st.session_state["datos_editados"]


# ── PESTAÑAS ──────────────────────────────────────────────────────────────────
if len(datos_proyectos) == 2:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Análisis Individual",
        "⚖️ Comparación",
        "🗓️ Gantt",
        "📈 Control de Avance",
        "📉 Curva S",
    ])
else:
    tab1, tab3, tab4, tab5 = st.tabs([
        "📊 Análisis Individual",
        "🗓️ Gantt",
        "📈 Control de Avance",
        "📉 Curva S",
    ])
    tab2 = None


# ── VISTAS ────────────────────────────────────────────────────────────────────
with tab1:
    mostrar_tab_analisis(p1, col_cap, col_val, min_porcentaje, datos_editados)

if tab2 is not None:
    with tab2:
        mostrar_tab_comparacion(
            datos_proyectos[0],
            datos_proyectos[1],
            col_cap,
            col_val,
            min_porcentaje,
        )

with tab3:
    st.session_state["datos_editados"] = mostrar_tab_gantt(
        datos_editados, col_cap, col_val, p1['nombre']
    )
    datos_editados = st.session_state["datos_editados"]

with tab4:
    mostrar_tab_avance(datos_editados, col_cap, col_val)

with tab5:
    mostrar_tab_curva_s(datos_editados, col_cap, col_val)