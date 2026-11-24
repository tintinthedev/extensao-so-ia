"""Monitor de métricas do sistema em tempo real."""

import streamlit as st

from frontend.dashboard import REFRESH_SECONDS, render_dashboard
from frontend.processes import open_processes_dialog

st.set_page_config(
    page_title="Monitor do sistema",
    page_icon=":material/monitoring:",
    layout="wide",
)


@st.fragment(run_every=REFRESH_SECONDS)
def live_dashboard() -> None:
    render_dashboard()


st.title("Monitor do sistema")
st.caption(
    "Métricas coletadas localmente com psutil · "
    f"atualização a cada {REFRESH_SECONDS:g} segundos"
)

live_dashboard()
open_processes_dialog()
