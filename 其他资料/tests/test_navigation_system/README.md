# 智能导航系统 - 测试工程

## 📋 项目简介

这是一个用于测试代码审查功能的C语言测试工程，模拟了一个完整的车载智能导航系统。

## 🎯 设计目的

1. **测试AI审查的功能发现能力**：AI应能从`main`函数出发，自动识别6个主要功能模块
2. **测试跨文件代码探索**：每个功能都涉及多个文件，需要AI使用各种工具进行探索
3. **测试问题发现能力**：代码中故意设计了多种业务逻辑和技术问题
4. **测试工具使用**：验证AI能否正确使用7个代码分析工具

## 📂 项目结构

```
test_navigation_system/
├── main.c                    # 主程序（入口函数）
├── PROJECT_SPEC.md           # 项目规格说明（包含所有功能描述）
├── README.md                 # 本文件
│
├── 功能1：系统初始化
│   ├── system_init.c/h
│   ├── config_loader.c/h
│   └── memory_manager.c/h
│
├── 功能2：GPS数据采集
│   ├── gps_receiver.c/h
│   ├── nmea_parser.c/h
│   ├── data_filter.c/h
│   └── ring_buffer.c/h
│
├── 功能3：路径规划
│   ├── path_planner.c/h
│   ├── astar_algorithm.c/h
│   ├── road_network.c/h
│   └── navigation_guidance.c/h
│
├── 功能4：地图显示
│   ├── map_display.c/h
│   ├── map_loader.c/h
│   ├── graphics_renderer.c/h
│   └── display_buffer.c/h
│
├── 功能5：数据通信
│   ├── comm_manager.c/h
│   ├── tcp_client.c/h
│   └── protocol_handler.c/h
│
└── 功能6：系统日志
    ├── logger.c/h
    ├── log_formatter.c/h
    └── log_rotator.c/h
```

## 🔍 如何使用

### 用于自动审查（链路审查）

```yaml
审查配置：
  - 审查模式：自动审查 → 链路审查（智能版）
  - 入口函数：main
  - 软件类型：车载导航软件
  - 项目路径：E:\code\requirement_extractor\backend\tests\test_navigation_system
```

**预期结果**：
- AI应自动发现6个功能模块
- 每个功能模块应生成针对性的问题单
- 总问题数：预计15-25个

### 用于功能审查

从`PROJECT_SPEC.md`中复制功能描述，例如：

```yaml
功能名称：GPS数据采集与处理

功能描述：
系统需要持续从GPS模块接收位置数据并进行处理：
1. 从GPS串口接收NMEA格式的原始数据
2. 解析NMEA数据包，提取经度、维度、速度等信息
3. 对GPS数据进行滤波处理，去除异常定位点
4. 将处理后的数据存储到环形缓冲区
5. 当GPS信号丢失时，标记数据为无效
```

**预期结果**：
- AI应能定位到`gps_receiver.c`、`nmea_parser.c`等相关文件
- 发现环形缓冲区的并发问题
- 发现NMEA解析的缓冲区溢出风险

## 🐛 故意设计的问题

### 业务逻辑问题

1. **main.c:94** - 主循环没有sleep，导致CPU占用过高
2. **system_init.c:45** - 初始化失败时没有清理已加载的配置
3. **config_loader.c:65** - 端口范围检查可能过于严格（<1024的端口可能有效）
4. **memory_manager.c:30** - 内存分配失败时未释放已分配的缓冲区
5. **data_filter.c:95** - 速度过高时只警告不标记为无效
6. **path_planner.c:75** - 检查路径偏离时应该检查最近点而非第一个点

### 安全问题

7. **config_loader.c:50** - fgets可能导致缓冲区溢出
8. **nmea_parser.c:38** - strncpy可能截断数据
9. **system_init.c:28** - 配置文件路径硬编码
10. **comm_manager.c:19** - 服务器地址硬编码
11. **logger.c:18** - 日志文件路径硬编码

### 并发问题

12. **ring_buffer.c:72** - 没有加锁，并发读写可能数据竞争
13. **logger.c:68** - 并发写入日志可能导致混乱

### 性能问题

14. **map_loader.c:14** - 地图加载应该异步，避免阻塞主线程
15. **data_filter.c:102** - 时间相同时可能导致除零错误

### 其他问题

16. **map_display.c:41** - 地图加载失败时是否应该继续渲染？
17. **tcp_client.c:18** - 没有实现断线重连机制
18. **log_rotator.c:13** - 日志轮转时可能丢失数据
19. **display_buffer.c:40** - 应该检查缓冲区是否会溢出

## 📊 统计信息

- **总文件数**：40个（20个.c文件 + 20个.h文件）
- **总代码行数**：约2500行
- **功能数量**：6个主要功能
- **跨文件调用**：每个功能涉及4-7个文件
- **设计问题数**：19个已知问题

## 🛠️ AI工具使用示例

### get_file_outline
```
用途：快速了解文件结构
示例：get_file_outline("gps_receiver.c")
预期：看到parse_nmea_sentence, filter_gps_data等函数
```

### search_function_by_name
```
用途：全局搜索函数定义
示例：search_function_by_name("calculate_distance")
预期：找到data_filter.c和path_planner.c中的定义
```

### get_function_context
```
用途：获取完整函数代码
示例：get_function_context("ring_buffer.c", 72)
预期：看到rb_write函数，发现并发问题
```

### read_file_range
```
用途：读取特定代码段
示例：read_file_range("main.c", 80, 110)
预期：看到主循环，发现没有sleep
```

### search_function_in_file
```
用途：追踪函数调用
示例：search_function_in_file("main.c", "log_message")
预期：找到所有日志调用位置
```

### read_file
```
用途：读取小文件
示例：read_file("logger.h")
预期：看到日志级别定义和函数接口
```

### list_directory
```
用途：浏览项目结构
示例：list_directory(".")
预期：看到所有源文件
```

## ✅ 验收标准

### 自动审查（链路审查）

- [ ] AI能识别出至少5个功能模块
- [ ] 每个功能模块都有问题单
- [ ] 发现至少10个设计问题
- [ ] 问题描述准确且有具体代码位置

### 功能审查

- [ ] 根据功能描述能定位到正确的文件
- [ ] 能发现该功能相关的所有问题
- [ ] 能追踪跨文件的函数调用关系

### 工具使用

- [ ] AI使用了至少5种不同的工具
- [ ] 工具调用顺序合理（先outline后detail）
- [ ] 没有重复无效的工具调用

## 📝 使用建议

1. **首次测试**：使用自动审查，观察AI如何自动发现功能
2. **对比测试**：手动审查一遍，对比AI发现的问题
3. **针对性测试**：选择特定功能进行功能审查
4. **工具分析**：查看日志，分析AI的工具调用链

## 📚 相关文档

- `PROJECT_SPEC.md` - 详细的功能规格说明（包含所有功能的名称和描述）
- `CODE_REVIEW_MODES.md` - 代码审查模式说明（在上级目录）
- `SMART_CHAIN_REVIEW_README.md` - 智能链路审查说明（在business_review目录）

---

**创建日期**：2025-01-22  
**用途**：代码审查功能测试  
**维护者**：开发团队

