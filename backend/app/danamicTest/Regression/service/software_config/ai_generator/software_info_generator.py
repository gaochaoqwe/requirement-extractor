import requests
import json
from pathlib import Path

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 配置相关参数
try:
    from ....config import OLLAMA_HOST, OLLAMA_MODEL
except ImportError:
    # 如果没有配置文件，使用默认值
    OLLAMA_HOST = "https://hpc.613.com/zds"
    OLLAMA_MODEL = "qwen2.5:32b-instruct-q5_1-20k"

def generate_software_info_by_ai(software_name):
    """
    根据软件名称，使用AI生成软件相关信息
    
    Args:
        software_name (str): 软件名称
        
    Returns:
        dict: 包含软件简称、软件简称（英文）、系统名称、系统简称、组件的字典
              格式: {
                  "software_short_name": "软件简称",
                  "software_short_name_en": "软件简称（英文）", 
                  "system_name": "系统名称",
                  "system_short_name": "系统简称",
                  "component": "组件"
              }
    """
    
    # 获取数据库中的组件列表
    try:
        from ....db.models import regression_db_instance
        components_data = regression_db_instance.get_components()
        available_components = [comp['value'] for comp in components_data]
        log_info(f"获取到组件列表: {available_components}", Path(__file__).stem)
    except Exception as e:
        log_error(f"获取组件列表失败: {str(e)}", Path(__file__).stem)
        available_components = ['雷达组件', '红外组件', '吊舱组件']  # 默认组件列表
    
    # 构建提示词
    prompt = f"""
请根据以下软件名称，生成相应的软件信息，并严格按照以下JSON格式返回，不要包含任何其他文字：

软件名称：{software_name}

可选组件列表：{', '.join(available_components)}

请生成以下信息：
1. 软件简称：基于软件名称生成简短的中文简称（3-8个字符）
2. 软件简称（英文）：使用驼峰命名法的英文简称，如SoftwareShortName
3. 系统名称：软件所属的系统名称
4. 系统简称：系统的简短名称（3-6个字符）
5. 组件：从可选组件列表中选择最合适的一个

要求：
- 软件简称要简洁明了，体现软件的核心功能
- 英文简称使用驼峰命名法，首字母大写
- 系统名称要体现软件的应用领域
- 组件必须从提供的可选组件列表中选择
- 如果软件名称包含"雷达"相关词汇，优先选择"雷达组件"
- 如果软件名称包含"红外"相关词汇，优先选择"红外组件"
- 如果软件名称包含"吊舱"相关词汇，优先选择"吊舱组件"
- 其他情况默认选择"雷达组件"

示例：
软件名称：雷达探测系统运动控制软件
{{
    "software_short_name": "雷达运控软件",
    "software_short_name_en": "RadarMotionControl",
    "system_name": "雷达探测系统",
    "system_short_name": "雷达系统",
    "component": "雷达组件"
}}

请严格按照以下JSON格式返回，不要添加任何解释或其他内容：
{{
    "software_short_name": "软件简称",
    "software_short_name_en": "SoftwareShortName",
    "system_name": "系统名称",
    "system_short_name": "系统简称",
    "component": "组件名称"
}}

/nothink"""

    # 构建请求参数
    params = {
        'system': '你是一个软件信息生成专家。请根据给定的软件名称生成相应的软件简称、英文简称、系统名称和系统简称。必须严格按照JSON格式返回，不要添加任何解释文字。',
        'prompt': prompt,
        'model': OLLAMA_MODEL,
        'stream': False
    }
    
    max_loop = 3  # 设置最大重试次数为 3 次
    
    while max_loop > 0:
        try:
            log_info(f"正在为软件 '{software_name}' 生成AI信息，剩余重试次数: {max_loop}", Path(__file__).stem)
            
            # 发送请求到Ollama
            res = requests.post(url=f'{OLLAMA_HOST}/api/generate', json=params, verify=False, timeout=30)
            
            if res.status_code == 200:
                response_text = res.json()["response"]
                log_info(f"AI响应原始内容: {response_text}", Path(__file__).stem)
                
                # 解析JSON响应
                result = _parse_ai_response(response_text, available_components)
                if result:
                    log_info(f"AI生成软件信息成功: {result}", Path(__file__).stem)
                    return result
                else:
                    log_warning(f"AI响应解析失败，尝试重试", Path(__file__).stem)
            else:
                log_error(f"AI请求失败，状态码: {res.status_code}", Path(__file__).stem)
                
        except Exception as e:
            log_error(f"AI调用异常: {str(e)}", Path(__file__).stem)
            
        max_loop -= 1
    
    # 如果AI生成失败，返回默认值
    log_warning(f"AI生成失败，使用默认值", Path(__file__).stem)
    return _generate_default_software_info(software_name, available_components)

