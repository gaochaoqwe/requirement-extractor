"""
AI客户端模块

专注于纯粹的AI API调用，不包含业务逻辑和提示词定义。
所有提示词由ai_prompt_manager.py统一管理。
"""

import requests
import json
import re
from typing import List, Dict, Any, Tuple

# 配置相关参数
try:
    from .....utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
except ImportError:
    try:
        from .....utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL

# 导入日志工具
try:
    from ....utils.logging_utils.logger import log_info, log_debug, log_warning, log_error
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_debug, log_warning, log_error
    except ImportError:
        # 如果无法导入，定义占位符函数
        def log_info(msg, tag=""): print(f"[INFO] {msg}")
        def log_debug(msg, tag=""): print(f"[DEBUG] {msg}")
        def log_warning(msg, tag=""): print(f"[WARNING] {msg}")
        def log_error(msg, tag=""): print(f"[ERROR] {msg}")


def _parse_ai_response_json(response: str) -> List[Dict[str, Any]]:
    """
    解析AI响应JSON，处理多种AI响应格式
    
    Args:
        response: AI的原始响应
        
    Returns:
        List[Dict[str, Any]]: 解析后的测试用例列表
    """
    json_str = None
    
    try:
        # 🔧 新增：处理<think>标签，移除思考过程
        cleaned_response = response
        if "<think>" in response and "</think>" in response:
            # 移除<think>...</think>标签及其内容
            import re
            cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            log_debug(f"[AI_CLIENT] 移除<think>标签后的响应长度: {len(cleaned_response)}", "ai_client")
        
        # 方法1：尝试查找```json标记
        if "```json" in cleaned_response and "```" in cleaned_response[cleaned_response.index("```json")+7:]:
            start_idx = cleaned_response.index("```json") + 7  # 跳过```json
            end_idx = cleaned_response.rindex("```")
            json_str = cleaned_response[start_idx:end_idx].strip()
        
        # 方法2：优先尝试查找JSON对象格式 {...} （包含新的数组格式）
        elif "{" in cleaned_response and "}" in cleaned_response:
            start_idx = cleaned_response.index("{")
            end_idx = cleaned_response.rindex("}") + 1
            json_str = cleaned_response[start_idx:end_idx].strip()
        
        # 方法3：尝试查找JSON数组格式 [...] （仅用于纯数组响应）
        elif "[" in cleaned_response and "]" in cleaned_response:
            start_idx = cleaned_response.index("[")
            end_idx = cleaned_response.rindex("]") + 1
            json_str = cleaned_response[start_idx:end_idx].strip()
        
        # 方法4：尝试直接解析整个响应
        else:
            json_str = cleaned_response.strip()
        
        # 尝试解析JSON
        parsed_result = json.loads(json_str)
        
        # 🔧 新增：处理新的元组对格式
        if isinstance(parsed_result, dict):
            # 检查是否是新的元组对格式
            if 'test_pairs' in parsed_result:
                log_info(f"[AI_CLIENT] 检测到新的元组对格式", "ai_client")
                test_pairs = parsed_result.get('test_pairs', [])
                
                # 确保是数组格式
                if not isinstance(test_pairs, list):
                    test_pairs = [test_pairs]
                
                # 转换为标准格式
                result_list = []
                for i, pair in enumerate(test_pairs):
                    if isinstance(pair, dict) and 'description' in pair and 'method' in pair:
                        result_list.append({
                            'test_description': pair.get('description', '').strip(),
                            'test_method': pair.get('method', '').strip(),
                            # 保留其他字段（如requirement_description）
                            **{k: v for k, v in parsed_result.items() if k not in ['test_pairs']}
                        })
                    else:
                        log_warning(f"[AI_CLIENT] 无效的元组对格式，跳过项目 {i+1}: {pair}", "ai_client")
                
                log_info(f"[AI_CLIENT] 元组对格式转换完成，生成{len(result_list)}个测试项", "ai_client")
                return result_list
            
            # 检查是否是旧的数组格式（向后兼容）
            elif 'test_descriptions' in parsed_result and 'test_methods' in parsed_result:
                log_info(f"[AI_CLIENT] 检测到旧的数组格式，进行兼容处理", "ai_client")
                test_descriptions = parsed_result.get('test_descriptions', [])
                test_methods = parsed_result.get('test_methods', [])
                
                # 确保是数组格式
                if not isinstance(test_descriptions, list):
                    test_descriptions = [str(test_descriptions)]
                if not isinstance(test_methods, list):
                    test_methods = [str(test_methods)]
                
                # 验证数组长度一致性
                if len(test_descriptions) != len(test_methods):
                    log_warning(f"[AI_CLIENT] 测试描述和测试方法数量不匹配: {len(test_descriptions)} vs {len(test_methods)}", "ai_client")
                    # 取较小的长度，确保一一对应
                    min_length = min(len(test_descriptions), len(test_methods))
                    test_descriptions = test_descriptions[:min_length]
                    test_methods = test_methods[:min_length]
                
                # 转换为标准格式
                result_list = []
                for i, (desc, method) in enumerate(zip(test_descriptions, test_methods)):
                    result_list.append({
                        'test_description': desc.strip() if desc else '',
                        'test_method': method.strip() if method else '',
                        # 保留其他字段（如requirement_description）
                        **{k: v for k, v in parsed_result.items() if k not in ['test_descriptions', 'test_methods']}
                    })
                
                log_info(f"[AI_CLIENT] 旧数组格式转换完成，生成{len(result_list)}个测试项", "ai_client")
                return result_list
            else:
                # 传统单个对象格式
                return [parsed_result]
        elif isinstance(parsed_result, list):
            return parsed_result
        else:
            log_warning(f"[AI_CLIENT] 意外的JSON格式: {type(parsed_result)}", "ai_client")
            return []
    
    except Exception as e:
        log_error(f"[AI_CLIENT] JSON解析失败: {e}", "ai_client")
        log_debug(f"[AI_CLIENT] 原始响应: {response[:200]}...", "ai_client")
        log_debug(f"[AI_CLIENT] 提取的JSON字符串: {json_str[:200] if json_str else 'None'}...", "ai_client")
        return []


