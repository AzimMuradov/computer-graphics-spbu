import argparse
import sys
from typing import *

from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtCore import Qt
import numpy as np
from cffi import FFI
from PyQt6.QtWidgets import QApplication

from frontend.ui import MainWindow, MovingPointsCanvas, qt_surface_format


class Backend(Protocol):
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


class Core:
    def __init__(self):
        self.ffi = FFI()

        from pathlib import Path

        backend_dir = Path(__file__).parent.parent / "backend"

        with open(backend_dir / "library.h", mode="r") as f:
            dec = ""
            for line in f:
                if line.startswith("#"):
                    continue
                dec += line
            self.ffi.cdef(dec)
        self.lib = cast(Backend, self.ffi.dlopen(str(backend_dir / "libbackend.so")))

        self.init_parser()

        self.args = self.parser.parse_args()
        self.lib.drunk_cats_configure(self.args.fight_radius, self.args.hiss_radius)

    def main(self):
        QSurfaceFormat.setDefaultFormat(qt_surface_format())
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
        app = QApplication(sys.argv)
        window = MainWindow(
            point_radius=self.args.radius,
            num_points=self.args.num_points,
            image_path=self.args.image_path,
            width=self.args.window_width,
            height=self.args.window_height,
            core=self,
        )
        self.global_scale = app.devicePixelRatio()
        self.start_ui(app, window)

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
        points_ptr = self.ffi.cast("Position *", self.ffi.from_buffer(points))

        result_ptr = self.lib.drunk_cats_calculate_states(
            num_points, points_ptr, width, height, self.global_scale
        )

        # Convert the returned C array to a numpy array
        buffer: Any = self.ffi.buffer(result_ptr, num_points * self.ffi.sizeof("int"))
        result = np.frombuffer(
            buffer=buffer,
            dtype=np.int32,
        ).copy()

        self.lib.drunk_cats_free_states(result_ptr)

        return result

    def generate_points(self, count: int, zoom_factor: float) -> np.ndarray:
        points = np.random.uniform(
            -1 / zoom_factor, 1 / zoom_factor, size=(count, 2)
        ).astype(np.float64)
        return points

    def generate_deltas(
        self, widget: MovingPointsCanvas, count: int, speed: float
    ) -> np.ndarray:

        deltas = np.random.uniform(-speed / 20, speed / 20, size=(count, 2))
        return deltas.astype(np.float64)

    def init_parser(self):
        self.parser = argparse.ArgumentParser(
            description="OpenGL Moving Points Application"
        )
        self.parser.add_argument(
            "--radius",
            type=float,
            default=10,
            help="Radius of the points",
        )
        self.parser.add_argument(
            "--image-path",
            type=str,
            default=None,
            help="Path to the image file for point texture",
        )
        self.parser.add_argument(
            "--num-points",
            type=int,
            default=500,
            help="Number of points",
        )
        self.parser.add_argument(
            "--fight-radius",
            type=int,
            default=15,
            help="Radius of the cat's fight zone, must be smaller than hiss-radius",
        )
        self.parser.add_argument(
            "--hiss-radius",
            type=int,
            default=30,
            help="Radius of the cat's hiss zone, must be larger than fight-radius",
        )
        self.parser.add_argument(
            "--window-width",
            type=int,
            default=1000,
            help="Width of the window",
        )
        self.parser.add_argument(
            "--window-height",
            type=int,
            default=800,
            help="Height of the window",
        )
