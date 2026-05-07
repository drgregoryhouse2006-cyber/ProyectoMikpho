"""
utils/calculadora.py — Mikpho BI
──────────────────────────────────
Funciones puras de cálculo: métricas financieras, CPI, EAC, Curva S.
Sin dependencias de Streamlit ni matplotlib.
"""

from typing import Optional
import numpy as np
import pandas as pd
from datetime import date


def calcular_resumen_ejecutivo(
    df_filtrado: pd.DataFrame,
    col_cap: str,
    col_val: str,
) -> dict:
    """
    Calcula indicadores para el resumen ejecutivo:
    - Capítulo dominante y su % y costo
    - Cuántos capítulos acumulan el 80%
    - Si hay concentración alta (>40%)
    """
    df_ord = df_filtrado.sort_values('% Participación', ascending=False).reset_index(drop=True)

    if df_ord.empty:
        return {}

    cap_mayor   = df_ord.iloc[0][col_cap]
    pct_mayor   = df_ord.iloc[0]['% Participación']
    costo_mayor = df_ord.iloc[0][col_val]

    df_acum = df_ord.copy()
    df_acum['Acumulado'] = df_acum['% Participación'].cumsum()
    n_caps_80 = len(df_acum[df_acum['Acumulado'] <= 80]) + 1

    return {
        "cap_mayor":            cap_mayor,
        "pct_mayor":            pct_mayor,
        "costo_mayor":          costo_mayor,
        "n_caps_80":            n_caps_80,
        "total_caps":           len(df_ord),
        "alerta_concentracion": pct_mayor > 40,
    }


def calcular_avance(datos_editados: pd.DataFrame, col_val: str) -> dict:
    """
    Calcula métricas de avance físico y financiero.
    Retorna: tot_pres, tot_ejec, pct_total, df (con columna Costo Ejecutado)
    """
    df = datos_editados.copy()
    df["Costo Ejecutado"] = df[col_val] * (df["% Ejecutado (Real)"] / 100)

    tot_pres  = df[col_val].sum()
    tot_ejec  = df["Costo Ejecutado"].sum()
    pct_total = (tot_ejec / tot_pres * 100) if tot_pres > 0 else 0.0

    return {
        "tot_pres":  tot_pres,
        "tot_ejec":  tot_ejec,
        "pct_total": pct_total,
        "df":        df,
    }


def calcular_semaforo(pct_total: float) -> dict:
    """Retorna color, icono, texto y detalle según el % de avance."""
    if pct_total == 0:
        return {
            "color":   "#6b7280",
            "icono":   "⚪",
            "texto":   "Sin Inicio",
            "detalle": "No se ha registrado avance en ningún capítulo.",
        }
    elif pct_total < 25:
        return {
            "color":   "#ef4444",
            "icono":   "🔴",
            "texto":   "Inicio de Obra",
            "detalle": "El proyecto está en etapa inicial. Monitorea que los capítulos críticos arranquen a tiempo.",
        }
    elif pct_total < 60:
        return {
            "color":   "#f59e0b",
            "icono":   "🟡",
            "texto":   "En Ejecución",
            "detalle": "El proyecto avanza. Verifica que el ritmo de obra corresponda al cronograma planeado.",
        }
    elif pct_total < 90:
        return {
            "color":   "#3b82f6",
            "icono":   "🔵",
            "texto":   "Avanzado",
            "detalle": "Buen avance general. Enfócate en los capítulos con menor ejecución para cerrar sin retrasos.",
        }
    else:
        return {
            "color":   "#10b981",
            "icono":   "🟢",
            "texto":   "Casi Finalizado",
            "detalle": "El proyecto está en etapa de cierre. Revisa entregables y actas de liquidación.",
        }


