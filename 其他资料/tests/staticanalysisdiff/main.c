/**
 * 主测试程序
 */
#include "global_config.h"

int main() {
    printf("=== 静态分析测试程序 ===\n\n");
    
    // 初始化系统
    initialize_system();
    printf("系统已初始化\n\n");
    
    // 测试用户管理
    printf("=== 测试用户管理 ===\n");
    int user1 = add_user("Alice", 25);
    int user2 = add_user("Bob", 30);
    int user3 = add_user("Charlie", 35);
    printf("添加了 %d 个用户\n\n", g_user_count);
    
    // 测试消息发送
    printf("=== 测试消息发送 ===\n");
    send_message(user1, "Hello World!");
    send_safe_message(user2, "Safe Message");
    printf("发送了 %d 条消息\n\n", g_message_count);
    
    // 测试数据处理
    printf("=== 测试数据处理 ===\n");
    process_all_users();
    printf("\n");
    
    // 测试验证器
    printf("=== 测试验证器 ===\n");
    int valid = validate_and_access_user(0);
    printf("用户0验证结果: %d\n\n", valid);
    
    // 清理
    cleanup_system();
    printf("系统已清理\n");
    
    return 0;
}

