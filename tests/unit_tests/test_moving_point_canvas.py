import pytest
from unittest.mock import MagicMock
import numpy as np
from frontend.ui.widgets.main_window import MainWindow


@pytest.fixture
def core_mock():
    core = MagicMock()
    core.generate_points.return_value = np.zeros((100, 2))  # 100 точек в центре
    core.generate_deltas.return_value = np.random.uniform(-0.1, 0.1, (100, 2))
    return core


def test_main_window_num_points_input(core_mock):
    window = MainWindow(
        point_radius=5.0,
        num_points=100,
        use_texture=True,
        width=800,
        height=600,
        core=core_mock,
    )

    assert window.num_points_input.value() == 100

    window.num_points_input.setValue(200)
    assert window.num_points_input.value() == 200


def test_main_window_speed_slider(core_mock):
    window = MainWindow(
        point_radius=5.0,
        num_points=100,
        use_texture=True,
        width=800,
        height=600,
        core=core_mock,
    )

    assert window.speed_slider.value() == 200

    window.speed_slider.setValue(500)
    assert window.speed_slider.value() == 500
