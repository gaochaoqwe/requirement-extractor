/**
 * @file system_controller.c
 * @brief 系统控制器实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

#include "../../include/core/system_controller.h"
#include "../../include/core/image_manager.h"
#include "../../include/core/task_scheduler.h"
#include "../../include/acquisition/camera_driver.h"
#include "../../include/display/renderer.h"
#include "../../include/utils/logger.h"
#include "../../include/utils/memory_pool.h"
#include "../../include/config/settings_manager.h"

// 系统控制器结构
struct SystemController {
    SystemStatus status;
    ImageManager* image_mgr;
    TaskScheduler* task_scheduler;
    CameraDriver* camera;
    Renderer* renderer;
    MemoryPool* memory_pool;
    SettingsManager* settings;
    pthread_mutex_t status_mutex;
    bool initialized;
};

/**
 * @brief 创建系统控制器
 */
SystemController* system_controller_create(void) {
    SystemController* ctrl = malloc(sizeof(SystemController));
    if (!ctrl) {
        logger_error("分配系统控制器内存失败");
        return NULL;
    }

    memset(ctrl, 0, sizeof(SystemController));
    ctrl->status = SYS_STATUS_IDLE;
    ctrl->initialized = false;

    // 初始化状态锁
    if (pthread_mutex_init(&ctrl->status_mutex, NULL) != 0) {
        logger_error("初始化状态锁失败");
        free(ctrl);
        return NULL;
    }

    logger_info("系统控制器创建成功");
    return ctrl;
}

/**
 * @brief 初始化系统控制器
 */
ReturnCode system_controller_init(SystemController* ctrl) {
    if (!ctrl) {
        return ERROR_INVALID_PARAM;
    }

    logger_info("开始初始化系统控制器子模块");

    // 创建内存池
    ctrl->memory_pool = memory_pool_create(MEMORY_POOL_SIZE);
    if (!ctrl->memory_pool) {
        logger_error("创建内存池失败");
        return FAILURE;
    }

    // 创建设置管理器
    ctrl->settings = settings_manager_create();
    if (!ctrl->settings) {
        logger_error("创建设置管理器失败");
        return FAILURE;
    }

    // 创建任务调度器
    ctrl->task_scheduler = task_scheduler_create(MAX_TASK_QUEUE_SIZE);
    if (!ctrl->task_scheduler) {
        logger_error("创建任务调度器失败");
        return FAILURE;
    }

    // 创建图像管理器
    ctrl->image_mgr = image_manager_create(ctrl->memory_pool);
    if (!ctrl->image_mgr) {
        logger_error("创建图像管理器失败");
        return FAILURE;
    }

    // 创建相机驱动
    ctrl->camera = camera_driver_create();
    if (!ctrl->camera) {
        logger_error("创建相机驱动失败");
        return FAILURE;
    }

    // 创建渲染器
    ctrl->renderer = renderer_create();
    if (!ctrl->renderer) {
        logger_error("创建渲染器失败");
        return FAILURE;
    }

    // 初始化各个子模块
    if (task_scheduler_init(ctrl->task_scheduler) != SUCCESS) {
        logger_error("初始化任务调度器失败");
        return FAILURE;
    }

    if (image_manager_init(ctrl->image_mgr) != SUCCESS) {
        logger_error("初始化图像管理器失败");
        return FAILURE;
    }

    if (camera_driver_init(ctrl->camera, ctrl->settings) != SUCCESS) {
        logger_error("初始化相机驱动失败");
        return FAILURE;
    }

    if (renderer_init(ctrl->renderer, ctrl->settings) != SUCCESS) {
        logger_error("初始化渲染器失败");
        return FAILURE;
    }

    ctrl->initialized = true;
    logger_info("系统控制器初始化完成");
    return SUCCESS;
}

/**
 * @brief 启动系统
 */
