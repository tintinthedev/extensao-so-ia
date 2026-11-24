"""Orquestra uma renderização completa do dashboard."""

from __future__ import annotations

import streamlit as st

from backend.collector import SystemMetrics, get_collector
from frontend.charts import render_history_charts
from frontend.history import History
from frontend.measurements import render_measurements
from frontend.processes import render_processes

REFRESH_SECONDS = 2.0
HISTORY_SIZE = 10
MONITORING_KEY = "monitorando"
_HISTORY_KEY = "system_metrics_history"


def get_history() -> History:
    history = st.session_state.get(_HISTORY_KEY)
    if history is None or history.max_samples != HISTORY_SIZE:
        history = History(max_samples=HISTORY_SIZE)
        st.session_state[_HISTORY_KEY] = history
    return history


def render_dashboard() -> None:
    history = get_history()
    metrics: SystemMetrics | None

    if st.session_state.get(MONITORING_KEY, True):
        metrics = get_collector().sample()
        history.append(metrics)
    else:
        # Pausado: reaproveita a última amostra sem coletar nada novo.
        metrics = history.last_metrics

    if metrics is None:
        st.info(
            "Clique em **Iniciar monitoramento** para ver os primeiros dados.",
            icon=":material/play_arrow:",
        )
        return

    _render_summary(metrics)
    render_history_charts(history)
    render_measurements(history)
    render_processes(metrics)


def _render_summary(metrics: SystemMetrics) -> None:
    with st.container(horizontal=True):
        st.metric("CPU", f"{metrics.cpu_percent:.1f}%", border=True)
        st.metric(
            "RAM",
            f"{metrics.ram_percent:.1f}%",
            help=f"{metrics.ram_used_gb:.1f} GB em uso de {metrics.ram_total_gb:.1f} GB",
            border=True,
        )
        st.metric(
            "Leitura de disco", f"{metrics.disk_read_mb_s:.2f} MB/s", border=True
        )
        st.metric(
            "Escrita de disco", f"{metrics.disk_write_mb_s:.2f} MB/s", border=True
        )
