"""
utils/exportador.py — Mikpho BI
─────────────────────────────────
Generación de PDF ejecutivo, Excel de cronograma y paquete ZIP.
matplotlib.use('Agg') ya fue llamado en config.py — no repetir aquí.
"""

import io
import zipfile
from datetime import date
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from fpdf import FPDF


# ── LIMPIEZA DE TEXTO PARA PDF ────────────────────────────────────────────────
def _limpiar_para_pdf(texto: str) -> str:
    """Elimina caracteres fuera de latin-1 que Helvetica no soporta."""
    reemplazos = {
        '\u201c': '"', '\u201d': '"',
        '\u2018': "'", '\u2019': "'",
        '\u2013': '-', '\u2014': '-',
        '\u2026': '...', '\u00b0': '',
    }
    for orig, remp in reemplazos.items():
        texto = texto.replace(orig, remp)
    return texto.encode('latin-1', errors='ignore').decode('latin-1')

# ── PALETA CORPORATIVA ────────────────────────────────────────────────────────
# Tonos profesionales: azul marino, gris antracita y dorado suave
C_NAVY      = (20,  50,  90)        # #14325A — encabezado / títulos
C_BLUE      = (37,  99, 235)        # #2563EB — acento principal
C_GOLD      = (202, 138,  4)        # #CA8A04 — acento secundario / KPI
C_SLATE     = (71,  85, 105)        # #475569 — texto secundario
C_LIGHT_BG  = (246, 248, 251)       # #F6F8FB — fondo alterno de filas
C_WHITE     = (255, 255, 255)
C_BORDER    = (203, 213, 225)       # #CBD5E1 — líneas de tabla
C_TEXT      = (30,  41,  59)        # #1E293B — texto principal

# Paleta de barras (degradado de intensidad)
PALETTE_BARS = [
    "#1e3a5f", "#1d4ed8", "#2563eb", "#3b82f6",
    "#60a5fa", "#93c5fd", "#bfdbfe", "#dbeafe",
]


# ── HELPERS PDF ───────────────────────────────────────────────────────────────

def _rgb(pdf: FPDF, color: tuple, fill: bool = False) -> None:
    """Aplica color RGB al texto o al relleno del PDF."""
    r, g, b = color
    if fill:
        pdf.set_fill_color(r, g, b)
    else:
        pdf.set_text_color(r, g, b)


def _linea_h(pdf: FPDF, y: Optional[float] = None, color: tuple = C_BORDER) -> None:
    """Dibuja línea horizontal en el PDF."""
    y = y or pdf.get_y()
    pdf.set_draw_color(*color)
    pdf.line(20, y, 190, y)


def _seccion_titulo(pdf: FPDF, numero: str, texto: str) -> None:
    """
    Dibuja título de sección con badge numerado y línea decorativa.
    Estilo: badge azul marino + texto en mayúscula + regla gris.
    """
    pdf.ln(4)

    # Badge numérico azul
    _rgb(pdf, C_NAVY, fill=True)
    pdf.set_fill_color(*C_NAVY)
    badge_x = pdf.get_x()
    badge_y = pdf.get_y()
    pdf.rect(badge_x, badge_y, 7, 7, 'F')
    pdf.set_font("Helvetica", 'B', 7)
    _rgb(pdf, C_WHITE)
    pdf.set_xy(badge_x, badge_y + 0.5)
    pdf.cell(7, 6, numero, align='C')

    # Texto de título
    pdf.set_xy(badge_x + 9, badge_y)
    pdf.set_font("Helvetica", 'B', 11)
    _rgb(pdf, C_NAVY)
    pdf.cell(0, 7, texto.upper(), new_x="LMARGIN", new_y="NEXT")

    # Línea decorativa doble
    y_line = pdf.get_y()
    pdf.set_draw_color(*C_NAVY)
    pdf.set_line_width(0.6)
    pdf.line(20, y_line, 100, y_line)
    pdf.set_draw_color(*C_GOLD)
    pdf.set_line_width(0.3)
    pdf.line(100, y_line, 190, y_line)
    pdf.set_line_width(0.2)
    pdf.ln(5)


