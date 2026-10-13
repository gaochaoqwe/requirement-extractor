/*
 * 魔法数字测试文件
 * 目的：触发 rule_006 (硬编码 OR 魔法数字)
 */

#include <stdio.h>

// 函数1：包含硬编码值 - 应该被过滤
int calculate_buffer_size() {
    return 1024;  // 硬编码的缓冲区大小
}

// 函数2：包含多个魔法数字 - 应该被过滤
void process_data(int input) {
    if (input > 100) {  // 魔法数字 100
        printf("Large value\n");
    }
    
    int buffer[256];  // 魔法数字 256
    buffer[0] = 0xFF;  // 魔法数字 0xFF
}
