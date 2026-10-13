/**
 * @file memory_manager.c
 * @brief 内存管理实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "memory_manager.h"
#include "logger.h"

// 全局缓冲区指针
static void *gps_buffer = NULL;
static void *map_buffer = NULL;
static void *path_buffer = NULL;

/**
 * @brief 分配系统缓冲区
 */
int allocate_system_buffers(void) {
    // 分配GPS缓冲区
    gps_buffer = malloc(GPS_BUFFER_SIZE);
    if (gps_buffer == NULL) {
        log_message(LOG_ERROR, "Failed to allocate GPS buffer");
        return -1;  // 问题：没有释放已分配的内存
    }
    memset(gps_buffer, 0, GPS_BUFFER_SIZE);
    log_message(LOG_DEBUG, "GPS buffer allocated: %d bytes", GPS_BUFFER_SIZE);
    
    // 分配地图缓冲区
    map_buffer = malloc(MAP_BUFFER_SIZE);
    if (map_buffer == NULL) {
        log_message(LOG_ERROR, "Failed to allocate map buffer");
        return -1;  // 问题：内存泄漏，没有释放gps_buffer
    }
    memset(map_buffer, 0, MAP_BUFFER_SIZE);
    log_message(LOG_DEBUG, "Map buffer allocated: %d bytes", MAP_BUFFER_SIZE);
    
    // 分配路径缓冲区
    path_buffer = malloc(PATH_BUFFER_SIZE);
    if (path_buffer == NULL) {
        log_message(LOG_ERROR, "Failed to allocate path buffer");
        return -1;  // 问题：内存泄漏，没有释放前面的缓冲区
    }
    memset(path_buffer, 0, PATH_BUFFER_SIZE);
    log_message(LOG_DEBUG, "Path buffer allocated: %d bytes", PATH_BUFFER_SIZE);
    
    log_message(LOG_INFO, "All system buffers allocated successfully");
    return 0;
}

/**
 * @brief 释放系统缓冲区
 */
void free_system_buffers(void) {
    if (gps_buffer) {
        free(gps_buffer);
        gps_buffer = NULL;
    }
    
    if (map_buffer) {
        free(map_buffer);
        map_buffer = NULL;
    }
    
    if (path_buffer) {
        free(path_buffer);
        path_buffer = NULL;
    }
    
    log_message(LOG_INFO, "System buffers freed");
}

/**
 * @brief 获取GPS缓冲区指针
 */
void* get_gps_buffer(void) {
    return gps_buffer;
}

/**
 * @brief 获取地图缓冲区指针
 */
void* get_map_buffer(void) {
    return map_buffer;
}

/**
 * @brief 获取路径缓冲区指针
 */
void* get_path_buffer(void) {
    return path_buffer;
}

