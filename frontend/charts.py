"""Gráficos de histórico do dashboard."""

from __future__ import annotations

from typing import cast

import altair as alt
import pandas as pd
import streamlit as st

from frontend.history import History

_CHART_HEIGHT = 220
# d3-time-format: minuto e segundo da amostra.
_TOOLTIP_TIME_FORMAT = "%H:%M:%S"

_SERIES: tuple[tuple[str, str, str, str], ...] = (
    ("CPU (%)", "CPU (%)", "Uso de CPU nos últimos 2 minutos", ".1f"),
    ("RAM (%)", "RAM (%)", "Uso de RAM nos últimos 2 minutos", ".1f"),
    (
        "Leitura (MB/s)",
        "Disco · leitura (MB/s)",
        "Taxa de leitura de disco nos últimos 2 minutos",
        ".3~f",
    ),
    (
        "Escrita (MB/s)",
        "Disco · escrita (MB/s)",
        "Taxa de escrita de disco nos últimos 2 minutos",
        ".3~f",
    ),
)


def render_history_charts(history: History) -> None:
    frame = history.to_frame()

    if frame.empty:
        st.info("Aguardando as primeiras amostras.", icon=":material/hourglass:")
        return

    left, right = st.columns(2)
    with left:
        _chart_card(frame, _SERIES[0])
        _chart_card(frame, _SERIES[2])
    with right:
        _chart_card(frame, _SERIES[1])
        _chart_card(frame, _SERIES[3])


def _chart_card(frame: pd.DataFrame, series: tuple[str, str, str, str]) -> None:
    column, title, alt_text, value_format = series
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.altair_chart(
            _line_chart(frame, column, title, value_format),
            width="stretch",
            alt=alt_text,
        )


def _line_chart(
    frame: pd.DataFrame, column: str, title: str, value_format: str
) -> alt.LayerChart:
    x = alt.X(field="Horário", type="temporal", title="Horário")
    y = alt.Y(field=column, type="quantitative", title=title)
    tooltip = [
        alt.Tooltip(
            field="Horário",
            type="temporal",
            title="Horário",
            format=_TOOLTIP_TIME_FORMAT,
        ),
        alt.Tooltip(
            field=column,
            type="quantitative",
            title=title,
            format=value_format,
        ),
    ]

    base = alt.Chart(frame)
    # ty não resolve os overloads de mark_* do Altair 6; o cast é só para o checker.
    line = cast(alt.Chart, base.mark_line()).encode(x=x, y=y)
    # Pontos invisíveis servem de alvo para o tooltip, como no st.line_chart.
    points = cast(alt.Chart, base.mark_point(size=60, opacity=0)).encode(
        x=x, y=y, tooltip=tooltip
    )
    chart = alt.layer(line, points).properties(height=_CHART_HEIGHT)
    return cast(alt.LayerChart, chart)
