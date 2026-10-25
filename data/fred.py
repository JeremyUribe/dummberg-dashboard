"""Descarga, transformación y caché de datos US Treasury desde FRED."""

from __future__ import annotations

import io
import os
from datetime import datetime, timedelta
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

def _download_official_treasury_data() -> pd.DataFrame:
    """Descarga la curva diaria oficial del Tesoro de EE. UU."""

    year = datetime.now().year

    url = (
        "https://home.treasury.gov/resource-center/"
        "data-chart-center/interest-rates/"
        f"daily-treasury-rates.csv/{year}/all"
        f"?type=daily_treasury_yield_curve"
        f"&field_tdr_date_value={year}&page&_format=csv"
    )

    response = requests.get(url, timeout=(10, 45))
    response.raise_for_status()

    data = pd.read_csv(io.BytesIO(response.content))

    column_mapping = {
        "Date": "date",
        "1 Yr": "US 1Y",
        "2 Yr": "US 2Y",
        "3 Yr": "US 3Y",
        "5 Yr": "US 5Y",
        "7 Yr": "US 7Y",
        "10 Yr": "US 10Y",
        "20 Yr": "US 20Y",
        "30 Yr": "US 30Y",
    }

    data = data.rename(columns=column_mapping)

    required_columns = ["date", *FRED_SERIES.keys()]
    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Faltan columnas en el CSV oficial: {missing_columns}"
        )

    return _clean_treasury_data(data[required_columns])


def _empty_treasury_data() -> pd.DataFrame:
    """Devuelve una estructura vacía con las columnas esperadas."""
    return pd.DataFrame(columns=["date", *FRED_SERIES.keys()])


def _clean_treasury_data(data: pd.DataFrame) -> pd.DataFrame:
    """Valida y limpia fechas y rendimientos de Treasury."""
    if data.empty or "date" not in data.columns:
        return _empty_treasury_data()

    cleaned = data.copy()

    cleaned["date"] = pd.to_datetime(
        cleaned["date"],
        errors="coerce",
    )

    for label in FRED_SERIES:
        if label not in cleaned.columns:
            cleaned[label] = np.nan

        cleaned[label] = pd.to_numeric(
            cleaned[label],
            errors="coerce",
        )

    cleaned = (
        cleaned.dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
        .reset_index(drop=True)
    )

    return cleaned[["date", *FRED_SERIES.keys()]]


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

    response = requests.get(url, params=params, timeout=(5, 15))
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

    out["date"] = pd.to_datetime(
        out["date"],
        errors="coerce",
    )

    out[series_id] = pd.to_numeric(
        out["value"].replace(".", np.nan),
        errors="coerce",
    )

    return out[["date", series_id]].dropna(subset=["date"])


def _download_treasury_data() -> tuple[pd.DataFrame, list]:
    """Descarga y combina las series disponibles de FRED."""
    frames = []
    api_errors = []

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

    if not frames:
        return _empty_treasury_data(), api_errors

    merged = frames[0]

    for frame in frames[1:]:
        merged = merged.merge(
            frame,
            on="date",
            how="outer",
        )

    return _clean_treasury_data(merged), api_errors


def _load_treasury_cache() -> pd.DataFrame:
    """Lee y valida la caché local de Treasury."""
    cached = pd.read_pickle(FRED_CACHE_FILE)
    return _clean_treasury_data(cached)

def _merge_treasury_data(
    cached: pd.DataFrame,
    downloaded: pd.DataFrame,
) -> pd.DataFrame:
    """Combina datos descargados con la caché, conservando valores históricos."""

    cached = _clean_treasury_data(cached)
    downloaded = _clean_treasury_data(downloaded)

    if cached.empty:
        return downloaded

    if downloaded.empty:
        return cached

    cached = cached.set_index("date")
    downloaded = downloaded.set_index("date")

    # Prioriza los datos descargados y completa los valores faltantes
    # con los datos que ya estaban guardados.
    merged = downloaded.combine_first(cached)

    return (
        merged.reset_index()
        .sort_values("date")
        .reset_index(drop=True)
    )


def load_treasury() -> tuple[pd.DataFrame, str]:
    """Carga Treasury desde FRED y complementa con la curva oficial."""

    cached = _empty_treasury_data()

    if FRED_CACHE_FILE.exists():
        try:
            cached = _load_treasury_cache()
        except Exception as exc:
            print(f"No se pudo cargar la caché FRED: {exc}")

    # Comprobar la antigüedad de la caché antes de descargar
    # datos oficiales, para no alterar el control de 12 horas.
    cache_age = None

    if not cached.empty and FRED_CACHE_FILE.exists():
        cache_age = (
            datetime.now()
            - datetime.fromtimestamp(FRED_CACHE_FILE.stat().st_mtime)
        )

    # Consultar la curva diaria oficial del Tesoro de EE. UU.
    official = _empty_treasury_data()

    try:
        official = _download_official_treasury_data()
    except Exception as exc:
        print(f"No se pudo descargar la curva oficial del Tesoro: {exc}")

    def save_cache(data: pd.DataFrame) -> None:
        try:
            FRED_CACHE_FILE.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            data.to_pickle(FRED_CACHE_FILE)
        except Exception as exc:
            print(f"No se pudo guardar la caché Treasury: {exc}")

    # Si la caché es reciente, conservarla y complementarla
    # con los datos oficiales sin reiniciar su antigüedad.
    if (
        not cached.empty
        and cache_age is not None
        and cache_age < timedelta(hours=12)
    ):
        combined = _merge_treasury_data(cached, official)

        if not official.empty:
            latest_date = pd.to_datetime(official["date"]).max()
            status = (
                "Tesoro oficial + caché histórica "
                f"· último dato {latest_date.strftime('%d/%m/%Y')}"
            )
        else:
            status = (
                "FRED · caché local "
                "(no se pudo consultar el Tesoro oficial)"
            )

        return combined, status

    # Actualizar FRED cuando la caché ya no es reciente.
    if FRED_API_KEY:
        downloaded, api_errors = _download_treasury_data()
    else:
        downloaded, api_errors = _empty_treasury_data(), []

    if downloaded.empty:
        combined = _merge_treasury_data(cached, official)

        if not combined.empty:
            if not cached.empty:
                status = "Tesoro oficial + caché histórica"
            else:
                status = "Tesoro oficial · sin histórico de FRED"

            if not official.empty:
                latest_date = pd.to_datetime(official["date"]).max()
                status += (
                    f" · último dato {latest_date.strftime('%d/%m/%Y')}"
                )

            save_cache(combined)
            return combined, status

        error_detail = "; ".join(api_errors[:2])

        return (
            _empty_treasury_data(),
            "No se pudieron obtener datos de Treasury"
            + (f": {error_detail}" if error_detail else ""),
        )

    # Conservar el histórico de la caché y FRED.
    combined = _merge_treasury_data(cached, downloaded)

    # La fuente oficial complementa y prevalece sobre FRED
    # en las fechas para las que proporciona observaciones.
    combined = _merge_treasury_data(combined, official)

    save_cache(combined)

    status = (
        "FRED + Tesoro oficial · actualización consultada "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    if not official.empty:
        latest_date = pd.to_datetime(official["date"]).max()
        status += (
            f" · último dato oficial {latest_date.strftime('%d/%m/%Y')}"
        )

    if api_errors:
        status += (
            f" · avisos en {len(api_errors)} serie(s); "
            "se conservaron los datos disponibles"
        )

    return combined, status


