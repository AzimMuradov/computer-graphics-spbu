#ifndef LIBRARY_H
#define LIBRARY_H


#include <stddef.h>


/**
 * Cat position in the OpenGL coordinate system.
 */
typedef struct OpenGlPosition {
    double x;
    double y;
} OpenGlPosition;


/**
 * Set global configuration.
 *
 * It's important to note that `fight_radius` must be less than `hiss_radius`.
 *
 * @param fight_radius The radius between any two cats at which they always start fighting.
 * @param hiss_radius The radius between any two cats at which they may start hissing.
 */
void drunk_cats_configure(
    double fight_radius,
    double hiss_radius
);

/**
 * Calculate cat states.
 *
 * For example, if we have two cats (named *Alisa* and *Bob*),
 * depending on the radius **in the plain coordinate system** between them (named *R*):
 * - if `R in [0, fight_radius]`,
 *   then Alisa, Bob - both in the fighting state;
 * - if `R in (fight_radius, hiss_radius]`,
 *   then Alisa, Bob - each individually have `probability = Pr(Const / R^2)` to be in the hissing state.
 *
 * @param cat_count Number of cat positions given.
 * @param cat_positions Array of cat positions in the OpenGL coordinate system.
 * @param window_width Window width, must be positive.
 * @param window_height Window height, must be positive.
 * @param scale Window scale (e.g. 1.0 - no scale, 2.0 - two times scale), must be positive.
 *
 * @returns Cat states with the following semantics:
 *          - 0 - calm;
 *          - 1 - hisses;
 *          - 2 - wants to fight.
 */
int *drunk_cats_calculate_states(
    size_t cat_count,
    const OpenGlPosition *cat_positions,
    unsigned int window_width,
    unsigned int window_height,
    float scale
);

/**
 * Free allocated memory for the given states.
 *
 * @param states Pointer to the array of states.
 */
void drunk_cats_free_states(int *states);


#endif // LIBRARY_H
