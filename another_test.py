#! /usr/bin/python3

from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.Qt import QTimer, QElapsedTimer
import moderngl as gl
import numpy as np

TWOPI = np.pi * 2

opengl_version = (3, 3)


def qt_surface_format():
    fmt = QSurfaceFormat()
    fmt.setVersion(*opengl_version)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setSamples(4)
    return fmt


# in show(), before QApplication init

# in View.__init__()


class MyWidget(QOpenGLWidget):

    N = 99999
    W, H = 680, 360
    point_size = 0.8
    scale = 2
    speed = 0.25
    noise = 0.15

    def __init__(self):
        ...
        super().__init__()
        self.setFormat(qt_surface_format())
        self.resize(self.scale * self.W, self.scale * self.H)
        self.setMaximumSize(self.size())
        self.setMinimumSize(self.size())
        self.setWindowTitle(f"{self.N} Particles Moving Somewhat Randomly")
        self.timer = QTimer()
        self.clock = QElapsedTimer()

    def paintGL(self):
        ...
        self.setup()
        self.paintGL = self.render

    def setup(self):
        ...
        self.ctx = gl.create_context()
        self.ctx.enable(gl.BLEND)
        self.ctx.point_size = self.point_size * self.scale

        self.move_program = self.ctx.program(
            vertex_shader=move_vshader, varyings=["v_data"]
        )
        self.move_program["dimensions"] = self.W, self.H
        self.move_program["speed"] = self.speed

        self.align_program = self.ctx.program(
            vertex_shader=align_vshader, varyings=["v_data"]
        )
        self.align_program["N"] = self.N
        self.align_program["noise"] = self.noise
        self.align_program["data"] = 0
        self.align_program["offsets"] = 1
        self.align_program["dimensions"] = self.W, self.H

        texture_width = 8192
        texture_height = self.N // texture_width
        if self.N % texture_width:
            texture_height += 1
        texture_size = texture_width, texture_height

        particle_data = np.zeros((texture_width * texture_height, 4), dtype="f4")
        particle_data[: self.N, :3] = np.random.random((self.N, 3)) * np.array(
            (self.W, self.H, TWOPI)
        )
        particles_texture0 = self.ctx.texture(
            texture_size, 4, particle_data.tobytes(), dtype="f4"
        )
        particles_texture0.filter = gl.NEAREST, gl.NEAREST
        particles_texture1 = self.ctx.texture(texture_size, 4, dtype="f4")
        particles_texture1.filter = gl.NEAREST, gl.NEAREST
        self.particles_textures = [particles_texture0, particles_texture1]
        self.move_vao = self.ctx.vertex_array(self.move_program, [])
        self.align_vao = self.ctx.vertex_array(self.align_program, [])
        self.out_buffer = self.ctx.buffer(reserve=particle_data.nbytes, dynamic=True)

        number_of_cells = self.W * self.H
        offsets_texture_width = min(8192, number_of_cells)
        offsets_texture_height = 1
        if number_of_cells > 8192:
            offsets_texture_height = number_of_cells // 8192 + 1
        offsets_texture_size = offsets_texture_width, offsets_texture_height
        self.offsets_texture = self.ctx.texture(offsets_texture_size, 1, dtype="u4")
        self.offsets_texture.filter = gl.NEAREST, gl.NEAREST
        self.render_program = self.ctx.program(
            vertex_shader=vshader, fragment_shader=fshader
        )
        self.render_program["dimensions"] = self.W, self.H
        self.render_vao = self.ctx.vertex_array(self.render_program, [])

        self.blend_program = self.ctx.program(
            vertex_shader=blend_vshader, fragment_shader=blend_fshader
        )
        self.blend_vao = self.ctx.vertex_array(self.blend_program, [])

        self.texture0 = self.ctx.texture((self.width(), self.height()), 4)
        self.fbo0 = self.ctx.framebuffer(color_attachments=(self.texture0,))
        self.texture1 = self.ctx.texture(self.texture0.size, 4)
        self.fbo1 = self.ctx.framebuffer(color_attachments=(self.texture1,))

        self.timer.timeout.connect(self.update)
        self.runtime = 0
        self.mouseReleaseEvent = self.togglePaused
        self.setToolTip("click to start/pause")

    def render(self):
        ...
        fb = self.ctx.detect_framebuffer()
        fb.clear()

        self.particles_textures[0].use(location=0)
        self.fbo0.use()
        self.fbo0.clear()
        self.render_vao.render(gl.POINTS, self.N)

        self.fbo1.use()
        self.texture0.use(location=0)
        self.blend_vao.render(gl.TRIANGLE_FAN, 4)
        self.ctx.copy_framebuffer(fb, self.fbo1)

        fb.use()

        if self.clock.isValid() and self.clock.elapsed() > 25:
            in_texture, out_texture = self.particles_textures
            in_texture.use(location=0)
            self.move_vao.transform(self.out_buffer, vertices=self.N)

            data = np.frombuffer(self.out_buffer.read(self.N * 16), dtype="f4").reshape(
                (self.N, 4)
            )

            # SORT THE DATA BY CELL
            sorted_indices = np.argsort(data[:, 3])
            # data = data[sorted_indices, :]
            # data.resize((out_texture.width * out_texture.height, 4))
            data = np.resize(
                data[sorted_indices], (out_texture.width * out_texture.height, 4)
            )
            # END SORTING DATA - if not sorting just write out_buffer
            out_texture.write(data.tobytes())

            # COMPUTE OFFSETS ARRAY
            offsets = np.ones(self.W * self.H, dtype="uint32") * 0xFFFFFFFF
            prev_cell = None
            for i, cell in enumerate(data[: self.N, 3]):
                cell = int(cell)
                if cell != prev_cell:
                    offsets[cell] = i
                    prev_cell = cell

            offsets = np.resize(
                offsets, (self.offsets_texture.width, self.offsets_texture.height)
            )
            self.offsets_texture.write(offsets.tobytes())

            out_texture.use(location=0)
            self.offsets_texture.use(location=1)
            self.align_vao.transform(self.out_buffer, vertices=self.N)
            in_texture.write(self.out_buffer)

            self.runtime += self.clock.restart()

    def togglePaused(self, event):
        ...
        if self.clock.isValid():
            self.timer.stop()
            self.clock.invalidate()
        else:
            self.timer.start()
            self.clock.start()


