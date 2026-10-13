/**
 * 全局变量定义文件
 */
#include "global_config.h"

/* ========== 全局变量定义 ========== */

UserInfo g_users[MAX_USERS];
int g_user_count = 0;

Message g_messages[MAX_MESSAGES];
int g_message_count = 0;

SystemConfig g_system_config = {
    .max_connections = 100,
    .timeout_seconds = 30,
    .server_name = "TestServer"
};

int g_is_initialized = 0;
int g_error_code = 0;

/* ========== 基础函数实现 ========== */

void initialize_system(void) {
    g_user_count = 0;
    g_message_count = 0;
    g_is_initialized = 1;
    g_error_code = 0;
    
    // 初始化用户数组
    for (int i = 0; i < MAX_USERS; i++) {
        g_users[i].user_id = -1;
        g_users[i].username[0] = '\0';
        g_users[i].age = 0;
        g_users[i].is_active = 0;
    }
    
    // 初始化消息数组
    for (int i = 0; i < MAX_MESSAGES; i++) {
        g_messages[i].message_id = -1;
        g_messages[i].content[0] = '\0';
        g_messages[i].sender_id = -1;
        g_messages[i].is_read = 0;
    }
}

void cleanup_system(void) {
    g_is_initialized = 0;
    g_user_count = 0;
    g_message_count = 0;
}

int validate_user_index(int index) {
    // 验证索引是否在有效范围内
    if (index >= 0 && index < g_user_count && index < MAX_USERS) {
        return 1;  // 有效
    }
    return 0;  // 无效
}

int safe_string_copy(char* dest, const char* src, int dest_size) {
    if (dest == NULL || src == NULL || dest_size <= 0) {
        return -1;
    }
    
    strncpy(dest, src, dest_size - 1);
    dest[dest_size - 1] = '\0';
    return 0;
}

int calculate_hash(const char* str) {
    if (str == NULL) {
        return 0;
    }
    
    int hash = 0;
    while (*str) {
        hash = (hash * 31) + *str;
        str++;
    }
    return hash;
}

