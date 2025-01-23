from dataclasses import dataclass, field
import numpy as np
from typing import Optional

@dataclass
class CanvasState:
    zoom_factor: float = 1.0
    pan_offset: np.ndarray = field(
        default_factory=lambda: np.array([0.0, 0.0], dtype=np.float64)
    )
    followed_cat_id: Optional[int] = None
    speed_factor: float = 1.0
    follow_radius: float = 0.5
    
    def reset(self):
        self.zoom_factor = 1.0
        self.pan_offset = np.array([0.0, 0.0], dtype=np.float64)
        self.followed_cat_id = None