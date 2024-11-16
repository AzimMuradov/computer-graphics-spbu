#include "library.h"

#include <math.h>
#include <stddef.h>
#include <stdlib.h>

#include "internal/random.c"

#define USE_LIST_NODE_ALLOCATOR
#include "third-party/kdtree/kdtree.c"


static CatState *backend_g_state = NULL;
static size_t backend_g_cat_count = 0;
static double backend_g_cat_speed = 0.0;
static double backend_g_map_width = 0.0;
static double backend_g_map_height = 0.0;
static double backend_g_fight_radius = 0.0;
static double backend_g_hiss_radius = 0.0;

static const int CAT_MOOD_CALM = 0;
static const int CAT_MOOD_HISSES = 1;
static const int CAT_MOOD_WANTS_TO_FIGHT = 2;


static void place_cats(void);

static void move_cats(void);

static void update_cats_mood(void);


CatState *backend_init(
    const size_t cat_count,
    const double cat_speed,
    const double map_width,
    const double map_height,
    const double fight_radius,
    const double hiss_radius
) {
    void *state = calloc(cat_count, sizeof(CatState));

    if (state != NULL) {
        backend_g_state = state;
        backend_g_cat_count = cat_count;
        backend_g_cat_speed = cat_speed;
        backend_g_map_width = map_width;
        backend_g_map_height = map_height;
        backend_g_fight_radius = fight_radius;
        backend_g_hiss_radius = hiss_radius;

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
    backend_g_cat_speed = 0.0;
    backend_g_map_width = 0.0;
    backend_g_map_height = 0.0;
    backend_g_fight_radius = 0.0;
    backend_g_hiss_radius = 0.0;
}


// Internal

static void place_cats(void) {
    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];
        cat->x = (3 * backend_g_map_width) * rand_ud() - backend_g_map_width;
        cat->y = (3 * backend_g_map_height) * rand_ud() - backend_g_map_height;
    }
}

static void move_cats(void) {
    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];
        cat->x += backend_g_cat_speed * rand_d();
        cat->y += backend_g_cat_speed * rand_d();
    }
}

static void update_cats_mood(void) {
    // Clear mood data

    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];
        cat->mood = CAT_MOOD_CALM;
    }


    // Recalculate mood data

    struct kdtree *tree = kd_create(2);

    // Populate kd_tree
    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];
        const double pos[2] = {cat->x, cat->y};
        kd_insert(tree, pos, cat);
    }

    // Calculate "wants to fight" mood
    for (size_t i = 0; i < backend_g_cat_count; i++) {
        const CatState *cat = &backend_g_state[i];

        if (cat->mood == CAT_MOOD_WANTS_TO_FIGHT) continue;

        const double pos[2] = {cat->x, cat->y};

        struct kdres *fight_cats = kd_nearest_range(tree, pos, backend_g_fight_radius);
        if (fight_cats == NULL) exit(1);

        if (kd_res_size(fight_cats) > 1) {
            for (; !kd_res_end(fight_cats); kd_res_next(fight_cats)) {
                CatState *fight_cat = kd_res_item_data(fight_cats);
                fight_cat->mood = CAT_MOOD_WANTS_TO_FIGHT;
            }
        }
        kd_res_free(fight_cats);
    }

    // Calculate "hisses" mood
    for (size_t i = 0; i < backend_g_cat_count; i++) {
        CatState *cat = &backend_g_state[i];

        if (cat->mood == CAT_MOOD_WANTS_TO_FIGHT) continue;

        const double pos[2] = {cat->x, cat->y};

        struct kdres *cats = kd_nearest_range(tree, pos, backend_g_hiss_radius);
        if (cats == NULL) exit(1);

        for (; !kd_res_end(cats); kd_res_next(cats)) {
            const CatState *other_cat = kd_res_item_data(cats);
            if (cat == other_cat) continue;
            const double dist = hypot(cat->x - other_cat->x, cat->y - other_cat->y);
            if (rand_ud() <= (backend_g_fight_radius * backend_g_fight_radius) / (dist * dist)) {
                cat->mood = CAT_MOOD_HISSES;
                break;
            }
        }
        kd_res_free(cats);
    }

    kd_free(tree);
}
