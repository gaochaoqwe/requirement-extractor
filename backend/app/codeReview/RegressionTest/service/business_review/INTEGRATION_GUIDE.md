# 智能链路审查 - 集成指南

本文档说明如何将新的智能链路审查集成到现有的`business_runner.py`中。

## 🎯 集成目标

将原有的固定链路审查替换为AI自主的智能链路审查，同时保持向后兼容。

## 📝 修改步骤

### 步骤1：导入新模块

在 `business_runner.py` 文件顶部添加导入：

```python
# 在现有导入后添加
from .chain_review_smart import run_smart_chain_review, enable_smart_chain_review
```

### 步骤2：修改链路审查逻辑

找到 `business_runner.py` 中的链路审查部分（大约在第1000-1200行），原代码类似：

```python
# 原代码（大约1100行左右）
log_concurrent_info(f"[链路审查] 开始调用AI规划链路", "business_runner")

# 调用链路规划
chains = plan_chains(
    task_id=task_id,
    software_type=software_type,
    kb=kb,
    entry_function=entry_function,
    project_root=project_root,
    dir_context=dir_items,
    files_docs=file_summaries
)

log_concurrent_info(f"[链路审查] 规划完成，共 {len(chains)} 条链路", "business_runner")

# ... 后续链路审查逻辑
```

**替换为**：

```python
# 检查是否启用智能链路审查
if enable_smart_chain_review():
    log_concurrent_info(f"[链路审查] 🚀 使用智能链路审查（AI自主模式）", "business_runner")
    
    # 运行智能链路审查
    smart_result = run_smart_chain_review(
        task_id=task_id,
        project_root=project_root,
        software_type=software_type,
        entry_function=entry_function,
        kb=kb
    )
    
    log_concurrent_info(
        f"[链路审查] 智能审查完成 - "
        f"发现{smart_result['features_count']}个功能模块, "
        f"识别{smart_result['problems_count']}个问题",
        "business_runner"
    )
    
    # 智能审查已经保存了问题到数据库，无需额外处理
    # 直接跳过原有的链路审查逻辑
    
else:
    # 使用原有的固定链路审查
    log_concurrent_info(f"[链路审查] 使用传统链路审查（固定算法）", "business_runner")
    
    chains = plan_chains(
        task_id=task_id,
        software_type=software_type,
        kb=kb,
        entry_function=entry_function,
        project_root=project_root,
        dir_context=dir_items,
        files_docs=file_summaries
    )
    
    log_concurrent_info(f"[链路审查] 规划完成，共 {len(chains)} 条链路", "business_runner")
    
    # ... 保持原有的链路审查逻辑
```

### 步骤3：处理进度更新（可选）

如果需要更细粒度的进度更新，可以在 `run_smart_chain_review` 函数中添加进度回调：

```python
def run_smart_chain_review(
    task_id: int,
    project_root: str,
    software_type: str,
    entry_function: str,
    kb: Dict[str, Any],
    progress_callback = None  # 新增参数
) -> Dict[str, Any]:
    # ... 在审查每个功能后
    if progress_callback:
        progress_callback(i, len(features), feature_name)
```

在调用时传入：

```python
def update_progress(current, total, feature_name):
    _update_progress(task_id, inc=1, message=f"审查功能: {feature_name}")

smart_result = run_smart_chain_review(
    task_id=task_id,
    project_root=project_root,
    software_type=software_type,
    entry_function=entry_function,
    kb=kb,
    progress_callback=update_progress
)
```

## 🔧 环境配置

### 启用智能链路审查

**方法1：环境变量**
```bash
# Windows PowerShell
$env:ENABLE_SMART_CHAIN_REVIEW = "true"

# Linux/Mac
export ENABLE_SMART_CHAIN_REVIEW=true
```

**方法2：配置文件**

在 `config.py` 中添加：
```python
ENABLE_SMART_CHAIN_REVIEW = os.getenv('ENABLE_SMART_CHAIN_REVIEW', 'true').lower() == 'true'
```

然后在 `chain_review_smart.py` 中修改：
```python
def enable_smart_chain_review() -> bool:
    from ....config import ENABLE_SMART_CHAIN_REVIEW
    return ENABLE_SMART_CHAIN_REVIEW
```

### 禁用智能链路审查（回退到旧版）

```bash
export ENABLE_SMART_CHAIN_REVIEW=false
```

## 📊 完整示例

下面是一个完整的集成示例：

