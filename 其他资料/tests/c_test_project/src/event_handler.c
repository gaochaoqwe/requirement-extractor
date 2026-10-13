/**
 * @file event_handler.c
 * @brief 系统事件处理模块实现
 * @version 1.0
 * @date 2023-06-04
 */

#include "../include/event_handler.h"
#include "../include/logger.h"
#include "../include/utils.h"
#include <stdio.h>
#include <stdlib.h>

/* 模块全局变量 */
static bool g_handler_initialized = false;
static EventCallback g_callbacks[4] = {NULL, NULL, NULL, NULL};

/* 内部函数声明 */
static void print_event(const SystemEvent* event);

SystemStatus init_event_handler(void) {
    if (g_handler_initialized) {
        return SYSTEM_ERROR;
    }
    
    /* 注册默认处理函数 */
    register_event_callback(SYSTEM_OK, handle_ok_event);
    register_event_callback(SYSTEM_WARNING, handle_warning_event);
    register_event_callback(SYSTEM_ERROR, handle_error_event);
    register_event_callback(SYSTEM_CRITICAL, handle_critical_event);
    
    g_handler_initialized = true;
    return SYSTEM_OK;
}

SystemStatus register_event_callback(SystemStatus status, EventCallback callback) {
    if (!g_handler_initialized && status != SYSTEM_OK) {
        return SYSTEM_ERROR;
    }
    
    if (status < SYSTEM_OK || status > SYSTEM_CRITICAL || callback == NULL) {
        return SYSTEM_ERROR;
    }
    
    g_callbacks[status] = callback;
    return SYSTEM_OK;
}

SystemStatus handle_event(const SystemEvent* event) {
    if (!g_handler_initialized || event == NULL) {
        return SYSTEM_ERROR;
    }
    
    SystemStatus status = event->status;
    if (status < SYSTEM_OK || status > SYSTEM_CRITICAL) {
        return SYSTEM_ERROR;
    }
    
    /* 记录事件 */
    log_event(event);
    
    /* 调用对应的处理函数 */
    if (g_callbacks[status] != NULL) {
        return g_callbacks[status](event);
    }
    
    return SYSTEM_OK;
}

SystemStatus handle_ok_event(const SystemEvent* event) {
    if (event == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 正常状态事件只需打印 */
    print_event(event);
    return SYSTEM_OK;
}

SystemStatus handle_warning_event(const SystemEvent* event) {
    if (event == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 警告状态事件需要打印并记录 */
    print_event(event);
    log_warning("警告事件: %s", event->message);
    
    /* 这里可以添加警告处理逻辑，如发送通知等 */
    
    return SYSTEM_OK;
}

SystemStatus handle_error_event(const SystemEvent* event) {
    if (event == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 错误状态事件需要打印并记录 */
    print_event(event);
    log_error("错误事件: %s", event->message);
    
    /* 这里可以添加错误处理逻辑，如尝试恢复等 */
    
    return SYSTEM_OK;
}

SystemStatus handle_critical_event(const SystemEvent* event) {
    if (event == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 严重状态事件需要打印并记录 */
    print_event(event);
    log_error("严重事件: %s", event->message);
    
    /* 这里可以添加严重事件处理逻辑，如系统重启等 */
    printf("\n*** 严重警告: 系统状态危急! ***\n");
    printf("*** 需要立即采取措施! ***\n\n");
    
    return SYSTEM_OK;
}

SystemStatus shutdown_event_handler(void) {
    if (!g_handler_initialized) {
        return SYSTEM_ERROR;
    }
    
    /* 清除回调函数 */
    for (int i = 0; i < 4; i++) {
        g_callbacks[i] = NULL;
    }
    
    g_handler_initialized = false;
    return SYSTEM_OK;
}

/* 内部函数实现 */

static void print_event(const SystemEvent* event) {
    if (event == NULL) {
        return;
    }
    
    /* 获取事件时间字符串 */
    char time_str[32];
    timestamp_to_string(event->timestamp, time_str, sizeof(time_str));
    
    /* 获取事件状态字符串 */
    const char* status_str = status_to_string(event->status);
    
    /* 打印事件信息 */
    printf("[%s] [%s] %s\n", time_str, status_str, event->message);
} 