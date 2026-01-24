import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import os
<<<<<<< HEAD

# --- Cargar data ---
df = pd.read_pickle("vector_precios_unido_pen.pkl")

df = df[df['isin'] != 'PEP01000C4R4']
df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)

# Primer gráfico: solo GOB.CENTRAL y PEN
df_curve = df[(df['emisor'] == 'GOB.CENTRAL') & (df['moneda'] == 'PEN')]
df_curve = df_curve.sort_values('duración')

# --- App Dash ---
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Bondora"

# Crear lista de fechas únicas para selección
fechas_unicas = sorted(df_curve['fecha'].dt.date.unique())

app.layout = html.Div(
    className="container",
    children=[
        html.H1("Bondora", className="title"),
        html.P(
            "Visualización de curvas de tasas, variación diaria y evolución histórica de TIR y Spread.",
            className="subtitle"
        ),

        # Selector de fechas exactas (multi)
        html.Div([
            html.Label("Seleccionar Fechas:", className="label"),
            dcc.Dropdown(
                id='dropdown-fechas',
                options=[{'label': f.strftime('%d/%m/%Y'), 'value': str(f)} for f in fechas_unicas],
                value=[str(fechas_unicas[-1])],  # fecha por defecto
                multi=True,
                placeholder="Selecciona una o más fechas",
                style={'font-size': '14px'}
            )
        ], className="picker"),

        # Gráficos
        html.Div([
            dcc.Graph(id="graph-curve", className="graph"),
            dcc.Graph(id="graph-variation", className="graph"),
            html.Div([
                html.Label("Seleccionar ISIN:", className="label"),
                dcc.Dropdown(
                    id="dropdown-isin",
                    options=[{"label": i, "value": i} for i in sorted(df['isin'].unique())],
                    value=df['isin'].iloc[0],
                    style={'font-size': '14px'}
                )
            ], className="picker"),
            dcc.Graph(id="graph-historical", className="graph")
        ]),

        # Footer con creador e icono de fórmula 1
        html.Div(
            "Created By: Sergio 🚗💨",
            style={
                'position': 'fixed',
                'bottom': '5px',
                'left': '10px',
                'font-size': '12px',
                'color': '#888888'
            }
        )
        
    ]
)

=======
# --- Cargar data ---
try:
    df = pd.read_pickle(r"C:\Ideas Tontas\Dummberg\vector_precios_unido_pen.pkl")
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
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Bondora | SBS Peru"

# --- Layout ---
app.layout = html.Div(className="container", style={'font-family': 'Inter, sans-serif', 'backgroundColor': '#f8fafc', 'color': '#0f172a', 'padding': '20px'}, children=[

    # Header
    html.Div(children=[
        html.H1("Bondora", style={'margin': 0, 'font-size': '32px', 'font-weight': '700'}),
        html.P("SBS SOVEREIGN TERMINAL", style={'margin': 0, 'color': '#64748b', 'font-size': '16px'})
    ], style={'margin-bottom': '24px'}),

    # Controles
    html.Div(style={'display': 'flex', 'gap': '20px', 'margin-bottom': '24px'}, children=[
        html.Div(style={'flex': '1'}, children=[
            html.Label("Seleccionar Fechas", style={'font-weight': '600'}),
            dcc.DatePickerSingle(
                id='datepicker-fecha1',
                min_date_allowed=min(fechas_unicas) if fechas_unicas else None,
                max_date_allowed=max(fechas_unicas) if fechas_unicas else None,
                initial_visible_month=max(fechas_unicas) if fechas_unicas else None,
                date=max(fechas_unicas) if fechas_unicas else None,
                display_format='DD/MM/YYYY'
            ),
        ]),
        html.Div(style={'flex': '1'}, children=[
            html.Label("Eje X", style={'font-weight': '600'}),
            dcc.RadioItems(
                id='radio-xaxis',
                options=[
                    {'label': 'Duración', 'value': 'duración'},
                    {'label': 'Maturity', 'value': 'maturity'}
                ],
                value='duración',
                labelStyle={'display': 'inline-block', 'margin-right': '10px'}
            )
        ])
    ]),

    # Gráfico 1: Curva TIR
    html.Div(children=[
        html.H3("Curva de TIR", style={'margin-bottom': '8px'}),
        dcc.Graph(id="graph-curve")
    ], style={'margin-bottom': '40px'}),

    # Gráfico 2: Spread
    html.Div(children=[
        html.H3("Spread Interpolado (pb)", style={'margin-bottom': '8px'}),
        dcc.Graph(id="graph-spread")
    ], style={'margin-bottom': '40px'}),

    # Controles gráfico histórico
    html.Div(style={'display': 'flex', 'gap': '20px', 'margin-bottom': '16px'}, children=[
        html.Div(style={'flex': '1'}, children=[
            html.Label("Buscar Instrumento (ISIN/Nemotécnico)", style={'font-weight': '600'}),
            dcc.Dropdown(
                id="dropdown-busqueda",
                options=[{'label': b, 'value': b} for b in (sorted(df['busqueda'].unique()) if not df.empty else [])],
                value=df['busqueda'].iloc[0] if not df.empty else None
            )
        ]),
        html.Div(style={'flex': '1'}, children=[
            html.Label("Tipo de Evolución", style={'font-weight': '600'}),
            dcc.RadioItems(
                id='radio-hist-tipo',
                options=[
                    {'label': 'Yield (%)', 'value': 'tir %'},
                    {'label': 'Precio (%)', 'value': 'p. limpio (%)'}
                ],
                value='tir %',
                labelStyle={'display': 'inline-block', 'margin-right': '10px'}
            )
        ])
    ]),

    # Gráfico 3: Histórico
    html.Div(children=[
        dcc.Graph(id="graph-historical")
    ]),

    # Footer
    html.Div(style={'position': 'fixed', 'bottom': '5px', 'left': '10px', 'font-size': '12px', 'color': '#888'}, children=[
        "Created by Jeremy 🚗🏎️"
    ])
])

