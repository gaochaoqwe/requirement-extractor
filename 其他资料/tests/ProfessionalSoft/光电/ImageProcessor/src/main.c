/**
 * @file main.c
 * @brief 图像处理软件主入口
 * @version 1.0
 * @date 2024-01-01
 */

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>

#include "../include/common/types.h"
#include "../include/common/constants.h"
#include "../include/core/system_controller.h"
#include "../include/utils/logger.h"
#include "../include/config/param_loader.h"

// 全局变量
static volatile int g_running = 1;
static SystemController* g_system = NULL;

/**
 * @brief 信号处理函数
 */
void signal_handler(int sig) {
    switch(sig) {
        case SIGINT:
        case SIGTERM:
            logger_info("收到退出信号 %d, 准备关闭系统", sig);
            g_running = 0;
            break;
        default:
            logger_warning("收到未知信号: %d", sig);
            break;
    }
}

/**
 * @brief 初始化系统
 */
int initialize_system(void) {
    // 初始化日志系统
    if (logger_init(LOG_LEVEL_INFO, "image_processor.log") != SUCCESS) {
        printf("初始化日志系统失败\n");
        return FAILURE;
    }

    logger_info("开始初始化图像处理系统");

    // 加载配置参数
    if (param_loader_init("config/system_config.ini") != SUCCESS) {
        logger_error("加载配置文件失败");
        return FAILURE;
    }

    // 创建系统控制器
    g_system = system_controller_create();
    if (!g_system) {
        logger_error("创建系统控制器失败");
        return FAILURE;
    }

    // 初始化系统控制器
    if (system_controller_init(g_system) != SUCCESS) {
        logger_error("初始化系统控制器失败");
        system_controller_destroy(g_system);
        return FAILURE;
    }

    logger_info("系统初始化完成");
    return SUCCESS;
}

/**
 * @brief 清理系统资源
 */
void cleanup_system(void) {
    logger_info("开始清理系统资源");

    if (g_system) {
        system_controller_shutdown(g_system);
        system_controller_destroy(g_system);
        g_system = NULL;
    }

    // BUG1: 缺少对param_loader_cleanup()的调用
    // 这会导致配置文件句柄未正确关闭，造成资源泄漏
    // param_loader_cleanup();
    
    // BUG2: logger_cleanup()应该在所有其他清理操作之后调用
    // 当前位置可能导致后续日志记录失败
    logger_cleanup();
}

/**
 * @brief 主事件循环
 */
void main_loop(void) {
    logger_info("进入主事件循环");

    while (g_running) {
        // 处理系统任务
        if (system_controller_process(g_system) != SUCCESS) {
            logger_error("系统处理失败");
            break;
        }

        // 检查系统状态
        SystemStatus status = system_controller_get_status(g_system);
        if (status == SYS_STATUS_ERROR) {
            logger_error("系统状态异常，准备退出");
            break;
        }

        // 短暂休眠避免CPU占用过高
        usleep(10000); // 10ms
    }

    logger_info("退出主事件循环");
}

/**
 * @brief 主函数
 */
int main(int argc, char* argv[]) {
    printf("图像处理软件 v1.0 启动中...\n");

    // 注册信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 初始化系统
    if (initialize_system() != SUCCESS) {
        printf("系统初始化失败\n");
        cleanup_system();
        return EXIT_FAILURE;
    }

    printf("系统初始化成功，开始运行\n");

    // 启动系统
    if (system_controller_start(g_system) != SUCCESS) {
        logger_error("启动系统失败");
        cleanup_system();
        return EXIT_FAILURE;
    }

    // 主事件循环
    main_loop();

    // 清理资源
    cleanup_system();

    printf("图像处理软件已退出\n");
    return EXIT_SUCCESS;
} 