#include <stdlib.h>


/**
 * Generate random unsigned double in the range of `[0.0, 1.0]`.
 *
 * @returns By default: random double in `[0.0, 1.0]`,
 *          or if `TEST` defined: `0.0`.
 */
static double rand_ud(void) {
#ifndef TEST
    return (double) rand() / (double) RAND_MAX;
#else
    return 0.0;
#endif
}
