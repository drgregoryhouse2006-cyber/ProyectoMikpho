"""
vistas/tab_analisis.py — Mikpho BI
─────────────────────────────────────
Pestaña 1: Análisis Individual, Resumen Ejecutivo y Exportaciones.
Recibe datos ya procesados desde app.py — sin lógica de carga aquí.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.exportador import generar_pdf, generar_excel_cronograma, generar_excel_analisis, generar_zip


def mostrar_tab_analisis(
    p1: dict,
    col_cap: str,
    col_val: str,
    min_porcentaje: float,
    datos_editados: pd.DataFrame,
) -> None:
    """
    Renderiza la pestaña de Análisis Individual.

    Parámetros
    ----------
    p1              : dict con keys nombre, df_grp, total, m2, area
    col_cap         : nombre de la columna de capítulos
    col_val         : nombre de la columna de costos
    min_porcentaje  : umbral mínimo de participación (viene del slider en app.py)
    datos_editados  : DataFrame del cronograma editado por el usuario (para el ZIP)
    """

    nombre_limpio = p1['nombre'].replace(".xlsx", "").replace(".xls", "").strip()
    st.subheader(f"Análisis del Proyecto: {nombre_limpio}")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Costo Total",   f"$ {p1['total']:,.0f}")
    col2.metric("📐 Valor por m²",  f"$ {p1['m2']:,.0f}")
    col3.metric("🏢 Área",          f"{p1['area']:,.2f} m²")

    df_filtrado = (
        p1['df_grp'][p1['df_grp']['% Participación'] >= min_porcentaje]
        .sort_values(col_val, ascending=False)
    )

    # ── RESUMEN EJECUTIVO ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🧠 Resumen Ejecutivo")

    df_ord = df_filtrado.sort_values('% Participación', ascending=False)

    if len(df_ord) == 0:
        st.warning("⚠️ No hay capítulos que superen el filtro de relevancia actual.")
        return

    cap_mayor   = df_ord.iloc[0][col_cap]
    pct_mayor   = df_ord.iloc[0]['% Participación']
    costo_mayor = df_ord.iloc[0][col_val]

    # Cuántos capítulos acumulan el 80%
    df_acum = df_ord.copy()
    df_acum['Acumulado'] = df_acum['% Participación'].cumsum()
    n_caps_80 = len(df_acum[df_acum['Acumulado'] <= 80]) + 1

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

    # ── TREEMAP + TABLA ───────────────────────────────────────────────────────
    c_chart, c_table = st.columns([2, 1])
    with c_chart:
        fig_tree = px.treemap(
            df_filtrado,
            path=[col_cap],
            values=col_val,
            color=col_val,
            color_continuous_scale='teal',
        )
        fig_tree.update_layout(
            margin=dict(t=10, l=10, r=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    with c_table:
        df_display = df_filtrado[[col_cap, col_val, '% Participación']].copy()
        st.dataframe(
            df_display.style.format({
                col_val:            "${:,.0f}",
                '% Participación':  "{:.2f}%",
            }),
            height=400,
        )

    # ── EXPORTACIONES ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📑 Reporte Gerencial")

    try:
        pdf_bytes = generar_pdf(
            p1['nombre'], p1['total'], p1['m2'], p1['area'],
            df_filtrado, col_cap, col_val,
        )
        st.download_button(
            label="⬇️ Descargar Reporte en PDF",
            data=pdf_bytes,
            file_name=f"Reporte_{nombre_limpio}.pdf",
            mime="application/pdf",
        )
    except Exception as e_pdf:
        st.error(f"❌ Error generando el PDF: {e_pdf}")
        pdf_bytes = b""

    # ── ZIP COMPLETO ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📦 Exportar Paquete Completo")
    st.caption("Descarga el PDF gerencial + cronograma Excel + análisis financiero en un solo archivo.")

    try:
        excel_cronograma = generar_excel_cronograma(datos_editados, df_filtrado, col_cap)
        excel_analisis   = generar_excel_analisis(p1['df_grp'])

        zip_bytes = generar_zip(
            nombre_base      = nombre_limpio,
            pdf_bytes        = pdf_bytes,
            excel_cronograma = excel_cronograma,
            excel_analisis   = excel_analisis,
        )

        st.download_button(
            label="📦 Descargar Paquete Completo (ZIP)",
            data=zip_bytes,
            file_name=f"Mikpho_{nombre_limpio}_{date.today()}.zip",
            mime="application/zip",
        )
    except Exception as e_zip:
        st.warning(f"⚠️ No se pudo generar el ZIP: {e_zip}")