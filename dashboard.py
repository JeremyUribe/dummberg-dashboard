import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import numpy as np
import os

# ─── Cargar data ─────────────────────────────────────────────────────────────
try:
    df = pd.read_pickle("vector_precios_unido_pen.pkl")
except Exception:
    df = pd.DataFrame()

if not df.empty:
    df = df[df['isin'] != 'PEP01000C4R4'].copy()
    df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
    df['f. vencimiento'] = pd.to_datetime(df['f. vencimiento'], dayfirst=True)
    df['maturity'] = (df['f. vencimiento'] - df['fecha']).dt.days / 365
    df_curve = df[(df['emisor'] == 'GOB.CENTRAL') & (df['moneda'] == 'PEN')].copy()
    fechas_unicas = sorted(df_curve['fecha'].dt.date.unique())
    df['busqueda'] = df['isin'] + " | " + df['nemónico']
    busqueda_options = [{'label': b, 'value': b} for b in sorted(df['busqueda'].unique())]
    fecha_options   = [{'label': f.strftime('%d/%m/%Y'), 'value': str(f)} for f in fechas_unicas]
    default_fecha   = [str(fechas_unicas[-1])] if fechas_unicas else []
    default_busqueda = df['busqueda'].iloc[0] if not df.empty else None
else:
    df_curve = pd.DataFrame()
    fechas_unicas = []
    busqueda_options = []
    fecha_options = []
    default_fecha = []
    default_busqueda = None

PALETTE = ['#2563eb', '#e11d48', '#059669', '#d97706', '#7c3aed', '#0891b2']

# ─── App ─────────────────────────────────────────────────────────────────────
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap"
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Bondora"

