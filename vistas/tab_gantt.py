"""
vistas/tab_gantt.py — Mikpho BI
─────────────────────────────────
Pestaña 3: Cronograma editable y diagrama de Gantt.
Retorna el DataFrame modificado — app.py lo persiste en session_state.
"""

import io
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.exportador import generar_excel_cronograma


def mostrar_tab_gantt(
    datos_editados: pd.DataFrame,
    col_cap: str,
    col_val: str,
    nombre_proyecto: str,
) -> pd.DataFrame:
    """
    Renderiza la pestaña de Cronograma y Gantt.

    Parámetros
    ----------
    datos_editados  : DataFrame base del cronograma (desde session_state)
    col_cap         : nombre de la columna de capítulos
    col_val         : nombre de la columna de costos
    nombre_proyecto : nombre del archivo del proyecto (para el export)

    Retorna
    -------
    pd.DataFrame con las ediciones del usuario — app.py lo guarda en session_state.
    """

    st.info("Planifica los tiempos y registra el % de avance real para evaluar la obra.")

    # ── EDITOR DE CRONOGRAMA ──────────────────────────────────────────────────
    df_editado = st.data_editor(
        datos_editados,
        use_container_width=True,
        hide_index=True,
        column_config={
            col_val: None,  # ocultar columna de costos — no se edita aquí
            "Fecha de Inicio": st.column_config.DateColumn(
                "Fecha de Inicio",
                format="YYYY-MM-DD",
            ),
            "Días Estimados": st.column_config.NumberColumn(
                "Días Estimados",
                min_value=1,
                step=1,
            ),
            "% Ejecutado (Real)": st.column_config.NumberColumn(
                "% Ejecutado",
                min_value=0.0,
                max_value=100.0,
                step=5.0,
                format="%.1f %%",
            ),
        },
    )

    # ── VALIDACIÓN ────────────────────────────────────────────────────────────
    errores = []
    for _, fila in df_editado.iterrows():
        if pd.isna(fila["Fecha de Inicio"]):
            errores.append(f"❌ **{fila[col_cap]}** no tiene fecha de inicio.")
        if fila["Días Estimados"] <= 0:
            errores.append(f"❌ **{fila[col_cap]}** tiene días estimados inválidos.")

    if errores:
        for err in errores:
            st.warning(err)
        return df_editado

    # ── GANTT ─────────────────────────────────────────────────────────────────
    try:
        df_gantt = df_editado.copy()
        df_gantt["Inicio"] = pd.to_datetime(df_gantt["Fecha de Inicio"])
        df_gantt["Fin"]    = df_gantt["Inicio"] + pd.to_timedelta(
            df_gantt["Días Estimados"].astype(int), unit='d'
        )

        fig_gantt = px.timeline(
            df_gantt,
            x_start="Inicio",
            x_end="Fin",
            y=col_cap,
            color=col_cap,
            hover_data={
                "Días Estimados":      True,
                "% Ejecutado (Real)":  True,
            },
        )
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            font_color="white",
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error generando el Gantt: {e}")
        return df_editado

    # ── EXPORTAR EXCEL ────────────────────────────────────────────────────────
    st.markdown("---")
    nombre_limpio = nombre_proyecto.replace(".xlsx", "").replace(".xls", "").strip()

    try:
        # Construir df_filtrado mínimo para el exportador (solo capítulos visibles)
        df_filtrado_min = df_editado[[col_cap]].copy()
        df_filtrado_min[col_val] = 0.0  # placeholder — el Excel de gantt no usa costos

        excel_bytes = generar_excel_cronograma(df_editado, df_filtrado_min, col_cap)

        st.download_button(
            label="⬇️ Exportar Cronograma como Excel",
            data=excel_bytes,
            file_name=f"Cronograma_{nombre_limpio}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e_excel:
        st.warning(f"⚠️ No se pudo generar el Excel: {e_excel}")

    return df_editado