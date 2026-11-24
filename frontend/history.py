"""Janela deslizante com o histórico das amostras."""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any

import pandas as pd

from backend.collector import SystemMetrics


class History:
    """Amostras em memória, sem persistência em disco.

    ``to_frame`` devolve apenas a janela curta usada pelos gráficos; ``full_frame``
    devolve tudo o que foi coletado desde o início (ou desde o último ``clear``).
    """

    def __init__(self, max_samples: int = 10) -> None:
        self._rows: deque[dict[str, Any]] = deque(maxlen=max_samples)
        self._all_rows: list[dict[str, Any]] = []
        self._last_timestamp: float | None = None
        self._last_metrics: SystemMetrics | None = None

    @property
    def max_samples(self) -> int:
        return self._rows.maxlen or 0

    @property
    def last_metrics(self) -> SystemMetrics | None:
        """Última amostra coletada, usada enquanto o monitoramento está pausado."""
        return self._last_metrics

    def __len__(self) -> int:
        return len(self._all_rows)

    def append(self, metrics: SystemMetrics) -> None:
        if metrics.timestamp == self._last_timestamp:
            return
        self._last_timestamp = metrics.timestamp
        self._last_metrics = metrics
        row = {
            "Horário": datetime.fromtimestamp(metrics.timestamp),
            "CPU (%)": metrics.cpu_percent,
            "RAM (%)": metrics.ram_percent,
            "RAM usada (GB)": metrics.ram_used_gb,
            "Leitura (MB/s)": metrics.disk_read_mb_s,
            "Escrita (MB/s)": metrics.disk_write_mb_s,
            "Processos": metrics.process_count,
        }
        self._rows.append(row)
        self._all_rows.append(row)

    def clear(self) -> None:
        """Descarta as amostras, mantendo o timestamp para ignorar o cache do coletor."""
        self._rows.clear()
        self._all_rows.clear()
        self._last_metrics = None

    def to_frame(self) -> pd.DataFrame:
        return self._frame(list(self._rows))

    def full_frame(self) -> pd.DataFrame:
        return self._frame(self._all_rows)

    @staticmethod
    def _frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame["Horário"] = pd.to_datetime(frame["Horário"])
        return frame
