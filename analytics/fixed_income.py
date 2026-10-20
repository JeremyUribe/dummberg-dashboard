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
