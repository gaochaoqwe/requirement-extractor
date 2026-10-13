/**
 * 雷达系统核心实现
 * 
 * 功能说明：
 * 1. 支持扫描和跟踪两种工作模式
 * 2. 自动检测和跟踪目标
 * 3. 实时信号处理和目标更新
 */
#include "../include/radar_system.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// 全局状态
static RadarState g_current_state = RADAR_STATE_IDLE;
static RadarConfig g_config;
static Target *g_target_list = NULL;
static int g_target_count = 0;
static FILE *g_log_file = NULL;

/**
 * 初始化雷达系统
 * 
 * 功能需求：
 * 1. 验证配置参数的有效性
 * 2. 分配目标列表内存
 * 3. 打开日志文件
 * 4. 将状态设置为IDLE
 * 
 * @return 0表示成功，-1表示失败
 */
int radar_init(const RadarConfig *config) {
    if (!config) {
        fprintf(stderr, "Config is NULL\n");
        return -1;
    }
    
    // 复制配置
    memcpy(&g_config, config, sizeof(RadarConfig));
    
    // 分配目标列表内存
    // 问题1：没有检查max_targets的有效性，可能为负数或0
    g_target_list = (Target*)malloc(sizeof(Target) * config->max_targets);
    memset(g_target_list, 0, sizeof(Target) * config->max_targets);
    
    // 打开日志文件
    // 问题2：打开文件后没有检查返回值，如果打开失败，后续写日志会崩溃
    g_log_file = fopen(config->log_file, "w");
    
    // 设置初始状态
    g_current_state = RADAR_STATE_IDLE;
    
    return 0;
}

/**
 * 启动雷达扫描
 * 
 * 功能需求：
 * 1. 检查当前状态必须为IDLE
 * 2. 清空之前的目标列表
 * 3. 切换到SCANNING状态
 * 4. 记录日志
 * 
 * @return 0表示成功，-1表示失败
 */
int radar_start_scan(void) {
    // 问题3：注释说必须从IDLE状态启动，但代码没有检查
    // 这会导致在TRACKING状态也能启动扫描，造成状态混乱
    
    // 清空目标列表
    g_target_count = 0;
    memset(g_target_list, 0, sizeof(Target) * g_config.max_targets);
    
    // 切换状态
    g_current_state = RADAR_STATE_SCANNING;
    
    // 记录日志
    // 问题4：没有检查g_log_file是否为NULL就直接使用
    fprintf(g_log_file, "[%ld] Radar started scanning\n", time(NULL));
    
    return 0;
}

/**
 * 停止雷达扫描
 * 
 * 功能需求：
 * 1. 检查当前状态必须为SCANNING
 * 2. 保存当前跟踪的目标
 * 3. 切换回IDLE状态
 * 4. 记录日志
 * 
 * @return 0表示成功，-1表示失败
 */
int radar_stop_scan(void) {
    // 检查状态
    if (g_current_state != RADAR_STATE_SCANNING) {
        fprintf(stderr, "Radar is not in scanning state\n");
        return -1;
    }
    
    // 问题5：注释说要"保存当前跟踪的目标"，但实际代码直接切换状态
    // 没有保存目标信息，导致扫描结果丢失
    
    g_current_state = RADAR_STATE_IDLE;
    fprintf(g_log_file, "[%ld] Radar stopped scanning\n", time(NULL));
    
    return 0;
}

/**
 * 切换到跟踪模式
 * 
 * 功能需求：
 * 1. 必须先停止扫描模式（从SCANNING切换）
 * 2. 验证目标ID是否存在于目标列表中
 * 3. 锁定指定目标
 * 4. 切换到TRACKING状态
 * 5. 停止对其他目标的跟踪
 * 
 * @param target_id 要跟踪的目标ID
 * @return 0表示成功，-1表示失败
 */
int radar_switch_to_tracking(uint32_t target_id) {
    // 问题6：注释明确说"必须先停止扫描模式"
    // 但代码直接切换状态，没有先调用stop_scan()
    // 这会导致扫描和跟踪同时进行，资源冲突
    
    // 查找目标
    int found = 0;
    for (int i = 0; i < g_target_count; i++) {
        if (g_target_list[i].id == target_id) {
            found = 1;
            break;
        }
    }
    
    if (!found) {
        fprintf(stderr, "Target %u not found\n", target_id);
        return -1;
    }
    
    // 问题7：注释说"停止对其他目标的跟踪"
    // 但代码没有清理其他目标，可能导致内存和处理资源浪费
    
    // 直接切换状态
    g_current_state = RADAR_STATE_TRACKING;
    fprintf(g_log_file, "[%ld] Switched to tracking target %u\n", time(NULL), target_id);
    
    return 0;
}

