"""
负责调用AI模型的模块
"""
import os
import sys
import re
import uuid
import json
import logging
import traceback
import httpx
import openai
from openai import OpenAI
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, AsyncGenerator, Iterator
from app.utils.log_utils import log_once, log_with_interval, setup_logger

# 处理 jiter 库缺失的情况（Win7兼容性）
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError as e:
    if 'jiter' in str(e):
        # jiter 库缺失，这在某些系统如 Win7 可能发生
        import sys
        sys.stderr.write("警告: OpenAI 库依赖的 jiter 模块缺失，将使用替代方案\n")
        HAS_OPENAI = False
    else:
        # 其他导入错误，重新抛出
        raise

# 使用全局日志配置函数创建日志器
log_dir = os.path.join(os.path.dirname(__file__), '../../../../logs')
log_file = os.path.join(log_dir, 'regression_openai_api.log')
logger = setup_logger("wordllm", log_file, logging.INFO)

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
        
        # 判断是否是Ollama地址格式（如“192.168.202.1:11434”）
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
        self.usage = usage or {}
        self.id = response_id or f"cmpl-{uuid.uuid4().hex}"
        self.model = model_name or "gpt-3.5-turbo"
        self.created = created_timestamp or int(datetime.timestamp(datetime.now()))
        self.object = object_type

