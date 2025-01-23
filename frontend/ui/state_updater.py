from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np
from typing import Protocol


class Core(Protocol):
    def update_states(
        self, num_points: int, points: np.ndarray, width: int, height: int
    ) -> np.ndarray: ...


class UpdateStatesWorker(QObject):
    finished = pyqtSignal(np.ndarray)

    def __init__(
        self, core: Core, num_points: int, points: np.ndarray, width: int, height: int
    ):
        super().__init__()
        self.core = core
        self.num_points = num_points
        self.points = points
        self.width = width
        self.height = height

    def run(self):
        states = self.core.update_states(
            self.num_points, self.points, self.width, self.height
        )
        self.finished.emit(states)
