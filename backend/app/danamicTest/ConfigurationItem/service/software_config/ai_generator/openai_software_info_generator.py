#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于OpenAI的软件信息生成器
用于根据软件名称生成软件简称、英文简称、系统名称和系统简称
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from openai import OpenAI

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


class OpenAISoftwareInfoGenerator:
    """OpenAI软件信息生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.config = self._load_config()
        self.client = self._init_openai_client()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            # 获取项目根目录的config.json路径
            current_file = Path(__file__)
            # 从 service/software_config/ai_generator/openai_software_info_generator.py 
            # 回到 app 目录： ../../../.. (4个parent)
            # 然后到 config.json
            project_root = current_file.parent.parent.parent.parent.parent.parent
            config_path = project_root / "config.json"
            
            print(f"[DEBUG] 当前文件: {current_file}")
            print(f"[DEBUG] 配置文件路径: {config_path}")
            print(f"[DEBUG] 配置文件存在: {config_path.exists()}")
            
            log_info(f"尝试加载配置文件: {config_path}", Path(__file__).stem)
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"[DEBUG] 配置文件加载成功")
                    print(f"[DEBUG] OpenAI配置: {config.get('openai', {})}")
                    log_info(f"配置文件加载成功", Path(__file__).stem)
                    return config
            else:
                print(f"[DEBUG] 配置文件不存在！")
                log_warning(f"配置文件不存在: {config_path}", Path(__file__).stem)
                return {}
        except Exception as e:
            print(f"[DEBUG] 加载配置文件失败: {e}")
            log_error(f"加载配置文件失败", Path(__file__).stem, e)
            return {}
    
    def _init_openai_client(self) -> OpenAI:
        """初始化OpenAI客户端"""
        try:
            openai_config = self.config.get("openai", {})
            
            base_url = openai_config.get("base_url", "https://api.openai.com/v1")
            api_key = openai_config.get("api_key", "")
            read_timeout = openai_config.get("read_timeout", 300.0)
            
            # 检查是否需要绕过代理（针对国内AI服务商）
            bypass_proxy_domains = [
                'dashscope.aliyuncs.com',
                'api.dashscope.aliyuncs.com',
                'modelscope.cn',
                'api-inference.modelscope.cn',
                'siliconflow.cn',
                'api.siliconflow.cn'
            ]
            
            # ✅ 清除所有代理环境变量，避免httpx 0.28+版本的兼容性问题
            proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']
            for var in proxy_env_vars:
                if var in os.environ:
                    del os.environ[var]
                    log_info(f"已清除环境变量: {var}", Path(__file__).stem)
            
            should_bypass_proxy = any(domain in base_url for domain in bypass_proxy_domains)
            
            if should_bypass_proxy:
                log_info(f"检测到国内AI服务商API，配置代理绕过 - base_url: {base_url}", Path(__file__).stem)
                # 设置环境变量绕过代理
                no_proxy_list = ','.join(bypass_proxy_domains)
                os.environ['NO_PROXY'] = no_proxy_list
                os.environ['no_proxy'] = no_proxy_list
                log_info(f"已设置NO_PROXY环境变量: {no_proxy_list}", Path(__file__).stem)
            
            # 初始化OpenAI客户端
            print(f"[DEBUG] API Key前10个字符: {api_key[:10] if api_key else 'None'}...")
            print(f"[DEBUG] API Key长度: {len(api_key) if api_key else 0}")
            print(f"[DEBUG] Base URL: {base_url}")
            
            client_kwargs = {
                "api_key": api_key,
                "base_url": base_url,
                "timeout": read_timeout
            }
                
            client = OpenAI(**client_kwargs)
            
            log_info(f"OpenAI客户端初始化完成 - base_url: {base_url}", Path(__file__).stem)
            return client
            
        except Exception as e:
            log_error(f"初始化OpenAI客户端失败", Path(__file__).stem, e)
            raise
    
    def generate_software_info(self, software_name: str) -> Optional[Dict[str, str]]:
        """
        根据软件名称生成软件信息
        
        Args:
            software_name: 软件名称
            
        Returns:
            Dict包含：
            - software_short_name: 软件简称
            - software_short_name_en: 软件简称(英文)
            - system_name: 系统名称
            - system_short_name: 系统简称
        """
        try:
            print(f"[DEBUG] 开始为软件 '{software_name}' 生成信息")
            log_info(f"开始为软件 '{software_name}' 生成信息", Path(__file__).stem)
            
            # 构建提示词
            prompt = self._build_prompt(software_name)
            print(f"[DEBUG] 提示词已构建，长度: {len(prompt)}")
            
            # 调用OpenAI API
            print("[DEBUG] 正在调用OpenAI API...")
            response = self._call_openai_api(prompt)
            print(f"[DEBUG] API调用完成，结果: {response}")
            
            if response:
                print(f"[DEBUG] 软件信息生成成功: {response}")
                log_info(f"软件信息生成成功: {response}", Path(__file__).stem)
                return response
            else:
                print("[DEBUG] OpenAI返回空结果")
                log_warning("OpenAI返回空结果", Path(__file__).stem)
                return None
                
        except Exception as e:
            print(f"[DEBUG] 生成软件信息失败: {e}")
            import traceback
            traceback.print_exc()
            log_error(f"生成软件信息失败", Path(__file__).stem, e)
            return None
    
    def _build_prompt(self, software_name: str) -> str:
        """构建提示词"""
        prompt = f"""你是一个软件信息分析专家。请根据给定的软件名称，提取以下信息：

软件名称：{software_name}

请按照以下规则生成软件信息：

