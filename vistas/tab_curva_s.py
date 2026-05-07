"""
vistas/tab_curva_s.py — Mikpho BI
───────────────────────────────────
Pestaña 5: Curva S — Avance Planeado vs Real acumulado en el tiempo.
Recibe datos_editados ya persistidos en session_state desde app.py.
"""

from datetime import date
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


def mostrar_tab_curva_s(
    datos_editados: pd.DataFrame,
    col_cap: str,
    col_val: str,
) -> None:
    """
    Renderiza la pestaña de Curva S.

    Parámetros
    ----------
    datos_editados : DataFrame del cronograma con fechas y % Ejecutado (Real)
    col_cap        : nombre de la columna de capítulos
    col_val        : nombre de la columna de costos
    """

    st.subheader("📉 Curva S — Avance Planeado vs Real")
    st.markdown("Seguimiento acumulado del progreso del proyecto en el tiempo.")

    # ── VALIDACIÓN DE FECHAS ──────────────────────────────────────────────────
    try:
        df_curva = datos_editados.copy()
        df_curva["Inicio"] = pd.to_datetime(df_curva["Fecha de Inicio"])
        df_curva["Fin"]    = df_curva["Inicio"] + pd.to_timedelta(
            df_curva["Días Estimados"].astype(int), unit='d'
        )
    except Exception:
        st.error("❌ Revisa que el cronograma tenga fechas y días válidos en la pestaña Gantt.")
        return

    fecha_inicio_proy = df_curva["Inicio"].min()
    fecha_fin_proy    = df_curva["Fin"].max()

    if pd.isna(fecha_inicio_proy) or pd.isna(fecha_fin_proy):
        st.warning("⚠️ Completa las fechas en la pestaña Gantt para generar la Curva S.")
        return

    # ── PESO DE CADA CAPÍTULO ─────────────────────────────────────────────────
    total_val = df_curva[col_val].sum()
    if total_val == 0:
        st.warning("⚠️ El presupuesto total es cero — no se puede construir la Curva S.")
        return

    df_curva['Peso'] = df_curva[col_val] / total_val * 100

    # ── RANGO DE FECHAS DIARIO ────────────────────────────────────────────────
    rango_fechas = pd.date_range(start=fecha_inicio_proy, end=fecha_fin_proy, freq='D')

    # ── CURVA PLANEADA ────────────────────────────────────────────────────────
    avance_planeado = []
    for fecha in rango_fechas:
        aporte = 0.0
        for _, row in df_curva.iterrows():
            if row["Inicio"] <= fecha <= row["Fin"]:
                duracion = (row["Fin"] - row["Inicio"]).days or 1
                aporte  += row['Peso'] / duracion
        avance_planeado.append(aporte)

    curva_planeada = (
        pd.Series(avance_planeado, index=rango_fechas)
        .cumsum()
        .clip(upper=100)
    )

    # ── CURVA REAL ────────────────────────────────────────────────────────────
    hoy = pd.Timestamp(date.today())
    avance_real = []

    for fecha in rango_fechas:
        if fecha > hoy:
            avance_real.append(None)
            continue
        aporte_real = 0.0
        for _, row in df_curva.iterrows():
            if fecha >= row["Inicio"]:
                fin_real    = min(row["Fin"], hoy)
                duracion_real = (fin_real - row["Inicio"]).days or 1
                fraccion    = row["% Ejecutado (Real)"] / 100
                aporte_real += (row['Peso'] * fraccion) / duracion_real
        avance_real.append(aporte_real)

    curva_real_acum = (
        pd.Series(avance_real, index=rango_fechas)
        .cumsum()
        .clip(upper=100)
    )

    # ── GRÁFICA ───────────────────────────────────────────────────────────────
    df_plot = pd.DataFrame({
        "Fecha":        rango_fechas,
        "Planeado (%)": curva_planeada.values,
        "Real (%)":     curva_real_acum.values,
    })

    fig_curva = px.line(
        df_plot,
        x="Fecha",
        y=["Planeado (%)", "Real (%)"],
        title="Curva S — Avance Acumulado",
        labels={"value": "Avance Acumulado (%)", "variable": ""},
        color_discrete_map={
            "Planeado (%)": "#3b82f6",
            "Real (%)":     "#10b981",
        },
    )

    fig_curva.add_vline(
        x=hoy.timestamp() * 1000,
        line_dash="dash",
        line_color="#f59e0b",
        annotation_text="Hoy",
        annotation_font_color="#f59e0b",
    )

    fig_curva.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        hovermode="x unified",
        yaxis=dict(range=[0, 105], ticksuffix="%"),
        legend=dict(orientation="h", y=-0.2),
    )
    fig_curva.update_traces(line_width=2.5)
    st.plotly_chart(fig_curva, use_container_width=True)

    # ── KPIs DE DESVIACIÓN ────────────────────────────────────────────────────
    st.markdown("---")

    try:
        idx_hoy      = int(np.argmin([abs((f - hoy).days) for f in curva_planeada.index]))
        planeado_hoy = float(curva_planeada.iloc[idx_hoy])
        real_hoy     = (
            float(curva_real_acum.dropna().iloc[-1])
            if not curva_real_acum.dropna().empty
            else 0.0
        )
        desviacion = real_hoy - planeado_hoy

        c_s1, c_s2, c_s3 = st.columns(3)
        c_s1.metric("📅 Avance Planeado a Hoy", f"{planeado_hoy:.1f}%")
        c_s2.metric("🏗️ Avance Real a Hoy",     f"{real_hoy:.1f}%")
        c_s3.metric(
            "📊 Desviación",
            f"{desviacion:+.1f}%",
            delta_color="normal" if desviacion >= 0 else "inverse",
        )

        if desviacion < -10:
            st.error("🔴 El proyecto está significativamente atrasado respecto al cronograma planeado.")
        elif desviacion < 0:
            st.warning("🟡 El proyecto presenta un leve atraso. Monitorea el ritmo de ejecución.")
        else:
            st.success("🟢 El proyecto está al día o adelantado respecto al cronograma planeado.")

    except Exception as e:
        st.warning(f"⚠️ No se pudieron calcular los KPIs de desviación: {e}")