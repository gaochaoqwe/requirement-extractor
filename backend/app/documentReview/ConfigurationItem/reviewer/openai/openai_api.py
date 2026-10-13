"""
负责调用AI模型的模块
"""
import os
import sys
import uuid
import json
import re
import logging
import traceback
import httpx
import openai
from openai import OpenAI, APIConnectionError, RateLimitError, APIStatusError, APITimeoutError
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.completion_usage import CompletionUsage
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, AsyncGenerator, Iterator # Re-add typing imports
from pathlib import Path
from app.utils.log_utils import log_once, log_with_interval, setup_logger
import time

def setup_debug_logger():
    """设置调试日志记录器"""
    # 确保日志目录存在
    log_dir = Path(__file__).parent.parent.parent.parent.parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / 'ai_reviewer_debug.log'
    
    # 创建记录器，使用更具体的名称避免冲突
    logger = logging.getLogger('ai_reviewer.config_item')
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建详细的格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器到logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logger.info(f"AI Reviewer 配置项调试日志已启用，日志文件: {log_file}")
    
    return logger

# 设置调试日志记录器
logger = setup_debug_logger()

# 处理 jiter 库缺失的情况（Win7兼容性）
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError as e:
    if 'jiter' in str(e):
        # jiter 库缺失，这在某些系统如 Win7 可能发生
        sys.stderr.write("警告: OpenAI 库依赖的 jiter 模块缺失，将使用替代方案\n")
        HAS_OPENAI = False
    else:
        # 其他导入错误，重新抛出
        raise

# 使用全局日志配置函数创建日志器
log_dir = os.path.join(os.path.dirname(__file__), '../../../../logs')
log_file = os.path.join(log_dir, 'config_item_openai_api.log')
logger = setup_logger("wordllm", log_file, logging.DEBUG)

