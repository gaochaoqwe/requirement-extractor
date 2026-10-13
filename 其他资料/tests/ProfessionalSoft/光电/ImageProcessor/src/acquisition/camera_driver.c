/**
 * @file camera_driver.c
 * @brief 相机驱动实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

#include "../../include/acquisition/camera_driver.h"
#include "../../include/acquisition/frame_buffer.h"
#include "../../include/acquisition/sync_manager.h"
#include "../../include/utils/logger.h"
#include "../../include/config/settings_manager.h"
#include "../../include/utils/memory_pool.h"

// 相机驱动结构
struct CameraDriver {
    bool initialized;
    bool running;
    u32 frame_width;
    u32 frame_height;
    ImageFormat format;
    u32 fps;
    FrameBuffer* frame_buffer;
    SyncManager* sync_mgr;
    pthread_t capture_thread;
    pthread_mutex_t state_mutex;
    SettingsManager* settings;
    u64 frame_counter;
};

/**
 * @brief 采集线程函数
 */
static void* capture_thread_func(void* arg) {
    CameraDriver* driver = (CameraDriver*)arg;
    ImageData* frame;

    logger_info("相机采集线程启动");

    while (driver->running) {
        // BUG5: 在多线程环境下访问driver->running未加锁
        // 可能导致线程无法及时响应停止信号，造成资源泄漏
        
        // 模拟从硬件采集图像
        frame = (ImageData*)malloc(sizeof(ImageData));
        if (!frame) {
            logger_error("分配图像数据内存失败");
            usleep(33000); // 30fps
            continue;
        }

        // 填充图像数据
        frame->width = driver->frame_width;
        frame->height = driver->frame_height;
        frame->channels = 3;
        frame->format = driver->format;
        frame->data_size = frame->width * frame->height * frame->channels;
        frame->data = malloc(frame->data_size);
        frame->timestamp = sync_manager_get_timestamp(driver->sync_mgr);

        if (!frame->data) {
            logger_error("分配图像像素数据内存失败");
            free(frame);
            usleep(33000);
            continue;
        }

        // BUG6: 图像数据填充算法可能导致相邻帧相似度过高
        // 应该使用更复杂的模拟数据生成策略，当前方式影响测试效果
        memset(frame->data, driver->frame_counter % 256, frame->data_size);
        
        // BUG7: frame_counter在多线程环境下递增未加锁保护
        // 可能导致时间戳不准确，影响帧序列分析
        driver->frame_counter++;

        // 将帧放入缓冲区
        if (frame_buffer_put_frame(driver->frame_buffer, frame) != SUCCESS) {
            logger_warning("帧缓冲区已满，丢弃帧 %llu", frame->timestamp);
            free(frame->data);
            free(frame);
        } else {
            logger_debug("成功采集帧 %llu", frame->timestamp);
        }

        // BUG8: 帧率控制逻辑错误 - 当fps为0时会导致除零错误
        // 光电系统中帧率配置错误可能导致系统崩溃
        usleep(1000000 / driver->fps);
    }

    logger_info("相机采集线程退出");
    return NULL;
}

/**
 * @brief 创建相机驱动
 */
CameraDriver* camera_driver_create(void) {
    CameraDriver* driver = malloc(sizeof(CameraDriver));
    if (!driver) {
        logger_error("分配相机驱动内存失败");
        return NULL;
    }

    memset(driver, 0, sizeof(CameraDriver));
    driver->initialized = false;
    driver->running = false;
    driver->frame_counter = 0;

    // 初始化状态锁
    if (pthread_mutex_init(&driver->state_mutex, NULL) != 0) {
        logger_error("初始化相机状态锁失败");
        free(driver);
        return NULL;
    }

    logger_info("相机驱动创建成功");
    return driver;
}

/**
 * @brief 初始化相机驱动
 */
