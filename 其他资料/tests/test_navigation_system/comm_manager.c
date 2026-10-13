/**
 * @file comm_manager.c
 * @brief 通信管理实现
 */

#include <stdio.h>
#include "comm_manager.h"
#include "tcp_client.h"
#include "protocol_handler.h"
#include "logger.h"

/**
 * @brief 初始化通信模块
 */
int comm_initialize(void) {
    int ret;
    
    log_message(LOG_INFO, "Initializing communication module");
    
    // 初始化协议处理器
    ret = protocol_handler_init();
    if (ret != 0) {
        log_message(LOG_ERROR, "Protocol handler init failed");
        return -1;
    }
    
    // 连接到服务器
    ret = tcp_connect("127.0.0.1", 8080);  // 问题：服务器地址硬编码
    if (ret != 0) {
        log_message(LOG_WARNING, "TCP connection failed, running in offline mode");
        return -2;
    }
    
    log_message(LOG_INFO, "Communication module initialized");
    return 0;
}

/**
 * @brief 关闭通信模块
 */
void comm_shutdown(void) {
    log_message(LOG_INFO, "Shutting down communication module");
    tcp_disconnect();
    protocol_handler_cleanup();
}

