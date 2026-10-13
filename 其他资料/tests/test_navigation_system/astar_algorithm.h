/**
 * @file astar_algorithm.h
 * @brief A*路径搜索算法接口
 */

#ifndef ASTAR_ALGORITHM_H
#define ASTAR_ALGORITHM_H

#include "gps_receiver.h"
#include "path_planner.h"

/**
 * @brief A*搜索算法
 * @param start 起点
 * @param goal 终点
 * @param path 输出路径（需要调用者释放）
 * @param path_len 路径长度
 * @return 0表示成功，非0表示失败
 */
int astar_search(const GPSData *start, const GPSData *goal, 
                 PathPoint **path, int *path_len);

/**
 * @brief 计算启发式值（h值）
 * @param current 当前点
 * @param goal 目标点
 * @return 启发式值
 */
double calculate_heuristic(const GPSData *current, const GPSData *goal);

#endif // ASTAR_ALGORITHM_H

