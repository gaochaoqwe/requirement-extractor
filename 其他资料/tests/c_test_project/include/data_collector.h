/**
 * @file data_collector.h
 * @brief 系统数据采集模块
 * @version 1.0
 * @date 2023-06-04
 */

#ifndef DATA_COLLECTOR_H
#define DATA_COLLECTOR_H

#include "system_monitor.h"

/**
 * @brief 初始化数据采集模块
 * @param sampling_rate_ms 采样率（毫秒）
 * @return SystemStatus 初始化状态
 */
SystemStatus init_data_collector(uint32_t sampling_rate_ms);

/**
 * @brief 采集CPU使用率
 * @return uint32_t CPU使用率百分比
 */
uint32_t collect_cpu_usage(void);

/**
 * @brief 采集内存使用率
 * @return uint32_t 内存使用率百分比
 */
uint32_t collect_memory_usage(void);

/**
 * @brief 采集系统温度
 * @return uint32_t 系统温度（摄氏度）
 */
uint32_t collect_temperature(void);

/**
 * @brief 采集电池电量
 * @return uint32_t 电池电量百分比
 */
uint32_t collect_battery_level(void);

/**
 * @brief 采集完整系统数据
 * @param data 输出参数，存储采集的系统数据
 * @return SystemStatus 采集状态
 */
SystemStatus collect_all_data(SystemData* data);

/**
 * @brief 关闭数据采集模块
 * @return SystemStatus 关闭状态
 */
SystemStatus shutdown_data_collector(void);

#endif /* DATA_COLLECTOR_H */ 