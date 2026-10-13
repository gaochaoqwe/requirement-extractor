/**
 * @file utils.c
 * @brief 系统工具函数模块实现
 * @version 1.0
 * @date 2023-06-04
 */

#include "../include/utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

time_t get_current_timestamp(void) {
    return time(NULL);
}

char* timestamp_to_string(time_t timestamp, char* buffer, size_t buffer_size) {
    static char static_buffer[32];
    char* result_buffer = buffer;
    size_t result_size = buffer_size;
    
    /* 如果没有提供缓冲区，使用静态缓冲区 */
    if (buffer == NULL) {
        result_buffer = static_buffer;
        result_size = sizeof(static_buffer);
    }
    
    /* 转换时间戳为本地时间 */
    struct tm* tm_info = localtime(&timestamp);
    if (tm_info == NULL) {
        safe_strcpy(result_buffer, "Invalid timestamp", result_size);
        return result_buffer;
    }
    
    /* 格式化时间字符串 */
    if (strftime(result_buffer, result_size, "%Y-%m-%d %H:%M:%S", tm_info) == 0) {
        safe_strcpy(result_buffer, "Format error", result_size);
    }
    
    return result_buffer;
}

int generate_random(int min, int max) {
    if (min > max) {
        int temp = min;
        min = max;
        max = temp;
    }
    
    return min + rand() % (max - min + 1);
}

char* safe_strcpy(char* dest, const char* src, size_t dest_size) {
    if (dest == NULL || src == NULL || dest_size == 0) {
        return dest;
    }
    
    size_t src_len = strlen(src);
    size_t copy_len = src_len < dest_size - 1 ? src_len : dest_size - 1;
    
    memcpy(dest, src, copy_len);
    dest[copy_len] = '\0';
    
    return dest;
}

char* safe_strcat(char* dest, const char* src, size_t dest_size) {
    if (dest == NULL || src == NULL || dest_size == 0) {
        return dest;
    }
    
    size_t dest_len = strlen(dest);
    if (dest_len >= dest_size - 1) {
        return dest;  /* 目标缓冲区已满 */
    }
    
    size_t src_len = strlen(src);
    size_t available = dest_size - dest_len - 1;
    size_t copy_len = src_len < available ? src_len : available;
    
    memcpy(dest + dest_len, src, copy_len);
    dest[dest_len + copy_len] = '\0';
    
    return dest;
}

const char* status_to_string(SystemStatus status) {
    switch (status) {
        case SYSTEM_OK:
            return "OK";
        case SYSTEM_ERROR:
            return "ERROR";
        case SYSTEM_WARNING:
            return "WARNING";
        case SYSTEM_CRITICAL:
            return "CRITICAL";
        default:
            return "UNKNOWN";
    }
}

bool check_null_ptr(const void* ptr, const char* ptr_name, const char* file, int line) {
    if (ptr == NULL) {
        fprintf(stderr, "空指针错误: %s 在 %s:%d\n", ptr_name, file, line);
        return true;
    }
    return false;
}

void* check_memory_alloc(void* ptr, size_t size, const char* file, int line) {
    if (ptr == NULL) {
        fprintf(stderr, "内存分配失败: 无法分配 %zu 字节，在 %s:%d\n", size, file, line);
        exit(EXIT_FAILURE);
    }
    return ptr;
} 