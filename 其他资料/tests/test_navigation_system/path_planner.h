/**
 * @file path_planner.h
 * @brief 路径规划接口
 */

#ifndef PATH_PLANNER_H
#define PATH_PLANNER_H

#include "gps_receiver.h"

// 路径点结构
typedef struct {
    double latitude;
    double longitude;
    char instruction[128];  // 导航指令
    double distance;        // 到下一点的距离
} PathPoint;

/**
 * @brief 规划路径
 * @param start 起点GPS数据
 * @param dest 目标GPS坐标
 * @return 0表示成功，非0表示失败
 */
int plan_route(const GPSData *start, const GPSData *dest);

/**
 * @brief 重新规划路径
 * @param current 当前GPS数据
 * @return 0表示成功，非0表示失败
 */
int replan_route(const GPSData *current);

/**
 * @brief 检查路径偏离
 * @param current 当前GPS数据
 * @return 偏离距离（米）
 */
double check_path_deviation(const GPSData *current);

/**
 * @brief 发送位置更新
 * @param data GPS数据
 * @return 0表示成功，非0表示失败
 */
int send_position_update(const GPSData *data);

#endif // PATH_PLANNER_H

