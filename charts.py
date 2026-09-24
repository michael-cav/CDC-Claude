"""Plotly figure builders. Each takes a chart-ready DataFrame and returns a Figure.

Conventions: bars, lines, and color scales start at zero (no truncated axes); hover text
and axes use thousands separators; palettes come from config (colorblind-safe).
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.config import (
    ABBR, BIRTHS, BOTTOM_COLOR, MONTH, MONTH_ORDER, SEQUENTIAL_SCALE, SEX, SEX_COLORS,
    SEX_OPTIONS, STATE, TOP_COLOR, TOTAL_COLOR,
)
from dashboard.metrics import RATIO

LABELS = {MONTH: "Month", BIRTHS: "Births", STATE: "State", SEX: "Infant sex"}


def _style(fig: go.Figure, title: str, height: int | None = None) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left", font=dict(size=16)),
        template="plotly_white",
        margin=dict(l=10, r=10, t=70, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right", title_text=""),
        font=dict(size=13),
    )
    if height:
        fig.update_layout(height=height)
    return fig


def _month_str(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Plain-string months plus the chronological order of months actually present."""
    out = df.assign(**{MONTH: df[MONTH].astype(str)})
    present = set(out[MONTH])
    return out, [m for m in MONTH_ORDER if m in present]


def monthly_trend(by_month: pd.DataFrame) -> go.Figure:
    data, order = _month_str(by_month)
    fig = px.line(data, x=MONTH, y=BIRTHS, markers=True, category_orders={MONTH: order},
                  labels=LABELS, color_discrete_sequence=[TOTAL_COLOR])
    fig.update_traces(hovertemplate="%{x}<br>Births: %{y:,.0f}<extra></extra>")
    fig.update_yaxes(rangemode="tozero", tickformat=",d", title="Births")
    return _style(fig, "Monthly births, current selection", 400)


def sex_comparison(by_month_sex: pd.DataFrame) -> go.Figure:
    data, order = _month_str(by_month_sex)
    fig = px.bar(data, x=MONTH, y=BIRTHS, color=SEX, barmode="group", labels=LABELS,
                 color_discrete_map=SEX_COLORS,
                 category_orders={MONTH: order, SEX: SEX_OPTIONS})
    fig.update_traces(hovertemplate="%{x}<br>Births: %{y:,.0f}<extra>%{fullData.name}</extra>")
    fig.update_yaxes(rangemode="tozero", tickformat=",d", title="Births")
    return _style(fig, "Female and male births by month", 400)


def sex_ratio(ratio_df: pd.DataFrame) -> go.Figure:
    data, order = _month_str(ratio_df)
    fig = px.bar(data, x=MONTH, y=RATIO, category_orders={MONTH: order},
                 labels={MONTH: "Month", RATIO: "Males per 100 females"},
                 color_discrete_sequence=[TOTAL_COLOR])
    fig.update_traces(hovertemplate="%{x}<br>%{y:.1f} male births per 100 female births<extra></extra>")
    fig.add_hline(y=100, line_dash="dash", line_color="#333333",
                  annotation_text="Equal counts (100)", annotation_position="bottom right")
    fig.update_yaxes(rangemode="tozero", title="Males per 100 females")
    return _style(fig, "Male births per 100 female births", 400)


def state_ranking(by_state: pd.DataFrame, title: str) -> go.Figure:
    n = len(by_state)
    fig = px.bar(by_state, x=BIRTHS, y=STATE, orientation="h", labels=LABELS,
                 color_discrete_sequence=[TOTAL_COLOR])
    fig.update_traces(hovertemplate="%{y}<br>Births: %{x:,.0f}<extra></extra>")
    if n <= 15:  # value labels only when they stay legible
        fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_yaxes(categoryorder="total ascending", dtick=1, title=None)  # largest at top
    fig.update_xaxes(rangemode="tozero", tickformat=",d", title="Births")
    return _style(fig, title, min(1400, max(300, 22 * n + 110)))


def choropleth(by_state: pd.DataFrame) -> go.Figure:
    fig = px.choropleth(
        by_state, locations=ABBR, locationmode="USA-states", scope="usa",
        color=BIRTHS, color_continuous_scale=SEQUENTIAL_SCALE,
        range_color=(0, int(by_state[BIRTHS].max())),  # scale starts at zero
        hover_name=STATE, hover_data={ABBR: False, BIRTHS: ":,.0f"}, labels=LABELS,
    )
    fig.update_traces(marker_line_color="white", marker_line_width=0.6)
    fig.update_layout(coloraxis_colorbar=dict(title="Births", tickformat=","))
    return _style(fig, "Births by state, current selection", 480)


def heatmap(matrix: pd.DataFrame, share: bool) -> go.Figure:
    label = "% of state's births" if share else "Births"
    fig = px.imshow(matrix, aspect="auto", color_continuous_scale=SEQUENTIAL_SCALE, zmin=0,
                    labels=dict(x="Month", y="State", color=label))
    value = "Share: %{z:.1f}%" if share else "Births: %{z:,.0f}"
    fig.update_traces(hovertemplate=f"%{{y}}<br>%{{x}}<br>{value}<extra></extra>")
    fig.update_layout(coloraxis_colorbar=dict(title=label, tickformat=".0f" if share else ","))
    fig.update_yaxes(dtick=1, title=None, tickfont=dict(size=11))
    fig.update_xaxes(side="top", title=None)
    title = "Share of each state's births by month" if share else "Births by state and month"
    return _style(fig, title, max(380, 20 * len(matrix) + 130))


def top_bottom(top: pd.DataFrame, bottom: pd.DataFrame) -> go.Figure:
    n = len(top)
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.2,
                        subplot_titles=(f"Top {n} geographies", f"Bottom {n} geographies"))
    for col, frame, color in ((1, top, TOP_COLOR), (2, bottom, BOTTOM_COLOR)):
        fig.add_trace(go.Bar(
            x=frame[BIRTHS], y=frame[STATE], orientation="h", marker_color=color,
            text=frame[BIRTHS], texttemplate="%{x:,.0f}", textposition="outside",
            cliponaxis=False, showlegend=False,
            hovertemplate="%{y}<br>Births: %{x:,.0f}<extra></extra>",
        ), row=1, col=col)
    fig.update_yaxes(categoryorder="total ascending")  # largest at top within each panel
    fig.update_xaxes(rangemode="tozero", tickformat=",d", title_text="Births")
    return _style(fig, "Highest and lowest birth counts in the selection", max(320, 40 * n + 150))
