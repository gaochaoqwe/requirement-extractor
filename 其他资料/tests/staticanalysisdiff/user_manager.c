/**
 * 用户管理模块
 * 包含真实问题1和2，误报问题1和2
 */
#include "global_config.h"

/* ========== 真实问题1: 数组越界（需要跨文件分析g_user_count） ========== */

int add_user(const char* username, int age) {
    if (username == NULL) {
        return -1;
    }
    
    // 检查是否还有空间
    if (g_user_count >= MAX_USERS) {
        return -1;  // 数组已满
    }
    
    // 创建新用户
    int new_id = g_user_count;
    g_users[new_id].user_id = new_id;
    strncpy(g_users[new_id].username, username, MAX_NAME_LENGTH - 1);
    g_users[new_id].username[MAX_NAME_LENGTH - 1] = '\0';
    g_users[new_id].age = age;
    g_users[new_id].is_active = 1;
    
    g_user_count++;
    
    return new_id;
}

/* ========== 真实问题2: 数组越界访问（条件检查不完整） ========== */

UserInfo* get_user_by_id(int user_id) {
    // 问题：只检查了user_id >= 0，没有检查上界
    // 当user_id >= MAX_USERS时会越界
    if (user_id >= 0) {
        return &g_users[user_id];  // 🔴 真实问题：可能越界！
    }
    return NULL;
}

/* ========== 误报1: 看起来越界但实际安全（有全局变量边界检查） ========== */

int get_active_user_count(void) {
    int count = 0;
    
    // 这里看起来可能越界，但实际上g_user_count始终 <= MAX_USERS
    // 因为在add_user中已经检查过了
    for (int i = 0; i < g_user_count; i++) {
        if (g_users[i].is_active) {
            count++;
        }
    }
    
    return count;
}

/* ========== 误报2: 看起来条件不可达但实际可能到达 ========== */

int deactivate_user(int user_id) {
    // 这个检查看起来冗余，但由于get_user_by_id有bug，
    // 这个检查实际上是必要的
    if (user_id < 0 || user_id >= MAX_USERS) {
        return -1;
    }
    
    if (user_id >= g_user_count) {
        return -1;  // 用户不存在
    }
    
    g_users[user_id].is_active = 0;
    return 0;
}

/* ========== 用于测试的辅助函数 ========== */

void print_user_info(int user_id) {
    UserInfo* user = get_user_by_id(user_id);
    if (user != NULL && user->user_id >= 0) {
        printf("User %d: %s (age: %d, active: %d)\n",
               user->user_id, user->username, user->age, user->is_active);
    }
}

