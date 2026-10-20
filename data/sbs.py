"""Carga y preparación de datos de renta fija de la SBS."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

SBS_FILE = Path(
    os.getenv(
        "SBS_DATA_FILE",
        str(BASE_DIR / "vector_precios_unido_pen.pkl"),
    )
)

EXCLUDED_ISIN = "PEP01000C4R4"

REQUIRED_COLUMNS = {
    "isin",
    "fecha",
    "f. vencimiento",
    "emisor",
    "moneda",
    "tir %",
    "nemónico",
}


def load_sbs():
    """Carga y transforma los datos SBS para el dashboard.

    Returns:
        df: base completa de instrumentos procesados.
        df_curve: observaciones de deuda soberana en PEN.
        date_options: opciones de fechas para Dash.
        search_options: opciones de búsqueda de instrumentos.
        default_dates: fecha seleccionada por defecto.
        default_search: instrumento seleccionado por defecto.
    """
    try:
        raw = pd.read_pickle(SBS_FILE)
    except Exception as exc:
        print(f"No se pudo cargar el archivo SBS {SBS_FILE}: {exc}")
        return pd.DataFrame(), pd.DataFrame(), [], [], [], None

    if raw.empty:
        return raw, pd.DataFrame(), [], [], [], None

    missing = REQUIRED_COLUMNS.difference(raw.columns)

    if missing:
        print(
            "El archivo SBS no contiene columnas requeridas: "
            f"{sorted(missing)}"
        )
        return pd.DataFrame(), pd.DataFrame(), [], [], [], None

    df = raw.copy()

    df = df[df["isin"].astype(str) != EXCLUDED_ISIN].copy()

    df["fecha"] = pd.to_datetime(
        df["fecha"], dayfirst=True, errors="coerce"
    )
    df["f. vencimiento"] = pd.to_datetime(
        df["f. vencimiento"], dayfirst=True, errors="coerce"
    )
    df["tir %"] = pd.to_numeric(df["tir %"], errors="coerce")

    if "p. limpio (%)" in df.columns:
        df["p. limpio (%)"] = pd.to_numeric(
            df["p. limpio (%)"], errors="coerce"
        )
    else:
        df["p. limpio (%)"] = np.nan

    df = df.dropna(subset=["fecha", "f. vencimiento"]).copy()

    df["maturity"] = (
        df["f. vencimiento"] - df["fecha"]
    ).dt.days / 365.25

    df["busqueda"] = (
        df["isin"].astype(str)
        + " | "
        + df["nemónico"].astype(str)
    )

    df_curve = df[
        (df["emisor"] == "GOB.CENTRAL")
        & (df["moneda"] == "PEN")
    ].copy()

    dates = sorted(
        df_curve["fecha"].dt.normalize().dropna().unique()
    )

    date_options = [
        {
            "label": pd.Timestamp(date).strftime("%d/%m/%Y"),
            "value": pd.Timestamp(date).strftime("%Y-%m-%d"),
        }
        for date in dates
    ]

    search_options = [
        {"label": value, "value": value}
        for value in sorted(df["busqueda"].dropna().unique())
    ]

    default_dates = (
        [pd.Timestamp(dates[-1]).strftime("%Y-%m-%d")]
        if dates
        else []
    )

    default_search = (
        search_options[0]["value"] if search_options else None
    )

    return (
        df,
        df_curve,
        date_options,
        search_options,
        default_dates,
        default_search,
    )
