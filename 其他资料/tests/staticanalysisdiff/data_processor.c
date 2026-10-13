/**
 * 数据处理模块
 * 包含误报问题5、6、7
 */
#include "global_config.h"

/* ========== 误报5: 条件分支都会初始化变量 ========== */

int process_user_data(int user_id) {
    int result;  // 看起来未初始化
    
    // 但实际上所有分支都会初始化result
    if (g_is_initialized) {
        if (validate_user_index(user_id)) {
            result = g_users[user_id].age * 2;
        } else {
            result = -1;  // 无效用户
        }
    } else {
        result = -2;  // 系统未初始化
    }
    
    // 这里使用result是安全的
    return result;
}

/* ========== 误报6: 宏定义保证了安全性 ========== */

void initialize_buffer_array(void) {
    // SMALL_BUFFER_SIZE 定义为64，TINY_BUFFER_SIZE定义为16
    // 所以这个循环是安全的
    char buffers[SMALL_BUFFER_SIZE][TINY_BUFFER_SIZE];
    
    // 看起来可能越界，但由于宏定义，这是安全的
    for (int i = 0; i < SMALL_BUFFER_SIZE; i++) {
        for (int j = 0; j < TINY_BUFFER_SIZE; j++) {
            buffers[i][j] = 0;
        }
    }
    
    // 访问最后一个元素也是安全的
    buffers[SMALL_BUFFER_SIZE - 1][TINY_BUFFER_SIZE - 1] = 'X';
}

/* ========== 误报7: 基于全局状态的条件检查 ========== */

int conditional_processing(void) {
    int value;
    
    // 这个条件基于全局配置宏SAFE_MODE（定义为1）
    #if SAFE_MODE
        value = 100;  // 安全模式下总是初始化
    #else
        // 非安全模式可能不初始化
        value = calculate_hash("test");
    #endif
    
    // 由于SAFE_MODE=1，这里使用value是安全的
    return value * 2;
}

/* ========== 辅助函数 ========== */

void process_all_users(void) {
    // 使用全局变量g_user_count，这是安全的
    for (int i = 0; i < g_user_count; i++) {
        if (g_users[i].is_active) {
            int processed = process_user_data(i);
            printf("Processed user %d: result = %d\n", i, processed);
        }
    }
}

int get_config_value(const char* key) {
    if (key == NULL) {
        return -1;
    }
    
    // 基于字符串计算配置值
    int hash = calculate_hash(key);
    
    // 使用宏定义确保返回值在合理范围内
    if (hash < 0) {
        return 0;
    }
    
    return hash % MAX_USERS;  // 保证不会超过MAX_USERS
}

