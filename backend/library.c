#include "library.h"

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

static CatState *backend_g_state = NULL;
static size_t backend_g_cat_count = 0;
static double backend_g_map_width = 0.0;
static double backend_g_map_height = 0.0;
static double backend_g_fight_radius = 0.0;

CatState *backend_init(
    const size_t cat_count,
    const double map_width,
    const double map_height,
    const double fight_radius
) {
    printf("cat_count = %zu\n", cat_count);
    printf("map_width = %f\n", map_width);
    printf("map_height = %f\n", map_height);
    printf("fight_radius = %f\n", fight_radius);

    void *state = calloc(cat_count, sizeof(CatState));

    if (state != NULL) {
        backend_g_state = state;
        backend_g_cat_count = cat_count;
        backend_g_map_width = map_width;
        backend_g_map_height = map_height;
        backend_g_fight_radius = fight_radius;
    }

    return state;
}

void backend_update_state(void) {
    // TODO : Main logic
    // Here we update `backend_g_state`
}

void backend_dispose(void) {
    free(backend_g_state);

    backend_g_state = NULL;
    backend_g_cat_count = 0;
    backend_g_map_width = 0.0;
    backend_g_map_height = 0.0;
    backend_g_fight_radius = 0.0;
}
