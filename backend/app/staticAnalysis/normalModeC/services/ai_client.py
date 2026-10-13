"""
OpenAI API Client for Static Analysis
"""
import os
import json
import uuid
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError, APITimeoutError

# 加载全局配置：services -> normalModeC -> staticAnalysis -> app
APP_DIR = Path(__file__).resolve().parents[3]
CONFIG_PATH = APP_DIR / "config.json"
PROJECT_ROOT = APP_DIR.parent

# print(f"[配置文件路径] 尝试加载: {CONFIG_PATH}")

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "sk-dummy-key-for-testing",
    "base_url": "https://api.openai.com/v1",
    "model_name": "gpt-3.5-turbo",
    "connect_timeout": 10.0,
    "read_timeout": 180.0,
    "write_timeout": 60.0,
    "pool_timeout": 60.0
}

# 尝试加载配置文件
OPENAI_CONFIG = {}
try:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config_data = json.load(f)
            OPENAI_CONFIG = config_data.get("openai", {})
    else:
        # print(f"[警告] 配置文件不存在: {CONFIG_PATH}，使用默认配置")
        OPENAI_CONFIG = DEFAULT_CONFIG
except Exception as e:
            # print(f"[错误] 加载配置文件失败: {str(e)}，使用默认配置")
    OPENAI_CONFIG = DEFAULT_CONFIG