def _parse_ai_response(response_text, available_components):
    """
    解析AI响应文本
    
    Args:
        response_text (str): AI响应的原始文本
        available_components (list): 可用组件列表
        
    Returns:
        dict: 解析后的软件信息字典，如果解析失败返回None
    """
    try:
        import re
        
        # 清理响应文本
        cleaned_response = response_text.strip()
        
        # 移除 <think> 标签及其内容
        think_pattern = r'<think>.*?</think>'
        cleaned_response = re.sub(think_pattern, '', cleaned_response, flags=re.DOTALL)
        cleaned_response = cleaned_response.strip()
        
        # 移除可能的markdown格式
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        log_info(f"清理后的AI响应: {cleaned_response}", Path(__file__).stem)
        
        # 尝试解析JSON
        if not cleaned_response:
            log_error("清理后的AI响应为空", Path(__file__).stem)
            return None
            
        result = json.loads(cleaned_response)
        
        # 验证结果格式
        required_fields = ["software_short_name", "software_short_name_en", "system_name", "system_short_name", "component"]
        if isinstance(result, dict) and all(field in result for field in required_fields):
            # 验证组件是否在可选列表中
            if result["component"] not in available_components:
                log_warning(f"AI选择的组件 '{result['component']}' 不在可选列表中，使用默认组件", Path(__file__).stem)
                result["component"] = available_components[0] if available_components else "雷达组件"
            
            log_info(f"AI解析成功: {result}", Path(__file__).stem)
            return result
        else:
            log_error(f"AI响应格式不正确: {result}", Path(__file__).stem)
            return None
            
    except json.JSONDecodeError as e:
        log_error(f"AI响应JSON解析失败: {str(e)}", Path(__file__).stem)
        return None
    except Exception as e:
        log_error(f"AI响应解析异常: {str(e)}", Path(__file__).stem)
        return None

def _generate_default_software_info(software_name, available_components):
    """
    生成默认的软件信息
    
    Args:
        software_name (str): 软件名称
        available_components (list): 可用组件列表
        
    Returns:
        dict: 默认的软件信息字典
    """
    try:
        # 根据软件名称智能选择组件
        component = available_components[0] if available_components else "雷达组件"
        
        if "雷达" in software_name:
            component = "雷达组件" if "雷达组件" in available_components else component
        elif "红外" in software_name:
            component = "红外组件" if "红外组件" in available_components else component
        elif "吊舱" in software_name:
            component = "吊舱组件" if "吊舱组件" in available_components else component
        
        # 生成简单的默认值
        software_short_name = software_name[:6] + "软件" if len(software_name) > 6 else software_name
        
        return {
            "software_short_name": software_short_name,
            "software_short_name_en": "SoftwareShortName", 
            "system_name": f"{software_name}系统",
            "system_short_name": "系统简称",
            "component": component
        }
        
    except Exception as e:
        log_error(f"默认值生成也失败，使用最简单的默认值: {str(e)}", Path(__file__).stem)
        return {
            "software_short_name": f"{software_name}简称",
            "software_short_name_en": "SoftwareShortName", 
            "system_name": f"{software_name}系统",
            "system_short_name": "系统简称",
            "component": available_components[0] if available_components else "雷达组件"
        }

def format_software_info_for_excel(software_info):
    """
    格式化软件信息用于Excel填充
    
    Args:
        software_info (dict): AI生成的软件信息
        
    Returns:
        tuple: (软件简称, 软件简称英文, 系统名称, 系统简称, 组件)
    """
    return (
        software_info.get("software_short_name", ""),
        software_info.get("software_short_name_en", ""),
        software_info.get("system_name", ""),
        software_info.get("system_short_name", ""),
        software_info.get("component", "")
    )
