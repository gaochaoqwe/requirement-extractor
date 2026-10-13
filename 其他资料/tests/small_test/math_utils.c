#include "math_utils.h"

int square(int x) {
    return x * x;
}

double sqrt_custom(double x) {
    double guess = x / 2.0;
    for (int i = 0; i < 10; i++) {
        guess = (guess + x / guess) / 2.0;
    }
    return guess;
}

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
} 