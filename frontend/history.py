"""Janela deslizante com o histórico das amostras."""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any

import pandas as pd

from backend.collector import SystemMetrics


class History:
    """Últimas amostras em memória, sem persistência em disco."""

    def __init__(self, max_samples: int = 10) -> None:
        self._rows: deque[dict[str, Any]] = deque(maxlen=max_samples)
        self._last_timestamp: float | None = None

    @property
    def max_samples(self) -> int:
        return self._rows.maxlen or 0

    def __len__(self) -> int:
        return len(self._rows)

    def append(self, metrics: SystemMetrics) -> None:
        if metrics.timestamp == self._last_timestamp:
            return
        self._last_timestamp = metrics.timestamp
        self._rows.append(
            {
                "Horário": datetime.fromtimestamp(metrics.timestamp),
                "CPU (%)": metrics.cpu_percent,
                "RAM (%)": metrics.ram_percent,
                "Leitura (MB/s)": metrics.disk_read_mb_s,
                "Escrita (MB/s)": metrics.disk_write_mb_s,
            }
        )

    def to_frame(self) -> pd.DataFrame:
        frame = pd.DataFrame(list(self._rows))
        if not frame.empty:
            frame["Horário"] = pd.to_datetime(frame["Horário"])
        return frame
