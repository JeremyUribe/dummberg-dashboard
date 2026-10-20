from __future__ import annotations

import plotly.graph_objects as go
from dash import html

# -----------------------------------------------------------------------------
# Identidad visual de Bondora
# -----------------------------------------------------------------------------

INK = "#202923"
MUTED = "#777B73"
GRID = "#E8E7E0"
PAPER = "#F5F4EF"
WHITE = "#FFFFFF"
NAVY = "#243B53"
RUST = "#B65F43"
TEAL = "#487A72"
GOLD = "#A88645"

PALETTE = [
    NAVY,
    RUST,
    TEAL,
    GOLD,
    "#71658A",
    "#6E7D87",
]


# -----------------------------------------------------------------------------
# Componentes de diseño
# -----------------------------------------------------------------------------

def section_label(
    number: str,
    label: str,
    right: str = None,
):
    children = [
        html.Span(number, className="section-number"),
        html.Span(label, className="section-title"),
    ]

    if right:
        children.append(
            html.Span(right, className="section-meta")
        )

    return html.Div(
        children,
        className="section-head",
    )


# -----------------------------------------------------------------------------
# Configuración de gráficos
# -----------------------------------------------------------------------------

def plot_layout(
    x_title: str = "",
    y_title: str = "",
    height: int = 365,
    date_axis: bool = False,
):
    xaxis = dict(
        title=dict(
            text=x_title,
            font=dict(size=11, color=MUTED),
        ),
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=GRID,
        linewidth=1,
        tickfont=dict(size=10, color=MUTED),
        ticks="outside",
        ticklen=4,
        tickcolor=GRID,
        automargin=True,
    )

    if date_axis:
        xaxis["showgrid"] = False

    return dict(
        template="plotly_white",
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(
            family="IBM Plex Sans, sans-serif",
            size=12,
            color=INK,
        ),
        xaxis=xaxis,
        yaxis=dict(
            title=dict(
                text=y_title,
                font=dict(size=11, color=MUTED),
            ),
            showgrid=True,
            gridcolor=GRID,
            griddash="dot",
            zeroline=False,
            showline=False,
            tickfont=dict(size=10, color=MUTED),
            automargin=True,
        ),
        margin=dict(l=54, r=24, t=28, b=48),
        height=height,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=INK,
            bordercolor=INK,
            font=dict(
                color=WHITE,
                family="IBM Plex Sans, sans-serif",
                size=12,
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0)",
            font=dict(size=11, color=MUTED),
        ),
    )


def empty_figure(
    message: str = "Selecciona datos para visualizar",
):
    fig = go.Figure()

    fig.update_layout(
        **plot_layout(height=300),
        annotations=[
            dict(
                text=message,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=13, color=MUTED),
            )
        ],
    )

    return fig
