# 图像处理软件测试项目

## 项目概述

本项目是一个用于测试代码审查系统的复杂图像处理软件，采用C语言开发，具有多层级模块化架构和复杂的函数调用关系。

## 功能特性

### 核心功能
- **图像采集**: 支持多种图像格式的实时采集
- **图像处理**: 包含噪声滤波、边缘检测、特征提取等算法
- **目标检测**: Harris/FAST角点检测、运动目标跟踪
- **图像显示**: 实时图像渲染和覆盖层管理
- **系统控制**: 多线程任务调度和系统状态管理

### 技术特点
- **模块化设计**: 清晰的分层架构，便于维护和扩展
- **内存管理**: 统一的内存池管理，避免内存泄漏
- **多线程**: 图像采集、处理、显示并行执行
- **配置管理**: 灵活的参数配置和运行时调整
- **日志系统**: 完善的日志记录和调试支持

## 目录结构

```
ImageProcessor/
├── src/                    # 源代码目录
│   ├── main.c             # 主程序入口
│   ├── core/              # 核心控制模块
│   │   ├── system_controller.c    # 系统控制器
│   │   ├── image_manager.c        # 图像管理器
│   │   └── task_scheduler.c       # 任务调度器
│   ├── acquisition/       # 图像采集模块
│   │   ├── camera_driver.c        # 相机驱动
│   │   ├── frame_buffer.c         # 帧缓冲管理
│   │   └── sync_manager.c         # 同步管理
│   ├── processing/        # 图像处理模块
│   │   ├── filters/               # 滤波算法
│   │   │   ├── noise_filter.c
│   │   │   ├── edge_detector.c
│   │   │   └── histogram_equalizer.c
│   │   ├── algorithms/            # 检测算法
│   │   │   ├── feature_extractor.c
│   │   │   ├── object_detector.c
│   │   │   └── motion_tracker.c
│   │   └── enhancement/           # 图像增强
│   │       ├── brightness_adjuster.c
│   │       ├── contrast_enhancer.c
│   │       └── sharpening_filter.c
│   ├── display/           # 显示模块
│   │   ├── renderer.c             # 图像渲染器
│   │   ├── overlay_manager.c      # 覆盖层管理
│   │   └── output_formatter.c     # 输出格式化
│   ├── utils/             # 工具模块
│   │   ├── memory_pool.c          # 内存池管理
│   │   ├── math_utils.c           # 数学工具
│   │   ├── file_utils.c           # 文件操作
│   │   └── logger.c               # 日志系统
│   └── config/            # 配置管理
│       ├── param_loader.c         # 参数加载器
│       ├── calibration.c          # 标定管理
│       └── settings_manager.c     # 设置管理器
├── include/               # 头文件目录
│   ├── common/            # 通用定义
│   │   ├── types.h               # 类型定义
│   │   ├── constants.h           # 常量定义
│   │   └── error_codes.h         # 错误码定义
│   └── [模块对应的头文件目录]
├── docs/                  # 文档目录
│   └── 调用链路说明.md      # 详细的调用关系文档
├── config/                # 配置文件目录
│   └── system_config.ini  # 系统配置文件
├── Makefile              # 构建文件
└── README.md             # 项目说明
```

## 编译和运行

### 系统要求
- GCC 4.9+ 或其他支持C99的编译器
- pthread 库
- 数学库 (libm)

### 编译步骤

```bash
# 克隆或下载项目到本地
cd ImageProcessor

# 编译项目
make all

# 运行程序
make run

# 调试运行
make debug
```

### 其他命令

```bash
# 清理构建文件
make clean

# 查看代码统计
make stats

# 内存泄漏检查 (需要valgrind)
make memcheck

# 性能分析 (需要gprof)
make profile

# 查看帮助
make help
```

## 调用关系分析

本项目专门设计用于测试代码审查系统的调用链分析能力，具有以下特点：

### 复杂调用关系
1. **深度调用链**: main → system_controller → 各子模块 → 工具函数
2. **交叉依赖**: 模块间相互调用，形成复杂的依赖网络
3. **多线程调用**: 采集线程、处理线程、显示线程并行执行
4. **回调机制**: 任务完成通知、错误处理回调等

### 测试要点
1. **静态调用分析**: 分析函数间的直接调用关系
2. **动态调用分析**: 识别运行时的间接调用和回调
3. **模块依赖分析**: 分析模块间的依赖关系和接口
4. **资源管理分析**: 跟踪内存分配、释放的调用路径

详细的调用链路说明请参考 [调用链路说明.md](docs/调用链路说明.md)

## 配置说明

### 系统配置文件 (config/system_config.ini)

```ini
[camera]
width = 1920
height = 1080
fps = 30
format = RGB24

[processing]
max_features = 1000
quality_level = 0.01
min_distance = 10.0
use_harris = true

[display]
refresh_rate = 30
overlay_enabled = true

[system]
log_level = INFO
memory_pool_size = 67108864  # 64MB
max_threads = 4
```

## 开发说明

### 代码规范
- 遵循C99标准
- 使用统一的命名规范
- 每个函数都有详细的文档注释
- 错误处理和日志记录完整

### 扩展开发
- 新增算法模块请参考existing模块结构
- 添加新的配置参数需更新settings_manager
- 新增错误类型需在error_codes.h中定义
- 所有内存分配都应使用memory_pool

## 许可证

本项目仅用于测试目的，不用于商业用途。

## 联系方式

如有问题请联系开发团队。 