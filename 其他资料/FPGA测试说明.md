# FPGA静态分析测试说明

## 📋 问题修复

已修复Excel文件格式问题：
- ❌ 之前：7列格式，导致验证失败
- ✅ 现在：8列格式（A-H），符合FPGA处理器要求

### 8列格式说明
```
A列：序号
B列：检测项（规则编号）
C列：问题描述
D列：文件名
E列：行号
F列：列号
G列：严重程度
H列：建议
```

## 🚀 快速开始

### 步骤1：生成测试数据

双击运行：`E:\code\requirement_extractor\生成测试数据.bat`

这将生成：
1. `T-Linter导出表单 copy.xlsx` - 测试Excel（20条数据）
2. `fpga_test_codebase.zip` - 代码库压缩包（20个文件）

### 步骤2：上传测试

1. 确保后端服务器正在运行
2. 访问：`http://localhost:8085/static-analysis/fpga`
3. 上传刚生成的两个文件
4. 选择FPGA规则（或全选）
5. 点击"开始智能过滤"

### 步骤3：查看结果

观察前端显示：
- ✅ 进度条应该从0开始增长
- ✅ 确定规则：11条（R类规则）
- ✅ 不确定规则：9条（A类规则）
- ✅ AI审查进度实时更新
- ✅ 可下载两份问题单

## 📊 测试数据覆盖

### A类规则（建议准则 - 不确定）：9条
1. A-1-5：时钟信号命名
2. A-2-3：复位信号命名
3. A-3-1：状态机命名
4. A-4-2：端口顺序
5. A-5-3：注释完整性
6. A-6-1：case default
7. A-7-2：参数定义
8. A-8-1：实体文件名
9. A-9-3：总线命名

### R类规则（强制准则 - 确定）：11条
1. R-1-1：组合逻辑环路
2. R-2-5：时钟域同步
3. R-3-2：复位连接
4. R-4-1：阻塞赋值
5. R-5-4：敏感列表
6. R-1-3：锁存器推断
7. R-2-1：位宽匹配
8. R-3-5：溢出检测
9. R-4-3：除零保护
10. R-5-2：进程敏感列表
11. R-6-1：竞争冒险

## 🔍 日志位置

如果遇到问题，查看日志：
```
后端主日志：
E:\code\requirement_extractor\backend\logs\app.log

FPGA API日志：
E:\code\requirement_extractor\backend\app\staticAnalysis\filter\logs\system\fpga_api.log

FPGA Excel处理日志：
E:\code\requirement_extractor\backend\app\staticAnalysis\filter\logs\system\fpga_excel_processor.log

FPGA增强服务日志：
E:\code\requirement_extractor\backend\app\staticAnalysis\filter\logs\system\fpga_enhanced_service.log
```

## ⚠️ 常见问题

### 1. Excel验证失败
- 检查是否是8列格式
- 检查"结果1" sheet是否存在
- 重新运行生成脚本

### 2. 代码提取失败
- 检查zip文件是否损坏
- 文件应在zip根目录，不要有子文件夹

### 3. 前端进度不更新
- 检查后端日志确认任务是否真正启动
- 检查session_id是否匹配
- F12查看浏览器控制台是否有错误

### 4. AI审查不工作
- 检查OpenAI API配置
- 查看相关日志确认API调用

---

**最后更新**: 2025-11-10 23:05
**状态**: ✅ Excel格式已修复，可以测试
