"""
AI客户端封装
提供统一的AI调用接口，支持流式响应和JSON解析
"""
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Tuple
from openai import OpenAI
import httpx

# 导入统一的日志系统
from ....utils.concurrent_logger import (
    log_concurrent_debug as log_debug,
    log_concurrent_warning as log_warning,
    log_concurrent_error as log_error,
    log_concurrent_info as log_info
)

class AIClient:
    def __init__(self):
        """初始化AI客户端"""
        # 读取项目根目录的配置文件
        self.config = self._load_config()
        
        # 配置OpenAI客户端
        openai_config = self.config.get("openai", {})
        
        # 获取base_url和其他配置
        base_url = openai_config.get("base_url", "http://localhost:11434/v1")
        api_key = openai_config.get("api_key", "sk-xxx")
        read_timeout = openai_config.get("read_timeout", 1200.0)
        
        # 检查是否需要绕过代理（针对国内AI服务商）
        # 支持的域名列表：阿里云、ModelScope、SiliconFlow、ApiFlow等
        bypass_proxy_domains = [
            'dashscope.aliyuncs.com',
            'api.dashscope.aliyuncs.com',
            'modelscope.cn',
            'api-inference.modelscope.cn',
            'siliconflow.cn',
            'api.siliconflow.cn',
            'apiflow.cc'
        ]
        
        http_client = None
        should_bypass_proxy = any(domain in base_url for domain in bypass_proxy_domains)
        
        if should_bypass_proxy:
            log_info(f"检测到国内AI服务商API，配置代理绕过 - base_url: {base_url}", "ai_client")
            # 设置环境变量绕过代理（添加所有支持的域名）
            no_proxy_list = ','.join(bypass_proxy_domains)
            os.environ['NO_PROXY'] = no_proxy_list
            os.environ['no_proxy'] = no_proxy_list
            log_info(f"已设置NO_PROXY环境变量: {no_proxy_list}", "ai_client")
            
            # 创建禁用代理的HTTP客户端
            # 注意：httpx 0.24.0+ 已移除 proxies 参数，使用环境变量 NO_PROXY 控制
            http_client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=openai_config.get("connect_timeout", 10.0),
                    read=read_timeout,
                    write=openai_config.get("write_timeout", 10.0),
                    pool=openai_config.get("pool_timeout", 1.0)
                )
            )
            log_info("已配置HTTP客户端绕过代理设置", "ai_client")
        
        # 初始化OpenAI客户端
        client_kwargs = {
            "api_key": api_key,
            "base_url": base_url,
            "timeout": read_timeout
        }
        
        if http_client:
            client_kwargs["http_client"] = http_client
            
        self.client = OpenAI(**client_kwargs)
        
        # 获取模型参数
        self.model_params = self.config.get("model_params", {})
        self.default_model = openai_config.get("model_name", "qwen2.5-coder:7b")
        
        log_info(f"AI客户端初始化完成 - 模型: {self.default_model}, base_url: {base_url}", "ai_client")
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 获取项目根目录的config.json路径
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent.parent.parent  # 回到项目根目录
            config_path = project_root / "config.json"
            
            log_info(f"尝试加载配置文件: {config_path}", "ai_client")
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    log_info(f"配置文件加载成功", "ai_client")
                    return config
            else:
                log_warning(f"配置文件不存在: {config_path}", "ai_client")
                return {}
        except Exception as e:
            log_error(f"加载配置文件失败", "ai_client", e)
            return {}
        
    def call_ai_stream(self, prompt: str, model: str = None) -> Tuple[Dict[str, Any], str]:
        """
        调用AI进行流式分析
        
        Args:
            prompt: 提示词
            model: 使用的模型名称
            
        Returns:
            Tuple[Dict[str, Any], str]: (解析后的JSON结果, 原始响应内容)
        """
        # 导入性能分析器
        from ....utils.performance_analyzer import performance_analyzer
        
        # 使用配置文件中的模型名称
        if model is None:
            model = self.default_model
        
        try:
            with performance_analyzer.measure_step("AI调用-创建请求") as request_step:
                # 调用OpenAI API进行流式响应
                request_step.add_metadata("model", model)
                request_step.add_metadata("prompt_length", len(prompt))
                
                log_info(f"准备调用AI模型: {model}, base_url: {self.client.base_url}", "ai_client")
                
                # 记录原始请求内容
                log_info("=" * 80, "ai_client")
                log_info("[AI原始请求 - 开始]", "ai_client")
                log_info(f"模型: {model}", "ai_client")
                log_info(f"Temperature: {self.model_params.get('temperature', 0.1)}", "ai_client")
                max_tokens_display = self.model_params.get('max_tokens', None)
                if max_tokens_display is None or max_tokens_display <= 0:
                    log_info(f"Max Tokens: 无限制（使用模型默认）", "ai_client")
                else:
                    log_info(f"Max Tokens: {max_tokens_display}", "ai_client")
                log_info("-" * 80, "ai_client")
                log_info("提示词内容:", "ai_client")
                log_info(prompt, "ai_client")
                log_info("[AI原始请求 - 结束]", "ai_client")
                log_info("=" * 80, "ai_client")
                
                # 构建API调用参数
                api_params = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "temperature": self.model_params.get("temperature", 0.1)
                }
                
                # 只有当 max_tokens 是正数时才添加限制
                max_tokens = self.model_params.get("max_tokens", None)
                if max_tokens is not None and max_tokens > 0:
                    api_params["max_tokens"] = max_tokens
                    log_info(f"使用 max_tokens 限制: {max_tokens}", "ai_client")
                else:
                    log_info("不限制 max_tokens（使用模型默认）", "ai_client")
                
                stream = self.client.chat.completions.create(**api_params)
            
            with performance_analyzer.measure_step("AI调用-流式响应处理") as stream_step:
                # 收集流式响应内容
                complete_content = ""
                chunk_count = 0
                for chunk in stream:
                    chunk_count += 1
                    if chunk.choices[0].delta.content is not None:
                        delta_content = chunk.choices[0].delta.content
                        complete_content += delta_content
                        # 移除实时打印，改为日志记录
                        # print(delta_content, end="", flush=True)
                
                stream_step.add_metadata("chunk_count", chunk_count)
                stream_step.add_metadata("response_length", len(complete_content))
                
                log_debug(f"AI响应内容长度: {len(complete_content)} 字符", "ai_client")
                
                # 记录原始响应内容
                log_info("=" * 80, "ai_client")
                log_info("[AI原始响应 - 开始]", "ai_client")
                log_info(f"响应长度: {len(complete_content)} 字符", "ai_client")
                log_info(f"接收块数: {chunk_count}", "ai_client")
                log_info("-" * 80, "ai_client")
                log_info("响应内容:", "ai_client")
                log_info(complete_content, "ai_client")
                log_info("[AI原始响应 - 结束]", "ai_client")
                log_info("=" * 80, "ai_client")
            
            with performance_analyzer.measure_step("AI调用-响应解析"):
                # 解析JSON响应
                result = self._process_model_response(complete_content)
                return result, complete_content
            
        except Exception as e:
            log_error(f"调用AI时出错", "ai_client", e)
            return {"error": f"AI调用失败: {str(e)}", "problems": []}, ""
    
    def _process_model_response(self, content: str) -> Dict[str, Any]:
        """
        处理模型响应内容，提取JSON格式的结果
        
        Args:
            content: 模型原始响应内容
            
        Returns:
            Dict[str, Any]: 解析后的结果
        """
        try:
            # 使用改进的JSON清理方法
            cleaned_content = self._clean_json_string(content)
            log_debug(f"JSON清理完成，长度: {len(cleaned_content)}", "ai_client")
            
            # 尝试解析JSON
            try:
                result = json.loads(cleaned_content)
                log_debug("JSON解析成功", "ai_client")
            except json.JSONDecodeError as e:
                log_warning(f"JSON解析失败，尝试备用修复: {str(e)}", "ai_client")
                # 使用备用的修复方法
                result = self._try_fix_json(cleaned_content)
            
            # 验证结果格式
            if not isinstance(result, dict):
                log_warning(f"AI返回的不是字典格式: {type(result)}", "ai_client")
                return {"error": "返回格式不正确", "problems": []}
            
            # 确保包含problems字段
            if "problems" not in result:
                result["problems"] = []
                log_debug("添加缺失的problems字段", "ai_client")
            
            # 验证function_info字段
            function_info = result.get("function_info", {})
            if function_info:
                if not isinstance(function_info, dict):
                    log_warning(f"function_info不是字典格式: {type(function_info)}", "ai_client")
                    result["function_info"] = {}
                elif not function_info.get("function_description") and not function_info.get("commented_code"):
                    log_warning("function_info内容为空", "ai_client")
            else:
                # 如果没有function_info字段，添加空字典
                result["function_info"] = {}
                log_debug("AI响应中缺少function_info字段，已添加空字典", "ai_client")
            
            return result
            
        except Exception as e:
            error_msg = f"处理AI响应时出错: {str(e)}"
            log_error(error_msg, "ai_client", e)
            log_debug(f"原始内容: {content[:500]}...", "ai_client")
            return {"error": error_msg, "problems": []}
    
    def _clean_json_string(self, json_str):
        """
        清理JSON字符串，处理常见的格式问题
        
        Args:
            json_str: 原始JSON字符串
            
        Returns:
            str: 清理后的JSON字符串
        """
        # 1. Handle <think>...</think> or leading </think>
        last_think_end_tag_index = json_str.rfind("</think>")
        if last_think_end_tag_index != -1:
            json_str = json_str[last_think_end_tag_index + len("</think>"):]
            json_str = json_str.lstrip()
        
        # 2. 移除 BOM 标记
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
        
        # 3. 处理 Markdown 代码块标记
        json_str = ''.join(
            char for char in json_str 
            if char == '\n' or char == '\t' or not (0 <= ord(char) < 32 or ord(char) == 127)
        )
        
        # 4. 提取JSON内容 - 改进版本，处理完整的JSON对象
        # 首先检查是否有Markdown代码块标记
        if "```json" in json_str:
            start_marker = "```json"
            end_marker = "```"
            start_pos = json_str.find(start_marker) + len(start_marker)
            end_pos = json_str.find(end_marker, start_pos)
            if end_pos > start_pos:
                json_str = json_str[start_pos:end_pos].strip()
        
        # 然后确保提取完整的JSON对象，而不是截断多问题的情况
        # 计算括号平衡，确保提取的是完整的JSON对象
        if '{' in json_str:
            start_idx = json_str.find('{')
            brace_count = 0
            end_idx = -1
            
            for i in range(start_idx, len(json_str)):
                if json_str[i] == '{':
                    brace_count += 1
                elif json_str[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if end_idx > start_idx:
                json_str = json_str[start_idx:end_idx + 1]
        
        # 修复JSON字符串中的常见问题
        import re
        
        # 首先尝试直接解析
        try:
            json.loads(json_str)
            return json_str  # 如果成功，直接返回
        except json.JSONDecodeError:
            pass  # 如果失败，继续进行修复
        
        # 使用更简单直接的方法：直接修复常见的引号问题
        # 最常见的问题是source_code字段中的 "^" 没有被转义
        
        # 1. 修复 addToHistory 调用中的引号问题
        json_str = json_str.replace('"^"', '\\"^\\"')
        json_str = json_str.replace('"+"', '\\"+\\"')
        json_str = json_str.replace('"-"', '\\"-\\"')
        json_str = json_str.replace('"*"', '\\"*\\"')
        json_str = json_str.replace('"/"', '\\"/\\"')
        
        # 2. 修复其他常见的未转义引号
        json_str = json_str.replace('throw std::runtime_error("Division by zero")', 'throw std::runtime_error(\\"Division by zero\\")')
        json_str = json_str.replace('std::cout << "', 'std::cout << \\"')
        json_str = json_str.replace('" << std', '\\" << std')
        
        # 3. 在最终解析前，修复Windows路径中的反斜杠问题
        # 但要小心不要破坏已经修复的引号转义
        if '\\' in json_str and '\\\\' not in json_str:
            # 检测到单反斜杠但没有双反斜杠，可能是Windows路径
            # 但先检查是否已经有转义的引号
            if '\\"' not in json_str:
                json_str = json_str.replace('\\', '\\\\')
            else:
                # 如果已经有转义的引号，只转义非引号相关的反斜杠
                import re
                # 只转义不在 \" 模式中的反斜杠
                json_str = re.sub(r'\\(?!")', r'\\\\', json_str)
        
        return json_str

    def _try_fix_json(self, content: str) -> Dict[str, Any]:
        """
        尝试修复常见的JSON格式问题
        
        Args:
            content: 原始内容
            
        Returns:
            Dict[str, Any]: 修复后的结果
        """
        try:
            # 尝试一些常见的修复方法
            fixes = [
                # 移除末尾可能的不完整内容
                lambda x: x.rsplit(',', 1)[0] + '}' if x.count('{') > x.count('}') else x,
                # 移除开头可能的额外内容
                lambda x: x[x.find('{'):] if '{' in x else x,
                # 移除结尾可能的额外内容  
                lambda x: x[:x.rfind('}')+1] if '}' in x else x,
            ]
            
            for fix_func in fixes:
                try:
                    fixed_content = fix_func(content)
                    result = json.loads(fixed_content)
                    log_debug("JSON修复成功", "ai_client")
                    return result
                except:
                    continue
            
            # 如果所有修复都失败，返回错误结果
            log_error("所有JSON修复尝试都失败", "ai_client")
            return {"error": "JSON格式无法修复", "problems": []}
            
        except Exception as e:
            log_error("JSON修复过程中出错", "ai_client", e)
            return {"error": f"JSON修复失败: {str(e)}", "problems": []}
    
    def call_ai_with_tools(
        self, 
        messages: list, 
        tools: list,
        tool_choice: str = "auto",
        model: str = None
    ) -> Dict[str, Any]:
        """
        调用AI并支持工具调用（Function Calling）
        
        Args:
            messages: 消息历史列表
            tools: 工具定义列表
            tool_choice: 工具选择策略（"auto", "none", 或指定工具）
            model: 使用的模型名称
            
        Returns:
            Dict[str, Any]: AI响应
        """
        try:
            if not model:
                model = self.default_model
            
            # 准备API调用参数
            api_params = {
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": tool_choice,
            }
            
            # 添加模型参数
            api_params.update(self.model_params)
            
            log_debug(f"调用AI模型（带工具）: {model}", "ai_client")
            log_debug(f"工具数量: {len(tools)}", "ai_client")
            
            # 记录原始请求内容
            log_info("=" * 80, "ai_client")
            log_info("[AI原始请求（带工具）- 开始]", "ai_client")
            log_info(f"模型: {model}", "ai_client")
            log_info(f"工具数量: {len(tools)}", "ai_client")
            log_info(f"Tool Choice: {tool_choice}", "ai_client")
            log_info("-" * 80, "ai_client")
            log_info("消息历史:", "ai_client")
            for i, msg in enumerate(messages):
                log_info(f"  消息 {i+1} ({msg.get('role', 'unknown')}): {msg.get('content', '<no content>')[:200]}...", "ai_client")
            log_info("-" * 80, "ai_client")
            log_info("可用工具:", "ai_client")
            for tool in tools:
                log_info(f"  - {tool.get('function', {}).get('name', 'unnamed')}", "ai_client")
            log_info("[AI原始请求（带工具）- 结束]", "ai_client")
            log_info("=" * 80, "ai_client")
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(**api_params)
            
            # 解析响应
            message = response.choices[0].message
            
            result = {
                "message": {
                    "role": message.role,
                    "content": message.content,
                    "tool_calls": []
                }
            }
            
            # 处理工具调用
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result["message"]["tool_calls"].append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
            
            log_debug(f"AI响应: content={message.content}, tool_calls={len(result['message']['tool_calls'])}", "ai_client")
            
            # 记录原始响应内容
            log_info("=" * 80, "ai_client")
            log_info("[AI原始响应（带工具）- 开始]", "ai_client")
            log_info(f"Role: {message.role}", "ai_client")
            log_info(f"工具调用数量: {len(result['message']['tool_calls'])}", "ai_client")
            log_info("-" * 80, "ai_client")
            log_info("响应内容:", "ai_client")
            log_info(message.content if message.content else "<无文本内容>", "ai_client")
            if result["message"]["tool_calls"]:
                log_info("-" * 80, "ai_client")
                log_info("工具调用:", "ai_client")
                for tc in result["message"]["tool_calls"]:
                    log_info(f"  工具: {tc['function']['name']}", "ai_client")
                    log_info(f"  参数: {tc['function']['arguments']}", "ai_client")
            log_info("[AI原始响应（带工具）- 结束]", "ai_client")
            log_info("=" * 80, "ai_client")
            
            return result
            
        except Exception as e:
            error_msg = f"调用AI（带工具）时出错: {str(e)}"
            log_error(error_msg, "ai_client", e)
            return {
                "error": error_msg,
                "message": {
                    "role": "assistant",
                    "content": f"调用失败: {str(e)}",
                    "tool_calls": []
                }
            }