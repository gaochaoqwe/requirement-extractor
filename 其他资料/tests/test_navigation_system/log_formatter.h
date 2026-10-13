/**
 * @file log_formatter.h
 * @brief 日志格式化接口
 */

#ifndef LOG_FORMATTER_H
#define LOG_FORMATTER_H

/**
 * @brief 格式化日志条目
 * @param level 日志级别
 * @param message 消息内容
 * @param buffer 输出缓冲区
 * @param size 缓冲区大小
 * @return 0表示成功，非0表示失败
 */
int format_log_entry(int level, const char *message, char *buffer, int size);

#endif // LOG_FORMATTER_H

