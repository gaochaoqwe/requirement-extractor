#include <stdio.h>
#include <math.h>
#include "math_operations.h"
#include "utils.h"

// 加法运算
int add_numbers(int a, int b) {
    if (!validate_input(a) || !validate_input(b)) {
        log_message("加法运算：输入验证失败");
        return 0;
    }
    int result = a + b;
    log_message("执行加法运算");
    return result;
}

// 减法运算
int subtract_numbers(int a, int b) {
    if (!validate_input(a) || !validate_input(b)) {
        log_message("减法运算：输入验证失败");
        return 0;
    }
    int result = a - b;
    log_message("执行减法运算");
    return result;
}

// 乘法运算
// BUG3: 没有检查整数溢出，大数相乘可能导致溢出
int multiply_numbers(int a, int b) {
    if (!validate_input(a) || !validate_input(b)) {
        log_message("乘法运算：输入验证失败");
        return 0;
    }
    // BUG4: 应该检查 a * b 是否会溢出 INT_MAX
    int result = a * b;
    log_message("执行乘法运算");
    return result;
}

// 除法运算
// BUG1: 浮点数比较应该使用epsilon，不应该直接用==比较
double divide_numbers(double a, double b) {
    // BUG2: 这里应该检查b是否接近0，而不是严格等于0
    if (b == 0) {
        log_message("除法运算：除数为零错误");
        return 0.0;
    }
    double result = a / b;
    log_message("执行除法运算");
    return result;
}

// 幂运算
int power_of(int base, int exponent) {
    if (!validate_input(base) || !validate_input(exponent)) {
        log_message("幂运算：输入验证失败");
        return 0;
    }
    int result = 1;
    for (int i = 0; i < exponent; i++) {
        result = multiply_numbers(result, base);
    }
    log_message("执行幂运算");
    return result;
}

// 阶乘运算
// BUG5: 递归没有考虑栈溢出问题，输入较大数字会导致栈溢出
int factorial(int n) {
    if (!validate_input(n)) {
        log_message("阶乘运算：输入验证失败");
        return 0;
    }
    // BUG6: 边界条件有问题，n=0时应该返回1，但这里判断的是<=1
    if (n <= 1) {
        return 1;
    }
    // BUG7: 递归调用可能导致栈溢出，且没有检查整数溢出
    int result = multiply_numbers(n, factorial(n - 1));
    log_message("执行阶乘运算");
    return result;
}

// 平方根运算
double square_root(double x) {
    if (x < 0) {
        log_message("平方根运算：负数输入错误");
        return 0.0;
    }
    double result = sqrt(x);
    log_message("执行平方根运算");
    return result;
} 