def calcular_proyeccion(
    tot_pres: float,
    tot_ejec: float,
    costo_real: float,
) -> Optional[dict]:
    """
    Calcula CPI, EAC, ETC y variación de costo.
    Retorna None si los datos no son suficientes para calcular.
    """
    if costo_real <= 0 or tot_ejec <= 0:
        return None

    cpi       = tot_ejec / costo_real
    eac       = tot_pres / cpi if cpi > 0 else tot_pres
    variacion = eac - tot_pres
    var_pct   = (variacion / tot_pres * 100) if tot_pres > 0 else 0.0
    etc       = eac - costo_real

    if cpi >= 1.0:
        estado = {
            "color":   "#10b981",
            "texto":   "✅ Bajo presupuesto",
            "detalle": "El proyecto está siendo más eficiente de lo planeado.",
        }
    elif cpi >= 0.9:
        estado = {
            "color":   "#f59e0b",
            "texto":   "⚠️ Leve sobrecosto",
            "detalle": "El proyecto está ligeramente sobre presupuesto. Monitorea de cerca.",
        }
    else:
        estado = {
            "color":   "#ef4444",
            "texto":   "🔴 Sobrecosto crítico",
            "detalle": "El proyecto está significativamente sobre presupuesto. Se requiere acción inmediata.",
        }

    return {
        "cpi":       cpi,
        "eac":       eac,
        "variacion": variacion,
        "var_pct":   var_pct,
        "etc":       etc,
        "estado":    estado,
    }


def calcular_curva_s(
    df_curva: pd.DataFrame,
    col_cap: str,
    col_val: str,
) -> Optional[dict]:
    """
    Genera las series de Curva S planeada y real.

    Requiere columnas: Inicio (datetime), Fin (datetime),
                       % Ejecutado (Real), col_val

    Retorna dict con claves:
        rango_fechas, curva_planeada, curva_real,
        planeado_hoy, real_hoy, desviacion, hoy
    Retorna None si las fechas son inválidas.
    """
    fecha_inicio = df_curva["Inicio"].min()
    fecha_fin    = df_curva["Fin"].max()
    hoy          = pd.Timestamp(date.today())

    if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
        return None

    df = df_curva.copy()
    total_val  = df[col_val].sum()
    df['Peso'] = (df[col_val] / total_val * 100) if total_val > 0 else 0.0

    rango = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')

    # ── Curva planeada ────────────────────────────────────────────────────────
    planeado = []
    for fecha in rango:
        aporte = 0.0
        for _, row in df.iterrows():
            if row["Inicio"] <= fecha <= row["Fin"]:
                duracion = max((row["Fin"] - row["Inicio"]).days, 1)
                aporte  += row['Peso'] / duracion
        planeado.append(aporte)

    curva_planeada = pd.Series(planeado, index=rango).cumsum().clip(upper=100)

    # ── Curva real ────────────────────────────────────────────────────────────
    real = []
    for fecha in rango:
        if fecha > hoy:
            real.append(None)
            continue
        aporte_real = 0.0
        for _, row in df.iterrows():
            if row["Inicio"] <= fecha <= min(row["Fin"], hoy):
                duracion_real = max((min(row["Fin"], hoy) - row["Inicio"]).days, 1)
                fraccion      = row["% Ejecutado (Real)"] / 100
                aporte_real  += (row['Peso'] * fraccion) / duracion_real
        real.append(aporte_real)

    curva_real_acum = pd.Series(real, index=rango).cumsum().clip(upper=100)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    # ── KPIs ──────────────────────────────────────────────────────────────────
    idx_hoy      = int(np.argmin([abs((f - hoy).days) for f in curva_planeada.index]))
    planeado_hoy = float(curva_planeada.iloc[idx_hoy])
    real_hoy     = (
        float(curva_real_acum.dropna().iloc[-1])
        if not curva_real_acum.dropna().empty
        else 0.0
    )
    desviacion = real_hoy - planeado_hoy

    return {
        "rango_fechas":   rango,
        "curva_planeada": curva_planeada,
        "curva_real":     curva_real_acum,
        "planeado_hoy":   planeado_hoy,
        "real_hoy":       real_hoy,
        "desviacion":     desviacion,
        "hoy":            hoy,
    }