# 从配置获取OpenAI设置，如果不存在则使用默认值
OPENAI_API_KEY = OPENAI_CONFIG.get("api_key", DEFAULT_CONFIG["api_key"])
OPENAI_BASE_URL = OPENAI_CONFIG.get("base_url", DEFAULT_CONFIG["base_url"])
OPENAI_MODEL_NAME = OPENAI_CONFIG.get("model_name", DEFAULT_CONFIG["model_name"])
CONNECT_TIMEOUT = OPENAI_CONFIG.get("connect_timeout", DEFAULT_CONFIG["connect_timeout"])
READ_TIMEOUT = OPENAI_CONFIG.get("read_timeout", DEFAULT_CONFIG["read_timeout"])
WRITE_TIMEOUT = OPENAI_CONFIG.get("write_timeout", DEFAULT_CONFIG["write_timeout"])
POOL_TIMEOUT = OPENAI_CONFIG.get("pool_timeout", DEFAULT_CONFIG["pool_timeout"])

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

    def get_client(self) -> OpenAI:
        """获取OpenAI客户端实例"""
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

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
        
        # 打印API请求配置信息
        # 调试信息已注释以减少输出
        # print(f"\n[API配置信息] ============================")
        # print(f"模型名称: {self.ai_model}")
        # print(f"API基础URL: {self.base_url}")
        # print(f"API密钥前5位: {self.api_key[:5]}...")
        # print(f"超时设置: {self.timeout}")
        # print(f"请求ID: {call_id}")
        # print(f"提示词长度: {len(prompt)} 字符")
        # print(f"======================================\n")
        
        # 检查是否使用测试密钥
        if self.api_key == "sk-dummy-key-for-testing":
            # print("[警告] 使用测试密钥，返回模拟数据")
            # 返回模拟数据
            return {
                "problems": [
                    {
                        "file_name": "example.c",
                        "source_code": prompt[:100] + "...",  # 截取部分提示词作为源代码
                        "violation_rules": "模拟规则违反",
                        "issue_name": "模拟问题",
                        "issue_location": "example.c:main",
                        "description_requirement": "这是一个模拟的需求描述。",
                        "description_issue": "这是一个模拟的问题描述。",
                        "description_location": "这是一个模拟的问题位置。",
                        "description_impact": "这是一个模拟的影响分析。"
                    }
                ]
            }, call_id
        
        try:
            # print(f"[AI分析] 开始分析... (ID: {call_id})")
            
            # 构建请求参数
            request_params = {
                "model": self.ai_model,
                "messages": [
                    {"role": "system", "content": "You are a static code analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 8192,
                "stream": True
            }
            
            # 打印完整请求参数
            # print(f"[请求参数] {json.dumps(request_params, ensure_ascii=False, default=str)}")
            
            # 使用流式输出
            stream = client.chat.completions.create(**request_params)
            
            full_content_parts: List[str] = []
            
            # 处理流式响应
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    delta_content = chunk.choices[0].delta.content
                    full_content_parts.append(delta_content)
                    # print(delta_content, end="", flush=True)  # 实时打印流式内容
            
            # 合并完整内容
            complete_content = "".join(full_content_parts)
            # print("\n[AI分析] 分析完成")
            
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
                
                # 在最终解析前，修复Windows路径中的反斜杠问题
                if '\\' in json_str and '\\\\' not in json_str:
                    # 检测到单反斜杠但没有双反斜杠，可能是Windows路径
                    json_str = json_str.replace('\\', '\\\\')
                
                # 处理源代码中的控制字符
                import re
                
                def replace_source_code(match):
                    source_code = match.group(1)
                    # 将源代码中的换行符和缩进替换为转义字符
                    source_code = source_code.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    return f'"source_code": "{source_code}"'
                
                # 替换source_code字段中的内容
                json_str = re.sub(r'"source_code"\s*:\s*"([^"]*)"', replace_source_code, json_str)
                
                return json_str
            
            # 清理并解析JSON
            try:
                cleaned_content = _clean_json_string(complete_content)
                result = json.loads(cleaned_content)
                
                # 记录成功解析的结果
                print(f"\n[AI客户端] JSON解析成功 (ID: {call_id})")
                problems_count = len(result.get("problems", []))
                if problems_count > 0:
                    print(f"[AI客户端] 发现 {problems_count} 个问题")
                else:
                    print(f"[AI客户端] 未发现问题")
                
                return result, call_id
            except json.JSONDecodeError as e:
                print(f"\n[错误] JSON解析失败 (ID: {call_id}): {str(e)}")
                print(f"[错误] 清理后的内容: {cleaned_content[:500]}...")
                print(f"[错误] 原始AI返回内容: {complete_content[:500]}...")
                
                # 尝试从原始内容中提取问题信息
                raw_problems_found = self._try_extract_problems_from_raw(complete_content)
                if raw_problems_found:
                    print(f"[警告] 从原始内容中提取到 {len(raw_problems_found)} 个潜在问题，但JSON格式有误")
                
                # 在解析失败时，返回一个空的问题列表和原始内容
                return {
                    "problems": [], 
                    "error": f"JSON解析失败: {str(e)}", 
                    "raw": complete_content,
                    "cleaned": cleaned_content,
                    "potential_problems_found": raw_problems_found is not None
                }, call_id
            
        except (APIConnectionError, RateLimitError, APIStatusError, APITimeoutError) as e:
            error_msg = f"OpenAI API错误: {str(e)}"
            print(f"\n[错误] {error_msg}")
            return {"problems": [], "error": error_msg}, call_id
        except Exception as e:
            error_msg = f"未预期的错误: {str(e)}"
            print(f"\n[错误] {error_msg}")
            import traceback
            print(traceback.format_exc())
            return {"problems": [], "error": error_msg}, call_id

    def _try_extract_problems_from_raw(self, raw_content: str) -> bool:
        """
        尝试从原始AI返回内容中检测是否包含问题信息
        即使JSON解析失败也能知道AI是否发现了问题
        
        Args:
            raw_content: 原始AI返回内容
            
        Returns:
            bool: 如果检测到可能包含问题信息则返回True
        """
        # 常见的问题指示词
        problem_indicators = [
            "issue_name",
            "issue_level", 
            "violation_rules",
            "description_issue",
            "违反",
            "问题",
            "错误",
            "警告",
            "CRITICAL",
            "MAJOR",
            "MINOR",
            "WARNING"
        ]
        
        # 转换为小写进行检查
        content_lower = raw_content.lower()
        
        # 检查是否包含问题相关的关键词
        for indicator in problem_indicators:
            if indicator.lower() in content_lower:
                return True
        
        return False