# --- Funciones helper ---
PALETTE = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']

def layout_light(title, xtitle, ytitle):
    return go.Layout(
        template="plotly_white",
        title=dict(text=title, font=dict(size=14, color='#0f172a')),
        xaxis=dict(title=xtitle),
        yaxis=dict(title=ytitle),
        font=dict(family="Inter, sans-serif", size=12),
        hoverlabel=dict(bgcolor="#0f172a", font_color="white"),
        hovermode="x unified"
    )

>>>>>>> 862bad5 ("Primer commit Dummberg")
# --- Callbacks ---
@app.callback(
    [Output("graph-curve", "figure"), Output("graph-spread", "figure")],
    [Input("datepicker-fecha1", "date"), Input("radio-xaxis", "value")]
)
<<<<<<< HEAD
def update_curve(fechas_seleccionadas):
    if not fechas_seleccionadas:
        return go.Figure(), go.Figure()

    fechas_dt = pd.to_datetime(fechas_seleccionadas)

    # Filtrar solo fechas seleccionadas
    df_sel = df_curve[df_curve['fecha'].isin(fechas_dt)]

    # --- Curva TIR vs Duración ---
    fig_curve = go.Figure()
    for fecha in sorted(df_sel['fecha'].unique()):
        df_f = df_sel[df_sel['fecha'] == fecha]
        fig_curve.add_trace(go.Scatter(
            x=df_f['duración'],
            y=df_f['tir %'],
            mode='lines+markers',
            line=dict(shape='spline', width=2),
            marker=dict(size=5),
            name=fecha.strftime('%d/%m/%Y')
=======
def update_curves(fecha_sel, xaxis):
    if not fecha_sel or df.empty: return go.Figure(), go.Figure()
    fecha_dt = pd.to_datetime(fecha_sel)
    df_sel = df_curve[df_curve['fecha'] == fecha_dt]

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
        fig_curve.add_trace(go.Scatter(
            x=x_i, y=y_i, mode='lines', name=fecha.strftime('%d/%m/%Y'),
            line=dict(width=2, color=color)
        ))
        fig_curve.add_trace(go.Scatter(
            x=x, y=y, mode='markers', marker=dict(size=8, color=color),
            text=nem, hovertemplate="%{text}<br>X: %{x}<br>TIR: %{y:.2f}%<extra></extra>",
            showlegend=False
>>>>>>> 862bad5 ("Primer commit Dummberg")
        ))
    fig_curve.update_layout(
        title=f"Curva TIR vs Duración",
        template="plotly_white",
        xaxis_title="Duración (años)",
        yaxis_title="TIR (%)",
        font=dict(family="Inter, Helvetica, sans-serif", size=12)
    )

<<<<<<< HEAD
    # --- Variación diaria en puntos básicos (gráfico de área) ---
    df_var = df_sel.copy()
    df_var = df_var.sort_values(['isin', 'fecha'])
    df_var['var_pb'] = df_var.groupby('isin')['tir %'].diff() * 100

    fig_var = go.Figure()
    for fecha in sorted(df_var['fecha'].unique()):
        df_f = df_var[df_var['fecha'] == fecha]
        fig_var.add_trace(go.Scatter(
            x=df_f['duración'],
            y=df_f['var_pb'],
            mode='lines',
            fill='tozeroy',  # gráfico de área
            line=dict(shape='spline', width=2),
            name=fecha.strftime('%d/%m/%Y'),
            opacity=0.6
        ))

    fig_var.update_layout(
        title=f"Variación diaria de TIR (pb)",
        template="plotly_white",
        xaxis_title="Duración (años)",
        yaxis_title="Variación (pb)",
        font=dict(family="Inter, Helvetica, sans-serif", size=12)
    )

    return fig_curve, fig_var


=======
    fig_curve.update_layout(layout_light("Curva de TIR", xaxis.capitalize(), "TIR (%)"))

    # Spread solo si hay más de 1 fecha para interpolar
    fig_spread = go.Figure()
    if len(curvas_interp) >= 2:
        fechas_ord = sorted(curvas_interp.keys())
        f1, f2 = fechas_ord[-2], fechas_ord[-1]
        x1, y1 = curvas_interp[f1]
        x2, y2 = curvas_interp[f2]
        x_common = np.linspace(max(x1.min(), x2.min()), min(x1.max(), x2.max()), 300)
        y1_c, y2_c = np.interp(x_common, x1, y1), np.interp(x_common, x2, y2)
        spread_pb = (y2_c - y1_c) * 100

        fig_spread.add_trace(go.Scatter(
            x=x_common, y=spread_pb, mode='lines', fill='tozeroy',
            line=dict(width=2, color='#10b981')
        ))

    fig_spread.update_layout(layout_light("Spread Interpolado (pb)", xaxis.capitalize(), "bps"))

    return fig_curve, fig_spread

>>>>>>> 862bad5 ("Primer commit Dummberg")
@app.callback(
    Output("graph-historical", "figure"),
    [Input("dropdown-busqueda", "value"), Input("radio-hist-tipo", "value")]
)
<<<<<<< HEAD
def update_historical(isin):
    df_isin = df[df['isin'] == isin].sort_values('fecha')
=======
def update_hist(busqueda, tipo):
    if not busqueda or df.empty: return go.Figure()
    isin = busqueda.split(" | ")[0]
    df_i = df[df['isin'] == isin].sort_values('fecha')

>>>>>>> 862bad5 ("Primer commit Dummberg")
    fig = go.Figure()
    # TIR
    fig.add_trace(go.Scatter(
<<<<<<< HEAD
        x=df_isin['fecha'], y=df_isin['tir %'],
        mode='lines+markers',
        line=dict(shape='spline', color='#1f77b4', width=2),
        marker=dict(size=5),
        name='TIR (%)',
        yaxis='y1'
    ))
    # Spread en pb en segundo eje
    fig.add_trace(go.Scatter(
        x=df_isin['fecha'], y=df_isin['spreads']*100,
        mode='lines+markers',
        line=dict(shape='spline', color='#d62728', width=2),
        marker=dict(size=5),
        name='Spread (pb)',
        yaxis='y2'
    ))
    fig.update_layout(
        title=f"Evolución histórica TIR y Spread - {isin}",
        template="plotly_white",
        xaxis=dict(title="Fecha"),
        yaxis=dict(title="TIR (%)", side='left', showgrid=True, zeroline=False),
        yaxis2=dict(title="Spread (pb)", overlaying='y', side='right', showgrid=False, zeroline=False),
        legend=dict(x=0.01, y=0.99),
        font=dict(family="Inter, Helvetica, sans-serif", size=12)
    )
=======
        x=df_i['fecha'], y=df_i[tipo], mode='lines+markers',
        line=dict(width=2, color='#3b82f6' if tipo=='tir %' else '#ef4444'),
        marker=dict(size=6),
        name=tipo
    ))

    fig.update_layout(layout_light(f"Histórico: {busqueda}", "Fecha", tipo))
>>>>>>> 862bad5 ("Primer commit Dummberg")
    return fig

# --- Run server ---
port = int(os.environ.get("PORT", 10000))  # Render asigna el puerto
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)
<<<<<<< HEAD

=======
>>>>>>> 862bad5 ("Primer commit Dummberg")
