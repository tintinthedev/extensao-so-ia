"""Orquestra uma renderização completa do dashboard."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from backend.collector import SystemMetrics, get_collector
from frontend.charts import render_history_charts
from frontend.history import History
from frontend.processes import render_processes

REFRESH_SECONDS = 2.0
HISTORY_SIZE = 60
_HISTORY_KEY = "system_metrics_history"


def _history() -> History:
    history = st.session_state.get(_HISTORY_KEY)
    if history is None:
        history = History(max_samples=HISTORY_SIZE)
        st.session_state[_HISTORY_KEY] = history
    return history


def render_dashboard() -> None:
    metrics = get_collector().sample()
    history = _history()
    history.append(metrics)

    _render_summary(metrics)
    render_history_charts(history)
    render_processes(metrics)


def _render_summary(metrics: SystemMetrics) -> None:
    cpu, ram, read, write = st.columns(4)
    cpu.metric("CPU", f"{metrics.cpu_percent:.1f}%", border=True)
    ram.metric(
        "RAM",
        f"{metrics.ram_percent:.1f}%",
        help=f"{metrics.ram_used_gb:.1f} GB em uso de {metrics.ram_total_gb:.1f} GB",
        border=True,
    )
    read.metric("Leitura de disco", f"{metrics.disk_read_mb_s:.2f} MB/s", border=True)
    write.metric("Escrita de disco", f"{metrics.disk_write_mb_s:.2f} MB/s", border=True)
