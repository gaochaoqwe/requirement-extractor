/**
 * CWE测试用例文件 - 增强版
 * 包含10个CWE规则相关的问题（3个真实问题，7个误报）
 * 这些问题需要跨文件分析和深入的代码上下文理解才能准确判断
 */

#include "cwe_utils.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

// ==================== 问题1: S_15_01 变量未初始化使用（真实问题）====================
// 文件: cwe_test_cases.c, 行号: 19
// 这是一个真实的bug：指针未初始化就使用
void test_uninitialized_variable() {
    int *ptr;  // 未初始化的指针
    // 真实问题：直接使用未初始化的指针会导致未定义行为
    *ptr = 100;  // 行号: 19 - 真实问题
    printf("Value: %d\n", *ptr);
}

// ==================== 问题2: S_21_01 一般的数组越界（误报）====================
// 文件: cwe_test_cases.c, 行号: 31
// 这看起来像数组越界，但实际上是安全的
void test_array_bounds_check() {
    int numbers[10];
    int user_input = 5;  // 假设来自用户输入
    
    // 误报：虽然看起来可能越界，但有完整的边界检查
    if (user_input >= 0 && user_input < 10) {
        numbers[user_input] = 42;  // 行号: 31 - 误报：索引已被验证
        printf("Set numbers[%d] = %d\n", user_input, numbers[user_input]);
    }
}

// ==================== 问题3: S_41_03 一般的整数溢出（真实问题）====================
// 文件: cwe_test_cases.c, 行号: 43
// 整数溢出导致的缓冲区分配错误
void* allocate_buffer_with_overflow(int count, int size) {
    // 真实问题：没有检查整数溢出
    size_t total = count * size;  // 行号: 43 - 真实问题：乘法可能溢出
    return malloc(total);
}

void test_integer_overflow() {
    int item_count = 0x40000000;  // 很大的数字
    int item_size = 8;
    void *buffer = allocate_buffer_with_overflow(item_count, item_size);
    if (buffer) {
        free(buffer);
    }
}

// ==================== 问题4: S_30_06 指针解引用前未判空（误报）====================
// 文件: cwe_test_cases.c, 行号: 65
// 这里看起来没有判空，但通过跨文件分析可以看出是安全的
void test_pointer_usage_with_cross_file() {
    int user_id = 1;
    // 误报：虽然没有直接判空，但跨文件分析显示get_user_by_id对有效ID总是返回非NULL
    // 因为user_id=1在init_system_config中已初始化
    char *username = get_user_by_id(user_id);
    printf("Username: %s\n", username);  // 行号: 65 - 误报：实际是安全的
}

// ==================== 问题5: S_05_01 使用释放后的内存（真实问题）====================
// 文件: cwe_test_cases.c, 行号: 77
// 经典的use-after-free问题
void test_use_after_free() {
    char *data = (char*)malloc(128);
    if (data) {
        strcpy(data, "Important data");
        printf("Data: %s\n", data);
        free(data);
        // 真实问题：访问已释放的内存
        printf("Freed data: %s\n", data);  // 行号: 77 - 真实问题
    }
}

// ==================== 问题6: S_34_04 文件句柄使用后未释放（误报）====================
// 文件: cwe_test_cases.c, 行号: 96
// 看起来像资源泄漏，但实际在所有路径上都正确关闭了
FILE* open_config_file(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (fp == NULL) {
        perror("Failed to open file");
    }
    return fp;
}

void test_file_handle_management() {
    FILE *fp = open_config_file("config.txt");  // 行号: 96 - 误报
    if (fp != NULL) {
        char buffer[256];
        if (fgets(buffer, sizeof(buffer), fp) != NULL) {
            printf("Config: %s", buffer);
        }
        fclose(fp);  // 正确关闭
    }
    // 误报：文件句柄在所有路径上都被正确关闭
}

// ==================== 问题7: S_27_07 污染数据用于格式化字符串（误报）====================
// 文件: cwe_test_cases.c, 行号: 119
// 看起来像格式化字符串漏洞，但输入已被净化
void sanitize_input(char *output, const char *input, size_t max_len) {
    // 移除格式化字符
    size_t j = 0;
    for (size_t i = 0; input[i] && j < max_len - 1; i++) {
        if (input[i] != '%') {
            output[j++] = input[i];
        }
    }
    output[j] = '\0';
}

