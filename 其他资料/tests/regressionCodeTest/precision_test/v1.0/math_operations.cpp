#include "math_operations.h"
#include <cmath>

// === 完全不变的函数（10个以上）- 应该被识别为unchanged ===

// 函数1: 基础加法
int add(int a, int b) {
    return a + b;
}

// 函数2: 基础减法
int subtract(int a, int b) {
    return a - b;
}

// 函数3: 最小值函数
int min_value(int a, int b) {
    return a < b ? a : b;
}

// 函数4: 最大值函数
int max_value(int a, int b) {
    return a > b ? a : b;
}

// 函数5: 绝对值函数
int abs_value(int x) {
    return x < 0 ? -x : x;
}

// 函数6: 平方函数
double square(double x) {
    return x * x;
}

// 函数7: 立方函数
double cube(double x) {
    return x * x * x;
}

// 函数8: 判断偶数
bool is_even(int n) {
    return n % 2 == 0;
}

// 函数9: 判断奇数
bool is_odd(int n) {
    return n % 2 != 0;
}

// 函数10: 符号函数
int sign(int x) {
    if (x > 0) return 1;
    if (x < 0) return -1;
    return 0;
}

// 函数11: 交换函数
void swap_values(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

// 函数12: 距离函数
double distance_2d(double x1, double y1, double x2, double y2) {
    double dx = x2 - x1;
    double dy = y2 - y1;
    return sqrt(dx * dx + dy * dy);
}

// === 只有格式变化的函数（10个以上）- 应该被识别为unchanged ===

// 函数13: 乘法（将有格式变化）
int multiply(int a, int b) {
    return a * b;
}

// 函数14: 除法（将有格式变化）
double divide_double(double a, double b) {
    if (b == 0.0) return 0.0;
    return a / b;
}

// 函数15: 求余（将有格式变化）
int modulo(int a, int b) {
    if (b == 0) return 0;
    return a % b;
}

// 函数16: 阶乘（将有格式变化）
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

// 函数17: 斐波那契（将有格式变化）
int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// 函数18: 最大公约数（将有格式变化）
int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

// 函数19: 最小公倍数（将有格式变化）
int lcm(int a, int b) {
    return (a * b) / gcd(a, b);
}

// 函数20: 判断质数（将有格式变化）
bool is_prime(int n) {
    if (n < 2) return false;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

// 函数21: 数字反转（将有格式变化）
int reverse_number(int n) {
    int result = 0;
    while (n > 0) {
        result = result * 10 + n % 10;
        n /= 10;
    }
    return result;
}

// 函数22: 数位和（将有格式变化）
int digit_sum(int n) {
    int sum = 0;
    while (n > 0) {
        sum += n % 10;
        n /= 10;
    }
    return sum;
}

// 函数23: 判断回文数（将有格式变化）
bool is_palindrome(int n) {
    return n == reverse_number(n);
}

// === 轻微逻辑变化的函数（10个以上）- 应该被识别为modified ===

// 函数24: 安全除法（将添加输入验证）
int safe_divide(int a, int b) {
    if (b == 0) return 0;
    return a / b;
}

// 函数25: 幂运算（将改进算法）
double power(double base, int exp) {
    if (exp == 0) return 1.0;
    double result = 1.0;
    for (int i = 0; i < exp; i++) {
        result *= base;
    }
    return result;
}

// 函数26: 平方根近似（将改进精度）
double sqrt_approx(double x) {
    if (x < 0) return 0;
    return sqrt(x);
}

// 函数27: 角度转弧度（将添加范围检查）
double deg_to_rad(double degrees) {
    return degrees * M_PI / 180.0;
}

// 函数28: 弧度转角度（将添加范围检查）
double rad_to_deg(double radians) {
    return radians * 180.0 / M_PI;
}

// 函数29: 限制值范围（将改进边界处理）
double clamp(double value, double min_val, double max_val) {
    if (value < min_val) return min_val;
    if (value > max_val) return max_val;
    return value;
}

// 函数30: 线性插值（将添加边界检查）
double lerp(double a, double b, double t) {
    return a + t * (b - a);
}

// 函数31: 数组求和（将添加空指针检查）
int array_sum(int* arr, int size) {
    int sum = 0;
    for (int i = 0; i < size; i++) {
        sum += arr[i];
    }
    return sum;
}

// 函数32: 数组最大值（将添加边界检查）
int array_max(int* arr, int size) {
    if (size <= 0) return 0;
    int max = arr[0];
    for (int i = 1; i < size; i++) {
        if (arr[i] > max) max = arr[i];
    }
    return max;
}

// 函数33: 数组最小值（将添加边界检查）
int array_min(int* arr, int size) {
    if (size <= 0) return 0;
    int min = arr[0];
    for (int i = 1; i < size; i++) {
        if (arr[i] < min) min = arr[i];
    }
    return min;
}

// 函数34: 计算平均值（将改进精度处理）
double average(int* arr, int size) {
    if (size <= 0) return 0.0;
    return (double)array_sum(arr, size) / size;
}

// === 重大逻辑变化的函数（10个以上）- 应该被识别为modified ===

// 函数35: 排序算法（将从冒泡排序改为快速排序）
void bubble_sort(int* arr, int size) {
    for (int i = 0; i < size - 1; i++) {
        for (int j = 0; j < size - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                swap_values(&arr[j], &arr[j + 1]);
            }
        }
    }
}

// 函数36: 查找算法（将从线性查找改为二分查找）
int linear_search(int* arr, int size, int target) {
    for (int i = 0; i < size; i++) {
        if (arr[i] == target) return i;
    }
    return -1;
}

// 函数37: 字符串长度（将改为更高效的实现）
int string_length(const char* str) {
    int len = 0;
    while (str[len] != '\0') {
        len++;
    }
    return len;
}

// 函数38: 字符串复制（将添加安全检查）
void string_copy(char* dest, const char* src) {
    int i = 0;
    while (src[i] != '\0') {
        dest[i] = src[i];
        i++;
    }
    dest[i] = '\0';
}

// 函数39: 字符串比较（将改进比较逻辑）
int string_compare(const char* str1, const char* str2) {
    int i = 0;
    while (str1[i] != '\0' && str2[i] != '\0') {
        if (str1[i] != str2[i]) {
            return str1[i] - str2[i];
        }
        i++;
    }
    return str1[i] - str2[i];
}

// 函数40: 矩阵乘法（将优化算法）
void matrix_multiply(int a[][3], int b[][3], int result[][3]) {
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            result[i][j] = 0;
            for (int k = 0; k < 3; k++) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
}

// === 将被删除的函数（10个以上）- 应该被识别为deleted ===

// 函数41: 旧的计算器函数
int old_calculator(int a, int b, char op) {
    switch (op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return b != 0 ? a / b : 0;
        default: return 0;
    }
}

// 函数42: 废弃的随机数生成器
int old_random(int seed) {
    static int state = 1;
    if (seed != 0) state = seed;
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state;
}

// 函数43: 旧的日期计算
int days_in_month_old(int month, int year) {
    int days[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (month == 2 && year % 4 == 0) return 29;
    return days[month - 1];
}

// 函数44: 废弃的温度转换
double celsius_to_fahrenheit_old(double celsius) {
    return celsius * 9.0 / 5.0 + 32.0;
}

// 函数45: 旧的文件大小计算
long file_size_old(const char* filename) {
    return 0;  // 简化实现
}

// 函数46: 废弃的内存分配器
void* old_malloc(size_t size) {
    return malloc(size);
}

// 函数47: 旧的错误处理
void old_error_handler(int error_code) {
    printf("Error: %d\n", error_code);
}

// 函数48: 废弃的日志函数
void old_log(const char* message) {
    printf("LOG: %s\n", message);
}

// 函数49: 旧的配置读取
int old_read_config(const char* key) {
    return 0;  // 简化实现
}

// 函数50: 废弃的网络函数
int old_send_data(const char* data) {
    return 0;  // 简化实现
} 