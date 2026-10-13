"""
代码分析Agent - 完整的Function Calling实现
支持工具调用、上下文维护和ReAct模式
"""
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from .ai_client import StaticAnalysisAIClient
from ..utils.logger import get_session_logger


class CodeAnalysisAgentV2:
    """代码分析Agent - 使用Function Calling"""
    
    def __init__(self, session_id: str, codebase_path: str = None):
        self.session_id = session_id
        self.codebase_path = Path(codebase_path) if codebase_path else None
        self.logger = get_session_logger(session_id)
        self.ai_client = StaticAnalysisAIClient(session_id)
        
        # 对话历史（维护上下文）
        self.conversation_history = []
        
        # 工具调用统计
        self.tool_call_count = 0
        self.max_tool_calls = 10  # 最多允许10次工具调用
        
        # 定义可用工具
        self.tools = self._define_tools()
        
        self.logger.info("=" * 100)
        self.logger.info("初始化 CodeAnalysisAgentV2")
        self.logger.info(f"代码库路径: {self.codebase_path}")
        self.logger.info(f"可用工具数量: {len(self.tools)}")
        self.logger.info("=" * 100)
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义Agent可用的工具（OpenAI Function Calling格式）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取代码库中的文件内容。用于查看问题所在文件的完整代码。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径，相对于代码库根目录，例如: 'array_bounds.c' 或 'src/main.c'"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "列出代码库中指定目录的文件和子目录。用于了解代码库结构。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "目录路径，相对于代码库根目录，例如: '.' 表示根目录，'src' 表示src目录"
                            }
                        },
                        "required": ["directory_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "在代码库中搜索包含指定关键字的代码行。用于查找相关的代码片段。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "要搜索的关键字，例如: 'buffer', 'malloc', '函数名'"
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "文件模式，例如: '*.c', '*.h'。默认搜索所有文件。"
                            }
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_function_context",
                    "description": "获取指定文件中某一行所在函数的完整代码。用于理解问题行的函数上下文。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "line_number": {
                                "type": "integer",
                                "description": "行号"
                            }
                        },
                        "required": ["file_path", "line_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_variable_usage",
                    "description": "追踪变量在文件中的所有使用位置（声明、赋值、读取）。对于分析数组越界、未初始化变量、缓冲区问题非常有用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "variable_name": {
                                "type": "string",
                                "description": "变量名，例如: 'buffer', 'index', 'ptr'"
                            },
                            "line_number": {
                                "type": "integer",
                                "description": "可选：从哪一行开始查找（用于限定在某个函数内）"
                            }
                        },
                        "required": ["file_path", "variable_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_call_graph",
                    "description": "获取函数的调用关系：哪些函数调用了它（callers），它调用了哪些函数（callees）。对于分析资源泄漏、调用链问题非常有用。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "函数名，例如: 'malloc', 'process_data', 'main'"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "可选：限定在某个文件中查找"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            }
        ]
    
    def analyze_uncertain_issue(
        self,
        issue_data: Dict[str, Any],
        rule_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析不确定规则的问题
        
        Args:
            issue_data: 问题数据 {issue_name, issue_file, issue_line, issue_description}
            rule_info: 规则信息 {rule_code, rule_name, rule_description}
            
        Returns:
            分析结果 {is_real_issue, confidence, analysis_result, reasoning, evidence, recommendations}
        """
        try:
            self.logger.info("=" * 100)
            self.logger.info(f">>> 开始AI Agent分析问题（V2 - Function Calling）<<<")
            self.logger.info(f"问题名称: {issue_data.get('issue_name')}")
            self.logger.info(f"问题文件: {issue_data.get('issue_file')}")
            self.logger.info(f"问题行号: {issue_data.get('issue_line')}")
            self.logger.info(f"规则编号: {rule_info.get('rule_code', 'N/A')}")
            self.logger.info("=" * 100)
            
            if not self.codebase_path or not self.codebase_path.exists():
                self.logger.warning("无法访问代码库，跳过AI分析")
                return {
                    "is_real_issue": True,
                    "confidence": 0.5,
                    "analysis_result": "无法访问代码库，无法进行深度分析",
                    "reasoning": "代码库不可用",
                    "evidence": [],
                    "recommendations": "建议人工审查"
                }
            
            # 重置对话历史和工具调用计数
            self.conversation_history = []
            self.tool_call_count = 0
            
            # 构建初始提示词
            initial_prompt = self._build_initial_prompt(issue_data, rule_info)
            
            # 执行ReAct循环（思考-行动-观察）
            result = self._react_loop(initial_prompt, issue_data, rule_info)
            
            self.logger.info("=" * 100)
            self.logger.info(f">>> AI Agent分析完成 <<<")
            self.logger.info(f"是否为真实问题: {result.get('is_real_issue')}")
            self.logger.info(f"置信度: {result.get('confidence')}")
            self.logger.info(f"工具调用次数: {self.tool_call_count}")
            self.logger.info("=" * 100)
            
            return result
            
        except Exception as e:
            error_msg = f"AI Agent分析失败: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "is_real_issue": True,
                "confidence": 0.5,
                "analysis_result": error_msg,
                "reasoning": "分析过程出错",
                "evidence": [],
                "recommendations": "建议人工审查"
            }
    
    def _build_initial_prompt(
        self,
        issue_data: Dict[str, Any],
        rule_info: Dict[str, Any]
    ) -> str:
        """构建初始提示词"""
        
        issue_name = issue_data.get('issue_name', '未知问题')
        issue_file = issue_data.get('issue_file', '未知文件')
        issue_line = issue_data.get('issue_line', '未知行号')
        issue_desc = issue_data.get('issue_description', '无描述')
        
        rule_code = rule_info.get('rule_code', '未知规则')
        rule_name = rule_info.get('rule_name', '未知规则名称')
        rule_desc = rule_info.get('rule_description', '无规则描述')
        
        prompt = f"""你是一个专业的C/C++代码静态分析专家。你的任务是通过深度代码分析，判断以下静态分析工具报告的问题是否为**确定存在的真实问题**。

**问题信息：**
- 规则编号：{rule_code}
- 规则名称：{rule_name}
- 规则描述：{rule_desc}
- 问题位置：{issue_file}:{issue_line}
- 问题描述：{issue_desc}

**关键原则：宁可漏过，不可误报！**

我们要给开发人员提供的问题必须是**确定存在**的问题。如果无法通过代码分析**完全确认**问题一定会发生，就应该判定为误报。

**严格的判断标准：**

✅ **真实问题（is_real_issue: true）的条件：**
- 问题在当前代码中**一定会触发**，不是"可能"或"潜在"
- 对于数组越界：必须通过代码分析确认索引**一定**会超出数组范围
- 对于缓冲区溢出：必须确认写入的数据**一定**会超出缓冲区大小
- 对于未初始化变量：必须确认变量在使用前**一定**没有被赋值
- 对于资源泄漏：必须确认在所有代码路径中资源**一定**不会被释放
- 有充分的代码证据支持，不是基于假设

❌ **误报（is_real_issue: false）的情况：**
- 代码有边界检查、输入验证或其他保护措施
- 问题只在特定假设条件下发生（如"如果输入超过X"，但代码中有检查）
- 变量在使用前已经被正确初始化
- 资源在所有路径中都被正确释放
- 数组/缓冲区的大小足够容纳所有可能的数据
- 无法通过代码分析完全确认问题一定发生

**你必须使用的工具（按需调用）：**

1. **read_file(file_path)**: 读取完整文件内容 - **必须首先调用此工具！**
2. **get_function_context(file_path, line_number)**: 获取函数完整代码
3. **get_variable_usage(file_path, variable_name)**: 追踪变量的所有使用位置（声明、赋值、读取）
4. **search_code(keyword, file_pattern)**: 搜索相关代码（如函数调用、宏定义等）
5. **get_call_graph(function_name, file_path)**: 获取函数调用关系
6. **list_directory(directory_path)**: 查看代码库结构

**强制性分析步骤：**

1. **第一步：必须调用 read_file 读取问题所在文件的完整代码**
2. **第二步：分析问题行的上下文（函数、变量定义、边界检查等）**
3. **第三步：使用 get_variable_usage 追踪关键变量（如数组、索引、缓冲区等）**
4. **第四步：分析所有相关的代码路径，确认问题是否一定会触发**
5. **第五步：寻找保护措施（边界检查、输入验证、初始化等）**
6. **第六步：如果涉及跨文件调用，使用 search_code 或 get_call_graph 获取更多信息**

**特别注意：**

⚠️ **对于数组越界、缓冲区溢出等问题：**
- 必须追踪索引变量的所有赋值和使用
- 必须确认数组/缓冲区的大小
- 必须检查是否有边界检查（如 if (index < size)）
- 只有在索引**一定**会超出范围时才判定为真实问题

⚠️ **对于未初始化变量问题：**
- 必须追踪变量从声明到使用的所有代码路径
- 必须确认在所有路径中变量都没有被初始化
- 如果存在任何一条路径会初始化变量，就判定为误报

⚠️ **不要猜测，不要假设：**
- 所有判断必须基于实际代码
- 如果看不到完整的上下文，必须调用工具获取
- 如果不确定，倾向于判定为误报（is_real_issue: false）

**最终回答格式要求：**

当你完成深度分析后，必须以JSON格式返回结果（不要用markdown代码块包裹）：

{{
    "is_real_issue": true/false,
    "confidence": 0.95,
    "analysis_result": "简短结论：这是/不是真实问题",
    "reasoning": "详细的分析过程：\n1. 读取文件发现...\n2. 追踪变量发现...\n3. 检查边界条件发现...\n4. 综合判断：问题一定会/不会发生，因为...",
    "evidence": ["证据1：具体代码行", "证据2：追踪结果", "证据3：边界检查情况"],
    "recommendations": "如果是真实问题，提供修复建议；如果是误报，说明为什么是安全的"
}}

**现在开始分析！请立即调用 read_file 工具读取问题文件，然后逐步深入分析。记住：必须完全确认问题一定存在，才能判定为真实问题！**"""
        
        return prompt
    
    def _react_loop(
        self,
        initial_prompt: str,
        issue_data: Dict[str, Any],
        rule_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ReAct循环：Reasoning（推理）+ Acting（行动）
        
        循环流程：
        1. AI思考并决定调用哪个工具
        2. 执行工具调用
        3. 将工具结果反馈给AI
        4. AI继续思考或给出最终答案
        """
        import asyncio
        import concurrent.futures
        
        # 添加初始消息到对话历史
        self.conversation_history.append({
            "role": "user",
            "content": initial_prompt
        })
        
        self.logger.info("开始ReAct循环...")
        
        while self.tool_call_count < self.max_tool_calls:
            self.logger.info(f"\n--- ReAct循环 第{self.tool_call_count + 1}轮 ---")
            
            # 调用AI（带工具定义）
            try:
                # 使用线程池在新线程中运行异步代码
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._call_ai_with_tools()
                    )
                    ai_response = future.result(timeout=120)
            except Exception as e:
                self.logger.error(f"调用AI失败: {str(e)}")
                break
            
            # 检查AI是否要调用工具
            if ai_response.get("tool_calls"):
                # AI决定调用工具
                tool_calls = ai_response["tool_calls"]
                self.logger.info(f"AI请求调用 {len(tool_calls)} 个工具")
                
                # 将AI的响应添加到历史
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response.get("content") or "",
                    "tool_calls": tool_calls
                })
                
                # 执行所有工具调用
                for tool_call in tool_calls:
                    self.tool_call_count += 1
                    tool_result = self._execute_tool_call(tool_call)
                    
                    # 将工具结果添加到历史
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "name": tool_call["function"]["name"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
            else:
                # AI给出了最终答案（不再调用工具）
                self.logger.info("AI给出最终答案")
                final_content = ai_response.get("content", "")
                
                # 解析最终答案
                result = self._parse_final_answer(final_content)
                return result
        
        # 达到最大工具调用次数
        self.logger.warning(f"达到最大工具调用次数限制: {self.max_tool_calls}")
        return {
            "is_real_issue": True,
            "confidence": 0.5,
            "analysis_result": "分析超时，达到最大工具调用次数",
            "reasoning": "Agent调用了太多工具仍未得出结论",
            "evidence": [],
            "recommendations": "建议人工审查"
        }
    
    async def _call_ai_with_tools(self) -> Dict[str, Any]:
        """调用AI（带工具定义）"""
        import httpx
        
        self.logger.info("调用AI（带工具定义）...")
        self.logger.info(f"当前对话历史长度: {len(self.conversation_history)}")
        
        # 准备请求
        request_data = {
            "model": self.ai_client.model_name,
            "messages": self.conversation_history,
            "tools": self.tools,
            "tool_choice": "auto",  # 让AI自动决定是否调用工具
            **self.ai_client.model_params
        }
        
        self.logger.info("=" * 80)
        self.logger.info("AI请求（带工具）:")
        self.logger.info(f"消息数: {len(request_data['messages'])}")
        self.logger.info(f"工具数: {len(request_data['tools'])}")
        self.logger.info("=" * 80)
        
        start_time = time.time()
        
        # 发送请求
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),
            proxies=self.ai_client.proxies
        ) as client:
            response = await client.post(
                f"{self.ai_client.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.ai_client.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            
            response.raise_for_status()
            response_data = response.json()
        
        elapsed = time.time() - start_time
        self.logger.info(f"AI响应完成，耗时: {elapsed:.2f}秒")
        
        # 提取响应
        choice = response_data["choices"][0]
        message = choice["message"]
        
        self.logger.info("=" * 80)
        self.logger.info("AI响应:")
        self.logger.info(f"内容: {message.get('content', '无')}")
        self.logger.info(f"工具调用: {message.get('tool_calls', '无')}")
        self.logger.info("=" * 80)
        
        return message
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        tool_name = tool_call["function"]["name"]
        tool_args = json.loads(tool_call["function"]["arguments"])
        
        self.logger.info(f"\n>>> 执行工具: {tool_name}")
        self.logger.info(f"参数: {json.dumps(tool_args, ensure_ascii=False)}")
        
        try:
            # 根据工具名称调用相应的方法
            if tool_name == "read_file":
                result = self._tool_read_file(tool_args["file_path"])
            elif tool_name == "list_directory":
                result = self._tool_list_directory(tool_args["directory_path"])
            elif tool_name == "search_code":
                result = self._tool_search_code(
                    tool_args["keyword"],
                    tool_args.get("file_pattern")
                )
            elif tool_name == "get_function_context":
                result = self._tool_get_function_context(
                    tool_args["file_path"],
                    tool_args["line_number"]
                )
            elif tool_name == "get_variable_usage":
                result = self._tool_get_variable_usage(
                    tool_args["file_path"],
                    tool_args["variable_name"],
                    tool_args.get("line_number")
                )
            elif tool_name == "get_call_graph":
                result = self._tool_get_call_graph(
                    tool_args["function_name"],
                    tool_args.get("file_path")
                )
            else:
                result = {"error": f"未知工具: {tool_name}"}
            
            self.logger.info(f"工具执行成功")
            self.logger.info(f"结果: {str(result)[:200]}...")
            
            return result
            
        except Exception as e:
            error_msg = f"工具执行失败: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    # ========== 工具实现 ==========
    
    def _tool_read_file(self, file_path: str) -> Dict[str, Any]:
        """工具：读取文件"""
        try:
            full_path = self.codebase_path / file_path
            if not full_path.exists():
                # 尝试查找文件
                found_files = list(self.codebase_path.rglob(Path(file_path).name))
                if found_files:
                    full_path = found_files[0]
                else:
                    return {"error": f"文件不存在: {file_path}"}
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 添加行号
            lines = content.split('\n')
            numbered_lines = [f"{i+1:4d} | {line}" for i, line in enumerate(lines)]
            
            return {
                "file_path": str(full_path.relative_to(self.codebase_path)),
                "content": '\n'.join(numbered_lines),
                "line_count": len(lines)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_list_directory(self, directory_path: str) -> Dict[str, Any]:
        """工具：列出目录"""
        try:
            if directory_path == ".":
                full_path = self.codebase_path
            else:
                full_path = self.codebase_path / directory_path
            
            if not full_path.exists():
                return {"error": f"目录不存在: {directory_path}"}
            
            items = []
            for item in full_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "directory": str(full_path.relative_to(self.codebase_path)),
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_search_code(self, keyword: str, file_pattern: str = None) -> Dict[str, Any]:
        """工具：搜索代码"""
        try:
            results = []
            pattern = file_pattern or "*"
            
            for file_path in self.codebase_path.rglob(pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if keyword in line:
                                    results.append({
                                        "file": str(file_path.relative_to(self.codebase_path)),
                                        "line": line_num,
                                        "content": line.strip()
                                    })
                                    if len(results) >= 20:  # 限制结果数量
                                        break
                    except:
                        continue
                
                if len(results) >= 20:
                    break
            
            return {
                "keyword": keyword,
                "results": results,
                "count": len(results),
                "total_matches": len(results)  # 兼容性字段
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_get_function_context(self, file_path: str, line_number: int) -> Dict[str, Any]:
        """工具：获取函数上下文"""
        try:
            full_path = self.codebase_path / file_path
            if not full_path.exists():
                found_files = list(self.codebase_path.rglob(Path(file_path).name))
                if found_files:
                    full_path = found_files[0]
                else:
                    return {"error": f"文件不存在: {file_path}"}
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 简单的函数边界检测
            start_line = line_number - 1
            end_line = line_number - 1
            
            # 向上查找函数开始
            for i in range(line_number - 2, -1, -1):
                if re.search(r'^\w+.*\(.*\)\s*\{', lines[i]):
                    start_line = i
                    break
                if i > 0 and line_number - i > 50:  # 最多向上50行
                    break
            
            # 向下查找函数结束
            brace_count = 0
            for i in range(start_line, len(lines)):
                brace_count += lines[i].count('{') - lines[i].count('}')
                if brace_count == 0 and i > start_line:
                    end_line = i
                    break
                if i - start_line > 100:  # 最多100行
                    end_line = i
                    break
            
            # 提取函数代码
            function_lines = lines[start_line:end_line + 1]
            numbered_lines = [
                f"{'>>>' if i == line_number - 1 else '   '} {i+1:4d} | {line.rstrip()}"
                for i, line in enumerate(function_lines, start=start_line)
            ]
            
            return {
                "file_path": str(full_path.relative_to(self.codebase_path)),
                "target_line": line_number,
                "function_start": start_line + 1,
                "function_end": end_line + 1,
                "content": '\n'.join(numbered_lines)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_get_variable_usage(self, file_path: str, variable_name: str, line_number: int = None) -> Dict[str, Any]:
        """工具：获取变量使用情况"""
        try:
            full_path = self.codebase_path / file_path
            if not full_path.exists():
                found_files = list(self.codebase_path.rglob(Path(file_path).name))
                if found_files:
                    full_path = found_files[0]
                else:
                    return {"error": f"文件不存在: {file_path}"}
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            usages = []
            
            # 如果指定了行号，限定在该行所在的函数内
            search_start = 0
            search_end = len(lines)
            
            if line_number:
                # 找到函数边界
                for i in range(line_number - 2, -1, -1):
                    if re.search(r'^\w+.*\(.*\)\s*\{', lines[i]):
                        search_start = i
                        break
                
                brace_count = 0
                for i in range(search_start, len(lines)):
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    if brace_count == 0 and i > search_start:
                        search_end = i + 1
                        break
            
            # 搜索变量使用
            # 匹配模式：声明、赋值、读取
            patterns = [
                (r'\b(int|char|float|double|void|struct|unsigned|long|short)\s+\*?\s*' + re.escape(variable_name) + r'\b', 'declaration'),
                (re.escape(variable_name) + r'\s*\[', 'array_access'),
                (re.escape(variable_name) + r'\s*=', 'assignment'),
                (r'=\s*' + re.escape(variable_name) + r'\b', 'read'),
                (r'\b' + re.escape(variable_name) + r'\s*\(', 'function_call'),
                (r'\b' + re.escape(variable_name) + r'\b', 'usage'),
            ]
            
            for i in range(search_start, search_end):
                line = lines[i]
                for pattern, usage_type in patterns:
                    if re.search(pattern, line):
                        usages.append({
                            "line_number": i + 1,
                            "type": usage_type,
                            "content": line.strip(),
                            "context": f"{i+1:4d} | {line.rstrip()}"
                        })
                        break  # 只记录第一个匹配的类型
            
            return {
                "file_path": str(full_path.relative_to(self.codebase_path)),
                "variable_name": variable_name,
                "search_range": f"lines {search_start + 1} - {search_end}",
                "total_usages": len(usages),
                "usages": usages[:20]  # 最多返回20个使用位置
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_get_call_graph(self, function_name: str, file_path: str = None) -> Dict[str, Any]:
        """工具：获取函数调用图"""
        try:
            # 确定搜索范围
            if file_path:
                full_path = self.codebase_path / file_path
                if not full_path.exists():
                    found_files = list(self.codebase_path.rglob(Path(file_path).name))
                    if found_files:
                        full_path = found_files[0]
                    else:
                        return {"error": f"文件不存在: {file_path}"}
                search_files = [full_path]
            else:
                # 搜索所有 .c 和 .h 文件
                search_files = list(self.codebase_path.rglob("*.c")) + list(self.codebase_path.rglob("*.h"))
            
            # 查找函数定义
            function_definition = None
            definition_file = None
            
            # 函数定义模式：返回类型 函数名(参数) {
            func_def_pattern = re.compile(r'^\s*\w+\s+\*?\s*' + re.escape(function_name) + r'\s*\([^)]*\)\s*\{?')
            
            for file in search_files:
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    for i, line in enumerate(lines):
                        if func_def_pattern.search(line):
                            function_definition = {
                                "file": str(file.relative_to(self.codebase_path)),
                                "line": i + 1,
                                "signature": line.strip()
                            }
                            definition_file = file
                            break
                    
                    if function_definition:
                        break
                except:
                    continue
            
            # 查找调用者（哪些函数调用了这个函数）
            callers = []
            # 查找被调用者（这个函数调用了哪些函数）
            callees = []
            
            func_call_pattern = re.compile(r'\b' + re.escape(function_name) + r'\s*\(')
            
            for file in search_files:
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    # 查找调用这个函数的地方
                    for i, line in enumerate(lines):
                        if func_call_pattern.search(line):
                            # 找到调用所在的函数
                            caller_func = self._find_enclosing_function(lines, i)
                            if caller_func and caller_func != function_name:
                                callers.append({
                                    "function": caller_func,
                                    "file": str(file.relative_to(self.codebase_path)),
                                    "line": i + 1,
                                    "context": line.strip()
                                })
                except:
                    continue
            
            # 如果找到函数定义，查找它调用的函数
            if definition_file:
                try:
                    with open(definition_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    # 找到函数体
                    start_line = function_definition["line"] - 1
                    end_line = start_line
                    
                    brace_count = 0
                    for i in range(start_line, len(lines)):
                        brace_count += lines[i].count('{') - lines[i].count('}')
                        if brace_count == 0 and i > start_line:
                            end_line = i
                            break
                    
                    # 在函数体内查找函数调用
                    func_call_general = re.compile(r'\b([a-zA-Z_]\w+)\s*\(')
                    for i in range(start_line, end_line + 1):
                        matches = func_call_general.findall(lines[i])
                        for match in matches:
                            # 排除常见的关键字和当前函数本身
                            if match not in ['if', 'while', 'for', 'switch', 'return', 'sizeof', function_name]:
                                callees.append({
                                    "function": match,
                                    "line": i + 1,
                                    "context": lines[i].strip()
                                })
                except:
                    pass
            
            return {
                "function_name": function_name,
                "definition": function_definition,
                "callers": callers[:10],  # 最多返回10个调用者
                "callees": callees[:10],  # 最多返回10个被调用函数
                "total_callers": len(callers),
                "total_callees": len(callees)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _find_enclosing_function(self, lines: List[str], line_index: int) -> Optional[str]:
        """查找包围指定行的函数名"""
        # 向上查找函数定义
        func_pattern = re.compile(r'^\s*\w+\s+\*?\s*([a-zA-Z_]\w+)\s*\([^)]*\)\s*\{?')
        
        for i in range(line_index, -1, -1):
            match = func_pattern.search(lines[i])
            if match:
                return match.group(1)
            if i < line_index - 100:  # 最多向上查找100行
                break
        
        return None
    
    def _parse_final_answer(self, content: str) -> Dict[str, Any]:
        """解析AI的最终答案"""
        try:
            self.logger.info("开始解析AI最终答案...")
            self.logger.info(f"原始内容长度: {len(content)} 字符")
            
            # 尝试从内容中提取JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group()
                self.logger.info(f"提取到JSON: {json_str[:200]}...")
                
                try:
                    result = json.loads(json_str)
                    
                    # 验证必需字段
                    if "is_real_issue" in result and "confidence" in result:
                        self.logger.info("JSON解析成功，包含必需字段")
                        return {
                            "is_real_issue": bool(result["is_real_issue"]),
                            "confidence": float(result["confidence"]),
                            "analysis_result": result.get("analysis_result", ""),
                            "reasoning": result.get("reasoning", content),
                            "evidence": result.get("evidence", []),
                            "recommendations": result.get("recommendations", "")
                        }
                except json.JSONDecodeError as je:
                    self.logger.warning(f"JSON解析失败: {str(je)}")
            
            # 如果无法解析JSON，从文本中智能推断
            self.logger.info("未找到有效JSON，尝试从文本推断...")
            
            content_lower = content.lower()
            
            # 更准确的关键词匹配
            is_real_issue = True
            confidence = 0.6
            
            # 检查明确的误报标识
            false_positive_keywords = [
                '误报', 'false positive', '不是真实问题', 'not a real issue',
                '不是问题', 'not an issue', '是安全的', 'is safe',
                '这是一个误报', 'this is a false positive'
            ]
            
            # 检查明确的真实问题标识
            real_issue_keywords = [
                '真实问题', 'real issue', '确实存在', 'does exist',
                '这是一个真实问题', 'this is a real issue',
                '违反规则', 'violates the rule', '违反了规则'
            ]
            
            # 优先检查明确的判断
            for keyword in false_positive_keywords:
                if keyword in content_lower:
                    is_real_issue = False
                    confidence = 0.8
                    self.logger.info(f"检测到误报关键词: {keyword}")
                    break
            
            if is_real_issue:  # 如果还没判断为误报，再检查真实问题
                for keyword in real_issue_keywords:
                    if keyword in content_lower:
                        is_real_issue = True
                        confidence = 0.8
                        self.logger.info(f"检测到真实问题关键词: {keyword}")
                        break
            
            # 提取分析结果摘要（取前200字符）
            analysis_result = content[:200] + "..." if len(content) > 200 else content
            
            self.logger.info(f"推断结果: is_real_issue={is_real_issue}, confidence={confidence}")
            
            return {
                "is_real_issue": is_real_issue,
                "confidence": confidence,
                "analysis_result": analysis_result,
                "reasoning": content,
                "evidence": [],
                "recommendations": "建议人工审查"
            }
            
        except Exception as e:
            self.logger.error(f"解析最终答案失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "is_real_issue": True,
                "confidence": 0.5,
                "analysis_result": "解析失败",
                "reasoning": content,
                "evidence": [],
                "recommendations": "建议人工审查"
            }

