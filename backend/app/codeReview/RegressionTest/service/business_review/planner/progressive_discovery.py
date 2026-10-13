"""
渐进式功能发现模块

实现多轮渐进式分析：
- Round 1: 基于目录结构的粗粒度划分
- Round 2: 基于函数签名的细化
- Round 3: 基于main函数的验证
- Round N: 深入细化（可选）

每一轮都可以修正之前的判断
"""
import json
import re
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from ..memory.memory_manager import MemoryManager
from ..tools.code_extractor import CodeExtractor
from ...ai.ai_client import AIClient
from ....utils.concurrent_logger import (
    log_concurrent_info as log_info,
    log_concurrent_error as log_error,
    log_concurrent_debug as log_debug,
    log_concurrent_warning as log_warning,
    set_current_thread_task
)


class ProgressiveDiscovery:
    """渐进式功能发现器"""
    
    def __init__(self, task_id: int, project_root: str, language: str = 'c', 
                 entry_function: str = 'main'):
        """
        初始化
        
        Args:
            task_id: 任务ID
            project_root: 项目根目录
            language: 编程语言
            entry_function: 入口函数名称
        """
        self.task_id = task_id
        self.project_root = Path(project_root)
        self.language = language
        self.entry_function = entry_function
        
        # 核心组件
        self.memory = MemoryManager(task_id, project_root)
        self.extractor = CodeExtractor(project_root, language)
        self.ai_client = AIClient()
        
        # 配置
        self.max_rounds = 5  # 最多5轮
        self.current_round = 0
    
    def run_discovery(self) -> Dict[str, Any]:
        """
        运行完整的功能发现流程
        
        Returns:
            发现结果
        """
        # 设置当前线程的任务上下文（确保日志写入正确的文件夹）
        set_current_thread_task(self.task_id, self.task_id, "progressive_discovery")
        
        log_info(f"[渐进式发现] 开始任务 {self.task_id}", "progressive_discovery")
        
        # 初始化记忆
        project_info = {
            "name": self.project_root.name,
            "language": self.language,
            "entry_point": "main"
        }
        self.memory.create_initial_memory(project_info)
        
        # Round 1: 目录结构分析
        log_info("[Round 1] 开始: 目录结构分析", "progressive_discovery")
        round1_result = self._round_1_directory_analysis()
        self.memory.save_round(1, round1_result)
        
        # Round 2: 函数签名分析
        log_info("[Round 2] 开始: 函数签名分析", "progressive_discovery")
        round2_result = self._round_2_function_signature_analysis()
        self.memory.save_round(2, round2_result)
        
        # Round 3: main函数验证
        log_info("[Round 3] 开始: main函数验证", "progressive_discovery")
        round3_result = self._round_3_main_function_verification()
        self.memory.save_round(3, round3_result)
        
        # 可选：Round 4+ 深入细化
        # 这里可以根据需要添加更多轮次
        
        # 标记完成
        self.memory.mark_discovery_complete()
        
        log_info("[渐进式发现] 完成！", "progressive_discovery")
        
        return {
            "status": "completed",
            "total_rounds": 3,
            "memory_path": str(self.memory.memory_dir / "latest.json"),
            "visualization_data": self.memory.get_visualization_data()
        }
    
    def _round_1_directory_analysis(self) -> Dict[str, Any]:
        """
        Round 1: 基于目录结构的粗粒度功能划分
        
        让AI看目录树，给出初步的功能模块划分
        """
        log_debug("[Round 1] 提取目录树...", "progressive_discovery")
        
        # 提取目录树
        dir_tree = self.extractor.extract_directory_tree(max_depth=3)
        
        # 获取项目概览
        overview = self.extractor.get_compact_overview()
        
        # 构建AI提示
        prompt = self._build_round1_prompt(dir_tree, overview)
        
        log_debug("[Round 1] 调用AI进行分析...", "progressive_discovery")
        
        # 调用AI
        result, _ = self.ai_client.call_ai_stream(prompt)
        
        # 解析AI的响应
        features = self._parse_ai_features(result)
        
        return {
            "method": "directory_analysis",
            "summary": "基于目录结构的粗粒度划分",
            "features": features,
            "ai_decisions": [
                {
                    "stage": "round_1",
                    "input": "目录树 + 项目概览",
                    "output": f"识别了 {len(features)} 个顶层功能模块"
                }
            ]
        }
    
    def _round_2_function_signature_analysis(self) -> Dict[str, Any]:
        """
        Round 2: 基于函数签名的细化（分批执行）
        
        按目录/模块分组，逐批分析，避免token爆炸
        """
        log_debug("[Round 2] 提取函数签名...", "progressive_discovery")
        
        # 加载上一轮的记忆
        previous_memory = self.memory.load_latest()
        
        # 提取所有函数签名
        all_functions = self.extractor.extract_function_signatures()
        log_debug(f"[Round 2] 共提取 {len(all_functions)} 个函数签名", "progressive_discovery")
        
        # 按目录分组（分批策略）
        modules = self._group_functions_by_module(all_functions)
        log_debug(f"[Round 2] 分为 {len(modules)} 个模块", "progressive_discovery")
        
        # 逐模块分析
        all_module_features = []
        for i, (module_name, module_functions) in enumerate(modules.items(), 1):
            log_debug(f"[Round 2.{i}] 分析模块: {module_name} ({len(module_functions)} 个函数)", "progressive_discovery")
            
            # 分析单个模块
            module_result = self._analyze_module_batch(
                module_name=module_name,
                functions=module_functions,
                previous_memory=previous_memory,
                batch_index=i,
                total_batches=len(modules)
            )
            
            all_module_features.extend(module_result.get("features", []))
        
        log_debug(f"[Round 2] 所有模块分析完成，共 {len(all_module_features)} 个子功能", "progressive_discovery")
        
        # 最终汇总（让AI整合所有模块的分析结果）
        log_debug("[Round 2] 汇总所有模块分析结果...", "progressive_discovery")
        final_features = self._summarize_modules(all_module_features, previous_memory)
        
        return {
            "method": "function_signature_analysis_batch",
            "summary": f"分批分析（{len(modules)}个模块）+ 最终汇总",
            "features": final_features,
            "ai_decisions": [
                {
                    "stage": "round_2",
                    "input": f"上一轮记忆 + {len(all_functions)} 个函数签名（分{len(modules)}批）",
                    "output": f"识别为 {len(final_features)} 个功能模块"
                }
            ]
        }
    
    def _group_functions_by_module(self, functions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按目录分组函数（分批策略）
        
        策略：
        1. 按第一级目录分组（如 src/, include/, utils/）
        2. 如果某个目录函数过多（>100），进一步细分为二级目录
        3. 如果仍然过多，按文件分组
        """
        from collections import defaultdict
        
        modules = defaultdict(list)
        MAX_FUNCTIONS_PER_BATCH = 100
        
        for func in functions:
            file_path = func["file"]
            
            # 提取目录路径
            if '/' in file_path:
                parts = file_path.split('/')
                # 使用第一级目录作为模块名
                module_name = parts[0]
            else:
                module_name = "root"
            
            modules[module_name].append(func)
        
        # 检查是否有模块函数过多，需要进一步细分
        final_modules = {}
        for module_name, funcs in modules.items():
            if len(funcs) <= MAX_FUNCTIONS_PER_BATCH:
                final_modules[module_name] = funcs
            else:
                # 进一步按二级目录或文件细分
                sub_modules = defaultdict(list)
                for func in funcs:
                    file_path = func["file"]
                    if '/' in file_path:
                        parts = file_path.split('/')
                        if len(parts) >= 2:
                            sub_module_name = f"{parts[0]}/{parts[1]}"
                        else:
                            sub_module_name = file_path
                    else:
                        sub_module_name = file_path
                    
                    sub_modules[sub_module_name].append(func)
                
                final_modules.update(sub_modules)
        
        return dict(final_modules)
    
    def _analyze_module_batch(
        self,
        module_name: str,
        functions: List[Dict[str, Any]],
        previous_memory: Dict[str, Any],
        batch_index: int,
        total_batches: int
    ) -> Dict[str, Any]:
        """分析单个模块的函数签名"""
        
        # 构建prompt
        prompt = f"""你是一位代码架构分析专家，正在进行项目的功能模块识别（第2轮分析）。

【当前进度】批次 {batch_index}/{total_batches}

【本批次模块】{module_name}

【第1轮分析结果（参考）】
{self._format_previous_features(previous_memory)}

【本模块的函数签名】({len(functions)} 个函数)
{self._format_function_signatures(functions)}

【任务】
基于这个模块的函数签名，识别出本模块包含的功能模块。

**注意**：
1. 只分析本批次的函数，不要试图分析整个项目
2. 如果函数属于第1轮已识别的功能，标注出来
3. 如果发现新的功能模块，也要列出来
4. 为每个功能模块标注关键函数
5. **对于复杂功能，请划分子功能（sub_features）**，例如：
   - "网络通信" → ["连接管理", "数据发送", "数据接收"]
   - "配置管理" → ["配置加载", "配置验证", "配置保存"]

【返回格式】JSON
```json
{{
  "features": [
    {{
      "id": "feature_X",
      "name": "功能模块名称",
      "description": "功能描述",
      "confidence": "high/medium/low",
      "evidence": "为什么这样划分",
      "related_files": ["file1.c", "file2.c"],
      "key_functions": ["func1", "func2"],
      "sub_features": [
        {{
          "id": "feature_X_1",
          "name": "子功能名称",
          "description": "子功能描述",
          "confidence": "high/medium/low",
          "evidence": "划分理由",
          "related_files": ["file.c"],
          "key_functions": ["func"],
          "sub_features": []
        }}
      ]
    }}
  ]
}}
```
"""
        
        try:
            result, _ = self.ai_client.call_ai_stream(prompt)
            features = self._parse_ai_features(result)
            
            return {
                "module": module_name,
                "features": features,
                "function_count": len(functions)
            }
        except Exception as e:
            log_error(f"[Round 2.{batch_index}] 分析模块 {module_name} 失败: {e}", "progressive_discovery")
            return {
                "module": module_name,
                "features": [],
                "function_count": len(functions),
                "error": str(e)
            }
    
    def _summarize_modules(
        self,
        all_module_features: List[Dict[str, Any]],
        previous_memory: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """汇总所有模块的分析结果"""
        
        if not all_module_features:
            return previous_memory.get("features", [])
        
        # 如果模块不多，直接合并
        if len(all_module_features) <= 10:
            return all_module_features
        
        # 否则让AI进行智能合并
        prompt = f"""你是一位代码架构分析专家，现在需要整合多个模块的分析结果。

【各模块识别的功能】
{json.dumps([{"id": f.get("id"), "name": f.get("name"), "description": f.get("description")} 
             for f in all_module_features], indent=2, ensure_ascii=False)}

【任务】
1. 合并相似或重复的功能模块
2. 识别跨模块的功能
3. 整理出清晰的功能模块列表

【返回格式】JSON（完整的features数组，包含所有字段）
```json
{{
  "features": [...]
}}
```
"""
        
        try:
            result, _ = self.ai_client.call_ai_stream(prompt)
            features = self._parse_ai_features(result)
            return features if features else all_module_features
        except Exception as e:
            log_error(f"[Round 2] 汇总失败，返回原始结果: {e}", "progressive_discovery")
            return all_module_features
    
    def _format_previous_features(self, memory: Dict[str, Any]) -> str:
        """格式化第1轮的功能列表"""
        features = memory.get("features", [])
        if not features:
            return "（第1轮未识别出功能）"
        
        lines = []
        for f in features:
            lines.append(f"- {f.get('name')}: {f.get('description')}")
        return "\n".join(lines)
    
    def _format_function_signatures(self, functions: List[Dict[str, Any]]) -> str:
        """格式化函数签名列表"""
        lines = []
        for func in functions[:100]:  # 限制数量
            lines.append(f"- {func.get('signature', '')} // {func.get('file', '')}:{func.get('line', 0)}")
        
        if len(functions) > 100:
            lines.append(f"... 还有 {len(functions) - 100} 个函数")
        
        return "\n".join(lines)
    
    def _round_3_main_function_verification(self) -> Dict[str, Any]:
        """
        Round 3: AI驱动的递归探索（从main函数开始）
        
        AI自主决定探索路径和深度，使用工具理解调用链
        """
        log_debug("[Round 3] 定位main函数...", "progressive_discovery")
        
        # 加载上一轮的记忆
        previous_memory = self.memory.load_latest()
        
        # 查找main函数
        main_func = self.extractor.find_main_function()
        
        if not main_func:
            log_debug("[Round 3] 未找到main函数，使用其他入口点", "progressive_discovery")
            # 尝试查找其他可能的入口点
            entry_points = self._find_entry_points()
            if not entry_points:
                return {
                    "method": "main_function_verification",
                    "summary": "未找到入口函数",
                    "features": previous_memory.get("features", []),
                    "ai_decisions": []
                }
            main_func = entry_points[0]
        
        # 开始递归探索
        log_debug(f"[Round 3] 从 {main_func['name']} 开始递归探索", "progressive_discovery")
        
        exploration_result = self._recursive_exploration(
            entry_function=main_func,
            previous_memory=previous_memory,
            max_depth=5,
            max_functions_per_depth=5
        )
        
        return exploration_result
    
    def _find_entry_points(self) -> List[Dict[str, Any]]:
        """查找可能的入口点（如果没有main函数）"""
        all_functions = self.extractor.extract_function_signatures()
        
        # 简单启发式：查找常见的入口函数名
        entry_names = ['main', 'start', 'init', 'run', 'entry']
        
        for func in all_functions:
            if func.get('name', '').lower() in entry_names:
                return [func]
        
        # 如果找不到，返回第一个函数
        return [all_functions[0]] if all_functions else []
    
    def _recursive_exploration(
        self,
        entry_function: Dict[str, Any],
        previous_memory: Dict[str, Any],
        max_depth: int = 5,
        max_functions_per_depth: int = 5
    ) -> Dict[str, Any]:
        """
        AI驱动的递归探索
        
        Args:
            entry_function: 入口函数
            previous_memory: 上一轮的记忆
            max_depth: 最大探索深度
            max_functions_per_depth: 每层最多探索的函数数量
        """
        explored_functions = set()  # 已探索的函数
        exploration_history = []     # 探索历史
        actual_files: Set[str] = set()
        actual_functions: Set[str] = set()
        
        # 初始化：从入口函数开始
        current_targets = [entry_function['name']]
        current_depth = 0
        
        log_debug(f"[Round 3] 开始递归探索，最大深度: {max_depth}", "progressive_discovery")
        
        while current_targets and current_depth < max_depth:
            log_debug(f"[Round 3] 探索第 {current_depth + 1} 层，目标函数: {current_targets}", "progressive_discovery")
            
            next_targets = []
            
            for func_name in current_targets:
                if func_name in explored_functions:
                    continue
                
                # 读取函数代码
                func_meta = self._get_function_code(func_name)
                if not func_meta:
                    log_debug(f"[Round 3] 无法获取函数 {func_name} 的代码", "progressive_discovery")
                    continue
                
                actual_functions.add(func_name)
                actual_files.add(func_meta['file'])
                
                # 让AI分析这个函数
                analysis = self._analyze_function_for_exploration(
                    func_name=func_name,
                    func_code=func_meta['code'],
                    func_file=func_meta['file'],
                    start_line=func_meta['start_line'],
                    exploration_history=exploration_history,
                    previous_memory=previous_memory,
                    current_depth=current_depth,
                    max_depth=max_depth
                )
                
                # 记录探索历史
                explored_functions.add(func_name)
                analysis['file'] = func_meta['file']
                analysis['start_line'] = func_meta['start_line']
                analysis['code'] = func_meta['code']
                exploration_history.append(analysis)
                
                # 获取AI建议的下一步目标
                suggested_targets = analysis.get("next_targets", [])
                if isinstance(suggested_targets, list):
                    next_targets.extend([
                        target for target in suggested_targets if isinstance(target, str)
                    ][:max_functions_per_depth])
                else:
                    log_warning(
                        f"[Round 3] 函数 {func_name} 返回的 next_targets 类型异常: {suggested_targets}",
                        "progressive_discovery"
                    )
                
                log_debug(f"[Round 3] 函数 {func_name} 分析完成，建议探索: {suggested_targets}", "progressive_discovery")
            
            # 进入下一层
            current_targets = list(set(next_targets))[:max_functions_per_depth]  # 去重并限制数量
            current_depth += 1
        
        log_debug(f"[Round 3] 递归探索完成，共探索 {len(explored_functions)} 个函数", "progressive_discovery")
        
        # 基于探索历史，让AI整合并调整功能划分
        final_features = self._integrate_exploration_results(
            exploration_history=exploration_history,
            previous_memory=previous_memory,
            actual_files=actual_files,
            actual_functions=actual_functions
        )
        
        return {
            "method": "recursive_exploration",
            "summary": f"AI驱动递归探索（深度{current_depth}，探索{len(explored_functions)}个函数）",
            "features": final_features,
            "ai_decisions": [
                {
                    "stage": "round_3",
                    "method": "recursive_exploration",
                    "explored_functions": list(explored_functions),
                    "max_depth_reached": current_depth,
                    "actual_files": list(actual_files),
                    "actual_functions": list(actual_functions)
                }
            ]
        }
    
    def _get_function_code(self, func_name: str) -> Optional[Dict[str, Any]]:
        """获取函数的完整代码及元数据"""
        all_functions = self.extractor.extract_function_signatures()
        
        # 查找函数
        target_func = None
        for func in all_functions:
            if func['name'] == func_name:
                target_func = func
                break
        
        if not target_func:
            return None
        
        # 读取文件
        file_path = self.project_root / target_func['file']
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 提取函数代码（简单方式：从函数定义行开始读取50行）
            start_line = target_func['line'] - 1
            end_line = min(start_line + 50, len(lines))
            
            func_code = ''.join(lines[start_line:end_line])
            return {
                "code": func_code,
                "file": target_func['file'],
                "start_line": target_func['line'],
                "end_line": end_line,
            }
        except Exception as e:
            log_error(f"读取函数 {func_name} 代码失败: {e}", "progressive_discovery")
            return None
    
    def _analyze_function_for_exploration(
        self,
        func_name: str,
        func_code: str,
        func_file: str,
        start_line: int,
        exploration_history: List[Dict[str, Any]],
        previous_memory: Dict[str, Any],
        current_depth: int,
        max_depth: int
    ) -> Dict[str, Any]:
        """让AI分析函数并决定下一步探索目标"""
        
        # 构建prompt
        prompt = f"""你正在探索代码项目的功能结构（第3轮分析：递归探索）。

【当前进度】
- 探索深度: {current_depth + 1}/{max_depth}
- 已探索函数: {len(exploration_history)}

【当前分析的函数】
{func_name}

【函数代码】
```c
{func_code[:1000]}  // 截取前1000字符
```

【位置】
- 文件: {func_file}
- 起始行: {start_line}

【第2轮分析结果（参考）】
{self._format_previous_features(previous_memory)}

【任务】
1. 理解这个函数的职责和所属模块
2. 识别函数调用了哪些关键函数（3-5个）
3. 决定是否需要继续深入探索（如果已经理解足够，返回空列表）

【返回格式】JSON
```json
{{
  "function_name": "{func_name}",
  "module": "所属模块名",
  "description": "函数职责描述",
  "key_calls": ["被调用的关键函数1", "被调用的关键函数2"],
  "next_targets": ["需要进一步探索的函数1", "需要进一步探索的函数2"],
  "confidence": "high/medium/low",
  "reasoning": "为什么需要探索这些函数"
}}
```

**注意**：
- 只列出最关键的函数（3-5个）
- 如果函数很简单或已经足够理解，next_targets返回空数组
- 优先探索业务逻辑函数，跳过简单的工具函数
"""
        
        try:
            result, _ = self.ai_client.call_ai_stream(prompt)
            
            # 确保result是字符串
            if not isinstance(result, str):
                log_error(f"[Round 3] AI返回类型错误: {type(result)}, 内容: {result}", "progressive_discovery")
                return {
                    "function_name": func_name,
                    "module": "unknown",
                    "next_targets": [],
                    "error": "AI返回类型不是字符串"
                }
            
            log_debug(f"[Round 3] AI返回内容长度: {len(result)}, 前100字符: {result[:100]}", "progressive_discovery")
            
            # 解析JSON
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                # 尝试直接解析
                start = result.find('{')
                end = result.rfind('}') + 1
                if start != -1 and end > start:
                    analysis = json.loads(result[start:end])
                else:
                    log_error(f"[Round 3] 无法从AI响应中提取JSON: {result}", "progressive_discovery")
                    analysis = {
                        "function_name": func_name,
                        "module": "unknown",
                        "next_targets": []
                    }
            
            return analysis
        
        except Exception as e:
            log_error(f"[Round 3] 分析函数 {func_name} 失败: {e}", "progressive_discovery")
            import traceback
            log_error(f"[Round 3] 详细错误: {traceback.format_exc()}", "progressive_discovery")
            return {
                "function_name": func_name,
                "module": "unknown",
                "next_targets": [],
                "error": str(e)
            }
    
    def _integrate_exploration_results(
        self,
        exploration_history: List[Dict[str, Any]],
        previous_memory: Dict[str, Any],
        actual_files: Set[str],
        actual_functions: Set[str]
    ) -> List[Dict[str, Any]]:
        """基于探索历史，整合并调整功能划分"""
        
        if not exploration_history:
            return previous_memory.get("features", [])
        
        exploration_context = self._format_exploration_history(exploration_history)
        files_list = sorted(actual_files)
        functions_list = sorted(actual_functions)
        files_str = "\n".join(f"- {path}" for path in files_list) or "(无)"
        functions_str = "\n".join(f"- {name}" for name in functions_list) or "(无)"
        
        # 构建prompt
        prompt = f"""你正在整合递归探索的结果（第3轮分析：验证和调整）。

【第2轮识别的功能模块】
{self._format_previous_features(previous_memory)}

【递归探索发现（包含真实代码）】
{exploration_context}

【已确认的实际文件】
{files_str}

【已确认的实际函数】
{functions_str}

【重要约束】
1. ✅ 仅使用上述“已确认”的文件和函数，禁止编造新名称
2. ✅ 如果某功能缺少实际证据，请标记 `verified: false`，并将 `confidence` 降为 `low`
3. ✅ `related_files` 与 `key_functions` 必须来源于实际探索结果
4. ✅ 如需继续探索其他函数，请明确指出原因
5. ❌ 不要猜测、补全或创造不存在的文件/函数

【任务】
基于实际的函数调用关系，验证和调整功能划分：
1. 确认哪些功能模块是准确的
2. 调整或剔除缺乏证据的功能
3. 合并重复或高度相关的模块
4. 标注每个功能的置信度和优先级
5. **对于复杂功能，细化为子功能（sub_features）**，但同样必须引用真实代码

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
      "evidence": "引用实际代码的证据（请提及函数名/文件/行号）",
      "related_files": ["相对路径"],
      "key_functions": ["函数名"],
      "call_chain": "main → ...",
      "verified": true,
      "sub_features": [
        {{
          "id": "feature_X_1",
          "name": "子功能名称",
          "description": "子功能描述",
          "confidence": "high/medium/low",
          "evidence": "引用实际证据",
          "related_files": ["相对路径"],
          "key_functions": ["函数名"],
          "sub_features": []
        }}
      ]
    }}
  ]
}}
```
"""
        
        try:
            result, _ = self.ai_client.call_ai_stream(prompt)
            features = self._parse_ai_features(result)
            if not features:
                return previous_memory.get("features", [])
            
            return self._validate_features(features, actual_files, actual_functions)
        
        except Exception as e:
            log_error(f"[Round 3] 整合探索结果失败: {e}", "progressive_discovery")
            return previous_memory.get("features", [])
    
    def _format_exploration_history(self, history: List[Dict[str, Any]]) -> str:
        """格式化探索历史，包含代码和来源信息"""
        lines = []
        for i, item in enumerate(history, 1):
            func_name = item.get("function_name", "unknown")
            module = item.get("module", "unknown")
            key_calls = item.get("key_calls", [])
            file_path = item.get("file", "unknown")
            start_line = item.get("start_line", 0)
            code_snippet = (item.get("code") or "").strip()
            if len(code_snippet) > 400:
                code_snippet = code_snippet[:400] + "\n// ..."
            
            lines.append(f"{i}. 函数: {func_name} | 模块: {module} | 文件: {file_path} | 起始行: {start_line}")
            if key_calls:
                lines.append(f"   调用: {', '.join(key_calls[:5])}")
            if code_snippet:
                lines.append("   代码片段:\n" + "\n".join("     " + line for line in code_snippet.splitlines()))
        
        return "\n".join(lines[:20])  # 限制长度

    def _validate_features(
        self,
        features: List[Dict[str, Any]],
        actual_files: Set[str],
        actual_functions: Set[str]
    ) -> List[Dict[str, Any]]:
        """验证AI输出，过滤幻觉内容"""
        validated = []
        warnings: List[str] = []

        def _file_exists(path: str) -> bool:
            return any(path == f or f.endswith(path) for f in actual_files)

        for feature in features:
            new_feature = feature.copy()

            # 验证 related_files
            related_files = feature.get("related_files", []) or []
            valid_files = [f for f in related_files if _file_exists(f)]
            missing_files = [f for f in related_files if f not in valid_files]
            if missing_files:
                warnings.append(
                    f"功能 {feature.get('name', 'unknown')} 引用了不存在的文件: {', '.join(missing_files)}"
                )
            new_feature["related_files"] = valid_files

            # 验证 key_functions
            key_functions = feature.get("key_functions", []) or []
            valid_functions = []
            missing_functions = []
            for func in key_functions:
                func_name = func.split('(')[0].strip()
                if func_name in actual_functions:
                    valid_functions.append(func_name if '(' not in func else func)
                else:
                    missing_functions.append(func)
            if missing_functions:
                warnings.append(
                    f"功能 {feature.get('name', 'unknown')} 引用了不存在的函数: {', '.join(missing_functions)}"
                )
            new_feature["key_functions"] = valid_functions

            # 标记置信度
            if not valid_files or not valid_functions:
                new_feature["confidence"] = "low"
                new_feature["verified"] = False
                evidence = new_feature.get("evidence", "")
                if evidence:
                    evidence += " "
                evidence += "缺少实际文件或函数支持"
                new_feature["evidence"] = evidence

            # 递归验证子功能
            if "sub_features" in new_feature and isinstance(new_feature["sub_features"], list):
                new_feature["sub_features"] = self._validate_features(
                    new_feature["sub_features"], actual_files, actual_functions
                )

            validated.append(new_feature)

        if warnings:
            log_warning(
                f"[Round 3] 发现 {len(warnings)} 个潜在幻觉条目，已降级或移除其中的引用", "progressive_discovery"
            )
            for msg in warnings:
                log_warning(f"[Round 3] {msg}", "progressive_discovery")

        return validated
    
    def _build_round1_prompt(self, dir_tree: Dict[str, Any], overview: str) -> str:
        """构建Round 1的AI提示"""
        prompt = f"""# 任务：代码库功能模块初步划分（Round 1 - 目录结构分析）

## 背景
你是一个专业的代码分析专家。现在需要对一个{self.language}项目进行功能模块划分。
这是第一轮分析，你只需要根据目录结构和项目概览给出**粗粒度**的功能模块划分。

**重要提示**：
1. 这只是第一轮，不需要100%准确
2. 后续会有更多轮次来细化和修正
3. 重点关注目录结构暗示的功能划分

## 项目概览
{overview}

## 目录树详情
```
{json.dumps(dir_tree, indent=2, ensure_ascii=False)}
```

## 你的任务
基于以上信息，给出**顶层功能模块**的划分。

**功能层级划分指引**：
- 对于复杂功能，可以划分子功能（sub_features）来细化
- 子功能结构与父功能相同，可以嵌套多层
- 例如："数据处理" → ["数据采集", "数据过滤", "数据存储"]

## 输出格式（严格JSON）
```json
{{
  "features": [
    {{
      "id": "feature_1",
      "name": "功能模块名称",
      "description": "该模块的功能描述",
      "confidence": "high|medium|low",
      "evidence": "为什么这样划分的理由（基于目录结构）",
      "related_directories": ["相关的目录路径"],
      "sub_features": [
        {{
          "id": "feature_1_1",
          "name": "子功能名称",
          "description": "子功能描述",
          "confidence": "high|medium|low",
          "evidence": "划分理由",
          "related_directories": ["目录"],
          "sub_features": []
        }}
      ]
    }}
  ],
  "reasoning": "你的整体分析思路"
}}
```

请开始分析：
"""
        return prompt
    
    def _build_round2_prompt(self, previous_memory: Dict[str, Any], functions_by_file: Dict[str, List[Dict]]) -> str:
        """构建Round 2的AI提示"""
        
        # 简化函数信息（只保留签名）
        simplified_functions = {}
        for file_path, funcs in functions_by_file.items():
            simplified_functions[file_path] = [
                {
                    "name": f["name"],
                    "signature": f["signature"],
                    "line": f["line"]
                }
                for f in funcs
            ]
        
        prompt = f"""# 任务：代码库功能模块细化（Round 2 - 函数签名分析）

## 背景
这是第二轮分析。你需要基于：
1. **上一轮的功能划分**（可能有错误，需要修正）
2. **所有函数签名**

来细化功能模块的划分。

**重要提示**：
1. 上一轮的划分**不一定准确**，如果发现错误，请大胆修正
2. 可以添加子功能（sub_features）来细化模块
3. 可以合并或拆分之前的模块
4. 重点关注函数命名暗示的功能聚合

## 上一轮的功能划分
```json
{json.dumps(previous_memory.get("features", []), indent=2, ensure_ascii=False)}
```

## 所有函数签名（按文件分组）
```json
{json.dumps(simplified_functions, indent=2, ensure_ascii=False)}
```

## 你的任务
1. 审视上一轮的划分，指出不合理的地方
2. 基于函数签名，细化功能模块
3. 为每个顶层模块添加子功能（如果合适）

## 输出格式（严格JSON）
```json
{{
  "corrections": [
    {{
      "previous_feature_id": "feature_1",
      "issue": "what was wrong",
      "action": "merge|split|rename|keep",
      "reason": "why"
    }}
  ],
  "features": [
    {{
      "id": "feature_1",
      "name": "功能模块名称",
      "description": "该模块的功能描述",
      "confidence": "high|medium|low",
      "evidence": "为什么这样划分的理由（基于函数签名）",
      "related_files": ["相关的文件路径"],
      "key_functions": ["关键函数名"],
      "sub_features": [
        {{
          "id": "feature_1_1",
          "name": "子功能名称",
          "description": "子功能描述",
          "confidence": "high|medium|low",
          "related_functions": ["相关函数名"]
        }}
      ]
    }}
  ],
  "reasoning": "你的整体分析思路和修正说明"
}}
```

请开始分析：
"""
        return prompt
    
    def _build_round3_prompt(self, previous_memory: Dict[str, Any], main_func: Dict[str, Any], main_content: str) -> str:
        """构建Round 3的AI提示"""
        
        prompt = f"""# 任务：代码库功能模块验证（Round 3 - main函数分析）

## 背景
这是第三轮分析。你需要基于：
1. **上一轮的功能划分**（可能有错误，需要修正）
2. **main函数的实现代码**（程序入口）

来验证和调整功能模块的划分。

**重要提示**：
1. main函数反映了程序的整体流程和功能调用关系
2. 上一轮的划分**不一定准确**，如果与main函数的逻辑不符，请修正
3. 重点关注功能的调用顺序和依赖关系

## 上一轮的功能划分
```json
{json.dumps(previous_memory.get("features", []), indent=2, ensure_ascii=False)}
```

## main函数信息
- 位置：{main_func['file']}:{main_func['line']}
- 签名：{main_func['signature']}

## main函数所在文件内容
```{self.language}
{main_content}
```

## 你的任务
1. 分析main函数的执行流程
2. 验证上一轮的功能划分是否合理
3. 调整功能模块的优先级、依赖关系

## 输出格式（严格JSON）
```json
{{
  "main_flow_analysis": "main函数的执行流程总结",
  "corrections": [
    {{
      "previous_feature_id": "feature_1",
      "issue": "what was wrong",
      "action": "adjust_priority|add_dependency|keep",
      "reason": "why (based on main flow)"
    }}
  ],
  "features": [
    {{
      "id": "feature_1",
      "name": "功能模块名称",
      "description": "该模块的功能描述",
      "confidence": "high|medium|low",
      "priority": 1,
      "depends_on": ["feature_2"],
      "evidence": "为什么这样划分的理由（基于main函数）",
      "related_files": ["相关的文件路径"],
      "key_functions": ["关键函数名"],
      "sub_features": [...]
    }}
  ],
  "reasoning": "你的整体分析思路和验证结论"
}}
```

请开始分析：
"""
        return prompt
    
    def _parse_ai_features(self, ai_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析AI返回的功能列表
        
        Args:
            ai_response: AI的JSON响应
            
        Returns:
            功能列表
        """
        try:
            # 如果AI返回的是字符串，尝试解析
            if isinstance(ai_response, str):
                ai_response = json.loads(ai_response)
            
            features = ai_response.get("features", [])
            
            # 确保每个feature都有必要的字段
            for feature in features:
                if "id" not in feature:
                    feature["id"] = f"feature_{hash(feature.get('name', ''))}"
                if "confidence" not in feature:
                    feature["confidence"] = "medium"
                if "sub_features" not in feature:
                    feature["sub_features"] = []
                if "review_status" not in feature:
                    feature["review_status"] = "pending"
                if "issues_found" not in feature:
                    feature["issues_found"] = []
            
            return features
        
        except Exception as e:
            log_error(f"解析AI响应失败: {e}", "progressive_discovery")
            return []
    
    def _count_all_features(self, features: List[Dict[str, Any]]) -> int:
        """递归计数所有功能（含子功能）"""
        count = len(features)
        for feature in features:
            count += self._count_all_features(feature.get("sub_features", []))
        return count
    
    def get_feature_for_review(self, feature_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取待审查的功能
        
        Args:
            feature_id: 指定功能ID，None表示自动选择下一个
            
        Returns:
            功能信息
        """
        memory = self.memory.load_latest()
        if not memory:
            return None
        
        if feature_id:
            return self.memory.get_feature_by_id(feature_id)
        
        # 自动选择：找第一个未审查的
        features = memory.get("features", [])
        return self._find_next_pending_feature(features)
    
    def _find_next_pending_feature(self, features: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """递归查找下一个待审查的功能"""
        for feature in features:
            if feature.get("review_status") == "pending":
                return feature
            
            # 递归查找子功能
            sub_feature = self._find_next_pending_feature(feature.get("sub_features", []))
            if sub_feature:
                return sub_feature
        
        return None

