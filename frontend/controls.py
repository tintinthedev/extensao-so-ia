"""Controles de monitoramento na barra lateral."""

from __future__ import annotations

import streamlit as st

from frontend.dashboard import MONITORING_KEY, REFRESH_SECONDS, get_history


def _toggle_monitoring() -> None:
    st.session_state[MONITORING_KEY] = not st.session_state[MONITORING_KEY]


def _clear_history() -> None:
    get_history().clear()


def render_controls() -> None:
    monitoring = bool(st.session_state[MONITORING_KEY])

    with st.sidebar:
        st.header("Monitoramento")
        st.caption(
            "Coleta do computador onde o app está rodando, "
            f"a cada {REFRESH_SECONDS:g} s."
        )

        st.button(
            "Pausar" if monitoring else "Iniciar monitoramento",
            icon=":material/pause:" if monitoring else ":material/play_arrow:",
            type="primary",
            width="stretch",
            on_click=_toggle_monitoring,
        )

        st.button(
            "Limpar histórico",
            icon=":material/delete:",
            width="stretch",
            on_click=_clear_history,
        )

        status = "Monitorando" if monitoring else "Pausado"
        st.caption(f"Estado: {status}")
