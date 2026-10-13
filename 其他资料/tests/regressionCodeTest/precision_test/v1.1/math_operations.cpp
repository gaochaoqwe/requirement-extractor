#include "math_operations.h"
#include <cmath>
#include <stdexcept>

// === 完全不变的函数（12个）===

// 函数1: 基础加法 - 完全相同
int add(int a, int b) {
    return a + b;
}

// 函数2: 基础减法 - 完全相同
int subtract(int a, int b) {
    return a - b;
}

// 函数3: 最小值函数 - 完全相同
int min_value(int a, int b) {
    return a < b ? a : b;
}

// 函数4: 最大值函数 - 完全相同
int max_value(int a, int b) {
    return a > b ? a : b;
}

// 函数5: 绝对值函数 - 完全相同
int abs_value(int x) {
    return x < 0 ? -x : x;
}

// 函数6: 平方函数 - 完全相同
double square(double x) {
    return x * x;
}

// 函数7: 立方函数 - 完全相同
double cube(double x) {
    return x * x * x;
}

// 函数8: 判断偶数 - 完全相同
bool is_even(int n) {
    return n % 2 == 0;
}

// 函数9: 判断奇数 - 完全相同
bool is_odd(int n) {
    return n % 2 != 0;
}

// 函数10: 符号函数 - 完全相同
int sign(int x) {
    if (x > 0) return 1;
    if (x < 0) return -1;
    return 0;
}