app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%css%}
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
            --bg:      #f8fafc;
            --card:    #ffffff;
            --hover:   #f1f5f9;
            --bdr:     #e2e8f0;
            --bhi:     #cbd5e1;
            --tx:      #0f172a;
            --muted:   #64748b;
            --blue:    #2563eb;
            --green:   #059669;
            --red:     #e11d48;
            --amber:   #d97706;
            --violet:  #7c3aed;
            --r:       8px;
            --mono:    'IBM Plex Mono', monospace;
            --sans:    'IBM Plex Sans', sans-serif;
            --sh:      0 1px 3px rgba(15,23,42,.07), 0 1px 2px rgba(15,23,42,.04);
        }
        html,body { background:var(--bg); color:var(--tx); font-family:var(--sans); -webkit-font-smoothing:antialiased; }
        ::-webkit-scrollbar { width:5px; height:5px; }
        ::-webkit-scrollbar-track { background:var(--bg); }
        ::-webkit-scrollbar-thumb { background:var(--bhi); border-radius:3px; }

        .shell { display:flex; flex-direction:column; min-height:100vh; }

        .topbar {
            display:flex; align-items:center; justify-content:space-between;
            padding:0 32px; height:52px; background:#fff;
            border-bottom:1px solid var(--bdr); position:sticky; top:0; z-index:100;
        }
        .brand { display:flex; align-items:baseline; gap:10px; }
        .logo  { font-family:var(--mono); font-size:17px; font-weight:600; color:var(--tx); }
        .sep   { color:var(--bhi); }
        .sub   { font-family:var(--mono); font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:1.5px; }
        .badge { font-family:var(--mono); font-size:10px; padding:3px 10px; border-radius:20px; background:#eff6ff; color:var(--blue); border:1px solid #bfdbfe; text-transform:uppercase; letter-spacing:1px; }

        .main  { flex:1; padding:22px 32px; max-width:1500px; margin:0 auto; width:100%; }

        .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(145px,1fr)); gap:10px; margin-bottom:16px; }
        .sc    { background:var(--card); border:1px solid var(--bdr); border-radius:var(--r); padding:12px 15px; box-shadow:var(--sh); transition:box-shadow .15s,border-color .15s; }
        .sc:hover { box-shadow:0 4px 12px rgba(15,23,42,.1); border-color:var(--bhi); }
        .sl    { font-family:var(--mono); font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:5px; }
        .sv    { font-family:var(--mono); font-size:18px; font-weight:600; line-height:1; }
        .sv.b  { color:var(--blue); } .sv.g { color:var(--green); } .sv.a { color:var(--amber); }

        .sec   { background:var(--card); border:1px solid var(--bdr); border-radius:var(--r); margin-bottom:14px; overflow:hidden; box-shadow:var(--sh); }
        .shead { display:flex; align-items:center; gap:8px; padding:11px 18px; border-bottom:1px solid var(--bdr); background:#fafbfc; }
        .dot   { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
        .stit  { font-family:var(--mono); font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:1.5px; }
        .sbody { padding:15px 18px; }

        .clabel { font-family:var(--mono); font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; margin-bottom:5px; display:block; }

        /* Interpolation */
        .ig { display:grid; grid-template-columns:1fr 1fr 1fr auto; gap:10px; align-items:end; }
        .ii {
            font-family:var(--mono); font-size:13px; padding:7px 10px;
            border:1px solid var(--bdr); border-radius:5px; color:var(--tx); background:#fff;
            width:100%; outline:none; transition:border-color .15s, box-shadow .15s;
        }
        .ii:focus { border-color:var(--blue); box-shadow:0 0 0 3px rgba(37,99,235,.1); }
        .ib {
            font-family:var(--mono); font-size:12px; font-weight:500;
            padding:7px 18px; border-radius:5px; border:none;
            background:var(--blue); color:#fff; cursor:pointer; white-space:nowrap;
            transition:background .15s, transform .1s;
        }
        .ib:hover  { background:#1d4ed8; }
        .ib:active { transform:scale(0.97); }
        .rbox  { margin-top:14px; padding:14px 18px; border-radius:6px; display:flex; align-items:center; gap:20px; }
        .rbox.ok  { background:#eff6ff; border:1px solid #bfdbfe; }
        .rbox.err { background:#fff1f2; border:1px solid #fecdd3; }
        .rlabel { font-family:var(--mono); font-size:10px; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px; }
        .rval   { font-family:var(--mono); font-size:24px; font-weight:600; line-height:1; }
        .rbox.ok  .rlabel { color:var(--blue); }
        .rbox.ok  .rval   { color:var(--blue); }
        .rbox.err .rlabel { color:var(--red); }
        .rbox.err .rval   { color:var(--red); font-size:13px; font-weight:400; }
        .rmeta { font-family:var(--mono); font-size:11px; color:var(--muted); margin-left:auto; text-align:right; line-height:1.6; }

        .footer { padding:10px 32px; border-top:1px solid var(--bdr); background:#fff; }
        .fi  { display:flex; justify-content:space-between; align-items:center; }
        .ft  { font-family:var(--mono); font-size:11px; color:var(--muted); }
        .ftag{ font-family:var(--mono); font-size:10px; padding:2px 7px; border-radius:3px; background:var(--bdr); color:var(--muted); }

        ._dash-loading-callback { opacity:0 !important; }
        .dash-spinner { display:none !important; }
    </style>
</head>
<body>
<div class="shell">
  <nav class="topbar">
    <div class="brand">
      <span class="logo">bondora</span><span class="sep"> / </span><span class="sub">SBS Sovereign Curves</span>
    </div>
    <span class="badge">PEN · GOB. CENTRAL</span>
  </nav>
  {%app_entry%}
  <footer class="footer"><div class="fi"><span class="ft">Jeremy · Fixed Income Analytics</span><span class="ftag">v3.0</span></div></footer>
</div>
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
'''

# ─── White Plotly layout ──────────────────────────────────────────────────────
def white_layout(xtitle, ytitle, height=340, year_ticks=True):
    xax = dict(
        title=dict(text=xtitle, font=dict(size=11, color='#64748b')),
        gridcolor='#f1f5f9', zeroline=False,
        showline=True, linecolor='#e2e8f0', linewidth=1,
        tickfont=dict(size=10, color='#94a3b8'),
        title_standoff=8,
    )
    if year_ticks:
        xax.update(dtick=1, tick0=0, ticksuffix=" yr")

    return dict(
        template="plotly_white",
        plot_bgcolor='#ffffff', paper_bgcolor='#ffffff',
        font=dict(family="IBM Plex Mono, monospace", size=11, color='#475569'),
        xaxis=xax,
        yaxis=dict(
            title=dict(text=ytitle, font=dict(size=11, color='#64748b')),
            gridcolor='#f1f5f9', zeroline=False,
            showline=True, linecolor='#e2e8f0', linewidth=1,
            tickfont=dict(size=10, color='#94a3b8'),
            title_standoff=8,
        ),
        margin=dict(l=56, r=20, t=16, b=48),
        hovermode="x unified",
        hoverlabel=dict(bgcolor='#1e293b', bordercolor='#334155',
                        font=dict(family='IBM Plex Mono', size=11, color='#f8fafc')),
        legend=dict(bgcolor='rgba(255,255,255,0.92)', bordercolor='#e2e8f0', borderwidth=1,
                    font=dict(family='IBM Plex Mono', size=10, color='#64748b'), x=0.01, y=0.99),
        height=height,
    )

# ─── Stats ────────────────────────────────────────────────────────────────────
def build_stats():
    if df_curve.empty:
        return html.Div()
    last = df_curve[df_curve['fecha'] == df_curve['fecha'].max()]
    return html.Div(className="stats", children=[
        html.Div(className="sc", children=[html.Div("Última fecha",   className="sl"), html.Div(last['fecha'].iloc[0].strftime('%d/%m/%Y'), className="sv b")]),
        html.Div(className="sc", children=[html.Div("Bonos activos",  className="sl"), html.Div(str(len(last)), className="sv")]),
        html.Div(className="sc", children=[html.Div("TIR mín.",       className="sl"), html.Div(f"{last['tir %'].min():.2f}%", className="sv g")]),
        html.Div(className="sc", children=[html.Div("TIR máx.",       className="sl"), html.Div(f"{last['tir %'].max():.2f}%", className="sv a")]),
        html.Div(className="sc", children=[html.Div("Fechas disp.",   className="sl"), html.Div(str(df_curve['fecha'].nunique()), className="sv")]),
    ])

# ─── Layout ───────────────────────────────────────────────────────────────────
app.layout = html.Div(className="main", children=[

    build_stats(),

    # Controles
    html.Div(className="sec", children=[
        html.Div(className="shead", children=[html.Div(className="dot", style={'background':'#2563eb'}), html.Span("Configuración de curva", className="stit")]),
        html.Div(className="sbody", children=[
            html.Div(style={'display':'grid','gridTemplateColumns':'1fr 220px','gap':'16px','alignItems':'start'}, children=[
                html.Div([
                    html.Span("Seleccionar fechas", className="clabel"),
                    dcc.Dropdown(id='dropdown-fechas', options=fecha_options, value=default_fecha, multi=True,
                                 placeholder="Seleccionar fechas...", style={'fontFamily':'IBM Plex Mono','fontSize':'12px'})
                ]),
                html.Div([
                    html.Span("Eje X", className="clabel"),
                    dcc.RadioItems(
                        id='radio-xaxis',
                        options=[{'label':'  Duración','value':'duración'},{'label':'  Madurez','value':'maturity'}],
                        value='duración',
                        labelStyle={'display':'inline-block','marginRight':'18px','fontFamily':'IBM Plex Mono','fontSize':'12px','color':'#475569','cursor':'pointer'}
                    )
                ]),
            ])
        ])
    ]),

    # Curva + Spread
    html.Div(style={'display':'grid','gridTemplateColumns':'3fr 2fr','gap':'14px','marginBottom':'14px'}, children=[
        html.Div(className="sec", children=[
            html.Div(className="shead", children=[html.Div(className="dot", style={'background':'#2563eb'}), html.Span("Curva de rendimientos", className="stit")]),
            dcc.Graph(id="graph-curve", config={'displayModeBar':True,'modeBarButtonsToRemove':['select2d','lasso2d','autoScale2d'],'displaylogo':False}),
        ]),
        html.Div(className="sec", children=[
            html.Div(className="shead", children=[html.Div(className="dot", style={'background':'#059669'}), html.Span("Spread interpolado (bps)", className="stit")]),
            dcc.Graph(id="graph-spread", config={'displayModeBar':False}),
        ]),
    ]),

    # Panel de yield interpolada
    html.Div(className="sec", children=[
        html.Div(className="shead", children=[html.Div(className="dot", style={'background':'#7c3aed'}), html.Span("Consulta de yield interpolada", className="stit")]),
        html.Div(className="sbody", children=[
            html.Div(className="ig", children=[
                html.Div([
                    html.Span("Fecha de la curva", className="clabel"),
                    dcc.Dropdown(id='interp-fecha', options=fecha_options,
                                 value=str(fechas_unicas[-1]) if fechas_unicas else None,
                                 placeholder="Seleccionar...", clearable=False,
                                 style={'fontFamily':'IBM Plex Mono','fontSize':'12px'})
                ]),
                html.Div([
                    html.Span("Eje X", className="clabel"),
                    dcc.Dropdown(id='interp-xaxis',
                                 options=[{'label':'Duración (años)','value':'duración'},
                                          {'label':'Madurez (años)','value':'maturity'}],
                                 value='duración', clearable=False,
                                 style={'fontFamily':'IBM Plex Mono','fontSize':'12px'})
                ]),
                html.Div([
                    html.Span("Valor en años", className="clabel"),
                    dcc.Input(id='interp-valor', type='number', placeholder='Ej: 5.5',
                              min=0, step=0.01, className="ii",
                              debounce=False)
                ]),
                html.Button("Calcular →", id='interp-btn', n_clicks=0, className="ib"),
            ]),
            html.Div(id='interp-result'),
        ])
    ]),

    # Histórico
    html.Div(className="sec", children=[
        html.Div(className="shead", children=[html.Div(className="dot", style={'background':'#d97706'}), html.Span("Serie de tiempo histórica", className="stit")]),
        html.Div(className="sbody", children=[
            html.Div(style={'display':'grid','gridTemplateColumns':'1fr 200px','gap':'16px','marginBottom':'12px'}, children=[
                html.Div([
                    html.Span("Instrumento (ISIN / Nemónico)", className="clabel"),
                    dcc.Dropdown(id="dropdown-busqueda", options=busqueda_options, value=default_busqueda,
                                 style={'fontFamily':'IBM Plex Mono','fontSize':'12px'})
                ]),
                html.Div([
                    html.Span("Métrica", className="clabel"),
                    dcc.RadioItems(
                        id='radio-metric',
                        options=[{'label':'  TIR (%)','value':'tir %'},{'label':'  Precio (%)','value':'p. limpio (%)'}],
                        value='tir %',
                        labelStyle={'display':'inline-block','marginRight':'16px','fontFamily':'IBM Plex Mono','fontSize':'12px','color':'#475569','cursor':'pointer'}
                    )
                ]),
            ]),
        ]),
        dcc.Graph(id="graph-historical", config={'displayModeBar':True,'modeBarButtonsToRemove':['select2d','lasso2d'],'displaylogo':False}),
    ]),
])

# ─── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(
    [Output("graph-curve","figure"), Output("graph-spread","figure")],
    [Input("dropdown-fechas","value"), Input("radio-xaxis","value")]
)
def update_curves(selected_dates, xaxis):
    empty = go.Figure(layout=go.Layout(**white_layout("","",year_ticks=False)))
    if df_curve.empty or not selected_dates:
        return empty, empty

    fechas_dt = pd.to_datetime(selected_dates)
    df_sel = df_curve[df_curve['fecha'].isin(fechas_dt)]
    if df_sel.empty:
        return empty, empty

    xtitle = "Duración (años)" if xaxis == 'duración' else "Madurez (años)"
    fig_curve   = go.Figure()
    curvas_interp = {}

    for i, fecha in enumerate(sorted(df_sel['fecha'].unique())):
        df_f = df_sel[df_sel['fecha'] == fecha].sort_values(xaxis)
        x, y, nem = df_f[xaxis].values, df_f['tir %'].values, df_f['nemónico'].values
        if len(x) < 2:
            continue
        x_i = np.linspace(x.min(), x.max(), 200)
        y_i = np.interp(x_i, x, y)
        curvas_interp[fecha] = (x_i, y_i)
        color = PALETTE[i % len(PALETTE)]

        fig_curve.add_trace(go.Scatter(
            x=x_i, y=y_i, mode='lines', name=fecha.strftime('%d/%m/%Y'),
            line=dict(width=2.5, color=color)
        ))
        fig_curve.add_trace(go.Scatter(
            x=x, y=y, mode='markers',
            marker=dict(size=7, color=color, line=dict(width=1.5, color='#fff')),
            text=nem,
            hovertemplate="<b>%{text}</b><br>%{x:.2f} yr → <b>%{y:.3f}%</b><extra></extra>",
            showlegend=False
        ))

    fig_curve.update_layout(**white_layout(xtitle, "TIR (%)"))

    # Spread
    fig_spread = go.Figure()
    if len(curvas_interp) >= 2:
        f1, f2 = sorted(curvas_interp.keys())[0], sorted(curvas_interp.keys())[-1]
        x1,y1 = curvas_interp[f1]; x2,y2 = curvas_interp[f2]
        xc = np.linspace(max(x1.min(),x2.min()), min(x1.max(),x2.max()), 200)
        sp = (np.interp(xc,x2,y2) - np.interp(xc,x1,y1)) * 100
        pos = sp >= 0
        fig_spread.add_trace(go.Scatter(x=xc, y=np.where(pos,sp,0), mode='lines', fill='tozeroy',
            line=dict(width=2,color='#059669'), fillcolor='rgba(5,150,105,0.1)', name=f"+ {f2:%d/%m/%Y}"))
        fig_spread.add_trace(go.Scatter(x=xc, y=np.where(~pos,sp,0), mode='lines', fill='tozeroy',
            line=dict(width=2,color='#e11d48'), fillcolor='rgba(225,29,72,0.08)', name=f"− {f1:%d/%m/%Y}"))
        fig_spread.add_hline(y=0, line_color='#cbd5e1', line_width=1)

    fig_spread.update_layout(**white_layout(xtitle, "bps"))
    return fig_curve, fig_spread


@app.callback(
    Output("interp-result","children"),
    Input("interp-btn","n_clicks"),
    [State("interp-fecha","value"), State("interp-xaxis","value"), State("interp-valor","value")],
    prevent_initial_call=True
)
def calc_interpolation(n_clicks, fecha_str, xaxis, valor):
    def err(msg):
        return html.Div(className="rbox err", children=[
            html.Div([html.Div("Error", className="rlabel"), html.Div(msg, className="rval")])
        ])

    if not fecha_str or valor is None:
        return err("Completa todos los campos")

    fecha_dt = pd.to_datetime(fecha_str)
    df_f = df_curve[df_curve['fecha'] == fecha_dt].sort_values(xaxis)
    if df_f.empty:
        return err(f"Sin datos para {fecha_str}")

    x_data = df_f[xaxis].values
    y_data = df_f['tir %'].values
    if len(x_data) < 2:
        return err("Insuficientes puntos")
    if valor < x_data.min() or valor > x_data.max():
        return err(f"Fuera del rango [{x_data.min():.2f} – {x_data.max():.2f} yr]")

    yield_v  = float(np.interp(valor, x_data, y_data))
    eje_lbl  = "duración" if xaxis == "duración" else "madurez"

    return html.Div(className="rbox ok", children=[
        html.Div([
            html.Div("Yield interpolada", className="rlabel"),
            html.Div(f"{yield_v:.4f}%",   className="rval"),
        ]),
        html.Div(className="rmeta", children=[
            html.Div(f"{eje_lbl}: {valor:.2f} yr"),
            html.Div(fecha_dt.strftime('%d/%m/%Y')),
        ]),
    ])


@app.callback(
    Output("graph-historical","figure"),
    [Input("dropdown-busqueda","value"), Input("radio-metric","value")]
)
def update_hist(busqueda, metric):
    empty = go.Figure(layout=go.Layout(**white_layout("","",height=300,year_ticks=False)))
    if df.empty or not busqueda:
        return empty
    isin = busqueda.split(" | ")[0]
    df_i = df[df['isin'] == isin].sort_values('fecha')
    if df_i.empty:
        return empty

    x, y = df_i['fecha'], df_i[metric].values
    fig  = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='none', fill='tozeroy',
                             fillcolor='rgba(37,99,235,0.06)', showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(width=2,color='#2563eb'), name=metric,
                             hovertemplate="%{x|%d/%m/%Y} → <b>%{y:.3f}</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=[x.iloc[-1]], y=[y[-1]], mode='markers',
                             marker=dict(size=8,color='#2563eb',line=dict(width=2,color='#fff')),
                             showlegend=False,
                             hovertemplate=f"Último: {y[-1]:.3f}<extra></extra>"))
    layout = white_layout("Fecha", metric.upper(), height=300, year_ticks=False)
    fig.update_layout(**layout)
    return fig


# ─── Run ──────────────────────────────────────────────────────────────────────
port = int(os.environ.get("PORT", 10000))
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=port)
