"""
vistas/tab_comparacion.py — Mikpho BI
───────────────────────────────────────
Pestaña 2: Comparación entre dos proyectos cargados simultáneamente.
Solo se muestra desde app.py cuando hay exactamente 2 archivos cargados.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def mostrar_tab_comparacion(
    p1: dict,
    p2: dict,
    col_cap: str,
    col_val: str,
    min_porcentaje: float,
) -> None:
    """
    Renderiza la pestaña de Comparación entre dos proyectos.

    Parámetros
    ----------
    p1, p2         : dicts con keys nombre, df_grp, total, m2, area
    col_cap        : nombre de la columna de capítulos
    col_val        : nombre de la columna de costos
    min_porcentaje : umbral mínimo de participación (viene del slider en app.py)
    """

    nombre_p1 = p1['nombre'].replace(".xlsx", "").replace(".xls", "").strip()
    nombre_p2 = p2['nombre'].replace(".xlsx", "").replace(".xls", "").strip()

    st.subheader("🥊 Comparativa de Proyectos")

    # ── MÉTRICAS LADO A LADO ──────────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.info(f"**🔵 {nombre_p1}**")
        st.metric("Costo Total", f"$ {p1['total']:,.0f}")
        st.metric("Costo x m²",  f"$ {p1['m2']:,.0f}")

    with c2:
        st.info(f"**🔴 {nombre_p2}**")
        dif_m2 = ((p2['m2'] - p1['m2']) / p1['m2']) * 100 if p1['m2'] > 0 else 0
        st.metric(
            "Costo Total",
            f"$ {p2['total']:,.0f}",
            delta=f"{dif_m2:.2f}% vs Proy. 1",
            delta_color="inverse",
        )
        dif_total = ((p2['total'] - p1['total']) / p1['total']) * 100 if p1['total'] > 0 else 0
        st.metric(
            "Costo x m²",
            f"$ {p2['m2']:,.0f}",
            delta=f"{dif_total:.2f}% vs Proy. 1",
            delta_color="inverse",
        )

    # ── BARRAS COMPARATIVAS ───────────────────────────────────────────────────
    st.markdown("---")
    df_vs = pd.concat([
        p1['df_grp'][p1['df_grp']['% Participación'] >= min_porcentaje],
        p2['df_grp'][p2['df_grp']['% Participación'] >= min_porcentaje],
    ])

    if df_vs.empty:
        st.warning("⚠️ No hay capítulos que superen el filtro de relevancia actual.")
        return

    fig_vs = px.bar(
        df_vs,
        x=col_cap,
        y=col_val,
        color="Proyecto",
        barmode='group',
        title="Costo por Capítulo — Comparativa",
        color_discrete_sequence=['#00f2fe', '#f87171'],
    )
    fig_vs.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis_tickangle=-35,
    )
    st.plotly_chart(fig_vs, use_container_width=True)

    # ── TORTAS DE DISTRIBUCIÓN ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🥧 Distribución por Capítulo")

    c_pie1, c_pie2 = st.columns(2)

    with c_pie1:
        df_pie1 = p1['df_grp'][p1['df_grp']['% Participación'] >= min_porcentaje]
        fig_pie1 = px.pie(
            df_pie1,
            names=col_cap,
            values=col_val,
            title=nombre_p1,
            color_discrete_sequence=px.colors.sequential.Teal,
        )
        fig_pie1.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie1.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            showlegend=False,
        )
        st.plotly_chart(fig_pie1, use_container_width=True)

    with c_pie2:
        df_pie2 = p2['df_grp'][p2['df_grp']['% Participación'] >= min_porcentaje]
        fig_pie2 = px.pie(
            df_pie2,
            names=col_cap,
            values=col_val,
            title=nombre_p2,
            color_discrete_sequence=px.colors.sequential.RdBu,
        )
        fig_pie2.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            showlegend=False,
        )
        st.plotly_chart(fig_pie2, use_container_width=True)

    # ── TABLA DIFERENCIAL ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📋 Diferencia por Capítulo")

    df_dif = pd.merge(
        p1['df_grp'][[col_cap, col_val]].rename(columns={col_val: "Costo P1"}),
        p2['df_grp'][[col_cap, col_val]].rename(columns={col_val: "Costo P2"}),
        on=col_cap,
        how='outer',
    ).fillna(0)

    df_dif["Diferencia ($)"] = df_dif["Costo P2"] - df_dif["Costo P1"]
    df_dif["Diferencia (%)"] = (
        (df_dif["Costo P2"] - df_dif["Costo P1"])
        / df_dif["Costo P1"].replace(0, 1)
        * 100
    )

    st.dataframe(
        df_dif.style
        .format({
            "Costo P1":       "${:,.0f}",
            "Costo P2":       "${:,.0f}",
            "Diferencia ($)": "${:,.0f}",
            "Diferencia (%)": "{:.1f}%",
        })
        .map(
            lambda v: "color: #ef4444" if isinstance(v, (int, float)) and v > 0
                      else "color: #10b981",
            subset=["Diferencia ($)", "Diferencia (%)"],
        ),
        hide_index=True,
        use_container_width=True,
    )