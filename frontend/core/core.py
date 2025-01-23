import argparse
import logging
import sys
from pathlib import Path
from typing import *

import numpy as np
from cffi import FFI
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtWidgets import QApplication

from frontend.ui.widgets.moving_points_canvas import (
    MovingPointsCanvas,
    create_surface_format,
)
from frontend.ui.widgets.main_window import MainWindow
from frontend.constants import RenderingConstants

# Set up logger
logging.basicConfig()
logger = logging.getLogger()


class Backend(Protocol):
    """Protocol defining the interface for the backend library"""

    def drunk_cats_configure(self, fight_radius: float, hiss_radius: float): ...

    def drunk_cats_calculate_states(
        self,
        cat_count: int,
        cat_positions: Any,
        window_width: int,
        window_height: int,
        scale: float,
    ) -> Any: ...

    def drunk_cats_free_states(self, states: Any): ...


class ArgumentParser:
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="OpenGL Moving Points Application")
        parser.add_argument(
            "--radius",
            type=float,
            default=RenderingConstants.DEFAULT_POINT_RADIUS,
            help="Radius of the points",
        )
        parser.add_argument(
            "--image-path",
            type=str,
            default=None,
            help="Path to the image file for point texture",
        )
        parser.add_argument(
            "--num-points",
            type=int,
            default=RenderingConstants.DEFAULT_NUM_POINTS,
            help="Number of points",
        )
        parser.add_argument(
            "--fight-radius",
            type=int,
            default=15,
            help="Radius of the cat's fight zone, must be smaller than hiss-radius",
        )
        parser.add_argument(
            "--hiss-radius",
            type=int,
            default=30,
            help="Radius of the cat's hiss zone, must be larger than fight-radius",
        )
        parser.add_argument(
            "--window-width", type=int, default=1000, help="Width of the window"
        )
        parser.add_argument(
            "--window-height", type=int, default=800, help="Height of the window"
        )
        parser.add_argument(
            "--debug", type=bool, default=False, help="Enable debug messages"
        )
        return parser


class Core:
    """Main application core handling backend integration and UI coordination"""

    def __init__(self):
        self.ffi = self._initialize_ffi()
        self.lib = self._load_backend_library()
        self.parser = ArgumentParser.create_parser()
        self.args = self.parser.parse_args()
        self.global_scale = 1.0

        self._configure_logging()
        self._configure_backend()

    def _initialize_ffi(self) -> FFI:
        ffi = FFI()
        backend_dir = Path(__file__).parent.parent.parent / "backend"

        with open(backend_dir / "library.h", mode="r") as f:
            declarations = "".join(line for line in f if not line.startswith("#"))
            ffi.cdef(declarations)
        return ffi

    def _load_backend_library(self) -> Backend:
        backend_path = Path(__file__).parent.parent.parent / "backend" / "libbackend.so"
        return cast(Backend, self.ffi.dlopen(str(backend_path)))

    def _configure_logging(self) -> None:
        if self.args.debug:
            logger.setLevel(logging.DEBUG)

    def _configure_backend(self) -> None:
        self.lib.drunk_cats_configure(self.args.fight_radius, self.args.hiss_radius)

    def main(self) -> None:
        self._configure_qt()
        app = QApplication(sys.argv)
        window = self._create_main_window()
        self.global_scale = app.devicePixelRatio()
        self.start_ui(app, window)

    @staticmethod
    def _configure_qt() -> None:
        QSurfaceFormat.setDefaultFormat(create_surface_format())
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)

    def _create_main_window(self) -> MainWindow:
        return MainWindow(
            point_radius=self.args.radius,
            num_points=self.args.num_points,
            image_path=self.args.image_path,
            width=self.args.window_width,
            height=self.args.window_height,
            core=self,
        )

    def start_ui(self, app: QApplication, window: MainWindow) -> None:
        window.show()
        sys.exit(app.exec())

    def update_num_points(self, window: MainWindow, num_points: int) -> None:
        window.update_num_points(num_points)

    def update_speed(self, window: MainWindow, speed: int) -> None:
        window.update_speed(speed)

    def update_states(
        self, num_points: int, points: np.ndarray, width: int, height: int
    ) -> np.ndarray:
        points_ptr = self.ffi.cast("OpenGlPosition *", self.ffi.from_buffer(points))
        result_ptr = self.lib.drunk_cats_calculate_states(
            num_points, points_ptr, width, height, self.global_scale
        )

        result = self._process_state_results(result_ptr, num_points)
        self.lib.drunk_cats_free_states(result_ptr)
        self._log_debug_states(result)

        return result

    def _process_state_results(self, result_ptr: Any, num_points: int) -> np.ndarray:
        buffer = self.ffi.buffer(result_ptr, num_points * self.ffi.sizeof("int"))
        return np.frombuffer(buffer=buffer, dtype=np.int32).copy()

    @staticmethod
    def _log_debug_states(result: np.ndarray) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            mapping = {0: "calm", 1: "hisses", 2: "wants to fight"}
            log_obj = {i: mapping[state] for i, state in enumerate(result)}
            logger.debug(str(log_obj))

    @staticmethod
    def generate_points(count: int, zoom_factor: float) -> np.ndarray:
        """Generate random point positions."""
        return np.random.uniform(
            -1 / zoom_factor, 1 / zoom_factor, size=(count, 2)
        ).astype(np.float64)

    @staticmethod
    def generate_deltas(
        widget: MovingPointsCanvas, count: int, speed: float
    ) -> np.ndarray:
        """Generate random movement deltas for points."""
        return np.random.uniform(-speed / 20, speed / 20, size=(count, 2)).astype(
            np.float64
        )
