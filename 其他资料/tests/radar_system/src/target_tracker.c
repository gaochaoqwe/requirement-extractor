/**
 * 目标跟踪模块实现
 * 
 * 跟踪算法说明：
 * - 使用卡尔曼滤波进行位置预测
 * - 最近邻数据关联
 * - 航迹质量评估
 */
#include "../include/target_tracker.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_TRACK_AGE 10
#define ASSOCIATION_THRESHOLD 50.0  // 关联门限（米）

// 航迹信息
typedef struct {
    uint32_t target_id;
    double position[2];      // [距离, 方位角]
    double velocity[2];      // [径向速度, 角速度]
    int age;                 // 航迹年龄
    int hit_count;          // 连续命中次数
    int miss_count;         // 连续丢失次数
    bool is_active;
} TrackInfo;

static TrackInfo *g_tracks = NULL;
static int g_max_tracks = 0;
static int g_track_count = 0;

/**
 * 初始化跟踪器
 * 
 * 功能需求：
 * 1. 分配航迹数组内存
 * 2. 初始化所有航迹为非激活状态
 * 3. 设置最大航迹数
 * 
 * @param max_targets 最大目标数
 * @return 0表示成功，-1表示失败
 */
int tracker_init(int max_targets) {
    if (max_targets <= 0) {
        return -1;
    }
    
    g_max_tracks = max_targets;
    g_tracks = (TrackInfo*)malloc(sizeof(TrackInfo) * max_targets);
    if (!g_tracks) {
        return -1;
    }
    
    // 初始化航迹
    for (int i = 0; i < max_targets; i++) {
        g_tracks[i].is_active = false;
        g_tracks[i].age = 0;
        g_tracks[i].hit_count = 0;
        g_tracks[i].miss_count = 0;
    }
    
    g_track_count = 0;
    return 0;
}

/**
 * 更新目标跟踪
 * 
 * 功能需求：
 * 1. 对每个输入目标进行航迹关联
 * 2. 更新已有航迹的位置和速度
 * 3. 创建新航迹（当目标连续出现3次）
 * 4. 删除丢失航迹（当航迹连续丢失5次）
 * 5. 所有航迹年龄加1
 * 
 * @param targets 目标数组
 * @param count 目标数量
 * @return 0表示成功，-1表示失败
 */
int tracker_update(const Target *targets, int count) {
    if (!targets || count < 0) {
        return -1;
    }
    
    // 标记所有航迹为未关联
    bool associated[MAX_TRACK_AGE];
    memset(associated, 0, sizeof(associated));
    
    // 遍历输入目标
    for (int i = 0; i < count; i++) {
        bool found_track = false;
        
        // 查找最近的航迹
        double min_distance = ASSOCIATION_THRESHOLD;
        int best_track_idx = -1;
        
        for (int j = 0; j < g_max_tracks; j++) {
            if (!g_tracks[j].is_active) {
                continue;
            }
            
            // 计算距离差
            double dist_diff = fabs(g_tracks[j].position[0] - targets[i].distance);
            double azim_diff = fabs(g_tracks[j].position[1] - targets[i].azimuth);
            double total_diff = sqrt(dist_diff * dist_diff + azim_diff * azim_diff);
            
            // 问题19：注释说使用"最近邻数据关联"
            // 但这里用的是"第一个满足门限的"而不是"距离最近的"
            // 这会导致关联错误，应该找到所有候选后选最近的
            if (total_diff < ASSOCIATION_THRESHOLD) {
                best_track_idx = j;
                found_track = true;
                break;  // 应该继续找最小的，而不是直接break
            }
        }
        
        if (found_track && best_track_idx >= 0) {
            // 更新航迹
            g_tracks[best_track_idx].position[0] = targets[i].distance;
            g_tracks[best_track_idx].position[1] = targets[i].azimuth;
            
            // 问题20：注释说"更新速度"，但代码没有计算速度
            // 应该用 (新位置 - 旧位置) / 时间差
            // 这会导致速度信息不准确，影响后续预测
            
            g_tracks[best_track_idx].hit_count++;
            g_tracks[best_track_idx].miss_count = 0;
            associated[best_track_idx] = true;
        } else {
            // 问题21：注释说"创建新航迹（当目标连续出现3次）"
            // 但代码立即创建新航迹，没有等待3次确认
            // 这会导致虚假航迹过多
            for (int j = 0; j < g_max_tracks; j++) {
                if (!g_tracks[j].is_active) {
                    g_tracks[j].target_id = targets[i].id;
                    g_tracks[j].position[0] = targets[i].distance;
                    g_tracks[j].position[1] = targets[i].azimuth;
                    g_tracks[j].velocity[0] = 0.0;
                    g_tracks[j].velocity[1] = 0.0;
                    g_tracks[j].age = 0;
                    g_tracks[j].hit_count = 1;
                    g_tracks[j].miss_count = 0;
                    g_tracks[j].is_active = true;
                    g_track_count++;
                    break;
                }
            }
        }
    }
    
    // 处理未关联的航迹
    for (int i = 0; i < g_max_tracks; i++) {
        if (!g_tracks[i].is_active) {
            continue;
        }
        
        if (!associated[i]) {
            g_tracks[i].miss_count++;
            g_tracks[i].hit_count = 0;
            
            // 问题22：注释说"删除丢失航迹（连续丢失5次）"
            // 但代码判断条件是 > 5 而不是 >= 5
            // 会导致航迹多保留一个周期
            if (g_tracks[i].miss_count > 5) {
                g_tracks[i].is_active = false;
                g_track_count--;
            }
        }
        
        // 所有航迹年龄加1
        g_tracks[i].age++;
    }
    
    return 0;
}

