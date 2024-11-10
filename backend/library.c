#include "library.h"

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

static CatState *backend_g_state = NULL;

CatState *setup_backend(
    const size_t cat_count,
    const double map_width,
    const double map_height,
    const double fight_radius,
    const double hiss_radius
) {
    printf("max_n = %zu\n", cat_count);
    printf("map_width = %f\n", map_width);
    printf("map_height = %f\n", map_height);
    printf("fight_radius = %f\n", fight_radius);
    printf("hiss_radius = %f\n", hiss_radius);

    backend_g_state = calloc(cat_count, sizeof(CatState));

    return backend_g_state;
}

void backend_update_state(void) {
    // TODO : Main logic
    // Here we update `backend_g_state`
}

void teardown_backend(void) {
    free(backend_g_state);
    backend_g_state = NULL;
}
