import argparse
import sys

import numpy as np
from cffi import FFI
from PyQt5.QtWidgets import QApplication

from frontend.ui import MainWindow, MovingPointsCanvas


class Core:
    lib_path = "backend/libbackend.so"

    def __init__(self):
        self.ffi = FFI()
        self.lib = self.ffi.dlopen(self.lib_path)
        self.init_parser()
        self.args = self.parser.parse_args()

        with open("backend/library.h", mode="r") as f:
            dec = ""
            for line in f:
                if line.startswith("#"):
                    continue
                dec += line
            self.ffi.cdef(dec)

        self.lib.backend_init(self.args.fight_radius, self.args.hiss_radius)

    def main(self):
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
        sys.exit(app.exec_())

    def update_num_points(self, window: MainWindow, num_points: int) -> None:
        window.update_num_points(num_points)

    def update_speed(self, window: MainWindow, speed: int) -> None:
        window.update_speed(speed)

    def update_states(
        self, num_points: int, points: np.ndarray, width: int, height: int
    ) -> np.ndarray:
        points_ptr = self.ffi.cast("Cat*", self.ffi.from_buffer(points))

        result_ptr = self.lib.update_states(
            num_points, points_ptr, width, height, self.global_scale
        )
        # Convert the returned C array to a numpy array
        result = np.frombuffer(
            self.ffi.buffer(result_ptr, num_points * self.ffi.sizeof("int")),
            dtype=np.int32,
        ).copy()

        self.lib.free_states(result_ptr)

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
            default=50,
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
            default=50000,
            help="Number of points",
        )
        self.parser.add_argument(
            "--fight-radius",
            type=int,
            default=100,
            help="Radius of the cat's fight zone, must be smaller than hiss-radius",
        )
        self.parser.add_argument(
            "--hiss-radius",
            type=int,
            default=200,
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
