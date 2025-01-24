import pytest
import numpy as np
from PyQt6.QtCore import QPoint, Qt, QPointF, QEvent
from PyQt6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from typing import no_type_check
import sys

from frontend.ui.widgets.main_window import MainWindow
from frontend.core.core import Core

import sys
from unittest.mock import patch


@pytest.fixture
def core():
    default_args = [
        "--radius",
        "5.0",
        "--num-points",
        "1000",
        "--fight-radius",
        "15",
        "--hiss-radius",
        "30",
        "--window-width",
        "800",
        "--window-height",
        "600",
        "--no-use-texture",
        "--no-debug",
    ]

    with patch.object(sys, "argv", [""] + default_args):
        core = Core()
        return core


@pytest.fixture
def app(qapp):
    return qapp


@pytest.fixture
def qapp():
    if not QApplication.instance():
        return QApplication([])
    return QApplication.instance()


@pytest.fixture
def main_window(app, core):
    window = MainWindow(
        point_radius=5.0,
        num_points=1000,
        use_texture=False,
        width=800,
        height=600,
        core=core,
    )
    window.show()
    return window


class TestMovingPointsStress:
    @no_type_check
    @pytest.mark.stress
    def test_rapid_mouse_movements(self, main_window):
        """Test rapid mouse movements and clicks"""
        canvas = main_window.canvas

        for _ in range(1000):
            # Generate random mouse positions
            x = np.random.randint(0, canvas.width())
            y = np.random.randint(0, canvas.height())

            # Create mouse move event
            move_event = QMouseEvent(
                QEvent.Type.MouseMove,
                QPointF(x, y),
                Qt.MouseButton.NoButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )
            canvas.mouseMoveEvent(move_event)

            if _ % 100 == 0:  # Occasionally double click
                click_event = QMouseEvent(
                    QEvent.Type.MouseButtonDblClick,
                    QPointF(x, y),
                    Qt.MouseButton.LeftButton,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier,
                )
                canvas.mouseDoubleClickEvent(click_event)

            QTest.qWait(10)

    @no_type_check
    @pytest.mark.stress
    def test_texture_switching(self, main_window):
        """Test rapid texture switching"""
        for _ in range(500):
            main_window.toggle_use_texture(2)  # Enable
            QTest.qWait(1)
            main_window.toggle_use_texture(0)  # Disable
            QTest.qWait(1)

        # Verify final state is stable
        main_window.canvas.update()
        QTest.qWait(10)

    @no_type_check
    @pytest.mark.stress
    def test_following_mode_stress(self, main_window):
        """Test stress on following mode"""
        canvas = main_window.canvas

        for _ in range(100):
            # Simulate double click at random positions
            x = np.random.randint(0, canvas.width())
            y = np.random.randint(0, canvas.height())

            event = QMouseEvent(
                QEvent.Type.MouseButtonDblClick,
                QPointF(x, y),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            canvas.mouseDoubleClickEvent(event)

            # Move points
            canvas.update_positions()
            QTest.qWait(10)

            # Toggle following mode off
            key_event = QKeyEvent(
                QEvent.Type.KeyPress, Qt.Key.Key_F, Qt.KeyboardModifier.NoModifier
            )
            canvas.keyPressEvent(key_event)

            QTest.qWait(10)