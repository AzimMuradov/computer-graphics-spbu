#include "library.h"

#include <stddef.h>
#include <stdlib.h>


/**
 * Convert cat positions in the OpenGL coordinate system to the plain flatten coordinates.
 *
 * Every position `{x, y}` in the OpenGL coordinate system
 * will be scaled using the given window size and scale.
 *
 * The given array `[{x_1, y_1}, ..., {x_n, y_n}]`
 * will be restructured to `[x_1, y_1, ..., x_n, y_n]`.
 *
 * @param cat_count Number of cat positions given.
 * @param cat_positions Array of cat positions in the OpenGL coordinate system.
 * @param window_width Window width, must be positive.
 * @param window_height Window height, must be positive.
 * @param scale Window scale (e.g. 1.0 - no scale, 2.0 - two times scale), must be positive.
 *
 * @returns Cat positions as plain flatten coordinates.
 */
static double *convert_opengl_to_plain_coordinates(
    const size_t cat_count,
    const OpenGlPosition *cat_positions,
    const unsigned int window_width,
    const unsigned int window_height,
    const float scale
) {
    double *flat_cat_positions = malloc(cat_count * 2 * sizeof(double));

    for (size_t i = 0; i < cat_count; i++) {
        const OpenGlPosition cat_pos = cat_positions[i];
        flat_cat_positions[2 * i] = cat_pos.x * 0.5 * window_width * scale;
        flat_cat_positions[2 * i + 1] = cat_pos.y * 0.5 * window_height * scale;
    }

    return flat_cat_positions;
}
