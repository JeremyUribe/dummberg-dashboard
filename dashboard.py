
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import os
# --- Cargar data ---
try:
    df = pd.read_pickle("vector_precios_unido_pen.pkl")
except:
    df = pd.DataFrame()

if not df.empty:
    df = df[df['isin'] != 'PEP01000C4R4']
    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
    df['f. vencimiento'] = pd.to_datetime(df['f. vencimiento'], dayfirst=True)
    df['maturity'] = (df['f. vencimiento'] - df['fecha']).dt.days / 365
    df_curve = df[(df['emisor'] == 'GOB.CENTRAL') & (df['moneda'] == 'PEN')]
    fechas_unicas = sorted(df_curve['fecha'].dt.date.unique())
    df['busqueda'] = df['isin'] + " | " + df['nemónico']
else:
    fechas_unicas = []

# --- App ---
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500;600;700&display=swap"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Bondora"

# --- CSS claro con footer ---
app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%css%}
    <style>
        body { margin:0; font-family:'Inter',sans-serif; background:#f8fafc; color:#0f172a; }
        .container { max-width:1400px; margin:0 auto; padding:24px; }
        .header { display:flex; flex-direction:column; align-items:flex-start; border-bottom:2px solid #3b82f6; margin-bottom:24px; padding-bottom:12px; }
        .title-main { font-family:'JetBrains Mono'; font-size:28px; font-weight:700; color:#1e293b; }
        .subtitle { font-family:'JetBrains Mono'; font-size:14px; color:#475569; margin-top:2px; }
        .card { background:#ffffff; border:1px solid #e2e8f0; padding:20px; margin-bottom:20px; border-radius:6px; }
        .controls-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px,1fr)); gap:16px; margin-bottom:20px; }
        .label { font-family:'JetBrains Mono'; font-size:11px; color:#475569; margin-bottom:8px; display:block; }
        .section-title { font-family:'JetBrains Mono'; font-size:14px; color:#3b82f6; margin-bottom:16px; border-left:3px solid #3b82f6; padding-left:10px; }
        /* Footer fijo abajo izquierda */
        .footer-fixed {
            position: fixed;
            bottom: 10px;
            left: 10px;
            font-family:'JetBrains Mono';
            font-size:12px;
            color:#475569;
            display:flex;
            align-items:center;
            gap:6px;
        }
    </style>
</head>
<body>
    {%app_entry%}
    <div class="footer-fixed">
        <span>Created by: Jeremy</span>
        <span>🏎️</span>
    </div>
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
'''

# --- Paleta de colores ---
PALETTE = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']

# --- Layout ---
app.layout = html.Div(className="container", children=[

    # Cabecera con Bondora + descripción
    html.Div(className="header", children=[
        html.Div("Bondora", className="title-main"),
        html.Div("SBS SOVEREIGN", className="subtitle")
    ]),

    html.Div(className="controls-grid", children=[
        html.Div(className="card", children=[
            html.Label("SELECT DATES", className="label"),
            dcc.Dropdown(
                id='dropdown-fechas',
                options=[{'label': f.strftime('%d/%m/%Y'), 'value': str(f)} for f in fechas_unicas],
                value=[str(fechas_unicas[-1])] if fechas_unicas else [],
                multi=True,
                placeholder="Select dates..."
            )
        ]),
        html.Div(className="card", children=[
            html.Label("X-AXIS METRIC", className="label"),
            dcc.RadioItems(
                id='radio-xaxis',
                options=[
                    {'label': ' DURATION', 'value': 'duración'},
                    {'label': ' MATURITY', 'value': 'maturity'}
                ],
                value='duración',
                labelStyle={'display': 'inline-block', 'margin-right': '20px', 'font-size': '12px', 'font-family': 'JetBrains Mono'}
            ),
        ]),
    ]),

    html.Div(className="card", children=[
        html.Div("CURVE ANALYSIS", className="section-title"),
        dcc.Graph(id="graph-curve", config={'displayModeBar': False}),
    ]),

    html.Div(className="card", children=[
        html.Div("INTERPOLATED SPREAD (bps)", className="section-title"),
        dcc.Graph(id="graph-spread", config={'displayModeBar': False}),
    ]),

    html.Div(className="card", children=[
        html.Div("HISTORICAL TIME SERIES", className="section-title"),
        html.Div([
            html.Label("SEARCH INSTRUMENT (ISIN/SYMBOL)", className="label"),
            dcc.Dropdown(
                id="dropdown-busqueda",
                options=[{'label': b, 'value': b} for b in (sorted(df['busqueda'].unique()) if not df.empty else [])],
                value=df['busqueda'].iloc[0] if not df.empty else None,
            ),
        ], style={'margin-bottom': '10px'}),
        html.Div([
            html.Label("METRIC TO DISPLAY", className="label"),
            dcc.RadioItems(
                id='radio-metric',
                options=[
                    {'label': 'YIELD (%)', 'value': 'tir %'},
                    {'label': 'PRICE (%)', 'value': 'p. limpio (%)'}
                ],
                value='tir %',
                labelStyle={'display': 'inline-block', 'margin-right': '15px', 'font-size': '12px', 'font-family': 'JetBrains Mono'}
            )
        ]),
        dcc.Graph(id="graph-historical", config={'displayModeBar': False})
    ])
])

# --- Layout gráfico claro ---
def get_light_layout(title, xtitle, ytitle):
    return go.Layout(
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="JetBrains Mono, monospace", size=11, color='#0f172a'),
        title=dict(text=title, font=dict(size=14, color='#3b82f6')),
        xaxis=dict(gridcolor='#e2e8f0', zeroline=False, title=xtitle, showline=True, linecolor='#cbd5e1'),
        yaxis=dict(gridcolor='#e2e8f0', zeroline=False, title=ytitle, showline=True, linecolor='#cbd5e1'),
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode="x unified",
        legend=dict(bgcolor='rgba(255,255,255,0)', font=dict(size=10))
    )

# --- Callbacks ---
@app.callback(
    [Output("graph-curve", "figure"), Output("graph-spread", "figure")],
    [Input("dropdown-fechas", "value"), Input("radio-xaxis", "value")]
)
def update_curves(selected_dates, xaxis):
    if df.empty or not selected_dates:
        return go.Figure(), go.Figure()

    fechas_dt = pd.to_datetime(selected_dates)
    df_sel = df_curve[df_curve['fecha'].isin(fechas_dt)]
    if df_sel.empty: return go.Figure(), go.Figure()

    fig_curve = go.Figure()
    curvas_interp = {}
    for i, fecha in enumerate(sorted(df_sel['fecha'].unique())):
        df_f = df_sel[df_sel['fecha'] == fecha].sort_values(xaxis)
        x, y, nem = df_f[xaxis].values, df_f['tir %'].values, df_f['nemónico'].values
        if len(x) < 2: continue

        x_i = np.linspace(x.min(), x.max(), 300)
        y_i = np.interp(x_i, x, y)
        curvas_interp[fecha] = (x_i, y_i)

        color = PALETTE[i % len(PALETTE)]
        fig_curve.add_trace(go.Scatter(x=x_i, y=y_i, mode='lines', name=fecha.strftime('%d/%m/%Y'), line=dict(width=2, color=color)))
        fig_curve.add_trace(go.Scatter(x=x, y=y, mode='markers', marker=dict(size=7, color=color), text=nem,
                                       hovertemplate="Instrument: %{text}<br>X: %{x}<br>TIR: %{y:.2f}%<extra></extra>",
                                       showlegend=False))

    fig_curve.update_layout(get_light_layout("YIELD CURVE", xaxis.upper(), "YIELD (%)"))

    # --- Spread ---
    fig_spread = go.Figure()
    if len(curvas_interp) >= 2:
        fechas_ord = sorted(curvas_interp.keys())
        f1, f2 = fechas_ord[0], fechas_ord[-1]
        x1, y1 = curvas_interp[f1]
        x2, y2 = curvas_interp[f2]
        x_common = np.linspace(max(x1.min(), x2.min()), min(x1.max(), x2.max()), 300)
        y1_c, y2_c = np.interp(x_common, x1, y1), np.interp(x_common, x2, y2)
        spread_pb = (y2_c - y1_c) * 100

        fig_spread.add_trace(go.Scatter(x=x_common, y=spread_pb, mode='lines', fill='tozeroy', line=dict(width=2, color='#10b981'),
                                        name=f"Spread {f2:%d/%m/%Y}"))

    fig_spread.update_layout(get_light_layout("INTERPOLATED SPREAD", xaxis.upper(), "bps"))
    return fig_curve, fig_spread

@app.callback(
    Output("graph-historical", "figure"),
    [Input("dropdown-busqueda", "value"), Input("radio-metric", "value")]
)
def update_hist(busqueda, metric):
    if df.empty or not busqueda: return go.Figure()
    isin = busqueda.split(" | ")[0]
    df_i = df[df['isin'] == isin].sort_values('fecha')
    if df_i.empty: return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_i['fecha'], y=df_i[metric], mode='lines+markers', line=dict(width=2, color='#3b82f6'),
                             marker=dict(size=6), name=metric))
    fig.update_layout(get_light_layout(f"HISTORICAL: {busqueda}", "DATE", metric))
    return fig
# --- Run server ---

port = int(os.environ.get("PORT", 10000))  # Render asigna el puerto
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)


