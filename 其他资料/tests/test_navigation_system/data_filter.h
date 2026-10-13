/**
 * @file data_filter.h
 * @brief GPS数据滤波接口
 */

#ifndef DATA_FILTER_H
#define DATA_FILTER_H

#include "gps_receiver.h"

#define MAX_POSITION_JUMP 500.0  // 最大位置跳变（米）

/**
 * @brief 初始化数据滤波器
 * @return 0表示成功，非0表示失败
 */
int data_filter_init(void);

/**
 * @brief 清理数据滤波器
 */
void data_filter_cleanup(void);

/**
 * @brief 滤波GPS数据
 * @param data 当前GPS数据
 * @param last_position 上次有效位置
 * @return 0表示数据有效，非0表示数据异常
 */
int filter_gps_data(GPSData *data, const GPSData *last_position);

/**
 * @brief 计算两点间距离（米）
 * @param lat1 点1纬度
 * @param lon1 点1经度
 * @param lat2 点2纬度
 * @param lon2 点2经度
 * @return 距离（米）
 */
double calculate_distance(double lat1, double lon1, double lat2, double lon2);

/**
 * @brief 计算速度（基于位置变化）
 * @param data 当前GPS数据
 * @param last_position 上次位置
 * @return 速度（km/h）
 */
double calculate_velocity(const GPSData *data, const GPSData *last_position);

#endif // DATA_FILTER_H