def load_openai_config():
    """从 config.json 加载 OpenAI 配置"""
    config_path = os.path.join(os.path.dirname(__file__), '../../../../config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取 OpenAI 配置
        openai_config = config.get('openai', {})
        model_params = config.get('model_params', {})
        
        # 确保 base_url 格式正确
        base_url = openai_config.get('base_url', 'https://api.openai.com/v1')
        
        # 判断是否是Ollama地址格式（如"192.168.202.1:11434"）
        if ':' in base_url and not base_url.startswith('http'):
            # 无协议前缀的IP:PORT格式，添加http://
            base_url = f"http://{base_url}"
            logger.info(f"Ollama地址格式检测: 添加http://前缀 -> {base_url}")
        
        # 正常处理URL格式
        if base_url.endswith('/'):
            base_url = base_url.rstrip('/')
        if not base_url.endswith('/v1'):
            base_url = f"{base_url}/v1"
            
        logger.info(f"最终API基础URL: {base_url}")
        
        # 准备客户端参数
        api_key = openai_config.get('api_key', '')
        
        client_kwargs = {
            'api_key': api_key,
            'base_url': base_url,
        }
        
        return {
            'client_kwargs': client_kwargs,
            'model': openai_config.get('model_name', 'gpt-3.5-turbo'),
            'temperature': float(model_params.get('temperature', 0.1)),
            'max_tokens': int(model_params.get('max_tokens', 2000))
        }
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {
            'api_key': '',
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.1,
            'max_tokens': 8192
        }

from app.config import get_config

# Helper classes to mimic OpenAI's response structure for internal processing after streaming
class _MimicMessage:
    def __init__(self, content=None, role="assistant"):
        self.content = content
        self.role = role
        self.json_content = None  # Populated by _process_model_response

class _MimicChoice:
    def __init__(self, content=None, finish_reason=None):
        self.message = _MimicMessage(content)
        self.finish_reason = finish_reason
        self.index = 0

class _MimicCompletionResponse:
    def __init__(self, choices=None, usage=None, response_id=None, model_name=None, created_timestamp=None, object_type="chat.completion"):
        self.choices = choices if choices is not None else [_MimicChoice()]
        self.usage = usage
        self.id = response_id
        self.model = model_name
        self.created = created_timestamp if created_timestamp is not None else int(datetime.timestamp(datetime.now()))
        self.object = object_type

class ModelCaller:
    """负责调用AI模型的工具类"""

    @staticmethod
    def get_client(client_kwargs: Dict) -> Any:
        """获取 OpenAI 客户端"""
        if not HAS_OPENAI:
            logger.warning("OpenAI 库不可用（可能是缺少 jiter 依赖），将使用 Ollama 或其他替代方案")
            return None
        
        # 添加超时配置
        # 设置较大的超时值(180秒=3分钟)，避免大模型生成时间过长导致请求超时
        timeout_settings = httpx.Timeout(60.0, connect=10.0, read=180.0, write=60.0)
        
        # 使用客户端配置创建OpenAI对象
        log_once(logger.info, f"创建OpenAI客户端，连接到: {client_kwargs.get('base_url')}，超时设置: {timeout_settings}", f"client_create_{client_kwargs.get('base_url')}")
        
        # 添加timeout参数
        client_kwargs['timeout'] = timeout_settings
        logger.debug(f"[DEBUG] Final client_kwargs for OpenAI init: {client_kwargs}")
        if 'api_key' not in client_kwargs or not client_kwargs['api_key']:
            logger.error(f"[FATAL] api_key not found in client_kwargs: {client_kwargs}")
            raise ValueError("api_key is required for OpenAI client")
        if 'base_url' not in client_kwargs or not client_kwargs['base_url']:
            logger.error(f"[FATAL] base_url not found in client_kwargs: {client_kwargs}")
            raise ValueError("base_url is required for OpenAI client")
        return OpenAI(**client_kwargs)

    @classmethod
    def call_model(
        cls,
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        调用OpenAI大模型，支持流式日志记录，但返回完整的、与非流式兼容的响应对象。
        """
        # 记录完整的请求信息
        import sys
        sys.stderr.write("\n" + "="*80 + "\n")
        sys.stderr.write("【完整请求信息】\n")
        sys.stderr.write("="*80 + "\n")
        sys.stderr.write(f"模型: {model}\n")
        sys.stderr.write(f"温度: {temperature}\n")
        sys.stderr.write(f"最大tokens: {max_tokens}\n")
        if system_prompt:
            sys.stderr.write(f"\n【系统提示】\n{system_prompt}\n")
        if prompt:
            sys.stderr.write(f"\n【用户提示】\n{prompt}\n")
        sys.stderr.write("="*80 + "\n\n")

        config = load_openai_config()
        model_to_use = model or config['model']
        temperature_to_use = temperature if temperature is not None else config['temperature']
        max_tokens_to_use = max_tokens if max_tokens is not None else config['max_tokens']
        
        client_config = config['client_kwargs']
        client = cls.get_client(client_config)
        
        messages: List[ChatCompletionMessageParam] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if prompt:
            messages.append({"role": "user", "content": prompt})
        
        call_id = str(uuid.uuid4())[:8]
        log_once(logger.info, f"[Stream] OpenAI API 调用开始 (ID: {call_id})", f"api_call_start_{call_id}")
        log_once(logger.info, f"[Stream] 模型: {model_to_use}, 温度: {temperature_to_use}, 最大tokens: {max_tokens_to_use}", f"model_info_{call_id}")
        
        if system_prompt:
            system_prompt_log = f"[Stream] 系统提示 (前200字): {system_prompt[:200]}{'...' if len(system_prompt) > 200 else ''}"
            log_once(logger.info, system_prompt_log, f"system_prompt_{call_id}")
        
        user_prompt_log = f"[Stream] 用户提示 (前200字): {prompt[:200]}{'...' if len(prompt) > 200 else ''}"
        log_once(logger.info, user_prompt_log, f"user_prompt_{call_id}")
        if prompt:
            logger.debug(f"[Stream] 用户完整提示 (长度 {len(prompt)}):\n{prompt}")
        
        full_content_parts: List[str] = []
        final_usage: Optional[CompletionUsage] = None
        final_finish_reason: Optional[str] = None
        response_id_from_stream: Optional[str] = None
        model_from_stream: Optional[str] = None
        created_timestamp_from_stream: Optional[int] = None

        max_retries = 3
        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.info(f"[Stream] 开始流式请求 (ID: {call_id})... (第{attempt+1}次尝试)")
                stream = client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature_to_use,
                    max_tokens=max_tokens_to_use,
                    stream=True,
                    stream_options={"include_usage": True},
                    **kwargs
                )

                full_content_parts = []
                final_usage = None
                final_finish_reason = None
                response_id_from_stream = None
                model_from_stream = None
                created_timestamp_from_stream = None

                for chunk_idx, chunk in enumerate(stream):
                    if not response_id_from_stream:
                        response_id_from_stream = chunk.id
                        model_from_stream = chunk.model
                        created_timestamp_from_stream = chunk.created
                    if chunk.usage:
                        final_usage = chunk.usage
                    if chunk.choices:
                        choice = chunk.choices[0]
                        if choice.delta and choice.delta.content:
                            delta_content = choice.delta.content
                            full_content_parts.append(delta_content)
                            # 不在这里输出流式内容，由调用者决定是否需要
                            # sys.stderr.write(delta_content)
                        if choice.finish_reason:
                            final_finish_reason = choice.finish_reason
                            logger.info(f"收到终止原因: {final_finish_reason}")
                
                # 打印完整的响应内容
                complete_content_str = "".join(full_content_parts)
                
                
                # 构建完整的响应对象
                response = ChatCompletion(
                    id=response_id_from_stream or str(uuid.uuid4()),
                    choices=[
                        Choice(
                            index=0,
                            message=ChatCompletionMessage(
                                role="assistant",
                                content=complete_content_str
                            ),
                            finish_reason=final_finish_reason
                        )
                    ],
                    created=created_timestamp_from_stream or int(time.time()),
                    model=model_from_stream or model_to_use,
                    object="chat.completion",
                    usage=final_usage
                )
                # 记录模型响应到stderr
                import sys
                sys.stderr.write(f"模型原始响应 (ID: {call_id}): {response}\n")
                # 统一使用内部处理函数解析并填充 json_content，保证后续逻辑一致
                processed_resp = ModelCaller._process_model_response(response, complete_content_str, call_id)
                return processed_resp
                
            except Exception as e:
                last_exception = e
                logger.error(f"流式请求失败 (ID: {call_id}, 第{attempt+1}次尝试): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待重试... (ID: {call_id})")
                    time.sleep(1)  # 简单的重试延迟
                else:
                    logger.error(f"达到最大重试次数，放弃请求 (ID: {call_id})")
                    raise last_exception

    @staticmethod
    def _process_model_response(response, content, call_id=None):
        """处理模型响应内容"""
        # 生成唯一的请求ID作为日志缓存键
        if call_id is None:
            call_id = str(uuid.uuid4())[:8]

        # 基本合法性检查
        if not response.choices:
            log_once(logger.warning, "响应对象不包含选择", f"no_choices_{call_id}")
            return response

        if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
            log_once(logger.warning, "未找到有效的响应内容", f"no_content_{call_id}")
            return response

        # 记录关键信息，避免输出过长日志
        log_once(logger.info, f"模型响应内容总长度: {len(content)} 字符", f"content_length_{call_id}")

        # ========== 第一阶段：清理原始字符串 ==========
        cleaned_content = ModelCaller._clean_json_string(content)
        cleaned_content = ModelCaller._fix_invalid_json_escape(cleaned_content)
        if cleaned_content != content:
            log_once(logger.info, "已清理无效的 JSON 转义字符", f"json_cleaned_{call_id}")

        # ========== 第二阶段：处理可能的 Markdown 代码块 ==========
        json_str = cleaned_content.strip()
        log_once(logger.info, f"处理前的字符串（前50字符）: '{json_str[:50]}'", f"pre_process_str_{call_id}")

        if json_str.startswith('```'):
            log_once(logger.info, "检测到代码块标记", f"code_block_detected_{call_id}")
            if json_str.startswith('```json'):
                # ```json ... ```
                try:
                    if '```' in json_str[7:]:
                        actual_json = json_str.split('```json', 1)[1].split('```', 1)[0].strip()
                        log_once(logger.info, f"从```json...```中提取的JSON（前50字符）: '{actual_json[:50]}'", f"json_extracted_{call_id}")
                        json_str = actual_json
                    else:
                        # 只有开头 ```json 没有结尾 ```
                        json_str = json_str[7:].strip()
                        log_once(logger.info, f"从```json(无结束标记)中提取的JSON（前50字符）: '{json_str[:50]}'", f"json_extracted_no_end_{call_id}")
                except Exception as e:
                    log_once(logger.error, f"处理```json标记时出错: {e}", f"json_marker_error_{call_id}")
            else:
                # 普通 ``` ... ```
                parts = json_str.split('```')
                log_once(logger.info, f"分割后得到 {len(parts)} 个部分", f"parts_count_{call_id}")
                if len(parts) >= 3:
                    original_part = parts[1]
                    log_once(logger.info, f"代码块内容（前50字符）: '{original_part[:50]}'", f"code_block_content_{call_id}")
                    if original_part.lstrip().startswith('json'):
                        json_str = original_part[4:].lstrip()
                        log_once(logger.info, f"json 标记已移除，处理后内容（前50字符）: '{json_str[:50]}'", f"json_marker_removed_{call_id}")
                    else:
                        json_str = original_part
                        log_once(logger.info, "代码块内容不包含 json 标记", f"no_json_marker_{call_id}")

        # 记录处理后的 JSON 字符串
        log_once(logger.info, f"处理后的 JSON 字符串前 1000 字符: {json_str[:1000]}", f"json_processed_{call_id}")
        log_once(logger.info, f"字符串类型: {type(json_str).__name__}, 长度: {len(json_str)}", f"string_type_{call_id}")

        # 可选：将字符串写入调试文件方便排查
        try:
            if len(json_str) > 0:
                debug_file_path = f"temp/debug_json_{call_id}.json"
                os.makedirs(os.path.dirname(debug_file_path), exist_ok=True)
                with open(debug_file_path, "w", encoding="utf-8") as f:
                    f.write(json_str)
                log_once(logger.info, f"已将 JSON 内容写入调试文件: {debug_file_path}", f"debug_file_{call_id}")
        except Exception as e:
            log_once(logger.warning, f"写入调试文件失败: {e}", f"debug_write_fail_{call_id}")

        # ========== 第三阶段：尝试解析 JSON ==========
        try:
            result = json.loads(json_str)
            log_once(logger.info, "成功解析 JSON", f"json_parsed_{call_id}")
        except json.JSONDecodeError as json_err:
            # 解析失败时，尝试更多修复策略
            error_pos = json_err.pos
            error_line = json_err.lineno
            error_col = json_err.colno
            snippet = json_str[max(0, error_pos-20): error_pos+20]
            log_once(logger.error, f"JSON 解析失败 (行 {error_line}, 列 {error_col})。附近文本: '{snippet}'", f"json_error_{call_id}")

            # 尝试修复常见格式问题
            fixed_content = ModelCaller._attempt_json_fix(json_str)
            try:
                result = json.loads(fixed_content)
                log_once(logger.info, "修复后成功解析 JSON", f"json_fix_success_{call_id}")
            except Exception:
                log_once(logger.error, "修复后仍然无法解析 JSON", f"json_fix_fail_{call_id}")
                result = {"problems": [], "error": "JSON解析失败"}
        except Exception as e:
            log_once(logger.error, f"处理响应时发生未预期错误: {e}\n{traceback.format_exc()}", f"unknown_error_{call_id}")
            result = {"problems": [], "error": "处理响应时发生错误"}

        # ========== 第四阶段：规范结果结构 ==========
        if isinstance(result, list):
            result = {"problems": result}
        elif isinstance(result, dict) and 'chapters' in result and isinstance(result['chapters'], list):
            result = {"problems": result.get('chapters', [])}

        # 将解析结果写回响应对象，保持接口一致
        response.choices[0].message.json_content = result
        return response

    @staticmethod
    def _clean_json_string(json_str):
        # 1. Handle <think>...</think> or leading </think>
        # Find the last occurrence of </think>. If found, take everything after it.
        # This handles cases like "<think>...</think>{JSON}" and "</think>{JSON}"
        last_think_end_tag_index = json_str.rfind("</think>")
        if last_think_end_tag_index != -1:
            # Take the substring after "</think>"
            json_str = json_str[last_think_end_tag_index + len("</think>"):]
            # Strip leading whitespace that might have been between </think> and {
            json_str = json_str.lstrip()
        
        # 2. 移除 BOM 标记
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
            
        # 3. 处理 Markdown 代码块标记
        # 先处理 ```json 和 ``` 包裹的内容
        json_str = ''.join(
            char for char in json_str 
            if char == '\n' or char == '\t' or not (0 <= ord(char) < 32 or ord(char) == 127)
        )
        
        # 4. 移除JSON字符串前后的非JSON字符 (extract content between first '{' and last '}')
        # This step is crucial for isolating the JSON object itself.

        
        json_start = json_str.find('{')
        # +1 to include the closing brace for slicing, rfind returns index of '}'
        json_end = json_str.rfind('}') 
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = json_str[json_start : json_end + 1]
        # else: if no valid { } structure is found, json_str remains as is (potentially empty or non-JSON)
            
        return json_str.strip() # Final strip for any residual whitespace

    @staticmethod
    def _fix_invalid_json_escape(content):
        content = content.strip()
        invalid_escapes = [r'\\[^"\\bfnrtu]']
        for pattern in invalid_escapes:
            content = re.sub(pattern, lambda m: m.group(0).replace('\\', '\\\\'), content)
        return content

    @staticmethod
    def _attempt_json_fix(content):
        if content.startswith('```') and '```' in content[3:]:
            parts = content.split('```')
            if len(parts) >= 3:
                content = parts[1]
                if content.lstrip().startswith('json'):
                    content = content[4:].strip()
        if not content.lstrip().startswith('{') and not content.lstrip().startswith('['):
            obj_start = content.find('{')
            arr_start = content.find('[')
            if obj_start >= 0 and (arr_start < 0 or obj_start < arr_start):
                content = content[obj_start:]
            elif arr_start >= 0:
                content = content[arr_start:]
        if content.count('{') > content.count('}'):
            content += '}' * (content.count('{') - content.count('}'))
        elif content.count('[') > content.count(']'):
            content += ']' * (content.count('[') - content.count(']'))
        return content
