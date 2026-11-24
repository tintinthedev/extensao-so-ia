"""Tabela de processos e dialog com a lista completa."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from backend.collector import ProcessInfo, SystemMetrics

_TOP_N = 5
_DIALOG_FLAG = "processes_dialog_open"
_SNAPSHOT_KEY = "processes_dialog_snapshot"


def _processes_frame(processes: tuple[ProcessInfo, ...]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "#": rank,
                "PID": proc.pid,
                "Processo": proc.name,
                "CPU (%)": round(proc.cpu_percent, 2),
                "RAM (%)": round(proc.memory_percent, 2),
            }
            for rank, proc in enumerate(processes, start=1)
        ]
    )


def render_processes(metrics: SystemMetrics) -> None:
    # Snapshot usado pelo dialog aberto a partir do script principal.
    st.session_state[_SNAPSHOT_KEY] = metrics

    with st.container(border=True):
        st.subheader("Processos")
        st.caption("Top 5 por uso de CPU, já normalizado pela capacidade total.")

        if not metrics.processes:
            st.info("Nenhum processo visível.", icon=":material/visibility_off:")
            return

        st.dataframe(
            _processes_frame(metrics.processes[:_TOP_N]),
            hide_index=True,
            alt="Cinco processos com maior uso de CPU",
        )

        if st.button(
            f"Ver todos os {metrics.process_count} processos",
            icon=":material/list:",
        ):
            st.session_state[_DIALOG_FLAG] = True
            # O dialog é renderizado fora do fragment para não perder o scroll
            # a cada atualização de 2 s.
            st.rerun(scope="app")


def open_processes_dialog() -> None:
    """Abre o dialog da lista completa, se solicitado pelo botão."""
    if not st.session_state.get(_DIALOG_FLAG):
        return
    metrics = st.session_state.get(_SNAPSHOT_KEY)
    if metrics is None:
        return
    _processes_dialog(metrics)


def _dismiss_dialog() -> None:
    st.session_state[_DIALOG_FLAG] = False


@st.dialog(
    "Todos os processos",
    width="large",
    icon=":material/list:",
    on_dismiss=_dismiss_dialog,
)
def _processes_dialog(metrics: SystemMetrics) -> None:
    updated = datetime.fromtimestamp(metrics.timestamp)
    st.caption(
        f"{metrics.process_count} processos · ordenados por uso de CPU · "
        f"amostra de {updated:%H:%M:%S}"
    )
    st.dataframe(
        _processes_frame(metrics.processes),
        hide_index=True,
        height=520,
        alt="Lista completa de processos ordenada por uso de CPU",
    )