move_vshader = """#version 330
#define TWOPI radians(360.)
uniform sampler2D data;
uniform vec2 dimensions;
uniform float speed;
out vec4 v_data;

ivec2 ind(int k) {
    return ivec2(k % 8192, k / 8192);
}

void main(){
    vec3 in_vert = texelFetch(data, ind(gl_VertexID), 0).xyz;
    vec2 pos = in_vert.xy;
    float theta = in_vert.z;
    pos += speed * vec2(cos(theta), sin(theta));
    pos = fract((pos + dimensions) / dimensions) * dimensions;
    float cell = floor(pos.x) + dimensions.y * floor(pos.y);
    v_data = vec4(pos, theta, cell);
}
"""

align_vshader = """#version 330
#define TWOPI radians(360.)
uniform int N;
uniform sampler2D data;
uniform usampler2D offsets;
uniform vec2 dimensions;
uniform float noise;
out vec4 v_data;

#define MANTISSA_MASK 0x007FFFFFu
#define FLOAT_ONE     0x3F800000u

uint hash(uvec2 xy) {
    uint x = xy.x;
    uint y = xy.y;
    x += x >> 11;
    x ^= x << 7;
    x += y;
    x ^= x << 6;
    x += x >> 15;
    x ^= x << 5;
    x += x >> 12;
    x ^= x << 9;
    return x;
}

float random(vec2 uv) {
    uvec2 bits = floatBitsToUint(uv);
    uint h = hash(bits);
    h &= MANTISSA_MASK;
    h |= FLOAT_ONE;

    float r2 = uintBitsToFloat(h);
    return r2 - 1.;
}

ivec2 ind(int k) {
    return ivec2(k % 8192, k / 8192);
}

void main() {
    int W = int(dimensions.x), H = int(dimensions.y);
    ivec2 dataSize = textureSize(data, 0);
    vec4 in_vert = texelFetch(data, ind(gl_VertexID), 0);
    vec2 pos = in_vert.xy;
    float theta = in_vert.z;

    // THE ACTUAL ALIGNMENT HAPPENS HERE
    int thisCell = int(in_vert.w);
    int[9] neighborCells = int[](thisCell, thisCell+1, thisCell+W+1,
        thisCell+W, thisCell+W-1, thisCell-1, thisCell-W-1, thisCell-W,
        thisCell-W-1);
    float s = 0, c = 0;
    int n = 0;
    for(int i = 0; i < 9; ++i) {
        int cell = neighborCells[i];
        int cellX = cell % W, cellY = cell / W;
        if (cellX >= W || cellX < 0) continue;
        if (cellY >= H || cellY < 0) continue;
        int offset = int(texelFetch(offsets, ind(cell), 0).r);
        while (offset < N){
            vec4 vert = texelFetch(data, ind(offset), 0);
            if (int(vert.w) != cell) break;
            if (distance(vert.xy, pos) < 1.){
                ++n;
                float th = vert.z;
                s += sin(th);
                c += cos(th);
            }
            ++offset;
        }
    }
    s /= n;
    c /= n;

    theta = atan(s, c);
    // END OF ALIGNMENT PROCEDURE

    theta += (random(theta * pos) - .5) * TWOPI * noise;
    v_data = vec4(pos, theta, in_vert.w);
}
"""

