# 嵌入式系统监控软件

这是一个用于嵌入式系统的监控软件示例，用于监控系统的CPU使用率、内存使用率、温度和电池电量等指标。

## 功能特点

- 实时监控系统各项指标
- 基于阈值的警告和严重状态检测
- 事件日志记录
- 可配置的监控参数
- 模块化设计，易于扩展

## 目录结构

```
c_test_project/
├── include/              # 头文件目录
│   ├── system_monitor.h  # 主头文件
│   ├── config_manager.h  # 配置管理模块
│   ├── data_collector.h  # 数据采集模块
│   ├── data_analyzer.h   # 数据分析模块
│   ├── logger.h          # 日志模块
│   ├── event_handler.h   # 事件处理模块
│   └── utils.h           # 工具函数模块
├── src/                  # 源代码目录
│   ├── system_monitor.c  # 主模块实现
│   ├── config_manager.c  # 配置管理模块实现
│   ├── data_collector.c  # 数据采集模块实现
│   ├── data_analyzer.c   # 数据分析模块实现
│   ├── logger.c          # 日志模块实现
│   ├── event_handler.c   # 事件处理模块实现
│   ├── utils.c           # 工具函数模块实现
│   └── main.c            # 主程序入口
├── config/               # 配置文件目录
│   └── system_monitor.conf # 系统配置文件
├── lib/                  # 库文件目录
├── obj/                  # 编译中间文件目录
├── bin/                  # 可执行文件目录
└── Makefile              # 构建脚本
```

## 编译与运行

### 编译

```bash
make
```

### 运行

```bash
make run
```

或者直接运行可执行文件：

```bash
./bin/system_monitor
```

### 清理

```bash
make clean
```

## 配置

可以通过修改 `config/system_monitor.conf` 文件来配置系统参数，或者通过命令行参数指定配置文件：

```bash
./bin/system_monitor -c path/to/config/file
```

## 模块说明

- **system_monitor**: 主模块，协调各个子模块的工作
- **config_manager**: 负责加载和管理系统配置
- **data_collector**: 负责采集系统数据
- **data_analyzer**: 负责分析系统数据并生成事件
- **logger**: 负责记录系统日志
- **event_handler**: 负责处理系统事件
- **utils**: 提供通用工具函数

## 注意事项

- 本软件仅为示例，实际使用时需要根据具体硬件平台进行适配
- 数据采集模块目前使用模拟数据，实际使用时需要替换为真实的硬件接口 