def _kpi_box(
    pdf: FPDF, x: float, y: float, w: float, h: float,
    etiqueta: str, valor: str, sub: str = "", color: tuple = C_BLUE
) -> None:
    """
    Dibuja un recuadro tipo KPI card con borde izquierdo de color,
    etiqueta pequeña, valor grande y sub-etiqueta opcional.
    """
    # Fondo claro
    pdf.set_fill_color(*C_LIGHT_BG)
    pdf.rect(x, y, w, h, 'F')

    # Borde izquierdo de acento
    pdf.set_fill_color(*color)
    pdf.rect(x, y, 2.5, h, 'F')

    # Borde exterior sutil
    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.2)
    pdf.rect(x, y, w, h)

    # Etiqueta superior
    pdf.set_xy(x + 5, y + 2.5)
    pdf.set_font("Helvetica", '', 7)
    _rgb(pdf, C_SLATE)
    pdf.cell(w - 7, 4, etiqueta.upper())

    # Valor principal
    pdf.set_xy(x + 5, y + 6.5)
    pdf.set_font("Helvetica", 'B', 11)
    _rgb(pdf, C_TEXT)
    pdf.cell(w - 7, 6, valor)

    # Sub-etiqueta
    if sub:
        pdf.set_xy(x + 5, y + 13)
        pdf.set_font("Helvetica", 'I', 7)
        _rgb(pdf, C_SLATE)
        pdf.cell(w - 7, 4, sub)


# ── GRÁFICAS ──────────────────────────────────────────────────────────────────

def _color_barra(idx: int, total: int) -> str:
    """Retorna color de barra según posición (degradado azul marino → celeste)."""
    palette = [
        "#1e3a5f", "#1e4976", "#1d4ed8", "#2563eb",
        "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe",
    ]
    n = len(palette)
    return palette[min(idx, n - 1)] if total <= n else palette[int(idx * (n - 1) / max(total - 1, 1))]


def _setup_axes(ax, color_fondo: str = "#ffffff") -> None:
    """Aplica estilo corporativo limpio a un eje matplotlib."""
    ax.set_facecolor(color_fondo)
    ax.tick_params(colors="#475569", labelsize=8)
    ax.xaxis.label.set_color("#475569")
    ax.yaxis.label.set_color("#475569")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color("#cbd5e1")
        ax.spines[spine].set_linewidth(0.6)
    ax.grid(axis="x", color="#e2e8f0", linewidth=0.5, linestyle="--", alpha=0.8)
    ax.set_axisbelow(True)


