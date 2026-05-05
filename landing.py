"""
landing.py  —  Mikpho BI · Pantalla de bienvenida
──────────────────────────────────────────────────
SOLUCIÓN DEFINITIVA:

El iframe de components.html tiene sandbox='allow-scripts' pero NO
allow-top-navigation, por eso window.top, window.parent y postMessage
fallan silenciosamente — es una restricción del navegador, no un bug
de código.

La solución: el botón "ABRIR SISTEMA" es un st.button() nativo de
Streamlit, NO un botón dentro del HTML. El HTML solo muestra la
landing visual. El botón real flota encima con CSS absoluto.

Uso en app.py (sin cambios):

    from landing import mostrar_landing

    if "mostrar_app" not in st.session_state:
        st.session_state["mostrar_app"] = False

    if not st.session_state["mostrar_app"]:
        mostrar_landing()
        st.stop()
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


def _leer_html() -> str:
    ruta = Path(__file__).parent / "mikpho_landing.html"
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró mikpho_landing.html en: {ruta.parent}"
        )
    return ruta.read_text(encoding="utf-8")


def mostrar_landing() -> None:

    # ── 1. CSS global: oculta chrome de Streamlit y posiciona el botón ──
    st.markdown("""
        <style>
            /* Ocultar elementos de Streamlit */
            #MainMenu, header, footer { visibility: hidden; }
            .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }

            /* Botón nativo de Streamlit estilizado como el de la landing */
            div[data-testid="stButton"] > button {
                position: fixed !important;
                top: 14px !important;
                right: 24px !important;
                z-index: 9999 !important;
                background: #00f2fe !important;
                color: #0a0f1e !important;
                font-family: 'Rajdhani', sans-serif !important;
                font-weight: 700 !important;
                font-size: 14px !important;
                letter-spacing: 1px !important;
                padding: 8px 22px !important;
                border-radius: 8px !important;
                border: none !important;
                cursor: pointer !important;
                transition: background 0.2s, transform 0.2s !important;
                box-shadow: 0 0 20px rgba(0,242,254,0.35) !important;
            }
            div[data-testid="stButton"] > button:hover {
                background: #f59e0b !important;
                transform: translateY(-2px) !important;
            }
            /* Ocultar el borde/decoración del contenedor del botón */
            div[data-testid="stButton"] {
                position: fixed !important;
                top: 0 !important;
                right: 0 !important;
                z-index: 9999 !important;
            }
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    # ── 2. Botón NATIVO de Streamlit — este SÍ funciona siempre ─────────
    if st.button("▶ ABRIR SISTEMA", key="btn_abrir_sistema"):
        st.session_state["mostrar_app"] = True
        st.rerun()

    # ── 3. HTML de la landing como fondo visual (solo decorativo) ────────
    # Los botones del HTML NO necesitan funcionar — el botón real
    # es el st.button() de arriba. El HTML es pura presentación.
    try:
        html_content = _leer_html()
    except FileNotFoundError:
        # Si no existe el HTML, mostrar landing mínima de emergencia
        html_content = _landing_minima()

    components.html(
        html_content,
        height=4200,
        scrolling=False,
    )


def _landing_minima() -> str:
    """Landing de emergencia si mikpho_landing.html no existe."""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@700&family=DM+Sans:wght@300;400&display=swap" rel="stylesheet">
    <style>
      *{margin:0;padding:0;box-sizing:border-box}
      body{
        background:#0a0f1e;color:#e2e8f0;
        font-family:'DM Sans',sans-serif;
        min-height:100vh;
        display:flex;flex-direction:column;align-items:center;justify-content:center;
        text-align:center;padding:40px 20px;
        background-image:linear-gradient(rgba(0,242,254,.03) 1px,transparent 1px),
                         linear-gradient(90deg,rgba(0,242,254,.03) 1px,transparent 1px);
        background-size:40px 40px;
      }
      h1{font-family:'Rajdhani',sans-serif;font-size:3rem;font-weight:700;
         color:#fff;margin-bottom:16px;line-height:1.1}
      h1 span{color:#00f2fe}
      p{color:#94a3b8;font-size:1.1rem;max-width:480px;line-height:1.7;margin-bottom:40px}
      .badge{display:inline-flex;align-items:center;gap:8px;
             background:rgba(0,242,254,.08);border:1px solid rgba(0,242,254,.2);
             border-radius:100px;padding:5px 16px;font-size:12px;color:#00f2fe;
             margin-bottom:28px;letter-spacing:1px;text-transform:uppercase}
      .dot{width:6px;height:6px;background:#00f2fe;border-radius:50%;
           animation:pulse 2s infinite}
      @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
      .hint{font-size:13px;color:#475569;margin-top:20px}
      .hint strong{color:#00f2fe}
    </style>
    </head>
    <body>
      <div class="badge"><span class="dot"></span>Sistema activo — Santa Marta</div>
      <h1>MIKPHO <span>INTELLIGENCE</span><br>SYSTEM v2.0</h1>
      <p>Control y Business Intelligence para proyectos de construcción.<br>
         Presupuesto · Cronograma · Ejecución · Proyección</p>
      <p class="hint">Haz clic en <strong>▶ ABRIR SISTEMA</strong> (esquina superior derecha)</p>
    </body>
    </html>
    """