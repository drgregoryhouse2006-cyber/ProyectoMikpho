"""
vistas/tab_avance.py — Mikpho BI
──────────────────────────────────
Pestaña 4: Control de Ejecución y Salud Financiera.
Recibe datos_editados ya persistidos en session_state desde app.py.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def mostrar_tab_avance(
    datos_editados: pd.DataFrame,
    col_cap: str,
    col_val: str,
) -> None:
    """
    Renderiza la pestaña de Control de Avance y Salud Financiera.

    Parámetros
    ----------
    datos_editados : DataFrame del cronograma con % Ejecutado (Real)
    col_cap        : nombre de la columna de capítulos
    col_val        : nombre de la columna de costos
    """

    st.subheader("📈 Control de Ejecución y Salud Financiera")
    st.markdown(
        "Comparativa de **Costo Presupuestado** vs. **Valor Ganado** "
        "según el progreso registrado."
    )

    # ── CÁLCULOS BASE ─────────────────────────────────────────────────────────
    df_avance = datos_editados.copy()
    df_avance["Costo Ejecutado"] = (
        df_avance[col_val] * (df_avance["% Ejecutado (Real)"] / 100)
    )

    tot_pres  = df_avance[col_val].sum()
    tot_ejec  = df_avance["Costo Ejecutado"].sum()
    pct_total = (tot_ejec / tot_pres * 100) if tot_pres > 0 else 0.0

    # ── SEMÁFORO DE SALUD ─────────────────────────────────────────────────────
    if pct_total == 0:
        color_salud  = "#6b7280"
        icono_salud  = "⚪"
        texto_salud  = "Sin Inicio"
        detalle_salud = "No se ha registrado avance en ningún capítulo."
    elif pct_total < 25:
        color_salud  = "#ef4444"
        icono_salud  = "🔴"
        texto_salud  = "Inicio de Obra"
        detalle_salud = "El proyecto está en etapa inicial. Monitorea que los capítulos críticos arranquen a tiempo."
    elif pct_total < 60:
        color_salud  = "#f59e0b"
        icono_salud  = "🟡"
        texto_salud  = "En Ejecución"
        detalle_salud = "El proyecto avanza. Verifica que el ritmo de obra corresponda al cronograma planeado."
    elif pct_total < 90:
        color_salud  = "#3b82f6"
        icono_salud  = "🔵"
        texto_salud  = "Avanzado"
        detalle_salud = "Buen avance general. Enfócate en los capítulos con menor ejecución para cerrar sin retrasos."
    else:
        color_salud  = "#10b981"
        icono_salud  = "🟢"
        texto_salud  = "Casi Finalizado"
        detalle_salud = "El proyecto está en etapa de cierre. Revisa entregables y actas de liquidación."

    st.markdown(f"""
    <div style="background-color:#1f2937; border-left: 6px solid {color_salud};
                padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
        <span style="font-size:28px">{icono_salud}</span>
        <span style="font-size:20px; font-weight:bold; color:{color_salud};
                     margin-left:10px;">{texto_salud}</span>
        <p style="color:#d1d5db; margin-top:8px; margin-bottom:0">{detalle_salud}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Presupuesto Analizado",   f"$ {tot_pres:,.0f}")
    c2.metric(
        "Costo Total Ejecutado",
        f"$ {tot_ejec:,.0f}",
        help="Dinero que representa el % de obra física ya construida.",
    )
    c3.metric("Avance Físico del Proyecto", f"{pct_total:.1f} %")

    # ── BARRA DE PROGRESO GLOBAL ──────────────────────────────────────────────
    fig_gauge = px.bar(
        x=[pct_total, 100 - pct_total],
        y=["Avance", "Avance"],
        orientation='h',
        color=["Ejecutado", "Pendiente"],
        color_discrete_map={"Ejecutado": color_salud, "Pendiente": "#374151"},
        title=f"Progreso Global del Proyecto: {pct_total:.1f}%",
    )
    fig_gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        showlegend=True,
        height=120,
        margin=dict(t=40, b=10, l=10, r=10),
        xaxis=dict(range=[0, 100], showticklabels=False),
        yaxis=dict(showticklabels=False),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    # ── CAPÍTULOS EN RIESGO ───────────────────────────────────────────────────
    st.markdown("---")
    df_riesgo = df_avance[df_avance["% Ejecutado (Real)"] < 30].copy()

    if len(df_riesgo) > 0:
        st.warning(f"⚠️ **{len(df_riesgo)} capítulo(s) con menos del 30% de ejecución:**")
        st.dataframe(
            df_riesgo[[col_cap, col_val, "% Ejecutado (Real)"]].style.format({
                col_val:               "${:,.0f}",
                "% Ejecutado (Real)":  "{:.1f}%",
            }),
            hide_index=True,
            use_container_width=True,
        )

    # ── PROYECCIÓN DE COSTO FINAL ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔮 Proyección de Costo Final")

    costo_real_invertido = st.number_input(
        "💸 Costo real invertido hasta hoy ($):",
        min_value=0.0,
        value=float(tot_ejec),
        step=1000.0,
        help="Dinero real que ha salido de caja hasta la fecha, independiente del avance físico.",
    )

    if costo_real_invertido > 0 and tot_ejec > 0:
        cpi        = tot_ejec / costo_real_invertido
        eac        = tot_pres / cpi if cpi > 0 else tot_pres
        variacion  = eac - tot_pres
        var_pct    = (variacion / tot_pres * 100) if tot_pres > 0 else 0.0
        etc        = eac - costo_real_invertido

        if cpi >= 1.0:
            color_cpi  = "#10b981"
            estado_cpi = "✅ Bajo presupuesto"
            detalle_cpi = "El proyecto está siendo más eficiente de lo planeado."
        elif cpi >= 0.9:
            color_cpi  = "#f59e0b"
            estado_cpi = "⚠️ Leve sobrecosto"
            detalle_cpi = "El proyecto está ligeramente sobre presupuesto. Monitorea de cerca."
        else:
            color_cpi  = "#ef4444"
            estado_cpi = "🔴 Sobrecosto crítico"
            detalle_cpi = "El proyecto está significativamente sobre presupuesto. Se requiere acción inmediata."

        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        c_p1.metric(
            "CPI (Eficiencia)",
            f"{cpi:.2f}",
            help="Mayor a 1: bajo presupuesto. Menor a 1: sobre presupuesto.",
        )
        c_p2.metric(
            "Costo Final Proyectado",
            f"$ {eac:,.0f}",
            delta=f"{var_pct:+.1f}% vs presupuesto",
            delta_color="inverse",
        )
        c_p3.metric(
            "Costo Restante Estimado",
            f"$ {etc:,.0f}",
            help="Cuánto falta por invertir para terminar la obra al ritmo actual.",
        )
        c_p4.metric("Variación Total", f"$ {variacion:+,.0f}", delta_color="inverse")

        st.markdown(f"""
        <div style="background-color:#1f2937; border-left: 6px solid {color_cpi};
                    padding: 14px 20px; border-radius: 8px; margin: 12px 0;">
            <p style="color:{color_cpi}; font-weight:bold; font-size:16px; margin:0">
                {estado_cpi}
            </p>
            <p style="color:#d1d5db; margin:6px 0 0 0">{detalle_cpi}</p>
        </div>
        """, unsafe_allow_html=True)

        fig_proy = px.bar(
            x=["Presupuesto Original", "Costo Real a la Fecha", "Proyección Final"],
            y=[tot_pres, costo_real_invertido, eac],
            color=["Presupuesto Original", "Costo Real a la Fecha", "Proyección Final"],
            color_discrete_sequence=["#3b82f6", "#f59e0b", color_cpi],
            title="Presupuesto vs Realidad vs Proyección Final",
            labels={"x": "", "y": "Costo ($)"},
        )
        fig_proy.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            showlegend=False,
        )
        fig_proy.update_traces(texttemplate='$ %{y:,.0f}', textposition='outside')
        st.plotly_chart(fig_proy, use_container_width=True)

    else:
        st.info("💡 Ingresa el costo real invertido hasta hoy para ver la proyección.")

    # ── GRÁFICA PRESUPUESTO VS EJECUTADO ─────────────────────────────────────
    st.markdown("---")
    df_grafica = pd.melt(
        df_avance,
        id_vars=[col_cap],
        value_vars=[col_val, "Costo Ejecutado"],
        var_name="Tipo de Costo",
        value_name="Dinero ($)",
    )

    fig_avance = px.bar(
        df_grafica,
        x=col_cap,
        y="Dinero ($)",
        color="Tipo de Costo",
        barmode='group',
        title="Presupuesto Inicial vs. Ejecutado a la Fecha",
        color_discrete_map={
            col_val:           '#3b82f6',
            'Costo Ejecutado': '#10b981',
        },
    )
    fig_avance.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis_tickangle=-35,
    )
    st.plotly_chart(fig_avance, use_container_width=True)
