/**
 * @file logger.h
 * @brief 系统日志模块
 * @version 1.0
 * @date 2023-06-04
 */

#ifndef LOGGER_H
#define LOGGER_H

#include "system_monitor.h"

/**
 * @brief 初始化日志模块
 * @param log_file_path 日志文件路径
 * @param enabled 是否启用日志
 * @return SystemStatus 初始化状态
 */
SystemStatus init_logger(const char* log_file_path, bool enabled);

/**
 * @brief 记录系统事件
 * @param event 系统事件
 * @return SystemStatus 记录状态
 */
SystemStatus log_event(const SystemEvent* event);

/**
 * @brief 记录系统数据
 * @param data 系统数据
 * @return SystemStatus 记录状态
 */
SystemStatus log_data(const SystemData* data);

/**
 * @brief 记录调试信息
 * @param format 格式字符串
 * @param ... 可变参数
 * @return SystemStatus 记录状态
 */
SystemStatus log_debug(const char* format, ...);

/**
 * @brief 记录信息
 * @param format 格式字符串
 * @param ... 可变参数
 * @return SystemStatus 记录状态
 */
SystemStatus log_info(const char* format, ...);

/**
 * @brief 记录警告
 * @param format 格式字符串
 * @param ... 可变参数
 * @return SystemStatus 记录状态
 */
SystemStatus log_warning(const char* format, ...);

/**
 * @brief 记录错误
 * @param format 格式字符串
 * @param ... 可变参数
 * @return SystemStatus 记录状态
 */
SystemStatus log_error(const char* format, ...);

/**
 * @brief 关闭日志模块
 * @return SystemStatus 关闭状态
 */
SystemStatus shutdown_logger(void);

#endif /* LOGGER_H */ 