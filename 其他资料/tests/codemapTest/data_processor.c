#include <stdio.h>
#include <stdlib.h>
#include "data_processor.h"
#include "utils.h"
#include "math_operations.h"

// 处理数组 - 综合处理函数
void process_array(int* array, int size) {
    if (array == NULL || size <= 0) {
        log_message("数组处理：无效输入");
        return;
    }
    
    printf("开始处理数组，大小: %d\n", size);
    log_message("开始数组处理");
    
    // 显示原始数组
    printf("原始数组: ");
    for (int i = 0; i < size; i++) {
        printf("%d ", array[i]);
    }
    printf("\n");
    
    // 查找最大值和最小值
    int max = find_maximum(array, size);
    int min = find_minimum(array, size);
    printf("最大值: %d, 最小值: %d\n", max, min);
    
    // 计算总和
    int sum = 0;
    for (int i = 0; i < size; i++) {
        sum = add_numbers(sum, array[i]);
    }
    printf("数组总和: %d\n", sum);
    
    log_message("数组处理完成");
}

// 计算数组平均值
double calculate_average(int* array, int size) {
    if (array == NULL || size <= 0) {
        log_message("平均值计算：无效输入");
        return 0.0;
    }
    
    int sum = 0;
    for (int i = 0; i < size; i++) {
        sum = add_numbers(sum, array[i]);
    }
    
    double average = divide_numbers((double)sum, (double)size);
    log_message("计算数组平均值");
    return average;
}

// 查找数组最大值
// BUG14: 返回0作为错误标识不合理，因为0可能是数组中的有效最大值
int find_maximum(int* array, int size) {
    if (array == NULL || size <= 0) {
        log_message("最大值查找：无效输入");
        // BUG15: 返回0无法区分是错误还是数组最大值确实是0
        return 0;
    }
    
    int max = array[0];
    // BUG16: 循环从1开始，但没有检查size是否>=1，虽然前面检查了size<=0
    for (int i = 1; i < size; i++) {
        if (array[i] > max) {
            max = array[i];
        }
    }
    
    log_message("查找数组最大值");
    return max;
}

// 查找数组最小值
int find_minimum(int* array, int size) {
    if (array == NULL || size <= 0) {
        log_message("最小值查找：无效输入");
        return 0;
    }
    
    int min = array[0];
    for (int i = 1; i < size; i++) {
        if (array[i] < min) {
            min = array[i];
        }
    }
    
    log_message("查找数组最小值");
    return min;
}

// 冒泡排序数组
// BUG17: 冒泡排序时间复杂度为O(n²)，对大数组性能很差，应该使用快速排序等算法
void sort_array(int* array, int size) {
    if (array == NULL || size <= 0) {
        log_message("数组排序：无效输入");
        return;
    }
    
    // BUG18: 没有优化的冒泡排序，即使数组已经有序仍然会遍历所有元素
    for (int i = 0; i < size - 1; i++) {
        for (int j = 0; j < size - i - 1; j++) {
            if (array[j] > array[j + 1]) {
                // 交换元素
                int temp = array[j];
                array[j] = array[j + 1];
                array[j + 1] = temp;
            }
        }
    }
    
    log_message("数组排序完成");
}

// 在数组中搜索元素
// BUG19: 线性搜索效率低，如果数组已排序应该使用二分查找
int search_element(int* array, int size, int target) {
    if (array == NULL || size <= 0) {
        log_message("元素搜索：无效输入");
        return -1;
    }
    
    // BUG20: 对于大数组，线性搜索O(n)效率太低
    for (int i = 0; i < size; i++) {
        if (array[i] == target) {
            log_message("找到目标元素");
            return i;
        }
    }
    
    log_message("未找到目标元素");
    return -1;
}

// 反转数组
void reverse_array(int* array, int size) {
    if (array == NULL || size <= 0) {
        log_message("数组反转：无效输入");
        return;
    }
    
    for (int i = 0; i < size / 2; i++) {
        int temp = array[i];
        array[i] = array[size - 1 - i];
        array[size - 1 - i] = temp;
    }
    
    log_message("数组反转完成");
} 