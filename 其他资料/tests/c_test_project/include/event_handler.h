/**
 * @file event_handler.h
 * @brief 系统事件处理模块
 * @version 1.0
 * @date 2023-06-04
 */

#ifndef EVENT_HANDLER_H
#define EVENT_HANDLER_H

#include "system_monitor.h"

/**
 * @brief 初始化事件处理模块
 * @return SystemStatus 初始化状态
 */
SystemStatus init_event_handler(void);

/**
 * @brief 注册事件处理回调函数
 * @param status 事件状态
 * @param callback 回调函数
 * @return SystemStatus 注册状态
 */
typedef SystemStatus (*EventCallback)(const SystemEvent*);
SystemStatus register_event_callback(SystemStatus status, EventCallback callback);

/**
 * @brief 处理系统事件
 * @param event 系统事件
 * @return SystemStatus 处理状态
 */
SystemStatus handle_event(const SystemEvent* event);

/**
 * @brief 处理正常状态事件
 * @param event 系统事件
 * @return SystemStatus 处理状态
 */
SystemStatus handle_ok_event(const SystemEvent* event);

/**
 * @brief 处理警告状态事件
 * @param event 系统事件
 * @return SystemStatus 处理状态
 */
SystemStatus handle_warning_event(const SystemEvent* event);

/**
 * @brief 处理错误状态事件
 * @param event 系统事件
 * @return SystemStatus 处理状态
 */
SystemStatus handle_error_event(const SystemEvent* event);

/**
 * @brief 处理严重状态事件
 * @param event 系统事件
 * @return SystemStatus 处理状态
 */
SystemStatus handle_critical_event(const SystemEvent* event);

/**
 * @brief 关闭事件处理模块
 * @return SystemStatus 关闭状态
 */
SystemStatus shutdown_event_handler(void);

#endif /* EVENT_HANDLER_H */ 