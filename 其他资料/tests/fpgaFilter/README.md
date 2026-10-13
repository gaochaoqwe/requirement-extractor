# FPGA静态分析过滤器测试包

## 📦 测试文件说明

本测试包包含完整的FPGA静态分析测试数据，用于验证FPGA过滤器的所有功能。

### 测试覆盖范围

#### 📊 测试数据统计
- **总问题数**: 20条
- **A类规则（建议准则）**: 9条 - 不确定规则，需AI审查
- **R类规则（强制准则）**: 11条 - 确定规则，直接保留
- **Verilog文件**: 18个
- **VHDL文件**: 2个

#### 🎯 规则覆盖详情

**A类规则（建议准则 - 不确定）**:
1. `A-1-5` - 时钟信号命名规范 (clock_divider.v:15)
2. `A-2-3` - 复位信号命名规范 (counter.v:23)
3. `A-3-1` - 状态机命名清晰度 (state_machine.v:45)
4. `A-4-2` - 模块端口顺序规范 (uart_tx.v:156)
5. `A-5-3` - 注释说明完整性 (spi_master.v:178)
6. `A-6-1` - case语句default分支 (decoder.v:267)
7. `A-7-2` - 参数定义规范 (encoder.v:289)
8. `A-8-1` - 实体名与文件名一致性 (controller.vhd:45)
9. `A-9-3` - 总线信号命名规范 (bus_interface.v:156)

**R类规则（强制准则 - 确定）**:
1. `R-1-1` - 组合逻辑环路检测 (alu.v:67)
2. `R-2-5` - 时钟域交叉同步 (fifo.v:89)
3. `R-3-2` - 复位信号连接 (memory_ctrl.v:102)
4. `R-4-1` - 阻塞/非阻塞赋值 (data_path.v:134)
5. `R-5-4` - 敏感列表完整性 (i2c_slave.v:201)
6. `R-1-3` - 锁存器推断 (pipeline.v:223)
7. `R-2-1` - 信号位宽匹配 (arbiter.v:245)
8. `R-3-5` - 溢出检测 (multiplier.v:312)
9. `R-4-3` - 除零保护 (divider.v:334)
10. `R-5-2` - 进程敏感列表 (processor.vhd:78)
11. `R-6-1` - 竞争冒险 (dma_ctrl.v:189)

## 🚀 使用方法

### 1. 生成测试数据

```bash
cd E:\code\requirement_extractor\backend\tests\fpgaFilter

# 生成Excel测试表单
python generate_test_excel.py

# 打包测试代码库
python create_test_package.py
```

### 2. 测试文件位置

生成后会在项目根目录创建两个文件：
- `T-Linter导出表单 copy.xlsx` - 测试Excel文件
- `fpga_test_codebase.zip` - 代码库压缩包

### 3. 前端测试流程

1. 启动后端服务器:
   ```bash
   cd E:\code\requirement_extractor\backend
   python run_fastapi.py
   ```

2. 访问前端界面:
   ```
   http://localhost:8085/static-analysis/fpga
   ```

3. 上传测试文件:
   - 上传 `T-Linter导出表单 copy.xlsx`
   - 上传 `fpga_test_codebase.zip`
   - 选择需要测试的规则
   - 点击"开始智能过滤"

### 4. 预期结果

#### 第一阶段：确定规则过滤
- 应保留 **11条** R类规则问题
- 这些问题无需AI审查，直接输出

#### 第二阶段：不确定规则AI审查
- **9条** A类规则问题将由AI审查
- AI会判断每个问题是否真正违反规范
- 根据代码上下文给出审查意见

#### 最终输出
- **确定规则问题单**: 包含所有R类确定问题
- **完整问题单**: 包含R类问题 + AI审查后保留的A类问题

## 📋 测试检查清单

- [ ] Excel解析正确（20条数据全部读取）
- [ ] 规则分类正确（9条A类，11条R类）
- [ ] 代码提取正确（从zip中提取对应行）
- [ ] 确定规则直接保留（11条）
- [ ] 不确定规则进入AI审查（9条）
- [ ] AI审查逻辑正确（基于代码上下文判断）
- [ ] 进度实时更新
- [ ] 问题单格式正确（12列）
- [ ] 下载功能正常

## 🔍 调试信息

### 查看日志
```bash
# 查看主日志
tail -f E:\code\requirement_extractor\backend\logs\app.log

# 查看FPGA API日志
tail -f E:\code\requirement_extractor\backend\logs\fpga_api.log
```

### 常见问题

1. **Excel解析失败**: 检查"结果1" sheet是否存在
2. **代码提取失败**: 检查zip文件结构，文件应在根目录
3. **AI审查不工作**: 检查OpenAI API配置
4. **进度不更新**: 检查前端轮询间隔设置

## 📝 文件清单

### 测试代码文件
```
test_codebase/
├── alu.v              # ALU模块 - R-1-1
├── arbiter.v          # 仲裁器 - R-2-1
├── bus_interface.v    # 总线接口 - A-9-3
├── clock_divider.v    # 时钟分频 - A-1-5
├── controller.vhd     # 控制器 - A-8-1
├── counter.v          # 计数器 - A-2-3
├── data_path.v        # 数据通路 - R-4-1
├── decoder.v          # 译码器 - A-6-1
├── divider.v          # 除法器 - R-4-3
├── dma_ctrl.v         # DMA控制 - R-6-1
├── encoder.v          # 编码器 - A-7-2
├── fifo.v             # FIFO - R-2-5
├── i2c_slave.v        # I2C从机 - R-5-4
├── memory_ctrl.v      # 内存控制 - R-3-2
├── multiplier.v       # 乘法器 - R-3-5
├── pipeline.v         # 流水线 - R-1-3
├── processor.vhd      # 处理器 - R-5-2
├── spi_master.v       # SPI主机 - A-5-3
├── state_machine.v    # 状态机 - A-3-1
└── uart_tx.v          # UART发送 - A-4-2
```

### 脚本文件
```
generate_test_excel.py    # 生成测试Excel
create_test_package.py    # 打包测试文件
README.md                 # 本文档
```

## ✅ 验证完整性

运行以下命令验证所有文件是否就绪：
```bash
python create_test_package.py
```

应该看到：
- ✓ 20个测试文件完整
- ✅ 代码库已打包
- 📦 生成的文件列表

---

**最后更新**: 2025-11-10
**作者**: FPGA静态分析团队
