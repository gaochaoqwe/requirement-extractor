# 链路审查Round 3幻觉问题深度分析

## 🚨 问题描述

在链路审查的Round 3（main函数验证阶段），AI产生了严重的幻觉问题，凭空创造了大量不存在的文件和功能模块。

### 实际项目结构（tiny_test）
```
tiny_test/
├── math_utils.c  (包含 add, square, main 函数)
└── math_utils.h  (函数声明)
```

### AI幻觉产出（Round 3）
```json
{
  "features": [
    {
      "name": "程序入口和主控制流",
      "related_files": ["main.c"],  // ❌ 不存在
      "key_functions": ["init_system", "setup_environment", "main_loop"]  // ❌ 都不存在
    },
    {
      "name": "数学计算核心",
      "related_files": ["math_utils.c", "calculator.c", "advanced_math.c"],  // ❌ 后两个不存在
      "key_functions": ["multiply", "divide", "sqrt", "power"]  // ❌ 都不存在
    },
    {
      "name": "接口和API层",
      "related_files": ["interface.h", "api.c", "binding.c"],  // ❌ 全部不存在
      "key_functions": ["init_interface", "register_functions", "bind_functions"]  // ❌ 全部不存在
    },
    {
      "name": "数据处理和验证",
      "related_files": ["data_processor.c", "validator.c", "error_handler.c"],  // ❌ 全部不存在
      "key_functions": ["validate_input", "process_data", "handle_error"]  // ❌ 全部不存在
    }
  ]
}
```

**幻觉率**: ~80% 的内容是虚构的！

---

## 🔍 根本原因分析

### 原因1：递归探索失败 ⭐⭐⭐⭐⭐

**日志证据**（第433行）：
```
[Round 3] AI返回类型错误: <class 'dict'>, 内容: {
  'function_name': 'main', 
  'next_targets': ['add', 'square'], 
  ...
}
[Round 3] 函数 main 分析完成，建议探索: []  // ❌ 返回空列表！
[Round 3] 递归探索完成，共探索 1 个函数  // ❌ 只探索了main，没有继续
```

**问题**：
```python
# 在 _analyze_function_for_exploration 返回了dict而不是list
# 导致 next_targets 为空，递归立即终止

analysis = {
    "function_name": "main",
    "next_targets": ["add", "square"],  # 这里有目标
    ...
}

# 但是代码期望返回一个list，导致解析失败
suggested_targets = analysis.get("next_targets", [])  # 获取成功
# 但后续处理逻辑可能有问题，导致没有继续探索add和square
```

**结果**：
- ✗ AI只看到了main函数的代码
- ✗ 没有看到add和square的实现
- ✗ Round 3的"验证"变成了"凭空想象"

---

### 原因2：Round 3提示词设计缺陷 ⭐⭐⭐⭐⭐

**日志证据**（第444-492行）：
```python
prompt = """
你正在整合递归探索的结果（第3轮分析：验证和调整）。

【第2轮识别的功能模块】
- 数学工具库: 提供基础的数学运算功能
- 程序入口: 提供程序的入口点
- 接口声明: 提供函数接口的声明

【递归探索发现】
1. main (unknown)  // ❌ 只有这一行！

【任务】
基于实际的函数调用关系，验证和调整功能划分...
"""
```

**问题剖析**：

1. **输入信息严重不足**：
   ```
   【递归探索发现】只有 "1. main (unknown)"
   
   没有：
   - ✗ main函数的实际代码
   - ✗ add、square函数的代码
   - ✗ 实际的函数调用关系
   - ✗ 实际的文件列表
   ```

2. **AI被迫"猜测"**：
   ```
   Round 2说：有"数学工具库"、"程序入口"、"接口声明"
         ↓
   Round 3只给：main函数名（连代码都没有）
         ↓
   AI想：这些功能应该对应哪些文件？
         ↓
   AI猜：数学工具库 → 肯定有 calculator.c, advanced_math.c
         接口声明 → 肯定有 interface.h, api.c
         程序入口 → 肯定有 main.c, init.c
   ```

