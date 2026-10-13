/**
 * @file system_monitor.h
 * @brief 嵌入式系统监控软件主头文件
 * @version 1.0
 * @date 2023-06-04
 */

#ifndef SYSTEM_MONITOR_H
#define SYSTEM_MONITOR_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>

/* 系统状态码定义 */
typedef enum {
    SYSTEM_OK = 0,
    SYSTEM_ERROR,
    SYSTEM_WARNING,
    SYSTEM_CRITICAL
} SystemStatus;

/* 系统配置结构体 */
typedef struct {
    char system_name[64];
    uint32_t sampling_rate_ms;
    uint32_t warning_threshold;
    uint32_t critical_threshold;
    bool logging_enabled;
    char log_file_path[256];
} SystemConfig;

/* 系统监控数据结构体 */
typedef struct {
    uint32_t cpu_usage;
    uint32_t memory_usage;
    uint32_t temperature;
    uint32_t battery_level;
    time_t timestamp;
} SystemData;

/* 系统事件结构体 */
typedef struct {
    SystemStatus status;
    char message[256];
    time_t timestamp;
} SystemEvent;

/* 函数声明 */

/**
 * @brief 初始化系统监控
 * @param config 系统配置
 * @return SystemStatus 初始化状态
 */
SystemStatus initialize_system(const SystemConfig* config);

/**
 * @brief 采集系统数据
 * @param data 输出参数，存储采集的系统数据
 * @return SystemStatus 采集状态
 */
SystemStatus collect_system_data(SystemData* data);

/**
 * @brief 分析系统数据
 * @param data 系统数据
 * @param event 输出参数，存储分析结果事件
 * @return SystemStatus 分析状态
 */
SystemStatus analyze_system_data(const SystemData* data, SystemEvent* event);

/**
 * @brief 记录系统事件
 * @param event 系统事件
 * @return SystemStatus 记录状态
 */
SystemStatus log_system_event(const SystemEvent* event);

/**
 * @brief 处理系统事件
 * @param event 系统事件
 * @return SystemStatus 处理状态
 */
SystemStatus handle_system_event(const SystemEvent* event);

/**
 * @brief 关闭系统监控
 * @return SystemStatus 关闭状态
 */
SystemStatus shutdown_system(void);

#endif /* SYSTEM_MONITOR_H */ 