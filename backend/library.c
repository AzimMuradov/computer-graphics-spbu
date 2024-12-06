#include "library.h"

#include <math.h>
#include <stddef.h>
#include <stdlib.h>

#include "third-party/kdtree/kdtree.c"


// static const int CAT_STATE_CALM = 0;
static const int CAT_STATE_HISSES = 1;
static const int CAT_STATE_WANTS_TO_FIGHT = 2;


static double drunk_cats_g_fight_radius = 0.0;
static double drunk_cats_g_hiss_radius = 0.0;


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
    size_t cat_count,
    const OpenGlPosition *cat_positions,
    unsigned int window_width,
    unsigned int window_height,
    float scale
);

/**
 * Generate random unsigned double in the range of `[0.0, 1.0]`.
 *
 * @returns By default: random double in `[0.0, 1.0]`,
 *          or if `TEST` defined: `0.0`.
 */
static double rand_ud(void);


void drunk_cats_configure(const double fight_radius, const double hiss_radius) {
    drunk_cats_g_fight_radius = fight_radius;
    drunk_cats_g_hiss_radius = hiss_radius;
}

int *drunk_cats_calculate_states(
    const size_t cat_count,
    const OpenGlPosition *cat_positions,
    const unsigned int window_width,
    const unsigned int window_height,
    const float scale
) {
    double *positions = convert_opengl_to_plain_coordinates(
        cat_count, cat_positions,
        window_width, window_height, scale
    );
    int *states = calloc(cat_count, sizeof(int));

    // Recalculate states

    struct kdtree *tree = kd_create(2);

    // Populate kd_tree
    for (size_t i = 0; i < cat_count; i++) {
        kd_insert(tree, positions + 2 * i, (void *) i);
    }

    // Calculate "wants to fight" states
    for (size_t i = 0; i < cat_count; i++) {
        const int *state = &states[i];

        if (*state == CAT_STATE_WANTS_TO_FIGHT) continue;

        struct kdres *fight_cats = kd_nearest_range(tree, positions + 2 * i, drunk_cats_g_fight_radius);
        if (fight_cats == NULL) exit(1);

        if (kd_res_size(fight_cats) > 1) {
            for (; !kd_res_end(fight_cats); kd_res_next(fight_cats)) {
                const size_t fight_cat_i = (size_t) kd_res_item_data(fight_cats);
                states[fight_cat_i] = CAT_STATE_WANTS_TO_FIGHT;
            }
        }
        kd_res_free(fight_cats);
    }

    // Calculate "hisses" states
    for (size_t i = 0; i < cat_count; i++) {
        int *state = &states[i];

        if (*state == CAT_STATE_WANTS_TO_FIGHT) continue;

        struct kdres *hiss_cats = kd_nearest_range(tree, positions + 2 * i, drunk_cats_g_hiss_radius);
        if (hiss_cats == NULL) exit(1);

        for (; !kd_res_end(hiss_cats); kd_res_next(hiss_cats)) {
            const size_t other_cat_i = (size_t) kd_res_item_data(hiss_cats);
            if (i == other_cat_i) continue;
            const double dist = hypot(
                positions[2 * i] - positions[2 * other_cat_i],
                positions[2 * i + 1] - positions[2 * other_cat_i + 1]
            );
            if (rand_ud() <= (drunk_cats_g_fight_radius * drunk_cats_g_fight_radius) / (dist * dist)) {
                *state = CAT_STATE_HISSES;
                break;
            }
        }
        kd_res_free(hiss_cats);
    }

    kd_free(tree);

    free(positions);

    return states;
}

void drunk_cats_free_states(int *states) {
    free(states);
}


// Internal

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

static double rand_ud(void) {
#ifndef TEST
    return (double) rand() / (double) RAND_MAX;
#else
    return 0.0;
#endif
}
