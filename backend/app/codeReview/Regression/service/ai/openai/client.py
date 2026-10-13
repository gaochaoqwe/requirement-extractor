"""
OpenAI API Client for Code Review
"""
import os
import json
import uuid
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError, APITimeoutError
from app.codeReview.Regression.service.ai import log_debug
import sys

# 加载全局配置
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent  # 定位到backend目录
CONFIG_PATH = PROJECT_ROOT / "app" / "config.json"  # 指向backend/app/config.json
with open(CONFIG_PATH, encoding="utf-8") as f:
    _config_data = json.load(f)

# 从config.json获取OpenAI配置
OPENAI_CONFIG = _config_data.get("openai", {})
OPENAI_API_KEY = OPENAI_CONFIG.get("api_key", "")
OPENAI_BASE_URL = OPENAI_CONFIG.get("base_url", "https://api.openai.com/v1")
OPENAI_MODEL_NAME = OPENAI_CONFIG.get("model_name", "gpt-3.5-turbo")
CONNECT_TIMEOUT = OPENAI_CONFIG.get("connect_timeout", 10.0)
READ_TIMEOUT = OPENAI_CONFIG.get("read_timeout", 180.0)
WRITE_TIMEOUT = OPENAI_CONFIG.get("write_timeout", 60.0)
POOL_TIMEOUT = OPENAI_CONFIG.get("pool_timeout", 60.0)

