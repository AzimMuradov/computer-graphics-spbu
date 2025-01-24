import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from frontend.core.core import Core

def test_generate_points():
    # Arrange
    count = 10
    zoom_factor = 2.0

    # Act
    points = Core.generate_points(count, zoom_factor)

    # Assert
    assert points.shape == (count, 2)
    assert np.all(points >= -1 / zoom_factor)
    assert np.all(points <= 1 / zoom_factor)


def test_generate_deltas():
    # Arrange
    count = 5
    speed = 10.0

    # Act
    deltas = Core.generate_deltas(None, count, speed)

    # Assert
    assert deltas.shape == (count, 2)
    assert np.all(deltas >= -speed / 20)
    assert np.all(deltas <= speed / 20)


@patch("frontend.core.core.Core._initialize_ffi", return_value=MagicMock())
@patch("frontend.core.core.Core._load_backend_library", return_value=MagicMock())
@patch("sys.argv", new=["program_name", "--radius", "10", "--num-points", "100"])
def test_update_states(mock_load_backend_library, mock_initialize_ffi):
    # Arrange
    num_points = 3
    points = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]], dtype=np.float64)
    width, height = 800, 600
    global_scale = 1.0

    core = Core()
    core.global_scale = global_scale

    # Mocks Setup
    mock_ffi = mock_initialize_ffi.return_value
    mock_lib = mock_load_backend_library.return_value

    mock_result_ptr = MagicMock()
    mock_lib.drunk_cats_calculate_states.return_value = mock_result_ptr

    mock_ffi.sizeof.return_value = 4

    mock_buffer_data = b"\x00\x00\x00\x00" + b"\x01\x00\x00\x00" + b"\x02\x00\x00\x00"  # 3 int (0, 1, 2)
    mock_ffi.buffer.return_value = mock_buffer_data

    # Act
    result = core.update_states(num_points, points, width, height)

    # Arrange
    mock_ffi.cast.assert_called_once_with(
        "OpenGlPosition *", mock_ffi.from_buffer(points)
    )

    mock_lib.drunk_cats_calculate_states.assert_called_once_with(
        num_points, mock_ffi.cast.return_value, width, height, global_scale
    )

    mock_lib.drunk_cats_free_states.assert_called_once_with(mock_result_ptr)

    expected_result = np.array([0, 1, 2], dtype=np.int32)
    np.testing.assert_array_equal(result, expected_result)