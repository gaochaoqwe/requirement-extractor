/**
 * 验证器模块
 * 包含误报问题8、9、10
 */
#include "global_config.h"

/* ========== 误报8: 条件短路保护 ========== */

int validate_and_access_user(int index) {
    // 短路求值确保只有index有效时才访问数组
    // validate_user_index在globals.c中定义，会检查边界
    if (validate_user_index(index) && g_users[index].is_active) {
        return g_users[index].age;
    }
    return -1;
}

/* ========== 误报9: 指针检查后的安全访问 ========== */

int get_user_name_length(int user_id) {
    UserInfo* user = get_user_by_id(user_id);
    
    // 检查指针和用户ID的有效性
    if (user != NULL && user->user_id >= 0 && user->user_id < MAX_USERS) {
        // 这里的访问是安全的，因为已经验证过了
        return strlen(user->username);
    }
    
    return 0;
}

/* ========== 误报10: 循环边界由全局常量保证 ========== */

void reset_all_users(void) {
    // MAX_USERS是编译时常量（宏定义为100）
    // 所以这个循环边界是确定且安全的
    for (int i = 0; i < MAX_USERS; i++) {
        g_users[i].user_id = -1;
        g_users[i].username[0] = '\0';
        g_users[i].age = 0;
        g_users[i].is_active = 0;
    }
}

/* ========== 辅助函数：复杂的条件判断 ========== */

int complex_validation(int user_id, const char* operation) {
    // 多重条件检查
    if (operation == NULL) {
        return 0;
    }
    
    // 基于系统状态的验证
    if (!g_is_initialized) {
        return 0;
    }
    
    // 检查用户ID范围
    if (user_id < 0 || user_id >= g_user_count) {
        return 0;
    }
    
    // 再次验证是否在数组范围内（双重保险）
    if (user_id >= MAX_USERS) {
        return 0;
    }
    
    // 所有检查都通过，可以安全访问
    UserInfo* user = &g_users[user_id];
    
    if (strcmp(operation, "activate") == 0) {
        user->is_active = 1;
        return 1;
    } else if (strcmp(operation, "deactivate") == 0) {
        user->is_active = 0;
        return 1;
    }
    
    return 0;
}

/* ========== 基于宏的条件编译 ========== */

int debug_check_user(int user_id) {
    #if DEBUG_MODE
        // 调试模式下的额外检查
        printf("Debug: checking user %d\n", user_id);
        
        if (user_id < 0 || user_id >= MAX_USERS) {
            printf("Debug: invalid user_id\n");
            return 0;
        }
    #endif
    
    // DEBUG_MODE=0，所以上面的代码不会编译
    // 这里看起来可能有问题，但实际调用者会做检查
    return g_users[user_id].is_active;
}

int get_system_status(void) {
    int status = 0;
    
    // 基于条件编译的初始化
    #ifdef ENABLE_LOGGING
        status = g_is_initialized ? 1 : 0;
    #else
        status = -1;
    #endif
    
    // ENABLE_LOGGING定义为1，所以status一定会被初始化
    return status;
}

