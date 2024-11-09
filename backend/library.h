#ifndef BACKEND_LIBRARY_H
#define BACKEND_LIBRARY_H

#include <stddef.h>

typedef struct CatState {
    double x;
    double y;
    // mood:
    // 0 == calm
    // 1 == hisses
    // 2 == wants to fight
    int mood;
} CatState;

CatState *setup_backend(
    size_t max_n,
    double map_width,
    double map_height,
    double fight_radius,
    double hiss_radius
);

void backend_update_state(void);

void teardown_backend(void);

#endif // BACKEND_LIBRARY_H
