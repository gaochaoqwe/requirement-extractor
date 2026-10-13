/**
 * 主测试文件
 * 用于静态分析过滤工具测试
 */
#include <stdio.h>
#include <stdlib.h>
#include "test_utils.h"

// 外部函数声明
extern void normal_array_access();
extern void problematic_array_access();
extern void normal_memory_usage();
extern void problematic_memory_usage();
extern void normal_variable_usage();
extern void problematic_variable_usage();

int main() {
    printf("=== 静态分析过滤工具测试代码库 ===\n");
    printf("本代码库包含故意埋入的代码问题，用于测试AI分析能力\n\n");
    
    printf("1. 测试数组边界问题...\n");
    normal_array_access();
    problematic_array_access();  // 包含数组越界问题
    
    printf("\n2. 测试内存管理问题...\n");
    normal_memory_usage();
    problematic_memory_usage();  // 包含内存释放后使用问题
    
    printf("\n3. 测试变量初始化问题...\n");
    normal_variable_usage();
    problematic_variable_usage();  // 包含未初始化变量问题
    
    printf("\n=== 测试完成 ===\n");
    return 0;
}
