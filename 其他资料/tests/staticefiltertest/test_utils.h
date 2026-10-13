/**
 * 测试工具头文件
 * 用于静态分析过滤工具测试
 */
#ifndef TEST_UTILS_H
#define TEST_UTILS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 常量定义
#define MAX_BUFFER_SIZE 1024
#define MAX_ARRAY_SIZE 100
#define TEST_STRING_LENGTH 50

// 测试结构体
typedef struct {
    int id;
    char name[TEST_STRING_LENGTH];
    float value;
    int *data_ptr;
} TestData;

// 函数声明
void print_test_header(const char *test_name);
void print_test_result(const char *test_name, int passed);
int validate_array_bounds(int index, int max_size);
void safe_string_copy(char *dest, const char *src, size_t dest_size);

// 内联函数
static inline void log_message(const char *msg) {
    printf("[LOG] %s\n", msg);
}

#endif // TEST_UTILS_H
