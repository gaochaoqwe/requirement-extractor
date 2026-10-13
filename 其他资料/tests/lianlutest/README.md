# 雷达仿真系统测试用例

## 系统简介

这是一个C语言编写的雷达仿真系统，用于测试AI代码审查工具对**链路级业务逻辑问题**的检测能力。

系统包含以下模块：
- **radar_system**: 雷达核心控制模块
- **signal_processor**: 信号采集和处理模块  
- **target_tracker**: 目标跟踪模块

## 系统架构

```
main.c (主程序)
├── radar_system.c (雷达控制)
│   ├── radar_init()
│   ├── radar_start_scan()
│   ├── radar_stop_scan()
│   ├── radar_switch_to_tracking()
│   ├── radar_process_signal()
│   ├── radar_get_targets()
│   └── radar_cleanup()
│
├── signal_processor.c (信号处理)
│   ├── signal_processor_init()
│   ├── signal_acquire()
│   ├── signal_filter()
│   ├── signal_fft_transform()
│   ├── signal_release()
│   └── signal_processor_cleanup()
│
└── target_tracker.c (目标跟踪)
    ├── tracker_init()
    ├── tracker_update()
    ├── tracker_predict_position()
    ├── tracker_associate_measurements()
    ├── tracker_get_track_quality()
    └── tracker_cleanup()
```

## 正确的工作流程

### 初始化阶段
1. `radar_init()` - 初始化雷达系统
2. `signal_processor_init()` - 初始化信号处理器
3. `tracker_init()` - 初始化跟踪器

### 运行阶段
1. `radar_start_scan()` - 启动扫描（仅能从IDLE状态启动）
2. 循环处理：
   - `signal_acquire()` - 采集信号
   - `signal_filter()` - 滤波去噪（**必须步骤**）
   - `signal_fft_transform()` - FFT变换（**必须在滤波后**）
   - `radar_process_signal()` - 处理信号并提取目标
   - `radar_get_targets()` - 获取目标列表
   - `tracker_update()` - 更新跟踪（**每个周期都要调用**）
   - `signal_release()` - 释放信号内存
3. 切换跟踪模式：
   - `tracker_get_track_quality()` - 评估航迹质量
   - `radar_stop_scan()` - **必须先停止扫描**
   - `radar_switch_to_tracking()` - 切换到跟踪模式

### 清理阶段
1. `tracker_cleanup()` - 清理跟踪器
2. `signal_processor_cleanup()` - 清理信号处理器
3. `radar_cleanup()` - 清理雷达系统

## 已埋入的功能实现错误

### 🔴 问题类型：通过注释和代码不匹配来模拟真实业务逻辑错误

### radar_system.c

| 问题编号 | 涉及函数 | 问题描述 | 影响 |
|---------|---------|---------|------|
| **问题3** | `radar_start_scan()` | 注释说必须从IDLE状态启动，但代码没有检查状态 | 可能在TRACKING状态启动扫描，导致状态混乱 |
| **问题5** | `radar_stop_scan()` | 注释说要保存当前跟踪的目标，但代码直接切换状态 | 扫描结果丢失 |
| **问题6-7** | `radar_switch_to_tracking()` | 注释说必须先停止扫描，但代码直接切换；应该清理其他目标但没有 | 扫描和跟踪同时运行，资源冲突 |
| **问题8** | `radar_process_signal()` | 距离范围判断条件写反了（用OR代替AND） | 处理了范围外的目标 |
| **问题9** | `radar_process_signal()` | 没有检查目标数量是否超过max_targets | 数组越界 |
| **问题10** | `radar_get_targets()` | 注释说保证线程安全，但没有锁 | 多线程数据竞争 |
| **问题11** | `radar_get_targets()` | 超时判断条件反了（保留超时的，过滤未超时的） | 返回的都是过期目标 |
| **问题12** | `radar_cleanup()` | 注释说关闭日志文件，但忘记关闭 | 文件句柄泄漏 |

### signal_processor.c

| 问题编号 | 涉及函数 | 问题描述 | 影响 |
|---------|---------|---------|------|
| **问题13** | `signal_filter()` | 注释说原地修改，但分配了新内存且没释放旧的 | 内存泄漏 |
| **问题14** | `signal_filter()` | 边界处理时会访问负数索引 | 未定义行为/崩溃 |
| **问题15** | `signal_fft_transform()` | 注释说必须在滤波后调用，但没有检查 | 对噪声数据FFT，结果不准 |
| **问题16** | `signal_fft_transform()` | 使用全局缓冲区但没有线程保护 | 多线程冲突 |

