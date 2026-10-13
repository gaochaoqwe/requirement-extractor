/**
 * @file navigation_guidance.h
 * @brief 导航指引生成接口
 */

#ifndef NAVIGATION_GUIDANCE_H
#define NAVIGATION_GUIDANCE_H

#include "path_planner.h"

/**
 * @brief 生成导航指引
 * @param path 路径点数组
 * @param path_len 路径长度
 * @return 0表示成功，非0表示失败
 */
int generate_guidance(const PathPoint *path, int path_len);

#endif // NAVIGATION_GUIDANCE_H