1. **软件简称**：
   - 提取软件名称中表示具体功能的部分（通常是最后几个字，如"随动控制软件"、"管理软件"等）
   - 如果软件名称较短，可以适当保留关键词

2. **系统名称**：
   - 如果能识别出软件简称，则系统名称 = 软件名称去掉软件简称后的部分
   - 如果无法识别软件简称，查找关键字["设备", "系统", "吊舱", "搜索仪"]，从开头截取到关键字（包括关键字）
   - 如果都不适用，使用软件名称本身

3. **系统简称**：
   - 从系统名称中去掉前面由数字、字母、"/"、"-"组成的前缀
   - 例如："D-3/BBTEEE超级搜索雷达" → "超级搜索雷达"
   - 例如："DDBBTEEE超级搜索雷达" → "超级搜索雷达"

4. **软件简称(英文)**：
   - 将软件简称中的每个汉字转换为拼音首字母，全部大写
   - 例如："随动控制软件" → "SDKZRJ"
   - 例如："管理软件" → "GLRJ"

**示例1**：
软件名称：DDBBTEEE超级搜索雷达 随动控制软件
- 软件简称：随动控制软件
- 系统名称：DDBBTEEE超级搜索雷达
- 系统简称：超级搜索雷达
- 软件简称(英文)：SDKZRJ

**示例2**：
软件名称：雷达搜索设备随动控制软件
- 软件简称：随动控制软件
- 系统名称：雷达搜索设备
- 系统简称：雷达搜索设备
- 软件简称(英文)：SDKZRJ

**示例3**：
软件名称：D-3/BBTEEE火控管理软件
- 软件简称：管理软件
- 系统名称：D-3/BBTEEE火控
- 系统简称：火控
- 软件简称(英文)：GLRJ

请严格按照以下JSON格式返回结果，不要包含任何其他内容：

{{
    "software_short_name": "软件简称",
    "software_short_name_en": "软件简称英文大写",
    "system_name": "系统名称",
    "system_short_name": "系统简称"
}}"""
        
        return prompt
    
    def _call_openai_api(self, prompt: str) -> Optional[Dict[str, str]]:
        """调用OpenAI API"""
        try:
            openai_config = self.config.get("openai", {})
            model = openai_config.get("model_name", "gpt-3.5-turbo")
            model_params = self.config.get("model_params", {})
            
            print(f"[DEBUG] 调用OpenAI API - 模型: {model}")
            log_info(f"调用OpenAI API - 模型: {model}", Path(__file__).stem)
            log_debug(f"提示词内容:\n{prompt}", Path(__file__).stem)
            
            # 构建API调用参数
            api_params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": model_params.get("temperature", 0.1)
            }
            
            # 只有当 max_tokens 是正数时才添加限制
            max_tokens = model_params.get("max_tokens")
            if max_tokens and max_tokens > 0:
                api_params["max_tokens"] = max_tokens
            
            print(f"[DEBUG] API参数: temperature={api_params['temperature']}, max_tokens={max_tokens}")
            
            # 调用API
            print("[DEBUG] 正在请求OpenAI...")
            response = self.client.chat.completions.create(**api_params)
            print("[DEBUG] OpenAI请求成功")
            
            # 获取响应内容
            content = response.choices[0].message.content
            print(f"[DEBUG] 响应内容长度: {len(content) if content else 0}")
            print(f"[DEBUG] 响应内容: {content[:200] if content else 'None'}...")
            
            log_info(f"OpenAI响应内容:\n{content}", Path(__file__).stem)
            
            # 解析JSON响应
            print("[DEBUG] 正在解析响应...")
            result = self._parse_response(content)
            print(f"[DEBUG] 解析结果: {result}")
            
            return result
            
        except Exception as e:
            print(f"[DEBUG] 调用OpenAI API失败: {e}")
            import traceback
            traceback.print_exc()
            log_error(f"调用OpenAI API失败", Path(__file__).stem, e)
            return None
    
    def _parse_response(self, content: str) -> Optional[Dict[str, str]]:
        """解析AI响应"""
        try:
            # 清理响应内容
            cleaned_content = self._clean_json_string(content)
            
            # 解析JSON
            result = json.loads(cleaned_content)
            
            # 验证必需字段
            required_fields = ['software_short_name', 'software_short_name_en', 'system_name', 'system_short_name']
            if all(field in result for field in required_fields):
                return result
            else:
                log_warning(f"AI响应缺少必需字段: {result}", Path(__file__).stem)
                return None
                
        except json.JSONDecodeError as e:
            log_error(f"JSON解析失败: {content}", Path(__file__).stem, e)
            return None
        except Exception as e:
            log_error(f"解析AI响应失败", Path(__file__).stem, e)
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串"""
        # 移除 BOM 标记
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
        
        # 处理 Markdown 代码块标记
        if "```json" in json_str:
            start_pos = json_str.find("```json") + len("```json")
            end_pos = json_str.find("```", start_pos)
            if end_pos > start_pos:
                json_str = json_str[start_pos:end_pos].strip()
        elif "```" in json_str:
            # 处理没有语言标识的代码块
            start_pos = json_str.find("```") + len("```")
            end_pos = json_str.find("```", start_pos)
            if end_pos > start_pos:
                json_str = json_str[start_pos:end_pos].strip()
        
        # 提取完整的JSON对象
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
        
        return json_str.strip()


# 便捷函数
def generate_software_info_by_openai(software_name: str) -> Optional[Dict[str, str]]:
    """
    使用OpenAI生成软件信息的便捷函数
    
    Args:
        software_name: 软件名称
        
    Returns:
        Dict包含软件简称、英文简称、系统名称、系统简称
    """
    generator = OpenAISoftwareInfoGenerator()
    return generator.generate_software_info(software_name)