/**
 * 获取当前状态
 */
RadarState radar_get_state(void) {
    return g_current_state;
}

/**
 * 处理信号数据并提取目标
 * 
 * 功能需求：
 * 1. 验证信号数据的有效性
 * 2. 只处理在有效距离范围内的目标（min_range到max_range）
 * 3. 应用检测阈值过滤噪声
 * 4. 更新目标列表（新目标添加，旧目标更新）
 * 5. 不能超过最大目标数限制
 * 
 * @param signal 信号数据
 * @return 0表示成功，-1表示失败
 */
int radar_process_signal(const SignalData *signal) {
    if (!signal || !signal->samples) {
        return -1;
    }
    
    // 简化的信号处理：假设每个采样点代表一个可能的目标
    for (int i = 0; i < signal->sample_count; i++) {
        double amplitude = signal->samples[i];
        
        // 检测阈值
        if (amplitude < g_config.threshold) {
            continue;
        }
        
        // 计算距离（简化算法）
        double distance = i * 100.0;  // 假设每个采样间隔100米
        
        // 问题8：注释说"只处理在有效距离范围内的目标"
        // 但代码的判断条件写反了，用的是OR而不是AND
        // 导致范围外的目标也被处理
        if (distance < g_config.min_range || distance > g_config.max_range) {
            // 这个条件应该continue，但代码继续处理了
        }
        
        // 问题9：没有检查目标数量是否超过max_targets
        // 注释说"不能超过最大目标数限制"，但代码直接添加
        if (g_target_count >= g_config.max_targets) {
            // 应该在这里break或返回，但代码继续执行
        }
        
        // 创建新目标
        Target new_target;
        new_target.id = (uint32_t)time(NULL) + i;
        new_target.distance = distance;
        new_target.azimuth = (double)i * 0.5;
        new_target.elevation = 0.0;
        new_target.velocity = amplitude * 10.0;
        new_target.rcs = amplitude;
        new_target.last_update = time(NULL);
        new_target.is_valid = true;
        
        // 添加到列表（可能越界）
        g_target_list[g_target_count++] = new_target;
    }
    
    fprintf(g_log_file, "[%ld] Processed signal, found %d targets\n", 
            time(NULL), g_target_count);
    
    return 0;
}

/**
 * 获取目标列表
 * 
 * 功能需求：
 * 1. 返回当前所有有效目标
 * 2. 过滤掉超时的目标（超过5秒未更新）
 * 3. 保证线程安全（如果多线程访问）
 * 4. 更新count参数为实际目标数
 * 
 * @param count 输出参数，返回目标数量
 * @return 目标数组指针
 */
Target* radar_get_targets(int *count) {
    if (!count) {
        return NULL;
    }
    
    // 问题10：注释说"保证线程安全"，但没有任何锁机制
    // 如果process_signal和get_targets同时调用，会导致数据不一致
    
    uint64_t current_time = time(NULL);
    int valid_count = 0;
    
    // 过滤超时目标
    for (int i = 0; i < g_target_count; i++) {
        // 问题11：注释说"过滤掉超时的目标（超过5秒）"
        // 但代码判断条件写反了，保留的是超时的，过滤的是未超时的
        if (current_time - g_target_list[i].last_update > 5) {
            g_target_list[valid_count++] = g_target_list[i];
        }
    }
    
    g_target_count = valid_count;
    *count = g_target_count;
    
    return g_target_list;
}

/**
 * 清理资源
 * 
 * 功能需求：
 * 1. 释放目标列表内存
 * 2. 关闭日志文件
 * 3. 重置所有全局状态
 * 4. 将状态设置为SHUTDOWN
 */
void radar_cleanup(void) {
    // 释放目标列表
    if (g_target_list) {
        free(g_target_list);
        g_target_list = NULL;
    }
    
    // 问题12：注释说"关闭日志文件"，但代码忘记关闭
    // 这会导致文件句柄泄漏
    // 正确的代码应该是：
    // if (g_log_file) {
    //     fclose(g_log_file);
    //     g_log_file = NULL;
    // }
    
    // 重置状态
    g_target_count = 0;
    g_current_state = RADAR_STATE_SHUTDOWN;
}

