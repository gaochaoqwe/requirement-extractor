/**
 * @file main.c
 * @brief 智能导航系统主程序
 * @author Navigation Team
 * @date 2025-01-22
 */

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include "system_init.h"
#include "gps_receiver.h"
#include "path_planner.h"
#include "map_display.h"
#include "comm_manager.h"
#include "logger.h"

// 全局状态标志
static volatile int system_running = 1;

/**
 * @brief 信号处理函数
 * @param sig 信号编号
 */
void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        printf("Received termination signal, shutting down...\n");
        system_running = 0;
    }
}

/**
 * @brief 主函数 - 系统入口
 * @return 0表示成功，非0表示失败
 */
int main(int argc, char *argv[]) {
    int ret;
    
    // 注册信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    printf("========================================\n");
    printf("Smart Navigation System v1.0\n");
    printf("========================================\n");
    
    // 【功能1】系统初始化
    log_message(LOG_INFO, "Starting system initialization...");
    ret = system_initialize();
    if (ret != 0) {
        log_message(LOG_ERROR, "System initialization failed with code: %d", ret);
        return -1;
    }
    log_message(LOG_INFO, "System initialization completed successfully");
    
    // 【功能2】启动GPS接收
    log_message(LOG_INFO, "Starting GPS receiver...");
    ret = gps_receiver_start();
    if (ret != 0) {
        log_message(LOG_ERROR, "GPS receiver start failed");
        goto cleanup;
    }
    
    // 【功能4】初始化地图显示
    log_message(LOG_INFO, "Initializing map display...");
    ret = map_display_init();
    if (ret != 0) {
        log_message(LOG_ERROR, "Map display initialization failed");
        goto cleanup;
    }
    
    // 【功能5】初始化通信模块
    log_message(LOG_INFO, "Initializing communication module...");
    ret = comm_initialize();
    if (ret != 0) {
        log_message(LOG_WARNING, "Communication initialization failed, running in offline mode");
        // 不退出，继续以离线模式运行
    }
    
    log_message(LOG_INFO, "All modules initialized, entering main loop");
    
    // 主循环
    int loop_count = 0;
    while (system_running) {
        // 【功能2】接收GPS数据
        GPSData gps_data;
        ret = gps_receive_data(&gps_data);
        if (ret == 0 && gps_data.valid) {
            // GPS数据有效，更新显示
            update_current_position(&gps_data);
            
            // 【功能3】检查是否需要重新规划路径
            if (check_path_deviation(&gps_data) > 100.0) {
                log_message(LOG_WARNING, "Path deviation detected, replanning...");
                ret = replan_route(&gps_data);
                if (ret != 0) {
                    log_message(LOG_ERROR, "Route replanning failed");
                }
            }
            
            // 【功能4】更新地图显示
            display_map(&gps_data);
            
            // 【功能5】上传位置数据（每10次循环上传一次）
            if (loop_count % 10 == 0) {
                send_position_update(&gps_data);
            }
        } else {
            log_message(LOG_WARNING, "GPS data invalid or unavailable");
        }
        
        // 问题：这里没有sleep，会导致CPU占用过高
        loop_count++;
    }
    
cleanup:
    log_message(LOG_INFO, "Shutting down system...");
    
    // 清理资源
    gps_receiver_stop();
    map_display_cleanup();
    comm_shutdown();
    system_cleanup();
    
    log_message(LOG_INFO, "System shutdown complete");
    printf("Thank you for using Smart Navigation System!\n");
    
    return 0;
}

