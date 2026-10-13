#include <stdio.h>
#include "utils.h"
#include "math_operations.h"
#include "data_processor.h"

// 主函数 - 程序入口点
int main() {
    printf("=== 代码地图测试程序 ===\n");
    
    // 调用工具函数
    print_welcome_message();
    
    // 调用数学运算函数
    int a = 10, b = 5;
    int sum = add_numbers(a, b);
    int product = multiply_numbers(a, b);
    
    printf("数学运算结果: %d + %d = %d, %d * %d = %d\n", 
           a, b, sum, a, b, product);
    
    // 调用数据处理函数
    int data[] = {1, 2, 3, 4, 5};
    int size = sizeof(data) / sizeof(data[0]);
    
    process_array(data, size);
    double average = calculate_average(data, size);
    printf("数组平均值: %.2f\n", average);
    
    // 调用清理函数
    cleanup_resources();
    
    return 0;
}

// 辅助函数 - 显示程序信息
void show_program_info() {
    printf("程序版本: 1.0\n");
    printf("作者: 测试用户\n");
    printf("功能: 代码地图功能测试\n");
} 