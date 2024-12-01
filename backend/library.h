#ifndef LIBRARY_H
#define LIBRARY_H


#include <stddef.h>


typedef struct Position {
    double x;
    double y;
} Position;


void drunk_cats_configure(
    double fight_radius,
    double hiss_radius
);

// state:
// 0 == calm
// 1 == hisses
// 2 == wants to fight
int *drunk_cats_calculate_states(
    size_t cat_count,
    const Position *cat_positions,
    int window_width,
    int window_height,
    float scale
);

void drunk_cats_free_states(int *states);


#endif // LIBRARY_H
