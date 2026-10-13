"""
智能功能发现器 - AI自主探索代码库并划分功能模块

核心策略：
1. 从入口函数开始，AI使用工具自主探索代码库
2. 基于代码语义和调用关系，AI自动识别功能模块
3. 智能划分功能，确保每个模块在token限制内
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from ....ai.openai.client import AIClient
from .....utils.concurrent_logger import log_concurrent_info, log_concurrent_warning, log_concurrent_debug


class SmartFeatureDiscovery:
    """智能功能发现器"""
    
    def __init__(self, project_root: str, entry_function: str = "main"):
        self.project_root = Path(project_root)
        self.entry_function = entry_function
        self.ai_client = AIClient()
        
        # Token限制（保守估计：1个字符≈0.3 tokens）
        self.MAX_TOKENS_PER_FEATURE = 15000  # 每个功能模块最多15k tokens
        self.MAX_TOTAL_CONTEXT = 60000  # 模型总上下文60k tokens
        
    def discover_features(self, software_type: str, kb: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        AI自主发现代码库中的功能模块
        
        Returns:
            List[Dict]: 功能列表，每个功能包含：
            {
                "name": "功能名称",
                "description": "功能描述",
                "entry_point": "入口函数",
                "related_files": ["文件列表"],
                "related_functions": ["函数列表"],
                "estimated_tokens": 估算token数,
                "priority": "高/中/低"
            }
        """
        log_concurrent_info(f"[功能发现] 开始AI自主功能发现，入口函数: {self.entry_function}", "smart_discovery")
        
        # 阶段1：初步探索 - 了解项目结构
        project_structure = self._get_project_structure()
        log_concurrent_info(f"[功能发现] 项目结构：{len(project_structure.get('files', []))} 个代码文件", "smart_discovery")
        
        # 阶段2：入口点分析 - 找到主要功能分支
        entry_analysis = self._analyze_entry_point()
        log_concurrent_info(f"[功能发现] 入口点分析完成", "smart_discovery")
        
        # 阶段3：AI自主功能划分
        features = self._ai_discover_features(software_type, kb, project_structure, entry_analysis)
        log_concurrent_info(f"[功能发现] AI识别出 {len(features)} 个功能模块", "smart_discovery")
        
        # 阶段4：Token估算和智能细分
        refined_features = self._refine_and_estimate_tokens(features)
        log_concurrent_info(f"[功能发现] 细化后共 {len(refined_features)} 个可审查单元", "smart_discovery")
        
        return refined_features
    
    def _get_project_structure(self) -> Dict[str, Any]:
        """获取项目结构概览"""
        from .....config import ALLOWED_CODE_EXTENSIONS
        
        files = []
        total_lines = 0
        
        for ext in ALLOWED_CODE_EXTENSIONS:
            for file in self.project_root.rglob(f"*{ext}"):
                rel_path = str(file.relative_to(self.project_root))
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = sum(1 for _ in f)
                    files.append({
                        "path": rel_path,
                        "extension": ext,
                        "lines": line_count
                    })
                    total_lines += line_count
                except:
                    continue
        
        return {
            "files": files,
            "total_files": len(files),
            "total_lines": total_lines,
            "avg_lines_per_file": total_lines // len(files) if files else 0
        }
    
    def _analyze_entry_point(self) -> Dict[str, Any]:
        """分析入口函数，找到主要调用分支"""
        log_concurrent_debug(f"[功能发现] 分析入口函数: {self.entry_function}", "smart_discovery")
        
        # 使用简单的静态分析找到入口函数
        entry_file = None
        entry_code = None
        
        # 搜索入口函数
        for c_file in self.project_root.rglob("*.c"):
            try:
                with open(c_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                    if f"int {self.entry_function}(" in code or f"void {self.entry_function}(" in code:
                        entry_file = str(c_file.relative_to(self.project_root))
                        # 提取函数体（简化版）
                        start = code.find(f"{self.entry_function}(")
                        if start > 0:
                            # 往回找函数声明的开始
                            start = code.rfind('\n', 0, start) + 1
                            # 往后找函数结束（简单计算大括号）
                            brace_count = 0
                            in_func = False
                            end = start
                            for i in range(start, len(code)):
                                if code[i] == '{':
                                    in_func = True
                                    brace_count += 1
                                elif code[i] == '}':
                                    brace_count -= 1
                                    if in_func and brace_count == 0:
                                        end = i + 1
                                        break
                            entry_code = code[start:end]
                        break
            except:
                continue
        
        if not entry_file:
            log_concurrent_warning(f"[功能发现] 未找到入口函数 {self.entry_function}", "smart_discovery")
            return {"found": False}
        
        return {
            "found": True,
            "file": entry_file,
            "code_snippet": entry_code[:2000] if entry_code else "",  # 限制长度
            "code_length": len(entry_code) if entry_code else 0
        }
    
    def _ai_discover_features(
        self,
        software_type: str,
        kb: Dict[str, Any],
        project_structure: Dict[str, Any],
        entry_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """让AI自主发现和划分功能模块"""
        
        kb_text = kb.get('kb_text', '')[:2000]
        
        # 构建AI提示词
        prompt = f"""你是一位资深的软件架构师和代码分析专家。

【任务】
根据项目信息和入口函数，**自主识别**代码库中的主要功能模块。

【项目信息】
- 软件类型：{software_type}
- 代码文件数：{project_structure['total_files']}
- 总代码行数：{project_structure['total_lines']}
- 入口函数：{self.entry_function}

【入口函数代码】
```c
{entry_analysis.get('code_snippet', '未找到入口函数')}
```

【文件列表（前30个）】
{self._format_file_list(project_structure['files'][:30])}

【领域知识】
{kb_text}

【核心要求】
1. **自主推断**：根据入口函数、文件名称、代码结构，推断有哪些功能模块
2. **语义分组**：按业务功能语义分组，不是按文件分组
3. **完整性**：所有功能模块加起来应该覆盖整个代码库
4. **粒度适中**：每个功能模块应该是一个独立的业务功能（不要太大也不要太小）

【输出格式】JSON
{{
  "features": [
    {{
      "name": "功能名称（如：系统初始化、数据处理、通信管理等）",
      "description": "功能的业务描述",
      "rationale": "为什么识别出这个功能（基于什么推断）",
      "estimated_files": ["相关文件的推测列表"],
      "estimated_functions": ["关键函数的推测列表"],
      "priority": "高/中/低"
    }}
  ]
}}

**重要**：
- 根据入口函数的调用推断主要功能流程
- 根据文件名推断功能模块（如：comm_xxx.c可能是通信模块）
- 考虑{software_type}软件的典型功能模块
- 每个功能应该是独立可审查的单元

请开始分析！"""

        log_concurrent_debug(f"[功能发现] AI输入提示词长度: {len(prompt)}", "smart_discovery")
        
        # 调用AI
        result, raw = self.ai_client.call_ai_stream(prompt)
        
        log_concurrent_debug(f"[功能发现] AI原始响应: {raw[:500]}...", "smart_discovery")
        
        features = result.get('features', [])
        
        if not isinstance(features, list):
            log_concurrent_warning(f"[功能发现] AI返回格式错误，使用默认划分", "smart_discovery")
            return self._default_feature_split(project_structure)
        
        return features
    
    def _refine_and_estimate_tokens(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """细化功能并估算token数"""
        refined = []
        
        for feature in features:
            # 粗略估算：基于预估的文件数和函数数
            estimated_files = feature.get('estimated_files', [])
            estimated_functions = feature.get('estimated_functions', [])
            
            # 估算token（非常粗略）：
            # - 每个文件约500 tokens（如果读取大纲）
            # - 每个函数约200 tokens（如果读取代码）
            estimated_tokens = len(estimated_files) * 500 + len(estimated_functions) * 200
            
            feature['estimated_tokens'] = estimated_tokens
            
            # 如果预估超过限制，标记需要进一步细分
            if estimated_tokens > self.MAX_TOKENS_PER_FEATURE:
                feature['needs_subdivision'] = True
                feature['subdivision_strategy'] = "按文件分批处理"
            else:
                feature['needs_subdivision'] = False
            
            refined.append(feature)
        
        return refined
    
    def _format_file_list(self, files: List[Dict[str, Any]]) -> str:
        """格式化文件列表"""
        lines = []
        for f in files:
            lines.append(f"- {f['path']} ({f['lines']} 行)")
        return '\n'.join(lines)
    
    def _default_feature_split(self, project_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """默认的功能划分策略（AI失败时的后备方案）"""
        log_concurrent_warning(f"[功能发现] 使用默认划分策略", "smart_discovery")
        
        # 简单按文件名模式分组
        features = [
            {
                "name": "主流程",
                "description": "包含main函数和主要控制流程",
                "estimated_files": ["main.c"],
                "estimated_functions": ["main"],
                "priority": "高"
            },
            {
                "name": "其他模块",
                "description": "其他功能模块",
                "estimated_files": [f['path'] for f in project_structure['files'][:10]],
                "estimated_functions": [],
                "priority": "中"
            }
        ]
        
        return features


def discover_features_for_task(
    task_id: int,
    project_root: str,
    software_type: str,
    entry_function: str,
    kb: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    为任务发现功能模块（供外部调用）
    
    Args:
        task_id: 任务ID
        project_root: 项目根目录
        software_type: 软件类型
        entry_function: 入口函数
        kb: 知识库
        
    Returns:
        功能列表
    """
    log_concurrent_info(f"[Task {task_id}] 开始智能功能发现", "smart_discovery")
    
    discoverer = SmartFeatureDiscovery(project_root, entry_function)
    features = discoverer.discover_features(software_type, kb)
    
    log_concurrent_info(f"[Task {task_id}] 功能发现完成，共 {len(features)} 个功能模块", "smart_discovery")
    
    # 记录每个功能的详细信息
    for i, feature in enumerate(features, 1):
        log_concurrent_info(
            f"[Task {task_id}] 功能{i}: {feature.get('name')} "
            f"(预估{feature.get('estimated_tokens', 0)} tokens, "
            f"优先级:{feature.get('priority', '未知')})",
            "smart_discovery"
        )
    
    return features

