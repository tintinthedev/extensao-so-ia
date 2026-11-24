"""Monitor de métricas do sistema em tempo real."""

import streamlit as st

from frontend.controls import render_controls
from frontend.dashboard import MONITORING_KEY, REFRESH_SECONDS, render_dashboard
from frontend.processes import open_processes_dialog

st.set_page_config(
    page_title="Monitor do sistema",
    page_icon=":material/monitoring:",
    layout="wide",
)

if MONITORING_KEY not in st.session_state:
    st.session_state[MONITORING_KEY] = True


@st.fragment(run_every=REFRESH_SECONDS if st.session_state[MONITORING_KEY] else None)
def live_dashboard() -> None:
    render_dashboard()


render_controls()

st.title("Monitor do sistema")

live_dashboard()
open_processes_dialog()
