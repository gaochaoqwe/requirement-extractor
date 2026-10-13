/*
 * 未初始化变量测试文件
 * 目的：触发 rule_004 (未初始化 + 可能)
 */

#include <stdio.h>

// 函数1：使用未初始化变量 - 应该被过滤（未初始化 + 可能）
int calculate_sum(int a, int b) {
    int result;  // 声明但未初始化
    
    if (a > 0) {
        result = a + b;
    }
    // 如果a <= 0，result可能未被初始化就返回
    return result;
}

// 函数2：条件初始化 - 应该被过滤
void conditional_init(int flag) {
    int value;  // 未初始化
    
    if (flag) {
        value = 100;
    }
    
    // 这里value可能未初始化
    printf("%d\n", value);
}
