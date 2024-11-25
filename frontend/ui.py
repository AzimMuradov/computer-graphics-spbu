from __future__ import annotations

from functools import partial
from typing import *
import moderngl
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QOpenGLWidget,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class Core(Protocol):
    def __init__(self): ...
    def start_ui(self, app: QApplication, window: MainWindow): ...
    def update_num_points(self, window: MainWindow, num_points: int): ...
    def update_speed(self, window: MainWindow, speed: int): ...
    def generate_points(self, count: int, zoom_factor: float) -> np.ndarray: ...
    def generate_deltas(
        self, widget: MovingPointsCanvas, count: int, speed: float
    ) -> np.ndarray: ...
    def update_states(
        self, num_points: int, points: np.ndarray, width: int, height: int
    ) -> np.ndarray: ...


# Vertex shader code with zoom and pan transformations
vertex_shader_code = """
#version 410 core

in vec2 position; // Point position
in int state; // Point state (0, 1, or 2)
flat out int fragState; // Pass state to fragment shader
uniform float pointRadius;
uniform float zoom;
uniform vec2 panOffset;

void main() {
    gl_PointSize = pointRadius * 2.0 * zoom;
    gl_Position = vec4((position + panOffset) * zoom, 0.0, 1.0); // Output requires vec4(float)
    fragState = state; // Pass state to fragment shader
}
"""

# Fragment shader code to sample from texture or set color
fragment_shader_code = """
#version 410 core

flat in int fragState; // State passed from vertex shader
uniform sampler2D pointTexture;
uniform bool useTexture;
out vec4 fragColor;

void main() {
    if (useTexture) {
        vec2 coord = gl_PointCoord;
        fragColor = texture(pointTexture, coord);
    } else {
        vec2 coord = 2.0 * gl_PointCoord - 1.0;

        if (dot(coord, coord) > 1.0) {
                discard;
            }

        // Color based on state
        if (fragState == 0) {
            fragColor = vec4(0.0, 0.7, 1.0, 1.0); // Blue
        } else if (fragState == 1) {
            fragColor = vec4(0.0, 1.0, 0.0, 1.0); // Green
        } else if (fragState == 2) {
            fragColor = vec4(1.0, 0.0, 0.0, 1.0); // Red
        }
    }
}
"""
from PyQt5.QtCore import QObject, QThread, pyqtSignal


# Worker class to handle the heavy computation
class UpdateStatesWorker(QObject):
    finished = pyqtSignal(np.ndarray)  # Signal to return the result

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
        # Perform the heavy computation
        states = self.core.update_states(
            self.num_points, self.points, self.width, self.height
        )
        self.finished.emit(states)  # Emit the result when done


