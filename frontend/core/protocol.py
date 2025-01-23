from typing import Protocol, Any
import numpy as np
from PyQt6.QtWidgets import QApplication


class Core(Protocol):
    def start_ui(
        self, app: QApplication, window: Any
    ): ...
    def update_num_points(self, window: Any, num_points: int): ...
    def update_speed(self, window: Any, speed: int): ...
    def generate_points(self, count: int, zoom_factor: float) -> np.ndarray: ...
    def generate_deltas(self, widget: Any, count: int, speed: float) -> np.ndarray: ...
    def update_states(
        self, num_points: int, points: np.ndarray, width: int, height: int
    ) -> np.ndarray: ...
