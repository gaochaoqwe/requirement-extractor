/**
 * @file data_analyzer.c
 * @brief 系统数据分析模块实现
 * @version 1.0
 * @date 2023-06-04
 */

#include "../include/data_analyzer.h"
#include "../include/utils.h"
#include <stdio.h>
#include <string.h>

/* 模块全局变量 */
static bool g_analyzer_initialized = false;
static uint32_t g_warning_threshold = 0;
static uint32_t g_critical_threshold = 0;

/* 内部函数声明 */
static SystemStatus get_status_by_value(uint32_t value);
static void generate_event_message(SystemEvent* event, const SystemData* data);

SystemStatus init_data_analyzer(uint32_t warning_threshold, uint32_t critical_threshold) {
    if (g_analyzer_initialized) {
        return SYSTEM_ERROR;
    }
    
    /* 验证阈值 */
    if (warning_threshold >= 100 || critical_threshold > 100 || warning_threshold >= critical_threshold) {
        return SYSTEM_ERROR;
    }
    
    g_warning_threshold = warning_threshold;
    g_critical_threshold = critical_threshold;
    g_analyzer_initialized = true;
    
    return SYSTEM_OK;
}

SystemStatus analyze_cpu_usage(uint32_t cpu_usage) {
    if (!g_analyzer_initialized) {
        return SYSTEM_ERROR;
    }
    
    return get_status_by_value(cpu_usage);
}

SystemStatus analyze_memory_usage(uint32_t memory_usage) {
    if (!g_analyzer_initialized) {
        return SYSTEM_ERROR;
    }
    
    return get_status_by_value(memory_usage);
}

SystemStatus analyze_temperature(uint32_t temperature) {
    if (!g_analyzer_initialized) {
        return SYSTEM_ERROR;
    }
    
    /* 温度阈值不同于百分比，需要特殊处理 */
    /* 假设正常温度范围为25-45摄氏度，警告为45-60，严重为60+ */
    if (temperature < 45) {
        return SYSTEM_OK;
    } else if (temperature < 60) {
        return SYSTEM_WARNING;
    } else {
        return SYSTEM_CRITICAL;
    }
}

SystemStatus analyze_battery_level(uint32_t battery_level) {
    if (!g_analyzer_initialized) {
        return SYSTEM_ERROR;
    }
    
    /* 电池电量是反向的，越低越严重 */
    if (battery_level > 30) {
        return SYSTEM_OK;
    } else if (battery_level > 15) {
        return SYSTEM_WARNING;
    } else {
        return SYSTEM_CRITICAL;
    }
}

SystemStatus analyze_all_data(const SystemData* data, SystemEvent* event) {
    if (!g_analyzer_initialized || data == NULL || event == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 分析各项数据 */
    SystemStatus cpu_status = analyze_cpu_usage(data->cpu_usage);
    SystemStatus memory_status = analyze_memory_usage(data->memory_usage);
    SystemStatus temp_status = analyze_temperature(data->temperature);
    SystemStatus battery_status = analyze_battery_level(data->battery_level);
    
    /* 取最严重的状态 */
    SystemStatus overall_status = SYSTEM_OK;
    
    if (cpu_status > overall_status) overall_status = cpu_status;
    if (memory_status > overall_status) overall_status = memory_status;
    if (temp_status > overall_status) overall_status = temp_status;
    if (battery_status > overall_status) overall_status = battery_status;
    
    /* 填充事件信息 */
    event->status = overall_status;
    event->timestamp = data->timestamp;
    generate_event_message(event, data);
    
    return overall_status;
}

SystemStatus shutdown_data_analyzer(void) {
    if (!g_analyzer_initialized) {
        return SYSTEM_ERROR;
    }
    
    g_analyzer_initialized = false;
    return SYSTEM_OK;
}

/* 内部函数实现 */

static SystemStatus get_status_by_value(uint32_t value) {
    if (value < g_warning_threshold) {
        return SYSTEM_OK;
    } else if (value < g_critical_threshold) {
        return SYSTEM_WARNING;
    } else {
        return SYSTEM_CRITICAL;
    }
}

static void generate_event_message(SystemEvent* event, const SystemData* data) {
    if (event == NULL || data == NULL) {
        return;
    }
    
    char message[256] = {0};
    
    switch (event->status) {
        case SYSTEM_OK:
            snprintf(message, sizeof(message),
                     "系统状态正常. CPU: %u%%, 内存: %u%%, 温度: %u°C, 电池: %u%%",
                     data->cpu_usage, data->memory_usage, data->temperature, data->battery_level);
            break;
            
        case SYSTEM_WARNING:
            if (data->cpu_usage >= g_warning_threshold) {
                snprintf(message, sizeof(message),
                         "警告: CPU使用率过高 (%u%%). 内存: %u%%, 温度: %u°C, 电池: %u%%",
                         data->cpu_usage, data->memory_usage, data->temperature, data->battery_level);
            } else if (data->memory_usage >= g_warning_threshold) {
                snprintf(message, sizeof(message),
                         "警告: 内存使用率过高 (%u%%). CPU: %u%%, 温度: %u°C, 电池: %u%%",
                         data->memory_usage, data->cpu_usage, data->temperature, data->battery_level);
            } else if (data->temperature >= 45) {
                snprintf(message, sizeof(message),
                         "警告: 系统温度过高 (%u°C). CPU: %u%%, 内存: %u%%, 电池: %u%%",
                         data->temperature, data->cpu_usage, data->memory_usage, data->battery_level);
            } else if (data->battery_level <= 30) {
                snprintf(message, sizeof(message),
                         "警告: 电池电量低 (%u%%). CPU: %u%%, 内存: %u%%, 温度: %u°C",
                         data->battery_level, data->cpu_usage, data->memory_usage, data->temperature);
            }
            break;
            
        case SYSTEM_CRITICAL:
            if (data->cpu_usage >= g_critical_threshold) {
                snprintf(message, sizeof(message),
                         "严重: CPU使用率极高 (%u%%). 内存: %u%%, 温度: %u°C, 电池: %u%%",
                         data->cpu_usage, data->memory_usage, data->temperature, data->battery_level);
            } else if (data->memory_usage >= g_critical_threshold) {
                snprintf(message, sizeof(message),
                         "严重: 内存使用率极高 (%u%%). CPU: %u%%, 温度: %u°C, 电池: %u%%",
                         data->memory_usage, data->cpu_usage, data->temperature, data->battery_level);
            } else if (data->temperature >= 60) {
                snprintf(message, sizeof(message),
                         "严重: 系统温度极高 (%u°C). CPU: %u%%, 内存: %u%%, 电池: %u%%",
                         data->temperature, data->cpu_usage, data->memory_usage, data->battery_level);
            } else if (data->battery_level <= 15) {
                snprintf(message, sizeof(message),
                         "严重: 电池电量极低 (%u%%). CPU: %u%%, 内存: %u%%, 温度: %u°C",
                         data->battery_level, data->cpu_usage, data->memory_usage, data->temperature);
            }
            break;
            
        default:
            snprintf(message, sizeof(message),
                     "系统状态未知. CPU: %u%%, 内存: %u%%, 温度: %u°C, 电池: %u%%",
                     data->cpu_usage, data->memory_usage, data->temperature, data->battery_level);
            break;
    }
    
    safe_strcpy(event->message, message, sizeof(event->message));
} 