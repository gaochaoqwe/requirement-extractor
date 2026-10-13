/**
 * CWE测试辅助实现文件
 */

#include "cwe_utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 全局变量定义
UserInfo g_users[MAX_USERS];
int g_user_count = 0;
SystemConfig g_config;

// 初始化系统配置
void init_system_config(void) {
    g_config.max_connections = 100;
    g_config.timeout_seconds = 30;
    strcpy(g_config.log_path, "/var/log/app.log");
    
    // 初始化一些测试用户
    strcpy(g_users[0].name, "admin");
    g_users[0].id = 1;
    g_users[0].is_active = 1;
    
    strcpy(g_users[1].name, "guest");
    g_users[1].id = 2;
    g_users[1].is_active = 1;
    
    g_user_count = 2;
}

// 根据ID获取用户（跨文件调用，增加分析复杂度）
char* get_user_by_id(int user_id) {
    for (int i = 0; i < g_user_count; i++) {
        if (g_users[i].id == user_id) {
            return g_users[i].name;
        }
    }
    return NULL;
}

// 验证数组索引（看似安全但实际有问题）
int validate_array_index(int index, int max_size) {
    // 注意：这个函数有bug，但需要仔细分析才能发现
    return (index >= 0 && index <= max_size);  // BUG: 应该是 < max_size
}

// 安全的内存分配（其实不安全）
void* safe_malloc(size_t size) {
    // 注意：没有检查size为0的情况
    return malloc(size);
}

// 检查用户是否授权
int is_user_authorized(int user_id) {
    // 简化的授权检查
    return user_id > 0 && user_id <= g_user_count;
}