3. **缺少约束机制**：
   ```python
   # 提示词中没有明确说明：
   【重要约束】
   1. 只能使用探索中实际发现的文件
   2. 只能使用探索中实际发现的函数
   3. 如果没有探索到某个功能的证据，标记为"未验证"
   4. 不要猜测或添加不存在的内容
   ```

---

### 原因3：缺少实际代码输入 ⭐⭐⭐⭐⭐

**对比分析**：

| 轮次 | 输入内容 | 信息量 | AI行为 |
|------|---------|--------|--------|
| Round 1 | 目录树 + 项目概览 | 少，但足够 | ✓ 基于实际结构推断 |
| Round 2 | 函数签名列表（6个） | 中等 | ✓ 基于实际签名分析 |
| Round 3 | "1. main (unknown)" | **极少** | ✗ **凭空想象** |

**应该提供什么**：
```python
【递归探索发现】

1. main函数（tiny_test/math_utils.c:57）
   ```c
   int main() {
       int num1 = 5;
       int num2 = 3;
       int num3 = 2;
       
       int sum = add(num1, num2);      // 调用add
       int result = square(num3);      // 调用square
       
       return 0;
   }
   ```
   调用关系：main → add, square

2. add函数（tiny_test/math_utils.c:15）
   ```c
   int add(int a, int b) {
       int result;
       if (a > 0) {
           result = result + a + b;  // Bug: 未初始化
       } else {
           result = a + b;
       }
       return result;
   }
   ```

3. square函数（tiny_test/math_utils.c:40）
   ```c
   int square(int x) {
       int arr[5] = {1, 2, 3, 4, 5};
       int index = x;
       return arr[index] * arr[index];  // Bug: 可能越界
   }
   ```

【实际文件列表】
- tiny_test/math_utils.c
- tiny_test/math_utils.h

【实际函数列表】
- main, add, square (in math_utils.c)
- add, square 声明 (in math_utils.h)
```

---

### 原因4：AI的"常识"作祟 ⭐⭐⭐⭐

**AI的思维过程**（推测）：
```
AI接收到：
  - "数学工具库"
  - "接口声明"
  - "程序入口"

AI的"常识"：
  - 数学工具库？那应该有：
    ✗ calculator.c (计算器)
    ✗ advanced_math.c (高级数学)
    ✗ 加减乘除、平方根、幂运算...

  - 接口声明？那应该有：
    ✗ interface.h (接口头文件)
    ✗ api.c (API实现)
    ✗ binding.c (绑定代码)

  - 程序入口？那应该有：
    ✗ main.c (主文件)
    ✗ init.c (初始化)
    ✗ init_system, setup_environment...

AI输出：一个"典型的"C项目结构（但完全是虚构的）
```

**问题**：
- AI的训练数据中有大量的"典型C项目"结构
- 当输入信息不足时，AI会回退到这些"常识"模式
- 而不是诚实地说"我没有足够的信息"

---

### 原因5：验证机制缺失 ⭐⭐⭐⭐

**当前流程**：
```
Round 2 → 识别功能模块（基于函数签名）
   ↓
Round 3 → AI自由发挥（没有任何验证）
   ↓
后续审查 → 基于虚假信息进行（灾难！）
```

**缺少的验证**：
1. ✗ 文件存在性检查
   ```python
   for file in AI_output["related_files"]:
       if not os.path.exists(file):
           warning(f"文件 {file} 不存在！")
   ```

2. ✗ 函数存在性检查
   ```python
   for func in AI_output["key_functions"]:
       if func not in actual_functions:
           warning(f"函数 {func} 不存在！")
   ```

