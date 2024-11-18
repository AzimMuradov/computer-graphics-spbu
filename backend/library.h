#include <stddef.h>

typedef struct PixelPosition {
    double x;
    double y;
} PixelPosition;

typedef struct Cat {
    double x;
    double y;
} Cat;

typedef struct CatState {
    PixelPosition pos;
    int mood;
    // mood:
    // 0 == calm
    // 1 == hisses
    // 2 == wants to fight
} CatState;

void backend_init(
    double fight_radius,
    double hiss_radius
);

int* update_states(size_t cat_count, Cat *cats, int window_width, int window_height, float scale);

void free_states(int *states);

