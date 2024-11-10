#include "library.h"

#include <math.h>
#include <stddef.h>
#include <stdlib.h>

#include "internal/random.c"


static CatState *backend_g_state = NULL;
static size_t backend_g_cat_count = 0;
static double backend_g_map_width = 0.0;
static double backend_g_map_height = 0.0;
static double backend_g_fight_radius = 0.0;

static const double MAX_CAT_SPEED = 2.0;

static const int CAT_MOOD_CALM = 0;
static const int CAT_MOOD_HISSES = 1;
static const int CAT_MOOD_WANTS_TO_FIGHT = 2;


static void place_cats(void);

static void move_cats(void);

static void update_cats_mood(void);


CatState *backend_init(
    const size_t cat_count,
    const double map_width,
    const double map_height,
    const double fight_radius
) {
    void *state = calloc(cat_count, sizeof(CatState));

    if (state != NULL) {
        backend_g_state = state;
        backend_g_cat_count = cat_count;
        backend_g_map_width = map_width;
        backend_g_map_height = map_height;
        backend_g_fight_radius = fight_radius;

        place_cats();
        update_cats_mood();
    }

    return state;
}

void backend_update_state(void) {
    move_cats();
    update_cats_mood();
}

void backend_dispose(void) {
    free(backend_g_state);

    backend_g_state = NULL;
    backend_g_cat_count = 0;
    backend_g_map_width = 0.0;
    backend_g_map_height = 0.0;
    backend_g_fight_radius = 0.0;
}


// Internal

static void place_cats(void) {
    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];
        cat->x = backend_g_map_width * rand_ud();
        cat->y = backend_g_map_height * rand_ud();
    }
}

static void move_cats(void) {
    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];
        cat->x += MAX_CAT_SPEED * rand_d();
        cat->y += MAX_CAT_SPEED * rand_d();
    }
}

static void update_cats_mood(void) {
    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];
        cat->mood = CAT_MOOD_CALM;
    }

    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];

        if (cat->mood == CAT_MOOD_WANTS_TO_FIGHT) continue;

        for (size_t j = 0; j < backend_g_cat_count; j++) {
            if (i == j) continue;

            CatState *other_cat = &backend_g_state[j];

            const double dist = hypot(cat->x - other_cat->x, cat->y - other_cat->y);

            if (dist <= backend_g_fight_radius) {
                cat->mood = CAT_MOOD_WANTS_TO_FIGHT;
                other_cat->mood = CAT_MOOD_WANTS_TO_FIGHT;
                break;
            }
            if (cat->mood == CAT_MOOD_CALM && rand_ud() <= 1.0 / dist * dist) {
                cat->mood = CAT_MOOD_HISSES;
                if (other_cat->mood == CAT_MOOD_CALM) {
                    other_cat->mood = CAT_MOOD_HISSES;
                }
            }
        }
    }
}
