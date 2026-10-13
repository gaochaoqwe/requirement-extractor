/**
 * @file system_monitor.c
 * @brief 嵌入式系统监控软件主模块实现
 * @version 1.0
 * @date 2023-06-04
 */

#include "../include/system_monitor.h"
#include "../include/config_manager.h"
#include "../include/data_collector.h"
#include "../include/data_analyzer.h"
#include "../include/logger.h"
#include "../include/event_handler.h"
#include "../include/utils.h"

/* 全局变量 */
static bool g_system_initialized = false;
static SystemConfig g_system_config;

/* 系统监控函数实现 */

SystemStatus initialize_system(const SystemConfig* config) {
    if (g_system_initialized) {
        return SYSTEM_ERROR;
    }
    
    if (!validate_config(config)) {
        return SYSTEM_ERROR;
    }
    
    /* 复制配置 */
    memcpy(&g_system_config, config, sizeof(SystemConfig));
    
    /* 初始化各模块 */
    SystemStatus status = SYSTEM_OK;
    
    status = init_logger(config->log_file_path, config->logging_enabled);
    if (status != SYSTEM_OK) {
        return status;
    }
    
    status = init_data_collector(config->sampling_rate_ms);
    if (status != SYSTEM_OK) {
        shutdown_logger();
        return status;
    }
    
    status = init_data_analyzer(config->warning_threshold, config->critical_threshold);
    if (status != SYSTEM_OK) {
        shutdown_data_collector();
        shutdown_logger();
        return status;
    }
    
    status = init_event_handler();
    if (status != SYSTEM_OK) {
        shutdown_data_analyzer();
        shutdown_data_collector();
        shutdown_logger();
        return status;
    }
    
    g_system_initialized = true;
    
    /* 记录初始化成功 */
    log_info("系统监控初始化成功: %s", config->system_name);
    
    return SYSTEM_OK;
}

SystemStatus collect_system_data(SystemData* data) {
    if (!g_system_initialized || data == NULL) {
        return SYSTEM_ERROR;
    }
    
    return collect_all_data(data);
}

SystemStatus analyze_system_data(const SystemData* data, SystemEvent* event) {
    if (!g_system_initialized || data == NULL || event == NULL) {
        return SYSTEM_ERROR;
    }
    
    return analyze_all_data(data, event);
}

SystemStatus log_system_event(const SystemEvent* event) {
    if (!g_system_initialized || event == NULL) {
        return SYSTEM_ERROR;
    }
    
    return log_event(event);
}

SystemStatus handle_system_event(const SystemEvent* event) {
    if (!g_system_initialized || event == NULL) {
        return SYSTEM_ERROR;
    }
    
    return handle_event(event);
}

SystemStatus shutdown_system(void) {
    if (!g_system_initialized) {
        return SYSTEM_ERROR;
    }
    
    /* 关闭各模块 */
    shutdown_event_handler();
    shutdown_data_analyzer();
    shutdown_data_collector();
    
    /* 记录关闭信息 */
    log_info("系统监控已关闭: %s", g_system_config.system_name);
    
    /* 关闭日志模块 */
    shutdown_logger();
    
    g_system_initialized = false;
    
    return SYSTEM_OK;
} 