def call_ai_api(system_prompt: str, user_prompt: str, model: str = None) -> str:
    """
    调用AI API获取响应
    
    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        model: 模型名称（可选）
        
    Returns:
        str: AI的原始响应
    """
    if model is None:
        model = OLLAMA_MODEL
    
    log_info(f"[AI_CLIENT] 开始调用AI API - 模型: {model}", "ai_client")
    log_debug(f"[AI_CLIENT] 系统提示词长度: {len(system_prompt)}", "ai_client")
    log_debug(f"[AI_CLIENT] 用户提示词长度: {len(user_prompt)}", "ai_client")
    
    # 构建请求数据
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    
    try:
        # 发送请求
        url = f"{OLLAMA_HOST}/api/chat"
        log_debug(f"[AI_CLIENT] 请求URL: {url}", "ai_client")
        
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        # Ollama API返回格式: {"message": {"role": "assistant", "content": "..."}}
        message = result.get("message", {})
        ai_response = message.get("content", "") if isinstance(message, dict) else ""
        
        log_info(f"[AI_CLIENT] AI API调用成功，响应长度: {len(ai_response)}", "ai_client")
        log_debug(f"[AI_RESPONSE_FULL] AI完整原始响应: {ai_response}", "ai_client")
        
        return ai_response
        
    except requests.exceptions.RequestException as e:
        log_error(f"[AI_CLIENT] AI API请求失败: {e}", "ai_client")
        return ""
    except Exception as e:
        log_error(f"[AI_CLIENT] AI API调用异常: {e}", "ai_client")
        return ""


def generate_test_cases(ceshi_neirong: str, ceshi_leixing: str, jianceyi_flag: str, use_custom_prompt: bool = False) -> List[Dict[str, Any]]:
    """
    根据软件需求描述，生成测试相对应的测试内容和测试方法
    
    Args:
        ceshi_neirong: 需求描述内容或自定义提示词
        ceshi_leixing: 测试类型
        jianceyi_flag: 检测仪标志
        use_custom_prompt: 是否使用自定义提示词
    
    Returns:
        List[Dict[str, Any]]: 测试用例列表
    """
    log_info(f"[AI_CLIENT] 开始生成测试用例 - 测试类型: {ceshi_leixing}, 检测仪: {jianceyi_flag}, 自定义提示词: {use_custom_prompt}", "ai_client")
    
    if use_custom_prompt:
        # 使用自定义提示词模式
        log_info("[AI_CLIENT] 使用自定义提示词模式", "ai_client")
        system_prompt = "你是一个专业的软件测试专家。请严格按照用户的要求生成测试内容。"
        user_prompt = str(ceshi_neirong)
    else:
        # 使用提示词管理器获取提示词
        log_info("[AI_CLIENT] 使用标准提示词模式", "ai_client")
        
        try:
            try:
                from .ai_prompt_manager import prompt_manager
            except ImportError:
                try:
                    from ai_prompt_manager import prompt_manager
                except ImportError:
                    from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.ai_services.ai_prompt_manager import prompt_manager
            
            has_detector = jianceyi_flag == '有检测仪'
            
            prompt_config = prompt_manager.get_prompt_config(ceshi_leixing, ceshi_neirong, has_detector)
            
            # 🔧 正确处理结构化提示词
            if prompt_config.get('use_structured', False):
                # 对于结构化提示词，将structured_prompt作为user_prompt
                system_prompt = ""  # 结构化提示词不需要系统提示词
                user_prompt = prompt_config.get('structured_prompt', '')
                log_info(f"[AI_CLIENT] 使用结构化提示词模式，提示词长度: {len(user_prompt)}", "ai_client")
            else:
                # 对于传统提示词，使用system_prompt和user_prompt
                system_prompt = prompt_config['system_prompt']
                user_prompt = prompt_config['user_prompt']
                log_info(f"[AI_CLIENT] 使用传统提示词模式", "ai_client")
                
        except ImportError:
            log_error("[AI_CLIENT] 无法导入提示词管理器", "ai_client")
            return []
        except Exception as e:
            log_error(f"[AI_CLIENT] 获取提示词配置失败: {e}", "ai_client")
            return []
    
    # 调用AI API
    ai_response = call_ai_api(system_prompt, user_prompt)
    
    if not ai_response:
        log_warning("[AI_CLIENT] AI响应为空", "ai_client")
        return []
    
    # 解析AI响应
    test_cases = _parse_ai_response_json(ai_response)
    
    log_info(f"[AI_CLIENT] 成功生成 {len(test_cases)} 个测试用例", "ai_client")
    return test_cases


