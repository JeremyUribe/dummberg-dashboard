"""Bondora — Fixed Income Research

Datos locales SBS: vector_precios_unido_pen.pkl
Datos US Treasury: FRED API (variable de entorno FRED_API_KEY)

Dependencias: pip install dash pandas numpy plotly requests
"""
from __future__ import annotations

import os

from analytics.fixed_income import (
    interpolate_yield,
    calculate_curve_spread,
    prepare_selected_curves,
)

import numpy as np
import pandas as pd

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# Configuración
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Configuración e importación de datos
# -----------------------------------------------------------------------------
from data.sbs import load_sbs
from data.fred import load_treasury, FRED_SERIES, TENOR_YEARS
from components.charts import (
    INK,
    MUTED,
    GRID,
    PAPER,
    WHITE,
    NAVY,
    RUST,
    TEAL,
    GOLD,
    PALETTE,
    section_label,
    plot_layout,
    empty_figure,
)



# -----------------------------------------------------------------------------
# Carga SBS
# -----------------------------------------------------------------------------

df, df_curve, fecha_options, busqueda_options, default_fecha, default_busqueda = load_sbs()

# -----------------------------------------------------------------------------
# US Treasury / FRED
# -----------------------------------------------------------------------------

df_treasury, fred_status = load_treasury()

TREASURY_TENORS = list(FRED_SERIES.keys())

treasury_dates = (
    df_treasury["date"].dt.strftime("%Y-%m-%d").tolist()
    if not df_treasury.empty
    else []
)

treasury_date_options = [
    {
        "label": pd.to_datetime(date).strftime("%d/%m/%Y"),
        "value": date,
    }
    for date in treasury_dates
]

treasury_default_date = (
    [treasury_dates[-1]] if treasury_dates else []
)

# -----------------------------------------------------------------------------
# Helpers de diseño y gráficos
# -----------------------------------------------------------------------------


def build_overview():
    if df_curve.empty:
        return html.Div(className="overview-strip", children=[html.Div("SBS", className="overview-kicker"), html.Div("No se pudo cargar la base de datos local", className="overview-note")])
    latest_date = df_curve["fecha"].max().normalize()
    latest = df_curve[df_curve["fecha"].dt.normalize() == latest_date]
    stats = [
        ("OBSERVACIÓN MÁS RECIENTE", latest_date.strftime("%d %b %Y")),
        ("BONOS EN CURVA", f"{len(latest):,}"),
        ("TIR MÍNIMA", f"{latest['tir %'].min():.2f}%" if latest["tir %"].notna().any() else "—"),
        ("TIR MÁXIMA", f"{latest['tir %'].max():.2f}%" if latest["tir %"].notna().any() else "—"),
        ("FECHAS HISTÓRICAS", f"{df_curve['fecha'].dt.normalize().nunique():,}"),
    ]
    return html.Div(className="overview-strip", children=[
        html.Div(className="overview-heading", children=[html.Div("MARKET SNAPSHOT", className="overview-kicker"), html.Div("Perú · Deuda soberana en PEN", className="overview-note")]),
        *[html.Div(className="overview-stat", children=[html.Div(k, className="stat-label"), html.Div(v, className="stat-value")]) for k, v in stats]
    ])

# -----------------------------------------------------------------------------
# App / CSS
# -----------------------------------------------------------------------------
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=False)
app.title = "Bondora — Fixed Income Research"

# SEO: robots.txt y sitemap.xml para buscadores
# -----------------------------------------------------------------------------

@app.server.route("/robots.txt")
def robots_txt():
    contenido = (
        "User-agent: *\n"
        "Disallow:\n"
        "\n"
        "Sitemap: https://bondora.onrender.com/sitemap.xml\n"
    )
    return Response(contenido, mimetype="text/plain")


@app.server.route("/sitemap.xml")
def sitemap_xml():
    contenido = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://bondora.onrender.com/</loc>
    </url>
