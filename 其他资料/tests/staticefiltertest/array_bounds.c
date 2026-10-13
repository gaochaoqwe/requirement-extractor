/**
 * 测试文件：数组越界问题
 * 对应规则：GJB_R_01_06_08 - 数组禁止越界使用
 */
#include <stdio.h>
#include <stdlib.h>

#define ARRAY_SIZE 10

// 正常的数组操作函数
void normal_array_access() {
    int arr[ARRAY_SIZE];
    int i;
    
    // 正常初始化
    for (i = 0; i < ARRAY_SIZE; i++) {
        arr[i] = i * 2;
    }
    
    // 正常访问
    printf("Array element 5: %d\n", arr[5]);
}

// 存在数组越界问题的函数
void problematic_array_access() {
    int buffer[5];
    int i;
    
    // 初始化数组
    for (i = 0; i < 5; i++) {
        buffer[i] = i;
    }
    
    // 问题1：数组越界写入 - 这里故意越界访问
    buffer[5] = 100;  // 越界！数组索引应该是0-4
    
    // 问题2：数组越界读取
    printf("Invalid access: %d\n", buffer[6]);  // 越界！
    
    // 问题3：循环中的越界
    for (i = 0; i <= 5; i++) {  // 应该是 i < 5
        buffer[i] = i * 10;  // 当i=5时越界
    }
}

// 动态数组越界问题
void dynamic_array_bounds() {
    int *dynamic_arr = (int*)malloc(8 * sizeof(int));
    
    if (dynamic_arr != NULL) {
        // 正常访问
        for (int i = 0; i < 8; i++) {
            dynamic_arr[i] = i;
        }
        
        // 越界访问 - 分配了8个元素，有效索引是0-7
        dynamic_arr[8] = 999;  // 越界！
        dynamic_arr[10] = 888; // 更严重的越界！
        
        free(dynamic_arr);
    }
}

// 看起来像越界但实际不是的情况（误报场景）
void false_positive_array_access() {
    int buffer[10];
    int size = 10;
    
    // 初始化数组
    for (int i = 0; i < size; i++) {
        buffer[i] = i;
    }
    
    // 这看起来像越界，但实际上是安全的
    // 因为size已经明确设置为10，与数组大小匹配
    int last_index = size - 1;
    printf("Last element: %d\n", buffer[last_index]);  // 实际上是buffer[9]，安全
    
    // 另一个看起来可疑但安全的访问
    if (size <= 10) {  // 有边界检查
        buffer[size - 1] = 999;  // 实际是buffer[9]，安全
    }
}

int main() {
    printf("Testing array bounds...\n");
    
    normal_array_access();
    problematic_array_access();  // 这个函数包含越界问题
    dynamic_array_bounds();      // 这个函数也包含越界问题
    false_positive_array_access();  // 看起来可疑但实际安全
    
    return 0;
}
