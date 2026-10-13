# 测试工程文件列表

## 📊 文件统计

- **C源文件**: 22个
- **头文件**: 22个
- **文档文件**: 3个（PROJECT_SPEC.md, README.md, PROJECT_FILES.md）
- **总文件数**: 47个

## 📁 文件清单

### 主程序
1. `main.c` - 主程序入口

### 功能1：系统初始化与配置管理
2. `system_init.c` / `system_init.h` - 系统初始化
3. `config_loader.c` / `config_loader.h` - 配置文件加载
4. `memory_manager.c` / `memory_manager.h` - 内存管理

### 功能2：GPS数据采集与处理
5. `gps_receiver.c` / `gps_receiver.h` - GPS数据接收
6. `nmea_parser.c` / `nmea_parser.h` - NMEA协议解析
7. `data_filter.c` / `data_filter.h` - 数据滤波
8. `ring_buffer.c` / `ring_buffer.h` - 环形缓冲区

### 功能3：路径规划与导航算法
9. `path_planner.c` / `path_planner.h` - 路径规划
10. `astar_algorithm.c` / `astar_algorithm.h` - A*算法
11. `road_network.c` / `road_network.h` - 道路网络
12. `navigation_guidance.c` / `navigation_guidance.h` - 导航指引

### 功能4：地图显示与用户交互
13. `map_display.c` / `map_display.h` - 地图显示
14. `map_loader.c` / `map_loader.h` - 地图加载
15. `graphics_renderer.c` / `graphics_renderer.h` - 图形渲染
16. `display_buffer.c` / `display_buffer.h` - 显示缓冲区

### 功能5：数据通信与远程更新
17. `comm_manager.c` / `comm_manager.h` - 通信管理
18. `tcp_client.c` / `tcp_client.h` - TCP客户端
19. `protocol_handler.c` / `protocol_handler.h` - 协议处理

### 功能6：系统日志与调试支持
20. `logger.c` / `logger.h` - 日志系统
21. `log_formatter.c` / `log_formatter.h` - 日志格式化
22. `log_rotator.c` / `log_rotator.h` - 日志轮转

### 文档文件
23. `PROJECT_SPEC.md` - 项目规格说明（包含6个功能的详细描述）
24. `README.md` - 项目说明文档
25. `PROJECT_FILES.md` - 本文件

## 🔍 功能与文件映射表

| 功能名称 | 涉及文件数 | 文件列表 |
|---------|----------|---------|
| 系统初始化 | 7个 | main.c, system_init.*, config_loader.*, memory_manager.* |
| GPS数据采集 | 9个 | main.c, gps_receiver.*, nmea_parser.*, data_filter.*, ring_buffer.* |
| 路径规划 | 9个 | main.c, path_planner.*, astar_algorithm.*, road_network.*, navigation_guidance.* |
| 地图显示 | 9个 | main.c, map_display.*, map_loader.*, graphics_renderer.*, display_buffer.* |
| 数据通信 | 7个 | main.c, comm_manager.*, tcp_client.*, protocol_handler.* |
| 系统日志 | 8个 | 所有文件都调用logger.*, logger.*, log_formatter.*, log_rotator.* |

## 🎯 跨文件调用关系

### main.c 调用链

```
main.c
├─→ system_initialize() → system_init.c
│   ├─→ load_config_file() → config_loader.c
│   ├─→ allocate_system_buffers() → memory_manager.c
│   └─→ logger_init() → logger.c
│
├─→ gps_receiver_start() → gps_receiver.c
│   ├─→ nmea_parser_init() → nmea_parser.c
│   ├─→ data_filter_init() → data_filter.c
│   └─→ rb_init() → ring_buffer.c
│
├─→ map_display_init() → map_display.c
│   ├─→ display_buffer_init() → display_buffer.c
│   └─→ graphics_renderer_init() → graphics_renderer.c
│
├─→ comm_initialize() → comm_manager.c
│   ├─→ protocol_handler_init() → protocol_handler.c
│   └─→ tcp_connect() → tcp_client.c
│
└─→ plan_route() → path_planner.c
    ├─→ astar_search() → astar_algorithm.c
    ├─→ load_road_network() → road_network.c
    └─→ generate_guidance() → navigation_guidance.c
```

### 数据流

```
GPS硬件
  ↓
nmea_parser (解析NMEA)
  ↓
data_filter (滤波)
  ↓
ring_buffer (缓存)
  ↓
path_planner (路径规划)
  ↓
map_display (地图显示)
  ↓
comm_manager (上传数据)
```

## 🐛 故意设计的问题分布

| 问题类型 | 数量 | 分布文件 |
|---------|------|---------|
| 业务逻辑问题 | 6个 | main.c, system_init.c, config_loader.c, memory_manager.c, data_filter.c, path_planner.c |
| 安全问题 | 5个 | config_loader.c, nmea_parser.c, system_init.c, comm_manager.c, logger.c |
| 并发问题 | 2个 | ring_buffer.c, logger.c |
| 性能问题 | 2个 | map_loader.c, data_filter.c |
| 其他问题 | 4个 | map_display.c, tcp_client.c, log_rotator.c, display_buffer.c |
| **总计** | **19个** | **14个文件包含问题** |

## 📝 代码注释标记

所有故意设计的问题都在代码中用注释标记：
```c
// 问题：这里没有sleep，会导致CPU占用过高
// 问题：内存分配失败时未释放已分配的缓冲区
// 问题：没有加锁，并发读写可能数据竞争
```

搜索 `// 问题：` 可以找到所有标记的问题。

## 🔧 编译说明（仅供参考）

虽然这是测试代码，不需要实际编译，但提供编译命令示例：

```bash
gcc -o navigation main.c system_init.c config_loader.c memory_manager.c \
    gps_receiver.c nmea_parser.c data_filter.c ring_buffer.c \
    path_planner.c astar_algorithm.c road_network.c navigation_guidance.c \
    map_display.c map_loader.c graphics_renderer.c display_buffer.c \
    comm_manager.c tcp_client.c protocol_handler.c \
    logger.c log_formatter.c log_rotator.c \
    -lm
```

## ✅ 验收清单

使用本测试工程进行代码审查时，应验证：

- [ ] AI能从main.c出发自动发现6个功能模块
- [ ] 每个功能都能追踪到相应的文件
- [ ] AI使用了get_file_outline探索文件结构
- [ ] AI使用了search_function_by_name跨文件搜索
- [ ] AI使用了get_function_context获取完整函数
- [ ] AI发现了至少10个以上的设计问题
- [ ] 问题描述包含具体的文件名和行号
- [ ] 问题分类准确（业务/安全/并发/性能）

---

**文件创建日期**: 2025-01-22  
**最后更新**: 2025-01-22  
**用途**: 代码审查功能测试