3. ✗ 交叉验证
   ```python
   # Round 2发现了哪些函数？
   round2_functions = {"add", "square", "main"}
   
   # Round 3说有哪些函数？
   round3_functions = {
       "add", "square", "multiply", "divide",  # ← 后两个从哪来的？
       "init_system", "setup_environment", ...
   }
   
   # 差异检查
   hallucinated = round3_functions - round2_functions
   # → {"multiply", "divide", "init_system", ...}
   ```

---

## 💡 解决方案

### 方案1：修复递归探索逻辑 ⭐⭐⭐⭐⭐（最重要）

**问题代码**（推测）：
```python
def _analyze_function_for_exploration(self, func_name, func_code, ...):
    # AI返回一个dict
    analysis = AI.call(prompt)
    
    # 但是调用方期望返回list
    return analysis  # ❌ 类型不匹配

# 调用方
suggested_targets = analysis.get("next_targets", [])
next_targets.extend(suggested_targets)  # ❌ 可能为空
```

**修复方案**：
```python
def _recursive_exploration(self, ...):
    while current_targets and current_depth < max_depth:
        next_targets = []
        
        for func_name in current_targets:
            # 读取函数代码
            func_code = self._get_function_code(func_name)
            
            # 让AI分析
            analysis = self._analyze_function_for_exploration(...)
            
            # ✓ 添加调试日志
            log_debug(f"[Round 3] AI返回: {analysis}", "progressive_discovery")
            log_debug(f"[Round 3] next_targets类型: {type(analysis.get('next_targets'))}", "progressive_discovery")
            
            # ✓ 健壮处理
            suggested = analysis.get("next_targets", [])
            if isinstance(suggested, list):
                next_targets.extend(suggested)
            else:
                log_warning(f"[Round 3] next_targets不是list: {suggested}", "progressive_discovery")
            
            # ✓ 确保继续探索
            explored_functions.add(func_name)
            exploration_history.append({
                "function_name": func_name,
                "code": func_code,
                "analysis": analysis
            })
        
        # ✓ 确保有下一步目标
        if not next_targets:
            log_warning("[Round 3] 没有更多探索目标，提前终止", "progressive_discovery")
            break
        
        current_targets = list(set(next_targets))[:max_functions_per_depth]
        current_depth += 1
```

---

### 方案2：增强Round 3提示词 ⭐⭐⭐⭐⭐（最重要）

**修复后的提示词**：
```python
def _integrate_exploration_results(self, exploration_history, previous_memory):
    # 构建完整的探索上下文
    exploration_context = []
    for i, item in enumerate(exploration_history, 1):
        exploration_context.append(f"""
{i}. {item['function_name']} ({item.get('file', 'unknown')}:{item.get('line', 0)})
   ```c
   {item['code'][:500]}  # 显示实际代码
   ```
   调用关系: {item.get('calls', [])}
""")
    
    # ✓ 提取实际的文件列表
    actual_files = set()
    for item in exploration_history:
        if 'file' in item:
            actual_files.add(item['file'])
    
    # ✓ 提取实际的函数列表
    actual_functions = {item['function_name'] for item in exploration_history}
    
    prompt = f"""
你正在整合递归探索的结果（第3轮分析：验证和调整）。

【第2轮识别的功能模块】
{self._format_previous_features(previous_memory)}

【递归探索发现】（实际代码）
{chr(10).join(exploration_context)}

【重要约束】
1. ✓ 只能使用以下实际发现的文件：
   {list(actual_files)}
   
2. ✓ 只能使用以下实际发现的函数：
   {list(actual_functions)}
   
3. ✓ 如果第2轮识别的某个功能在探索中**没有找到证据**：
   - 标记为 "verified": false
   - 置信度降为 "low"
   - 说明理由："未在探索中发现相关代码"
   
4. ✗ **禁止猜测或添加不存在的文件/函数**
   - 如果某个功能只是推测，明确标注
   - 不要凭空创造文件名

【任务】
基于**实际探索到的代码**，验证和调整功能划分：
1. 确认哪些功能模块是准确的（有实际代码支持）
2. 调整不准确的功能划分
3. 删除没有证据支持的功能
4. 合并相关的功能模块

【返回格式】JSON（完整的features数组）
```json
{{
  "features": [
    {{
      "id": "feature_X",
      "name": "功能模块名称",
      "description": "功能描述",
      "confidence": "high/medium/low",
      "priority": "high/medium/low",
      "evidence": "基于探索发现的具体证据（引用实际函数名和代码片段）",
      "related_files": ["实际文件1.c"],  // 只能来自实际发现的文件
      "key_functions": ["实际函数1"],    // 只能来自实际发现的函数
      "call_chain": "实际的调用链",
      "verified": true/false,  // 是否在探索中得到验证
      "sub_features": [...]
    }}
  ]
}}
```

【示例：如何处理未验证的功能】
如果Round 2说有"接口声明"功能，但探索中没有发现interface.h或相关函数：
```json
{{
  "id": "feature_interface",
  "name": "接口声明",
  "verified": false,
  "confidence": "low",
  "evidence": "第2轮基于函数签名推测，但递归探索中未找到独立的接口文件或API函数",
  "related_files": [],  // 空，因为没有实际证据
  "key_functions": []
}}
```
"""
    
    try:
        result, _ = self.ai_client.call_ai_stream(prompt)
        features = self._parse_ai_features(result)
        
        # ✓ 验证AI输出
        features = self._validate_features(features, actual_files, actual_functions)
        
        return features
    except Exception as e:
        log_error(f"[Round 3] 整合探索结果失败: {e}", "progressive_discovery")
        return previous_memory.get("features", [])
```

