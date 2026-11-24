"""Histórico completo das medições e download em CSV."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.history import History

_HISTORY_HEIGHT = 260


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    export = frame.copy()
    export["Horário"] = export["Horário"].dt.strftime("%Y-%m-%d %H:%M:%S")
    export["CPU (%)"] = export["CPU (%)"].round(1)
    export["RAM (%)"] = export["RAM (%)"].round(1)
    export["RAM usada (GB)"] = export["RAM usada (GB)"].round(2)
    export["Leitura (MB/s)"] = export["Leitura (MB/s)"].round(3)
    export["Escrita (MB/s)"] = export["Escrita (MB/s)"].round(3)
    return export.to_csv(index=False).encode("utf-8")


def render_measurements(history: History) -> None:
    with st.container(border=True):
        st.subheader("Histórico de medições")

        frame = history.full_frame()
        if frame.empty:
            st.info(
                "Nenhuma amostra coletada ainda.",
                icon=":material/hourglass:",
            )
            return

        st.caption(
            f"{len(frame)} amostras · "
            f"CPU média {frame['CPU (%)'].mean():.1f}% e pico "
            f"{frame['CPU (%)'].max():.1f}% · "
            f"RAM média {frame['RAM (%)'].mean():.1f}% e pico "
            f"{frame['RAM (%)'].max():.1f}%"
        )

        display = frame.iloc[::-1].copy()
        display["Horário"] = display["Horário"].dt.strftime("%H:%M:%S")
        st.dataframe(
            display,
            hide_index=True,
            height=_HISTORY_HEIGHT,
            alt="Todas as medições coletadas, da mais recente para a mais antiga",
            column_config={
                "Horário": st.column_config.TextColumn(width="small"),
                "CPU (%)": st.column_config.NumberColumn(
                    format="%.1f", width="small"
                ),
                "RAM (%)": st.column_config.NumberColumn(
                    format="%.1f", width="small"
                ),
                "RAM usada (GB)": st.column_config.NumberColumn(
                    "RAM usada", format="%.2f GB", width="small"
                ),
                "Leitura (MB/s)": st.column_config.NumberColumn(
                    format="%.3f", width="small"
                ),
                "Escrita (MB/s)": st.column_config.NumberColumn(
                    format="%.3f", width="small"
                ),
                "Processos": st.column_config.NumberColumn(
                    format="%d", width="small"
                ),
            },
        )

        st.download_button(
            "Baixar medições (CSV)",
            data=_csv_bytes(frame),
            file_name="medicoes_sistema.csv",
            mime="text/csv",
            icon=":material/download:",
            width="stretch",
        )
