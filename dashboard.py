
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

# --- Cargar data ---
df = pd.read_pickle("gitvector_precios_historico.pkl")

df = df[df['isin'] != 'PEP01000C4R4']
df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)

# Primer gráfico: solo GOB.CENTRAL y PEN
df_curve = df[(df['emisor'] == 'GOB.CENTRAL') & (df['moneda'] == 'PEN')]
df_curve = df_curve.sort_values('duración')

# --- App Dash ---
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Curvas Soberanas SBS"

# Crear lista de fechas únicas para selección
fechas_unicas = sorted(df_curve['fecha'].dt.date.unique())

app.layout = html.Div(
    className="container",
    children=[
        html.H1("Curvas Soberanas SBS", className="title"),
        html.P("Visualización de curvas de tasas, variación diaria y evolución histórica de TIR y Spread.", className="subtitle"),

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
        ])
    ]
)

# --- Callbacks ---
@app.callback(
    Output("graph-curve", "figure"),
    Output("graph-variation", "figure"),
    Input("dropdown-fechas", "value")
)
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
        ))
    fig_curve.update_layout(
        title=f"Curva TIR vs Duración",
        template="plotly_white",
        xaxis_title="Duración (años)",
        yaxis_title="TIR (%)",
        font=dict(family="Inter, Helvetica, sans-serif", size=12)
    )

    # --- Variación diaria en puntos básicos ---
    df_var = df_sel.copy()
    df_var = df_var.sort_values(['isin', 'fecha'])
    df_var['var_pb'] = df_var.groupby('isin')['tir %'].diff() * 100

    fig_var = go.Figure()
    for fecha in sorted(df_var['fecha'].unique()):
        df_f = df_var[df_var['fecha'] == fecha]
        fig_var.add_trace(go.Bar(
            x=df_f['duración'],
            y=df_f['var_pb'],
            name=fecha.strftime('%d/%m/%Y')
        ))
    fig_var.update_layout(
        title=f"Variación diaria de TIR (pb)",
        template="plotly_white",
        xaxis_title="Duración (años)",
        yaxis_title="Variación (pb)",
        barmode='group',
        font=dict(family="Inter, Helvetica, sans-serif", size=12)
    )

    return fig_curve, fig_var


@app.callback(
    Output("graph-historical", "figure"),
    Input("dropdown-isin", "value")
)
def update_historical(isin):
    df_isin = df[df['isin'] == isin].sort_values('fecha')
    fig = go.Figure()
    # TIR
    fig.add_trace(go.Scatter(
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
    return fig



if __name__ == "__main__":
    app.run(debug=True)