class MovingPointsCanvas(QGLWidget):

    FPS = 100

    def __init__(
        self,
        core: Core,
        point_radius=5,
        num_points=50000,
        image_path=None,
        r1: float = 0.1,
        r2: float = 0.1,
    ):
        super().__init__()
        self.core = core
        self.point_radius = point_radius
        self.num_points = num_points
        self.image_path = image_path
        self.use_texture = image_path is not None
        self.zoom_factor = 1.0  # Initial zoom factor
        self.pan_offset = np.array([0.0, 0.0], dtype=np.float64)  # Initial pan offset
        self.mouse_dragging = False  # Track if mouse is dragging
        self.last_mouse_pos = None  # Last mouse position for panning
        self.show_cursor_coords = False  # Flag to toggle cursor display
        self.is_updating_states = False
        self.cursor_coords = np.array(
            [0.0, 0.0], dtype=np.float64
        )  # Store cursor coordinates
        self.speed_factor = 1.0  # Initial speed factor
        self.r1 = r1
        self.r2 = r2

        # Generate random points and directions
        self.points = self.core.generate_points(self.num_points, self.zoom_factor)
        self.states = np.zeros(self.num_points, dtype=int)

        # Timer for updating points
        self.timer = QTimer()
        self.core_thread = QThread(parent=self)

        # Initial target positions as current positions
        self.update_deltas()
        self.target_update_timer = QTimer()
        self.state_update_timer = QTimer()
        # Timer to update target positions

        self.target_update_timer.timeout.connect(self.update_deltas)
        self.state_update_timer.timeout.connect(self.update_states)
        self.state_update_timer.start(500)
        self.target_update_timer.start(500)  # Update targets every 0.5 seconds
        self.timer.start(round(1000 / self.FPS))
        self.timer.timeout.connect(self.update_positions)

    def update_deltas(self):
        self.deltas = self.core.generate_deltas(
            self, self.num_points, self.speed_factor
        )

    def update_states(self):
        # Use a worker thread for the heavy computation
        if self.is_updating_states:
            return  # Skip if a thread is already running
        self.is_updating_states = True  # Mark as running
        self.core_thread = QThread(parent=self)
        self.worker = UpdateStatesWorker(
            self.core, self.num_points, self.points, self.width(), self.height()
        )
        self.worker.moveToThread(self.core_thread)

        # Connect signals and slots
        self.core_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_states_update)
        self.worker.finished.connect(self.core_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.core_thread.finished.connect(self.core_thread.deleteLater)
        self.worker.finished.connect(self.reset_update_flag)
        # Start the thread
        self.core_thread.start()

    def reset_update_flag(self):
        """Reset the flag to allow the next thread to start."""
        self.is_updating_states = False

    def handle_states_update(self, new_states: np.ndarray):
        # Update states in the main thread
        self.states = new_states

    def update_num_points(self, num_points: int):
        self.num_points = num_points
        self.points = self.core.generate_points(self.num_points, self.zoom_factor)
        self.states = np.zeros(self.num_points, dtype=int)
        self.update_deltas()
        self.initializeGL()

    def update_positions(self):
        interpolation_speed = 1.0 / self.FPS
        self.points += self.deltas * interpolation_speed

        # Update VBO and state buffer with new data
        self.vbo.write(self.points.astype("f4").tobytes())
        self.state_buffer.write(self.states.astype("i4").tobytes())

        self.update()

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.enable_direct(GL_POINT_SPRITE)

        # Compile shaders and create program
        self.shader_program = self.ctx.program(
            vertex_shader=vertex_shader_code,
            fragment_shader=fragment_shader_code,
        )

        # Load texture if an image path is provided
        if self.use_texture:
            self.texture = self.load_texture(self.image_path)

        # Create Vertex Buffer Object (VBO) for positions
        self.vbo = self.ctx.buffer(self.points.astype("f4").tobytes())

        # Create a Buffer for states
        self.state_buffer = self.ctx.buffer(self.states.astype("i4").tobytes())

        # Create Vertex Array Object (VAO)
        self.vao = self.ctx.vertex_array(
            self.shader_program,
            [
                (self.vbo, "2f", "position"),  # Bind position attribute
                (self.state_buffer, "1i", "state"),  # Bind state attribute
            ],
        )

    def load_texture(self, file_path):
        image = QImage(file_path).convertToFormat(QImage.Format_RGBA8888)
        width, height = image.width(), image.height()

        bits = image.bits()  # Get the texture data
        if bits is None:
            raise Exception("Failed to load texture")
        data = bits.asstring(width * height * 4)
        texture = self.ctx.texture((width, height), 4, data)
        texture.use()  # Make the texture active
        return texture

    @no_type_check
    def paintGL(self):
        self.ctx.clear(0.0, 0.0, 0.0)  # Clear the screen with black

        # Set shader uniforms
        self.shader_program["pointRadius"].value = self.point_radius
        self.shader_program["zoom"].value = float(self.zoom_factor)
        self.shader_program["panOffset"].value = tuple(self.pan_offset)
        self.shader_program["useTexture"].value = self.use_texture

        # Bind the texture if used
        if self.use_texture:
            self.texture.use(0)
            self.shader_program["pointTexture"].value = 0

        # Render the points
        self.vao.render(moderngl.POINTS, vertices=self.num_points)

    def resizeGL(self, w: int, h: int):
        glViewport(0, 0, w, h)

    def wheelEvent(self, event):
        # Zoom in/out with the mouse wheel
        self.zoom_factor *= 1.1 if event.angleDelta().y() > 0 else 0.9
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_dragging = True
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.mouse_dragging:
            # Calculate movement difference
            dx = (event.x() - self.last_mouse_pos.x()) / self.width()  # type: ignore[attr-defined]
            dy = (event.y() - self.last_mouse_pos.y()) / self.height()  # type: ignore[attr-defined]

            # Update pan offset, scaled by zoom factor
            self.pan_offset[0] += dx / self.zoom_factor
            self.pan_offset[1] -= dy / self.zoom_factor
            self.last_mouse_pos = event.pos()

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_dragging = False


class MainWindow(QMainWindow):
    def __init__(
        self,
        point_radius: float,
        num_points: int,
        image_path: str,
        width: int,
        height: int,
        core: Core,
    ):
        super().__init__()
        self.resize(width, height)
        self.setWindowTitle("Optimized Moving Points Field with OpenGL")
        self.core = core
        self.canvas = MovingPointsCanvas(
            core=self.core,
            point_radius=point_radius,
            num_points=num_points,
            image_path=image_path,
        )

        # Number of points control
        self.num_points_label = QLabel("Number of Points:")
        self.num_points_input = QSpinBox()
        self.num_points_input.setRange(1, 1000000)
        self.num_points_input.setValue(num_points)

        # Speed control slider
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 1000)
        self.speed_slider.setValue(200)  # Set default speed factor to 1.0 (scaled)
        self.speed_label = QLabel("Speed:")

        # Layout for controls
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.speed_label)
        control_layout.addWidget(self.speed_slider)
        control_layout.addWidget(self.num_points_label)
        control_layout.addWidget(self.num_points_input)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control_layout.addWidget(self.canvas)
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()

        # Connect with core
        self.speed_slider.valueChanged.connect(partial(self.core.update_speed, self))
        self.num_points_input.valueChanged.connect(
            partial(self.core.update_num_points, self)
        )

        # Main widget setup
        main_widget = QWidget()
        main_widget.setLayout(control_layout)
        self.setCentralWidget(main_widget)

    def update_num_points(self, value: int):
        self.canvas.update_num_points(value)

    # Exponentially scale the speed factor
    def update_speed(self, value: int):
        self.canvas.speed_factor = 1.5 ** ((value - 200) / 20)
