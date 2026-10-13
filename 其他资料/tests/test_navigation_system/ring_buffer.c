/**
 * @file ring_buffer.c
 * @brief 环形缓冲区实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ring_buffer.h"
#include "logger.h"

// 环形缓冲区结构
typedef struct {
    GPSData *buffer;
    int capacity;
    int size;
    int read_index;
    int write_index;
} RingBuffer;

static RingBuffer *rb = NULL;

/**
 * @brief 初始化环形缓冲区
 */
int rb_init(int capacity) {
    if (capacity <= 0) {
        log_message(LOG_ERROR, "Invalid ring buffer capacity: %d", capacity);
        return -1;
    }
    
    rb = (RingBuffer*)malloc(sizeof(RingBuffer));
    if (rb == NULL) {
        log_message(LOG_ERROR, "Failed to allocate ring buffer structure");
        return -2;
    }
    
    rb->buffer = (GPSData*)malloc(sizeof(GPSData) * capacity);
    if (rb->buffer == NULL) {
        log_message(LOG_ERROR, "Failed to allocate ring buffer data");
        free(rb);
        rb = NULL;
        return -3;
    }
    
    rb->capacity = capacity;
    rb->size = 0;
    rb->read_index = 0;
    rb->write_index = 0;
    
    log_message(LOG_INFO, "Ring buffer initialized with capacity: %d", capacity);
    return 0;
}

/**
 * @brief 清理环形缓冲区
 */
void rb_cleanup(void) {
    if (rb) {
        if (rb->buffer) {
            free(rb->buffer);
        }
        free(rb);
        rb = NULL;
        log_message(LOG_INFO, "Ring buffer cleaned up");
    }
}

/**
 * @brief 写入数据
 */
int rb_write(const GPSData *data) {
    if (rb == NULL) {
        log_message(LOG_ERROR, "Ring buffer not initialized");
        return -1;
    }
    
    if (data == NULL) {
        log_message(LOG_ERROR, "Invalid data pointer");
        return -2;
    }
    
    // 问题：没有加锁，并发写入可能导致数据竞争
    
    // 如果缓冲区满，覆盖最旧的数据
    if (rb->size >= rb->capacity) {
        log_message(LOG_DEBUG, "Ring buffer full, overwriting oldest data");
        rb->read_index = (rb->read_index + 1) % rb->capacity;
    } else {
        rb->size++;
    }
    
    // 写入数据
    memcpy(&rb->buffer[rb->write_index], data, sizeof(GPSData));
    rb->write_index = (rb->write_index + 1) % rb->capacity;
    
    return 0;
}

/**
 * @brief 读取数据
 */
int rb_read(GPSData *data) {
    if (rb == NULL) {
        log_message(LOG_ERROR, "Ring buffer not initialized");
        return -1;
    }
    
    if (data == NULL) {
        log_message(LOG_ERROR, "Invalid data pointer");
        return -2;
    }
    
    // 问题：没有加锁，并发读写可能导致数据竞争
    
    if (rb->size == 0) {
        log_message(LOG_DEBUG, "Ring buffer empty");
        return -3;
    }
    
    // 读取数据
    memcpy(data, &rb->buffer[rb->read_index], sizeof(GPSData));
    rb->read_index = (rb->read_index + 1) % rb->capacity;
    rb->size--;
    
    return 0;
}

/**
 * @brief 获取缓冲区大小
 */
int rb_size(void) {
    if (rb == NULL) {
        return 0;
    }
    return rb->size;
}

/**
 * @brief 判断是否为空
 */
int rb_empty(void) {
    if (rb == NULL) {
        return 1;
    }
    return (rb->size == 0);
}

/**
 * @brief 判断是否满
 */
int rb_full(void) {
    if (rb == NULL) {
        return 0;
    }
    return (rb->size >= rb->capacity);
}