// 函数11: 交换函数 - 完全相同
void swap_values(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

// 函数12: 距离函数 - 完全相同
double distance_2d(double x1, double y1, double x2, double y2) {
    double dx = x2 - x1;
    double dy = y2 - y1;
    return sqrt(dx * dx + dy * dy);
}

// === 只有格式变化的函数（11个）===

// 函数13: 乘法 - 只有格式变化（缩进）
int multiply(int a, int b) {
        return a * b;  // 缩进变化
}

// 函数14: 除法 - 只有格式变化（空行）
double divide_double(double a, double b) {
    
    if (b == 0.0) return 0.0;
    
    return a / b;
}

// 函数15: 求余 - 只有格式变化（注释位置）
int modulo(int a, int b) {
    if (b == 0) return 0; // 内联注释
    return a % b;
}

// 函数16: 阶乘 - 变量名变化
int factorial(int num) {  // 参数名从n改为num
    if (num <= 1) return 1;
    return num * factorial(num - 1);
}

// 函数17: 斐波那契 - 只有格式变化
int fibonacci(int n) 
{  // 大括号换行
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// 函数18: 最大公约数 - 只有空格变化
int gcd(int a,int b) {  // 参数间空格变化
    while(b!=0) {  // 操作符间空格变化
        int temp=b;
        b=a%b;
        a=temp;
    }
    return a;
}

// 函数19: 最小公倍数 - 只有格式变化
int lcm(int a, int b) 
{
    return (a * b) / gcd(a, b);
}

// 函数20: 判断质数 - 只有注释变化
bool is_prime(int n) {
    // 检查是否为质数 - 添加了注释
    if (n < 2) return false;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

// 函数21: 数字反转 - 只有格式变化
int reverse_number(int n) 
{
    int result = 0;
    while (n > 0) 
    {
        result = result * 10 + n % 10;
        n /= 10;
    }
    return result;
}

// 函数22: 数位和 - 只有变量名变化
int digit_sum(int number) {  // 参数名从n改为number
    int sum = 0;
    while (number > 0) {
        sum += number % 10;
        number /= 10;
    }
    return sum;
}

// 函数23: 判断回文数 - 只有格式变化
bool is_palindrome(int n) {
    return n == reverse_number(n);  // 去掉多余空格
}

// === 轻微逻辑变化的函数（11个）===

// 函数24: 安全除法 - 添加了输入验证
int safe_divide(int a, int b) {
    // 添加了更多输入验证
    if (a == 0) return 0;
    if (b == 0) return 0;
    return a / b;
}

// 函数25: 幂运算 - 改进算法（使用标准库）
double power(double base, int exp) {
    // 使用标准库函数重写
    return std::pow(base, exp);
}

// 函数26: 平方根近似 - 改进精度
double sqrt_approx(double x) {
    if (x < 0) return 0;
    if (x == 0) return 0;  // 添加了边界检查
    return sqrt(x);
}

// 函数27: 角度转弧度 - 添加范围检查
double deg_to_rad(double degrees) {
    // 添加角度范围规范化
    while (degrees > 360) degrees -= 360;
    while (degrees < 0) degrees += 360;
    return degrees * M_PI / 180.0;
}

// 函数28: 弧度转角度 - 添加范围检查
double rad_to_deg(double radians) {
    // 添加弧度范围规范化
    while (radians > 2 * M_PI) radians -= 2 * M_PI;
    while (radians < 0) radians += 2 * M_PI;
    return radians * 180.0 / M_PI;
}

// 函数29: 限制值范围 - 改进边界处理
double clamp(double value, double min_val, double max_val) {
    // 添加参数有效性检查
    if (min_val > max_val) {
        double temp = min_val;
        min_val = max_val;
        max_val = temp;
    }
    if (value < min_val) return min_val;
    if (value > max_val) return max_val;
    return value;
}

// 函数30: 线性插值 - 添加边界检查
double lerp(double a, double b, double t) {
    // 添加t值范围检查
    if (t < 0.0) t = 0.0;
    if (t > 1.0) t = 1.0;
    return a + t * (b - a);
}

// 函数31: 数组求和 - 添加空指针检查
int array_sum(int* arr, int size) {
    if (arr == nullptr || size <= 0) return 0;  // 添加空指针检查
    int sum = 0;
    for (int i = 0; i < size; i++) {
        sum += arr[i];
    }
    return sum;
}

// 函数32: 数组最大值 - 添加边界检查
int array_max(int* arr, int size) {
    if (arr == nullptr || size <= 0) return 0;  // 添加空指针检查
    int max = arr[0];
    for (int i = 1; i < size; i++) {
        if (arr[i] > max) max = arr[i];
    }
    return max;
}

// 函数33: 数组最小值 - 添加边界检查
int array_min(int* arr, int size) {
    if (arr == nullptr || size <= 0) return 0;  // 添加空指针检查
    int min = arr[0];
    for (int i = 1; i < size; i++) {
        if (arr[i] < min) min = arr[i];
    }
    return min;
}

// 函数34: 计算平均值 - 改进精度处理
double average(int* arr, int size) {
    if (arr == nullptr || size <= 0) return 0.0;  // 添加空指针检查
    long long sum = 0;  // 使用long long避免溢出
    for (int i = 0; i < size; i++) {
        sum += arr[i];
    }
    return static_cast<double>(sum) / size;
}

// === 重大逻辑变化的函数（6个）===

// 函数35: 排序算法 - 从冒泡排序改为快速排序
void quick_sort(int* arr, int size) {  // 函数名也改了
    if (arr == nullptr || size <= 1) return;
    
    // 简化的快速排序实现
    std::sort(arr, arr + size);  // 使用标准库
}

// 函数36: 查找算法 - 从线性查找改为二分查找
int binary_search(int* arr, int size, int target) {  // 函数名改了
    if (arr == nullptr || size <= 0) return -1;
    
    int left = 0, right = size - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

// 函数37: 字符串长度 - 改为更高效的实现
int string_length(const char* str) {
    if (str == nullptr) return 0;  // 添加空指针检查
    
    // 使用指针算术代替循环计数
    const char* start = str;
    while (*str != '\0') str++;
    return static_cast<int>(str - start);
}

// 函数38: 字符串复制 - 添加安全检查
void string_copy(char* dest, const char* src) {
    if (dest == nullptr || src == nullptr) return;  // 安全检查
    
    // 添加长度限制
    int count = 0;
    const int MAX_LENGTH = 1000;
    while (src[count] != '\0' && count < MAX_LENGTH) {
        dest[count] = src[count];
        count++;
    }
    dest[count] = '\0';
}

// 函数39: 字符串比较 - 改进比较逻辑
int string_compare(const char* str1, const char* str2) {
    if (str1 == nullptr && str2 == nullptr) return 0;
    if (str1 == nullptr) return -1;
    if (str2 == nullptr) return 1;
    
    // 使用更高效的比较方式
    while (*str1 != '\0' && *str2 != '\0') {
        if (*str1 != *str2) {
            return *str1 - *str2;
        }
        str1++;
        str2++;
    }
    return *str1 - *str2;
}

// 函数40: 矩阵乘法 - 优化算法
void matrix_multiply(int a[][3], int b[][3], int result[][3]) {
    if (a == nullptr || b == nullptr || result == nullptr) return;
    
    // 优化的矩阵乘法（缓存友好）
    for (int i = 0; i < 3; i++) {
        for (int k = 0; k < 3; k++) {  // 改变循环顺序
            int temp = a[i][k];
            for (int j = 0; j < 3; j++) {
                result[i][j] += temp * b[k][j];
            }
        }
    }
}

// === 新增的函数（10个以上）===

// 函数51: 新增的高级数学函数
double advanced_sqrt(double x) {
    if (x < 0) throw std::invalid_argument("Negative input");
    return sqrt(x);
}

// 函数52: 新增的三角函数
double safe_sin(double x) {
    return sin(x);
}

// 函数53: 新增的对数函数
double safe_log(double x) {
    if (x <= 0) throw std::invalid_argument("Non-positive input");
    return log(x);
}

// 函数54: 新增的组合数计算
long long combination(int n, int r) {
    if (r > n || r < 0) return 0;
    if (r == 0 || r == n) return 1;
    
    long long result = 1;
    for (int i = 0; i < r; i++) {
        result = result * (n - i) / (i + 1);
    }
    return result;
}

// 函数55: 新增的排列数计算
long long permutation(int n, int r) {
    if (r > n || r < 0) return 0;
    
    long long result = 1;
    for (int i = n; i > n - r; i--) {
        result *= i;
    }
    return result;
}

// 函数56: 新增的最大公约数（欧几里得算法）
int gcd_euclidean(int a, int b) {
    return b == 0 ? a : gcd_euclidean(b, a % b);
}

// 函数57: 新增的快速幂运算
long long fast_power(long long base, long long exp, long long mod) {
    long long result = 1;
    while (exp > 0) {
        if (exp % 2 == 1) {
            result = (result * base) % mod;
        }
        base = (base * base) % mod;
        exp /= 2;
    }
    return result;
}

// 函数58: 新增的数值积分
double simpson_integration(double (*f)(double), double a, double b, int n) {
    if (f == nullptr || n <= 0) return 0.0;
    
    double h = (b - a) / n;
    double sum = f(a) + f(b);
    
    for (int i = 1; i < n; i++) {
        double x = a + i * h;
        sum += (i % 2 == 0 ? 2 : 4) * f(x);
    }
    
    return sum * h / 3.0;
}

// 函数59: 新增的随机数生成器
int random_int(int min, int max) {
    if (min > max) {
        int temp = min;
        min = max;
        max = temp;
    }
    return min + rand() % (max - min + 1);
}

// 函数60: 新增的统计函数
double standard_deviation(int* arr, int size) {
    if (arr == nullptr || size <= 1) return 0.0;
    
    double mean = average(arr, size);
    double sum_squares = 0.0;
    
    for (int i = 0; i < size; i++) {
        double diff = arr[i] - mean;
        sum_squares += diff * diff;
    }
    
    return sqrt(sum_squares / (size - 1));
}

// 注意：所有old_*函数都被删除了，不再包含在v1.1中 