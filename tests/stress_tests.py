import pytest
from PyQt6.QtWidgets import QApplication
from frontend.ui.widgets.main_window import MainWindow
from frontend.core.core import Core
import numpy as np

# Используем фикстуру 'qapp' из pytest-qt, чтобы избежать создания QApplication вручную
@pytest.fixture
def app(qtbot):
    """Создаем экземпляр приложения для тестирования"""
    core = Core()
    window = MainWindow(
        point_radius=1.0,
        num_points=1000000,  # Стресс-тест с 1 миллионом точек
        use_texture=False,
        width=800,
        height=600,
        core=core,
    )
    qtbot.addWidget(window)  # Используем qtbot для управления окном
    return window

def test_large_number_of_points(app, qtbot):
    """Тест производительности при большом количестве точек"""
    app.show()  # Показываем окно
    qtbot.wait(1000)  # Даем приложению время на отрисовку
    assert app.canvas.num_points == 1000000  # Проверяем, что точек действительно миллион
    assert isinstance(app.canvas.points, np.ndarray)
    assert app.canvas.points.shape == (1000000, 2)

def test_maximum_speed(app, qtbot):
    """Тест производительности при максимальной скорости"""
    app.speed_slider.setValue(1000)  # Установка максимальной скорости
    qtbot.wait(100)  # Даем приложению время для применения изменений

    initial_positions = app.canvas.points.copy()  # Сохраняем начальные позиции
    qtbot.wait(500)  # Ждем, чтобы точки успели обновиться

    new_positions = app.canvas.points
    assert not np.array_equal(initial_positions, new_positions), "Точки не двигаются при максимальной скорости"