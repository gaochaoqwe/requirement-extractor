/**
 * @file map_display.c
 * @brief 地图显示实现
 */

#include <stdio.h>
#include "map_display.h"
#include "map_loader.h"
#include "graphics_renderer.h"
#include "display_buffer.h"
#include "logger.h"

/**
 * @brief 初始化地图显示
 */
int map_display_init(void) {
    int ret;
    
    log_message(LOG_INFO, "Initializing map display");
    
    // 初始化显示缓冲区
    ret = display_buffer_init();
    if (ret != 0) {
        log_message(LOG_ERROR, "Display buffer init failed");
        return -1;
    }
    
    // 初始化图形渲染器
    ret = graphics_renderer_init();
    if (ret != 0) {
        log_message(LOG_ERROR, "Graphics renderer init failed");
        return -2;
    }
    
    log_message(LOG_INFO, "Map display initialized successfully");
    return 0;
}

/**
 * @brief 清理地图显示
 */
void map_display_cleanup(void) {
    log_message(LOG_INFO, "Cleaning up map display");
    graphics_renderer_cleanup();
    display_buffer_cleanup();
}

/**
 * @brief 显示地图
 */
int display_map(const GPSData *current) {
    int ret;
    
    if (current == NULL || !current->valid) {
        log_message(LOG_WARNING, "Invalid GPS data for display");
        return -1;
    }
    
    // 加载地图瓦片
    ret = load_map_tiles(current->latitude, current->longitude);
    if (ret != 0) {
        log_message(LOG_WARNING, "Failed to load map tiles");
        // 问题：加载失败时是否应该继续渲染？
    }
    
    // 渲染地图
    ret = render_map(current);
    if (ret != 0) {
        log_message(LOG_ERROR, "Map rendering failed");
        return -2;
    }
    
    // 更新显示缓冲区
    ret = update_display_buffer();
    if (ret != 0) {
        log_message(LOG_ERROR, "Display buffer update failed");
        return -3;
    }
    
    return 0;
}