class AIClient:
    def __init__(self, ai_model: str = None):
        # 优先使用config.json中的模型名称
        self.ai_model = ai_model or OPENAI_MODEL_NAME
        
        # 从config.json设置超时值
        self.timeout = httpx.Timeout(
            connect=CONNECT_TIMEOUT,
            read=READ_TIMEOUT,
            write=WRITE_TIMEOUT,
            pool=POOL_TIMEOUT
        )
        
        # 从config.json获取API密钥和基础URL
        self.api_key = OPENAI_API_KEY
        self.base_url = OPENAI_BASE_URL
        
        # 确保base_url格式正确
        if self.base_url.endswith('/'):
            self.base_url = self.base_url.rstrip('/')
        if not self.base_url.endswith('/v1'):
            self.base_url = f"{self.base_url}/v1"

        # 针对 hyperbolic.xyz 域名绕过代理
        self.http_client = None
        try:
            if "hyperbolic.xyz" in self.base_url:
                log_debug(f"检测到Hyperbolic API，配置代理绕过 - base_url: {self.base_url}")
                # 设置环境变量绕过代理
                os.environ['NO_PROXY'] = 'api.hyperbolic.xyz,hyperbolic.xyz'
                os.environ['no_proxy'] = 'api.hyperbolic.xyz,hyperbolic.xyz'

                # 创建禁用代理的HTTP客户端
                self.http_client = httpx.Client(
                    proxies={},  # 禁用所有代理
                    timeout=httpx.Timeout(
                        connect=CONNECT_TIMEOUT,
                        read=READ_TIMEOUT,
                        write=WRITE_TIMEOUT,
                        pool=POOL_TIMEOUT
                    )
                )
                log_debug("已配置HTTP客户端绕过代理设置")
        except Exception as _e:
            log_debug(f"配置超参数HTTP客户端时发生异常: {_e}")

    def get_client(self) -> OpenAI:
        """获取OpenAI客户端实例"""
        kwargs = dict(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )
        # 若为 hyperbolic 域，传入禁用代理的 http_client
        if self.http_client is not None:
            kwargs["http_client"] = self.http_client
        return OpenAI(**kwargs)

    def call_ai_stream(self, prompt: str) -> Dict[str, Any]:
        """
        使用流式输出调用AI接口进行分析
        
        Args:
            prompt: 提示词
            
        Returns:
            Dict[str, Any]: AI分析结果
        """
        client = self.get_client()
        call_id = str(uuid.uuid4())[:8]
        
        # 将完整请求保存到文件以便调试
        debug_dir = PROJECT_ROOT / "logs" / "openai_debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 构建请求参数
            request_params = {
                "model": self.ai_model,
                "messages": [
                    {"role": "system", "content": "You are a static analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 8192,
                "stream": True
            }
            
            # 记录完整的请求参数到调试日志
            try:
                # 记录请求概要
                log_debug(f"[OpenAI Request {call_id}] Model: {self.ai_model}, Temperature: 0.1, Max Tokens: 8192")
                log_debug(f"[OpenAI Request {call_id}] Prompt Length: {len(prompt)} characters")
                log_debug(f"[OpenAI Request {call_id}] Base URL: {self.base_url}")
                
                # 记录完整的原始请求信息到主日志（不省略任何内容）
                log_debug(f"[OpenAI Request {call_id}] === COMPLETE REQUEST START ===")
                log_debug(f"[OpenAI Request {call_id}] Model: {request_params['model']}")
                log_debug(f"[OpenAI Request {call_id}] Temperature: {request_params['temperature']}")
                log_debug(f"[OpenAI Request {call_id}] Max Tokens: {request_params['max_tokens']}")
                log_debug(f"[OpenAI Request {call_id}] Stream: {request_params['stream']}")
                log_debug(f"[OpenAI Request {call_id}] Messages Count: {len(request_params['messages'])}")
                
                for i, msg in enumerate(request_params['messages']):
                    log_debug(f"[OpenAI Request {call_id}] Message {i+1} Role: {msg['role']}")
                    log_debug(f"[OpenAI Request {call_id}] Message {i+1} Content: {msg['content']}")
                
                log_debug(f"[OpenAI Request {call_id}] === COMPLETE REQUEST END ===")
                
                # 保存到文件
                request_file = debug_dir / f"request_{call_id}.json"
                with open(request_file, 'w', encoding='utf-8') as f:
                    json.dump(request_params, f, ensure_ascii=False, indent=2)
                
                log_debug(f"[OpenAI Request {call_id}] Complete request saved to: {request_file}")
                    
            except Exception as e:
                log_debug(f"[OpenAI Request {call_id}] Failed to log request: {e}")
            
            # 使用流式输出
            log_debug(f"[OpenAI Request {call_id}] Starting stream request...")
            stream = client.chat.completions.create(**request_params)
            
            full_content_parts: List[str] = []
            
            # 处理流式响应
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    delta_content = chunk.choices[0].delta.content
                    full_content_parts.append(delta_content)
                    # 不在这里输出流式内容，由调用者决定是否需要
                    # sys.stderr.write(delta_content)
            
            # 合并完整内容
            complete_content = "".join(full_content_parts)
            
            # 记录完整的响应内容到调试日志
            try:
                log_debug(f"[OpenAI Response {call_id}] Content Length: {len(complete_content)} characters")
                
                # 记录完整的原始响应信息到主日志（不省略任何内容）
                log_debug(f"[OpenAI Response {call_id}] === COMPLETE RESPONSE START ===")
                log_debug(f"[OpenAI Response {call_id}] Raw Response Content:")
                log_debug(f"[OpenAI Response {call_id}] {complete_content}")
                log_debug(f"[OpenAI Response {call_id}] === COMPLETE RESPONSE END ===")
                
                # 将完整响应保存到文件以便调试
                response_file = debug_dir / f"response_{call_id}.txt"
                with open(response_file, 'w', encoding='utf-8') as f:
                    f.write(complete_content)
                
                log_debug(f"[OpenAI Response {call_id}] Complete response saved to: {response_file}")
                    
            except Exception as e:
                log_debug(f"[OpenAI Response {call_id}] Failed to log response: {e}")
            
            def _clean_json_string(json_str):
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
            
            # 清理并解析JSON
            try:
                cleaned_content = _clean_json_string(complete_content)
                log_debug(f"[OpenAI Response {call_id}] JSON cleaning completed, length: {len(cleaned_content)}")
                
                # 保存清理后的JSON以便调试
                try:
                    cleaned_file = debug_dir / f"cleaned_{call_id}.json"
                    with open(cleaned_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    log_debug(f"[OpenAI Response {call_id}] Cleaned JSON saved to: {cleaned_file}")
                except Exception as e:
                    log_debug(f"[OpenAI Response {call_id}] Failed to save cleaned JSON: {e}")
                
                result = json.loads(cleaned_content)
                log_debug(f"[OpenAI Response {call_id}] JSON parsing successful")
                return result, call_id
                
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: {str(e)}"
                log_debug(f"[OpenAI Response {call_id}] {error_msg}")
                log_debug(f"[OpenAI Response {call_id}] 原始内容: {complete_content}")
                log_debug(f"[OpenAI Response {call_id}] 清理后内容: {cleaned_content}")
                sys.stderr.write(f"\n[错误] {error_msg}\n")
                
                # 保存失败的内容以便调试
                try:
                    error_file = debug_dir / f"error_{call_id}.txt"
                    with open(error_file, 'w', encoding='utf-8') as f:
                        f.write(f"Error: {error_msg}\n\n")
                        f.write(f"Original content ({len(complete_content)} chars):\n{complete_content}\n\n")
                        f.write(f"Cleaned content ({len(cleaned_content)} chars):\n{cleaned_content}\n\n")
                        f.write(f"JSON Error Details: {str(e)}")
                    log_debug(f"[OpenAI Response {call_id}] Error details saved to: {error_file}")
                except Exception as save_error:
                    log_debug(f"[OpenAI Response {call_id}] Failed to save error details: {save_error}")
                
                # 返回更详细的错误信息，包含原始内容用于调试
                return {
                    "problems": [], 
                    "error": error_msg, 
                    "raw_content": complete_content,
                    "cleaned_content": cleaned_content,
                    "json_error": str(e)
                }, call_id
            
        except (APIConnectionError, RateLimitError, APIStatusError, APITimeoutError) as e:
            error_msg = f"OpenAI API错误: {str(e)}"
            log_debug(f"[OpenAI Request {call_id}] API Error: {error_msg}")
            sys.stderr.write(f"\n[错误] {error_msg}\n")
            return {"problems": [], "error": error_msg}, call_id
