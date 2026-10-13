/*
 * 指针测试文件
 * 目的：触发 rule_003 (指针 + 可能)
 */

#include <stdlib.h>

// 函数1：指针使用问题 - 应该被过滤（指针 + 可能）
int* allocate_data(int size) {
    int* ptr = (int*)malloc(size * sizeof(int));
    // 没有检查malloc是否成功，可能返回NULL
    *ptr = 10;  // 指针可能为NULL，导致问题
    return ptr;
}

// 函数2：空指针解引用 - 应该被过滤（指针 + 可能）
void use_pointer(int* data) {
    // 没有检查指针是否为空
    if (data != NULL) {
        int value = *data;
    }
    // 但这里可能在某些路径使用
}
