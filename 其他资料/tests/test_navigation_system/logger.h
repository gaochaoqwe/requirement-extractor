/**
 * @file logger.h
 * @brief 日志系统接口
 */

#ifndef LOGGER_H
#define LOGGER_H

// 日志级别
#define LOG_DEBUG 0
#define LOG_INFO  1
#define LOG_WARNING 2
#define LOG_ERROR 3

/**
 * @brief 初始化日志系统
 * @return 0表示成功，非0表示失败
 */
int logger_init(void);

/**
 * @brief 关闭日志系统
 */
void logger_shutdown(void);

/**
 * @brief 记录日志消息
 * @param level 日志级别
 * @param format 格式化字符串
 * @param ... 可变参数
 */
void log_message(int level, const char *format, ...);

/**
 * @brief 设置日志级别
 * @param level 最小日志级别
 */
void set_log_level(int level);

#endif // LOGGER_H

