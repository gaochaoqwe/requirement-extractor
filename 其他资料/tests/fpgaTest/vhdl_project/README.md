# VHDL测试项目

这个项目包含纯VHDL代码，用于测试FPGA代码审查功能。

## 文件结构

```
vhdl_project/
├── src/
│   ├── counter.vhd        # 8位计数器实体
│   └── alu.vhd           # 简单ALU实体
├── memory/
│   └── ram.vhd           # RAM存储器实体
└── top.vhd               # 顶层实体
```

## 故意埋入的Bug

### counter.vhd
- Bug 1: 未使用的信号声明
- Bug 2: 时钟敏感列表不完整（缺少reset）
- Bug 3: 类型转换问题
- Bug 4: 组合逻辑敏感列表不完整
- Bug 5: 信号赋值但未使用

### alu.vhd
- Bug 1: 位宽不匹配
- Bug 2: case语句缺少others分支
- Bug 3: 信号多重驱动
- Bug 4: 类型转换错误
- Bug 5: 未使用的信号赋值

### ram.vhd
- Bug 1: 数组大小定义错误
- Bug 2: 未使用的信号声明
- Bug 3: 读写逻辑混乱
- Bug 4: 写操作中进行读操作
- Bug 5: 异步读操作导致竞争
- Bug 6: 信号赋值但未使用

### top.vhd
- Bug 1: 未使用的信号声明
- Bug 2: 端口映射使用open
- Bug 3: 信号多重驱动
- Bug 4: 信号赋值但未使用

## 测试目的

验证FPGA代码审查系统能够：
1. 识别VHDL语法和语义错误
2. 检测类型转换问题
3. 发现信号驱动冲突
4. 检测未使用的信号和端口
5. 提供VHDL专业的修改建议 