/**
 * @file data_analyzer.h
 * @brief 系统数据分析模块
 * @version 1.0
 * @date 2023-06-04
 */

#ifndef DATA_ANALYZER_H
#define DATA_ANALYZER_H

#include "system_monitor.h"

/**
 * @brief 初始化数据分析模块
 * @param warning_threshold 警告阈值
 * @param critical_threshold 严重阈值
 * @return SystemStatus 初始化状态
 */
SystemStatus init_data_analyzer(uint32_t warning_threshold, uint32_t critical_threshold);

/**
 * @brief 分析CPU使用率
 * @param cpu_usage CPU使用率百分比
 * @return SystemStatus 分析结果状态
 */
SystemStatus analyze_cpu_usage(uint32_t cpu_usage);

/**
 * @brief 分析内存使用率
 * @param memory_usage 内存使用率百分比
 * @return SystemStatus 分析结果状态
 */
SystemStatus analyze_memory_usage(uint32_t memory_usage);

/**
 * @brief 分析系统温度
 * @param temperature 系统温度（摄氏度）
 * @return SystemStatus 分析结果状态
 */
SystemStatus analyze_temperature(uint32_t temperature);

/**
 * @brief 分析电池电量
 * @param battery_level 电池电量百分比
 * @return SystemStatus 分析结果状态
 */
SystemStatus analyze_battery_level(uint32_t battery_level);

/**
 * @brief 分析完整系统数据
 * @param data 系统数据
 * @param event 输出参数，存储分析结果事件
 * @return SystemStatus 分析状态
 */
SystemStatus analyze_all_data(const SystemData* data, SystemEvent* event);

/**
 * @brief 关闭数据分析模块
 * @return SystemStatus 关闭状态
 */
SystemStatus shutdown_data_analyzer(void);

#endif /* DATA_ANALYZER_H */ 