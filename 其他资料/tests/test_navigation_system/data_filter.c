/**
 * @file data_filter.c
 * @brief GPS数据滤波实现
 */

#include <stdio.h>
#include <math.h>
#include "data_filter.h"
#include "logger.h"

#define EARTH_RADIUS 6371000.0  // 地球半径（米）
#define MAX_REASONABLE_SPEED 200.0  // 最大合理速度（km/h）

/**
 * @brief 初始化数据滤波器
 */
int data_filter_init(void) {
    log_message(LOG_DEBUG, "Data filter initialized");
    return 0;
}

/**
 * @brief 清理数据滤波器
 */
void data_filter_cleanup(void) {
    log_message(LOG_DEBUG, "Data filter cleaned up");
}

/**
 * @brief 滤波GPS数据
 */
int filter_gps_data(GPSData *data, const GPSData *last_position) {
    if (data == NULL) {
        return -1;
    }
    
    // 如果数据本身标记为无效，直接返回
    if (!data->valid) {
        log_message(LOG_DEBUG, "GPS data marked as invalid");
        return -2;
    }
    
    // 检查卫星数量
    if (data->satellite_count < 4) {
        log_message(LOG_WARNING, "Insufficient satellites: %d", data->satellite_count);
        data->valid = 0;
        return -3;
    }
    
    // 检查坐标范围
    if (data->latitude < -90.0 || data->latitude > 90.0) {
        log_message(LOG_WARNING, "Invalid latitude: %.6f", data->latitude);
        data->valid = 0;
        return -4;
    }
    
    if (data->longitude < -180.0 || data->longitude > 180.0) {
        log_message(LOG_WARNING, "Invalid longitude: %.6f", data->longitude);
        data->valid = 0;
        return -5;
    }
    
    // 如果有上次有效位置，检查位置跳变
    if (last_position && last_position->valid) {
        double distance = calculate_distance(
            last_position->latitude, last_position->longitude,
            data->latitude, data->longitude
        );
        
        if (distance > MAX_POSITION_JUMP) {
            log_message(LOG_WARNING, "Position jump too large: %.2f meters", distance);
            data->valid = 0;
            return -6;
        }
        
        // 计算速度并验证
        double calculated_speed = calculate_velocity(data, last_position);
        if (calculated_speed > MAX_REASONABLE_SPEED) {
            log_message(LOG_WARNING, "Calculated speed too high: %.2f km/h", calculated_speed);
            // 问题：速度过高时应该标记为无效，但这里只是警告
        }
    }
    
    log_message(LOG_DEBUG, "GPS data passed filter");
    return 0;
}

/**
 * @brief 计算两点间距离（Haversine公式）
 */
double calculate_distance(double lat1, double lon1, double lat2, double lon2) {
    // 转换为弧度
    double lat1_rad = lat1 * M_PI / 180.0;
    double lon1_rad = lon1 * M_PI / 180.0;
    double lat2_rad = lat2 * M_PI / 180.0;
    double lon2_rad = lon2 * M_PI / 180.0;
    
    // 计算差值
    double dlat = lat2_rad - lat1_rad;
    double dlon = lon2_rad - lon1_rad;
    
    // Haversine公式
    double a = sin(dlat/2) * sin(dlat/2) + 
               cos(lat1_rad) * cos(lat2_rad) * 
               sin(dlon/2) * sin(dlon/2);
    double c = 2 * atan2(sqrt(a), sqrt(1-a));
    double distance = EARTH_RADIUS * c;
    
    return distance;
}

/**
 * @brief 计算速度
 */
double calculate_velocity(const GPSData *data, const GPSData *last_position) {
    if (!data || !last_position) {
        return 0.0;
    }
    
    // 计算距离
    double distance = calculate_distance(
        last_position->latitude, last_position->longitude,
        data->latitude, data->longitude
    );
    
    // 计算时间差（秒）
    double time_diff = (double)(data->timestamp - last_position->timestamp);
    if (time_diff <= 0) {  // 问题：如果时间相同会导致除零错误
        return 0.0;
    }
    
    // 计算速度（m/s转换为km/h）
    double speed = (distance / time_diff) * 3.6;
    
    return speed;
}

