#include "library.h"

#include <math.h>
#include <stddef.h>
#include <stdlib.h>

#include "third-party/kdtree/kdtree.c"


static double backend_g_fight_radius = 0.0;
static double backend_g_hiss_radius = 0.0;

// static const int CAT_MOOD_CALM = 0;
static const int CAT_MOOD_HISSES = 1;
static const int CAT_MOOD_WANTS_TO_FIGHT = 2;


static double *recalculate_positions(
    size_t cat_count,
    const Position *cat_positions,
    int window_width,
    int window_height,
    float scale
);

static double rand_ud(void);


void backend_configure(const double fight_radius, const double hiss_radius) {
    backend_g_fight_radius = fight_radius;
    backend_g_hiss_radius = hiss_radius;
}

int *backend_calculate_states(
    const size_t cat_count,
    const Position *cat_positions,
    const int window_width,
    const int window_height,
    const float scale
) {
    double *positions = recalculate_positions(cat_count, cat_positions, window_width, window_height, scale);
    int *moods = calloc(cat_count, sizeof(int));

    // Recalculate mood data

    struct kdtree *tree = kd_create(2);

    // Populate kd_tree
    for (size_t i = 0; i < cat_count; i++) {
        kd_insert(tree, positions + 2 * i, (void *) i);
    }

    // Calculate "wants to fight" mood
    for (size_t i = 0; i < cat_count; i++) {
        const int *mood = &moods[i];

        if (*mood == CAT_MOOD_WANTS_TO_FIGHT) continue;

        struct kdres *fight_cats = kd_nearest_range(tree, positions + 2 * i, backend_g_fight_radius);
        if (fight_cats == NULL) exit(1);

        if (kd_res_size(fight_cats) > 1) {
            for (; !kd_res_end(fight_cats); kd_res_next(fight_cats)) {
                const size_t fight_cat_i = (size_t) kd_res_item_data(fight_cats);
                moods[fight_cat_i] = CAT_MOOD_WANTS_TO_FIGHT;
            }
        }
        kd_res_free(fight_cats);
    }

    // Calculate "hisses" mood
    for (size_t i = 0; i < cat_count; i++) {
        int *mood = &moods[i];

        if (*mood == CAT_MOOD_WANTS_TO_FIGHT) continue;

        struct kdres *hiss_cats = kd_nearest_range(tree, positions + 2 * i, backend_g_hiss_radius);
        if (hiss_cats == NULL) exit(1);

        for (; !kd_res_end(hiss_cats); kd_res_next(hiss_cats)) {
            const size_t other_cat_i = (size_t) kd_res_item_data(hiss_cats);
            if (i == other_cat_i) continue;
            const double dist = hypot(
                positions[2 * i] - positions[2 * other_cat_i],
                positions[2 * i + 1] - positions[2 * other_cat_i + 1]
            );
            if (rand_ud() <= (backend_g_fight_radius * backend_g_fight_radius) / (dist * dist)) {
                *mood = CAT_MOOD_HISSES;
                break;
            }
        }
        kd_res_free(hiss_cats);
    }

    kd_free(tree);

    free(positions);

    return moods;
}

void backend_free_states(int *states) {
    free(states);
}


// Internal

static double *recalculate_positions(
    const size_t cat_count,
    const Position *cat_positions,
    const int window_width,
    const int window_height,
    const float scale
) {
    double *flat_cat_positions = malloc(cat_count * 2 * sizeof(double));

    for (size_t i = 0; i < cat_count; i++) {
        const Position cat_pos = cat_positions[i];
        flat_cat_positions[2 * i] = (cat_pos.x + 1.0) * window_width * 0.5 * scale;
        flat_cat_positions[2 * i + 1] = (cat_pos.y + 1.0) * window_height * 0.5 * scale;
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
