# 混合FPGA测试项目

这个项目包含Verilog HDL和VHDL混合代码，用于测试FPGA代码审查功能对混合语言项目的支持。

## 文件结构

```
mixed_project/
├── verilog/
│   ├── spi_master.v       # SPI主控模块 (Verilog)
│   └── clock_divider.v    # 时钟分频器 (Verilog)
├── vhdl/
│   ├── uart_tx.vhd        # UART发送模块 (VHDL)
│   └── debouncer.vhd      # 按键消抖模块 (VHDL)
└── common/
    └── system_top.v       # 系统顶层模块 (Verilog)
```

## 故意埋入的Bug

### spi_master.v (Verilog)
- Bug 1: 状态机状态定义不规范
- Bug 2: 缺少状态定义
- Bug 3: 时钟生成逻辑错误
- Bug 4: 状态机逻辑不完整
- Bug 5: 缺少状态处理
- Bug 6: 数据传输逻辑错误

### clock_divider.v (Verilog)
- Bug 1: 计数器位宽不够
- Bug 2: 复位逻辑不完整
- Bug 3: 没有复位输出时钟
- Bug 4: 未检查参数有效性
- Bug 5: 时钟域问题

### uart_tx.vhd (VHDL)
- Bug 1: 状态机状态定义不完整
- Bug 2: 未使用的信号声明
- Bug 3: 敏感列表不完整
- Bug 4: 缺少others分支
- Bug 5: 信号赋值但未使用

### debouncer.vhd (VHDL)
- Bug 1: 未使用的信号声明
- Bug 2: 同步器级数不够
- Bug 3: 应该使用更多级的同步器
- Bug 4: 计数器逻辑错误
- Bug 5: 立即清零可能导致误触发
- Bug 6: 信号赋值但未使用

### system_top.v (Verilog)
- Bug 1: 未使用的信号声明
- Bug 2: 实例化时端口连接错误
- Bug 3: VHDL组件实例化语法错误
- Bug 4: 信号驱动冲突
- Bug 5: VHDL组件实例化语法错误
- Bug 6: 输出信号赋值错误
- Bug 7: 信号赋值但未使用

## 测试目的

验证FPGA代码审查系统能够：
1. 正确识别混合语言项目
2. 分别处理Verilog和VHDL代码
3. 检测跨语言组件集成问题
4. 识别状态机设计问题
5. 检测时序和时钟域问题
6. 提供针对不同语言的专业建议

## 特殊测试场景

- **语言混合**：测试系统对同一项目中包含多种HDL语言的处理能力
- **组件集成**：测试跨语言模块实例化的问题检测
- **接口匹配**：测试不同语言模块间接口的兼容性检查 