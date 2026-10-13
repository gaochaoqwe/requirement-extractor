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
from app.staticAnalysis.filter.services.ai_client import StaticAnalysisAIClient
from app.staticAnalysis.filter.utils.logger import get_session_logger


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
        self.max_tool_calls = 50  # 最多允许50次工具调用（与函数审查Agent一致）
        
        # 缓存，避免重复读取
        self.global_var_cache = None
        self.function_cache = {}
        
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
                    "name": "get_dependency_function",
                    "description": "获取被当前函数调用的其他函数的完整代码。用于理解函数调用的具体实现。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要查看的函数名，如 'malloc', 'processData'"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_global_variable",
                    "description": "获取全局变量、宏定义或数组的定义信息。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "variable_name": {
                                "type": "string",
                                "description": "变量、宏或数组的名称"
                            }
                        },
                        "required": ["variable_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_calls",
                    "description": "搜索某个函数在项目中被哪些地方调用。用于理解函数的使用上下文。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要搜索的函数名"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_all_globals",
                    "description": "列出代码中可能使用的所有全局变量、宏定义和数组的名称。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_outline",
                    "description": "获取文件的结构大纲：函数列表、全局变量、宏定义等。**这是了解大型文件的首选工具**，避免加载整个文件内容。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径，相对于代码库根目录，例如: 'main.c' 或 'src/utils.c'"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file_range",
                    "description": "按行范围读取文件的部分内容。用于查看特定代码区域，适合大型文件。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径，相对于代码库根目录"
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "起始行号（从1开始，包含）"
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "结束行号（包含）"
                            }
                        },
                        "required": ["file_path", "start_line", "end_line"]
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
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_by_name",
                    "description": "在项目中按函数名搜索函数，用于快速定位功能实现。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_name": {
                                "type": "string",
                                "description": "要搜索的函数名"
                            }
                        },
                        "required": ["function_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_function_in_file",
                    "description": "在指定文件中搜索特定函数的代码。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "function_name": {
                                "type": "string",
                                "description": "要搜索的函数名"
                            }
                        },
                        "required": ["file_path", "function_name"]
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

1. **get_file_outline(file_path)**: 获取文件结构大纲（函数列表、全局变量、宏定义）- **对于大型文件，首选此工具！**
2. **read_file_range(file_path, start_line, end_line)**: 按行范围读取文件内容
3. **get_function_context(file_path, line_number)**: 获取问题行所在函数的完整代码
4. **get_variable_usage(file_path, variable_name)**: 追踪变量的所有使用位置（声明、赋值、读取）
5. **search_code(keyword, file_pattern)**: 搜索相关代码（如函数调用、宏定义等）
6. **get_call_graph(function_name, file_path)**: 获取函数调用关系
7. **list_directory(directory_path)**: 查看代码库结构

**推荐的分析步骤（智能使用工具）：**

