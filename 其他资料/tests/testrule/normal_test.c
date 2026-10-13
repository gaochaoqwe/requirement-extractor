/*
 * 正常代码测试文件
 * 目的：不应该被过滤（没有触发任何规则的代码）
 */

#include <stdio.h>

/**
 * 计算两个数的和
 * @param a 第一个加数
 * @param b 第二个加数
 * @return 两数之和
 */
int add_numbers(int a, int b) {
    int result = a + b;  // 正确初始化
    return result;
}

/**
 * 打印数组内容
 * @param arr 数组指针
 * @param size 数组大小
 */
void print_array(const int* arr, int size) {
    // 有边界检查
    if (arr == NULL || size <= 0) {
        return;
    }
    
    // 正确的循环边界
    for (int i = 0; i < size; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}
