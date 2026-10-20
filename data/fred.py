"""Descarga, transformación y caché de datos US Treasury desde FRED."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent

FRED_API_KEY = os.getenv("FRED_API_KEY", "").strip()

FRED_CACHE_FILE = Path(
    os.getenv(
        "FRED_CACHE_FILE",
        str(BASE_DIR / "us_treasury_fred.pkl"),
    )
)

FRED_SERIES = {
    "US 1Y": "DGS1",
    "US 2Y": "DGS2",
    "US 3Y": "DGS3",
    "US 5Y": "DGS5",
    "US 7Y": "DGS7",
    "US 10Y": "DGS10",
    "US 20Y": "DGS20",
    "US 30Y": "DGS30",
}

TENOR_YEARS = {
    "US 1Y": 1,
    "US 2Y": 2,
    "US 3Y": 3,
    "US 5Y": 5,
    "US 7Y": 7,
    "US 10Y": 10,
    "US 20Y": 20,
    "US 30Y": 30,
}


def load_fred_series(
    series_id: str,
    api_key: str,
    start_date: str = "1990-01-01",
) -> pd.DataFrame:
    """Descarga una serie individual de observaciones de FRED."""

    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "sort_order": "asc",
    }

    response = requests.get(url, params=params, timeout=25)
    response.raise_for_status()

    payload = response.json()

    if "error_code" in payload:
        raise RuntimeError(
            payload.get("error_message", "FRED API error")
        )

    observations = payload.get("observations", [])
    out = pd.DataFrame(observations, columns=["date", "value"])

    if out.empty:
        return pd.DataFrame(columns=["date", series_id])

    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    out[series_id] = pd.to_numeric(
        out["value"].replace(".", np.nan),
        errors="coerce",
    )

    return out[["date", series_id]].dropna(subset=["date"])


def load_treasury() -> tuple[pd.DataFrame, str]:
    """Carga las series Treasury desde FRED o desde la caché local."""

    frames = []
    api_errors = []

    if FRED_API_KEY:
        for label, series_id in FRED_SERIES.items():
            try:
                series_df = load_fred_series(
                    series_id,
                    FRED_API_KEY,
                )
                series_df = series_df.rename(
                    columns={series_id: label}
                )
                frames.append(series_df)

            except Exception as exc:
                api_errors.append(f"{series_id}: {exc}")

        if frames:
            merged = frames[0]

            for frame in frames[1:]:
                merged = merged.merge(
                    frame,
                    on="date",
                    how="outer",
                )

            merged = (
                merged.sort_values("date")
                .drop_duplicates("date", keep="last")
                .reset_index(drop=True)
            )

            try:
                merged.to_pickle(FRED_CACHE_FILE)
            except Exception as exc:
                print(f"No se pudo guardar la caché FRED: {exc}")

            status = (
                "FRED · actualización consultada "
                f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )

            if api_errors:
                status += (
                    f" · avisos en {len(api_errors)} serie(s); "
                    "se conservaron las disponibles"
                )

            return merged, status

    # Sin API key o sin descargas disponibles: intentar recuperar caché.
    try:
        cached = pd.read_pickle(FRED_CACHE_FILE)

        if not cached.empty and "date" in cached.columns:
            cached["date"] = pd.to_datetime(
                cached["date"], errors="coerce"
            )

            for label in FRED_SERIES:
                if label not in cached.columns:
                    cached[label] = np.nan

            cached = (
                cached.sort_values("date")
                .reset_index(drop=True)
            )

            return cached, "FRED · datos de caché local"

    except Exception as exc:
        print(f"No se pudo cargar la caché FRED: {exc}")

    empty = pd.DataFrame(columns=["date", *FRED_SERIES])

    if not FRED_API_KEY:
        return (
            empty,
            "Configura FRED_API_KEY para descargar datos de FRED",
        )

    return (
        empty,
        "No se pudieron descargar los datos de FRED: "
        + "; ".join(api_errors[:2]),
    )

