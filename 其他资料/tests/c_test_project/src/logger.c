/**
 * @file logger.c
 * @brief 系统日志模块实现
 * @version 1.0
 * @date 2023-06-04
 */

#include "../include/logger.h"
#include "../include/utils.h"
#include <stdio.h>
#include <stdarg.h>
#include <time.h>

/* 模块全局变量 */
static bool g_logger_initialized = false;
static bool g_logging_enabled = false;
static FILE* g_log_file = NULL;
static char g_log_file_path[256] = {0};

/* 日志级别定义 */
typedef enum {
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR
} LogLevel;

/* 内部函数声明 */
static SystemStatus write_log(LogLevel level, const char* format, va_list args);
static const char* get_log_level_string(LogLevel level);

SystemStatus init_logger(const char* log_file_path, bool enabled) {
    if (g_logger_initialized) {
        return SYSTEM_ERROR;
    }
    
    g_logging_enabled = enabled;
    
    if (enabled) {
        if (log_file_path == NULL || log_file_path[0] == '\0') {
            return SYSTEM_ERROR;
        }
        
        safe_strcpy(g_log_file_path, log_file_path, sizeof(g_log_file_path));
        
        /* 打开日志文件 */
        g_log_file = fopen(log_file_path, "a");
        if (g_log_file == NULL) {
            return SYSTEM_ERROR;
        }
        
        /* 写入日志头部 */
        time_t now = time(NULL);
        struct tm* tm_info = localtime(&now);
        char time_str[32];
        strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);
        
        fprintf(g_log_file, "\n\n");
        fprintf(g_log_file, "==========================================================\n");
        fprintf(g_log_file, "系统日志开始 - %s\n", time_str);
        fprintf(g_log_file, "==========================================================\n");
        fflush(g_log_file);
    }
    
    g_logger_initialized = true;
    return SYSTEM_OK;
}

SystemStatus log_event(const SystemEvent* event) {
    if (!g_logger_initialized || !g_logging_enabled || event == NULL) {
        return SYSTEM_ERROR;
    }
    
    if (g_log_file == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 获取事件时间字符串 */
    char time_str[32];
    struct tm* tm_info = localtime(&event->timestamp);
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);
    
    /* 获取事件状态字符串 */
    const char* status_str = status_to_string(event->status);
    
    /* 写入事件日志 */
    fprintf(g_log_file, "[%s] [EVENT-%s] %s\n", time_str, status_str, event->message);
    fflush(g_log_file);
    
    return SYSTEM_OK;
}

SystemStatus log_data(const SystemData* data) {
    if (!g_logger_initialized || !g_logging_enabled || data == NULL) {
        return SYSTEM_ERROR;
    }
    
    if (g_log_file == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 获取数据时间字符串 */
    char time_str[32];
    struct tm* tm_info = localtime(&data->timestamp);
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);
    
    /* 写入数据日志 */
    fprintf(g_log_file, "[%s] [DATA] CPU: %u%%, 内存: %u%%, 温度: %u°C, 电池: %u%%\n",
            time_str, data->cpu_usage, data->memory_usage, data->temperature, data->battery_level);
    fflush(g_log_file);
    
    return SYSTEM_OK;
}

SystemStatus log_debug(const char* format, ...) {
    if (!g_logger_initialized || !g_logging_enabled || format == NULL) {
        return SYSTEM_ERROR;
    }
    
    va_list args;
    va_start(args, format);
    SystemStatus status = write_log(LOG_LEVEL_DEBUG, format, args);
    va_end(args);
    
    return status;
}

SystemStatus log_info(const char* format, ...) {
    if (!g_logger_initialized || !g_logging_enabled || format == NULL) {
        return SYSTEM_ERROR;
    }
    
    va_list args;
    va_start(args, format);
    SystemStatus status = write_log(LOG_LEVEL_INFO, format, args);
    va_end(args);
    
    return status;
}

SystemStatus log_warning(const char* format, ...) {
    if (!g_logger_initialized || !g_logging_enabled || format == NULL) {
        return SYSTEM_ERROR;
    }
    
    va_list args;
    va_start(args, format);
    SystemStatus status = write_log(LOG_LEVEL_WARNING, format, args);
    va_end(args);
    
    return status;
}

SystemStatus log_error(const char* format, ...) {
    if (!g_logger_initialized || !g_logging_enabled || format == NULL) {
        return SYSTEM_ERROR;
    }
    
    va_list args;
    va_start(args, format);
    SystemStatus status = write_log(LOG_LEVEL_ERROR, format, args);
    va_end(args);
    
    return status;
}

SystemStatus shutdown_logger(void) {
    if (!g_logger_initialized) {
        return SYSTEM_ERROR;
    }
    
    if (g_logging_enabled && g_log_file != NULL) {
        /* 写入日志尾部 */
        time_t now = time(NULL);
        struct tm* tm_info = localtime(&now);
        char time_str[32];
        strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);
        
        fprintf(g_log_file, "==========================================================\n");
        fprintf(g_log_file, "系统日志结束 - %s\n", time_str);
        fprintf(g_log_file, "==========================================================\n\n");
        
        /* 关闭日志文件 */
        fclose(g_log_file);
        g_log_file = NULL;
    }
    
    g_logger_initialized = false;
    return SYSTEM_OK;
}

/* 内部函数实现 */

static SystemStatus write_log(LogLevel level, const char* format, va_list args) {
    if (g_log_file == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 获取当前时间字符串 */
    time_t now = time(NULL);
    struct tm* tm_info = localtime(&now);
    char time_str[32];
    strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S", tm_info);
    
    /* 获取日志级别字符串 */
    const char* level_str = get_log_level_string(level);
    
    /* 写入日志头部 */
    fprintf(g_log_file, "[%s] [%s] ", time_str, level_str);
    
    /* 写入日志内容 */
    vfprintf(g_log_file, format, args);
    fprintf(g_log_file, "\n");
    
    /* 刷新缓冲区 */
    fflush(g_log_file);
    
    return SYSTEM_OK;
}

static const char* get_log_level_string(LogLevel level) {
    switch (level) {
        case LOG_LEVEL_DEBUG:
            return "DEBUG";
        case LOG_LEVEL_INFO:
            return "INFO";
        case LOG_LEVEL_WARNING:
            return "WARNING";
        case LOG_LEVEL_ERROR:
            return "ERROR";
        default:
            return "UNKNOWN";
    }
} 