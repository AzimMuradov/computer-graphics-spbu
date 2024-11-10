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

CatState *backend_init(
    size_t cat_count,
    double map_width,
    double map_height,
    double fight_radius
);

void backend_update_state(void);

void backend_dispose(void);


#endif // BACKEND_LIBRARY_H
