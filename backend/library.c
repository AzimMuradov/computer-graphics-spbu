#include "library.h"

#include <math.h>
#include <stddef.h>
#include <stdlib.h>

#include "internal/random.c"

#define NO_PTHREADS
#include "third-party/kdtree/kdtree.c"


static double backend_g_fight_radius = 0.0;
static double backend_g_hiss_radius = 0.0;

static const int CAT_MOOD_CALM = 0;
static const int CAT_MOOD_HISSES = 1;
static const int CAT_MOOD_WANTS_TO_FIGHT = 2;


PixelPosition *recalculate_positions(size_t cat_count, Cat *cats, int window_width, int window_height, float scale) {
    PixelPosition *positions = calloc(cat_count, sizeof(PixelPosition));

    for (size_t i = 0; i < cat_count; i++) {
        Cat *cat = &cats[i];
        PixelPosition *pos = &positions[i];
        pos->x = (cat->x + 1.0) * window_width * 0.5 * scale;
        pos->y = (1.0 + cat->y) * window_height * 0.5 * scale;
    }
    return positions;
}


int *update_states(size_t cat_count, Cat *cats, int window_width, int window_height, float scale) {

    PixelPosition *positions = recalculate_positions(cat_count, cats, window_width, window_height, scale);
    CatState *states = calloc(cat_count, sizeof(CatState));

    for (size_t i = 0; i < cat_count; i++) {
        CatState *state = &states[i];
        state->pos = positions[i];
        state->mood = CAT_MOOD_CALM;
    }

    // Recalculate mood data

    struct kdtree *tree = kd_create(2);

    // Populate kd_tree
    for (size_t i = 0; i < cat_count; i++) {
        CatState *state = &states[i];
        const double pos[2] = {state->pos.x, state->pos.y};
        kd_insert(tree, pos, state);
    }

    // Calculate "wants to fight" mood
    for (size_t i = 0; i < cat_count; i++) {
        const CatState *state = &states[i];

        if (state->mood == CAT_MOOD_WANTS_TO_FIGHT) continue;

        const double pos[2] = {state->pos.x, state->pos.y};

        struct kdres *fight_cats = kd_nearest_range(tree, pos, backend_g_fight_radius);
        if (fight_cats == NULL) exit(1);

        if (kd_res_size(fight_cats) > 1) {
            for (; !kd_res_end(fight_cats); kd_res_next(fight_cats)) {
                CatState *fight_state = kd_res_item_data(fight_cats);
                fight_state->mood = CAT_MOOD_WANTS_TO_FIGHT;
            }
        }
        kd_res_free(fight_cats);
    }

    // Calculate "hisses" mood
    for (size_t i = 0; i < cat_count; i++) {
        CatState *state = &states[i];

        if (state->mood == CAT_MOOD_WANTS_TO_FIGHT) continue;

        const double pos[2] = {state->pos.x, state->pos.y};

        struct kdres *cats = kd_nearest_range(tree, pos, backend_g_hiss_radius);
        if (cats == NULL) exit(1);

        for (; !kd_res_end(cats); kd_res_next(cats)) {
            CatState *other_cat = kd_res_item_data(cats);
            if (state == other_cat) continue;
            const double dist = hypot(state->pos.x - other_cat->pos.x, state->pos.y - other_cat->pos.y);
            if (rand_ud() <= (backend_g_fight_radius * backend_g_fight_radius) / (dist * dist)) {
                state->mood = CAT_MOOD_HISSES;
                if (other_cat->mood == CAT_MOOD_CALM) {
                    other_cat->mood = CAT_MOOD_HISSES;
                }
                break;
            }
        }
        kd_res_free(cats);
    }

    kd_free(tree);

    int* states_mood = calloc(cat_count, sizeof(int));
    for (size_t i = 0; i < cat_count; i++) {
        states_mood[i] = states[i].mood;
    }

    free(states);
    free(positions);
    return states_mood;
}

void free_states(int *states) {
    free(states);
}


void backend_init(
    const double fight_radius,
    const double hiss_radius
) {
    backend_g_fight_radius = fight_radius;
    backend_g_hiss_radius = hiss_radius;
}


