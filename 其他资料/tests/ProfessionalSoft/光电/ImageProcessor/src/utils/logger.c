/**
 * @file logger.c
 * @brief 日志系统实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <time.h>
#include <pthread.h>

#include "../../include/utils/logger.h"

// 日志系统结构
typedef struct {
    FILE* log_file;
    LogLevel level;
    pthread_mutex_t log_mutex;
    bool initialized;
    char log_filename[256];
} LoggerContext;

static LoggerContext g_logger = {0};

// 日志级别名称
static const char* level_names[] = {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "FATAL"
};

/**
 * @brief 获取当前时间字符串
 */
static void get_timestamp(char* buffer, size_t size) {
    time_t now = time(NULL);
    struct tm* tm_info = localtime(&now);
    strftime(buffer, size, "%Y-%m-%d %H:%M:%S", tm_info);
}

/**
 * @brief 内部日志输出函数
 */
static void log_internal(LogLevel level, const char* format, va_list args) {
    if (!g_logger.initialized || level < g_logger.level) {
        return;
    }

    pthread_mutex_lock(&g_logger.log_mutex);

    char timestamp[32];
    get_timestamp(timestamp, sizeof(timestamp));

    // 输出到控制台
    printf("[%s] [%s] ", timestamp, level_names[level]);
    vprintf(format, args);
    printf("\n");

    // 输出到文件
    if (g_logger.log_file) {
        fprintf(g_logger.log_file, "[%s] [%s] ", timestamp, level_names[level]);
        vfprintf(g_logger.log_file, format, args);
        fprintf(g_logger.log_file, "\n");
        // BUG14: 频繁的fflush调用严重影响性能
        // 在光电实时系统中，每次日志都强制刷新磁盘会导致严重的I/O瓶颈
        fflush(g_logger.log_file);
    }

    pthread_mutex_unlock(&g_logger.log_mutex);
}

/**
 * @brief 初始化日志系统
 */
ReturnCode logger_init(LogLevel level, const char* filename) {
    if (g_logger.initialized) {
        printf("日志系统已经初始化\n");
        return SUCCESS;
    }

    memset(&g_logger, 0, sizeof(LoggerContext));
    
    // 初始化互斥锁
    if (pthread_mutex_init(&g_logger.log_mutex, NULL) != 0) {
        printf("初始化日志互斥锁失败\n");
        return FAILURE;
    }

    g_logger.level = level;

    // 打开日志文件
    if (filename) {
        strncpy(g_logger.log_filename, filename, sizeof(g_logger.log_filename) - 1);
        g_logger.log_file = fopen(filename, "a");
        if (!g_logger.log_file) {
            printf("打开日志文件失败: %s\n", filename);
            pthread_mutex_destroy(&g_logger.log_mutex);
            return FAILURE;
        }
    }

    g_logger.initialized = true;
    
    logger_info("日志系统初始化完成，级别: %s", level_names[level]);
    return SUCCESS;
}

/**
 * @brief 设置日志级别
 */
void logger_set_level(LogLevel level) {
    if (g_logger.initialized) {
        g_logger.level = level;
        logger_info("日志级别设置为: %s", level_names[level]);
    }
}

/**
 * @brief 输出调试信息
 */
void logger_debug(const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_internal(LOG_LEVEL_DEBUG, format, args);
    va_end(args);
}

/**
 * @brief 输出信息
 */
void logger_info(const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_internal(LOG_LEVEL_INFO, format, args);
    va_end(args);
}

/**
 * @brief 输出警告
 */
void logger_warning(const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_internal(LOG_LEVEL_WARNING, format, args);
    va_end(args);
}

/**
 * @brief 输出错误
 */
void logger_error(const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_internal(LOG_LEVEL_ERROR, format, args);
    va_end(args);
}

/**
 * @brief 输出致命错误
 */
void logger_fatal(const char* format, ...) {
    va_list args;
    va_start(args, format);
    log_internal(LOG_LEVEL_FATAL, format, args);
    va_end(args);
}

/**
 * @brief 清理日志系统
 */
void logger_cleanup(void) {
    if (!g_logger.initialized) {
        return;
    }

    logger_info("日志系统正在关闭");

    pthread_mutex_lock(&g_logger.log_mutex);

    if (g_logger.log_file) {
        fclose(g_logger.log_file);
        g_logger.log_file = NULL;
    }

    g_logger.initialized = false;
    
    pthread_mutex_unlock(&g_logger.log_mutex);
    pthread_mutex_destroy(&g_logger.log_mutex);
} 