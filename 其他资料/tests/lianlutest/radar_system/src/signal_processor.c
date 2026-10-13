/**
 * 信号处理模块实现
 * 
 * 处理流程：
 * 1. signal_acquire() - 采集原始信号
 * 2. signal_filter() - 滤波去噪
 * 3. signal_fft_transform() - FFT变换
 * 4. 传递给radar_process_signal()处理
 * 5. signal_release() - 释放资源
 */
#include "../include/signal_processor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_SAMPLES 1024
#define FILTER_WINDOW_SIZE 5

static double *g_fft_buffer = NULL;
static int g_is_initialized = 0;

/**
 * 初始化信号处理器
 * 
 * 功能需求：
 * 1. 分配FFT缓冲区内存
 * 2. 初始化滤波器参数
 * 3. 设置初始化标志
 * 
 * @return 0表示成功，-1表示失败
 */
int signal_processor_init(void) {
    // 分配FFT缓冲区
    g_fft_buffer = (double*)malloc(sizeof(double) * MAX_SAMPLES * 2);
    if (!g_fft_buffer) {
        fprintf(stderr, "Failed to allocate FFT buffer\n");
        return -1;
    }
    
    memset(g_fft_buffer, 0, sizeof(double) * MAX_SAMPLES * 2);
    g_is_initialized = 1;
    
    return 0;
}

/**
 * 采集原始信号数据
 * 
 * 功能需求：
 * 1. 分配SignalData结构和采样数组
 * 2. 模拟从硬件采集信号数据
 * 3. 设置时间戳和频率信息
 * 4. 返回的内存需要调用者通过signal_release()释放
 * 
 * @return SignalData指针，失败返回NULL
 */
SignalData* signal_acquire(void) {
    if (!g_is_initialized) {
        fprintf(stderr, "Signal processor not initialized\n");
        return NULL;
    }
    
    // 分配SignalData结构
    SignalData *signal = (SignalData*)malloc(sizeof(SignalData));
    if (!signal) {
        return NULL;
    }
    
    // 分配采样数组
    signal->samples = (double*)malloc(sizeof(double) * MAX_SAMPLES);
    if (!signal->samples) {
        free(signal);
        return NULL;
    }
    
    // 模拟信号采集
    signal->sample_count = MAX_SAMPLES;
    signal->timestamp = (double)time(NULL);
    signal->frequency = 10e9;  // 10 GHz
    
    // 生成模拟数据（包含几个目标信号）
    for (int i = 0; i < MAX_SAMPLES; i++) {
        signal->samples[i] = sin(i * 0.1) * 0.5 + 
                           sin(i * 0.05) * 0.3 +
                           ((double)rand() / RAND_MAX) * 0.1;  // 添加噪声
    }
    
    return signal;
}

/**
 * 信号滤波处理
 * 
 * 功能需求：
 * 1. 使用移动平均滤波器去除高频噪声
 * 2. 保持信号的samples指针不变，原地修改数据
 * 3. 处理边界情况（数组开头和结尾）
 * 4. 验证输入参数的有效性
 * 
 * @param signal 待滤波的信号数据
 * @return 0表示成功，-1表示失败
 */
int signal_filter(SignalData *signal) {
    if (!signal || !signal->samples) {
        return -1;
    }
    
    // 问题13：注释说"保持signal的samples指针不变，原地修改数据"
    // 但代码分配了新内存，没有释放旧内存，导致内存泄漏
    // 而且后续的signal_release只会释放新指针，旧指针永远泄漏
    double *filtered = (double*)malloc(sizeof(double) * signal->sample_count);
    
    // 移动平均滤波
    for (int i = 0; i < signal->sample_count; i++) {
        double sum = 0.0;
        int count = 0;
        
        // 问题14：注释说"处理边界情况"
        // 但代码在边界时会访问负数索引，导致未定义行为
        for (int j = i - FILTER_WINDOW_SIZE/2; j <= i + FILTER_WINDOW_SIZE/2; j++) {
            // 应该检查 j >= 0 && j < signal->sample_count
            sum += signal->samples[j];
            count++;
        }
        
        filtered[i] = sum / count;
    }
    
    // 替换原数据（泄漏了原samples）
    signal->samples = filtered;
    
    return 0;
}

/**
 * FFT变换处理
 * 
 * 功能需求：
 * 1. 必须在滤波后调用（依赖signal_filter的处理结果）
 * 2. 将时域信号转换为频域
 * 3. 使用全局FFT缓冲区进行计算
 * 4. 变换后的结果写回signal->samples
 * 5. 保持sample_count不变
 * 
 * @param signal 待变换的信号
 * @return 0表示成功，-1表示失败
 */
int signal_fft_transform(SignalData *signal) {
    if (!signal || !signal->samples) {
        return -1;
    }
    
    // 问题15：注释明确说"必须在滤波后调用"
    // 但代码没有任何检查确保signal_filter已经被调用
    // 这会导致对未滤波的数据进行FFT，结果不准确
    
    if (!g_fft_buffer) {
        fprintf(stderr, "FFT buffer not allocated\n");
        return -1;
    }
    
    // 简化的FFT（仅作演示）
    // 问题16：注释说"使用全局FFT缓冲区"，但如果多线程调用会冲突
    for (int i = 0; i < signal->sample_count && i < MAX_SAMPLES; i++) {
        g_fft_buffer[i * 2] = signal->samples[i];  // 实部
        g_fft_buffer[i * 2 + 1] = 0.0;             // 虚部
    }
    
    // 执行FFT计算（简化版本）
    for (int i = 0; i < signal->sample_count; i++) {
        double real_part = 0.0;
        for (int k = 0; k < signal->sample_count; k++) {
            double angle = -2.0 * M_PI * i * k / signal->sample_count;
            real_part += signal->samples[k] * cos(angle);
        }
        signal->samples[i] = fabs(real_part);
    }
    
    return 0;
}

/**
 * 释放信号数据
 * 
 * 功能需求：
 * 1. 释放SignalData中的samples数组
 * 2. 释放SignalData结构本身
 * 3. 防止重复释放（指针置NULL）
 * 4. 能正确处理经过filter和fft变换后的signal
 * 
 * @param signal 要释放的信号数据
 */
void signal_release(SignalData *signal) {
    if (!signal) {
        return;
    }
    
    // 问题17：由于signal_filter中泄漏了原始samples
    // 这里只能释放filtered的内存，原始的永远泄漏
    if (signal->samples) {
        free(signal->samples);
    }
    
    free(signal);
    
    // 问题18：注释说"防止重复释放（指针置NULL）"
    // 但这里释放后没有将指针置NULL
    // 调用者的指针仍指向已释放内存（dangling pointer）
}

/**
 * 清理信号处理器
 * 
 * 功能需求：
 * 1. 释放FFT缓冲区
 * 2. 重置初始化标志
 * 3. 确保所有资源都被释放
 */
void signal_processor_cleanup(void) {
    if (g_fft_buffer) {
        free(g_fft_buffer);
        g_fft_buffer = NULL;
    }
    
    g_is_initialized = 0;
}

