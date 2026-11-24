"""Coleta de métricas do sistema com psutil."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import psutil

_BYTES_PER_MB = 1024 * 1024
_MIN_SAMPLE_INTERVAL = 1.0  # segundos


@dataclass(frozen=True)
class ProcessInfo:
    """Uma linha da lista de processos."""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


@dataclass(frozen=True)
class SystemMetrics:
    """Uma amostra completa do sistema."""

    timestamp: float
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    disk_read_mb_s: float
    disk_write_mb_s: float
    cpu_count: int
    processes: tuple[ProcessInfo, ...]

    @property
    def process_count(self) -> int:
        return len(self.processes)


class MetricsCollector:
    """Coletor com estado: taxas dependem da amostra anterior.

    A coleta é serializada por um lock porque os contadores anteriores são
    compartilhados entre as sessões do Streamlit.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cpu_count = psutil.cpu_count(logical=True) or 1
        self._prev_disk: tuple[int, int] | None = None
        self._prev_ts = time.monotonic()
        self._last: SystemMetrics | None = None
        self._prime()

    def _prime(self) -> None:
        """Inicializa as médias não bloqueantes do psutil."""
        psutil.cpu_percent(interval=None)
        for _ in psutil.process_iter(["cpu_percent"]):
            pass

    def sample(self) -> SystemMetrics:
        with self._lock:
            now = time.monotonic()
            if self._last is not None and now - self._prev_ts < _MIN_SAMPLE_INTERVAL:
                return self._last

            elapsed = max(now - self._prev_ts, 1e-9)
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()

            read_mb_s, write_mb_s = self._disk_rates(elapsed)
            processes = self._collect_processes()

            self._prev_ts = now
            self._last = SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                ram_percent=memory.percent,
                ram_used_gb=memory.used / (1024**3),
                ram_total_gb=memory.total / (1024**3),
                disk_read_mb_s=read_mb_s,
                disk_write_mb_s=write_mb_s,
                cpu_count=self._cpu_count,
                processes=processes,
            )
            return self._last

    def _disk_rates(self, elapsed: float) -> tuple[float, float]:
        counters = psutil.disk_io_counters()
        if counters is None:
            return 0.0, 0.0

        read_mb_s = write_mb_s = 0.0
        if self._prev_disk is not None:
            prev_read, prev_write = self._prev_disk
            read_mb_s = max(counters.read_bytes - prev_read, 0) / _BYTES_PER_MB / elapsed
            write_mb_s = (
                max(counters.write_bytes - prev_write, 0) / _BYTES_PER_MB / elapsed
            )
        self._prev_disk = (counters.read_bytes, counters.write_bytes)
        return read_mb_s, write_mb_s

    def _collect_processes(self) -> tuple[ProcessInfo, ...]:
        processes: list[ProcessInfo] = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent"], ad_value=None
        ):
            info = proc.info
            cpu = info.get("cpu_percent")
            mem = info.get("memory_percent")
            if cpu is None or mem is None:
                continue
            processes.append(
                ProcessInfo(
                    pid=info["pid"],
                    name=info.get("name") or f"pid {info['pid']}",
                    # psutil mede por núcleo; normaliza para a escala 0-100 do sistema.
                    cpu_percent=min(cpu / self._cpu_count, 100.0),
                    memory_percent=mem,
                )
            )
        processes.sort(key=lambda p: (p.cpu_percent, p.memory_percent), reverse=True)
        return tuple(processes)


_collector: MetricsCollector | None = None
_collector_lock = threading.Lock()


def get_collector() -> MetricsCollector:
    """Devolve o coletor único do processo."""
    global _collector
    with _collector_lock:
        if _collector is None:
            _collector = MetricsCollector()
        return _collector
