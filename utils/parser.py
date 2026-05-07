"""
utils/parser.py — Mikpho BI
────────────────────────────
Funciones de limpieza y transformación de datos crudos desde Excel.
Sin dependencias de Streamlit — puro pandas/re/unicodedata.
"""

import re
import unicodedata
from datetime import date
from typing import List, Optional

import pandas as pd


def limpiar_texto(texto) -> str:
    """Normaliza unicode y quita espacios extremos."""
    if not isinstance(texto, str):
        texto = str(texto)
    return unicodedata.normalize('NFKC', texto).strip()


def limpiar_valor_numerico(serie: pd.Series) -> pd.Series:
    """
    Convierte una serie de strings con formatos numéricos mixtos a float.
    Maneja separadores de miles con punto (1.234.567,89) y con coma (1,234,567.89).
    Valores no parseables se convierten a 0.0.
    """
    def parsear(val) -> float:
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


def obtener_hojas(archivo) -> List[str]:
    """Retorna la lista de hojas de un archivo Excel."""
    hojas = pd.ExcelFile(archivo).sheet_names
    return [str(h) for h in hojas] if hojas is not None else []


def cargar_excel(archivo, hoja: str, fila_encabezado: int) -> pd.DataFrame:
    """
    Lee un archivo Excel y devuelve un DataFrame limpio.
    - Valida que la hoja tenga suficientes filas antes de leer
    - Normaliza nombres de columnas
    - Elimina filas/columnas completamente vacías
    """
    df_preview = pd.read_excel(
        archivo, sheet_name=hoja, header=None, nrows=fila_encabezado + 2
    )
    if len(df_preview) <= fila_encabezado:
        raise ValueError(
            f"La hoja '{hoja}' solo tiene {len(df_preview)} fila(s), "
            f"pero el calibrador apunta a la fila {fila_encabezado}. "
            f"Ajusta el valor en el Calibrador de Datos."
        )
    df = pd.read_excel(archivo, sheet_name=hoja, header=fila_encabezado)
    df.columns = [limpiar_texto(c) for c in df.columns]
    df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)
    return df


def procesar_proyecto(
    archivo,
    hoja: str,
    fila_encabezado: int,
    col_cap: str,
    col_val: str,
    area: float,
    nombre: str,
) -> Optional[dict]:
    """
    Carga y procesa un archivo de presupuesto.
    Retorna dict con: nombre, df_grp, total, m2, area
    Retorna None si las columnas no existen o el archivo está vacío.
    """
    df = cargar_excel(archivo, hoja, fila_encabezado)

    if col_cap not in df.columns or col_val not in df.columns:
        return None

    df[col_cap] = df[col_cap].apply(limpiar_texto)
    df = df[df[col_cap].str.strip() != ''].copy()
    df[col_val] = limpiar_valor_numerico(df[col_val])

    costo_total = df[col_val].sum()
    valor_m2    = costo_total / area if area > 0 else 0.0

    df_grp = (
        df.groupby(col_cap, sort=False)[col_val]
        .sum()
        .reset_index()
    )
    df_grp = df_grp[df_grp[col_val] > 0].copy()
    df_grp['Proyecto']        = nombre
    df_grp['% Participación'] = (
        df_grp[col_val] / costo_total * 100 if costo_total > 0 else 0.0
    )

    return {
        "nombre": nombre,
        "df_grp": df_grp,
        "total":  costo_total,
        "m2":     valor_m2,
        "area":   area,
    }


def construir_df_tiempos(
    df_grp: pd.DataFrame,
    col_cap: str,
    col_val: str,
    min_pct: float,
) -> pd.DataFrame:
    """
    Construye el DataFrame base para el cronograma (Gantt / Curva S).
    Solo incluye capítulos con participación >= min_pct.
    """
    df = df_grp[df_grp['% Participación'] >= min_pct][[col_cap, col_val]].copy()
    df["Fecha de Inicio"]      = date.today()
    df["Días Estimados"]       = 30
    df["Días Estimados"]       = df["Días Estimados"].astype(int)
    df["% Ejecutado (Real)"]   = 0.0
    df = df.dropna(subset=[col_cap]).reset_index(drop=True)
    return df