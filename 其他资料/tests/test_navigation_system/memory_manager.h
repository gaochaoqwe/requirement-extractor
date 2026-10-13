/**
 * @file memory_manager.h
 * @brief 内存管理接口
 */

#ifndef MEMORY_MANAGER_H
#define MEMORY_MANAGER_H

#include <stddef.h>

#define GPS_BUFFER_SIZE (1024 * 10)     // 10KB GPS缓冲区
#define MAP_BUFFER_SIZE (1024 * 1024)   // 1MB 地图缓冲区
#define PATH_BUFFER_SIZE (1024 * 100)   // 100KB 路径缓冲区

/**
 * @brief 分配系统缓冲区
 * @return 0表示成功，非0表示失败
 */
int allocate_system_buffers(void);

/**
 * @brief 释放系统缓冲区
 */
void free_system_buffers(void);

/**
 * @brief 获取GPS缓冲区指针
 */
void* get_gps_buffer(void);

/**
 * @brief 获取地图缓冲区指针
 */
void* get_map_buffer(void);

/**
 * @brief 获取路径缓冲区指针
 */
void* get_path_buffer(void);

#endif // MEMORY_MANAGER_H

