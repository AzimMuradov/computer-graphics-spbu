from functools import partial
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpinBox,
    QSlider,
    QSizePolicy,
    QCheckBox,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt
from frontend.ui.widgets.moving_points_canvas import MovingPointsCanvas
from frontend.core.protocol import Core


class MainWindow(QMainWindow):
    def __init__(
        self,
        point_radius: float,
        num_points: int,
        use_texture: bool,
        width: int,
        height: int,
        core: Core,
    ):
        super().__init__()
        self.resize(width, height)
        self.setWindowTitle("Optimized Moving Points Field with OpenGL")
        self.core = core

        self.num_points = num_points
        self.use_texture = use_texture
        self.main_widget = QWidget()
        self.control_layout = QVBoxLayout()

        self._init_controls(num_points)
        self._init_canvas(point_radius, num_points, use_texture)
        self._setup_layout()
        self._connect_signals()

    def _init_controls(self, num_points: int):
        """Initialize control elements of the GUI"""
        self.controls_widget = QWidget()

        self.num_points_label = QLabel("Number of Points:")
        self.num_points_input = QSpinBox()
        self.num_points_input.setRange(1, 1000000)
        self.num_points_input.setValue(num_points)

        self.speed_label = QLabel("Speed:")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 1000)
        self.speed_slider.setValue(200)

        self.texture_checkbox = QCheckBox("Use Texture")
        self.texture_checkbox.setChecked(self.use_texture)
        self.texture_checkbox.stateChanged.connect(self.toggle_use_texture)

        self.cursor_push_checkbox = QCheckBox("Enable Cursor Push")
        self.cursor_push_checkbox.setChecked(False)
        self.cursor_push_checkbox.stateChanged.connect(self.toggle_cursor_push)

    def _init_canvas(self, point_radius: float, num_points: int, use_texture: bool):
        """Initialize the OpenGL canvas for rendering moving points"""
        self.canvas = MovingPointsCanvas(
            core=self.core,
            point_radius=point_radius,
            num_points=num_points,
            use_texture=use_texture,
        )
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def _setup_layout(self):
        """Set up the layout of all GUI elements"""
        top_layout = QHBoxLayout()

        left_controls = QVBoxLayout()

        points_layout = QHBoxLayout()
        points_layout.addWidget(self.num_points_label)
        points_layout.addWidget(self.num_points_input)

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_label)
        speed_layout.addWidget(self.speed_slider)

        left_controls.addLayout(points_layout)
        left_controls.addLayout(speed_layout)

        left_controls.addWidget(self.texture_checkbox)
        left_controls.addWidget(self.cursor_push_checkbox)

        top_layout.addLayout(left_controls)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.canvas)

        self.main_widget.setLayout(main_layout)
        self.setCentralWidget(self.main_widget)

        self.canvas.setFocus()

    def _connect_signals(self):
        """Connect all signals to their respective slots"""
        self.speed_slider.valueChanged.connect(partial(self.core.update_speed, self))
        self.num_points_input.valueChanged.connect(
            partial(self.core.update_num_points, self)
        )
        self.canvas.follow_mode_changed.connect(self.on_follow_mode_changed)

    def on_follow_mode_changed(self, is_following: bool):
        self.num_points_input.setEnabled(not is_following)

    def update_num_points(self, value: int):
        self.canvas.update_num_points(value)

    def update_speed(self, value: int):
        self.canvas.state.speed_factor = 1.5 ** ((value - 200) / 40)

    def toggle_use_texture(self, state: int):
        """Updating the value of the use_texture flag"""
        self.canvas.use_texture = bool(state)
        self.update_num_points(self.canvas.num_points)
    
    def toggle_cursor_push(self, state: int):
        """Updating the value of the cursor_push flag"""
        self.canvas.cursor_push = bool(state)
