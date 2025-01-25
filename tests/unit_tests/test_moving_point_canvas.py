import pytest
from unittest.mock import MagicMock, patch
import numpy as np


@pytest.fixture
def canvas(core_mock):
    from frontend.ui.widgets.moving_points_canvas import MovingPointsCanvas

    canvas = MovingPointsCanvas(
        core=core_mock,
        point_radius=5.0,
        num_points=100,
        use_texture=True,
        cursor_push=True,
        r1=15.0,
        r2=30.0,
    )
    return canvas


@pytest.fixture
def core_mock():
    core = MagicMock()
    core.generate_points.return_value = np.zeros((100, 2))  # 100 точек в центре
    core.generate_deltas.return_value = np.random.uniform(-0.1, 0.1, (100, 2))
    return core


def test_canvas_initialization(canvas):
    assert canvas.num_points == 100
    assert canvas.use_texture is True
    assert canvas.cursor_push is True
    assert canvas.points.shape == (100, 2)
    assert np.all(canvas.points == 0)  # Все точки должны быть в центре
    assert canvas.deltas.shape == (100, 2)


def test_canvas_update_num_points(canvas, core_mock):
    canvas.update_num_points(200)
    assert canvas.num_points == 200
    assert canvas.points.shape == (200, 2)
    assert core_mock.generate_points.called


def test_canvas_update_positions(canvas):
    initial_points = canvas.points.copy()
    canvas.update_positions()
    assert not np.array_equal(initial_points, canvas.points)


def test_canvas_update_states(canvas):
    canvas.states = np.zeros(100, dtype=int)
    canvas.update_states()
    assert canvas.is_updating_states is False