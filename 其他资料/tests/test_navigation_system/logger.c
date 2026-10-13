/**
 * @file logger.c
 * @brief 日志系统实现
 */

#include <stdio.h>
#include <stdarg.h>
#include <time.h>
#include <string.h>
#include "logger.h"
#include "log_formatter.h"
#include "log_rotator.h"

static int current_log_level = LOG_INFO;
static FILE *log_file = NULL;
static char log_filepath[256] = "/var/log/navigation.log";  // 问题：路径硬编码

// 日志级别名称
static const char *level_names[] = {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR"
};

/**
 * @brief 初始化日志系统
 */
int logger_init(void) {
    // 打开日志文件
    log_file = fopen(log_filepath, "a");
    if (log_file == NULL) {
        fprintf(stderr, "Failed to open log file: %s\n", log_filepath);
        // 问题：日志文件打开失败时应该有后备方案
        log_file = stderr;  // 使用标准错误作为后备
    }
    
    log_message(LOG_INFO, "Logger initialized");
    return 0;
}

/**
 * @brief 关闭日志系统
 */
void logger_shutdown(void) {
    log_message(LOG_INFO, "Logger shutting down");
    
    if (log_file && log_file != stderr) {
        fclose(log_file);
        log_file = NULL;
    }
}

/**
 * @brief 记录日志消息
 */
void log_message(int level, const char *format, ...) {
    if (level < current_log_level) {
        return;  // 过滤低级别日志
    }
    
    if (!log_file) {
        log_file = stderr;
    }
    
    // 获取当前时间
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    char time_str[64];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);
    
    // 问题：没有线程安全保护，并发写入可能导致日志混乱
    
    // 写入时间戳和级别
    fprintf(log_file, "[%s] [%s] ", time_str, level_names[level]);
    
    // 写入格式化消息
    va_list args;
    va_start(args, format);
    vfprintf(log_file, format, args);
    va_end(args);
    
    fprintf(log_file, "\n");
    fflush(log_file);  // 立即刷新
    
    // 检查是否需要轮转日志
    check_and_rotate_log();
}

/**
 * @brief 设置日志级别
 */
void set_log_level(int level) {
    if (level >= LOG_DEBUG && level <= LOG_ERROR) {
        current_log_level = level;
        log_message(LOG_INFO, "Log level set to: %s", level_names[level]);
    }
}

