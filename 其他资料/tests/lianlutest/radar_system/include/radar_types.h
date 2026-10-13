/**
 * 雷达系统基础类型定义
 */
#ifndef RADAR_TYPES_H
#define RADAR_TYPES_H

#include <stdint.h>
#include <stdbool.h>

// 雷达状态枚举
typedef enum {
    RADAR_STATE_IDLE = 0,
    RADAR_STATE_SCANNING,
    RADAR_STATE_TRACKING,
    RADAR_STATE_ERROR,
    RADAR_STATE_SHUTDOWN
} RadarState;

// 目标信息结构
typedef struct {
    uint32_t id;
    double distance;        // 距离（米）
    double azimuth;         // 方位角（度）
    double elevation;       // 俯仰角（度）
    double velocity;        // 速度（米/秒）
    double rcs;             // 雷达截面积
    uint64_t last_update;   // 最后更新时间戳
    bool is_valid;
} Target;

// 雷达配置结构
typedef struct {
    double scan_frequency;  // 扫描频率（Hz）
    double max_range;       // 最大探测距离（米）
    double min_range;       // 最小探测距离（米）
    int max_targets;        // 最大跟踪目标数
    double threshold;       // 检测阈值
    char log_file[256];
} RadarConfig;

// 信号数据结构
typedef struct {
    double *samples;        // 信号采样数据
    int sample_count;
    double timestamp;
    double frequency;
} SignalData;

#endif // RADAR_TYPES_H

