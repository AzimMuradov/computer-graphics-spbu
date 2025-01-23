# frontend/widgets/main_window.py
from functools import partial
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpinBox,
    QSlider,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from frontend.ui.widgets.moving_points_canvas import MovingPointsCanvas
from frontend.core.protocol import Core

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
        
        # Создание основного виджета и компоновки
        self.main_widget = QWidget()
        self.control_layout = QVBoxLayout()
        
        # Инициализация элементов управления
        self._init_controls(num_points)
        
        # Инициализация холста
        self._init_canvas(point_radius, num_points, image_path)
        
        # Настройка компоновки
        self._setup_layout()
        
        # Подключение сигналов
        self._connect_signals()

    def _init_controls(self, num_points: int):
        # Контроль количества точек
        self.num_points_label = QLabel("Number of Points:")
        self.num_points_input = QSpinBox()
        self.num_points_input.setRange(1, 1000000)
        self.num_points_input.setValue(num_points)

        # Контроль скорости
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 1000)
        self.speed_slider.setValue(200)
        self.speed_label = QLabel("Speed:")

    def _init_canvas(self, point_radius: float, num_points: int, image_path: str):
        self.canvas = MovingPointsCanvas(
            core=self.core,
            point_radius=point_radius,
            num_points=num_points,
            image_path=image_path,
        )
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

    def _setup_layout(self):
        # Добавление элементов управления
        self.control_layout.addWidget(self.speed_label)
        self.control_layout.addWidget(self.speed_slider)
        self.control_layout.addWidget(self.num_points_label)
        self.control_layout.addWidget(self.num_points_input)
        self.control_layout.addWidget(self.canvas)
        
        # Настройка главного виджета
        self.main_widget.setLayout(self.control_layout)
        self.setCentralWidget(self.main_widget)
        
        # Установка фокуса на холст
        self.canvas.setFocus()

    def _connect_signals(self):
        self.speed_slider.valueChanged.connect(
            partial(self.core.update_speed, self)
        )
        self.num_points_input.valueChanged.connect(
            partial(self.core.update_num_points, self)
        )
        self.canvas.follow_mode_changed.connect(self.on_follow_mode_changed)

    def on_follow_mode_changed(self, is_following: bool):
        self.num_points_input.setEnabled(not is_following)

    def update_num_points(self, value: int):
        self.canvas.update_num_points(value)

    def update_speed(self, value: int):
        self.canvas.speed_factor = 1.5 ** ((value - 200) / 20)