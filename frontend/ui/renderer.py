from dataclasses import dataclass
import numpy as np
import moderngl
from typing import *


@dataclass
class RenderState:
    points: np.ndarray
    states: np.ndarray
    followed_cat_id: Optional[int]
    zoom_factor: float
    pan_offset: np.ndarray
    point_radius: float
    follow_radius: float
    use_texture: bool


class PointRenderer:
    def __init__(
        self,
        ctx: moderngl.Context,
        shader_program: moderngl.Program,
        textures: list[moderngl.Texture],
    ):
        self.ctx = ctx
        self.shader_program = shader_program
        self.textures = textures

    @no_type_check
    def setup_uniforms(self, state: RenderState):
        self.shader_program["pointRadius"].value = state.point_radius
        self.shader_program["zoom"].value = float(state.zoom_factor)
        self.shader_program["panOffset"].value = tuple(state.pan_offset)
        self.shader_program["useTexture"].value = state.use_texture
        self.shader_program["highlightedIndex"].value = (
            state.followed_cat_id if state.followed_cat_id is not None else -1
        )
        if state.use_texture:
            self.shader_program["pointRadius"].value = state.point_radius * 4
            self.textures[0].use(location=0)  # Привязка текстуры для state = 0
            self.shader_program["stateTexture0"] = 0
            self.textures[1].use(location=1)
            self.shader_program["stateTexture1"] = 1
            self.textures[2].use(location=2)
            self.shader_program["stateTexture2"] = 2

    def get_visible_points(self, state: RenderState) -> tuple[np.ndarray, np.ndarray]:
        if state.followed_cat_id is not None:
            followed_cat_pos = state.points[state.followed_cat_id]
            distances = np.linalg.norm(state.points - followed_cat_pos, axis=1)
            visible_indices = distances <= state.follow_radius
            return state.points[visible_indices], state.states[visible_indices]
        return state.points, state.states