</urlset>"""
    return Response(contenido, mimetype="application/xml")


app.index_string = '''<!DOCTYPE html>
<html><head>{%metas%}<title>{%title%}</title>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-DQNC632HM7"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-DQNC632HM7');
</script>
{%css%}
<style>
*{box-sizing:border-box}html,body{margin:0;background:#F5F4EF;color:#202923;font-family:'IBM Plex Sans',sans-serif;-webkit-font-smoothing:antialiased}
:root{--paper:#F5F4EF;--white:#fff;--ink:#202923;--muted:#777B73;--line:#DCDCD3;--navy:#243B53;--rust:#B65F43;--teal:#487A72;--mono:'IBM Plex Mono',monospace}
.shell{min-height:100vh;display:flex;flex-direction:column}.topbar{height:62px;background:#F5F4EF;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 clamp(18px,4vw,58px);position:sticky;top:0;z-index:100}
.brand{display:flex;align-items:baseline;gap:14px}.brand-name{font-family:var(--mono);font-size:21px;font-weight:600;letter-spacing:-1.4px}.brand-divider{height:19px;border-left:1px solid #BDBFB6}.brand-sub{font-family:var(--mono);font-size:10px;letter-spacing:1.3px;color:var(--muted);text-transform:uppercase}.top-meta{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.7px}
.main{width:100%;max-width:1540px;margin:0 auto;padding:32px clamp(18px,4vw,58px) 54px}.page-intro{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding:5px 0 24px;border-bottom:1px solid var(--line);margin-bottom:22px}.eyebrow{font-family:var(--mono);font-size:10px;letter-spacing:1.7px;color:var(--rust);text-transform:uppercase;margin-bottom:12px}.page-title{font-size:clamp(28px,3vw,42px);font-weight:500;letter-spacing:-1.7px;line-height:1.1;margin:0 0 9px}.page-description{font-size:13px;color:var(--muted);line-height:1.6;max-width:660px}.page-code{text-align:right;font-family:var(--mono);font-size:10px;line-height:1.9;color:var(--muted);white-space:nowrap}
.overview-strip{display:flex;align-items:stretch;gap:0;background:#ECEBE4;border:1px solid var(--line);margin:0 0 28px;flex-wrap:wrap}.overview-heading{padding:17px 20px;min-width:205px;flex:1.25}.overview-kicker{font-family:var(--mono);font-size:10px;letter-spacing:1.2px;color:var(--muted);margin-bottom:7px}.overview-note{font-size:13px;color:var(--ink)}.overview-stat{padding:17px 19px;border-left:1px solid #D5D5CC;min-width:130px;flex:1}.stat-label{font-family:var(--mono);font-size:9px;letter-spacing:.6px;color:var(--muted);line-height:1.5;margin-bottom:7px}.stat-value{font-family:var(--mono);font-size:18px;font-weight:500;letter-spacing:-.6px;color:var(--ink);white-space:nowrap}
.section{background:var(--white);border:1px solid var(--line);margin-bottom:22px}.section-head{min-height:47px;display:flex;align-items:center;gap:12px;padding:0 19px;border-bottom:1px solid #E9E8E1}.section-number{font-family:var(--mono);font-size:10px;color:var(--rust)}.section-title{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:1.1px;color:#4D554E}.section-meta{margin-left:auto;font-family:var(--mono);font-size:10px;color:#92958D}.section-body{padding:17px 19px}.control-grid{display:grid;grid-template-columns:minmax(220px,1fr) minmax(180px,260px);gap:20px;align-items:end}.control-grid.three{grid-template-columns:minmax(220px,1fr) minmax(170px,220px) minmax(150px,190px)}.field-label{font-family:var(--mono);font-size:10px;letter-spacing:.5px;color:var(--muted);display:block;margin-bottom:7px}.field-note{font-size:11px;color:#92958D;margin-top:6px;line-height:1.5}.radio-wrap label{display:inline-flex;align-items:center;margin:5px 16px 5px 0;font-size:12px;color:#4D554E;cursor:pointer}.radio-wrap input{accent-color:var(--navy);margin-right:6px}
.dash-dropdown .Select-control,.dash-dropdown .Select__control{border-radius:0!important;border-color:var(--line)!important;box-shadow:none!important;font-family:'IBM Plex Sans',sans-serif!important;font-size:12px!important}.dash-dropdown .Select-control:hover{border-color:#A9ACA2!important}.dash-dropdown .Select-menu-outer{z-index:200!important}.result-box{display:flex;align-items:center;gap:20px;padding:15px 17px;margin-top:14px;border:1px solid #D8DFD9;background:#F5F7F3}.result-label{font-family:var(--mono);font-size:10px;letter-spacing:.7px;color:var(--teal);margin-bottom:5px}.result-value{font-family:var(--mono);font-size:25px;color:#315F56}.result-meta{margin-left:auto;text-align:right;color:var(--muted);font-family:var(--mono);font-size:10px;line-height:1.8}.error-box{border-color:#E8D4CC;background:#FBF4F1}.error-box .result-label,.error-box .result-value{color:var(--rust)}
.action-button{font-family:var(--mono);font-size:11px;padding:10px 17px;border:1px solid var(--navy);background:var(--navy);color:#fff;cursor:pointer;transition:background .15s}.action-button:hover{background:#182B3C}.footer{border-top:1px solid var(--line);padding:15px clamp(18px,4vw,58px);display:flex;justify-content:space-between;gap:15px;color:var(--muted);font-family:var(--mono);font-size:10px}.footer span:last-child{text-align:right}.fred-status{font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:8px;line-height:1.5}.source-link{color:var(--navy)}
@media(max-width:800px){.page-intro{align-items:flex-start;flex-direction:column}.page-code{text-align:left}.overview-heading{min-width:100%;border-bottom:1px solid #D5D5CC}.overview-stat{min-width:33%;border-left:0;border-top:1px solid #D5D5CC}.overview-stat:nth-child(odd){border-left:1px solid #D5D5CC}.control-grid,.control-grid.three{grid-template-columns:1fr}.section-body{padding:13px}.section-head{padding:0 13px}.top-meta{display:none}.footer{flex-direction:column}.footer span:last-child{text-align:left}}
._dash-loading{visibility:hidden}.dash-spinner{display:none!important}
</style></head><body><div class="shell"><nav class="topbar"><div class="brand"><span class="brand-name">bondora</span><span class="brand-divider"></span><span class="brand-sub">Fixed Income Research</span></div><div class="top-meta">MARKET DATA / CURVE ANALYTICS</div></nav>{%app_entry%}<footer class="footer"><span>Bondora · Independent fixed-income analytics</span><span>SBS · Ministerio de Economía y Finanzas / FRED · Federal Reserve Bank of St. Louis</span></footer></div><footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''

app.layout = html.Div(className="main", children=[
    html.Div(className="page-intro", children=[
        html.Div(children=[html.Div("MARKETS / CURVES / HISTORICAL DATA", className="eyebrow"),
            html.H1("Sovereign yield curves", className="page-title"),
            html.Div("Análisis de rendimientos, spreads y series históricas para renta fija local e internacional.", className="page-description")]),
        html.Div([html.Div("RESEARCH NOTE  /  01"), html.Div("PEN  ·  USD"), html.Div("DAILY OBSERVATIONS")], className="page-code")
    ]),
    build_overview(),

    html.Div(className="section", children=[
        section_label("01", "Perú · Curva soberana", "SBS / PEN"),
        html.Div(className="section-body", children=[
            html.Div(className="control-grid", children=[
                html.Div([html.Label("Fechas de comparación", className="field-label"), dcc.Dropdown(id="dropdown-fechas", options=fecha_options, value=default_fecha, multi=True, placeholder="Selecciona una o más fechas", className="dash-dropdown")]),
                html.Div([html.Label("Variable del eje horizontal", className="field-label"), dcc.RadioItems(id="radio-xaxis", options=[{"label":"Duración","value":"duración"},{"label":"Madurez","value":"maturity"}], value="duración", className="radio-wrap")])
            ]),
            html.Div("Selecciona varias fechas para comparar desplazamientos y cambios de pendiente en la curva.", className="field-note")
        ]),
        dcc.Graph(id="graph-curve", config={"displayModeBar":True,"modeBarButtonsToRemove":["select2d","lasso2d","autoScale2d"],"displaylogo":False})
    ]),

    html.Div(className="section", children=[section_label("02", "Cambio entre curvas", "BPS"), dcc.Graph(id="graph-spread", config={"displayModeBar":False,"displaylogo":False})]),

    html.Div(className="section", children=[
        section_label("03", "Consulta de yield interpolada", "LINEAR INTERPOLATION"),
        html.Div(className="section-body", children=[
            html.Div(className="control-grid three", children=[
                html.Div([html.Label("Fecha de la curva", className="field-label"), dcc.Dropdown(id="interp-fecha", options=fecha_options, value=default_fecha[0] if default_fecha else None, placeholder="Selecciona fecha", clearable=False, className="dash-dropdown")]),
                html.Div([html.Label("Eje de interpolación", className="field-label"), dcc.Dropdown(id="interp-xaxis", options=[{"label":"Duración (años)","value":"duración"},{"label":"Madurez (años)","value":"maturity"}], value="duración", clearable=False, className="dash-dropdown")]),
                html.Div([html.Label("Plazo objetivo (años)", className="field-label"), dcc.Input(id="interp-valor", type="number", placeholder="Ej. 5.5", min=0, step=0.01, className="field-input", style={"width":"100%","padding":"10px","border":"1px solid #DCDCD3","fontFamily":"IBM Plex Mono","fontSize":"12px"})]),
            ]),
            html.Div(style={"marginTop":"13px"}, children=[html.Button("Calcular yield", id="interp-btn", n_clicks=0, className="action-button")]),
            html.Div(id="interp-result")
        ])
    ]),

    html.Div(className="section", children=[
        section_label("04", "Histórico por instrumento", "SBS / ISIN"),
        html.Div(className="section-body", children=[
            html.Div(className="control-grid", children=[
                html.Div([html.Label("Instrumento", className="field-label"), dcc.Dropdown(id="dropdown-busqueda", options=busqueda_options, value=default_busqueda, placeholder="Busca por ISIN o nemónico", className="dash-dropdown")]),
                html.Div([html.Label("Métrica", className="field-label"), dcc.RadioItems(id="radio-metric", options=[{"label":"TIR (%)","value":"tir %"},{"label":"Precio limpio (%)","value":"p. limpio (%)"}], value="tir %", className="radio-wrap")])
            ])
        ]),
        dcc.Graph(id="graph-historical", config={"displayModeBar":True,"modeBarButtonsToRemove":["select2d","lasso2d"],"displaylogo":False})
    ]),

    html.Div(className="section", children=[
        section_label("05", "US Treasury · Curva del Tesoro", "FRED / USD"),
        html.Div(className="section-body", children=[
            html.Div(className="control-grid", children=[
                html.Div([html.Label("Fechas de comparación", className="field-label"), dcc.Dropdown(id="treasury-dates", options=treasury_date_options, value=treasury_default_date, multi=True, placeholder="Selecciona fechas", className="dash-dropdown")]),
                html.Div([html.Label("Plazo para la serie histórica", className="field-label"), dcc.Dropdown(id="treasury-tenor", options=[{"label":k,"value":k} for k in TREASURY_TENORS], value="US 10Y", clearable=False, className="dash-dropdown")])
            ]),
            html.Div(fred_status, className="fred-status", id="fred-status")
        ]),
        html.Div(className="section-body", children=[html.Div("CURVE SNAPSHOT", className="field-label"), dcc.Graph(id="graph-treasury-curve", config={"displayModeBar":False,"displaylogo":False})]),
        html.Div(className="section-body", style={"borderTop":"1px solid #E9E8E1"}, children=[html.Div("HISTORICAL YIELD", className="field-label"), dcc.Graph(id="graph-treasury-history", config={"displayModeBar":False,"displaylogo":False})])
    ])
])

# -----------------------------------------------------------------------------
# Callbacks SBS
# -----------------------------------------------------------------------------
@app.callback(
    [Output("graph-curve", "figure"), Output("graph-spread", "figure")],
    [Input("dropdown-fechas", "value"), Input("radio-xaxis", "value")]
)
def update_curves(selected_dates, xaxis):
    if df_curve.empty or not selected_dates:
        return (
            empty_figure("No hay datos para las fechas seleccionadas"),
            empty_figure("Selecciona al menos dos fechas"),
        )

    dates = pd.to_datetime(selected_dates)

    curve_data = df_curve[
        df_curve["fecha"].dt.strftime("%Y-%m-%d").isin(
            dates.strftime("%Y-%m-%d")
        )
    ]

    if curve_data.empty:
        return (
            empty_figure("No hay observaciones para esta selección"),
            empty_figure("Sin datos"),
        )

    x_title = (
        "Duración (años)"
        if xaxis == "duración"
        else "Madurez (años)"
    )

    fig_curve = go.Figure()
    interpolated = {}

    prepared_curves = prepare_selected_curves(
        df_curve,
        selected_dates,
        xaxis,
    )

    for i, curve in enumerate(prepared_curves):
        date = curve["date"]
        x = curve["x"]
        y = curve["y"]
        labels = curve["labels"]

        xi = np.linspace(x.min(), x.max(), 180)
        yi = np.interp(xi, x, y)

        interpolated[date] = (xi, yi)
        color = PALETTE[i % len(PALETTE)]

        fig_curve.add_trace(
            go.Scatter(
                x=xi,
                y=yi,
                mode="lines",
                name=date.strftime("%d/%m/%Y"),
                line=dict(width=2.2, color=color),
                hovertemplate=(
                    "%{x:.2f} años · %{y:.3f}%"
                    "<extra>%{fullData.name}</extra>"
                ),
            )
        )

        fig_curve.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                marker=dict(
                    size=6,
                    color=color,
                    line=dict(width=1, color=WHITE),
                ),
                text=labels,
                showlegend=False,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "%{x:.2f} años · %{y:.3f}%"
                    "<extra></extra>"
                ),
            )
        )

    fig_curve.update_layout(
        **plot_layout(x_title, "TIR (%)", 390)
    )

    fig_spread = go.Figure()

    if len(interpolated) >= 2:
        first, last = sorted(interpolated)[0], sorted(interpolated)[-1]

        x1, y1 = interpolated[first]
        x2, y2 = interpolated[last]

        xs, spread = calculate_curve_spread(x1, y1, x2, y2)

        if xs is not None:
            colors = [
                TEAL if value >= 0 else RUST
                for value in spread
            ]

            fig_spread.add_trace(
                go.Bar(
                    x=xs,
                    y=spread,
                    marker_color=colors,
                    marker_line_width=0,
                    name=f"{last:%d/%m/%Y} − {first:%d/%m/%Y}",
                    hovertemplate=(
                        "%{x:.2f} años · "
                        "<b>%{y:.1f} bps</b><extra></extra>"
                    ),
                )
            )

            fig_spread.add_hline(
                y=0,
                line_color="#AEB1A8",
                line_width=1,
            )

    if not fig_spread.data:
        fig_spread.add_annotation(
            text=(
                "Selecciona dos o más curvas con "
                "rangos de plazo superpuestos"
            ),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(color=MUTED, size=12),
        )

    layout = plot_layout(x_title, "Cambio (bps)", 250)
    layout["bargap"] = 0.12
    fig_spread.update_layout(**layout)

    return fig_curve, fig_spread


@app.callback(
    Output("interp-result", "children"), Input("interp-btn", "n_clicks"),
    [State("interp-fecha", "value"), State("interp-xaxis", "value"), State("interp-valor", "value")],
    prevent_initial_call=True
)
def calc_interpolation(n_clicks, date_str, xaxis, value):
    yield_value, error_message, date = interpolate_yield(
        df_curve,
        date_str,
        xaxis,
        value,
    )

    if error_message:
        return html.Div(
            className="result-box error-box",
            children=[
                html.Div(
                    [
                        html.Div(
                            "NO DISPONIBLE",
                            className="result-label",
                        ),
                        html.Div(
                            error_message,
                            className="result-value",
                            style={"fontSize": "14px"},
                        ),
                    ]
                )
            ],
        )

    return html.Div(
        className="result-box",
        children=[
            html.Div(
                [
                    html.Div(
                        "YIELD INTERPOLADA",
                        className="result-label",
                    ),
                    html.Div(
                        f"{yield_value:.4f}%",
                        className="result-value",
                    ),
                ]
            ),
            html.Div(
                [
                    html.Div(f"{value:.2f} años"),
                    html.Div(date.strftime("%d/%m/%Y")),
                    html.Div("Interpolación lineal"),
                ],
                className="result-meta",
            ),
        ],
    )



@app.callback(Output("graph-historical", "figure"), [Input("dropdown-busqueda", "value"), Input("radio-metric", "value")])
def update_history(search_value, metric):
    if df.empty or not search_value or metric not in df.columns:
        return empty_figure("Selecciona un instrumento para ver su historia")
    isin = search_value.split(" | ")[0]
    sub = df[df["isin"].astype(str) == isin].sort_values("fecha").dropna(subset=[metric])
    if sub.empty:
        return empty_figure("No hay observaciones para esta métrica")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub["fecha"], y=sub[metric], mode="lines", line=dict(width=1.8, color=NAVY), name=metric, hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:.3f}</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=[sub["fecha"].iloc[-1]], y=[sub[metric].iloc[-1]], mode="markers", marker=dict(size=7, color=RUST), showlegend=False, hovertemplate="Último dato · %{y:.3f}<extra></extra>"))
    fig.update_layout(**plot_layout("Fecha", metric.upper(), 320, date_axis=True))
    return fig

# -----------------------------------------------------------------------------
# Callbacks US Treasury / FRED
# -----------------------------------------------------------------------------
@app.callback(Output("graph-treasury-curve", "figure"), Input("treasury-dates", "value"))
def update_treasury_curve(selected_dates):
    if df_treasury.empty or not selected_dates:
        return empty_figure("No hay datos FRED disponibles. Configura FRED_API_KEY y reinicia la aplicación.")
    selected_set = set(pd.to_datetime(selected_dates).strftime("%Y-%m-%d"))
    sub = df_treasury[df_treasury["date"].dt.strftime("%Y-%m-%d").isin(selected_set)]
    if sub.empty:
        return empty_figure("No hay observaciones para las fechas seleccionadas")
    fig = go.Figure()
    for i, (_, row) in enumerate(sub.sort_values("date").iterrows()):
        xs, ys, labels = [], [], []
        for tenor in TREASURY_TENORS:
            value = row.get(tenor, np.nan)
            if pd.notna(value):
                xs.append(TENOR_YEARS[tenor]); ys.append(float(value)); labels.append(tenor)
        if xs:
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", name=row["date"].strftime("%d/%m/%Y"), line=dict(width=2.2, color=PALETTE[i % len(PALETTE)]), marker=dict(size=5), customdata=labels, hovertemplate="<b>%{customdata}</b><br>%{y:.3f}%<extra>%{fullData.name}</extra>"))
    fig.update_layout(**plot_layout("Plazo al vencimiento", "Rendimiento (%)", 350))
    fig.update_xaxes(tickmode="array", tickvals=list(TENOR_YEARS.values()), ticktext=["1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"])
    return fig


@app.callback(Output("graph-treasury-history", "figure"), [Input("treasury-tenor", "value"), Input("treasury-dates", "value")])
def update_treasury_history(tenor, selected_dates):
    if df_treasury.empty or tenor not in df_treasury.columns:
        return empty_figure("No hay datos históricos de FRED para mostrar")
    sub = df_treasury[["date", tenor]].dropna().sort_values("date")
    if sub.empty:
        return empty_figure("No hay observaciones para este plazo")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub["date"], y=sub[tenor], mode="lines", name=tenor, line=dict(width=1.8, color=NAVY), hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:.3f}%</b><extra></extra>"))
    if selected_dates:
        date_set = set(pd.to_datetime(selected_dates).strftime("%Y-%m-%d"))
        marks = sub[sub["date"].dt.strftime("%Y-%m-%d").isin(date_set)]
        if not marks.empty:
            fig.add_trace(go.Scatter(x=marks["date"], y=marks[tenor], mode="markers", name="Fechas seleccionadas", marker=dict(size=8, color=RUST, line=dict(width=1, color=WHITE)), hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:.3f}%</b><extra></extra>"))
    fig.update_layout(**plot_layout("Fecha", f"{tenor} · rendimiento (%)", 320, date_axis=True))
    return fig


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(debug=False, host="0.0.0.0", port=port)
