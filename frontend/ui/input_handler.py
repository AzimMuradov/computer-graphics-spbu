# frontend/handlers/input_handler.py
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QMouseEvent, QWheelEvent
import numpy as np
from typing import Optional

class InputHandler:
    def __init__(self):
        self.mouse_dragging = False
        self.last_mouse_pos: Optional[QPointF] = None
        
    def handle_wheel(self, event: QWheelEvent, zoom_factor: float) -> float:
        return zoom_factor * (1.1 if event.angleDelta().y() > 0 else 0.9)
        
    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_dragging = True
            self.last_mouse_pos = event.position()
            return True
        return False
        
    def handle_mouse_move(
        self, 
        event: QMouseEvent, 
        width: int, 
        height: int,
        zoom_factor: float,
        pan_offset: np.ndarray
    ) -> Optional[np.ndarray]:
        if not self.mouse_dragging or self.last_mouse_pos is None:
            return None
            
        dx = (event.position().x() - self.last_mouse_pos.x()) / width
        dy = (event.position().y() - self.last_mouse_pos.y()) / height
        
        pan_offset[0] += dx / zoom_factor
        pan_offset[1] -= dy / zoom_factor
        self.last_mouse_pos = event.position()
        
        return pan_offset