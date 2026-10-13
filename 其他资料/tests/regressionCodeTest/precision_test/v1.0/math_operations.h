#ifndef MATH_OPERATIONS_H
#define MATH_OPERATIONS_H

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

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
int factorial(int n);
int fibonacci(int n);
int gcd(int a, int b);
int lcm(int a, int b);
bool is_prime(int n);
int reverse_number(int n);
int digit_sum(int n);
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
void bubble_sort(int* arr, int size);
int linear_search(int* arr, int size, int target);
int string_length(const char* str);
void string_copy(char* dest, const char* src);
int string_compare(const char* str1, const char* str2);
void matrix_multiply(int a[][3], int b[][3], int result[][3]);

// === 将被删除的函数（10个）===
int old_calculator(int a, int b, char op);
int old_random(int seed);
int days_in_month_old(int month, int year);
double celsius_to_fahrenheit_old(double celsius);
long file_size_old(const char* filename);
void* old_malloc(size_t size);
void old_error_handler(int error_code);
void old_log(const char* message);
int old_read_config(const char* key);
int old_send_data(const char* data);

#endif // MATH_OPERATIONS_H 