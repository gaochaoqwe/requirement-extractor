/**
 * @file config_manager.h
 * @brief 系统配置管理模块
 * @version 1.0
 * @date 2023-06-04
 */

#ifndef CONFIG_MANAGER_H
#define CONFIG_MANAGER_H

#include "system_monitor.h"

/**
 * @brief 从文件加载系统配置
 * @param config_file 配置文件路径
 * @param config 输出参数，存储加载的配置
 * @return SystemStatus 加载状态
 */
SystemStatus load_config(const char* config_file, SystemConfig* config);

/**
 * @brief 保存系统配置到文件
 * @param config_file 配置文件路径
 * @param config 要保存的配置
 * @return SystemStatus 保存状态
 */
SystemStatus save_config(const char* config_file, const SystemConfig* config);

/**
 * @brief 验证系统配置有效性
 * @param config 要验证的配置
 * @return bool 配置是否有效
 */
bool validate_config(const SystemConfig* config);

/**
 * @brief 设置默认系统配置
 * @param config 输出参数，存储默认配置
 * @return void
 */
void set_default_config(SystemConfig* config);

/**
 * @brief 打印系统配置信息
 * @param config 要打印的配置
 * @return void
 */
void print_config(const SystemConfig* config);

#endif /* CONFIG_MANAGER_H */ 