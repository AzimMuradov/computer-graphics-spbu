import sys
import random
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QSizePolicy,
    QWidget,
    QVBoxLayout,
    QSpinBox,
    QLabel,
)
from PyQt5.QtGui import QPainter, QPixmap, QColor
from PyQt5.QtCore import Qt, QTimer, QTime


class MovingPointsCanvas(QWidget):
    def __init__(self, point_radius=5, num_points=50000):
        super().__init__()
        self.point_radius = point_radius
        self.num_points = num_points

        # Initialize numpy arrays for points and directions
        self.points = np.random.randint(
            0, 600, size=(self.num_points, 2)
        )  # (x, y) positions
        self.directions = np.random.choice(
            [-1, 1], size=(self.num_points, 2)
        ) * np.random.randint(1, 3, size=(self.num_points, 2))

        # Setup a buffer for rendering
        self.buffer = QPixmap(self.width(), self.height())
        self.buffer.fill(Qt.black)

        # Timer for updating points
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_positions)
        self.timer.start(20)  # Approximately 30 FPS

        # Track time for delta-based movement
        self.last_time = QTime.currentTime()

    def update_positions(self):
        # Calculate delta time in seconds
        current_time = QTime.currentTime()
        delta = self.last_time.msecsTo(current_time) / 1000.0
        self.last_time = current_time

        # Update positions based on directions and delta time
        self.points += (self.directions * delta * 50).astype(
            int
        )  # Multiply by speed factor

        # Bounce points off the window boundaries
        out_of_bounds_x = (self.points[:, 0] < self.point_radius) | (
            self.points[:, 0] > self.width() - self.point_radius
        )
        out_of_bounds_y = (self.points[:, 1] < self.point_radius) | (
            self.points[:, 1] > self.height() - self.point_radius
        )
        self.directions[out_of_bounds_x, 0] *= -1
        self.directions[out_of_bounds_y, 1] *= -1

        # Redraw buffer with new positions
        self.buffer.fill(Qt.black)
        painter = QPainter(self.buffer)
        painter.setPen(QColor(0, 100, 255))
        for point in self.points:
            painter.drawEllipse(
                point[0] - self.point_radius,
                point[1] - self.point_radius,
                self.point_radius * 2,
                self.point_radius * 2,
            )
        painter.end()

        # Trigger repaint
        self.update()

    def paintEvent(self, event):
        # Paint the buffer to the widget
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.buffer)

    def resizeEvent(self, event):
        # Resize buffer when window is resized to fit the new dimensions of the canvas
        self.buffer = QPixmap(self.width(), self.height())
        self.buffer.fill(Qt.black)
        self.points = np.random.randint(
            0, min(self.width(), self.height()), size=(self.num_points, 2)
        )
        super().resizeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optimized Moving Points Field")
        self.canvas = MovingPointsCanvas()

        # Number of points control
        self.num_points_label = QLabel("Number of Points:")
        self.num_points_input = QSpinBox()
        self.num_points_input.setRange(1, 100000)  # Adjust range as needed
        self.num_points_input.setValue(50000)
        self.num_points_input.valueChanged.connect(self.update_num_points)

        # Layout for controls
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.num_points_label)
        control_layout.addWidget(self.num_points_input)
        main_layout = QVBoxLayout()

        # Main widget setup
        main_widget = QWidget()
        main_layout.addLayout(control_layout)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.canvas)
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

    def resizeEvent(self, event):
        # Ensure the canvas resizes to take up the main window’s area minus the controls
        self.canvas.resize(
            self.width(),
            self.height()
            - self.num_points_label.height()
            - self.num_points_input.height(),
        )
        super().resizeEvent(event)

    def update_num_points(self, value):
        # Reinitialize the canvas with new number of points
        self.canvas.num_points = value
        self.canvas.points = np.random.randint(
            0, min(self.canvas.width(), self.canvas.height()), size=(value, 2)
        )
        self.canvas.directions = np.random.choice(
            [-1, 1], size=(value, 2)
        ) * np.random.randint(1, 3, size=(value, 2))
        self.canvas.update_positions()


# CLI initialization
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)  # Initial window size
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
