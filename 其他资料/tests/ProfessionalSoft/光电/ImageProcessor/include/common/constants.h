/**
 * @file constants.h
 * @brief 系统常量定义
 */

#ifndef CONSTANTS_H
#define CONSTANTS_H

// 系统配置常量
#define MAX_IMAGE_WIDTH         4096
#define MAX_IMAGE_HEIGHT        3072
#define MAX_CHANNELS            4
#define MAX_FRAME_BUFFER_SIZE   10
#define MAX_TASK_QUEUE_SIZE     100
#define MAX_LOG_MESSAGE_SIZE    512
#define MAX_FILE_PATH_SIZE      256

// 内存池配置
#define MEMORY_POOL_SIZE        (64 * 1024 * 1024)  // 64MB
#define MIN_BLOCK_SIZE          64
#define MAX_BLOCK_SIZE          (16 * 1024 * 1024)  // 16MB

// 图像处理参数
#define DEFAULT_FILTER_SIZE     3
#define MAX_FILTER_SIZE         15
#define HISTOGRAM_BINS          256
#define EDGE_THRESHOLD_LOW      50
#define EDGE_THRESHOLD_HIGH     150

// 特征检测参数
#define MAX_FEATURES            1000
#define FEATURE_QUALITY         0.01
#define MIN_DISTANCE            10.0

// 运动跟踪参数
#define MAX_TRACKING_OBJECTS    50
#define TRACKING_WINDOW_SIZE    15
#define TRACKING_ITERATIONS     10

// 显示参数
#define DISPLAY_REFRESH_RATE    30  // fps
#define OVERLAY_MAX_COUNT       20
#define TEXT_BUFFER_SIZE        128

// 日志级别
typedef enum {
    LOG_LEVEL_DEBUG = 0,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_FATAL
} LogLevel;

// 错误代码
#define ERR_CAMERA_INIT         0x1001
#define ERR_CAMERA_START        0x1002
#define ERR_CAMERA_CAPTURE      0x1003
#define ERR_BUFFER_FULL         0x1004
#define ERR_BUFFER_EMPTY        0x1005
#define ERR_INVALID_FORMAT      0x1006
#define ERR_PROCESSING_FAILED   0x1007
#define ERR_DISPLAY_INIT        0x1008
#define ERR_CONFIG_LOAD         0x1009
#define ERR_CALIBRATION         0x100A

// 任务优先级
#define PRIORITY_CRITICAL       0
#define PRIORITY_HIGH           1
#define PRIORITY_NORMAL         2
#define PRIORITY_LOW            3

// 同步相关
#define SYNC_TIMEOUT_MS         1000
#define MAX_RETRY_COUNT         3

#endif // CONSTANTS_H 