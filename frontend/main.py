import argparse
import sys

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
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from core import PointSystem

# Vertex shader code with zoom and pan transformations
vertex_shader_code = """
#version 330
in vec2 position;
uniform float pointRadius;
uniform float zoom;
uniform vec2 panOffset;
void main() {
    gl_PointSize = pointRadius * 2.0 * zoom;
    gl_Position = vec4((position + panOffset) * zoom, 0.0, 1.0);
}
"""

# Fragment shader code to sample from texture or set color
fragment_shader_code = """
#version 330
uniform sampler2D pointTexture;
uniform bool useTexture; // Whether to use the texture
out vec4 fragColor;
void main() {
    if (useTexture) {
        vec2 coord = gl_PointCoord;
        fragColor = texture(pointTexture, coord);
    } else {
        vec2 coord = gl_PointCoord - vec2(0.5);
        float dist = length(coord);

        // Discard fragments outside the circle's radius
        if (dist > 0.5) {
            discard;
        }
        fragColor = vec4(0.0, 0.5, 1.0, 1.0);
    }
}
"""


class MovingPointsCanvas(QGLWidget):

    FPS = 100

    def __init__(
        self,
        point_radius=5,
        num_points=500,
        image_path=None,
        r1: float = 0.1,
        r2: float = 0.1,
    ):
        super().__init__()
        self.point_radius = point_radius
        self.num_points = num_points
        self.image_path = image_path
        self.use_texture = image_path is not None
        self.zoom_factor = 1.0  # Initial zoom factor
        self.pan_offset = np.array([0.0, 0.0], dtype=np.float32)  # Initial pan offset
        self.mouse_dragging = False  # Track if mouse is dragging
        self.last_mouse_pos = None  # Last mouse position for panning
        self.speed_factor = 1.0  # Initial speed factor
        self.r1 = r1
        self.r2 = r2

        # Generate random points and directions
        self.points = np.random.uniform(-1, 1, size=(self.num_points, 2)).astype(
            np.float32
        )
        self.states = np.zeros(self.num_points, dtype=int)

        # Timer for updating points
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_positions)
        self.timer.start(round(1000 / self.FPS))

        # Initial target positions as current positions
        self.target_positions = np.copy(self.points)
        self.target_update_timer = QTimer()
        # Timer to update target positions
        self.target_update_timer.timeout.connect(self.update_targets)
        # self.target_update_timer.timeout.connect(self.upate_states)
        self.target_update_timer.start(500)  # Update targets every 0.5 seconds
        self.target_generator = self.generate_new_targets()  # Initialize generator

    def generate_new_targets(self):
        while True:
            new_targets = self.points + np.random.uniform(
                -self.speed_factor / 20, self.speed_factor / 20, self.points.shape
            )
            yield new_targets

    def update_targets(self):
        # Get next target positions from the generator
        self.target_positions = next(self.target_generator)

    def upate_states(self):
        self.core.apply_deltas(self.points - self.target_positions)
        self.states = self.core.states

    def initializeGL(self):
        glClearColor(0, 0, 0, 1)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_PROGRAM_POINT_SIZE)

        # Compile shaders and create a shader program
        self.shader_program = compileProgram(
            compileShader(vertex_shader_code, GL_VERTEX_SHADER),
            compileShader(fragment_shader_code, GL_FRAGMENT_SHADER),
        )

        # Load the texture if an image path is provided
        if self.use_texture:
            self.texture = self.load_texture(self.image_path)

        # Setup the Vertex Array Object (VAO)
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Setup the Vertex Buffer Object (VBO)
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, self.points.nbytes, self.points, GL_DYNAMIC_DRAW)

        # Get the position attribute from the shader
        pos_attrib = glGetAttribLocation(self.shader_program, "position")
        glEnableVertexAttribArray(pos_attrib)
        glVertexAttribPointer(pos_attrib, 2, GL_FLOAT, GL_FALSE, 0, None)

    def load_texture(self, file_path):
        # Load image and convert to OpenGL texture
        image = QImage(file_path)
        image = image.convertToFormat(QImage.Format_RGBA8888)

        # Get image dimensions and raw data
        width, height = image.width(), image.height()
        data = image.bits().asstring(width * height * 4)

        # Generate texture ID and bind
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Upload the texture data to the GPU
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            data,
        )

        glBindTexture(GL_TEXTURE_2D, 0)
        return texture_id

    def update_positions(self):
        # Smoothly interpolate points towards the target positions
        interpolation_speed = 1.0 / self.FPS  # Adjust speed factor for smoothness
        self.points += (self.target_positions - self.points) * interpolation_speed

        # Update the VBO with new positions
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.points.nbytes, self.points)

        self.update()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        # Use the shader program and set uniforms
        glUseProgram(self.shader_program)
        glUniform1f(
            glGetUniformLocation(self.shader_program, "pointRadius"), self.point_radius
        )
        glUniform1f(glGetUniformLocation(self.shader_program, "zoom"), self.zoom_factor)
        glUniform2fv(
            glGetUniformLocation(self.shader_program, "panOffset"), 1, self.pan_offset
        )
        glUniform1i(
            glGetUniformLocation(self.shader_program, "useTexture"), self.use_texture
        )

        # Bind texture if using
        if self.use_texture:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture)
            glUniform1i(glGetUniformLocation(self.shader_program, "pointTexture"), 0)

        # Draw points
        glBindVertexArray(self.VAO)
        glDrawArrays(GL_POINTS, 0, self.num_points)

    def resizeGL(self, w, h):
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
            dx = (event.x() - self.last_mouse_pos.x()) / self.width()
            dy = (event.y() - self.last_mouse_pos.y()) / self.height()

            # Update pan offset, scaled by zoom factor
            self.pan_offset[0] += dx / self.zoom_factor
            self.pan_offset[1] -= dy / self.zoom_factor

            self.last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_dragging = False


