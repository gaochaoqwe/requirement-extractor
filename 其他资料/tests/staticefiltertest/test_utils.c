/**
 * 测试工具实现文件
 */
#include "test_utils.h"

void print_test_header(const char *test_name) {
    printf("\n=== %s ===\n", test_name);
}

void print_test_result(const char *test_name, int passed) {
    printf("[%s] %s: %s\n", 
           passed ? "PASS" : "FAIL", 
           test_name, 
           passed ? "通过" : "失败");
}

int validate_array_bounds(int index, int max_size) {
    if (index < 0 || index >= max_size) {
        printf("警告：数组索引 %d 超出范围 [0, %d)\n", index, max_size);
        return 0;  // 无效
    }
    return 1;  // 有效
}

void safe_string_copy(char *dest, const char *src, size_t dest_size) {
    if (dest == NULL || src == NULL || dest_size == 0) {
        return;
    }
    
    strncpy(dest, src, dest_size - 1);
    dest[dest_size - 1] = '\0';  // 确保字符串结束
}

// 一些正常的工具函数
int calculate_sum(int *array, int size) {
    int sum = 0;
    
    if (array == NULL || size <= 0) {
        return 0;
    }
    
    for (int i = 0; i < size; i++) {
        sum += array[i];
    }
    
    return sum;
}

void initialize_test_data(TestData *data, int id, const char *name, float value) {
    if (data == NULL) {
        return;
    }
    
    data->id = id;
    safe_string_copy(data->name, name ? name : "Unknown", sizeof(data->name));
    data->value = value;
    data->data_ptr = NULL;
}
