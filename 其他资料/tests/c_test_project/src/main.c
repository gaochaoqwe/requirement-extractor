/**
 * @file main.c
 * @brief 嵌入式系统监控软件主程序
 * @version 1.0
 * @date 2023-06-04
 */

#include "../include/system_monitor.h"
#include "../include/config_manager.h"
#include "../include/data_collector.h"
#include "../include/data_analyzer.h"
#include "../include/logger.h"
#include "../include/event_handler.h"
#include "../include/utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>

/* 全局变量 */
static bool g_running = true;
static SystemConfig g_config;
static const char* CONFIG_FILE = "../config/system_monitor.conf";

/* 函数声明 */
static void signal_handler(int sig);
static void setup_signal_handlers(void);
static void monitor_loop(void);
static void print_usage(const char* program_name);
static void print_banner(void);

int main(int argc, char* argv[]) {
    /* 打印欢迎信息 */
    print_banner();
    
    /* 解析命令行参数 */
    const char* config_file = CONFIG_FILE;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return EXIT_SUCCESS;
        } else if (strcmp(argv[i], "--config") == 0 || strcmp(argv[i], "-c") == 0) {
            if (i + 1 < argc) {
                config_file = argv[++i];
            } else {
                fprintf(stderr, "错误: --config 选项需要一个参数\n");
                return EXIT_FAILURE;
            }
        }
    }
    
    /* 加载配置 */
    printf("加载配置文件: %s\n", config_file);
    if (load_config(config_file, &g_config) != SYSTEM_OK) {
        printf("无法加载配置文件，使用默认配置\n");
        set_default_config(&g_config);
    }
    
    /* 打印配置信息 */
    print_config(&g_config);
    
    /* 初始化系统 */
    printf("初始化系统监控...\n");
    if (initialize_system(&g_config) != SYSTEM_OK) {
        fprintf(stderr, "系统初始化失败\n");
        return EXIT_FAILURE;
    }
    
    /* 设置信号处理 */
    setup_signal_handlers();
    
    /* 主监控循环 */
    printf("系统监控已启动，按 Ctrl+C 退出\n\n");
    monitor_loop();
    
    /* 关闭系统 */
    printf("\n关闭系统监控...\n");
    shutdown_system();
    
    printf("系统监控已关闭\n");
    return EXIT_SUCCESS;
}

static void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        printf("\n收到终止信号，准备退出...\n");
        g_running = false;
    }
}

static void setup_signal_handlers(void) {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
}

static void monitor_loop(void) {
    SystemData data;
    SystemEvent event;
    
    while (g_running) {
        /* 采集系统数据 */
        if (collect_system_data(&data) != SYSTEM_OK) {
            fprintf(stderr, "数据采集失败\n");
            continue;
        }
        
        /* 分析系统数据 */
        if (analyze_system_data(&data, &event) != SYSTEM_OK) {
            fprintf(stderr, "数据分析失败\n");
            continue;
        }
        
        /* 处理系统事件 */
        handle_system_event(&event);
        
        /* 根据配置的采样率休眠 */
        usleep(g_config.sampling_rate_ms * 1000);
    }
}

static void print_usage(const char* program_name) {
    printf("用法: %s [选项]\n", program_name);
    printf("选项:\n");
    printf("  -h, --help            显示此帮助信息\n");
    printf("  -c, --config FILE     指定配置文件路径\n");
}

static void print_banner(void) {
    printf("\n");
    printf("==========================================================\n");
    printf("             嵌入式系统监控软件 v1.0                      \n");
    printf("==========================================================\n");
    printf("\n");
} 