#include <stdio.h>
#include "math_utils.h"

// 调用其他文件中的三个函数
void perform_calculations(int x) {
    int squared = square(x);           // 调用math_utils.c中的square函数
    double root = sqrt_custom(x);      // 调用math_utils.c中的sqrt_custom函数
    int fact = factorial(x);           // 调用math_utils.c中的factorial函数
    
    printf("Square: %d\n", squared);
    printf("Square root: %f\n", root);
    printf("Factorial: %d\n", fact);
} 