vshader = """#version 330
#define TWOPI radians(360.)
uniform sampler2D data;
uniform float N;
uniform vec2 dimensions;
out vec3 v_color;

#define ONETHIRD 1. / 3.
#define ONESIXTH 1. / 6.
#define TWOTHIRDS 2. / 3.

float _v(float m1, float m2, float h) {
    h = fract(h);
    if (h < ONESIXTH) return m1 + (m2 - m1) * h * 6.;
    if (h < .5) return m2;
    if (h < TWOTHIRDS) return m1 + (m2 - m1) * (TWOTHIRDS * h) * 6.0;
    return m1;
}

vec3 hsl_to_rgb(vec3 hsl) {
    float l = hsl.z, h = hsl.x;
    float m1, m2;
    if (hsl.y == 0.) return vec3(l, l, l);
    if (l <= .5) m2 = l * (1. + hsl.y);
    else m2 = l + hsl.y - l * hsl.y;
    m1 = 2. * l - m2;
    return vec3(_v(m1, m2, h + ONETHIRD), _v(m1, m2, h), _v(m1, m2, h - ONETHIRD));
}

ivec2 ind(int k) {
    return ivec2(k % 8192, k / 8192);
}

void main(){
    vec3 in_vert = texelFetch(data, ind(gl_VertexID), 0).xyz;
    vec2 pos = in_vert.xy / dimensions;
    float theta = in_vert.z;
    pos = 2. * pos - 1.;
    gl_Position = vec4(pos, 0., 1.);
    v_color = hsl_to_rgb(vec3(theta / TWOPI, .5, .5));
}
"""

fshader = """#version 330
in vec3 v_color;
out vec4 frag_color;

void main() {
    float r = 2. * distance(gl_PointCoord, vec2(.5, .5));
    float alpha = step(-1., -r);
    float brightness = step(-1., -r);
    frag_color = vec4(v_color, alpha);
}
"""

blend_vshader = """#version 330
vec2[4] vertices = vec2[](
    vec2(1., 1.), vec2(-1., 1.), vec2(-1., -1.), vec2(1., -1.)
);

void main(){
    gl_Position = vec4(vertices[gl_VertexID], 0., 1.);
}
"""

blend_fshader = """#version 330
uniform sampler2D pixels;
out vec4 fragColor;

void main(){
    vec2 dimensions = vec2(textureSize(pixels, 0));
    vec4 pix = texture(pixels, gl_FragCoord.xy /dimensions);
    fragColor = vec4(pix.rgb, clamp(pix.a + .07, 0., 1.));
}
"""

if __name__ == "__main__":

    from sys import argv, exit

    QSurfaceFormat.setDefaultFormat(qt_surface_format())
    app = QApplication(argv)
    mw = MyWidget()
    mw.show()
    exit(app.exec_())