---

### 方案3：增加后验证机制 ⭐⭐⭐⭐

```python
def _validate_features(
    self, 
    features: List[Dict], 
    actual_files: Set[str], 
    actual_functions: Set[str]
) -> List[Dict]:
    """验证AI输出的功能列表，移除幻觉内容"""
    
    validated_features = []
    warnings = []
    
    for feature in features:
        validated_feature = feature.copy()
        
        # 1. 验证文件
        related_files = feature.get('related_files', [])
        valid_files = []
        for file in related_files:
            # 检查文件是否实际存在
            if any(file in actual_file or actual_file.endswith(file) for actual_file in actual_files):
                valid_files.append(file)
            else:
                warnings.append(f"[警告] 功能 {feature['name']} 引用了不存在的文件: {file}")
        
        validated_feature['related_files'] = valid_files
        
        # 2. 验证函数
        key_functions = feature.get('key_functions', [])
        valid_functions = []
        for func in key_functions:
            # 提取函数名（可能包含参数）
            func_name = func.split('(')[0].strip()
            if func_name in actual_functions:
                valid_functions.append(func)
            else:
                warnings.append(f"[警告] 功能 {feature['name']} 引用了不存在的函数: {func}")
        
        validated_feature['key_functions'] = valid_functions
        
        # 3. 调整置信度
        if not valid_files or not valid_functions:
            validated_feature['confidence'] = 'low'
            validated_feature['verified'] = False
            validated_feature['evidence'] = (
                validated_feature.get('evidence', '') + 
                " [警告：缺少实际文件或函数支持]"
            )
        
        # 4. 递归验证子功能
        if 'sub_features' in validated_feature:
            validated_feature['sub_features'] = self._validate_features(
                validated_feature['sub_features'],
                actual_files,
                actual_functions
            )
        
        validated_features.append(validated_feature)
    
    # 打印警告
    if warnings:
        log_warning(f"[Round 3] 发现 {len(warnings)} 个幻觉问题:", "progressive_discovery")
        for w in warnings:
            log_warning(f"  {w}", "progressive_discovery")
    
    return validated_features
```

---

### 方案4：提供实际文件列表作为约束 ⭐⭐⭐⭐

