/*
 * 内存操作测试文件
 * 目的：触发 rule_002 (memcpy/memset + 可能)
 */

#include <string.h>

// 函数1：memcpy使用 - 应该被过滤（memcpy + 可能）
void copy_buffer(char* dest, const char* src, int size) {
    // 没有检查dest和src是否为NULL
    // 也没有检查size是否合理
    memcpy(dest, src, size);  // 可能导致缓冲区溢出
}

// 函数2：memset使用 - 应该被过滤（memset + 可能）
void clear_data(void* buffer, int size) {
    // 没有检查buffer是否为NULL
    // size可能不正确
    memset(buffer, 0, size);
}