class MainWindow(QMainWindow):
    def __init__(self, point_radius, num_points, image_path):
        super().__init__()
        self.setWindowTitle("Optimized Moving Points Field with OpenGL")
        self.canvas = MovingPointsCanvas(
            point_radius=point_radius, num_points=num_points, image_path=image_path
        )

        # Number of points control
        self.num_points_label = QLabel("Number of Points:")
        self.num_points_input = QSpinBox()
        self.num_points_input.setRange(1, 1000000)
        self.num_points_input.setValue(num_points)
        self.num_points_input.valueChanged.connect(self.update_num_points)

        # Speed control slider
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 1000)
        self.speed_slider.setValue(200)  # Set default speed factor to 1.0 (scaled)
        self.speed_slider.valueChanged.connect(self.update_speed)
        self.speed_label = QLabel("Speed:")

        # Layout for controls
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.speed_label)
        control_layout.addWidget(self.speed_slider)
        control_layout.addWidget(self.num_points_label)
        control_layout.addWidget(self.num_points_input)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control_layout.addWidget(self.canvas)

        # Main widget setup
        main_widget = QWidget()
        main_widget.setLayout(control_layout)
        self.setCentralWidget(main_widget)

    def update_num_points(self, value):
        self.canvas.num_points = value
        self.canvas.points = np.random.uniform(-1, 1, size=(value, 2)).astype(
            np.float32
        )
        self.canvas.initializeGL()
        self.canvas.update_targets()

    # Exponentially scale the speed factor
    def update_speed(self, value):
        self.canvas.speed_factor = 1.5 ** ((value - 200) / 20)


# CLI initialization
def main():
    parser = argparse.ArgumentParser(description="OpenGL Moving Points Application")
    parser.add_argument(
        "--radius", type=float, default=5.0, help="Radius of the points"
    )
    parser.add_argument(
        "--image-path",
        type=str,
        default=None,
        help="Path to the image file for point texture",
    )
    parser.add_argument("--num-points", type=int, default=500, help="Number of points")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow(
        point_radius=args.radius, num_points=args.num_points, image_path=args.image_path
    )
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
