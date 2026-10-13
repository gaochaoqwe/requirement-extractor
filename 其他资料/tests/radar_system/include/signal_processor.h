/**
 * 信号处理模块
 */
#ifndef SIGNAL_PROCESSOR_H
#define SIGNAL_PROCESSOR_H

#include "radar_types.h"

// 初始化信号处理器
int signal_processor_init(void);

// 采集原始信号
SignalData* signal_acquire(void);

// 信号滤波
int signal_filter(SignalData *signal);

// 信号FFT变换
int signal_fft_transform(SignalData *signal);

// 释放信号数据
void signal_release(SignalData *signal);

// 清理信号处理器
void signal_processor_cleanup(void);

#endif

