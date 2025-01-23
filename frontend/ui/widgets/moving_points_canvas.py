from __future__ import annotations

from typing import *

from frontend.constants import (
    RenderingConstants,
    UpdateIntervals,
    CameraSettings,
    OpenGLSettings,
)
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

    # Initialization

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

        self._init_core_components(core, point_radius, num_points, image_path, r1, r2)
        self._setup_timers()
        self._init_state()

    def _init_core_components(
        self,
        core: Core,
        point_radius: float,
        num_points: int,
        image_path: Optional[str],
        r1: float,
        r2: float,
    ):
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

    def _init_state(self):
        """Initialize state variables"""
        self.show_cursor_coords = False
        self.is_updating_states = False
        self.cursor_coords = np.zeros(2, dtype=np.float64)
        self.follow_radius = RenderingConstants.DEFAULT_FOLLOW_RADIUS

        # Generate initial points and states
        self.points = self.core.generate_points(self.num_points, self.state.zoom_factor)
        self.states = np.zeros(self.num_points, dtype=int)
        self.update_deltas()

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    def _setup_timers(self):
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

        self.setFocusPolicy(
            Qt.FocusPolicy.ClickFocus
        )  # Widget receives focus when clicked

    # OpenGL Setup and Rendering

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

    def load_texture(self, file_path):
        """Load texture from file"""
        image = QMovie(file_path).convertToFormat(QImage.Format_RGBA8888)
        width, height = image.width(), image.height()

        bits = image.bits()
        if bits is None:
            raise Exception("Failed to load texture")
        data = bits.asstring(width * height * 4)
        texture = self.ctx.texture((width, height), 4, data)
        texture.use()
        return texture

    @no_type_check
    def paintGL(self):
        """Render the scene"""
        self.fb = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        self.fb.clear()
        self.fb.use()

        render_state = RenderState(
            points=self.points,
            states=self.states,
            followed_cat_id=self.state.followed_cat_id,
            zoom_factor=self.state.zoom_factor,
            pan_offset=self.state.pan_offset,
            point_radius=self.point_radius,
            follow_radius=self.follow_radius,
            use_texture=self.use_texture,
        )
        # Set shader uniforms

        # Render points using current state
        self.renderer.setup_uniforms(render_state)
        visible_points, visible_states = self.renderer.get_visible_points(render_state)

        self.vbo.write(visible_points.astype("f4").tobytes())
        self.state_buffer.write(visible_states.astype("i4").tobytes())

        self.update_buffers()
        self.vao.render(moderngl.POINTS, vertices=self.num_points)

    def resizeGL(self, w: int, h: int):
        self.ctx.viewport = (0, 0, w, h)

    # Buffer Managment

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

    # State Updates

    def update_num_points(self, num_points: int):
        """Update the number of points being rendered"""
        self.num_points = num_points
        self.points = self.core.generate_points(self.num_points, self.state.zoom_factor)
        self.states = np.zeros(self.num_points, dtype=int)
        self.indices = np.arange(self.num_points, dtype=np.int32)
        self.index_buffer = self.ctx.buffer(self.indices.tobytes())
        self.update_deltas()
        self.update_buffers()
        self.update()

    def update_positions(self):
        """Update point positions and camera if following"""
        self._update_point_positions()
        self._update_camera_if_following()
        self._update_render_buffers()

    def _update_point_positions(self):
        """Update positions based on current deltas"""
        interpolation_speed = 1.0 / RenderingConstants.FPS
        self.points += self.deltas * interpolation_speed

    def _update_camera_if_following(self):
        """Update camera position when following a point"""
        if self.state.followed_cat_id is None:
            return

        followed_pos = self.points[self.state.followed_cat_id]
        target_pos = -followed_pos

        self.state.pan_offset = self._smooth_camera_movement(
            self.state.pan_offset, target_pos
        )
        self.state.zoom_factor = CameraSettings.FOLLOW_ZOOM_RATIO / self.follow_radius

    def _smooth_camera_movement(
        self, current_pos: np.ndarray, target_pos: np.ndarray
    ) -> np.ndarray:
        """Smooth camera movement using interpolation"""
        return (
            current_pos * (1 - CameraSettings.SMOOTHNESS)
            + target_pos * CameraSettings.SMOOTHNESS
        )

    def _update_render_buffers(self):
        """Update render buffers if states match points"""
        if len(self.points) == len(self.states):
            self.vbo.write(self.points.astype("f4").tobytes())
            self.state_buffer.write(self.states.astype("i4").tobytes())
        self.update()

    def update_deltas(self):
        """Update movement deltas"""
        self.deltas = self.core.generate_deltas(
            self, self.num_points, self.state.speed_factor
        )

    def update_states(self):
        """Update states using worker thread"""

        if self.is_updating_states:
            return  # Skip if a thread is already running

        self.is_updating_states = True  # Mark as running
        self._start_state_update_worker()

    def _start_state_update_worker(self):
        """Initialize and start state update worker thread"""
        self.core_thread = QThread(parent=self)
        self.worker = UpdateStatesWorker(
            self.core, self.num_points, self.points, self.width(), self.height()
        )

        self._setup_worker_connections()
        self.core_thread.start()

    def _setup_worker_connections(self):
        """Setup signal connections for worker thread"""
        self.worker.moveToThread(self.core_thread)

        # Connect signals
        self.core_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.handle_states_update)
        self.worker.finished.connect(self.core_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.core_thread.finished.connect(self.core_thread.deleteLater)
        self.worker.finished.connect(self.reset_update_flag)

    def reset_update_flag(self):
        """Reset the flag to allow the next thread to start."""
        self.is_updating_states = False

    def handle_states_update(self, new_states: np.ndarray):
        """Handle state updates from worker thread"""
        self.states = new_states

    def stop_following(self):
        """Stop following mode and reset state"""
        self.state = CanvasState()
        self.follow_mode_changed.emit(False)

    # Event Handlers

    def wheelEvent(self, event: QWheelEvent | None):
        """Handle mouse wheel zoom events"""
        if event is None:
            return
        self.state.zoom_factor = self.input_handler.handle_wheel(
            event, self.state.zoom_factor
        )

    def mousePressEvent(self, event: QMouseEvent | None):
        """Handle mouse press events"""
        if event is None:
            return
        self.input_handler.handle_mouse_press(event)

    def mouseMoveEvent(self, event: QMouseEvent | None):
        """Handle mouse movement for panning"""
        if event is None or self.input_handler.last_mouse_pos is None:
            return

        new_pan_offset = self.input_handler.handle_mouse_move(
            event,
            self.width(),
            self.height(),
            self.state.zoom_factor,
            self.state.pan_offset,
        )

        if new_pan_offset is not None:
            self.state.pan_offset = new_pan_offset

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.input_handler.mouse_dragging = False

    def mouseDoubleClickEvent(self, event):
        """Handle double click for point selection"""
        if event is None or self.state.followed_cat_id is not None:
            return

        world_pos = self._get_world_coordinates(event.position())
        selected_cat_id = self._find_nearest_cat_id(world_pos)

        self._handle_following_mode_starting(selected_cat_id)

    def _get_world_coordinates(self, screen_pos: QPointF) -> np.ndarray:
        """Convert screen coordinates to world coordinates"""
        world_x = (
            screen_pos.x() / self.width() * 2 - 1
        ) / self.state.zoom_factor - self.state.pan_offset[0]
        world_y = (
            screen_pos.y() / self.height() * 2 - 1
        ) / self.state.zoom_factor - self.state.pan_offset[1]
        return np.array([world_x, -world_y])

    def _find_nearest_cat_id(self, world_pos: np.ndarray) -> int:
        """Find the nearest point to given world coordinates"""
        distances = np.linalg.norm(self.points - world_pos, axis=1)
        return int(np.argmin(distances))

    def _handle_following_mode_starting(self, point_id: int):
        distances = np.linalg.norm(self.points - self.points[point_id], axis=1)

        if distances[point_id] < self.follow_radius:
            self.state.followed_cat_id = point_id
            self.follow_mode_changed.emit(True)
        else:
            self.state.followed_cat_id = None
            self.follow_mode_changed.emit(False)

    def keyPressEvent(self, event):
        if event is None:
            return
        F_KEY = 0x46
        if event.nativeVirtualKey() == F_KEY:
            self.stop_following()
            self.update()
