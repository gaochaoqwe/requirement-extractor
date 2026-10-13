"""
Agent执行器：实现ReAct (Reasoning + Acting) 模式的Agent主循环
"""
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from .agent_tools import AgentTools


class AgentExecutor:
    """Agent执行器，管理Agent的思考和行动循环"""
    
    def __init__(
        self,
        tools: AgentTools,
        ai_client,
        max_iterations: int = 10,
        max_tokens_per_message: int = 3000
    ):
        """
        初始化Agent执行器
        
        Args:
            tools: Agent工具集实例
            ai_client: AI客户端
            max_iterations: 最大迭代次数
            max_tokens_per_message: 每条消息的最大token数（粗略估计）
        """
        self.tools = tools
        self.ai_client = ai_client
        self.max_iterations = max_iterations
        self.max_tokens_per_message = max_tokens_per_message
        
        # 工具名到方法的映射
        self.tool_map = {
            "list_directory": self.tools.list_directory,
            "search_function_by_name": self.tools.search_function_by_name,
            "search_function_in_file": self.tools.search_function_in_file,
            "get_file_outline": self.tools.get_file_outline,
            "read_file_range": self.tools.read_file_range,
            "get_function_context": self.tools.get_function_context,
            "get_variable_usage": self.tools.get_variable_usage,
            "get_call_graph": self.tools.get_call_graph,
            "search_code": self.tools.search_code,
            "get_dependency_function": self.tools.get_dependency_function,
            "get_global_variable": self.tools.get_global_variable,
            "search_function_calls": self.tools.search_function_calls,
            "list_all_globals": self.tools.list_all_globals,
        }
    
    def execute(
        self,
        system_prompt: str,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行Agent任务
        
        Args:
            system_prompt: 系统提示词
            user_query: 用户查询
            context: 额外上下文信息
            
        Returns:
            执行结果
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        # 如果有上下文，添加到用户消息中
        if context:
            context_str = "\n\n【额外上下文】\n" + json.dumps(context, ensure_ascii=False, indent=2)
            messages[-1]["content"] += context_str
        
        iteration = 0
        tool_calls_history = []
        final_result = None
        max_context_chars = 60000
        
        while True:
            iteration += 1
            print(f"\n=== Agent迭代 {iteration} ===")
            
            try:
                # 调用AI模型
                response = self.ai_client.call_ai_with_tools(
                    messages=messages,
                    tools=AgentTools.get_tool_definitions(),
                    tool_choice="auto"
                )
                
                # 检查响应类型
                if not response:
                    final_result = {
                        "success": False,
                        "error": "AI模型返回空响应",
                        "tool_calls_history": tool_calls_history
                    }
                    break
                
                # 获取AI的响应消息
                assistant_message = response.get("message", {})
                
                # 检查是否需要调用工具
                tool_calls = assistant_message.get("tool_calls", [])
                
                if not tool_calls:
                    # 没有工具调用，说明AI已经得出结论
                    content = assistant_message.get("content", "")
                    
                    # 尝试解析JSON响应
                    try:
                        # 提取JSON内容（可能在```json ```标记中）
                        json_content = self._extract_json(content)
                        if json_content:
                            final_result = {
                                "success": True,
                                "result": json.loads(json_content),
                                "tool_calls_history": tool_calls_history,
                                "iterations": iteration
                            }
                        else:
                            final_result = {
                                "success": True,
                                "result": {"text": content},
                                "tool_calls_history": tool_calls_history,
                                "iterations": iteration
                            }
                    except json.JSONDecodeError:
                        final_result = {
                            "success": True,
                            "result": {"text": content},
                            "tool_calls_history": tool_calls_history,
                            "iterations": iteration
                        }
                    break
                
                # 有工具调用，执行工具
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.get("content"),
                    "tool_calls": tool_calls
                })
                
                # 执行每个工具调用
                for tool_call in tool_calls:
                    tool_name = tool_call.get("function", {}).get("name")
                    tool_args_str = tool_call.get("function", {}).get("arguments", "{}")
                    tool_id = tool_call.get("id")
                    
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    print(f"  工具调用: {tool_name}({tool_args})")
                    
                    # 执行工具
                    tool_result = self._execute_tool(tool_name, tool_args)
                    
                    # 记录工具调用历史
                    tool_calls_history.append({
                        "iteration": iteration,
                        "tool": tool_name,
                        "args": tool_args,
                        "result": tool_result
                    })
                    
                    # 将工具结果添加到消息历史中
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                
                # 管理上下文长度（避免超过token限制）
                messages = self._manage_context(messages)
                
                total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
                if total_chars > max_context_chars:
                    print(f"  上下文长度达到 {total_chars} 字符，停止迭代")
                    final_result = {
                        "success": False,
                        "error": "上下文过长，无法继续审查",
                        "tool_calls_history": tool_calls_history,
                        "iterations": iteration
                    }
                    break
                
            except Exception as e:
                print(f"  Agent迭代异常: {e}")
                final_result = {
                    "success": False,
                    "error": f"Agent执行异常: {str(e)}",
                    "tool_calls_history": tool_calls_history,
                    "iterations": iteration
                }
                break
        
        if final_result is None:
            final_result = {
                "success": False,
                "error": "未能在上下文限制内完成任务",
                "tool_calls_history": tool_calls_history,
                "iterations": iteration
            }
        
        return final_result
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        tool_func = self.tool_map.get(tool_name)
        if not tool_func:
            return {"error": f"未知工具: {tool_name}"}
        
        try:
            result = tool_func(**tool_args)
            return result
        except Exception as e:
            return {"error": f"工具执行异常: {str(e)}"}
    
    def _extract_json(self, text: str) -> Optional[str]:
        """从文本中提取JSON内容"""
        # 尝试直接解析
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            return text
        
        # 尝试从```json ```标记中提取
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        
        # 尝试从```标记中提取
        if '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end != -1:
                content = text[start:end].strip()
                if content.startswith('{') and content.endswith('}'):
                    return content
        
        return None
    
    def _manage_context(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        管理上下文长度，避免超过token限制
        
        策略：
        1. 保留system消息和最初的user消息
        2. 保留最近N轮的对话和工具调用
        3. 对于较早的工具调用结果，进行总结或截断
        """
        # 粗略估计消息长度
        total_length = sum(len(str(msg.get("content", ""))) for msg in messages)
        
        # 如果消息总长度超过阈值，进行裁剪
        if total_length > 20000:  # 约20000字符，粗略对应20k tokens
            # 保留system和初始user消息
            kept_messages = messages[:2]
            
            # 保留最近5轮的消息
            recent_messages = messages[-10:]  # 每轮约2条消息（assistant + tool）
            
            # 合并
            kept_messages.extend(recent_messages)
            
            print(f"  上下文管理: 从{len(messages)}条消息裁剪到{len(kept_messages)}条")
            return kept_messages
        
        return messages
    
    def _summarize_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """总结工具调用结果"""
        summary_parts = []
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            tool_result = result.get("result", {})
            
            if "error" in tool_result:
                summary_parts.append(f"- {tool_name}: 失败 ({tool_result['error']})")
            elif tool_name == "list_directory":
                content = tool_result.get("content", [])
                summary_parts.append(f"- {tool_name}: 找到{len(content)}个项目")
            elif tool_name == "search_function_by_name":
                count = tool_result.get("count", 0)
                summary_parts.append(f"- {tool_name}: 找到{count}个函数")
            else:
                summary_parts.append(f"- {tool_name}: 成功")
        
        return "\n".join(summary_parts)

