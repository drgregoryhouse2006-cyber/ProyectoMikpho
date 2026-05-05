import streamlit as st
from landing import mostrar_landing
 
# Controla si ya entró a la app o sigue en la landing
if "mostrar_app" not in st.session_state:
    st.session_state["mostrar_app"] = False
 
# Mientras no haya pulsado "ABRIR SISTEMA", muestra la landing
if not st.session_state["mostrar_app"]:
    mostrar_landing()
    st.stop()           # detiene la ejecución del resto de app.py
# ── FIN DEL BLOQUE A PEGAR ─────────────────────────────────────────

import re
import unicodedata
import io
import zipfile
import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from datetime import date
from fpdf import FPDF


def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return unicodedata.normalize('NFKC', texto).strip()

def limpiar_valor_numerico(serie):
    def parsear(val):
        if pd.isna(val):
            return 0.0
        s = str(val).strip()
        if re.search(r'\d{1,3}(\.\d{3})+(,\d+)?$', s):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
        s = re.sub(r'[^\d.\-]', '', s)
        try:
            return float(s)
        except ValueError:
            return 0.0
    return serie.apply(parsear)

# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf(nombre_proyecto, total, m2, area, df_filtrado, col_cap, col_val):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # --- ENCABEZADO ---
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_y(10)
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(0, 242, 254)
    pdf.cell(0, 10, "REPORTE EJECUTIVO DE PROYECTO", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(0, 8, "Mikpho Construcciones - Sistema BI", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    # --- SECCIÓN 1: RESUMEN FINANCIERO ---
    pdf.set_text_color(0, 242, 254)
    pdf.set_font("Helvetica", 'B', 13)
    pdf.cell(0, 8, "1. Resumen Financiero", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(0, 242, 254)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    nombre_limpio = nombre_proyecto.replace(".xlsx", "").replace(".xls", "")
    datos_resumen = [
        ("Proyecto Analizado", nombre_limpio),
        ("Area Total Construida", f"{area:,.2f} m2"),
        ("Costo Total Estimado", f"$ {total:,.0f}"),
        ("Valor por Metro Cuadrado", f"$ {m2:,.0f}"),
    ]
    pdf.set_font("Helvetica", '', 11)
    for etiqueta, valor in datos_resumen:
        pdf.set_text_color(150, 150, 150)
        pdf.cell(80, 8, etiqueta + ":", new_x="END")
        pdf.set_text_color(220, 220, 220)
        pdf.cell(0, 8, valor, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # --- SECCIÓN 2: DESGLOSE DE CAPÍTULOS ---
    pdf.set_text_color(0, 242, 254)
    pdf.set_font("Helvetica", 'B', 13)
    pdf.cell(0, 8, "2. Desglose de Capitulos Principales", new_x="LMARGIN", new_y="NEXT")
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    pdf.set_fill_color(31, 41, 55)
    pdf.set_text_color(0, 242, 254)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(100, 8, "Capitulo", border=0, fill=True, new_x="END")
    pdf.cell(40, 8, "Costo ($)", align='R', border=0, fill=True, new_x="END")
    pdf.cell(30, 8, "Participacion", align='R', border=0, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", '', 10)
    for i, (_, row) in enumerate(df_filtrado.iterrows()):
        pdf.set_fill_color(20, 30, 48) if i % 2 == 0 else pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(210, 210, 210)
        capitulo = str(row[col_cap])[:55]
        costo = row[col_val]
        part = row['% Participación']
        pdf.cell(100, 7, capitulo, border=0, fill=True, new_x="END")
        pdf.cell(40, 7, f"$ {costo:,.0f}", align='R', border=0, fill=True, new_x="END")
        pdf.cell(30, 7, f"{part:.2f}%", align='R', border=0, fill=True, new_x="LMARGIN", new_y="NEXT")

    # --- GRÁFICA DE PARTICIPACIÓN ---
    pdf.ln(6)
    pdf.set_text_color(0, 242, 254)
    pdf.set_font("Helvetica", 'B', 13)
    pdf.cell(0, 8, "3. Grafica de Participacion por Capitulo", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(0, 242, 254)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    try:
        fig, ax = plt.subplots(figsize=(9, max(3, len(df_filtrado) * 0.4)))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1f2937')

        nombres = [str(n)[:40] for n in df_filtrado[col_cap]]
        valores = df_filtrado['% Participación'].tolist()
        colores = ['#00f2fe' if v == max(valores) else '#3b82f6' for v in valores]

        bars = ax.barh(nombres, valores, color=colores, edgecolor='none')
        ax.set_xlabel('% Participación', color='white', fontsize=9)
        ax.tick_params(colors='white', labelsize=8)
        ax.spines['bottom'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        for bar, val in zip(bars, valores):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f'{val:.1f}%', va='center', color='white', fontsize=8)

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)

        pdf.image(buf, x=20, w=170)
    except Exception:
        pass

    pdf.ln(10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", 'I', 9)
    pdf.cell(0, 8, f"Reporte generado automaticamente el: {date.today()}", align='C', new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())

# --- 1. CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="Mikpho Intelligence System", layout="wide", page_icon="🏗️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #1f2937; padding: 15px; border-radius: 10px;
        border: 1px solid #00f2fe; box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Mikpho Construcciones - Sistema de Control y BI")
st.markdown("---")

# --- 2. BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Parámetros Base")
    area_1 = st.number_input("Área Proyecto 1 (m²)", min_value=1.0, value=1250.0)
    area_2 = st.number_input("Área Proyecto 2 (m²)", min_value=1.0, value=1500.0)
    st.markdown("---")
    st.subheader("🔧 Calibrador de Datos")
    fila_encabezado = st.number_input("Fila de títulos en Excel", min_value=0, value=2, step=1)
    st.markdown("---")
    # El resumen se renderiza más abajo con render_sidebar_resumen()
    # una vez que datos_proyectos esté disponible

# Función para renderizar resumen en sidebar (se llama después de procesar)
def render_sidebar_resumen(datos_proyectos, col_cap, col_val):
    with st.sidebar:
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

        cap_top = datos_proyectos[0]['df_grp'].sort_values(col_val, ascending=False).iloc[0]
        st.markdown("**🔝 Capítulo más costoso:**")
        st.markdown(f"""
        <div style="background-color:#1f2937; padding:10px; border-radius:8px;
                    border-left: 4px solid #f59e0b; margin-bottom:8px;">
            <p style="color:#f59e0b; margin:0; font-size:12px; font-weight:bold">
                {str(cap_top[col_cap])[:40]}
            </p>
            <p style="color:#d1d5db; margin:4px 0 0 0; font-size:12px">
                $ {cap_top[col_val]:,.0f}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.caption(f"🕐 Actualizado: {date.today()}")

# --- 3. CARGA MÚLTIPLE DE ARCHIVOS ---
st.markdown("### 📂 Carga de Presupuestos")

col_upload, col_demo = st.columns([3, 1])
with col_upload:
    archivos_subidos = st.file_uploader("Arrastra 1 o 2 Presupuestos (.xlsx)", type=["xlsx"], accept_multiple_files=True)
with col_demo:
    st.markdown("<br>", unsafe_allow_html=True)
    modo_demo = st.button("🎮 Cargar Datos Demo", use_container_width=True)

# Resetear modo demo si el usuario sube archivos reales
if archivos_subidos:
    st.session_state["modo_demo_activo"] = False

def generar_datos_demo():
    """Genera un proyecto de construcción ficticio para demostración."""
    capitulos = [
        "Preliminares y Descapote",
        "Cimentación y Estructura",
        "Mampostería y Muros",
        "Cubierta e Impermeabilización",
        "Instalaciones Hidráulicas",
        "Instalaciones Eléctricas",
        "Acabados y Pintura",
        "Carpintería y Ventanería",
        "Obras Exteriores",
        "Equipos Especiales"
    ]
    costos = [
        45_000_000,
        320_000_000,
        180_000_000,
        95_000_000,
        75_000_000,
        68_000_000,
        120_000_000,
        85_000_000,
        42_000_000,
        55_000_000
    ]
    ejecutado = [100, 85, 70, 60, 45, 40, 20, 15, 5, 0]

    df_demo = pd.DataFrame({
        "Capítulo": capitulos,
        "Costo Total": costos,
        "% Ejecutado (Real)": ejecutado
    })
    return df_demo

if modo_demo:
    st.session_state["modo_demo_activo"] = True

if st.session_state.get("modo_demo_activo") and not archivos_subidos:
    st.info("🎮 **Modo Demo activo** — Explorando proyecto de ejemplo: *Edificio Residencial Mikpho Tower*")

    df_demo = generar_datos_demo()
    col_cap = "Capítulo"
    col_val = "Costo Total"

    costo_total_demo = df_demo[col_val].sum()
    area_demo = area_1
    valor_m2_demo = costo_total_demo / area_demo

    df_grp_demo = df_demo[[col_cap, col_val]].copy()
    df_grp_demo['Proyecto'] = "Mikpho Tower (Demo)"
    df_grp_demo['% Participación'] = (df_grp_demo[col_val] / costo_total_demo) * 100

    datos_proyectos = [{
        "nombre": "MikphoTower_Demo.xlsx",
        "df_grp": df_grp_demo,
        "total": costo_total_demo,
        "m2": valor_m2_demo,
        "area": area_demo
    }]

    min_porcentaje = st.slider("Filtro de Relevancia (%):", 0.0, 5.0, 1.0, 0.1)

    df_tiempos_demo = df_grp_demo[[col_cap, col_val]].copy()
    df_tiempos_demo["Fecha de Inicio"] = date.today()
    df_tiempos_demo["Días Estimados"] = [15, 90, 60, 30, 25, 20, 40, 30, 15, 20]
    df_tiempos_demo["% Ejecutado (Real)"] = df_demo["% Ejecutado (Real)"].values

    datos_editados = df_tiempos_demo.copy()

    render_sidebar_resumen(datos_proyectos, col_cap, col_val)

    p1 = datos_proyectos[0]

    st.success("✅ Datos demo cargados. Navega por las pestañas para explorar todas las funcionalidades.")

if archivos_subidos:
    try:
        # --- DETECCIÓN DE HOJAS ---
        hojas_disponibles = pd.ExcelFile(archivos_subidos[0]).sheet_names

        if len(hojas_disponibles) > 1:
            st.info(f"📋 Se detectaron **{len(hojas_disponibles)} hojas** en el archivo. Selecciona cuál usar:")
            hoja_seleccionada = st.selectbox(
                "Hoja activa:",
                options=hojas_disponibles,
                index=0
            )
        else:
            hoja_seleccionada = hojas_disponibles[0]

        df_base = pd.read_excel(archivos_subidos[0], sheet_name=hoja_seleccionada, header=fila_encabezado)
        df_base.columns = [limpiar_texto(c) for c in df_base.columns]
        df_base = df_base.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)

        with st.expander("🛠️ Mapeo de Columnas (Aplica para todos los archivos)", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                col_cap = st.selectbox("Columna de Capítulos:", df_base.columns, index=1 if len(df_base.columns) > 1 else 0)
            with c2:
                col_val = st.selectbox("Columna de Costos:", df_base.columns, index=len(df_base.columns) - 1)

        # Lógica de Pestañas
        tab_comparacion = None  # se asigna solo si hay 2 archivos
        if len(archivos_subidos) == 2:
            tabs = st.tabs(["📊 Análisis Individual", "⚖️ Comparación", "🗓️ Gantt", "📈 Control de Avance", "📉 Curva S"])
            tab_finanzas, tab_comparacion, tab_cronograma, tab_avance, tab_curva_s = tabs
        else:
            tabs = st.tabs(["📊 Análisis Individual", "🗓️ Gantt", "📈 Control de Avance", "📉 Curva S"])
            tab_finanzas, tab_cronograma, tab_avance, tab_curva_s = tabs

        # Procesamiento de Datos Base
        datos_proyectos = []
        for i, archivo in enumerate(archivos_subidos[:2]):
            hojas_arch = pd.ExcelFile(archivo).sheet_names
            hoja_arch = hoja_seleccionada if hoja_seleccionada in hojas_arch else hojas_arch[0]
            df = pd.read_excel(archivo, sheet_name=hoja_arch, header=fila_encabezado)
            df.columns = [limpiar_texto(c) for c in df.columns]
            df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)

            if col_cap not in df.columns or col_val not in df.columns:
                st.error(f"❌ Las columnas '{col_cap}' o '{col_val}' no se encontraron en **{archivo.name}**. Revisa el mapeo.")
                continue

            df[col_cap] = df[col_cap].apply(limpiar_texto)
            df = df[df[col_cap].str.strip() != ''].copy()
            df[col_val] = limpiar_valor_numerico(df[col_val])

            costo_total = df[col_val].sum()
            area_usar = area_1 if i == 0 else area_2
            valor_m2 = costo_total / area_usar if area_usar > 0 else 0

            df_grp = (
                df.groupby(col_cap, sort=False)[col_val]
                .sum()
                .reset_index()
            )
            df_grp = df_grp[df_grp[col_val] > 0]
            df_grp['Proyecto'] = archivo.name
            df_grp['% Participación'] = (df_grp[col_val] / costo_total) * 100 if costo_total > 0 else 0

            datos_proyectos.append({
                "nombre": archivo.name, "df_grp": df_grp, "total": costo_total, "m2": valor_m2, "area": area_usar
            })

        if not datos_proyectos:
            st.error("❌ No se pudo procesar ningún archivo. Verifica que la fila de encabezado y el mapeo de columnas sean correctos.")
            st.stop()

        p1 = datos_proyectos[0]

        # El slider se define ANTES de usarlo para construir df_tiempos
        min_porcentaje = st.slider("Filtro de Relevancia (%):", 0.0, 5.0, 1.0, 0.1)

        # Inicializar datos_editados con session_state para que persista entre pestañas
        df_tiempos = p1['df_grp'][p1['df_grp']['% Participación'] >= min_porcentaje][[col_cap, col_val]].copy()
        df_tiempos["Fecha de Inicio"] = date.today()
        df_tiempos["Días Estimados"] = 30
        df_tiempos["Días Estimados"] = df_tiempos["Días Estimados"].astype(int)
        df_tiempos["% Ejecutado (Real)"] = 0.0
        df_tiempos = df_tiempos.dropna(subset=[col_cap]).reset_index(drop=True)

        # Preservar ediciones del usuario entre reruns usando session_state
        if "datos_editados" not in st.session_state:
            st.session_state["datos_editados"] = df_tiempos.copy()
        else:
            # Si cambiaron los capítulos (nuevo archivo), resetear
            cols_actuales = set(df_tiempos[col_cap].tolist())
            cols_guardadas = set(st.session_state["datos_editados"][col_cap].tolist()) if col_cap in st.session_state["datos_editados"].columns else set()
            if cols_actuales != cols_guardadas:
                st.session_state["datos_editados"] = df_tiempos.copy()

        datos_editados = st.session_state["datos_editados"]

        # ==========================================
        # PESTAÑA 1: ANÁLISIS INDIVIDUAL Y PDF
        # ==========================================
        with tab_finanzas:
            nombre_limpio = p1['nombre'].replace(".xlsx", "").replace(".xls", "")
            st.subheader(f"Análisis del Proyecto: {nombre_limpio}")
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Costo Total", f"$ {p1['total']:,.0f}")
            col2.metric("📐 Valor por m²", f"$ {p1['m2']:,.0f}")
            col3.metric("🏢 Área", f"{p1['area']:,.2f} m²")

            df_filtrado = p1['df_grp'][p1['df_grp']['% Participación'] >= min_porcentaje].sort_values(col_val, ascending=False)

            # --- RESUMEN EJECUTIVO INTELIGENTE ---
            st.markdown("---")
            st.subheader("🧠 Resumen Ejecutivo")

            df_ord = df_filtrado.sort_values('% Participación', ascending=False)
            cap_mayor = df_ord.iloc[0][col_cap] if len(df_ord) > 0 else "N/A"
            pct_mayor = df_ord.iloc[0]['% Participación'] if len(df_ord) > 0 else 0
            costo_mayor = df_ord.iloc[0][col_val] if len(df_ord) > 0 else 0

            # Cuántos capítulos acumulan el 80%
            df_acum = df_ord.copy()
            df_acum['Acumulado'] = df_acum['% Participación'].cumsum()
            caps_80 = df_acum[df_acum['Acumulado'] <= 80]
            n_caps_80 = len(caps_80) + 1

            # Concentración: alerta si el top 1 supera el 40%
            alerta_concentracion = pct_mayor > 40

            c_res1, c_res2 = st.columns(2)
            with c_res1:
                st.info(f"""
**📌 Capítulo dominante**
**{cap_mayor}** representa el **{pct_mayor:.1f}%** del presupuesto total, 
equivalente a **$ {costo_mayor:,.0f}**.
""")
                st.info(f"""
**📊 Regla 80/20**
El **{int(pct_mayor)}%** superior del presupuesto está concentrado en 
**{n_caps_80} capítulo(s)** de {len(df_ord)} totales.
""")
            with c_res2:
                if alerta_concentracion:
                    st.warning(f"""
**⚠️ Alta Concentración Detectada**
El capítulo **{cap_mayor}** supera el 40% del presupuesto.
Considera desglosarlo para mayor control de costos.
""")
                else:
                    st.success(f"""
**✅ Distribución Saludable**
Ningún capítulo supera el 40% del presupuesto.
El proyecto tiene una buena distribución de costos.
""")
                st.info(f"""
**🏗️ Eficiencia por m²**
Con **{p1['area']:,.0f} m²** construidos, cada metro cuadrado 
tiene un costo promedio de **$ {p1['m2']:,.0f}**.
""")

            c_chart, c_table = st.columns([2, 1])
            with c_chart:
                fig_tree = px.treemap(df_filtrado, path=[col_cap], values=col_val, color=col_val, color_continuous_scale='teal')
                fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_tree, use_container_width=True)
            with c_table:
                df_display = df_filtrado[[col_cap, col_val, '% Participación']].copy()
                st.dataframe(df_display.style.format({col_val: "${:,.0f}", '% Participación': "{:.2f}%"}), height=400)

            st.markdown("---")
            st.subheader("📑 Reporte Gerencial")
            pdf_bytes = generar_pdf(p1['nombre'], p1['total'], p1['m2'], p1['area'], df_filtrado, col_cap, col_val)
            nombre_archivo_pdf = p1['nombre'].replace(".xlsx", "").replace(".xls", "").strip()
            st.download_button(
                label="⬇️ Descargar Reporte en PDF",
                data=pdf_bytes,
                file_name=f"Reporte_{nombre_archivo_pdf}.pdf",
                mime="application/pdf"
            )

            # --- EXPORT ZIP COMPLETO ---
            st.markdown("---")
            st.subheader("📦 Exportar Paquete Completo")
            st.caption("Descarga el PDF gerencial y el cronograma Excel en un solo archivo.")

            try:
                # Generar Excel del cronograma
                df_export_zip = datos_editados[[col_cap, "Fecha de Inicio", "Días Estimados", "% Ejecutado (Real)"]].copy()
                df_export_zip.columns = ["Capítulo", "Fecha Inicio", "Días Estimados", "% Ejecutado"]

                buf_excel_zip = io.BytesIO()
                with pd.ExcelWriter(buf_excel_zip, engine='openpyxl') as writer:
                    df_export_zip.to_excel(writer, index=False, sheet_name="Cronograma")
                    df_filtrado.to_excel(writer, index=False, sheet_name="Presupuesto")
                buf_excel_zip.seek(0)

                # Generar Excel de análisis financiero
                buf_financiero = io.BytesIO()
                with pd.ExcelWriter(buf_financiero, engine='openpyxl') as writer:
                    p1['df_grp'].to_excel(writer, index=False, sheet_name="Capítulos")
                buf_financiero.seek(0)

                # Empaquetar todo en ZIP
                buf_zip = io.BytesIO()
                with zipfile.ZipFile(buf_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr(f"Reporte_{nombre_archivo_pdf}.pdf", pdf_bytes)
                    zf.writestr(f"Cronograma_{nombre_archivo_pdf}.xlsx", buf_excel_zip.getvalue())
                    zf.writestr(f"Analisis_{nombre_archivo_pdf}.xlsx", buf_financiero.getvalue())
                buf_zip.seek(0)

                st.download_button(
                    label="📦 Descargar Paquete Completo (ZIP)",
                    data=buf_zip,
                    file_name=f"Mikpho_{nombre_archivo_pdf}_{date.today()}.zip",
                    mime="application/zip"
                )

            except Exception as e_zip:
                st.warning(f"⚠️ No se pudo generar el ZIP: {e_zip}")

        # ==========================================
        # PESTAÑA 2: MODO VERSUS (Opcional)
        # ==========================================
        if tab_comparacion is not None:
            with tab_comparacion:
                p2 = datos_proyectos[1]
                st.subheader("🥊 Comparativa de Proyectos")
                c1, c2 = st.columns(2)
                nombre_limpio_p1 = p1['nombre'].replace(".xlsx", "").replace(".xls", "")
                with c1:
                    st.info(f"**🔵 {nombre_limpio_p1}**")
                    st.metric("Costo Total", f"$ {p1['total']:,.0f}")
                    st.metric("Costo x m²", f"$ {p1['m2']:,.0f}")
                nombre_limpio_p2 = p2['nombre'].replace(".xlsx", "").replace(".xls", "")
                with c2:
                    st.info(f"**🔴 {nombre_limpio_p2}**")
                    dif_m2 = ((p2['m2'] - p1['m2']) / p1['m2']) * 100 if p1['m2'] > 0 else 0
                    st.metric("Costo Total", f"$ {p2['total']:,.0f}", delta=f"{dif_m2:.2f}% vs Proy. 1", delta_color="inverse")

                df_vs = pd.concat([p1['df_grp'], p2['df_grp']])
                df_vs = df_vs[df_vs['% Participación'] >= min_porcentaje]

                # --- BARRAS COMPARATIVAS ---
                fig_vs = px.bar(df_vs, x=col_cap, y=col_val, color="Proyecto", barmode='group', color_discrete_sequence=['#00f2fe', '#f87171'])
                fig_vs.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_vs, use_container_width=True)

                # --- TORTAS DE DISTRIBUCIÓN ---
                st.markdown("---")
                st.markdown("#### 🥧 Distribución por Capítulo")
                c_pie1, c_pie2 = st.columns(2)

                with c_pie1:
                    df_pie1 = p1['df_grp'][p1['df_grp']['% Participación'] >= min_porcentaje]
                    fig_pie1 = px.pie(
                        df_pie1,
                        names=col_cap,
                        values=col_val,
                        title=nombre_limpio_p1,
                        color_discrete_sequence=px.colors.sequential.Teal
                    )
                    fig_pie1.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie1.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                        showlegend=False
                    )
                    st.plotly_chart(fig_pie1, use_container_width=True)

                with c_pie2:
                    df_pie2 = p2['df_grp'][p2['df_grp']['% Participación'] >= min_porcentaje]
                    fig_pie2 = px.pie(
                        df_pie2,
                        names=col_cap,
                        values=col_val,
                        title=nombre_limpio_p2,
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    fig_pie2.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie2.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                        showlegend=False
                    )
                    st.plotly_chart(fig_pie2, use_container_width=True)

                # --- TABLA DIFERENCIAL ---
                st.markdown("---")
                st.markdown("#### 📋 Diferencia por Capítulo")
                df_dif = pd.merge(
                    p1['df_grp'][[col_cap, col_val]].rename(columns={col_val: "Costo P1"}),
                    p2['df_grp'][[col_cap, col_val]].rename(columns={col_val: "Costo P2"}),
                    on=col_cap, how='outer'
                ).fillna(0)
                df_dif["Diferencia ($)"] = df_dif["Costo P2"] - df_dif["Costo P1"]
                df_dif["Diferencia (%)"] = ((df_dif["Costo P2"] - df_dif["Costo P1"]) / df_dif["Costo P1"].replace(0, 1)) * 100
                st.dataframe(
                    df_dif.style.format({
                        "Costo P1": "${:,.0f}",
                        "Costo P2": "${:,.0f}",
                        "Diferencia ($)": "${:,.0f}",
                        "Diferencia (%)": "{:.1f}%"
                    }).applymap(
                        lambda v: "color: #ef4444" if isinstance(v, (int, float)) and v > 0 else "color: #10b981",
                        subset=["Diferencia ($)", "Diferencia (%)"]
                    ),
                    hide_index=True,
                    use_container_width=True
                )

        # ==========================================
        # PESTAÑA 3: CRONOGRAMA Y ENTRADA DE AVANCE
        # ==========================================
        with tab_cronograma:
            st.info("Planifica los tiempos y registra el % de avance real para evaluar la obra.")

            st.session_state["datos_editados"] = st.data_editor(
                datos_editados,
                use_container_width=True,
                hide_index=True,
                column_config={
                    col_val: None,
                    "Fecha de Inicio": st.column_config.DateColumn("Fecha de Inicio", format="YYYY-MM-DD"),
                    "Días Estimados": st.column_config.NumberColumn("Días Estimados", min_value=1, step=1),
                    "% Ejecutado (Real)": st.column_config.NumberColumn("% Ejecutado", min_value=0.0, max_value=100.0, step=5.0, format="%.1f %%")
                }
            )
            datos_editados = st.session_state["datos_editados"]

            # --- VALIDACIÓN DE FECHAS Y DÍAS ---
            errores_gantt = []
            for _, fila in datos_editados.iterrows():
                if pd.isna(fila["Fecha de Inicio"]):
                    errores_gantt.append(f"❌ '{fila[col_cap]}' no tiene fecha de inicio.")
                if fila["Días Estimados"] <= 0:
                    errores_gantt.append(f"❌ '{fila[col_cap]}' tiene días estimados inválidos.")

            if errores_gantt:
                for err in errores_gantt:
                    st.warning(err)
            else:
                try:
                    datos_editados["Inicio"] = pd.to_datetime(datos_editados["Fecha de Inicio"])
                    datos_editados["Fin"] = datos_editados["Inicio"] + pd.to_timedelta(datos_editados["Días Estimados"].astype(int), unit='d')
                    fig_gantt = px.timeline(
                        datos_editados,
                        x_start="Inicio",
                        x_end="Fin",
                        y=col_cap,
                        color=col_cap,
                        hover_data={"Días Estimados": True, "% Ejecutado (Real)": True}
                    )
                    fig_gantt.update_yaxes(autorange="reversed")
                    fig_gantt.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,
                        font_color="white"
                    )
                    st.plotly_chart(fig_gantt, use_container_width=True)

                    # --- EXPORT COMO EXCEL ---
                    st.markdown("---")
                    df_export = datos_editados[[col_cap, "Fecha de Inicio", "Días Estimados", "Inicio", "Fin", "% Ejecutado (Real)"]].copy()
                    df_export.columns = ["Capítulo", "Fecha Inicio", "Días Estimados", "Inicio Calculado", "Fin Calculado", "% Ejecutado"]

                    buf_excel = io.BytesIO()
                    with pd.ExcelWriter(buf_excel, engine='openpyxl') as writer:
                        df_export.to_excel(writer, index=False, sheet_name="Cronograma")
                    buf_excel.seek(0)

                    nombre_archivo_gantt = p1['nombre'].replace(".xlsx", "").replace(".xls", "").strip()
                    st.download_button(
                        label="⬇️ Exportar Cronograma como Excel",
                        data=buf_excel,
                        file_name=f"Cronograma_{nombre_archivo_gantt}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    st.error(f"❌ Error generando el Gantt: {e}")

        # ==========================================
        # PESTAÑA 4: CONTROL DE AVANCE
        # ==========================================
        with tab_avance:
            st.subheader("📈 Control de Ejecución y Salud Financiera")
            st.markdown("Comparativa de **Costo Presupuestado** vs. **Valor Ganado (Costo Ejecutado)** según el progreso registrado.")

            if "datos_editados" not in st.session_state:
                st.info("⏳ Primero completa el cronograma en la pestaña 🗓️ Gantt.")
                st.stop()
            datos_editados = st.session_state["datos_editados"]
            df_avance = datos_editados.copy()
            df_avance["Costo Ejecutado"] = df_avance[col_val] * (df_avance["% Ejecutado (Real)"] / 100)

            tot_pres = df_avance[col_val].sum()
            tot_ejec = df_avance["Costo Ejecutado"].sum()
            pct_total = (tot_ejec / tot_pres * 100) if tot_pres > 0 else 0

            # --- SEMÁFORO DE SALUD ---
            if pct_total == 0:
                color_salud = "#6b7280"
                icono_salud = "⚪"
                texto_salud = "Sin Inicio"
                detalle_salud = "No se ha registrado avance en ningún capítulo."
            elif pct_total < 25:
                color_salud = "#ef4444"
                icono_salud = "🔴"
                texto_salud = "Inicio de Obra"
                detalle_salud = "El proyecto está en etapa inicial. Monitorea que los capítulos críticos arranquen a tiempo."
            elif pct_total < 60:
                color_salud = "#f59e0b"
                icono_salud = "🟡"
                texto_salud = "En Ejecución"
                detalle_salud = "El proyecto avanza. Verifica que el ritmo de obra corresponda al cronograma planeado."
            elif pct_total < 90:
                color_salud = "#3b82f6"
                icono_salud = "🔵"
                texto_salud = "Avanzado"
                detalle_salud = "Buen avance general. Enfócate en los capítulos con menor ejecución para cerrar sin retrasos."
            else:
                color_salud = "#10b981"
                icono_salud = "🟢"
                texto_salud = "Casi Finalizado"
                detalle_salud = "El proyecto está en etapa de cierre. Revisa entregables y actas de liquidación."

            st.markdown(f"""
            <div style="background-color:#1f2937; border-left: 6px solid {color_salud};
                        padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
                <span style="font-size:28px">{icono_salud}</span>
                <span style="font-size:20px; font-weight:bold; color:{color_salud}; margin-left:10px;">{texto_salud}</span>
                <p style="color:#d1d5db; margin-top:8px; margin-bottom:0">{detalle_salud}</p>
            </div>
            """, unsafe_allow_html=True)

            # --- MÉTRICAS ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Presupuesto Analizado", f"$ {tot_pres:,.0f}")
            c2.metric("Costo Total Ejecutado", f"$ {tot_ejec:,.0f}", help="Dinero que representa el % de obra física ya construida.")
            c3.metric("Avance Físico del Proyecto", f"{pct_total:.1f} %")

            # --- GAUGE DE PROGRESO ---
            fig_gauge = px.bar(
                x=[pct_total, 100 - pct_total],
                y=["Avance", "Avance"],
                orientation='h',
                color=["Ejecutado", "Pendiente"],
                color_discrete_map={"Ejecutado": color_salud, "Pendiente": "#374151"},
                title=f"Progreso Global del Proyecto: {pct_total:.1f}%"
            )
            fig_gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="white", showlegend=True, height=120,
                margin=dict(t=40, b=10, l=10, r=10),
                xaxis=dict(range=[0, 100], showticklabels=False),
                yaxis=dict(showticklabels=False)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown("---")

            # --- CAPÍTULOS EN RIESGO ---
            df_riesgo = df_avance[df_avance["% Ejecutado (Real)"] < 30].copy()
            if len(df_riesgo) > 0:
                st.warning(f"⚠️ **{len(df_riesgo)} capítulo(s) con menos del 30% de ejecución:**")
                st.dataframe(
                    df_riesgo[[col_cap, col_val, "% Ejecutado (Real)"]].style.format({
                        col_val: "${:,.0f}",
                        "% Ejecutado (Real)": "{:.1f}%"
                    }),
                    hide_index=True,
                    use_container_width=True
                )

            # --- PROYECCIÓN DE COSTO FINAL ---
            st.markdown("---")
            st.markdown("#### 🔮 Proyección de Costo Final")

            # Inputs del usuario para el costo real invertido hasta hoy
            costo_real_invertido = st.number_input(
                "💸 Costo real invertido hasta hoy ($):",
                min_value=0.0,
                value=float(tot_ejec),
                step=1000.0,
                help="Dinero real que ha salido de caja hasta la fecha, independiente del avance físico."
            )

            if costo_real_invertido > 0 and tot_ejec > 0:
                # CPI: eficiencia del costo (>1 bajo presupuesto, <1 sobre presupuesto)
                cpi = tot_ejec / costo_real_invertido

                # EAC: proyección del costo total final
                eac = tot_pres / cpi if cpi > 0 else tot_pres

                # Variación de costo proyectada
                variacion = eac - tot_pres
                variacion_pct = (variacion / tot_pres * 100) if tot_pres > 0 else 0

                # Costo restante estimado
                etc = eac - costo_real_invertido

                # Color según CPI
                if cpi >= 1.0:
                    color_cpi = "#10b981"
                    estado_cpi = "✅ Bajo presupuesto"
                    detalle_cpi = "El proyecto está siendo más eficiente de lo planeado."
                elif cpi >= 0.9:
                    color_cpi = "#f59e0b"
                    estado_cpi = "⚠️ Leve sobrecosto"
                    detalle_cpi = "El proyecto está ligeramente sobre presupuesto. Monitorea de cerca."
                else:
                    color_cpi = "#ef4444"
                    estado_cpi = "🔴 Sobrecosto crítico"
                    detalle_cpi = "El proyecto está significativamente sobre presupuesto. Se requiere acción inmediata."

                # Tarjetas de métricas
                c_p1, c_p2, c_p3, c_p4 = st.columns(4)
                c_p1.metric(
                    "CPI (Eficiencia)",
                    f"{cpi:.2f}",
                    help="Mayor a 1: bajo presupuesto. Menor a 1: sobre presupuesto."
                )
                c_p2.metric(
                    "Costo Final Proyectado",
                    f"$ {eac:,.0f}",
                    delta=f"{variacion_pct:+.1f}% vs presupuesto",
                    delta_color="inverse"
                )
                c_p3.metric(
                    "Costo Restante Estimado",
                    f"$ {etc:,.0f}",
                    help="Cuánto falta por invertir para terminar la obra al ritmo actual."
                )
                c_p4.metric(
                    "Variación Total",
                    f"$ {variacion:+,.0f}",
                    delta_color="inverse"
                )

                # Banner de estado
                st.markdown(f"""
                <div style="background-color:#1f2937; border-left: 6px solid {color_cpi};
                            padding: 14px 20px; border-radius: 8px; margin: 12px 0;">
                    <p style="color:{color_cpi}; font-weight:bold; font-size:16px; margin:0">
                        {estado_cpi}
                    </p>
                    <p style="color:#d1d5db; margin:6px 0 0 0">{detalle_cpi}</p>
                </div>
                """, unsafe_allow_html=True)

                # Gráfica de proyección
                categorias = ["Presupuesto Original", "Costo Real a la Fecha", "Proyección Final"]
                valores_graf = [tot_pres, costo_real_invertido, eac]
                colores_graf = ["#3b82f6", "#f59e0b", color_cpi]

                fig_proy = px.bar(
                    x=categorias,
                    y=valores_graf,
                    color=categorias,
                    color_discrete_sequence=colores_graf,
                    title="Presupuesto vs Realidad vs Proyección Final",
                    labels={"x": "", "y": "Costo ($)"}
                )
                fig_proy.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    showlegend=False
                )
                fig_proy.update_traces(texttemplate='$ %{y:,.0f}', textposition='outside')
                st.plotly_chart(fig_proy, use_container_width=True)

            else:
                st.info("💡 Ingresa el costo real invertido hasta hoy para ver la proyección.")

            df_grafica = pd.melt(df_avance, id_vars=[col_cap], value_vars=[col_val, "Costo Ejecutado"],
                                 var_name="Tipo de Costo", value_name="Dinero ($)")

            fig_avance = px.bar(df_grafica, x=col_cap, y="Dinero ($)", color="Tipo de Costo",
                                barmode='group', title="Presupuesto Inicial vs. Ejecutado a la Fecha",
                                color_discrete_map={col_val: '#3b82f6', 'Costo Ejecutado': '#10b981'})

            fig_avance.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_avance, use_container_width=True)

    # ==========================================
        # PESTAÑA 5: CURVA S
        # ==========================================
        with tab_curva_s:
            st.subheader("📉 Curva S — Avance Planeado vs Real")
            st.markdown("Seguimiento acumulado del progreso del proyecto en el tiempo.")

            if "datos_editados" not in st.session_state:
                st.warning("⚠️ Primero completa el cronograma en la pestaña 🗓️ Gantt.")
            else:
                datos_editados = st.session_state["datos_editados"]
                df_curva = datos_editados.copy()

                # Validar que tenga fechas e inicio calculado
                try:
                    df_curva["Inicio"] = pd.to_datetime(df_curva["Fecha de Inicio"])
                    df_curva["Fin"] = df_curva["Inicio"] + pd.to_timedelta(df_curva["Días Estimados"].astype(int), unit='d')
                except Exception:
                    st.error("❌ Revisa que el cronograma tenga fechas y días válidos en la pestaña Gantt.")
                    st.stop()

                fecha_inicio_proy = df_curva["Inicio"].min()
                fecha_fin_proy = df_curva["Fin"].max()

                if pd.isna(fecha_inicio_proy) or pd.isna(fecha_fin_proy):
                    st.warning("⚠️ Completa las fechas en la pestaña Gantt para generar la Curva S.")
                else:
                    # Generar rango de fechas diario
                    rango_fechas = pd.date_range(start=fecha_inicio_proy, end=fecha_fin_proy, freq='D')

                    # Calcular peso de cada capítulo sobre el total
                    df_curva['Peso'] = df_curva[col_val] / df_curva[col_val].sum() * 100

                    # Construir curva planeada acumulada
                    avance_planeado = []
                    for fecha in rango_fechas:
                        aporte = 0
                        for _, row in df_curva.iterrows():
                            if fecha >= row["Inicio"] and fecha <= row["Fin"]:
                                duracion = (row["Fin"] - row["Inicio"]).days or 1
                                aporte += row['Peso'] / duracion
                        avance_planeado.append(aporte)

                    curva_planeada = pd.Series(avance_planeado, index=rango_fechas).cumsum().clip(upper=100)

                    # Construir curva real — distribuir el % ejecutado hasta hoy
                    hoy = pd.Timestamp(date.today())
                    avance_real = []
                    for fecha in rango_fechas:
                        if fecha > hoy:
                            avance_real.append(None)
                            continue
                        aporte_real = 0
                        for _, row in df_curva.iterrows():
                            if fecha >= row["Inicio"] and fecha <= min(row["Fin"], hoy):
                                duracion_real = (min(row["Fin"], hoy) - row["Inicio"]).days or 1
                                fraccion_ejecutada = row["% Ejecutado (Real)"] / 100
                                aporte_real += (row['Peso'] * fraccion_ejecutada) / duracion_real
                        avance_real.append(aporte_real)

                    curva_real = pd.Series(avance_real, index=rango_fechas)
                    curva_real_acum = curva_real.cumsum().clip(upper=100)

                    # Armar DataFrame para Plotly
                    df_plot = pd.DataFrame({
                        "Fecha": rango_fechas,
                        "Planeado (%)": curva_planeada.values,
                        "Real (%)": curva_real_acum.values
                    })

                    fig_curva = px.line(
                        df_plot,
                        x="Fecha",
                        y=["Planeado (%)", "Real (%)"],
                        title="Curva S — Avance Acumulado",
                        labels={"value": "Avance Acumulado (%)", "variable": ""},
                        color_discrete_map={
                            "Planeado (%)": "#3b82f6",
                            "Real (%)": "#10b981"
                        }
                    )

                    # Línea vertical de hoy
                    fig_curva.add_vline(
                        x=hoy,
                        line_dash="dash",
                        line_color="#f59e0b",
                        annotation_text="Hoy",
                        annotation_font_color="#f59e0b"
                    )

                    fig_curva.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="white",
                        hovermode="x unified",
                        yaxis=dict(range=[0, 105], ticksuffix="%"),
                        legend=dict(orientation="h", y=-0.2)
                    )
                    fig_curva.update_traces(line_width=2.5)
                    st.plotly_chart(fig_curva, use_container_width=True)

                    # --- KPIs DE DESVIACIÓN ---
                    st.markdown("---")
                    fecha_hoy_idx = int(np.argmin(np.abs(curva_planeada.index - hoy)))  # type: ignore[arg-type]
                    planeado_hoy = float(curva_planeada.iloc[fecha_hoy_idx])
                    real_hoy = float(curva_real_acum.dropna().iloc[-1]) if not curva_real_acum.dropna().empty else 0
                    desviacion = real_hoy - planeado_hoy

                    c_s1, c_s2, c_s3 = st.columns(3)
                    c_s1.metric("📅 Avance Planeado a Hoy", f"{planeado_hoy:.1f}%")
                    c_s2.metric("🏗️ Avance Real a Hoy", f"{real_hoy:.1f}%")
                    c_s3.metric(
                        "📊 Desviación",
                        f"{desviacion:+.1f}%",
                        delta_color="normal" if desviacion >= 0 else "inverse"
                    )

                    if desviacion < -10:
                        st.error("🔴 El proyecto está significativamente atrasado respecto al cronograma planeado.")
                    elif desviacion < 0:
                        st.warning("🟡 El proyecto presenta un leve atraso. Monitorea el ritmo de ejecución.")
                    else:
                        st.success("🟢 El proyecto está al día o adelantado respecto al cronograma planeado.")

    except Exception as e:
        st.error(f"Error procesando los archivos: {e}")