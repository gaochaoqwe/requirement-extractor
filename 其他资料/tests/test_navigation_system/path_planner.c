/**
 * @file path_planner.c
 * @brief 路径规划实现
 */

#include <stdio.h>
#include <string.h>
#include <math.h>
#include "path_planner.h"
#include "astar_algorithm.h"
#include "road_network.h"
#include "navigation_guidance.h"
#include "logger.h"

static PathPoint *current_path = NULL;
static int path_length = 0;
static GPSData destination;

/**
 * @brief 规划路径
 */
int plan_route(const GPSData *start, const GPSData *dest) {
    int ret;
    
    if (start == NULL || dest == NULL) {
        log_message(LOG_ERROR, "Invalid start or destination");
        return -1;
    }
    
    log_message(LOG_INFO, "Planning route from (%.6f,%.6f) to (%.6f,%.6f)",
               start->latitude, start->longitude,
               dest->latitude, dest->longitude);
    
    // 加载道路网络
    ret = load_road_network();
    if (ret != 0) {
        log_message(LOG_ERROR, "Failed to load road network");
        return -2;
    }
    
    // 使用A*算法计算路径
    ret = astar_search(start, dest, &current_path, &path_length);
    if (ret != 0) {
        log_message(LOG_ERROR, "A* search failed");
        return -3;
    }
    
    if (path_length == 0) {
        log_message(LOG_WARNING, "No path found");
        return -4;
    }
    
    // 生成导航指引
    ret = generate_guidance(current_path, path_length);
    if (ret != 0) {
        log_message(LOG_WARNING, "Failed to generate guidance");
    }
    
    // 保存目标点
    memcpy(&destination, dest, sizeof(GPSData));
    
    log_message(LOG_INFO, "Route planned successfully, %d waypoints", path_length);
    return 0;
}

/**
 * @brief 重新规划路径
 */
int replan_route(const GPSData *current) {
    log_message(LOG_INFO, "Replanning route from current position");
    return plan_route(current, &destination);
}

/**
 * @brief 检查路径偏离
 */
double check_path_deviation(const GPSData *current) {
    if (current_path == NULL || path_length == 0) {
        return 0.0;  // 没有规划路径
    }
    
    // 简化版：只检查与第一个路径点的距离
    // 问题：应该检查与最近路径点的距离，而不是第一个
    double deviation = calculate_distance(
        current->latitude, current->longitude,
        current_path[0].latitude, current_path[0].longitude
    );
    
    if (deviation > 100.0) {
        log_message(LOG_WARNING, "Path deviation: %.2f meters", deviation);
    }
    
    return deviation;
}

/**
 * @brief 计算距离（简化版）
 */
static double calculate_distance(double lat1, double lon1, double lat2, double lon2) {
    double dlat = (lat2 - lat1) * 111000;  // 简化：1度纬度约111km
    double dlon = (lon2 - lon1) * 111000 * cos(lat1 * M_PI / 180.0);
    return sqrt(dlat*dlat + dlon*dlon);
}

/**
 * @brief 发送位置更新
 */
int send_position_update(const GPSData *data) {
    // 实际应调用通信模块
    log_message(LOG_DEBUG, "Sending position update: (%.6f, %.6f)",
               data->latitude, data->longitude);
    return 0;
}