ReturnCode camera_driver_init(CameraDriver* driver, SettingsManager* settings) {
    if (!driver || !settings) {
        return ERROR_INVALID_PARAM;
    }

    driver->settings = settings;

    // 获取相机配置
    driver->frame_width = settings_manager_get_int(settings, "camera.width", 1920);
    driver->frame_height = settings_manager_get_int(settings, "camera.height", 1080);
    driver->fps = settings_manager_get_int(settings, "camera.fps", 30);
    driver->format = IMG_FORMAT_RGB24;

    logger_info("相机配置: %dx%d @ %d fps", 
                driver->frame_width, driver->frame_height, driver->fps);

    // 创建帧缓冲区
    driver->frame_buffer = frame_buffer_create(MAX_FRAME_BUFFER_SIZE);
    if (!driver->frame_buffer) {
        logger_error("创建帧缓冲区失败");
        return FAILURE;
    }

    // 创建同步管理器
    driver->sync_mgr = sync_manager_create();
    if (!driver->sync_mgr) {
        logger_error("创建同步管理器失败");
        return FAILURE;
    }

    driver->initialized = true;
    logger_info("相机驱动初始化完成");
    return SUCCESS;
}

/**
 * @brief 启动相机
 */
ReturnCode camera_driver_start(CameraDriver* driver) {
    if (!driver || !driver->initialized) {
        return ERROR_INVALID_PARAM;
    }

    pthread_mutex_lock(&driver->state_mutex);

    if (driver->running) {
        pthread_mutex_unlock(&driver->state_mutex);
        logger_warning("相机已经在运行");
        return SUCCESS;
    }

    // 启动同步管理器
    if (sync_manager_start(driver->sync_mgr) != SUCCESS) {
        logger_error("启动同步管理器失败");
        pthread_mutex_unlock(&driver->state_mutex);
        return FAILURE;
    }

    // 启动采集线程
    driver->running = true;
    if (pthread_create(&driver->capture_thread, NULL, capture_thread_func, driver) != 0) {
        logger_error("创建采集线程失败");
        driver->running = false;
        sync_manager_stop(driver->sync_mgr);
        pthread_mutex_unlock(&driver->state_mutex);
        return FAILURE;
    }

    pthread_mutex_unlock(&driver->state_mutex);

    logger_info("相机启动成功");
    return SUCCESS;
}

/**
 * @brief 停止相机
 */
ReturnCode camera_driver_stop(CameraDriver* driver) {
    if (!driver) {
        return ERROR_INVALID_PARAM;
    }

    pthread_mutex_lock(&driver->state_mutex);

    if (!driver->running) {
        pthread_mutex_unlock(&driver->state_mutex);
        logger_info("相机已经停止");
        return SUCCESS;
    }

    // 停止采集线程
    driver->running = false;
    pthread_mutex_unlock(&driver->state_mutex);

    // 等待线程退出
    pthread_join(driver->capture_thread, NULL);

    // 停止同步管理器
    if (driver->sync_mgr) {
        sync_manager_stop(driver->sync_mgr);
    }

    logger_info("相机停止成功");
    return SUCCESS;
}

/**
 * @brief 捕获一帧图像
 */
ImageData* camera_driver_capture_frame(CameraDriver* driver) {
    if (!driver || !driver->running) {
        return NULL;
    }

    return frame_buffer_get_frame(driver->frame_buffer);
}

/**
 * @brief 获取相机状态
 */
bool camera_driver_is_running(CameraDriver* driver) {
    if (!driver) {
        return false;
    }

    pthread_mutex_lock(&driver->state_mutex);
    bool running = driver->running;
    pthread_mutex_unlock(&driver->state_mutex);

    return running;
}

/**
 * @brief 销毁相机驱动
 */
void camera_driver_destroy(CameraDriver* driver) {
    if (!driver) {
        return;
    }

    // 确保相机已停止
    camera_driver_stop(driver);

    // 销毁子模块
    if (driver->sync_mgr) {
        sync_manager_destroy(driver->sync_mgr);
    }

    if (driver->frame_buffer) {
        frame_buffer_destroy(driver->frame_buffer);
    }

    pthread_mutex_destroy(&driver->state_mutex);
    free(driver);

    logger_info("相机驱动销毁完成");
} 