```python
def _round_3_main_function_verification(self) -> Dict[str, Any]:
    """Round 3: 增加实际文件列表作为约束"""
    
    # 获取实际文件列表
    actual_files = []
    for ext in ['.c', '.cpp', '.h', '.hpp']:
        actual_files.extend(
            glob.glob(f"{self.project_root}/**/*{ext}", recursive=True)
        )
    
    # 转换为相对路径
    actual_files = [
        os.path.relpath(f, self.project_root) for f in actual_files
    ]
    
    log_debug(f"[Round 3] 实际文件列表: {actual_files}", "progressive_discovery")
    
    # 传递给后续处理
    exploration_result = self._recursive_exploration(...)
    exploration_result['actual_files'] = actual_files
    
    return exploration_result
```

---

### 方案5：改进AI判断提示 ⭐⭐⭐

```python
system_prompt += """
【重要原则】
1. **诚实原则**：如果没有看到实际代码，不要猜测
2. **证据原则**：每个功能必须有实际的代码证据支持
3. **保守原则**：不确定的标记为 "verified": false, "confidence": "low"

【禁止行为】
✗ 不要基于"常见项目结构"推测文件名
✗ 不要基于"应该有什么功能"添加不存在的函数
✗ 不要创造性地"补全"缺失的信息

【鼓励行为】
✓ 诚实地标注哪些功能得到验证、哪些没有
✓ 对于未验证的功能，明确说明原因
✓ 如果探索不充分，建议需要继续探索哪些部分
"""
```

---

## 📊 修复效果对比

### 修复前
```json
{
  "features": 4,
  "hallucinated_files": 10,  // 虚构的文件
  "hallucinated_functions": 20,  // 虚构的函数
  "accuracy": 20%
}
```

### 修复后（预期）
```json
{
  "features": 1-2,  // 更少但更准确
  "hallucinated_files": 0,
  "hallucinated_functions": 0,
  "accuracy": 100%,
  "example_output": {
    "id": "feature_math",
    "name": "数学工具模块",
    "verified": true,
    "confidence": "high",
    "evidence": "探索发现main函数调用add和square，实际代码在math_utils.c",
    "related_files": ["tiny_test/math_utils.c"],  // ✓ 实际文件
    "key_functions": ["add", "square", "main"],   // ✓ 实际函数
    "call_chain": "main → add, square",
    "sub_features": [
      {
        "name": "加法运算",
        "key_functions": ["add"],
        "verified": true
      },
      {
        "name": "平方运算",
        "key_functions": ["square"],
        "verified": true
      }
    ]
  }
}
```

---

## 🎯 实施优先级

### 高优先级（立即修复）⭐⭐⭐⭐⭐

1. **修复递归探索逻辑**
   - 确保探索add和square函数
   - 确保代码正确传递

2. **增强Round 3提示词**
   - 提供实际代码
   - 提供实际文件/函数列表作为约束
   - 明确禁止猜测

3. **增加验证机制**
   - 文件存在性检查
   - 函数存在性检查
   - 打印警告信息

### 中优先级（近期优化）⭐⭐⭐

4. **改进提示词设计**
   - 强调诚实原则
   - 提供示例

5. **增加调试日志**
   - 记录每一步探索
   - 记录AI的每个决策

---

## 📌 总结

### 核心问题
Round 3的递归探索**没有真正执行**，AI只看到了main函数名，没有看到任何实际代码，被迫凭空想象，产生了大量幻觉。

### 解决方向
1. ✅ 确保递归探索正常工作（探索add、square）
2. ✅ 在提示词中提供实际代码和文件列表
3. ✅ 明确禁止AI猜测或想象
4. ✅ 增加后验证机制，过滤幻觉内容

### 预期效果
- 幻觉率从 80% 降到 0%
- 功能划分更少但更准确
- 后续审查基于真实信息

---

**分析时间**: 2025-11-02  
**问题严重性**: 🔴 高危（导致整个审查基于虚假信息）  
**修复紧急性**: ⭐⭐⭐⭐⭐（最高优先级）