def generar_grafica_combinada(
    df: pd.DataFrame, col_cap: str
) -> Optional[io.BytesIO]:
    """
    Genera figura de dos paneles:
      Izquierda → barras horizontales con valor y porcentaje acumulado
      Derecha   → gráfica de dona con porcentaje de participación

    Retorna BytesIO PNG o None si falla.
    Siempre cierra la figura con finally para evitar leaks de memoria.
    """
    fig = None
    try:
        n = len(df)
        nombres  = [_limpiar_para_pdf(str(v))[:42] for v in df[col_cap]]
        valores  = df["% Participación"].tolist()
        costos   = df["Valor"].tolist() if "Valor" in df.columns else [0] * n

        colores_barras = [_color_barra(i, n) for i in range(n)]
        # Donut: si hay muchas categorías, colapsar las menores al 3 %
        etiq_dona, vals_dona, cols_dona = _preparar_dona(
            nombres, valores, colores_barras
        )

        fig = plt.figure(figsize=(14, max(4.5, n * 0.45 + 1.5)),
                         facecolor="#ffffff")
        gs  = gridspec.GridSpec(
            1, 2, width_ratios=[2.6, 1], wspace=0.38,
            left=0.01, right=0.99, top=0.90, bottom=0.10
        )

        # ── Panel izquierdo: barras horizontales ──────────────────────────────
        ax_bar = fig.add_subplot(gs[0])
        _setup_axes(ax_bar)

        y_pos = np.arange(n)
        bars  = ax_bar.barh(
            y_pos, valores, color=colores_barras,
            edgecolor="white", linewidth=0.4, height=0.62
        )

        # Valor dentro / fuera de la barra
        max_val = max(valores) if valores else 1
        for bar, val, nom in zip(bars, valores, nombres):
            ratio   = val / max_val
            offset  = 0.35 if ratio > 0.55 else bar.get_width() + 0.4
            color_t = "white" if ratio > 0.55 else "#1e3a5f"
            ha      = "right" if ratio > 0.55 else "left"
            x_txt   = bar.get_width() - 0.35 if ratio > 0.55 else offset
            ax_bar.text(
                x_txt,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%",
                va="center", ha=ha,
                color=color_t, fontsize=7.5, fontweight="bold"
            )

        ax_bar.set_yticks(y_pos)
        ax_bar.set_yticklabels(nombres, fontsize=7.5, color="#1e293b")
        ax_bar.set_xlabel("% Participación en el Presupuesto", fontsize=8,
                          color="#475569", labelpad=6)
        ax_bar.set_xlim(0, max_val * 1.18)
        ax_bar.invert_yaxis()

        # Línea media de referencia
        media = float(np.mean(valores))
        ax_bar.axvline(media, color="#ca8a04", linestyle="--",
                       linewidth=0.9, alpha=0.85,
                       label=f"Promedio: {media:.1f}%")
        ax_bar.legend(fontsize=7, loc="lower right",
                      framealpha=0.7, edgecolor="#cbd5e1")

        ax_bar.set_title("Participación por Capítulo",
                         fontsize=10, fontweight="bold",
                         color="#14325A", pad=8)

        # ── Panel derecho: dona ───────────────────────────────────────────────
        ax_don = fig.add_subplot(gs[1])
        ax_don.set_facecolor("#ffffff")

        wedge_props = dict(width=0.48, edgecolor="white", linewidth=1.2)
        resultado_pie = ax_don.pie(
            vals_dona, colors=cols_dona,
            startangle=90, counterclock=False,
            wedgeprops=wedge_props
        )
        wedges = resultado_pie[0]

        # Texto central
        ax_don.text(
            0, 0,
            f"{sum(valores):.0f}%\nTotal",
            ha="center", va="center",
            fontsize=9, fontweight="bold", color="#14325A",
            linespacing=1.4
        )

        # Leyenda lateral compacta
        leyenda = [
            mpatches.Patch(color=c, label=f"{e} ({v:.1f}%)")
            for e, v, c in zip(etiq_dona, vals_dona, cols_dona)
        ]
        ax_don.legend(
            handles=leyenda, loc="lower center",
            bbox_to_anchor=(0.5, -0.22),
            fontsize=6.5, framealpha=0.8,
            edgecolor="#cbd5e1", ncol=1,
            handlelength=1, handleheight=0.9
        )
        ax_don.set_title("Distribución del Costo",
                         fontsize=10, fontweight="bold",
                         color="#14325A", pad=8)

        # ── Marca de agua / fondo ─────────────────────────────────────────────
        fig.text(
            0.99, 0.01,
            "Mikpho Construcciones · Sistema BI",
            ha="right", va="bottom",
            fontsize=6.5, color="#94a3b8", style="italic"
        )

        buf = io.BytesIO()
        fig.savefig(
            buf, format="png", dpi=150,
            bbox_inches="tight", facecolor="#ffffff"
        )
        buf.seek(0)
        return buf

    except Exception:
        return None

    finally:
        if fig is not None:
            plt.close(fig)


# Constante de color dorado para matplotlib (hex)
C_GOLD_HEX = "#ca8a04"


