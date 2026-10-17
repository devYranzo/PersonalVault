from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal


class WorkerSignals(QObject):
    """Señales de un Worker. Se emiten desde el hilo de trabajo."""

    succeeded = Signal(int, object)  # job_id, resultado
    failed = Signal(int, object)  # job_id, excepción


class Worker(QRunnable):
    """
    Ejecuta `fn` en un hilo del QThreadPool y avisa del resultado.

    Importante: conecta las señales a métodos de un QObject (un slot),
    nunca a lambdas. Con una lambda, PySide ejecuta el callback en el
    hilo que emite la señal y tocarías la interfaz desde el hilo de
    trabajo.
    """

    def __init__(self, job_id: int, fn: Callable[[], Any]) -> None:
        super().__init__()

        # Quien lanza el Worker lo guarda hasta recibir la señal final.
        self.setAutoDelete(False)

        self.job_id = job_id
        self.signals = WorkerSignals()
        self._fn = fn

    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as exc:
            self.signals.failed.emit(self.job_id, exc)
        else:
            self.signals.succeeded.emit(self.job_id, result)