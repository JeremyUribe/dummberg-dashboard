"""Cálculos financieros para Bondora."""

import numpy as np
import pandas as pd


def interpolate_yield(curve_data, date_str, xaxis, value):
    """Calcula la TIR mediante interpolación lineal, sin extrapolar."""

    if not date_str or value is None:
        return None, "Completa la fecha y el plazo objetivo.", None

    date = pd.to_datetime(date_str)

    sub = (
        curve_data[
            curve_data["fecha"].dt.strftime("%Y-%m-%d")
            == date.strftime("%Y-%m-%d")
        ]
        .sort_values(xaxis)
        .dropna(subset=[xaxis, "tir %"])
    )

    sub = sub[
        np.isfinite(sub[xaxis]) & np.isfinite(sub["tir %"])
    ].drop_duplicates(subset=[xaxis])

    if len(sub) < 2:
        return None, "No hay suficientes puntos para interpolar.", date

    xs = sub[xaxis].to_numpy(dtype=float)
    ys = sub["tir %"].to_numpy(dtype=float)

    if value < xs.min() or value > xs.max():
        message = (
            f"El plazo debe estar entre {xs.min():.2f} "
            f"y {xs.max():.2f} años."
        )
        return None, message, date

    yield_value = float(np.interp(value, xs, ys))

    return yield_value, None, date


def calculate_curve_spread(x1, y1, x2, y2, points=70):
    """Calcula el cambio de TIR en puntos básicos entre dos curvas.

    Solo calcula el spread dentro del rango de plazos compartido.
    Devuelve (x, spread) o (None, None) si no hay superposición.
    """

    x1 = np.asarray(x1, dtype=float)
    y1 = np.asarray(y1, dtype=float)
    x2 = np.asarray(x2, dtype=float)
    y2 = np.asarray(y2, dtype=float)

    lo = max(x1.min(), x2.min())
    hi = min(x1.max(), x2.max())

    if lo >= hi:
        return None, None

    xs = np.linspace(lo, hi, points)

    # Las TIR están expresadas en porcentaje:
    # multiplicar su diferencia por 100 convierte el resultado a bps.
    spread = (
        np.interp(xs, x2, y2) - np.interp(xs, x1, y1)
    ) * 100

    return xs, spread


def prepare_selected_curves(curve_data, selected_dates, xaxis):
    """Filtra y prepara los puntos de las curvas SBS seleccionadas.

    Devuelve una lista de curvas listas para graficar.
    No depende de Dash ni de Plotly.
    """

    if curve_data.empty or not selected_dates:
        return []

    dates = pd.to_datetime(selected_dates)

    filtered = curve_data[
        curve_data["fecha"].dt.strftime("%Y-%m-%d").isin(
            dates.strftime("%Y-%m-%d")
        )
    ]

    if filtered.empty:
        return []

    prepared = []

    for date in sorted(filtered["fecha"].dt.normalize().unique()):
        sub = filtered[
            filtered["fecha"].dt.normalize() == date
        ].sort_values(xaxis)

        sub = sub.dropna(subset=[xaxis, "tir %"])

        sub = sub[
            np.isfinite(sub[xaxis])
            & np.isfinite(sub["tir %"])
        ]

        sub = sub.drop_duplicates(
            subset=[xaxis],
            keep="last",
        )

        if len(sub) < 2:
            continue

        prepared.append(
            {
                "date": pd.Timestamp(date),
                "x": sub[xaxis].to_numpy(dtype=float),
                "y": sub["tir %"].to_numpy(dtype=float),
                "labels": sub["nemónico"].tolist(),
            }
        )

    return prepared
