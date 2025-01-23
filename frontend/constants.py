from dataclasses import dataclass

@dataclass
class RenderingConstants:
    FPS: int = 100
    DEFAULT_POINT_RADIUS: int = 5
    DEFAULT_NUM_POINTS: int = 500
    DEFAULT_ZOOM_FACTOR: float = 1.0
    DEFAULT_FOLLOW_RADIUS: float = 0.5
    
@dataclass
class UpdateIntervals:
    POSITION_UPDATE: int = 1  # milliseconds
    TARGET_UPDATE: int = 500  # milliseconds
    STATE_UPDATE: int = 500   # milliseconds

@dataclass
class CameraSettings:
    SMOOTHNESS: float = 0.1
    FOLLOW_ZOOM_RATIO: float = 3.00

@dataclass
class OpenGLSettings:
    VERSION_MAJOR: int = 4
    VERSION_MINOR: int = 1
    SAMPLES: int = 4
    DEPTH_BUFFER_SIZE: int = 24
    STENCIL_BUFFER_SIZE: int = 8
