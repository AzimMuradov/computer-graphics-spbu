VERTEX_SHADER = """
#version 410 core

in vec2 position; // Point position
in int state; // Point state (0, 1, or 2)
in int index;
flat out int fragState; // Pass state to fragment shader
flat out int fragIndex;
uniform float pointRadius;
uniform float zoom;
uniform vec2 panOffset;
uniform int highlightedIndex; // Index of the highlighted point

void main() {
    gl_PointSize = pointRadius * 2.0 * zoom;
    gl_Position = vec4((position + panOffset) * zoom, 0.0, 1.0); // Output requires vec4(float)
    fragState = state; // Pass state to fragment shader
    fragIndex = index;
}
"""

FRAGMENT_SHADER = """
#version 410 core

flat in int fragIndex;
flat in int fragState; // State passed from vertex shader
uniform sampler2D stateTexture0;
uniform sampler2D stateTexture1;
uniform sampler2D stateTexture2;
uniform bool useTexture;
uniform int highlightedIndex;  // Index of follo
out vec4 fragColor;

float star(vec2 p, float r, int n, float m) {
    float an = 3.141593 / float(n);
    float en = 3.141593 / m;
    vec2 acs = vec2(cos(an), sin(an));
    vec2 ecs = vec2(cos(en), sin(en));
    float bn = mod(atan(p.x, p.y), 2.0 * an) - an;
    p = length(p) * vec2(cos(bn), abs(sin(bn)));
    p -= r * acs;
    p += ecs * clamp(-dot(p, ecs), 0.0, r * acs.y / ecs.y);
    return length(p) * sign(p.x);
}

void main() {
    vec2 coord;
    vec2 starCoord;

    if (useTexture) {
        coord = gl_PointCoord;
        starCoord = 2.0 * gl_PointCoord - 1.0;

         if (fragState == 0) {
            fragColor = texture(stateTexture0, coord);
        } else if (fragState == 1) {
            fragColor = texture(stateTexture1, coord);
        } else if (fragState == 2) {
            fragColor = texture(stateTexture2, coord);
        }
    } else {
        coord = 2.0 * gl_PointCoord - 1.0;
        starCoord = coord;

        if (dot(coord, coord) > 1.0) {
                discard;
            }

        // Color based on state
        if (fragState == 0) {
            fragColor = vec4(0.0, 0.7, 1.0, 1.0); // Blue
        } else if (fragState == 1) {
            fragColor = vec4(0.0, 1.0, 0.0, 1.0); // Green
        } else if (fragState == 2) {
            fragColor = vec4(1.0, 0.0, 0.0, 1.0); // Red
        }
    }

    if (fragIndex == highlightedIndex) {
        float s = star(starCoord * 1.5, 0.3, 5, 3.0);
        if (s < 0.0) {
            fragColor = vec4(1.0, 1.0, 1.0, 1.0); // White star
        }
    }
}
"""