void test_format_string_with_sanitized_input(const char *user_input) {
    char clean_input[256];
    sanitize_input(clean_input, user_input, sizeof(clean_input));
    // 误报：输入已被净化，移除了所有%字符
    printf(clean_input);  // 行号: 119 - 误报：输入已净化
    printf("\n");
}

// ==================== 问题8: S_21_10 污染数据用于数组下标（误报）====================
// 文件: cwe_test_cases.c, 行号: 144
// 看起来用户输入直接作为数组索引，但实际经过了验证
void test_array_access_with_validation(int user_index) {
    int data[20];
    
    // 初始化数组
    for (int i = 0; i < 20; i++) {
        data[i] = i * 10;
    }
    
    // 误报：虽然user_index来自外部，但经过了严格的边界检查
    if (user_index >= 0 && user_index < 20) {
        int value = data[user_index];  // 行号: 144 - 误报：已验证边界
        printf("Data at index %d: %d\n", user_index, value);
    }
}

// ==================== 问题9: S_23_03 函数循环调用（误报）====================
// 文件: cwe_test_cases.c, 行号: 164
// 看起来像递归调用，但实际上有明确的终止条件
int fibonacci_with_limit(int n, int depth) {
    // 误报：虽然是递归，但有深度限制，不会无限递归
    if (depth > 50 || n <= 1) {  // 深度限制防止栈溢出
        return n;
    }
    return fibonacci_with_limit(n - 1, depth + 1) + 
           fibonacci_with_limit(n - 2, depth + 1);  // 行号: 164 - 误报
}

void test_controlled_recursion() {
    int result = fibonacci_with_limit(10, 0);
    printf("Fibonacci result: %d\n", result);
}

// ==================== 问题10: S_06_01 分配内存未释放（误报）====================
// 文件: cwe_test_cases.c, 行号: 186
// 看起来像内存泄漏，但内存管理在调用者处理
char* create_user_message(const char *username) {
    char *message = (char*)malloc(256);  // 行号: 186 - 误报
    if (message) {
        snprintf(message, 256, "Welcome, %s!", username);
    }
    return message;  // 调用者负责释放
}

void test_memory_management_by_caller() {
    char *msg = create_user_message("Alice");
    if (msg) {
        printf("%s\n", msg);
        free(msg);  // 调用者正确释放了内存
    }
    // 误报：内存由调用者管理，这是常见的设计模式
}

// 主测试函数
int main() {
    printf("=== CWE Enhanced Test Cases ===\n\n");
    
    // 初始化系统
    init_system_config();
    
    printf("Test 1: Uninitialized Variable (REAL BUG)\n");
    // test_uninitialized_variable();  // 会崩溃 - 真实问题
    printf("Skipped (would crash)\n\n");
    
    printf("Test 2: Array Bounds Check (FALSE POSITIVE)\n");
    test_array_bounds_check();
    printf("\n");
    
    printf("Test 3: Integer Overflow (REAL BUG)\n");
    // test_integer_overflow();  // 真实问题
    printf("Skipped (would cause memory issues)\n\n");
    
    printf("Test 4: Pointer Usage Cross-File (FALSE POSITIVE)\n");
    test_pointer_usage_with_cross_file();
    printf("\n");
    
    printf("Test 5: Use After Free (REAL BUG)\n");
    // test_use_after_free();  // 真实问题
    printf("Skipped (would crash)\n\n");
    
    printf("Test 6: File Handle Management (FALSE POSITIVE)\n");
    test_file_handle_management();
    printf("\n");
    
    printf("Test 7: Format String with Sanitized Input (FALSE POSITIVE)\n");
    test_format_string_with_sanitized_input("Hello %s %d");
    printf("\n");
    
    printf("Test 8: Array Access with Validation (FALSE POSITIVE)\n");
    test_array_access_with_validation(10);
    printf("\n");
    
    printf("Test 9: Controlled Recursion (FALSE POSITIVE)\n");
    test_controlled_recursion();
    printf("\n");
    
    printf("Test 10: Memory Management by Caller (FALSE POSITIVE)\n");
    test_memory_management_by_caller();
    printf("\n");
    
    printf("=== All Tests Complete ===\n");
    return 0;
}
