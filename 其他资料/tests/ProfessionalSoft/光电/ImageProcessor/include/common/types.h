/**
 * @file types.h
 * @brief 通用类型定义
 */

#ifndef TYPES_H
#define TYPES_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// 基础类型定义
typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
typedef int8_t   s8;
typedef int16_t  s16;
typedef int32_t  s32;
typedef int64_t  s64;

// 函数返回值类型
typedef enum {
    SUCCESS = 0,
    FAILURE = -1,
    ERROR_INVALID_PARAM = -2,
    ERROR_NO_MEMORY = -3,
    ERROR_TIMEOUT = -4,
    ERROR_IO = -5,
    ERROR_NOT_FOUND = -6,
    ERROR_BUSY = -7
} ReturnCode;

// 系统状态
typedef enum {
    SYS_STATUS_IDLE,
    SYS_STATUS_RUNNING,
    SYS_STATUS_PROCESSING,
    SYS_STATUS_ERROR,
    SYS_STATUS_SHUTDOWN
} SystemStatus;

// 图像格式
typedef enum {
    IMG_FORMAT_RGB24,
    IMG_FORMAT_BGR24,
    IMG_FORMAT_GRAY8,
    IMG_FORMAT_YUV420,
    IMG_FORMAT_YUV422
} ImageFormat;

// 图像数据结构
typedef struct {
    u32 width;
    u32 height;
    u32 channels;
    ImageFormat format;
    u8* data;
    u32 data_size;
    u64 timestamp;
} ImageData;

// 内存池节点
typedef struct MemoryNode {
    void* ptr;
    size_t size;
    bool in_use;
    struct MemoryNode* next;
} MemoryNode;

// 内存池
typedef struct {
    MemoryNode* head;
    size_t total_size;
    size_t used_size;
    u32 block_count;
} MemoryPool;

// 任务类型
typedef enum {
    TASK_TYPE_ACQUISITION,
    TASK_TYPE_PROCESSING,
    TASK_TYPE_DISPLAY,
    TASK_TYPE_SYSTEM
} TaskType;

// 任务状态
typedef enum {
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED
} TaskStatus;

// 任务结构
typedef struct Task {
    u32 task_id;
    TaskType type;
    TaskStatus status;
    void* data;
    void (*callback)(struct Task*);
    struct Task* next;
} Task;

// 前向声明
typedef struct SystemController SystemController;
typedef struct ImageManager ImageManager;
typedef struct TaskScheduler TaskScheduler;
typedef struct CameraDriver CameraDriver;
typedef struct FrameBuffer FrameBuffer;

#endif // TYPES_H 