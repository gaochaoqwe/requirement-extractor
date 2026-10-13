/**
 * @file protocol_handler.c
 * @brief 通信协议处理实现
 */

#include <stdio.h>
#include "protocol_handler.h"
#include "logger.h"

/**
 * @brief 初始化协议处理器
 */
int protocol_handler_init(void) {
    log_message(LOG_DEBUG, "Protocol handler initialized");
    return 0;
}

/**
 * @brief 清理协议处理器
 */
void protocol_handler_cleanup(void) {
    log_message(LOG_DEBUG, "Protocol handler cleaned up");
}