def _preparar_dona(
    nombres: list, valores: list, colores: list,
    umbral: float = 3.0
) -> tuple:
    """
    Agrupa categorías menores al umbral en 'Otros' para la dona.
    Retorna (etiquetas, valores, colores) limpios.
    """
    datos = sorted(
        zip(nombres, valores, colores),
        key=lambda x: x[1], reverse=True
    )
    etiq, vals, cols = [], [], []
    otros_sum = 0.0
    for n, v, c in datos:
        if v >= umbral or len(etiq) < 5:
            etiq.append(n[:28])
            vals.append(v)
            cols.append(c)
        else:
            otros_sum += v

    if otros_sum > 0:
        etiq.append("Otros")
        vals.append(otros_sum)
        cols.append("#94a3b8")

    return etiq, vals, cols


def _generar_mini_barra_progreso(porcentaje: float, ancho: float = 50.0) -> float:
    """Retorna el ancho en mm de la barra de progreso según el porcentaje."""
    return min(porcentaje / 100.0, 1.0) * ancho


# ── PDF ───────────────────────────────────────────────────────────────────────

def generar_pdf(
    nombre_proyecto: str,
    total: float,
    m2: float,
    area: float,
    df_filtrado: pd.DataFrame,
    col_cap: str,
    col_val: str,
) -> bytes:
    """
    Genera el PDF ejecutivo del proyecto con estilo informe técnico corporativo.
    Retorna bytes listos para st.download_button.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    nombre_limpio = nombre_proyecto.replace(".xlsx", "").replace(".xls", "")

    # ═══════════════════════════════════════════════════════════════════════════
    # PORTADA / ENCABEZADO PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════════

    # Banda azul marina superior
    pdf.set_fill_color(*C_NAVY)
    pdf.rect(0, 0, 210, 28, "F")

    # Franja dorada delgada bajo la banda
    pdf.set_fill_color(*C_GOLD)
    pdf.rect(0, 28, 210, 1.5, "F")

    # Título principal (blanco sobre azul)
    pdf.set_xy(20, 6)
    pdf.set_font("Helvetica", "B", 16)
    _rgb(pdf, C_WHITE)
    pdf.cell(0, 8, "INFORME TÉCNICO DE PROYECTO", align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(20, 15)
    pdf.set_font("Helvetica", "", 9)
    _rgb(pdf, (180, 200, 230))
    pdf.cell(0, 6, "Mikpho Construcciones  ·  Sistema de Inteligencia de Negocio",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(12)

    # ── Bloque de identificación del proyecto ─────────────────────────────────
    pdf.set_fill_color(*C_NAVY)
    pdf.rect(20, pdf.get_y(), 170, 9, "F")
    pdf.set_xy(22, pdf.get_y() + 1.5)
    pdf.set_font("Helvetica", "B", 9)
    _rgb(pdf, (200, 220, 255))
    pdf.cell(0, 6, f"PROYECTO:  {nombre_limpio.upper()}")
    pdf.ln(11)

    # ── KPI CARDS (4 tarjetas en fila) ───────────────────────────────────────
    _seccion_titulo(pdf, "1", "Resumen Financiero")

    kw, kh, kg = 40.5, 20, 3          # ancho, alto, gap
    kx0 = 20.0
    ky  = pdf.get_y()

    _kpi_box(pdf, kx0,             ky, kw, kh,
             "Costo Total Estimado",
             f"$ {total:,.0f}", "COP / Presupuesto base", C_BLUE)

    _kpi_box(pdf, kx0 + kw + kg,   ky, kw, kh,
             "Valor / m²",
             f"$ {m2:,.0f}", "COP por metro cuadrado", C_NAVY)

    _kpi_box(pdf, kx0 + (kw+kg)*2, ky, kw, kh,
             "Área Total",
             f"{area:,.2f} m²", "Superficie construida", (30, 120, 60))

    _kpi_box(pdf, kx0 + (kw+kg)*3, ky, kw, kh,
             "N.º de Capítulos",
             str(len(df_filtrado)), "Ítems en presupuesto", C_GOLD)

    pdf.ln(kh + 8)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — DESGLOSE DE CAPÍTULOS (TABLA CON BARRAS DE PROGRESO)
    # ═══════════════════════════════════════════════════════════════════════════
    _seccion_titulo(pdf, "2", "Desglose de Capítulos Presupuestales")

    # Encabezado de tabla
    col_widths = (84, 36, 24, 26)      # Capítulo | Costo | % | Barra
    headers    = ("Capítulo / Partida", "Costo (COP $)", "Part. %", "Indicador")

    pdf.set_fill_color(*C_NAVY)
    pdf.set_font("Helvetica", "B", 8)
    _rgb(pdf, C_WHITE)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 7, h, border=0, fill=True, align="C", new_x="END")
    pdf.ln(7)

    # Línea separadora bajo encabezado
    _linea_h(pdf, color=C_GOLD)
    pdf.ln(1)

    # Filas de datos
    max_val   = df_filtrado["% Participación"].max() or 1
    bar_max_w = 22.0   # mm máximos para la barra de progreso en la tabla

    for i, (_, row) in enumerate(df_filtrado.iterrows()):
        # Fondo alterno
        bg = C_LIGHT_BG if i % 2 == 0 else C_WHITE
        pdf.set_fill_color(*bg)

        cap  = _limpiar_para_pdf(str(row[col_cap]))[:48]
        cost = row[col_val]
        part = row["% Participación"]

        y_row = pdf.get_y()
        row_h = 7

        # Columna: Capítulo
        _rgb(pdf, C_TEXT)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(col_widths[0], row_h, cap, border=0, fill=True,
                 align="L", new_x="END")

        # Columna: Costo
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(col_widths[1], row_h, f"$ {cost:,.0f}", border=0, fill=True,
                 align="R", new_x="END")

        # Columna: Porcentaje
        pdf.set_font("Helvetica", "B", 7.5)
        _rgb(pdf, C_BLUE)
        pdf.cell(col_widths[2], row_h, f"{part:.2f} %", border=0, fill=True,
                 align="C", new_x="END")

        # Columna: mini barra de progreso
        bx = pdf.get_x() + 1
        by = y_row + 2.5
        bw = _generar_mini_barra_progreso(part, bar_max_w)
        bh_rect = 2.8

        # Fondo de la barra (gris claro)
        pdf.set_fill_color(203, 213, 225)
        pdf.rect(bx, by, bar_max_w, bh_rect, "F")

        # Relleno proporcional al porcentaje
        if part >= max_val * 0.75:
            fill_color = C_NAVY
        elif part >= max_val * 0.40:
            fill_color = C_BLUE
        else:
            fill_color = (96, 165, 250)
        pdf.set_fill_color(*fill_color)
        if bw > 0:
            pdf.rect(bx, by, bw, bh_rect, "F")

        pdf.set_fill_color(*bg)
        pdf.cell(col_widths[3], row_h, "", border=0, fill=True,
                 new_x="LMARGIN", new_y="NEXT")

        # Línea horizontal entre filas
        _linea_h(pdf, color=C_BORDER)

    # Fila de total
    total_part = df_filtrado["% Participación"].sum()
    pdf.ln(1)
    pdf.set_fill_color(*C_NAVY)
    pdf.set_font("Helvetica", "B", 8)
    _rgb(pdf, C_WHITE)
    pdf.cell(col_widths[0], 7, "TOTAL PRESUPUESTO", border=0, fill=True, align="L", new_x="END")
    pdf.cell(col_widths[1], 7, f"$ {df_filtrado[col_val].sum():,.0f}", border=0, fill=True,
             align="R", new_x="END")
    pdf.cell(col_widths[2], 7, f"{total_part:.1f} %", border=0, fill=True,
             align="C", new_x="END")
    pdf.cell(col_widths[3], 7, "", border=0, fill=True,
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3 — VISUALIZACIÓN GRÁFICA (BARRAS + DONA)
    # ═══════════════════════════════════════════════════════════════════════════
    _seccion_titulo(pdf, "3", "Análisis Gráfico de Participación")

    buf = generar_grafica_combinada(df_filtrado, col_cap)
    if buf:
        # Si no cabe en la página, saltar a la siguiente
        espacio_restante = pdf.h - pdf.b_margin - pdf.get_y()
        img_h_estimada   = 90
        if espacio_restante < img_h_estimada:
            pdf.add_page()
            _seccion_titulo(pdf, "3", "Análisis Gráfico de Participación (cont.)")

        pdf.image(buf, x=20, w=170)
        buf.close()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4 — NOTAS Y CONSIDERACIONES
    # ═══════════════════════════════════════════════════════════════════════════
    pdf.ln(6)
    _seccion_titulo(pdf, "4", "Notas Técnicas y Consideraciones")

    notas = [
        "Los valores presentados corresponden al presupuesto base del proyecto sin IVA ni AIU.",
        "El porcentaje de participación refleja la proporción de cada capítulo sobre el costo directo total.",
        "La gráfica de dona agrupa capítulos con participación < 3 % bajo la categoría 'Otros'.",
        "Este reporte fue generado automáticamente por el Sistema BI de Mikpho Construcciones.",
        f"Fecha de generación: {date.today().strftime('%d de %B de %Y')}.",
    ]
    pdf.set_font("Helvetica", "", 8)
    _rgb(pdf, C_TEXT)
    for idx, nota in enumerate(notas, start=1):
        pdf.set_x(22)
        # Bullet
        pdf.set_font("Helvetica", "B", 8)
        _rgb(pdf, C_BLUE)
        pdf.cell(4, 5.5, f"{idx}.", new_x="END")
        pdf.set_font("Helvetica", "", 8)
        _rgb(pdf, C_SLATE)
        pdf.cell(0, 5.5, nota, new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════════════════════════
    # PIE DE PÁGINA EN TODAS LAS PÁGINAS
    # ═══════════════════════════════════════════════════════════════════════════
    _agregar_pie_pagina(pdf)

    return bytes(pdf.output())


def _agregar_pie_pagina(pdf: FPDF) -> None:
    """Agrega pie de página a la última página activa."""
    pdf.set_y(-14)
    pdf.set_fill_color(*C_NAVY)
    pdf.rect(0, pdf.get_y() - 1, 210, 16, "F")
    pdf.set_font("Helvetica", "I", 7.5)
    _rgb(pdf, (160, 185, 220))
    pdf.cell(90, 6, f"Mikpho Construcciones  ·  Sistema BI")
    pdf.cell(0, 6, f"Reporte generado el {date.today().strftime('%d/%m/%Y')}  ·  Página {pdf.page_no()}",
             align="R")


# ── EXCEL ─────────────────────────────────────────────────────────────────────

def generar_excel_cronograma(
    datos_editados: pd.DataFrame,
    df_filtrado: pd.DataFrame,
    col_cap: str,
) -> bytes:
    """Genera Excel con dos hojas: Cronograma y Presupuesto."""
    df_export = datos_editados[[
        col_cap, "Fecha de Inicio", "Días Estimados", "% Ejecutado (Real)"
    ]].copy()
    df_export.columns = ["Capítulo", "Fecha Inicio", "Días Estimados", "% Ejecutado"]

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_export.to_excel(writer,   index=False, sheet_name="Cronograma")
        df_filtrado.to_excel(writer, index=False, sheet_name="Presupuesto")
    buf.seek(0)
    return buf.getvalue()


def generar_excel_analisis(df_grp: pd.DataFrame) -> bytes:
    """Genera Excel con el análisis financiero por capítulos."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_grp.to_excel(writer, index=False, sheet_name="Capítulos")
    buf.seek(0)
    return buf.getvalue()


# ── ZIP ───────────────────────────────────────────────────────────────────────

def generar_zip(
    nombre_base: str,
    pdf_bytes: bytes,
    excel_cronograma: bytes,
    excel_analisis: bytes,
) -> bytes:
    """Empaqueta PDF + Excels en un ZIP y retorna los bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"Reporte_{nombre_base}.pdf",     pdf_bytes)
        zf.writestr(f"Cronograma_{nombre_base}.xlsx", excel_cronograma)
        zf.writestr(f"Analisis_{nombre_base}.xlsx",   excel_analisis)
    buf.seek(0)
    return buf.getvalue()