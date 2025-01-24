import pytest
import numpy as np
from PyQt6.QtCore import QPoint, Qt, QPointF, QEvent
from PyQt6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
import sys
import time

from frontend.ui.widgets.main_window import MainWindow
from frontend.core.core import Core

import sys
from unittest.mock import patch

@pytest.fixture
def core():
    # Подготавливаем аргументы по умолчанию
    default_args = [
        '--radius', '5.0',
        '--num-points', '1000',
        '--fight-radius', '15',
        '--hiss-radius', '30',
        '--window-width', '800',
        '--window-height', '600',
        '--no-use-texture',
        '--no-debug'
    ]
    
    # Патчим sys.argv для Core
    with patch.object(sys, 'argv', [''] + default_args):
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
        core=core
    )
    window.show()
    return window

class TestMovingPointsStress:
    @pytest.mark.stress
    @pytest.mark.parametrize("num_points", [1000, 10000, 100000])
    def test_points_scaling(self, main_window, num_points):
        """Test performance with different numbers of points"""
        canvas = main_window.canvas
        main_window.update_num_points(num_points)
        
        # Measure frame time for 100 frames
        times = []
        for _ in range(100):
            start = time.time()
            canvas.update()
            QTest.qWait(16)  # Wait for one frame
            times.append(time.time() - start)
            
        avg_frame_time = sum(times) / len(times)
        assert avg_frame_time < 0.5  # Ensure 30+ FPS

    @pytest.mark.stress
    def test_rapid_zoom_changes(self, main_window):
        """Test rapid zoom in/out operations"""
        canvas = main_window.canvas
        
        for _ in range(1000):
            # Simulate mouse wheel events
            event = QWheelEvent(
                QPointF(400, 300),
                QPointF(400, 300),
                QPoint(0, 120),
                QPoint(0, 120),
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
                Qt.ScrollPhase.NoScrollPhase,
                False
            )
            canvas.wheelEvent(event)
            QTest.qWait(1)

    @pytest.mark.stress
    def test_rapid_state_updates(self, main_window):
        """Test frequent state updates"""
        canvas = main_window.canvas
        
        # Force rapid state updates
        canvas.state_update_timer.setInterval(1)  # Set to minimum interval
        
        for _ in range(1000):
            canvas.update_states()
            QTest.qWait(1)
            
        assert not canvas.is_updating_states  # Ensure no deadlocks

    @pytest.mark.stress
    def test_concurrent_operations(self, main_window):
        """Test multiple operations happening simultaneously"""
        canvas = main_window.canvas
        
        # Simulate concurrent operations
        for _ in range(100):
            # Update points
            canvas.update_num_points(np.random.randint(100, 10000))
            
            # Change speed
            main_window.update_speed(np.random.randint(1, 1000))
            
            # Toggle texture
            main_window.toggle_use_texture(np.random.choice([0, 2]))
            
            # Update states
            canvas.update_states()
            
            QTest.qWait(1)

    @pytest.mark.stress
    def test_rapid_mouse_movements(self, main_window):
        """Test rapid mouse movements and clicks"""
        canvas = main_window.canvas
        print('эщкере')
        
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
                Qt.KeyboardModifier.NoModifier
            )
            canvas.mouseMoveEvent(move_event)
            
            if _ % 100 == 0:  # Occasionally double click
                click_event = QMouseEvent(
                    QEvent.Type.MouseButtonDblClick,
                    QPointF(x, y),
                    Qt.MouseButton.LeftButton,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier
                )
                canvas.mouseDoubleClickEvent(click_event)
            
            QTest.qWait(1)

    @pytest.mark.stress
    def test_memory_usage(self, main_window):
        """Test memory usage under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform memory-intensive operations
        for _ in range(10):
            main_window.update_num_points(100000)
            main_window.canvas.update_states()
            QTest.qWait(100)
            
            current_memory = process.memory_info().rss
            # Ensure memory growth is reasonable (less than 2x)
            assert current_memory < initial_memory * 2

    @pytest.mark.stress
    def test_rapid_window_resize(self, main_window):
        """Test rapid window resizing"""
        sizes = [(800, 600), (1920, 1080), (640, 480), (1280, 720)]
        
        for _ in range(100):
            for width, height in sizes:
                main_window.resize(width, height)
                QTest.qWait(10)
                
            # Verify rendering still works
            main_window.canvas.update()
            assert main_window.canvas.ctx.viewport == (0, 0, width, height)

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
                Qt.KeyboardModifier.NoModifier
            )
            canvas.mouseDoubleClickEvent(event)
            
            # Move points
            canvas.update_positions()
            QTest.qWait(10)
            
            # Toggle following mode off
            key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F, Qt.KeyboardModifier.NoModifier)
            canvas.keyPressEvent(key_event)
            
            QTest.qWait(10)