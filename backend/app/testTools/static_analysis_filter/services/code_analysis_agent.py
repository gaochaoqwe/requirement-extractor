"""
代码分析AI Agent - 用于深度分析不确定规则的问题
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from .ai_client import StaticAnalysisAIClient
from ..utils.logger import get_session_logger

class CodeAnalysisAgent:
    def __init__(self, session_id: str, codebase_path: str = None):
        self.session_id = session_id
        self.codebase_path = Path(codebase_path) if codebase_path else None
        self.logger = get_session_logger(session_id)
        self.ai_client = StaticAnalysisAIClient(session_id)
        
        # Agent工具集
        self.tools = {
            "list_directory": self._list_directory,
            "read_file": self._read_file,
            "search_in_files": self._search_in_files,
            "analyze_function": self._analyze_function,
            "find_function_calls": self._find_function_calls,
            "get_file_structure": self._get_file_structure,
            "analyze_data_flow": self._analyze_data_flow
        }
        
    def analyze_uncertain_issue(self, issue_data: Dict[str, Any], rule_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析不确定规则的问题
        
        Args:
            issue_data: 问题数据 {issue_name, issue_file, issue_line, issue_description}
            rule_info: 规则信息
            
        Returns:
            分析结果 {is_real_issue, confidence, analysis_result, evidence}
        """
        try:
            self.logger.info("=" * 100)
            self.logger.info(f">>> 开始AI Agent分析问题 <<<")
            self.logger.info(f"问题名称: {issue_data.get('issue_name')}")
            self.logger.info(f"问题文件: {issue_data.get('issue_file')}")
            self.logger.info(f"问题行号: {issue_data.get('issue_line')}")
            self.logger.info(f"规则编号: {rule_info.get('rule_code', 'N/A')}")
            self.logger.info("=" * 100)
            
            if not self.codebase_path or not self.codebase_path.exists():
                self.logger.warning("无法访问代码库，跳过AI分析")
                return {
                    "is_real_issue": False,
                    "confidence": 0.0,
                    "analysis_result": "无法访问代码库，无法进行深度分析",
                    "evidence": []
                }
            
            # 构建分析上下文
            self.logger.info("步骤1: 构建分析上下文（读取代码文件）")
            context = self._build_analysis_context(issue_data, rule_info)
            self.logger.info(f"上下文构建完成 - 文件内容长度: {len(context.get('file_content', '')) if context.get('file_content') else 0} 字符")
            
            # 执行AI分析
            self.logger.info("步骤2: 调用AI进行深度分析（这将花费几秒钟）")
            analysis_result = self._perform_ai_analysis(context, issue_data, rule_info)
            
            self.logger.info("=" * 100)
            self.logger.info(f">>> AI Agent分析完成 <<<")
            self.logger.info(f"是否为真实问题: {analysis_result.get('is_real_issue')}")
            self.logger.info(f"置信度: {analysis_result.get('confidence')}")
            self.logger.info(f"分析结果: {analysis_result.get('analysis_result', 'N/A')}")
            self.logger.info("=" * 100)
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"AI Agent分析失败: {str(e)}"
            self.logger.error(error_msg)
            return {
                "is_real_issue": False,
                "confidence": 0.0,
                "analysis_result": error_msg,
                "evidence": []
            }
    
    def _build_analysis_context(self, issue_data: Dict[str, Any], rule_info: Dict[str, Any]) -> Dict[str, Any]:
        """构建分析上下文"""
        context = {
            "issue": issue_data,
            "rule": rule_info,
            "codebase_info": {},
            "file_content": None,
            "function_context": None,
            "related_files": []
        }
        
        try:
            # 获取问题文件信息
            issue_file = issue_data.get('issue_file', '')
            issue_line = issue_data.get('issue_line', '')
            
            if issue_file:
                # 查找文件
                file_path = self._find_file_in_codebase(issue_file)
                if file_path:
                    context["file_content"] = self._read_file(str(file_path))
                    context["function_context"] = self._get_function_context(file_path, issue_line)
                    context["related_files"] = self._find_related_files(file_path)
            
            # 获取代码库结构信息
            context["codebase_info"] = self._get_codebase_summary()
            
        except Exception as e:
            self.logger.warning(f"构建分析上下文时出错: {str(e)}")
        
        return context
    
    def _perform_ai_analysis(self, context: Dict[str, Any], issue_data: Dict[str, Any], rule_info: Dict[str, Any]) -> Dict[str, Any]:
        """执行AI分析 - 同步方法，内部调用异步AI"""
        try:
            # 获取代码上下文
            self.logger.info("  -> 提取代码上下文...")
            code_context = self._extract_code_context(context, issue_data)
            self.logger.info(f"  -> 代码上下文提取完成，长度: {len(code_context)} 字符")
            
            # 使用新的AI客户端接口进行分析
            import asyncio
            import nest_asyncio
            
            # 允许嵌套事件循环
            try:
                nest_asyncio.apply()
            except:
                pass
            
            self.logger.info("  -> 准备调用AI API...")
            
            # 检查是否在异步上下文中
            try:
                loop = asyncio.get_running_loop()
                self.logger.info("  -> 检测到运行中的事件循环，使用线程池执行")
                # 在异步上下文中，使用run_in_executor在新线程中运行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.ai_client.analyze_code_issue(issue_data, rule_info, code_context)
                    )
                    self.logger.info("  -> 等待AI响应（最长120秒）...")
                    result = future.result(timeout=120)
                    self.logger.info("  -> AI响应接收完成")
                    return result
            except RuntimeError as re:
                if "no running event loop" in str(re):
                    self.logger.info("  -> 未检测到事件循环，直接创建新循环")
                    # 不在异步上下文中，直接创建新的事件循环
                    result = asyncio.run(
                        self.ai_client.analyze_code_issue(issue_data, rule_info, code_context)
                    )
                    self.logger.info("  -> AI响应接收完成")
                    return result
                else:
                    raise
            
        except Exception as e:
            self.logger.error(f"AI分析执行失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "is_real_issue": True,  # 保守策略：失败时认为是真实问题
                "confidence": 0.5,
                "analysis_result": f"AI分析失败: {str(e)}",
                "reasoning": "AI分析失败，采用保守策略",
                "evidence": [],
                "recommendations": "建议人工审查"
            }
    
    def _extract_code_context(self, context: Dict[str, Any], issue_data: Dict[str, Any]) -> str:
        """从上下文中提取代码片段"""
        try:
            file_content = context.get("file_content", "")
            if not file_content:
                return "无法获取代码内容"
            
            issue_line = issue_data.get('issue_line', '')
            if not issue_line or not str(issue_line).isdigit():
                return file_content[:2000]  # 返回前2000字符
            
            # 提取问题行周围的代码（前后各20行）
            lines = file_content.split('\n')
            line_num = int(issue_line)
            start_line = max(0, line_num - 20)
            end_line = min(len(lines), line_num + 20)
            
            context_lines = []
            for i in range(start_line, end_line):
                prefix = ">>> " if i == line_num - 1 else "    "
                context_lines.append(f"{prefix}{i+1:4d} | {lines[i]}")
            
            return '\n'.join(context_lines)
            
        except Exception as e:
            self.logger.warning(f"提取代码上下文失败: {str(e)}")
            return "代码上下文提取失败"
    
    def _build_analysis_prompt(self, context: Dict[str, Any], issue_data: Dict[str, Any], rule_info: Dict[str, Any]) -> str:
        """构建AI分析提示词"""
        issue_name = issue_data.get('issue_name', '')
        issue_file = issue_data.get('issue_file', '')
        issue_line = issue_data.get('issue_line', '')
        issue_description = issue_data.get('issue_description', '')
        
        rule_name = rule_info.get('rule_name', '')
        rule_description = rule_info.get('rule_description', '')
        analysis_complexity = rule_info.get('analysis_complexity', '')
        
        prompt = f"""你是一个专业的代码静态分析专家。请分析以下静态分析工具报告的问题是否为真实问题。

## 问题信息
- **问题名称**: {issue_name}
- **问题文件**: {issue_file}
- **问题行数**: {issue_line}
- **问题描述**: {issue_description}

## 规则信息
- **规则名称**: {rule_name}
- **规则描述**: {rule_description}
- **分析复杂度**: {analysis_complexity}

## 代码上下文"""

        # 添加文件内容
        if context.get("file_content"):
            file_lines = context["file_content"].split('\n')
            if issue_line and issue_line.isdigit():
                line_num = int(issue_line)
                start_line = max(1, line_num - 10)
                end_line = min(len(file_lines), line_num + 10)
                
                prompt += f"""
### 问题文件内容 ({issue_file}, 第{start_line}-{end_line}行)
```c
"""
                for i in range(start_line - 1, end_line):
                    line_marker = " -> " if (i + 1) == line_num else "    "
                    prompt += f"{line_marker}{i + 1:4d}: {file_lines[i]}\n"
                prompt += "```"
            else:
                # 如果没有行号，显示文件开头部分
                prompt += f"""
### 问题文件内容 ({issue_file}, 前50行)
```c
"""
                for i, line in enumerate(file_lines[:50], 1):
                    prompt += f"{i:4d}: {line}\n"
                prompt += "```"
        
        # 添加函数上下文
        if context.get("function_context"):
            prompt += f"""
### 函数上下文
```c
{context["function_context"]}
```"""
        
        # 添加相关文件信息
        if context.get("related_files"):
            prompt += f"""
### 相关文件
"""
            for related_file in context["related_files"][:3]:  # 最多显示3个相关文件
                prompt += f"- {related_file}\n"
        
        # 添加代码库信息
        if context.get("codebase_info"):
            codebase_info = context["codebase_info"]
            prompt += f"""
### 代码库信息
- 总文件数: {codebase_info.get('total_files', 'N/A')}
- C/C++文件数: {codebase_info.get('c_cpp_files', 'N/A')}
- 头文件数: {codebase_info.get('header_files', 'N/A')}
"""

        prompt += f"""

## 分析任务
请基于以上信息，深入分析这个静态分析问题是否为真实问题。考虑以下方面：

1. **代码上下文分析**: 分析问题所在的代码上下文，理解代码的实际逻辑
2. **数据流分析**: 如果涉及变量或指针，分析其数据流和生命周期
3. **控制流分析**: 分析代码的执行路径和条件分支
4. **规则适用性**: 判断该规则在当前上下文中是否真正适用
5. **误报可能性**: 评估静态分析工具可能的误报原因

## 输出要求
请以JSON格式返回分析结果：

```json
{{
    "is_real_issue": true/false,
    "confidence": 0.0-1.0,
    "analysis_result": "详细的分析说明",
    "evidence": [
        "支持结论的证据1",
        "支持结论的证据2"
    ],
    "reasoning": "分析推理过程",
    "recommendations": "如果是真实问题，给出修复建议；如果是误报，说明原因"
}}
```

注意：
- is_real_issue: true表示确实是问题，false表示可能是误报
- confidence: 置信度，0.0-1.0之间，越高表示越确定
- 分析要客观、准确，基于代码事实
- 如果信息不足以做出判断，请在confidence中体现不确定性
"""

        return prompt
    
    def _parse_analysis_result(self, ai_result: Dict[str, Any], raw_response: str) -> Dict[str, Any]:
        """解析AI分析结果"""
        try:
            # 如果AI返回的是字符串，尝试解析JSON
            if isinstance(ai_result, str):
                # 清理并解析JSON
                cleaned_result = self._clean_json_string(ai_result)
                ai_result = json.loads(cleaned_result)
            
            # 验证必需字段
            required_fields = ["is_real_issue", "confidence", "analysis_result"]
            for field in required_fields:
                if field not in ai_result:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 确保confidence在合理范围内
            confidence = float(ai_result.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))
            
            return {
                "is_real_issue": bool(ai_result.get("is_real_issue", False)),
                "confidence": confidence,
                "analysis_result": str(ai_result.get("analysis_result", "")),
                "evidence": ai_result.get("evidence", []),
                "reasoning": ai_result.get("reasoning", ""),
                "recommendations": ai_result.get("recommendations", ""),
                "raw_response": raw_response
            }
            
        except Exception as e:
            self.logger.error(f"解析AI分析结果失败: {str(e)}")
            return {
                "is_real_issue": False,
                "confidence": 0.0,
                "analysis_result": f"AI结果解析失败: {str(e)}",
                "evidence": [],
                "reasoning": "",
                "recommendations": "",
                "raw_response": raw_response
            }
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串"""
        # 移除markdown代码块标记
        json_str = json_str.replace('```json', '').replace('```', '')
        
        # 移除多余的空白字符
        json_str = json_str.strip()
        
        # 查找JSON对象的开始和结束
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = json_str[start_idx:end_idx + 1]
        
        return json_str
    
    # Agent工具方法
    def _list_directory(self, directory_path: str) -> List[str]:
        """列出目录内容"""
        try:
            if not self.codebase_path:
                return []
            
            target_path = self.codebase_path / directory_path
            if not target_path.exists() or not target_path.is_dir():
                return []
            
            return [item.name for item in target_path.iterdir()]
        except Exception as e:
            self.logger.warning(f"列出目录失败: {str(e)}")
            return []
    
    def _read_file(self, file_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            if not self.codebase_path:
                return None
            
            # 支持相对路径和绝对路径
            if Path(file_path).is_absolute():
                target_path = Path(file_path)
            else:
                target_path = self.codebase_path / file_path
            
            if not target_path.exists() or not target_path.is_file():
                return None
            
            # 只读取文本文件，限制大小
            if target_path.stat().st_size > 1024 * 1024:  # 1MB限制
                return None
            
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"读取文件失败: {str(e)}")
            return None
    
    def _search_in_files(self, pattern: str, file_extensions: List[str] = None) -> List[Dict[str, Any]]:
        """在文件中搜索模式"""
        try:
            if not self.codebase_path:
                return []
            
            import re
            results = []
            extensions = file_extensions or ['.c', '.cpp', '.h', '.hpp']
            
            for file_path in self.codebase_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    try:
                        content = self._read_file(str(file_path))
                        if content and re.search(pattern, content, re.IGNORECASE):
                            results.append({
                                "file": str(file_path.relative_to(self.codebase_path)),
                                "matches": len(re.findall(pattern, content, re.IGNORECASE))
                            })
                    except Exception:
                        continue
            
            return results[:10]  # 限制结果数量
        except Exception as e:
            self.logger.warning(f"搜索文件失败: {str(e)}")
            return []
    
    def _find_file_in_codebase(self, filename: str) -> Optional[Path]:
        """在代码库中查找文件"""
        try:
            if not self.codebase_path:
                return None
            
            # 直接路径匹配
            direct_path = self.codebase_path / filename
            if direct_path.exists():
                return direct_path
            
            # 文件名匹配
            file_basename = Path(filename).name
            for file_path in self.codebase_path.rglob(file_basename):
                if file_path.is_file():
                    return file_path
            
            return None
        except Exception as e:
            self.logger.warning(f"查找文件失败: {str(e)}")
            return None
    
    def _get_function_context(self, file_path: Path, line_number: str) -> Optional[str]:
        """获取函数上下文"""
        try:
            if not line_number or not line_number.isdigit():
                return None
            
            content = self._read_file(str(file_path))
            if not content:
                return None
            
            lines = content.split('\n')
            target_line = int(line_number) - 1  # 转为0基索引
            
            if target_line < 0 or target_line >= len(lines):
                return None
            
            # 简单的函数边界检测
            function_start = target_line
            function_end = target_line
            
            # 向上查找函数开始
            brace_count = 0
            for i in range(target_line, -1, -1):
                line = lines[i].strip()
                if '{' in line:
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')
                
                # 简单的函数签名检测
                if (brace_count <= 0 and 
                    ('(' in line and ')' in line) and 
                    not line.startswith('//') and 
                    not line.startswith('*')):
                    function_start = i
                    break
            
            # 向下查找函数结束
            brace_count = 0
            for i in range(function_start, len(lines)):
                line = lines[i].strip()
                if '{' in line:
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')
                    if brace_count <= 0 and i > function_start:
                        function_end = i
                        break
            
            # 返回函数上下文
            if function_end > function_start:
                function_lines = lines[function_start:function_end + 1]
                return '\n'.join(f"{i + function_start + 1:4d}: {line}" for i, line in enumerate(function_lines))
            
            return None
        except Exception as e:
            self.logger.warning(f"获取函数上下文失败: {str(e)}")
            return None
    
    def _find_related_files(self, file_path: Path) -> List[str]:
        """查找相关文件"""
        try:
            if not self.codebase_path:
                return []
            
            related_files = []
            file_stem = file_path.stem
            file_dir = file_path.parent
            
            # 查找同名的头文件/源文件
            for ext in ['.h', '.hpp', '.c', '.cpp']:
                related_path = file_dir / f"{file_stem}{ext}"
                if related_path.exists() and related_path != file_path:
                    related_files.append(str(related_path.relative_to(self.codebase_path)))
            
            # 查找同目录下的相关文件
            for sibling in file_dir.iterdir():
                if (sibling.is_file() and 
                    sibling.suffix.lower() in ['.c', '.cpp', '.h', '.hpp'] and
                    sibling != file_path and
                    len(related_files) < 5):
                    related_files.append(str(sibling.relative_to(self.codebase_path)))
            
            return related_files
        except Exception as e:
            self.logger.warning(f"查找相关文件失败: {str(e)}")
            return []
    
    def _get_codebase_summary(self) -> Dict[str, Any]:
        """获取代码库概要信息"""
        try:
            if not self.codebase_path:
                return {}
            
            summary = {
                "total_files": 0,
                "c_cpp_files": 0,
                "header_files": 0,
                "directories": 0
            }
            
            for item in self.codebase_path.rglob('*'):
                if item.is_file():
                    summary["total_files"] += 1
                    if item.suffix.lower() in ['.c', '.cpp']:
                        summary["c_cpp_files"] += 1
                    elif item.suffix.lower() in ['.h', '.hpp']:
                        summary["header_files"] += 1
                elif item.is_dir():
                    summary["directories"] += 1
            
            return summary
        except Exception as e:
            self.logger.warning(f"获取代码库概要失败: {str(e)}")
            return {}
    
    def _analyze_function(self, function_name: str) -> Dict[str, Any]:
        """分析函数"""
        # 这里可以实现更复杂的函数分析逻辑
        return {"function_name": function_name, "analysis": "Function analysis not implemented"}
    
    def _find_function_calls(self, function_name: str) -> List[Dict[str, Any]]:
        """查找函数调用"""
        return self._search_in_files(f"{function_name}\\s*\\(")
    
    def _get_file_structure(self, file_path: str) -> Dict[str, Any]:
        """获取文件结构"""
        content = self._read_file(file_path)
        if not content:
            return {}
        
        # 简单的结构分析
        functions = []
        import re
        
        # 查找函数定义
        function_pattern = r'^\s*(?:static\s+)?(?:inline\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*{'
        for i, line in enumerate(content.split('\n'), 1):
            match = re.match(function_pattern, line)
            if match:
                functions.append({
                    "name": match.group(1),
                    "line": i
                })
        
        return {
            "functions": functions,
            "total_lines": len(content.split('\n'))
        }
    
    def _analyze_data_flow(self, variable_name: str, file_path: str) -> Dict[str, Any]:
        """分析数据流"""
        # 这里可以实现数据流分析逻辑
        return {"variable": variable_name, "file": file_path, "analysis": "Data flow analysis not implemented"}
