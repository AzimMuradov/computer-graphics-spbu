#include <stdlib.h>


static double rand_d(void) {
    return (double) (rand() - RAND_MAX / 2) / (double) (RAND_MAX / 2);
}

static double rand_ud(void) {
    return (double) rand() / (double) RAND_MAX;
}
