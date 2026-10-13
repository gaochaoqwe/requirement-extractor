/*
 * 数组测试文件
 * 目的：触发 rule_001 (数组 + 可能)
 */

#include <stdio.h>

// 函数1：数组越界风险 - 应该被过滤（数组 + 可能）
int process_array(int arr[], int size) {
    int result = 0;
    // 故意写成可能越界的代码
    for (int i = 0; i <= size; i++) {  // 注意这里是 <=，可能越界
        result += arr[i];
    }
    return result;
}

// 函数2：数组访问但确定性问题 - 不应该被过滤
void fill_array(int arr[10]) {
    // 这里会有固定大小的数组问题，但不涉及"可能"
    arr[15] = 100;  // 明确越界
}
