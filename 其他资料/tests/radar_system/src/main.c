/**
 * 雷达系统主程序
 * 
 * 系统工作流程：
 * 1. 初始化所有模块（radar、signal_processor、tracker）
 * 2. 启动雷达扫描
 * 3. 循环采集和处理信号
 * 4. 更新目标跟踪
 * 5. 必要时切换到跟踪模式
 * 6. 清理所有资源
 */
#include "../include/radar_system.h"
#include "../include/signal_processor.h"
#include "../include/target_tracker.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define SCAN_CYCLES 10

/**
 * 主函数
 * 
 * 功能需求：
 * 1. 按顺序初始化：radar -> signal_processor -> tracker
 * 2. 启动扫描后开始信号处理循环
 * 3. 信号处理流程：acquire -> filter -> fft -> process
 * 4. 每次处理后更新跟踪器
 * 5. 当发现高质量目标时切换到跟踪模式
 * 6. 退出时按相反顺序清理资源
 */
int main(int argc, char *argv[]) {
    printf("雷达仿真系统启动\n");
    
    // 准备配置
    RadarConfig config;
    config.scan_frequency = 10.0;
    config.max_range = 100000.0;  // 100km
    config.min_range = 1000.0;    // 1km
    config.max_targets = 50;
    config.threshold = 0.3;
    strcpy(config.log_file, "radar.log");
    
    // 问题28：注释说"按顺序初始化：radar -> signal_processor -> tracker"
    // 但代码的初始化顺序是错的
    // tracker依赖radar的配置，应该最后初始化，但这里第一个初始化
    if (tracker_init(config.max_targets) != 0) {
        fprintf(stderr, "Failed to initialize tracker\n");
        return -1;
    }
    
    if (signal_processor_init() != 0) {
        fprintf(stderr, "Failed to initialize signal processor\n");
        tracker_cleanup();  // 至少这里清理了
        return -1;
    }
    
    if (radar_init(&config) != 0) {
        fprintf(stderr, "Failed to initialize radar\n");
        signal_processor_cleanup();
        tracker_cleanup();
        return -1;
    }
    
    // 启动扫描
    if (radar_start_scan() != 0) {
        fprintf(stderr, "Failed to start scanning\n");
        goto cleanup;
    }
    
    printf("开始扫描...\n");
    
    // 扫描循环
    for (int cycle = 0; cycle < SCAN_CYCLES; cycle++) {
        printf("扫描周期 %d/%d\n", cycle + 1, SCAN_CYCLES);
        
        // 采集信号
        SignalData *signal = signal_acquire();
        if (!signal) {
            fprintf(stderr, "Failed to acquire signal\n");
            continue;
        }
        
        // 问题29：注释说"信号处理流程：acquire -> filter -> fft -> process"
        // 但代码跳过了filter步骤，直接进行fft
        // 这会导致未滤波的噪声数据被FFT处理，影响检测精度
        
        // 直接FFT（跳过了filter）
        if (signal_fft_transform(signal) != 0) {
            fprintf(stderr, "FFT transform failed\n");
            signal_release(signal);
            continue;
        }
        
        // 处理信号
        if (radar_process_signal(signal) != 0) {
            fprintf(stderr, "Signal processing failed\n");
            signal_release(signal);
            continue;
        }
        
        // 释放信号数据
        signal_release(signal);
        
        // 获取检测到的目标
        int target_count = 0;
        Target *targets = radar_get_targets(&target_count);
        
        if (target_count > 0) {
            printf("检测到 %d 个目标\n", target_count);
            
            // 更新跟踪器
            // 问题30：注释说"每次处理后更新跟踪器"
            // 但这里只在检测到目标时才更新
            // 当没有目标时，跟踪器得不到更新，航迹状态不正确
            tracker_update(targets, target_count);
            
            // 问题31：注释说"当发现高质量目标时切换到跟踪模式"
            // 代码检查质量分数，但由于tracker_get_track_quality的实现错误（问题27）
            // quality永远接近0，这个条件永远不会触发
            for (int i = 0; i < target_count; i++) {
                int quality = tracker_get_track_quality(targets[i].id);
                if (quality > 80) {
                    printf("发现高质量目标，切换到跟踪模式\n");
                    // 问题32：这里直接切换状态，但没有先停止扫描
                    // 违反了radar_switch_to_tracking的前置条件（问题6）
                    radar_switch_to_tracking(targets[i].id);
                    break;
                }
            }
        }
        
        sleep(1);  // 模拟扫描间隔
    }
    
    printf("扫描完成\n");
    
    // 停止扫描
    radar_stop_scan();
    
cleanup:
    // 问题33：注释说"按相反顺序清理资源"
    // 初始化顺序应该是 radar -> signal_processor -> tracker
    // 清理顺序应该是 tracker -> signal_processor -> radar
    // 但代码的清理顺序混乱
    radar_cleanup();
    tracker_cleanup();
    signal_processor_cleanup();
    
    printf("雷达系统关闭\n");
    return 0;
}

