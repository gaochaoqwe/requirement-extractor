/**
 * @file data_collector.c
 * @brief 系统数据采集模块实现
 * @version 1.0
 * @date 2023-06-04
 */

#include "../include/data_collector.h"
#include "../include/utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

/* 模块全局变量 */
static bool g_collector_initialized = false;
static uint32_t g_sampling_rate_ms = 0;

/* 内部函数声明 */
static void simulate_hardware_delay(void);

SystemStatus init_data_collector(uint32_t sampling_rate_ms) {
    if (g_collector_initialized) {
        return SYSTEM_ERROR;
    }
    
    if (sampling_rate_ms < 100) {
        return SYSTEM_ERROR;
    }
    
    g_sampling_rate_ms = sampling_rate_ms;
    g_collector_initialized = true;
    
    /* 初始化随机数生成器，用于模拟数据 */
    srand((unsigned int)time(NULL));
    
    return SYSTEM_OK;
}

uint32_t collect_cpu_usage(void) {
    if (!g_collector_initialized) {
        return 0;
    }
    
    /* 模拟硬件延迟 */
    simulate_hardware_delay();
    
    /* 模拟CPU使用率数据 */
    return (uint32_t)generate_random(10, 95);
}

uint32_t collect_memory_usage(void) {
    if (!g_collector_initialized) {
        return 0;
    }
    
    /* 模拟硬件延迟 */
    simulate_hardware_delay();
    
    /* 模拟内存使用率数据 */
    return (uint32_t)generate_random(20, 85);
}

uint32_t collect_temperature(void) {
    if (!g_collector_initialized) {
        return 0;
    }
    
    /* 模拟硬件延迟 */
    simulate_hardware_delay();
    
    /* 模拟温度数据 (25-75摄氏度) */
    return (uint32_t)generate_random(25, 75);
}

uint32_t collect_battery_level(void) {
    if (!g_collector_initialized) {
        return 0;
    }
    
    /* 模拟硬件延迟 */
    simulate_hardware_delay();
    
    /* 模拟电池电量数据 */
    return (uint32_t)generate_random(10, 100);
}

SystemStatus collect_all_data(SystemData* data) {
    if (!g_collector_initialized || data == NULL) {
        return SYSTEM_ERROR;
    }
    
    /* 采集各项数据 */
    data->cpu_usage = collect_cpu_usage();
    data->memory_usage = collect_memory_usage();
    data->temperature = collect_temperature();
    data->battery_level = collect_battery_level();
    data->timestamp = get_current_timestamp();
    
    return SYSTEM_OK;
}

SystemStatus shutdown_data_collector(void) {
    if (!g_collector_initialized) {
        return SYSTEM_ERROR;
    }
    
    g_collector_initialized = false;
    return SYSTEM_OK;
}

/* 内部函数实现 */

static void simulate_hardware_delay(void) {
    /* 模拟硬件读取延迟，根据采样率计算 */
    uint32_t delay_ms = g_sampling_rate_ms / 10;
    
    /* 至少延迟10ms，最多延迟100ms */
    if (delay_ms < 10) delay_ms = 10;
    if (delay_ms > 100) delay_ms = 100;
    
    /* 实际项目中，这里应该使用平台特定的延迟函数 */
    /* 为了简化，我们使用一个简单的循环来模拟延迟 */
    clock_t start_time = clock();
    clock_t delay_clocks = (clock_t)(delay_ms * (CLOCKS_PER_SEC / 1000));
    
    while (clock() - start_time < delay_clocks) {
        /* 空循环模拟延迟 */
    }
} 