1. **第一步：了解文件结构** - 调用 **get_file_outline** 获取文件的函数列表和结构概览
2. **第二步：分析问题行上下文** - 调用 **get_function_context** 获取问题行所在函数的完整代码
3. **第三步：追踪关键变量** - 使用 **get_variable_usage** 追踪相关变量（如数组、索引、缓冲区等）
4. **第四步：查看周边代码（如需要）** - 使用 **read_file_range** 查看特定行范围的代码
5. **第五步：分析调用关系（如需要）** - 使用 **get_call_graph** 或 **search_code** 分析跨函数/跨文件的行为
6. **第六步：综合判断** - 基于所有证据，判断问题是否一定会发生

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
                debug_context = getattr(self, "_last_request_debug_info", None)
                if debug_context:
                    try:
                        import json as _json
                        self.logger.error(
                            "最近一次AI请求上下文: %s",
                            _json.dumps(debug_context, ensure_ascii=False)
                        )
                    except Exception:
                        self.logger.error("最近一次AI请求上下文: %s", debug_context)
                messages_preview = getattr(self, "_last_messages_preview", None)
                if messages_preview:
                    self.logger.error("对话消息预览: %s", messages_preview)
                import traceback
                self.logger.error("AI调用堆栈:\n%s", traceback.format_exc())
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
        
        # ⚠️ 限制对话历史长度，避免内网模型请求过大
        # 策略：保留初始prompt（第1条消息）+ 最近N轮对话
        max_history_messages = 15  # 最多保留15条消息
        if len(self.conversation_history) > max_history_messages:
            # 保留第1条（初始prompt）和最后14条消息
            messages_to_send = [self.conversation_history[0]] + self.conversation_history[-(max_history_messages-1):]
            self.logger.info(f"对话历史过长，截断为 {len(messages_to_send)} 条消息（保留初始prompt + 最近{max_history_messages-1}条）")
        else:
            messages_to_send = self.conversation_history
        
        # 准备请求
        request_data = {
            "model": self.ai_client.model_name,
            "messages": messages_to_send,
            "tools": self.tools,
            "tool_choice": "auto",  # 让AI自动决定是否调用工具
            **self.ai_client.model_params
        }
        
        # 缓存调试信息，方便在失败时快速定位
        try:
            self._last_messages_preview = [
                {
                    "role": msg.get("role"),
                    "content_preview": (msg.get("content") or "")[:200]
                }
                for msg in messages_to_send
            ]
        except Exception:
            self._last_messages_preview = None

        # 估算请求大小（用于诊断内网环境的限制问题）
        import json as json_module
        request_size_bytes = len(json_module.dumps(request_data, ensure_ascii=False).encode('utf-8'))
        request_size_kb = request_size_bytes / 1024
        
        self.logger.info("=" * 80)
        self.logger.info("AI请求（带工具）:")
        self.logger.info(f"消息数: {len(request_data['messages'])}")
        self.logger.info(f"工具数: {len(request_data['tools'])}")
        self.logger.info(f"预估请求大小: {request_size_kb:.2f} KB ({request_size_bytes} bytes)")
        if request_size_kb > 100:
            self.logger.warning(f"⚠️ 请求大小较大 ({request_size_kb:.2f} KB)，可能超过内网模型限制！")
        self.logger.info("=" * 80)
        
        self._last_request_debug_info = {
            "model": self.ai_client.model_name,
            "base_url": self.ai_client.base_url,
            "proxies": self.ai_client.proxies,
            "timeout_seconds": 120,
            "message_count": len(request_data["messages"]),
            "tool_count": len(request_data["tools"]),
            "request_size_kb": round(request_size_kb, 2)
        }

        start_time = time.time()
        
        # 发送请求
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(120.0),
            proxies=self.ai_client.proxies
        ) as client:
            try:
                response = await client.post(
                    f"{self.ai_client.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.ai_client.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_data
                )

                self.logger.info(
                    "AI原始响应: status=%s, headers=%s",
                    response.status_code,
                    {k: v for k, v in response.headers.items() if k.lower() in {"x-request-id", "date", "content-length"}}
                )

                response.raise_for_status()
                response_text_preview = response.text[:1000]
                self.logger.debug(f"AI响应文本预览(前1000字符): {response_text_preview}")
                response_data = response.json()
            except httpx.HTTPStatusError as e:
                self.logger.error(
                    "AI响应状态错误: status=%s, headers=%s",
                    e.response.status_code,
                    dict(e.response.headers)
                )
                self.logger.error(
                    "AI响应body: %s",
                    e.response.text[:2000]
                )
                raise
            except httpx.RequestError as e:
                self.logger.error(
                    "AI请求异常: type=%s, error=%s, request=%s",
                    e.__class__.__name__,
                    str(e),
                    getattr(e, "request", None)
                )
                raise
            except Exception as e:
                self.logger.error(f"AI调用过程中发生未知异常: {str(e)}")
                raise
        
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
            if tool_name == "get_dependency_function":
                result = self._tool_get_dependency_function(tool_args["function_name"])
            elif tool_name == "get_global_variable":
                result = self._tool_get_global_variable(tool_args["variable_name"])
            elif tool_name == "search_function_calls":
                result = self._tool_search_function_calls(tool_args["function_name"])
            elif tool_name == "list_all_globals":
                result = self._tool_list_all_globals()
            elif tool_name == "get_file_outline":
                result = self._tool_get_file_outline(tool_args["file_path"])
            elif tool_name == "read_file_range":
                result = self._tool_read_file_range(
                    tool_args["file_path"],
                    tool_args["start_line"],
                    tool_args["end_line"]
                )
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
            elif tool_name == "search_function_by_name":
                result = self._tool_search_function_by_name(
                    tool_args["function_name"]
                )
            elif tool_name == "search_function_in_file":
                result = self._tool_search_function_in_file(
                    tool_args["file_path"],
                    tool_args["function_name"]
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
    
    def _tool_get_file_outline(self, file_path: str) -> Dict[str, Any]:
        """工具：获取文件大纲（函数列表、全局变量、宏定义）"""
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
                lines = f.readlines()
            
            functions = []
            global_vars = []
            macros = []
            includes = []
            
            # 简单的C/C++代码解析
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # 匹配函数定义（简化版）
                func_match = re.match(r'^([a-zA-Z_][\w\s\*]*)\s+([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{?', stripped)
                if func_match and not stripped.startswith('//') and not stripped.startswith('/*'):
                    functions.append({
                        "name": func_match.group(2),
                        "signature": stripped.rstrip('{').strip(),
                        "line": i
                    })
                
                # 匹配全局变量（简化版）
                if re.match(r'^(static\s+)?(extern\s+)?(const\s+)?(int|char|float|double|void|struct|enum|unsigned|long|short)\s+', stripped):
                    if '(' not in stripped and not stripped.endswith(';'):  # 排除函数声明
                        global_vars.append({
                            "line": i,
                            "declaration": stripped[:80]  # 限制长度
                        })
                
                # 匹配宏定义
                if stripped.startswith('#define'):
                    macros.append({
                        "line": i,
                        "definition": stripped[:80]
                    })
                
                # 匹配include
                if stripped.startswith('#include'):
                    includes.append({
                        "line": i,
                        "file": stripped
                    })
            
            return {
                "file_path": str(full_path.relative_to(self.codebase_path)),
                "total_lines": len(lines),
                "functions": functions[:50],  # 最多返回50个函数
                "function_count": len(functions),
                "global_variables": global_vars[:20],  # 最多返回20个全局变量
                "macros": macros[:20],
                "includes": includes[:20]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_read_file_range(self, file_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """工具：按行范围读取文件"""
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
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            
            # 验证行号范围
            if start_line < 1 or start_line > total_lines:
                return {"error": f"起始行号 {start_line} 超出范围（文件共 {total_lines} 行）"}
            if end_line < start_line:
                return {"error": f"结束行号 {end_line} 小于起始行号 {start_line}"}
            
            # 限制单次读取行数，避免超出上下文
            max_range = 500  # 最多一次读取500行
            if end_line - start_line + 1 > max_range:
                return {"error": f"请求的行数过多（{end_line - start_line + 1}行），单次最多读取{max_range}行"}
            
            # 提取指定范围的行
            end_line = min(end_line, total_lines)
            selected_lines = all_lines[start_line-1:end_line]
            
            # 添加行号
            numbered_lines = [f"{start_line + i:4d} | {line.rstrip()}" for i, line in enumerate(selected_lines)]
            
            return {
                "file_path": str(full_path.relative_to(self.codebase_path)),
                "start_line": start_line,
                "end_line": end_line,
                "total_lines": total_lines,
                "content": '\n'.join(numbered_lines)
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
    
    def _tool_search_function_by_name(self, function_name: str) -> Dict[str, Any]:
        """工具：在项目中搜索函数"""
        try:
            results = []
            search_files = list(self.codebase_path.rglob("*.c")) + list(self.codebase_path.rglob("*.h")) + \
                          list(self.codebase_path.rglob("*.cpp")) + list(self.codebase_path.rglob("*.hpp"))
            
            # 函数定义模式
            func_pattern = re.compile(r'^\s*\w+\s+\*?\s*' + re.escape(function_name) + r'\s*\([^)]*\)\s*\{?')
            
            for file in search_files[:200]:  # 限制搜索文件数
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if func_pattern.search(line):
                            results.append({
                                "file": str(file.relative_to(self.codebase_path)),
                                "line": i,
                                "signature": line.strip()
                            })
                            
                            if len(results) >= 10:  # 最多返回10个结果
                                break
                except:
                    continue
                
                if len(results) >= 10:
                    break
            
            return {
                "function_name": function_name,
                "found": len(results) > 0,
                "count": len(results),
                "locations": results
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _tool_search_function_in_file(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """工具：在指定文件中搜索函数"""
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
                lines = f.readlines()
            
            results = []
            func_pattern = re.compile(r'^\s*\w+\s+\*?\s*' + re.escape(function_name) + r'\s*\([^)]*\)\s*\{?')
            
            for i, line in enumerate(lines, 1):
                if func_pattern.search(line):
                    # 尝试获取完整函数代码
                    func_start = i - 1
                    func_end = i - 1
                    brace_count = 0
                    in_function = False
                    
                    for j in range(i - 1, len(lines)):
                        if '{' in lines[j]:
                            in_function = True
                            brace_count += lines[j].count('{')
                        if '}' in lines[j]:
                            brace_count -= lines[j].count('}')
                            if in_function and brace_count <= 0:
                                func_end = j
                                break
                    
                    if func_end == i - 1:  # 如果没找到结束，取前50行
                        func_end = min(i - 1 + 50, len(lines) - 1)
                    
                    function_code = ''.join(lines[func_start:func_end + 1])
                    
                    results.append({
                        "line": i,
                        "signature": line.strip(),
                        "start_line": func_start + 1,
                        "end_line": func_end + 1,
                        "code": function_code
                    })
            
            return {
                "file_path": str(full_path.relative_to(self.codebase_path)),
                "function_name": function_name,
                "found": len(results) > 0,
                "count": len(results),
                "results": results
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
    
    # ========== 新增工具实现 ==========
    
    def _tool_get_dependency_function(self, function_name: str) -> Dict[str, Any]:
        """工具：获取依赖函数的代码"""
        try:
            # 检查缓存
            if function_name in self.function_cache:
                self.logger.info(f"从缓存中获取函数: {function_name}")
                return self.function_cache[function_name]
            
            # 常见标准库函数列表
            standard_functions = {
                'malloc', 'free', 'calloc', 'realloc',
                'memcpy', 'memset', 'memmove', 'memcmp',
                'strcpy', 'strncpy', 'strcat', 'strncat', 'strcmp', 'strncmp', 'strlen', 'strstr',
                'printf', 'fprintf', 'sprintf', 'snprintf', 'scanf', 'fscanf', 'sscanf',
                'fopen', 'fclose', 'fread', 'fwrite', 'fseek', 'ftell', 'feof', 'ferror',
                'exit', 'abort', 'atexit', 'system',
                'sin', 'cos', 'tan', 'sqrt', 'pow', 'exp', 'log',
                'time', 'clock', 'sleep', 'usleep'
            }
            
            # 如果是标准库函数，直接返回友好提示
            if function_name.lower() in standard_functions:
                result = {
                    "function_name": function_name,
                    "found": False,
                    "is_standard_library": True,
                    "message": f"{function_name} 是C标准库函数，无需查看实现。请基于你对标准库的理解进行审查。"
                }
                self.function_cache[function_name] = result
                return result
            
            # 在代码库中搜索函数定义
            self.logger.info(f"在代码库中搜索函数: {function_name}")
            func_pattern = re.compile(r'^\s*\w+\s+\*?\s*' + re.escape(function_name) + r'\s*\([^)]*\)\s*\{')
            
            for file_path in self.codebase_path.rglob('*.[ch]'):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        if func_pattern.search(line):
                            # 找到函数定义，提取完整函数代码
                            func_start = i
                            func_end = i
                            brace_count = 0
                            started = False
                            
                            for j in range(i, len(lines)):
                                for char in lines[j]:
                                    if char == '{':
                                        brace_count += 1
                                        started = True
                                    elif char == '}':
                                        brace_count -= 1
                                
                                if started and brace_count == 0:
                                    func_end = j
                                    break
                            
                            # 限制函数代码长度
                            if func_end - func_start > 200:
                                func_code = ''.join(lines[func_start:func_start + 200]) + "\n... (函数过长，已截断)"
                            else:
                                func_code = ''.join(lines[func_start:func_end + 1])
                            
                            result = {
                                "function_name": function_name,
                                "source_code": func_code,
                                "file_path": str(file_path.relative_to(self.codebase_path)),
                                "line": func_start + 1,
                                "found": True
                            }
                            
                            # 缓存结果
                            self.function_cache[function_name] = result
                            return result
                except:
                    continue
            
            # 未找到函数
            result = {
                "function_name": function_name,
                "found": False,
                "is_standard_library": False,
                "message": f"未找到函数 {function_name}，可能是外部库函数、系统调用或函数名不准确"
            }
            
            self.function_cache[function_name] = result
            return result
            
        except Exception as e:
            return {
                "function_name": function_name,
                "found": False,
                "error": f"查找函数时出错: {str(e)}"
            }
    
    def _tool_get_global_variable(self, variable_name: str) -> Dict[str, Any]:
        """工具：获取全局变量/宏定义"""
        try:
            # 初始化全局变量缓存（如果还没初始化）
            if self.global_var_cache is None:
                self.logger.info("初始化全局变量缓存...")
                self.global_var_cache = {}
                
                # 扫描代码库中的.h和.c文件，提取全局变量和宏定义
                for file_path in self.codebase_path.rglob('*.[ch]'):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        for i, line in enumerate(lines, 1):
                            stripped = line.strip()
                            
                            # 匹配宏定义
                            macro_match = re.match(r'#define\s+(\w+)\s+(.*)', stripped)
                            if macro_match:
                                macro_name = macro_match.group(1)
                                macro_value = macro_match.group(2).strip()
                                self.global_var_cache[macro_name] = {
                                    'type': 'macro',
                                    'file': str(file_path.relative_to(self.codebase_path)),
                                    'line': i,
                                    'code': stripped
                                }
                            
                            # 匹配全局变量（简化版）
                            global_var_match = re.match(
                                r'(static\s+)?(extern\s+)?(const\s+)?([a-zA-Z_]\w+)\s+([a-zA-Z_]\w+)\s*[=;]',
                                stripped
                            )
                            if global_var_match and not '(' in stripped:
                                var_name = global_var_match.group(5)
                                self.global_var_cache[var_name] = {
                                    'type': 'variable',
                                    'file': str(file_path.relative_to(self.codebase_path)),
                                    'line': i,
                                    'code': stripped
                                }
                    except:
                        continue
                
                self.logger.info(f"全局变量缓存初始化完成，共 {len(self.global_var_cache)} 项")
            
            # 查找变量
            if variable_name in self.global_var_cache:
                var_info = self.global_var_cache[variable_name]
                return {
                    "variable_name": variable_name,
                    "type": var_info.get('type', 'variable'),
                    "file": var_info.get('file', ''),
                    "line": var_info.get('line', 0),
                    "code": var_info.get('code', ''),
                    "found": True
                }
            else:
                return {
                    "variable_name": variable_name,
                    "found": False,
                    "message": f"未找到全局变量或宏定义 {variable_name}"
                }
        
        except Exception as e:
            return {
                "variable_name": variable_name,
                "found": False,
                "error": str(e)
            }
    
    def _tool_search_function_calls(self, function_name: str) -> Dict[str, Any]:
        """工具：搜索函数调用"""
        try:
            self.logger.info(f"搜索函数调用: {function_name}")
            call_pattern = re.compile(r'\b' + re.escape(function_name) + r'\s*\(')
            callers = []
            
            # 搜索.c和.h文件
            for file_path in self.codebase_path.rglob('*.[ch]'):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if call_pattern.search(line):
                            callers.append({
                                "file": str(file_path.relative_to(self.codebase_path)),
                                "line": i,
                                "code": line.strip()
                            })
                            
                            if len(callers) >= 20:  # 最多返回20个
                                break
                except:
                    continue
                
                if len(callers) >= 20:
                    break
            
            return {
                "function_name": function_name,
                "caller_count": len(callers),
                "callers": callers[:20],
                "message": f"找到 {len(callers)} 处调用" if callers else f"未找到对 {function_name} 的调用"
            }
        
        except Exception as e:
            return {
                "function_name": function_name,
                "error": str(e)
            }
    
    def _tool_list_all_globals(self) -> Dict[str, Any]:
        """工具：列出所有可用的全局变量"""
        try:
            # 确保全局变量缓存已初始化
            if self.global_var_cache is None:
                # 触发缓存初始化
                self._tool_get_global_variable("_dummy_var_to_init_cache")
            
            globals_list = []
            for name, info in list(self.global_var_cache.items())[:100]:  # 最多返回100个
                globals_list.append({
                    "name": name,
                    "type": info.get('type', 'variable'),
                    "file": info.get('file', '')
                })
            
            return {
                "count": len(self.global_var_cache),
                "globals": globals_list,
                "message": f"共有 {len(self.global_var_cache)} 个全局项（变量和宏），显示前100个"
            }
        
        except Exception as e:
            return {"error": str(e)}

