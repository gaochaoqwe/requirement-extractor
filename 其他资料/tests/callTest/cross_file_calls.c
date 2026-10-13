#include "utils.h"

// Function defined in this file calls functions defined in utils.c
int calculate(int value) {
    int s = square(value); // cross-file call
    int c = cube(value);   // cross-file call
    return s + c;
} 