ReturnCode system_controller_start(SystemController* ctrl) {
    if (!ctrl || !ctrl->initialized) {
        return ERROR_INVALID_PARAM;
    }

    pthread_mutex_lock(&ctrl->status_mutex);
    
    if (ctrl->status != SYS_STATUS_IDLE) {
        pthread_mutex_unlock(&ctrl->status_mutex);
        logger_warning("系统已经在运行中");
        return FAILURE;
    }

    // BUG3: 状态更新时机错误 - 应该在所有子系统成功启动后再更新状态
    // 当前位置可能导致状态不一致，影响系统稳定性
    ctrl->status = SYS_STATUS_RUNNING;

    // 启动相机
    if (camera_driver_start(ctrl->camera) != SUCCESS) {
        logger_error("启动相机失败");
        // BUG4: 错误处理时未恢复状态，系统会保持RUNNING状态但实际未运行
        pthread_mutex_unlock(&ctrl->status_mutex);
        return FAILURE;
    }

    // 启动任务调度器
    if (task_scheduler_start(ctrl->task_scheduler) != SUCCESS) {
        logger_error("启动任务调度器失败");
        camera_driver_stop(ctrl->camera);
        pthread_mutex_unlock(&ctrl->status_mutex);
        return FAILURE;
    }

    // 启动渲染器
    if (renderer_start(ctrl->renderer) != SUCCESS) {
        logger_error("启动渲染器失败");
        task_scheduler_stop(ctrl->task_scheduler);
        camera_driver_stop(ctrl->camera);
        pthread_mutex_unlock(&ctrl->status_mutex);
        return FAILURE;
    }

    pthread_mutex_unlock(&ctrl->status_mutex);

    logger_info("系统启动成功");
    return SUCCESS;
}

/**
 * @brief 处理系统任务
 */
ReturnCode system_controller_process(SystemController* ctrl) {
    if (!ctrl || !ctrl->initialized) {
        return ERROR_INVALID_PARAM;
    }

    // 处理图像采集
    ImageData* image = camera_driver_capture_frame(ctrl->camera);
    if (image) {
        // 将图像交给图像管理器处理
        if (image_manager_process_frame(ctrl->image_mgr, image) != SUCCESS) {
            logger_warning("图像处理失败");
        }

        // 显示图像
        if (renderer_display_image(ctrl->renderer, image) != SUCCESS) {
            logger_warning("图像显示失败");
        }
    }

    // 处理任务队列
    task_scheduler_process_tasks(ctrl->task_scheduler);

    return SUCCESS;
}

/**
 * @brief 获取系统状态
 */
SystemStatus system_controller_get_status(SystemController* ctrl) {
    if (!ctrl) {
        return SYS_STATUS_ERROR;
    }

    pthread_mutex_lock(&ctrl->status_mutex);
    SystemStatus status = ctrl->status;
    pthread_mutex_unlock(&ctrl->status_mutex);

    return status;
}

/**
 * @brief 关闭系统
 */
ReturnCode system_controller_shutdown(SystemController* ctrl) {
    if (!ctrl) {
        return ERROR_INVALID_PARAM;
    }

    logger_info("开始关闭系统");

    pthread_mutex_lock(&ctrl->status_mutex);
    ctrl->status = SYS_STATUS_SHUTDOWN;
    pthread_mutex_unlock(&ctrl->status_mutex);

    // 停止各个子模块
    if (ctrl->renderer) {
        renderer_stop(ctrl->renderer);
    }

    if (ctrl->task_scheduler) {
        task_scheduler_stop(ctrl->task_scheduler);
    }

    if (ctrl->camera) {
        camera_driver_stop(ctrl->camera);
    }

    logger_info("系统关闭完成");
    return SUCCESS;
}

/**
 * @brief 销毁系统控制器
 */
void system_controller_destroy(SystemController* ctrl) {
    if (!ctrl) {
        return;
    }

    // 销毁子模块
    if (ctrl->renderer) {
        renderer_destroy(ctrl->renderer);
    }

    if (ctrl->camera) {
        camera_driver_destroy(ctrl->camera);
    }

    if (ctrl->image_mgr) {
        image_manager_destroy(ctrl->image_mgr);
    }

    if (ctrl->task_scheduler) {
        task_scheduler_destroy(ctrl->task_scheduler);
    }

    if (ctrl->settings) {
        settings_manager_destroy(ctrl->settings);
    }

    if (ctrl->memory_pool) {
        memory_pool_destroy(ctrl->memory_pool);
    }

    pthread_mutex_destroy(&ctrl->status_mutex);
    free(ctrl);

    logger_info("系统控制器销毁完成");
} 