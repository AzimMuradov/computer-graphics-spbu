import numpy as np
from frontend.ui.canvas_state import CanvasState


def test_initial_state():
    # Arrange & Act
    state = CanvasState()

    # Assert
    assert state.zoom_factor == 1.0
    assert np.array_equal(state.pan_offset, np.array([0.0, 0.0], dtype=np.float64))
    assert state.followed_cat_id is None
    assert state.speed_factor == 1.0
    assert state.follow_radius == 0.5


def test_reset():
    # Arrange
    state = CanvasState(
        zoom_factor=2.0,
        pan_offset=np.array([10.0, 15.0], dtype=np.float64),
        followed_cat_id=42,
        speed_factor=2.5,
        follow_radius=1.0,
    )

    # Act
    state.reset()

    # Assert
    assert state.zoom_factor == 1.0
    assert np.array_equal(state.pan_offset, np.array([0.0, 0.0], dtype=np.float64))
    assert state.followed_cat_id is None

    assert state.speed_factor == 2.5
    assert state.follow_radius == 1.0
