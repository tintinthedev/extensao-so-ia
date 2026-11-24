"""Gráficos de histórico do dashboard."""

from __future__ import annotations

import streamlit as st

from frontend.history import History

_CHART_HEIGHT = 220

_SERIES: tuple[tuple[str, str, str], ...] = (
    ("CPU (%)", "CPU (%)", "Uso de CPU nos últimos 2 minutos"),
    ("RAM (%)", "RAM (%)", "Uso de RAM nos últimos 2 minutos"),
    (
        "Leitura (MB/s)",
        "Disco · leitura (MB/s)",
        "Taxa de leitura de disco nos últimos 2 minutos",
    ),
    (
        "Escrita (MB/s)",
        "Disco · escrita (MB/s)",
        "Taxa de escrita de disco nos últimos 2 minutos",
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


def _chart_card(frame, series: tuple[str, str, str]) -> None:
    column, title, alt = series
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.line_chart(
            frame,
            x="Horário",
            y=column,
            height=_CHART_HEIGHT,
            alt=alt,
        )
