/**
 * 雷达系统核心接口
 */
#ifndef RADAR_SYSTEM_H
#define RADAR_SYSTEM_H

#include "radar_types.h"

// 初始化雷达系统
int radar_init(const RadarConfig *config);

// 启动雷达扫描
int radar_start_scan(void);

// 停止雷达扫描
int radar_stop_scan(void);

// 切换到跟踪模式
int radar_switch_to_tracking(uint32_t target_id);

// 获取当前状态
RadarState radar_get_state(void);

// 处理信号数据
int radar_process_signal(const SignalData *signal);

// 获取目标列表
Target* radar_get_targets(int *count);

// 清理资源
void radar_cleanup(void);

#endif

