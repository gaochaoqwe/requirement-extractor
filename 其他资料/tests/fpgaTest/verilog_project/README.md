# Verilog测试项目

这个项目包含纯Verilog HDL代码，用于测试FPGA代码审查功能。

## 文件结构

```
verilog_project/
├── rtl/
│   ├── counter.v          # 8位计数器模块
│   └── alu.v             # 简单ALU模块
├── memory/
│   └── fifo.v            # FIFO存储器模块
└── top.v                 # 顶层模块
```

## 故意埋入的Bug

### counter.v
- Bug 1: always块敏感列表不完整（缺少reset）
- Bug 2: 组合逻辑使用assign而非always_comb
- Bug 3: 未使用的信号声明

### alu.v
- Bug 1: case语句缺少default分支
- Bug 2: 组合逻辑使用阻塞赋值
- Bug 3: 位宽不匹配可能导致溢出

### fifo.v
- Bug 1: 指针位宽不足
- Bug 2: 复位逻辑不完整
- Bug 3: full/empty标志逻辑错误

### top.v
- Bug 1: 端口悬空连接
- Bug 2: 信号多重驱动
- Bug 3: 未使用的信号声明

## 测试目的

验证FPGA代码审查系统能够：
1. 识别Verilog语法和语义错误
2. 检测设计规范问题
3. 发现时序和逻辑问题
4. 提供针对性的修改建议 