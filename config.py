"""
config.py — Mikpho BI
─────────────────────
Constantes globales, paleta de colores y CSS compartido.
Importar este módulo ANTES que matplotlib en cualquier archivo.
"""

import matplotlib
matplotlib.use('Agg')  # Backend sin GUI — debe setearse antes de cualquier import de pyplot

# ── PALETA DE COLORES ─────────────────────────────────────────────────────────
CYAN        = "#00f2fe"
AZUL        = "#3b82f6"
VERDE       = "#10b981"
AMARILLO    = "#f59e0b"
ROJO        = "#ef4444"
GRIS_OSCURO = "#1f2937"
GRIS_MED    = "#374151"
FONDO       = "#0e1117"
FONDO_CARD  = "#1f2937"
TEXTO_CLARO = "#d1d5db"
TEXTO_GRIS  = "#94a3b8"

# ── COLORES SEMÁFORO ──────────────────────────────────────────────────────────
SEMAFORO = {
    "sin_inicio": "#6b7280",
    "inicio":     ROJO,
    "ejecucion":  AMARILLO,
    "avanzado":   AZUL,
    "cierre":     VERDE,
}

# ── LAYOUT PLOTLY (base reutilizable) ─────────────────────────────────────────
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="white",
)

# ── CSS GLOBAL DE LA APP ──────────────────────────────────────────────────────
CSS_GLOBAL = """
<style>
.main { background-color: #0e1117; }

div[data-testid="metric-container"] {
    background-color: #1f2937;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #00f2fe;
    box-shadow: 0 0 10px rgba(0, 242, 254, 0.2);
}
</style>
"""

# ── PARÁMETROS POR DEFECTO ────────────────────────────────────────────────────
AREA_DEFAULT_1          = 1250.0
AREA_DEFAULT_2          = 1500.0
FILA_HEADER_DEFAULT     = 2
MIN_PORCENTAJE_DEFAULT  = 1.0