#include <stdio.h>

// 被调用的四个函数
int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int multiply(int a, int b) {
    return a * b;
}

int divide(int a, int b) {
    if (b != 0) {
        return a / b;
    }
    return 0;
}

// 调用其他四个函数的主函数
int calculate_all(int x, int y) {
    int result1 = add(x, y);        // 调用add函数
    int result2 = subtract(x, y);   // 调用subtract函数
    int result3 = multiply(x, y);   // 调用multiply函数
    int result4 = divide(x, y);     // 调用divide函数
    
    return result1 + result2 + result3 + result4;
} 