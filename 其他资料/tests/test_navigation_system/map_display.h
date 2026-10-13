/**
 * @file map_display.h
 * @brief 地图显示接口
 */

#ifndef MAP_DISPLAY_H
#define MAP_DISPLAY_H

#include "gps_receiver.h"

/**
 * @brief 初始化地图显示
 * @return 0表示成功，非0表示失败
 */
int map_display_init(void);

/**
 * @brief 清理地图显示
 */
void map_display_cleanup(void);

/**
 * @brief 显示地图
 * @param current 当前GPS位置
 * @return 0表示成功，非0表示失败
 */
int display_map(const GPSData *current);

#endif // MAP_DISPLAY_H

