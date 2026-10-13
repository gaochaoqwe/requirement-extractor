#ifndef TEST_MACROS_ARRAYS_H
#define TEST_MACROS_ARRAYS_H

// 简单宏定义
#define MAX_SIZE 1024
#define MIN_VALUE 0
#define DEFAULT_NAME "unknown"

// 带参数的宏定义
#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define DEBUG_PRINT(fmt, ...) printf("[DEBUG] " fmt "\n", ##__VA_ARGS__)

// 条件编译宏
#ifdef DEBUG
#define LOG_LEVEL 3
#else
#define LOG_LEVEL 1
#endif

// 复杂宏定义
#define INIT_STRUCT(name, size) \
    struct name { \
        int data[size]; \
        int count; \
    }

// 全局数组声明
extern int global_array[MAX_SIZE];
extern char global_buffer[256];
extern float global_matrix[10][10];
extern const char* global_strings[100];

// 静态数组
static int static_array[50] = {0};
static char static_buffer[] = "default";

// 多维数组
extern int multi_array[5][10][15];

#endif // TEST_MACROS_ARRAYS_H 