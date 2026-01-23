import sqlite3
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import os


# --- Cargar data ---
df = pd.read_pickle("vector_precios_2015_mas.pkl")

DB_PATH = "curvas.db"


def query(sql, params=None):
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql(sql, con, params=params)
    con.close()
    return df

# ----------------------------------
# DATA INICIAL (LIGERA)
# ----------------------------------
df_base = query("""
    SELECT DISTINCT fecha
    FROM curvas
    WHERE emisor = 'GOB.CENTRAL'
      AND moneda = 'PEN'
    ORDER BY fecha
""")

df_base["fecha"] = pd.to_datetime(df_base["fecha"])
fechas_unicas = df_base["fecha"].dt.date.tolist()

# ----------------------------------
# APP
# ----------------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Bondora"

app.layout = html.Div(className="container", children=[
    html.H1("Bondora"),

    dcc.Dropdown(
        id="dropdown-fechas",
        options=[{"label": f.strftime("%d/%m/%Y"), "value": str(f)} for f in fechas_unicas],
        value=[str(fechas_unicas[-1])],
        multi=True
    ),

    dcc.Graph(id="graph-curve"),
    dcc.Graph(id="graph-variation"),

    dcc.Dropdown(
        id="dropdown-isin",
        options=[{"label": r[0], "value": r[0]} for r in
                 query("SELECT DISTINCT isin FROM curvas ORDER BY isin").values],
        value=query("SELECT isin FROM curvas LIMIT 1").iloc[0, 0]
    ),

    dcc.Graph(id="graph-historical")
])

# ----------------------------------
# CALLBACK CURVAS
# ----------------------------------
@app.callback(
    Output("graph-curve", "figure"),
    Output("graph-variation", "figure"),
    Input("dropdown-fechas", "value")
)
def update_curve(fechas):
    fechas = tuple(fechas)

    df = query(f"""
        SELECT *
        FROM curvas
        WHERE fecha IN ({','.join(['?']*len(fechas))})
          AND emisor = 'GOB.CENTRAL'
          AND moneda = 'PEN'
          AND isin != 'PEP01000C4R4'
    """, fechas)

    df["fecha"] = pd.to_datetime(df["fecha"])

    # --- Curva ---
    fig_curve = go.Figure()
    for f in sorted(df["fecha"].unique()):
        d = df[df["fecha"] == f].sort_values("duración")
        fig_curve.add_trace(go.Scatter(
            x=d["duración"], y=d["tir %"],
            mode="lines",
            name=f.strftime("%d/%m/%Y")
        ))

    # --- Variación ---
    df = df.sort_values(["isin", "fecha"])
    df["var_pb"] = df.groupby("isin")["tir %"].diff() * 100

    fig_var = go.Figure()
    for f in sorted(df["fecha"].unique()):
        d = df[df["fecha"] == f]
        fig_var.add_trace(go.Scatter(
            x=d["duración"], y=d["var_pb"],
            mode="lines",
            fill="tozeroy",
            name=f.strftime("%d/%m/%Y"),
            opacity=0.6
        ))

    return fig_curve, fig_var

# ----------------------------------
# CALLBACK HISTÓRICO
# ----------------------------------
@app.callback(
    Output("graph-historical", "figure"),
    Input("dropdown-isin", "value")
)
def update_hist(isin):
    df = query("""
        SELECT fecha, `tir %`, spreads
        FROM curvas
        WHERE isin = ?
        ORDER BY fecha
    """, (isin,))

    df["fecha"] = pd.to_datetime(df["fecha"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["tir %"],
        mode="lines", name="TIR (%)"
    ))
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["spreads"]*100,
        mode="lines", name="Spread (pb)", yaxis="y2"
    ))

    fig.update_layout(
        yaxis2=dict(overlaying="y", side="right"),
        template="plotly_white"
    )

    return fig

# ----------------------------------
# RUN
# ----------------------------------
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)
