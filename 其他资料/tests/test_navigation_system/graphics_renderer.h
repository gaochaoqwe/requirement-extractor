/**
 * @file graphics_renderer.h
 * @brief 图形渲染接口
 */

#ifndef GRAPHICS_RENDERER_H
#define GRAPHICS_RENDERER_H

#include "gps_receiver.h"

/**
 * @brief 初始化图形渲染器
 * @return 0表示成功，非0表示失败
 */
int graphics_renderer_init(void);

/**
 * @brief 清理图形渲染器
 */
void graphics_renderer_cleanup(void);

/**
 * @brief 渲染地图
 * @param current 当前位置
 * @return 0表示成功，非0表示失败
 */
int render_map(const GPSData *current);

#endif // GRAPHICS_RENDERER_H