```python
# ==================== 在 business_runner.py 中 ====================

# 1. 导入（文件顶部）
from .chain_review_smart import run_smart_chain_review, enable_smart_chain_review

# 2. 在 run_business_review 函数中（链路审查部分）
def run_business_review(task_id: int, project_root: str, ...) -> str:
    # ... 前面的代码保持不变（函数扫描、文件审查等）
    
    # ========== 链路审查部分 ==========
    log_concurrent_info("=" * 60, "business_runner")
    log_concurrent_info("步骤3/4：链路审查", "business_runner")
    log_concurrent_info("=" * 60, "business_runner")
    
    if enable_smart_chain_review():
        # 🚀 新版：智能链路审查
        log_concurrent_info("[链路审查] 使用AI自主智能审查模式", "business_runner")
        
        try:
            smart_result = run_smart_chain_review(
                task_id=task_id,
                project_root=project_root,
                software_type=software_type,
                entry_function=entry_function,
                kb=kb
            )
            
            log_concurrent_info(
                f"[链路审查] ✅ 智能审查完成 - "
                f"{smart_result['features_count']}个功能模块, "
                f"{smart_result['problems_count']}个问题",
                "business_runner"
            )
            
        except Exception as e:
            log_concurrent_error(f"[链路审查] ❌ 智能审查失败，回退到传统方法", "business_runner", e)
            # 回退到旧方法
            chains = plan_chains(...)
            # ... 旧的链路审查逻辑
            
    else:
        # 📋 旧版：传统链路审查
        log_concurrent_info("[链路审查] 使用传统固定算法审查模式", "business_runner")
        
        chains = plan_chains(
            task_id=task_id,
            software_type=software_type,
            kb=kb,
            entry_function=entry_function,
            project_root=project_root,
            dir_context=dir_items,
            files_docs=file_summaries
        )
        
        log_concurrent_info(f"[链路审查] 规划完成，共 {len(chains)} 条链路", "business_runner")
        
        # ... 原有的链路审查逻辑（保持不变）
        for i, chain in enumerate(chains):
            # ... 审查每条链路
            pass
    
    # ... 后续代码保持不变
```

## 🧪 测试方案

### 测试1：基础功能测试

1. 启用智能审查：
   ```bash
   export ENABLE_SMART_CHAIN_REVIEW=true
   ```

2. 运行代码审查任务

3. 检查日志：
   ```bash
   tail -f logs/bg_debug.txt | grep "智能链路审查"
   ```

### 测试2：对比测试

1. **第一次**：使用旧版
   ```bash
   export ENABLE_SMART_CHAIN_REVIEW=false
   # 运行审查
   # 记录：问题数量、问题类型、审查时间
   ```

2. **第二次**：使用新版
   ```bash
   export ENABLE_SMART_CHAIN_REVIEW=true
   # 运行审查
   # 记录：问题数量、问题类型、审查时间
   ```

3. **对比**：
   - 问题单质量
   - 功能模块划分合理性
   - 是否发现了旧版未发现的问题

### 测试3：大型项目测试

选择一个大型项目（>10000行代码）：

1. 观察是否超token（应该不会）
2. 观察功能模块划分是否合理
3. 观察审查耗时

## 🐛 故障排查

### 问题1：导入错误

```
ImportError: cannot import name 'run_smart_chain_review'
```

**解决**：
- 检查文件路径是否正确
- 确保 `executor/__init__.py` 存在
- 尝试 `cd backend && python -m app.codeReview.ConfigurationItem.service.business_review.chain_review_smart`

### 问题2：OpenAI API错误

```
Error: Invalid tool call format
```

**解决**：
- 检查 `config.py` 中的OpenAI配置
- 确保使用支持function calling的模型（gpt-4, gpt-3.5-turbo-1106等）

### 问题3：超token

```
Error: Context length exceeded
```

**解决**：
- 调整 `MAX_TOKENS_PER_FEATURE` 参数（降低）
- 调整 `max_iterations` 参数（降低）
- 检查是否有非常大的文件

### 问题4：AI未能发现功能

```
[智能链路审查] 未发现任何功能模块，审查终止
```

**解决**：
- 检查入口函数是否正确
- 检查项目结构是否正常
- 查看日志中的AI响应，可能需要调整提示词

## 📈 性能优化

### 优化1：并发审查功能模块

修改 `chain_review_smart.py`，使用线程池并发审查多个功能：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_smart_chain_review(...):
    # ... 功能发现
    
    # 并发审查
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_feature = {
            executor.submit(executor.review_feature, feature, software_type, kb): feature
            for feature in features
        }
        
        for future in as_completed(future_to_feature):
            feature = future_to_feature[future]
            try:
                problems = future.result()
                # ... 处理结果
            except Exception as e:
                log_concurrent_error(f"审查失败: {feature.get('name')}", e)
```

### 优化2：缓存文件大纲

避免重复读取相同文件：

```python
class CodeAnalysisTools:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.outline_cache = {}  # 缓存文件大纲
    
    def get_file_outline(self, relative_path: str):
        if relative_path in self.outline_cache:
            return self.outline_cache[relative_path]
        
        # ... 读取文件
        result = {...}
        self.outline_cache[relative_path] = result
        return result
```

## ✅ 验收标准

智能链路审查成功集成的标准：

- [ ] 环境变量控制开关有效
- [ ] 启用智能审查后，不会超token
- [ ] 日志中能看到功能发现和审查过程
- [ ] 问题单保存到数据库（chain_review_problems表）
- [ ] 前端能正常显示链路审查结果
- [ ] 禁用智能审查后，能正常回退到旧版
- [ ] 至少在3个不同项目上测试成功

## 🎉 完成后

集成完成后，向用户展示：

1. **功能模块发现日志**：展示AI如何理解项目
2. **审查过程日志**：展示AI如何使用工具探索代码
3. **问题单对比**：新旧版本的问题单对比

建议逐步推广：
1. Week 1: 内部测试，小型项目
2. Week 2: Beta测试，中型项目
3. Week 3: 全面推广，作为默认选项

## 📚 相关资源

- [SMART_CHAIN_REVIEW_README.md](./SMART_CHAIN_REVIEW_README.md) - 功能说明
- [smart_feature_discovery.py](./planner/smart_feature_discovery.py) - 功能发现实现
- [smart_chain_executor.py](./executor/smart_chain_executor.py) - 审查执行实现
- [chain_review_smart.py](./chain_review_smart.py) - 集成入口

