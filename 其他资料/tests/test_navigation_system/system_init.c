/**
 * @file system_init.c
 * @brief 系统初始化实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "system_init.h"
#include "config_loader.h"
#include "memory_manager.h"
#include "logger.h"

// 系统状态
static int system_ready = 0;

/**
 * @brief 系统初始化
 */
int system_initialize(void) {
    int ret;
    
    // 初始化日志系统（最先初始化）
    ret = logger_init();
    if (ret != 0) {
        fprintf(stderr, "Failed to initialize logger\n");
        return -1;
    }
    
    // 加载配置文件
    log_message(LOG_INFO, "Loading configuration...");
    ret = load_config_file("/etc/navigation/config.ini");  // 问题：硬编码路径
    if (ret != 0) {
        log_message(LOG_ERROR, "Failed to load config file");
        return -2;
    }
    
    // 验证配置
    ret = validate_config();
    if (ret != 0) {
        log_message(LOG_ERROR, "Configuration validation failed");
        return -3;
    }
    
    // 分配系统缓冲区
    log_message(LOG_INFO, "Allocating system buffers...");
    ret = allocate_system_buffers();
    if (ret != 0) {
        log_message(LOG_ERROR, "Failed to allocate buffers");
        // 问题：这里没有清理已经加载的配置
        return -4;
    }
    
    // 初始化硬件模块
    log_message(LOG_INFO, "Initializing hardware modules...");
    // TODO: 实际的硬件初始化代码
    
    system_ready = 1;
    log_message(LOG_INFO, "System initialization complete");
    
    return 0;
}

/**
 * @brief 系统清理
 */
void system_cleanup(void) {
    log_message(LOG_INFO, "Starting system cleanup");
    
    // 释放缓冲区
    free_system_buffers();
    
    // 清理配置
    cleanup_config();
    
    // 关闭日志系统
    logger_shutdown();
    
    system_ready = 0;
}

/**
 * @brief 获取系统状态
 */
int get_system_status(void) {
    return system_ready;
}

