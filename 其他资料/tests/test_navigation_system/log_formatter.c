/**
 * @file log_formatter.c
 * @brief 日志格式化实现
 */

#include <stdio.h>
#include <time.h>
#include "log_formatter.h"

/**
 * @brief 格式化日志条目
 */
int format_log_entry(int level, const char *message, char *buffer, int size) {
    if (!message || !buffer || size <= 0) {
        return -1;
    }
    
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    
    snprintf(buffer, size, "[%04d-%02d-%02d %02d:%02d:%02d] [%d] %s",
             tm_info->tm_year + 1900,
             tm_info->tm_mon + 1,
             tm_info->tm_mday,
             tm_info->tm_hour,
             tm_info->tm_min,
             tm_info->tm_sec,
             level,
             message);
    
    return 0;
}

