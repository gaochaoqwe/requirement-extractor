#ifndef MATH_OPERATIONS_H
#define MATH_OPERATIONS_H

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <algorithm>

// === 完全不变的函数（12个）===
int add(int a, int b);
int subtract(int a, int b);
int min_value(int a, int b);
int max_value(int a, int b);
int abs_value(int x);
double square(double x);
double cube(double x);
bool is_even(int n);
bool is_odd(int n);
int sign(int x);
void swap_values(int* a, int* b);
double distance_2d(double x1, double y1, double x2, double y2);

// === 只有格式变化的函数（11个）===
int multiply(int a, int b);
double divide_double(double a, double b);
int modulo(int a, int b);
int factorial(int num);  // 参数名变化
int fibonacci(int n);
int gcd(int a, int b);
int lcm(int a, int b);
bool is_prime(int n);
int reverse_number(int n);
int digit_sum(int number);  // 参数名变化
bool is_palindrome(int n);

// === 轻微逻辑变化的函数（11个）===
int safe_divide(int a, int b);
double power(double base, int exp);
double sqrt_approx(double x);
double deg_to_rad(double degrees);
double rad_to_deg(double radians);
double clamp(double value, double min_val, double max_val);
double lerp(double a, double b, double t);
int array_sum(int* arr, int size);
int array_max(int* arr, int size);
int array_min(int* arr, int size);
double average(int* arr, int size);

// === 重大逻辑变化的函数（6个）===
void quick_sort(int* arr, int size);  // 函数名从bubble_sort改为quick_sort
int binary_search(int* arr, int size, int target);  // 函数名从linear_search改为binary_search
int string_length(const char* str);
void string_copy(char* dest, const char* src);
int string_compare(const char* str1, const char* str2);
void matrix_multiply(int a[][3], int b[][3], int result[][3]);

// === 新增的函数（10个）===
double advanced_sqrt(double x);
double safe_sin(double x);
double safe_log(double x);
long long combination(int n, int r);
long long permutation(int n, int r);
int gcd_euclidean(int a, int b);
long long fast_power(long long base, long long exp, long long mod);
double simpson_integration(double (*f)(double), double a, double b, int n);
int random_int(int min, int max);
double standard_deviation(int* arr, int size);

// 注意：所有old_*函数都被删除了

#endif // MATH_OPERATIONS_H 