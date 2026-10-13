/**
 * 目标跟踪模块
 */
#ifndef TARGET_TRACKER_H
#define TARGET_TRACKER_H

#include "radar_types.h"

// 初始化跟踪器
int tracker_init(int max_targets);

// 更新目标跟踪
int tracker_update(const Target *targets, int count);

// 预测目标位置
int tracker_predict_position(uint32_t target_id, double delta_time, 
                            double *pred_distance, double *pred_azimuth);

// 关联测量数据和航迹
int tracker_associate_measurements(const Target *measurements, int meas_count);

// 获取跟踪状态
int tracker_get_track_quality(uint32_t target_id);

// 清理跟踪器
void tracker_cleanup(void);

#endif

