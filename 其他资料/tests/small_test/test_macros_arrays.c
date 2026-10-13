#include "test_macros_arrays.h"
#include <stdio.h>
#include <string.h>

// 在当前文件中定义的宏
#define LOCAL_MACRO 42
#define BUFFER_SIZE 128
#define PROCESS_DATA(x) ((x) * 2 + 1)

// 全局数组定义
int global_array[MAX_SIZE];
char global_buffer[256];
float global_matrix[10][10];
const char* global_strings[100];
int multi_array[5][10][15];

// 当前文件的静态数组
static double local_static_array[BUFFER_SIZE];
static char local_buffer[MAX_SIZE];

// 测试函数1：使用各种宏定义
void test_macro_usage() {
    int size = MAX_SIZE;  // 使用简单宏
    int min = MIN_VALUE;  // 使用简单宏
    char name[64];
    strcpy(name, DEFAULT_NAME);  // 使用字符串宏
    
    int result = SQUARE(5);  // 使用函数式宏
    int max_val = MAX(10, 20);  // 使用函数式宏
    
    DEBUG_PRINT("size=%d, min=%d, result=%d", size, min, result);  // 使用变参宏
    
    int local_val = LOCAL_MACRO;  // 使用本文件宏
    int processed = PROCESS_DATA(local_val);  // 使用本文件函数式宏
}

// 测试函数2：使用各种数组
void test_array_usage() {
    // 使用全局数组
    global_array[0] = 100;
    global_buffer[0] = 'A';
    global_matrix[0][0] = 3.14f;
    global_strings[0] = "first";
    multi_array[0][0][0] = 999;
    
    // 使用静态数组
    static_array[0] = 200;
    strcpy(static_buffer, "modified");
    
    // 使用本文件静态数组
    local_static_array[0] = 2.718;
    local_buffer[0] = 'B';
    
    // 局部数组（不应该被识别为全局）
    int local_array[10];
    char local_str[BUFFER_SIZE];  // 使用宏定义大小
    
    local_array[0] = 1;
    local_str[0] = 'C';
}

// 测试函数3：混合使用宏和数组
void test_mixed_usage() {
    // 使用宏作为数组索引
    int index = MAX_SIZE - 1;
    global_array[index] = SQUARE(LOCAL_MACRO);
    
    // 使用宏作为循环边界
    for (int i = MIN_VALUE; i < MAX_SIZE && i < 10; i++) {
        local_static_array[i] = PROCESS_DATA(i);
    }
    
    // 条件编译宏的使用
    if (LOG_LEVEL > 2) {
        DEBUG_PRINT("Debug mode active");
    }
}

// 测试函数4：只有局部变量，不使用任何全局宏和数组
void test_local_only() {
    #define TEMP_MACRO 999  // 局部宏定义
    int local_array[50];
    char local_buffer[100];
    
    local_array[0] = TEMP_MACRO;
    local_buffer[0] = 'X';
    
    #undef TEMP_MACRO
} 