def moxingfenxi(str_temp: str, ceshi_leixing: str, jianceyi_flag: int = 0, test_name: str = "") -> Tuple[str, str]:
    """
    对软件的测试项进行分析，输出测试内容和测试方法
    
    Args:
        str_temp: 需求描述内容
        ceshi_leixing: 测试类型
        jianceyi_flag: 检测仪标志 (0: 无检测仪, 1: 有检测仪)
        test_name: 测试项名称
    
    Returns:
        Tuple[str, str]: (测试项描述, 测试方法)
    """
    log_info(f"[AI_CLIENT] 开始分析 - 测试类型: {ceshi_leixing}, 检测仪: {jianceyi_flag}, 测试名称: {test_name}", "ai_client")
    
    # 转换检测仪标志
    jianceyi_status = '有检测仪' if jianceyi_flag == 1 else '无检测仪'
    
    # 🔧 为结构化提示词传递测试名称
    if ceshi_leixing in ['功能测试', '性能测试', '边界测试'] and test_name:
        # 对于结构化提示词类型，需要将测试名称传递给prompt_manager
        try:
            try:
                from .ai_prompt_manager import prompt_manager
            except ImportError:
                try:
                    from ai_prompt_manager import prompt_manager
                except ImportError:
                    from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.ai_services.ai_prompt_manager import prompt_manager
            
            has_detector = jianceyi_status == '有检测仪'
            
            # 🔧 记录完整的需求描述内容
            log_info("=" * 120, "ai_client")
            log_info(f"[AI_CLIENT] 功能测试完整需求描述内容:\n{str_temp}", "ai_client")
            log_info("=" * 120, "ai_client")
            
            prompt_config = prompt_manager.get_prompt_config(ceshi_leixing, str_temp, has_detector, test_name)
            
            if prompt_config.get('use_structured', False):
                # 直接使用结构化提示词
                structured_prompt = prompt_config.get('structured_prompt', '')
                log_info(f"[AI_CLIENT] 使用结构化提示词，长度: {len(structured_prompt)}", "ai_client")
                log_info("=" * 120, "ai_client")
                log_info(f"[AI_CLIENT] 构建的结构化提示词:\n{structured_prompt}", "ai_client")
                log_info("=" * 120, "ai_client")
                
                # 使用自定义提示词模式调用generate_test_cases
                test_cases = generate_test_cases(structured_prompt, ceshi_leixing, jianceyi_status, use_custom_prompt=True)
            else:
                # 使用标准模式
                test_cases = generate_test_cases(str_temp, ceshi_leixing, jianceyi_status, use_custom_prompt=False)
        except Exception as e:
            log_warning(f"[AI_CLIENT] 使用结构化提示词失败，回退到标准模式: {e}", "ai_client")
            test_cases = generate_test_cases(str_temp, ceshi_leixing, jianceyi_status, use_custom_prompt=False)
    else:
        # 调用generate_test_cases获取测试用例
        test_cases = generate_test_cases(str_temp, ceshi_leixing, jianceyi_status, use_custom_prompt=False)
    
    if not test_cases:
        log_warning("[AI_CLIENT] 未生成任何测试用例", "ai_client")
        return "测试内容描述", "测试方法描述"
    
    # 格式化输出
    final_description_parts = []
    final_method_parts = []
    
    for i, test_case in enumerate(test_cases, 1):
        # 🔧 兼容不同的字段名称格式
        # 结构化提示词返回: test_description, test_method
        # 传统提示词返回: context, method
        context = test_case.get('test_description', test_case.get('context', '')).strip()
        method = test_case.get('test_method', test_case.get('method', '')).strip()
        
        # 🔧 修复：不再添加编号，因为AI返回的内容已经包含编号
        if context:
            final_description_parts.append(context)
        if method:
            final_method_parts.append(method)
    
    # 🔧 修复：使用换行分隔多个测试项，而不是 " | "
    final_description = '\n'.join(final_description_parts)
    final_method = '\n'.join(final_method_parts)
    
    log_info(f"[AI_CLIENT] 分析完成，生成{len(test_cases)}个测试项", "ai_client")
    log_debug(f"[AI_CLIENT] 最终描述: {final_description}", "ai_client")
    log_debug(f"[AI_CLIENT] 最终方法: {final_method}", "ai_client")
    
    return final_description, final_method 