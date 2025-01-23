from __future__ import annotations

from typing import *

from frontend.constants import RenderingConstants, UpdateIntervals, CameraSettings, OpenGLSettings
from frontend.ui.shader_source import VERTEX_SHADER, FRAGMENT_SHADER
from frontend.ui.state_updater import UpdateStatesWorker
from frontend.ui.renderer import RenderState, PointRenderer
from frontend.ui.canvas_state import CanvasState
from frontend.ui.input_handler import InputHandler

from PyQt6.QtGui import QMovie, QSurfaceFormat, QWheelEvent, QMouseEvent
import moderngl
import numpy as np
from OpenGL.GL import GL_POINT_SPRITE, GL_MULTISAMPLE
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF
from PyQt6.QtGui import QImage
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from frontend.core.protocol import Core

def create_surface_format() -> QSurfaceFormat:
    """Creates and configures OpenGL surface format"""
    fmt = QSurfaceFormat()
    fmt.setVersion(OpenGLSettings.VERSION_MAJOR, OpenGLSettings.VERSION_MINOR)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setSamples(OpenGLSettings.SAMPLES)
    fmt.setDepthBufferSize(OpenGLSettings.DEPTH_BUFFER_SIZE) 
    fmt.setStencilBufferSize(OpenGLSettings.STENCIL_BUFFER_SIZE)
    return fmt

