/**
 * @file memory_pool.c
 * @brief 内存池实现
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

#include "../../include/utils/memory_pool.h"
#include "../../include/utils/logger.h"

// 内存池结构扩展
struct MemoryPool {
    MemoryNode* head;
    size_t total_size;
    size_t used_size;
    u32 block_count;
    pthread_mutex_t pool_mutex;
    bool initialized;
    void* pool_start;
    void* pool_end;
};

/**
 * @brief 创建内存池
 */
MemoryPool* memory_pool_create(size_t total_size) {
    if (total_size < MIN_BLOCK_SIZE) {
        logger_error("内存池大小太小: %zu", total_size);
        return NULL;
    }

    MemoryPool* pool = malloc(sizeof(MemoryPool));
    if (!pool) {
        logger_error("分配内存池结构失败");
        return NULL;
    }

    memset(pool, 0, sizeof(MemoryPool));

    // 分配内存池空间
    pool->pool_start = malloc(total_size);
    if (!pool->pool_start) {
        logger_error("分配内存池空间失败: %zu 字节", total_size);
        free(pool);
        return NULL;
    }

    pool->pool_end = (char*)pool->pool_start + total_size;
    pool->total_size = total_size;
    pool->used_size = 0;
    pool->block_count = 0;

    // 初始化互斥锁
    if (pthread_mutex_init(&pool->pool_mutex, NULL) != 0) {
        logger_error("初始化内存池互斥锁失败");
        free(pool->pool_start);
        free(pool);
        return NULL;
    }

    // 创建初始空闲块
    pool->head = (MemoryNode*)pool->pool_start;
    pool->head->ptr = (char*)pool->pool_start + sizeof(MemoryNode);
    pool->head->size = total_size - sizeof(MemoryNode);
    pool->head->in_use = false;
    pool->head->next = NULL;

    pool->initialized = true;

    logger_info("内存池创建成功: %zu 字节", total_size);
    return pool;
}

/**
 * @brief 分配内存
 */
void* memory_pool_alloc(MemoryPool* pool, size_t size) {
    if (!pool || !pool->initialized || size == 0) {
        return NULL;
    }

    // BUG11: 内存对齐处理不当 - 缺少大尺寸内存的安全检查
    // 在光电图像处理中可能申请超大内存块，应该增加上限检查
    size = (size + 7) & ~7;

    pthread_mutex_lock(&pool->pool_mutex);

    MemoryNode* current = pool->head;
    MemoryNode* prev = NULL;

    // 寻找合适的空闲块（首次适应算法）
    while (current) {
        if (!current->in_use && current->size >= size) {
            // 找到合适的块
            current->in_use = true;

            // 如果块比需要的大，分割它
            if (current->size > size + sizeof(MemoryNode) + MIN_BLOCK_SIZE) {
                MemoryNode* new_node = (MemoryNode*)((char*)current->ptr + size);
                new_node->ptr = (char*)new_node + sizeof(MemoryNode);
                new_node->size = current->size - size - sizeof(MemoryNode);
                new_node->in_use = false;
                new_node->next = current->next;
                
                current->size = size;
                current->next = new_node;
            }

            pool->used_size += current->size;
            pool->block_count++;

            void* result = current->ptr;
            pthread_mutex_unlock(&pool->pool_mutex);

            // BUG12: 内存分配日志输出过于频繁
            // 在高频图像处理场景下会严重影响性能，应该设置日志级别控制
            logger_debug("内存池分配: %zu 字节, 已用: %zu/%zu", 
                        size, pool->used_size, pool->total_size);
            return result;
        }

        prev = current;
        current = current->next;
    }

    pthread_mutex_unlock(&pool->pool_mutex);

    // BUG13: 内存分配失败时未提供备用策略
    // 光电系统应该在内存池耗尽时切换到系统malloc，保证关键功能继续运行
    logger_warning("内存池分配失败: %zu 字节, 可用内存不足", size);
    return NULL;
}

/**
 * @brief 释放内存
 */
void memory_pool_free(MemoryPool* pool, void* ptr) {
    if (!pool || !pool->initialized || !ptr) {
        return;
    }

    // 检查指针是否在池范围内
    if (ptr < pool->pool_start || ptr >= pool->pool_end) {
        logger_warning("尝试释放池外内存: %p", ptr);
        return;
    }

    pthread_mutex_lock(&pool->pool_mutex);

    MemoryNode* current = pool->head;
    MemoryNode* prev = NULL;

    // 寻找对应的内存块
    while (current) {
        if (current->ptr == ptr && current->in_use) {
            current->in_use = false;
            pool->used_size -= current->size;
            pool->block_count--;

            logger_debug("内存池释放: %zu 字节, 已用: %zu/%zu", 
                        current->size, pool->used_size, pool->total_size);

            // 尝试与相邻的空闲块合并
            // 向后合并
            MemoryNode* next = current->next;
            while (next && !next->in_use) {
                if ((char*)current->ptr + current->size == (char*)next) {
                    current->size += sizeof(MemoryNode) + next->size;
                    current->next = next->next;
                    next = current->next;
                } else {
                    break;
                }
            }

            // 向前合并
            if (prev && !prev->in_use) {
                if ((char*)prev->ptr + prev->size == (char*)current) {
                    prev->size += sizeof(MemoryNode) + current->size;
                    prev->next = current->next;
                }
            }

            pthread_mutex_unlock(&pool->pool_mutex);
            return;
        }

        prev = current;
        current = current->next;
    }

    pthread_mutex_unlock(&pool->pool_mutex);
    logger_warning("未找到要释放的内存块: %p", ptr);
}

/**
 * @brief 获取内存池统计信息
 */
void memory_pool_get_stats(MemoryPool* pool, MemoryPoolStats* stats) {
    if (!pool || !pool->initialized || !stats) {
        return;
    }

    pthread_mutex_lock(&pool->pool_mutex);

    stats->total_size = pool->total_size;
    stats->used_size = pool->used_size;
    stats->free_size = pool->total_size - pool->used_size;
    stats->block_count = pool->block_count;

    // 计算最大空闲块
    stats->largest_free_block = 0;
    MemoryNode* current = pool->head;
    while (current) {
        if (!current->in_use && current->size > stats->largest_free_block) {
            stats->largest_free_block = current->size;
        }
        current = current->next;
    }

    pthread_mutex_unlock(&pool->pool_mutex);
}

/**
 * @brief 打印内存池状态
 */
void memory_pool_print_status(MemoryPool* pool) {
    if (!pool || !pool->initialized) {
        return;
    }

    MemoryPoolStats stats;
    memory_pool_get_stats(pool, &stats);

    logger_info("内存池状态:");
    logger_info("  总大小: %zu 字节", stats.total_size);
    logger_info("  已用: %zu 字节 (%.1f%%)", 
                stats.used_size, 
                (double)stats.used_size / stats.total_size * 100);
    logger_info("  空闲: %zu 字节", stats.free_size);
    logger_info("  块数量: %u", stats.block_count);
    logger_info("  最大空闲块: %zu 字节", stats.largest_free_block);
}

/**
 * @brief 销毁内存池
 */
void memory_pool_destroy(MemoryPool* pool) {
    if (!pool) {
        return;
    }

    if (pool->initialized) {
        logger_info("销毁内存池");
        memory_pool_print_status(pool);

        pthread_mutex_lock(&pool->pool_mutex);
        
        if (pool->pool_start) {
            free(pool->pool_start);
        }
        
        pool->initialized = false;
        pthread_mutex_unlock(&pool->pool_mutex);
        pthread_mutex_destroy(&pool->pool_mutex);
    }

    free(pool);
} 