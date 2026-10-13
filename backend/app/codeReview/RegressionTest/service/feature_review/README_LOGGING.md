# 功能审查日志系统说明

## 日志结构

功能审查的日志按照以下结构组织：

```
logs/
  task_{task_id}/
    logs/
      task_summary.log                          # 任务总日志
      feature_{feature_id}_{feature_name}/      # 功能点子文件夹
        exploration.log                         # 代码探索阶段日志
        review.log                              # 代码审查阶段日志
        summary.log                             # 功能点总结日志
```

## 日志内容

### 1. 任务总日志 (task_summary.log)
- 记录整个功能审查任务的开始和结束
- 包含每个功能点的处理进度
- 任务级别的错误和警告

### 2. 代码探索日志 (exploration.log)
- 记录AI Agent探索代码的过程
- 包含探索策略和发现的相关文件、函数
- 探索阶段的所有AI调用和工具使用

### 3. 代码审查日志 (review.log)
- 记录AI Agent审查代码的过程
- 包含发现的每个问题的详细信息
- 审查阶段的所有AI调用和分析结果

### 4. 功能点总结日志 (summary.log)
- 功能点的基本信息（名称、描述）
- 探索和审查的总结性信息
- 发现的问题数量和保存状态
- 功能点完成状态（成功/失败）

## 使用示例

### 查看特定任务的日志

```bash
# 查看任务总日志
cat logs/task_123/logs/task_summary.log

# 查看特定功能点的探索日志
cat logs/task_123/logs/feature_1_雷达扫描功能/exploration.log

# 查看特定功能点的审查日志
cat logs/task_123/logs/feature_1_雷达扫描功能/review.log

# 查看功能点总结
cat logs/task_123/logs/feature_1_雷达扫描功能/summary.log
```

### 日志查看工具

每个任务目录下都会生成一个`view_logs.py`脚本（计划功能），方便查看和分析日志。

## 日志级别

- **INFO**: 常规信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息

## 日志时间戳格式

所有日志都包含精确到毫秒的时间戳：
```
[2025-10-28 11:04:23.789] [INFO] 消息内容
```

## 注意事项

1. 日志文件自动创建，无需手动管理
2. 功能名称中的非法字符会自动转换为下划线
3. 功能名称过长时会自动截断为50字符
4. 所有日志同时输出到控制台和文件
5. 异常信息会自动记录完整的堆栈跟踪

## 日志查询建议

使用`grep`进行日志查询：

```bash
# 查找所有错误
grep "\[ERROR\]" logs/task_123/logs/task_summary.log

# 查找特定功能点的问题
grep "问题" logs/task_123/logs/feature_1_*/review.log

# 查找AI调用
grep "AI Agent" logs/task_123/logs/feature_1_*/exploration.log
```