class MovingPointsCanvas(QOpenGLWidget):
    """Canvas widget for rendering and managing moving points"""

    follow_mode_changed = pyqtSignal(bool)

    def __init__(
        self,
        core: Core,
        point_radius: float = RenderingConstants.DEFAULT_POINT_RADIUS,
        num_points: int = RenderingConstants.DEFAULT_NUM_POINTS,
        image_path: Optional[str] = None,
        r1: float = RenderingConstants.DEFAULT_R1,
        r2: float = RenderingConstants.DEFAULT_R2,
    ):
        super().__init__()
        self.setFormat(create_surface_format())
        
        # Initialize core components
        self._init_core_components(core, point_radius, num_points, image_path, r1, r2)
        
        # Setup timers
        self._setup_timers()
        
        # Initialize state
        self._init_state()

    def _init_core_components(self, core: Core, point_radius: float, num_points: int, 
                            image_path: Optional[str], r1: float, r2: float) -> None:
        """Initialize core components and parameters"""
        self.core = core
        self.state = CanvasState()
        self.input_handler = InputHandler()
        self.point_radius = point_radius
        self.num_points = num_points
        self.image_path = image_path
        self.use_texture = image_path is not None
        self.r1 = r1
        self.r2 = r2

    def _init_state(self) -> None:
        """Initialize state variables"""
        self.mouse_dragging = False
        self.last_mouse_pos: Optional[QPointF] = None
        self.show_cursor_coords = False
        self.is_updating_states = False
        self.cursor_coords = np.zeros(2, dtype=np.float64)
        self.follow_radius = RenderingConstants.DEFAULT_FOLLOW_RADIUS
        
        # Generate initial points and states
        self.points = self.core.generate_points(self.num_points, self.state.zoom_factor)
        self.states = np.zeros(self.num_points, dtype=int)
        self.update_deltas()

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    def _setup_timers(self) -> None:
        """Setup and start update timers"""
        # Position update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_positions)
        self.timer.start(UpdateIntervals.POSITION_UPDATE)

        # Target update timer
        self.target_update_timer = QTimer()
        self.target_update_timer.timeout.connect(self.update_deltas)
        self.target_update_timer.start(UpdateIntervals.TARGET_UPDATE)

        # State update timer
        self.state_update_timer = QTimer()
        self.state_update_timer.timeout.connect(self.update_states)
        self.state_update_timer.start(UpdateIntervals.STATE_UPDATE)

        self.core_thread = QThread(parent=self)

        self.follow_radius: float = RenderingConstants.DEFAULT_FOLLOW_RADIUS

        self.setFocusPolicy(
            Qt.FocusPolicy.ClickFocus
        )  # Widget receives focus when clicked

    def update_deltas(self):
        self.deltas = self.core.generate_deltas(
            self, self.num_points, self.state.speed_factor
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
        self.points = self.core.generate_points(self.num_points, self.state.zoom_factor)
        self.states = np.zeros(self.num_points, dtype=int)
        self.indices = np.arange(self.num_points, dtype=np.int32)
        self.index_buffer = self.ctx.buffer(self.indices.tobytes())
        self.update_deltas()
        self.update_buffers()
        self.update()

    def update_positions(self):
        interpolation_speed = 1.0 / RenderingConstants.FPS
        self.points += self.deltas * interpolation_speed

        # If tracking is enabled, center the camera on the selected cat

        if self.state.followed_cat_id is not None:
            followed_cat_pos = self.points[self.state.followed_cat_id]

            target_x = -followed_cat_pos[0]
            target_y = -followed_cat_pos[1]

            # Smoothly move camera to target position
            self.state.pan_offset[0] = (
                self.state.pan_offset[0] * (1 - CameraSettings.SMOOTHNESS) + target_x * CameraSettings.SMOOTHNESS
            )
            self.state.pan_offset[1] = (
                self.state.pan_offset[1] * (1 - CameraSettings.SMOOTHNESS) + target_y * CameraSettings.SMOOTHNESS
            )

            self.state.zoom_factor = CameraSettings.FOLLOW_ZOOM_RATIO / self.follow_radius

        # Update VBO and state buffer with new data
        if len(self.points) == len(self.states):
            self.vbo.write(self.points.astype("f4").tobytes())
            self.state_buffer.write(self.states.astype("i4").tobytes())
        self.update()

    def init_buffers(self):
        # Create Vertex Buffer Object (VBO) for positions

        self.vbo = self.ctx.buffer(self.points.astype("f4").tobytes())

        # Create a Buffer for states

        self.state_buffer = self.ctx.buffer(self.states.astype("i4").tobytes())

        indices = np.arange(len(self.points), dtype=np.int32)
        self.index_buffer = self.ctx.buffer(indices.astype("i4").tobytes())

        # Create Vertex Array Object (VAO)

        self.vao = self.ctx.vertex_array(
            self.shader_program,
            [
                (self.vbo, "2f", "position"),  # Bind position attribute
                (self.state_buffer, "1i", "state"),  # Bind state attribute
                (self.index_buffer, "1i", "index"),
            ],
        )

    def update_buffers(self):
        self.vbo.orphan(len(self.points) * 8)
        self.state_buffer.orphan(len(self.states) * 4)
        self.vbo.write(self.points.astype("f4").tobytes())
        self.state_buffer.write(self.states.astype("i4").tobytes())

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.enable_direct(GL_POINT_SPRITE)
        self.ctx.enable_direct(GL_MULTISAMPLE)

        self.indices = np.arange(self.num_points, dtype=np.int32)
        self.index_buffer = self.ctx.buffer(self.indices.tobytes())

        # Compile shaders and create program
        self.shader_program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=FRAGMENT_SHADER,
        )

        # Load texture if an image path is provided
        if self.use_texture:
            self.texture = self.load_texture(self.image_path)
        
        self.renderer = PointRenderer(self.ctx, self.shader_program)
        
        # Initialize buffers
        self.init_buffers()

    @no_type_check
    def paintGL(self):
        self.fb = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        self.fb.clear()
        self.fb.use()

        render_state = RenderState(
            points = self.points,
            states = self.states,
            followed_cat_id=self.state.followed_cat_id,
            zoom_factor=self.state.zoom_factor,
            pan_offset=self.state.pan_offset,
            point_radius=self.point_radius,
            follow_radius=self.follow_radius,
            use_texture=self.use_texture
        )
        # Set shader uniforms

        self.renderer.setup_uniforms(render_state)
        visible_points, visible_states = self.renderer.get_visible_points(render_state)

        self.vbo.write(visible_points.astype("f4").tobytes())
        self.state_buffer.write(visible_states.astype("i4").tobytes())

        self.update_buffers()
        self.vao.render(moderngl.POINTS, vertices=self.num_points)

    def load_texture(self, file_path):
        image = QMovie(file_path).convertToFormat(QImage.Format_RGBA8888)
        width, height = image.width(), image.height()

        bits = image.bits()  # Get the texture data
        if bits is None:
            raise Exception("Failed to load texture")
        data = bits.asstring(width * height * 4)
        texture = self.ctx.texture((width, height), 4, data)
        texture.use()  # Make the texture active
        return texture

    def resizeGL(self, w: int, h: int):
        self.ctx.viewport = (0, 0, w, h)

    def wheelEvent(self, event: QWheelEvent | None):
        # Zoom in/out with the mouse wheel
        if event is None:
            return
        self.state.zoom_factor = self.input_handler.handle_wheel(event, self.state.zoom_factor)

    def mousePressEvent(self, event: QMouseEvent | None):
        if event is None:
            return
        self.input_handler.handle_mouse_press(event)

    def mouseMoveEvent(self, event: QMouseEvent | None):
        if event is None or self.last_mouse_pos is None:
            return
        new_pan_offset = self.input_handler.handle_mouse_move(
            event,
            self.width(),
            self.height(),
            self.state.zoom_factor,
            self.state.pan_offset
        )

        if new_pan_offset is not None:
            self.state.pan_offset = new_pan_offset

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.input_handler.mouse_dragging = False

    def mouseDoubleClickEvent(self, event):
        if event is None:
            return
        click_x = event.position().x()
        click_y = event.position().y()

        world_x = (click_x / self.width() * 2 - 1) / self.state.zoom_factor - self.state.pan_offset[
            0
        ]
        world_y = (
            click_y / self.height() * 2 - 1
        ) / self.state.zoom_factor - self.state.pan_offset[1]

        distances = np.linalg.norm(self.points - np.array([world_x, -world_y]), axis=1)
        nearest_cat_id = int(np.argmin(distances))

        if distances[nearest_cat_id] < self.follow_radius:
            self.state.followed_cat_id = nearest_cat_id
            self.follow_mode_changed.emit(True)
        else:
            self.state.followed_cat_id = None
            self.follow_mode_changed.emit(False)

    def keyPressEvent(self, event):
        if event is None:
            return
        if event.nativeVirtualKey() == 0x46:  # 0x46 - is the key code for F
            self.stop_following()
            self.update()

    def stop_following(self):
        self.state = CanvasState()
        self.follow_mode_changed.emit(False)
        self.update()