### target_tracker.c

| 问题编号 | 涉及函数 | 问题描述 | 影响 |
|---------|---------|---------|------|
| **问题19** | `tracker_update()` | 注释说最近邻关联，但用的是第一个满足门限的 | 关联错误 |
| **问题20** | `tracker_update()` | 注释说更新速度，但代码没有计算 | 速度一直为0 |
| **问题21** | `tracker_update()` | 注释说连续3次确认才创建航迹，但立即创建 | 虚假航迹过多 |
| **问题22** | `tracker_update()` | 删除条件是>5而不是>=5 | 航迹多保留一周期 |
| **问题23-24** | `tracker_predict_position()` | 由于速度未更新（问题20），预测功能失效；没有验证负距离 | 预测无效 |
| **问题25** | `tracker_associate_measurements()` | 注释说用预测位置关联，但用的是当前位置 | 高速目标关联失败 |
| **问题27** | `tracker_get_track_quality()` | 计算公式写反了（除以age*100而不是age再乘100） | 质量分数永远接近0 |

### main.c

| 问题编号 | 涉及函数 | 问题描述 | 影响 |
|---------|---------|---------|------|
| **问题28** | `main()` | 初始化顺序错误（tracker先于radar） | tracker依赖radar配置可能失败 |
| **问题29** | `main()` | 跳过了filter步骤直接FFT | 处理噪声数据，检测精度差 |
| **问题30** | `main()` | 只在有目标时才更新跟踪器 | 无目标时航迹状态不更新 |
| **问题31** | `main()` | 质量检查永远不触发（因问题27） | 永远不会切换跟踪模式 |
| **问题32** | `main()` | 切换跟踪前没有停止扫描 | 违反前置条件（问题6） |
| **问题33** | `main()` | 清理顺序混乱 | 资源清理不完整 |

## 链路级问题示例

### 🔗 链路1：信号处理流程错误

**调用链**: `main()` → `signal_fft_transform()` (跳过`signal_filter()`)

- **问题29**: main中跳过filter直接FFT
- **问题15**: fft_transform没有检查是否已滤波
- **结果**: 噪声数据被处理，检测精度下降

### 🔗 链路2：状态机错误

**调用链**: `main()` → `radar_switch_to_tracking()` (未调用`radar_stop_scan()`)

- **问题32**: main中没有先停止扫描
- **问题6**: switch_to_tracking没有检查当前状态
- **结果**: 扫描和跟踪同时运行，资源冲突

### 🔗 链路3：跟踪预测失效

**调用链**: `tracker_update()` (不更新速度) → `tracker_predict_position()` (速度为0) → `tracker_associate_measurements()` (用当前位置)

- **问题20**: update时没有计算速度
- **问题23**: predict使用的速度永远是0
- **问题25**: associate没有使用预测位置
- **结果**: 整个预测功能链条失效

### 🔗 链路4：内存泄漏

**调用链**: `signal_acquire()` → `signal_filter()` (分配新内存) → `signal_release()` (只释放新指针)

- **问题13**: filter分配新内存但不释放旧的
- **问题17**: release只释放最后的指针
- **结果**: 每次滤波都泄漏原始采样数组

### 🔗 链路5：质量评估失效

**调用链**: `tracker_update()` (不计算速度) → `tracker_get_track_quality()` (公式错误) → `main()` (永远不切换模式)

- **问题20**: update不计算速度导致跟踪不准
- **问题27**: quality计算公式错误，分数接近0
- **问题31**: main中质量检查永远不触发
- **结果**: 永远无法切换到跟踪模式

## 测试目标

测试AI代码审查工具能否：

1. ✅ 识别注释与代码不匹配的业务逻辑错误
2. ✅ 发现跨函数的链路级问题
3. ✅ 理解函数间的依赖关系和前置条件
4. ✅ 追踪数据流和状态变化
5. ✅ 检测隐式的业务规则违反

## 编译说明

```bash
cd E:\code\requirement_extractor\backend\tests\lianlutest\radar_system
gcc -o radar_sim src/*.c -I include -lm
```

## 运行

```bash
./radar_sim
```

注意：由于存在大量业务逻辑错误，程序可能会产生异常行为或崩溃。

