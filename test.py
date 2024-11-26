import sys
import numpy as np
import moderngl
from PyQt6.QtCore import QElapsedTimer, Qt, QTimer
from PyQt6.QtGui import QMatrix4x4, QQuaternion, QVector3D
from PyQt6.QtWidgets import QApplication
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode, BulletWorld
from panda3d.core import Point3, Quat, TransformState, Vec3
from PIL import Image

VERTEX_SHADER = """
#version 330

in vec3 in_position;
in vec3 in_normal;
in vec2 in_texcoord;

uniform mat4 u_mvp_matrix;
uniform mat4 u_model_matrix;
uniform mat4 u_normal_matrix;

out vec3 v_normal;
out vec3 v_position;
out vec2 v_texcoord;

void main() {
    gl_Position = u_mvp_matrix * vec4(in_position, 1.0);
    v_position = (u_model_matrix * vec4(in_position, 1.0)).xyz;
    v_normal = normalize((u_normal_matrix * vec4(in_normal, 0.0)).xyz);
    v_texcoord = in_texcoord;
}
"""

FRAGMENT_SHADER = """
#version 330

in vec3 v_normal;
in vec3 v_position;
in vec2 v_texcoord;

uniform sampler2D u_sampler;
const vec3 light_color = vec3(0.8, 0.8, 0.8);
const vec3 light_position = vec3(5.0, 7.0, 2.0);
const vec3 ambient_light = vec3(0.3, 0.3, 0.3);

out vec4 frag_color;

void main() {
    vec4 tex_color = texture(u_sampler, v_texcoord);
    vec3 normal = normalize(v_normal);
    vec3 light_dir = normalize(light_position - v_position);
    float diff = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = diff * light_color * tex_color.rgb;
    vec3 ambient = ambient_light * tex_color.rgb;
    frag_color = vec4(diffuse + ambient, tex_color.a);
}
"""


class Object3D:
    def __init__(self, ctx, world, mass, pos, vertices, indices, texture_path):
        self.ctx = ctx
        self.world = world

        self.vao = ctx.vertex_array(
            program=None,  # Assigned later in the draw call
            content=[
                (
                    ctx.buffer(vertices),
                    "3f 3f 2f",
                    "in_position",
                    "in_normal",
                    "in_texcoord",
                )
            ],
            index_buffer=ctx.buffer(indices),
        )

        self.texture = ctx.texture(
            Image.open(texture_path).size, 4, Image.open(texture_path).tobytes()
        )
        self.texture.use()

        self.shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        self.node = BulletRigidBodyNode("Box")
        self.node.setMass(mass)

        p = Point3(pos.x(), pos.y(), pos.z())
        q = Quat.identQuat()
        self.node.setTransform(TransformState.make_pos_quat_scale(p, q, Vec3(1, 1, 1)))
        self.node.addShape(self.shape)
        world.attachRigidBody(self.node)

        self.position = pos
        self.model_matrix = QMatrix4x4()

    def update_physics(self):
        transform = self.node.getTransform()
        pos = transform.pos
        hpr = transform.getHpr()
        quat = Quat()
        quat.setHpr(hpr)
        self.position = QVector3D(pos.x, pos.y, pos.z)
        self.rotation = QQuaternion(quat.getX(), quat.getY(), quat.getZ(), quat.getW())

    def draw(self, program, proj_view_matrix):
        self.update_physics()
        self.model_matrix.setToIdentity()
        self.model_matrix.translate(self.position)
        self.model_matrix.rotate(self.rotation)
        program["u_mvp_matrix"].write((proj_view_matrix * self.model_matrix).data())
        program["u_model_matrix"].write(self.model_matrix.data())
        program["u_normal_matrix"].write(
            self.model_matrix.inverted()[0].transposed().data()
        )
        self.vao.render(moderngl.TRIANGLES)


class ModernGLWindow(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ModernGL with PyQt6 and Bullet Physics")
        self.resize(400, 400)
        self.timer = QTimer()
        self.elapsed_timer = QElapsedTimer()
        self.world = BulletWorld()
        self.objects = []

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER
        )
        self.world.setGravity(Vec3(0, -9.81, 0))
        self.init_objects()
        self.timer.timeout.connect(self.update_frame)
        self.elapsed_timer.start()
        self.timer.start(16)

    def init_objects(self):
        cube_vertices, cube_indices = self.load_model("assets/cube.dae")
        self.objects.append(
            Object3D(
                self.ctx,
                self.world,
                0,
                QVector3D(0, -3, 0),
                cube_vertices,
                cube_indices,
                "assets/cube.png",
            )
        )
        self.objects.append(
            Object3D(
                self.ctx,
                self.world,
                1,
                QVector3D(0.8, 3, 0),
                cube_vertices,
                cube_indices,
                "assets/cube.png",
            )
        )

    def load_model(self, path):
        # Load model vertices and indices (similar to the original COLLADA parsing logic)
        # Returns vertices and indices as NumPy arrays
        return np.zeros((0, 8), dtype="f4"), np.zeros(0, dtype="i4")  # Placeholder

    def update_frame(self):
        self.world.doPhysics(self.elapsed_timer.elapsed() / 1000)
        self.elapsed_timer.restart()
        self.update()

    def paintGL(self):
        self.ctx.clear(0.2, 0.2, 0.2, 1.0)
        proj_view_matrix = QMatrix4x4()
        proj_matrix = QMatrix4x4()
        proj_matrix.perspective(50, self.width() / self.height(), 0.1, 100)
        view_matrix = QMatrix4x4()
        view_matrix.lookAt(QVector3D(2, 3, 5), QVector3D(0, 0, 0), QVector3D(0, 1, 0))
        proj_view_matrix = proj_matrix * view_matrix

        for obj in self.objects:
            obj.draw(self.program, proj_view_matrix)

    def resizeGL(self, w, h):
        self.ctx.viewport = (0, 0, w, h)


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    app = QApplication(sys.argv)
    window = ModernGLWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