class ModelCaller:
    """负责调用AI模型的工具类"""

    @staticmethod
    def get_client(client_kwargs: Dict) -> Any:
        """获取 OpenAI 客户端"""
        if not HAS_OPENAI:
            logger.warning("OpenAI 库不可用（可能是缺少 jiter 依赖），将使用 Ollama 或其他替代方案")
            return None
        
        # 使用客户端配置创建OpenAI对象
        logger.info(f"创建OpenAI客户端，连接到: {client_kwargs.get('base_url')}")
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
        调用OpenAI大模型
        """
        # ====== OpenAI 调用逻辑 ======
        # 加载配置
        config = load_openai_config()
        
        # 设置参数，优先使用传入的参数，其次使用配置文件中的默认值
        model = model or config['model']
        temperature = temperature if temperature is not None else config['temperature']
        max_tokens = max_tokens if max_tokens is not None else config['max_tokens']
        
        # 创建客户端，使用新的client_kwargs格式
        try:
            client = cls.get_client(client_kwargs=config['client_kwargs'])
            
            # 打印调试信息
            logger.info(f"OpenAI客户端创建成功，连接到: {config['client_kwargs'].get('base_url')}")
        except Exception as e:
            logger.error(f"OpenAI客户端创建失败: {e}")
            logger.info("OpenAI 客户端不可用，转用 Ollama")
            return OllamaCaller.call_model(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if prompt:
            messages.append({"role": "user", "content": prompt})
        
        # 记录提示词到文件
        prompt_log_dir = os.path.join(log_dir, 'prompts')
        os.makedirs(prompt_log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        prompt_log_file = os.path.join(prompt_log_dir, f'regression_prompt_{timestamp}.txt')
        
        prompt_data = {
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'system_prompt': system_prompt,
            'prompt': prompt,
            'timestamp': timestamp
        }
        
        try:
            with open(prompt_log_file, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            logger.info(f'提示词已写入到 {prompt_log_file}')
        except Exception as e:
            logger.error(f'写入提示词日志失败: {e}')
        
        call_id = str(uuid.uuid4())[:8]
        log_once(logger.info, f"回归测试 OpenAI API 调用开始 (ID: {call_id})", f"api_call_start_{call_id}")
        log_once(logger.info, f"模型: {model}, 温度: {temperature}, 最大tokens: {max_tokens}", f"model_info_{call_id}")
        if system_prompt:
            system_prompt_log = f"系统提示: {system_prompt[:200]}..." if len(system_prompt) > 200 else f"系统提示: {system_prompt}"
            log_once(logger.info, system_prompt_log, f"system_prompt_{call_id}")
        user_prompt_log = f"用户提示: {prompt[:200]}..." if len(prompt) > 200 else f"用户提示: {prompt}"
        log_once(logger.info, user_prompt_log, f"user_prompt_{call_id}")

        # ====== 自动重试机制实现 ======
        max_retries = 3
        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.info(f"[Stream] 开始流式请求 (ID: {call_id})... (第{attempt+1}次尝试)")
                stream = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    stream_options={"include_usage": True},
                    **kwargs
                )
                response_chunks = []
                response_id_from_stream = None
                model_from_stream = None
                created_timestamp_from_stream = None
                full_content_parts = []
                for chunk_idx, chunk in enumerate(stream):
                    if not response_id_from_stream:
                        response_id_from_stream = chunk.id
                        model_from_stream = chunk.model
                        created_timestamp_from_stream = chunk.created
                    if chunk.choices:
                        choice = chunk.choices[0]
                        if choice.delta and choice.delta.content:
                            delta_content = choice.delta.content
                            full_content_parts.append(delta_content)
                            sys.stderr.write(delta_content)
                # 拼接完整内容
                full_content = ''.join(full_content_parts)
                
                # 创建模拟响应对象
                mimic_response = _MimicCompletionResponse(
                    choices=[_MimicChoice(content=full_content)]
                )
                
                # 处理模型响应
                try:
                    # 直接处理可能的markdown代码块内容
                    # 特别处理开始的 ```json 标记
                    json_content = full_content
                    if json_content.strip().startswith('```json'):
                        logger.info(f"流式响应包含```json标记")
                        try:
                            # 当完整的 ```json...``` 格式时的处理
                            if '```' in json_content[7:]:
                                actual_json = json_content.split('```json', 1)[1].split('```', 1)[0].strip()
                                logger.info(f"从流式响应中提取的JSON内容（前100字符）: {actual_json[:100]}")
                                json_content = actual_json
                            else:
                                # 如果只有开始标记而没有结束标记
                                json_content = json_content[7:].strip()  # 去掉 ```json 开始标记
                                logger.info(f"从流式响应中提取的JSON内容（前100字符）: {json_content[:100]}")
                        except Exception as e:
                            logger.error(f"处理流式响应中的```json标记时出错: {e}")
                    
                    # 尝试解析JSON
                    try:
                        # 使用处理后的json_content字符串
                        json_result = json.loads(json_content)
                        logger.info(f"成功从流式响应解析JSON: {json.dumps({k: type(v).__name__ for k, v in json_result.items()}, ensure_ascii=False)}")
                        
                        # 更新mimic_response的内容
                        mimic_response.choices[0].message.content = json_content
                        mimic_response.choices[0].message.json_content = json_result
                    except Exception as json_exc:
                        logger.warning(f"解析流式响应的JSON内容失败: {json_exc}")
                        # 保持原始内容
                        mimic_response.choices[0].message.content = full_content
                    
                    # 处理模型响应并返回
                    processed_response = ModelCaller._process_model_response(mimic_response, full_content, call_id)
                    
                    # 确保返回的对象有正确的结构
                    if not hasattr(processed_response, 'choices') or not processed_response.choices:
                        processed_response.choices = [_MimicChoice()]
                    if not hasattr(processed_response.choices[0], 'message'):
                        processed_response.choices[0].message = _MimicMessage()
                    
                    # 检查 json_content 字段
                    if not hasattr(processed_response.choices[0].message, 'json_content') or processed_response.choices[0].message.json_content is None:
                        logger.warning(f"响应对象缺少 json_content 字段，尝试从 content 字段解析")
                        if hasattr(processed_response.choices[0].message, 'content'):
                            try:
                                content_str = processed_response.choices[0].message.content
                                # 检查是否是json字符串
                                if content_str.strip().startswith('{') and content_str.strip().endswith('}'):
                                    processed_response.choices[0].message.json_content = json.loads(content_str)
                                    logger.info(f"从 content 字段成功解析 json_content")
                            except Exception as e:
                                logger.error(f"从 content 字段解析 json_content 失败: {e}")
                    
                    return processed_response
                    
                except Exception as parse_exc:
                    logger.warning(f"第{attempt+1}次处理模型响应时出错: {parse_exc}")
                    last_exception = parse_exc
                    continue
            except Exception as e:
                logger.warning(f"第{attempt+1}次模型请求异常: {e}")
                last_exception = e
                continue
        # 如果全部重试失败
        logger.error(f"模型多次输出非合法JSON，最终失败: {last_exception}")
        raise ValueError(f"模型连续{max_retries}次输出非合法JSON: {last_exception}")
    
    @staticmethod
    def _clean_json_string(json_str):
        """清理JSON字符串，移除<think>标签、BOM标记和不可见字符"""
        
        # 1. Handle <think>...</think> or leading </think>
        # Find the last occurrence of </think>. If found, take everything after it.
        # This handles cases like "<think>...</think>{JSON}" and "</think>{JSON}"
        last_think_end_tag_index = json_str.rfind("</think>")
        if last_think_end_tag_index != -1:
            # Take the substring after "</think>"
            json_str = json_str[last_think_end_tag_index + len("</think>"):]
            # Strip leading whitespace that might have been between </think> and {
            json_str = json_str.lstrip()
        
        # 2. 移除BOM标记 (original step)
        # 移除BOM标记
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
        
        # 3. 移除所有控制字符，但保留换行符和制表符 
        # ASCII 0-31 (excluding \n, \t) and 127 (DEL)
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
    def _process_model_response(response, content, call_id=None):
        """处理模型响应内容"""
        # 生成唯一的请求ID作为日志缓存键
        if call_id is None:
            call_id = str(uuid.uuid4())[:8]
            
        if not response.choices:
            log_once(logger.warning, "响应对象不包含选择", f"no_choices_{call_id}")
            return response
            
        if not hasattr(response.choices[0], 'message') or not hasattr(response.choices[0].message, 'content'):
            log_once(logger.warning, "未找到有效的响应内容", f"no_content_{call_id}")
            return response
            
        # 只记录关键信息
        log_once(logger.info, f"模型响应内容总长度: {len(content)} 字符", f"content_length_{call_id}")
        
        # 清理和预处理内容
        cleaned_content = ModelCaller._clean_json_string(content)
        cleaned_content = ModelCaller._fix_invalid_json_escape(cleaned_content)
        if cleaned_content != content:
            log_once(logger.info, "清理了无效的JSON转义字符", f"json_cleaned_{call_id}")
            
        try:
            # 尝试直接解析JSON
            # 首先尝试去除可能的代码块标记
            json_str = cleaned_content.strip()
            # 打印原始清理后的字符串
            log_once(logger.info, f"处理前的字符串（前50字符）: '{json_str[:50]}'", f"pre_process_str_{call_id}")
            
            # 处理可能的Markdown代码块
            if json_str.startswith('```'):
                log_once(logger.info, "检测到代码块标记", f"code_block_detected_{call_id}")
                
                # 特殊处理开始的 ```json 标记
                if json_str.startswith('```json'):
                    # 直接分割并取中间部分
                    try:
                        # 当完整的 ```json...``` 格式时的处理
                        if '```' in json_str[7:]:
                            actual_json = json_str.split('```json', 1)[1].split('```', 1)[0].strip()
                            log_once(logger.info, f"从```json...```中提取的JSON（前50字符）: '{actual_json[:50]}'", f"json_extracted_{call_id}")
                            json_str = actual_json
                        else:
                            # 如果只有开始标记而没有结束标记
                            json_str = json_str[7:].strip()  # 去掉 ```json 开始标记
                            log_once(logger.info, f"从```json(无结束标记)中提取的JSON（前50字符）: '{json_str[:50]}'", f"json_extracted_no_end_{call_id}")
                    except Exception as e:
                        log_once(logger.error, f"处理```json标记时出错: {e}", f"json_marker_error_{call_id}")
                
                # 常规处理其他类型的代码块
                else:         
                    parts = json_str.split('```')
                    log_once(logger.info, f"分割后得到 {len(parts)} 个部分", f"parts_count_{call_id}")
                    
                    if len(parts) >= 3:
                        original_part = parts[1]
                        log_once(logger.info, f"代码块内容（前50字符）: '{original_part[:50]}'", f"code_block_content_{call_id}")
                        
                        if original_part.lstrip().startswith('json'):
                            json_str = original_part[4:].lstrip()
                            log_once(logger.info, f"json标记已移除，处理后内容（前50字符）: '{json_str[:50]}'", f"json_marker_removed_{call_id}")
                        else:
                            json_str = original_part
                            log_once(logger.info, f"代码块内容不包含json标记", f"no_json_marker_{call_id}")
            
            # 记录处理后的JSON字符串
            log_once(logger.info, f"处理后的JSON字符串前1000字符: {json_str[:1000]}", f"json_processed_{call_id}")
            
            # 记录字符串的类型和编码信息
            log_once(logger.info, f"字符串类型: {type(json_str).__name__}, 长度: {len(json_str)}", f"string_type_{call_id}")
            
            # 记录前几个字符的ASCII码
            char_codes = [f"{c}({ord(c)})" for c in json_str[:20] if c]
            log_once(logger.info, f"字符串前20个字符的ASCII码: {char_codes}", f"char_codes_{call_id}")
            
            # 试着全部存为文件进行检查
            if len(json_str) > 0:
                debug_file_path = f"temp/debug_json_{call_id}.json"
                os.makedirs(os.path.dirname(debug_file_path), exist_ok=True)
                with open(debug_file_path, "w", encoding="utf-8") as f:
                    f.write(json_str)
                log_once(logger.info, f"已将JSON内容写入调试文件: {debug_file_path}", f"debug_file_{call_id}")
            
            try:
                result = json.loads(json_str)
                log_once(logger.info, "成功解析JSON", f"json_parsed_{call_id}")
            except json.JSONDecodeError as json_err:
                # 特别详细的错误信息
                error_pos = json_err.pos
                error_line = json_err.lineno
                error_col = json_err.colno
                error_msg = f"特殊的JSON解析错误: {str(json_err)}, 行: {error_line}, 列: {error_col}, 位置: {error_pos}"
                
                # 显示错误位置附近的字符
                context_size = 20
                start = max(0, error_pos - context_size)
                end = min(len(json_str), error_pos + context_size)
                error_context = json_str[start:end]
                error_context_chars = [f"{c}({ord(c)})" for c in error_context]
                
                log_once(logger.error, f"{error_msg}\n错误上下文: {error_context}\n字符码: {error_context_chars}", f"json_detailed_error_{call_id}")
                
                # 尝试修复常见问题
                if '```' in json_str:
                    cleaned_again = json_str.replace('```', '')
                    log_once(logger.info, f"尝试移除所有```标记", f"remove_all_backticks_{call_id}")
                    try:
                        result = json.loads(cleaned_again)
                        log_once(logger.info, "移除所有```后成功解析JSON", f"fixed_json_parsed_{call_id}")
                        json_str = cleaned_again  # 更新json_str为处理后的字符串
                    except Exception as e:
                        log_once(logger.error, f"移除```后仍无法解析: {str(e)}", f"fix_failed_{call_id}")
                        raise  # 重新抛出异常
                else:
                    raise  # 重新抛出异常
            
            # 确保返回的格式符合预期
            if 'problems' not in result:
                log_once(logger.warning, "响应中缺少'problems'字段，尝试转换格式", f"missing_problems_{call_id}")
                # 如果返回的是数组，包装成 problems 数组
                if isinstance(result, list):
                    result = {"problems": result}
                # 其他格式，尝试直接使用
                else:
                    result = {"problems": [result] if result else []}
            
            # 更新响应对象的内容为处理后的JSON字符串
            response.choices[0].message.content = json.dumps(result, ensure_ascii=False, indent=2)
            # 同时保存解析后的对象，以便后续处理
            response.choices[0].message.json_content = result
            
            log_once(logger.info, f"处理后的结果结构: {json.dumps({k: type(v).__name__ for k, v in result.items()}, ensure_ascii=False)}", f"result_structure_{call_id}")
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            if hasattr(e, 'pos') and hasattr(e, 'lineno') and hasattr(e, 'colno'):
                error_msg += f"\n错误位置: 行 {e.lineno}, 列 {e.colno} (位置 {e.pos})"
                # 显示错误位置附近的上下文
                context_size = 50
                start = max(0, e.pos - context_size)
                end = min(len(json_str), e.pos + context_size)
                error_msg += f"\n错误上下文: ...{json_str[start:end]}..."
                
                # 记录完整的JSON字符串（截断过长的内容）
                max_log_length = 2000
                error_msg += f"\n完整内容 (前{min(len(json_str), max_log_length)}字符):\n{json_str[:max_log_length]}"
            
            log_once(logger.error, error_msg, f"json_error_{call_id}")
            # 返回一个包含空问题列表的有效响应
            response.choices[0].message.content = json.dumps({"problems": []}, ensure_ascii=False, indent=2)
            response.choices[0].message.json_content = {"problems": []}
        except Exception as e:
            error_msg = f"处理模型响应时发生错误: {str(e)}"
            log_once(logger.error, error_msg, f"process_error_{call_id}")
            # 返回一个包含空问题列表的有效响应
            response.choices[0].message.content = json.dumps({"problems": []}, ensure_ascii=False, indent=2)
            response.choices[0].message.json_content = {"problems": []}
        
        return response

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