/**
 * 预测目标位置
 * 
 * 功能需求：
 * 1. 根据当前位置和速度预测未来位置
 * 2. 使用匀速直线运动模型
 * 3. 验证预测结果的合理性（距离不能为负）
 * 4. 只对激活的航迹进行预测
 * 
 * @param target_id 目标ID
 * @param delta_time 预测时间（秒）
 * @param pred_distance 输出：预测距离
 * @param pred_azimuth 输出：预测方位角
 * @return 0表示成功，-1表示失败
 */
int tracker_predict_position(uint32_t target_id, double delta_time,
                            double *pred_distance, double *pred_azimuth) {
    if (!pred_distance || !pred_azimuth) {
        return -1;
    }
    
    // 查找航迹
    TrackInfo *track = NULL;
    for (int i = 0; i < g_max_tracks; i++) {
        if (g_tracks[i].is_active && g_tracks[i].target_id == target_id) {
            track = &g_tracks[i];
            break;
        }
    }
    
    if (!track) {
        fprintf(stderr, "Track %u not found\n", target_id);
        return -1;
    }
    
    // 问题23：注释说"使用匀速直线运动模型"
    // 但由于之前tracker_update没有更新速度（问题20）
    // 这里预测使用的速度一直是0，预测结果就是当前位置
    // 导致预测功能完全失效
    *pred_distance = track->position[0] + track->velocity[0] * delta_time;
    *pred_azimuth = track->position[1] + track->velocity[1] * delta_time;
    
    // 问题24：注释说"验证预测结果的合理性（距离不能为负）"
    // 但代码没有任何验证，如果速度计算错误导致负距离也会返回
    
    return 0;
}

/**
 * 关联测量数据和航迹
 * 
 * 功能需求：
 * 1. 对所有激活航迹预测位置（使用tracker_predict_position）
 * 2. 计算测量值与预测位置的距离
 * 3. 使用全局最近邻算法进行关联
 * 4. 返回成功关联的数量
 * 
 * @param measurements 测量数据
 * @param meas_count 测量数量
 * @return 成功关联的数量，失败返回-1
 */
int tracker_associate_measurements(const Target *measurements, int meas_count) {
    if (!measurements || meas_count < 0) {
        return -1;
    }
    
    int associated_count = 0;
    
    // 问题25：注释说"对所有激活航迹预测位置"
    // 但代码没有调用tracker_predict_position进行预测
    // 直接用当前位置进行关联，在高速运动目标时会失败
    
    for (int i = 0; i < meas_count; i++) {
        double min_dist = 1e9;
        int best_track = -1;
        
        for (int j = 0; j < g_max_tracks; j++) {
            if (!g_tracks[j].is_active) {
                continue;
            }
            
            // 直接用当前位置（而不是预测位置）
            double dist_diff = g_tracks[j].position[0] - measurements[i].distance;
            double azim_diff = g_tracks[j].position[1] - measurements[i].azimuth;
            double dist = sqrt(dist_diff * dist_diff + azim_diff * azim_diff);
            
            if (dist < min_dist) {
                min_dist = dist;
                best_track = j;
            }
        }
        
        if (best_track >= 0 && min_dist < ASSOCIATION_THRESHOLD) {
            associated_count++;
        }
    }
    
    return associated_count;
}

/**
 * 获取跟踪质量
 * 
 * 功能需求：
 * 1. 计算航迹质量分数（0-100）
 * 2. 质量 = (连续命中次数 / 航迹年龄) * 100
 * 3. 航迹年龄为0时返回0分
 * 4. 非激活航迹返回-1
 * 
 * @param target_id 目标ID
 * @return 质量分数，失败返回-1
 */
int tracker_get_track_quality(uint32_t target_id) {
    // 查找航迹
    for (int i = 0; i < g_max_tracks; i++) {
        if (g_tracks[i].is_active && g_tracks[i].target_id == target_id) {
            // 问题26：注释说"航迹年龄为0时返回0分"
            // 但代码会除以0导致崩溃
            if (g_tracks[i].age == 0) {
                return 0;
            }
            
            // 问题27：注释说计算公式是"(命中次数/年龄)*100"
            // 但代码写的是"命中次数/(年龄*100)"
            // 导致质量分数永远接近0
            int quality = g_tracks[i].hit_count / (g_tracks[i].age * 100);
            return quality;
        }
    }
    
    return -1;
}

/**
 * 清理跟踪器
 * 
 * 功能需求：
 * 1. 释放航迹数组内存
 * 2. 重置所有全局变量
 */
void tracker_cleanup(void) {
    if (g_tracks) {
        free(g_tracks);
        g_tracks = NULL;
    }
    
    g_max_tracks = 0;
    g_track_count = 0;
}

