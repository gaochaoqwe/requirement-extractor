"""
鉴定测评表单辅助工具AI客户端
修复配置问题，使用config.json中的OpenAI参数
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from openai import OpenAI
import logging
from ..utils.logger import get_session_logger

class AssessmentAIClient:
    def __init__(self, session_id: str = None):
        self.session_id = session_id
        self.logger = get_session_logger(session_id) if session_id else logging.getLogger("assessment_ai_client")
        self.config = self._load_config()
        self._init_client()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 从testTools/assessment_form_helper回到app目录
            current_file = Path(__file__)
            app_dir = current_file.parent.parent.parent.parent  # 回到app目录
            config_path = app_dir / "config.json"
            
            if not config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
                
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.logger.info(f"成功加载配置文件: {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            raise

    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            # 使用config.json中的OpenAI配置
            openai_config = self.config.get("openai", {})
            
            if not openai_config:
                raise ValueError("config.json中未找到openai配置")
            
            # 检查是否需要绕过代理（针对hyperbolic.xyz）
            base_url = openai_config.get("base_url", "")
            if "hyperbolic.xyz" in base_url:
                self.logger.info(f"检测到Hyperbolic API，配置代理绕过 - base_url: {base_url}")
                os.environ['NO_PROXY'] = 'api.hyperbolic.xyz,hyperbolic.xyz'
                os.environ['no_proxy'] = 'api.hyperbolic.xyz,hyperbolic.xyz'
            
            # 设置客户端属性
            self.api_key = openai_config.get("api_key")
            self.base_url = base_url
            self.model_name = openai_config.get("model_name", "gpt-3.5-turbo")
            self.model_params = self.config.get("model_params", {})
            
            # 设置代理（如果需要）
            self.proxies = None
            if "hyperbolic.xyz" not in base_url:
                # 对于非hyperbolic的API，可能需要代理
                proxy_config = self.config.get("proxy", {})
                if proxy_config.get("enabled", False):
                    self.proxies = {
                        "http://": proxy_config.get("http"),
                        "https://": proxy_config.get("https")
                    }
            
            # 创建客户端参数（保持向后兼容）
            client_kwargs = {
                "api_key": self.api_key,
                "base_url": self.base_url,
                "timeout": openai_config.get("connect_timeout", 10.0)
            }
            
            # 移除None值
            client_kwargs = {k: v for k, v in client_kwargs.items() if v is not None}
            
            self.client = OpenAI(**client_kwargs)
            
            self.logger.info(f"AI客户端初始化完成 - 模型: {self.model_name}, base_url: {self.base_url}")
            
        except Exception as e:
            self.logger.error(f"AI客户端初始化失败: {str(e)}")
            raise

    async def generate_assessment_content(self, 
                                        test_description: str, 
                                        test_method: str, 
                                        original_requirement: str = None) -> Dict[str, Any]:
        """
        异步生成评估内容
        
        Args:
            test_description (str): 测试项描述
            test_method (str): 测试方法
            original_requirement (str, optional): 原始需求内容
            
        Returns:
            Dict[str, Any]: 生成的评估内容
        """
        try:
            self.logger.info("开始生成评估内容")
            self.logger.info(f"输入参数 - 测试项描述: {test_description}")
            self.logger.info(f"输入参数 - 测试方法: {test_method}")
            if original_requirement:
                self.logger.info(f"输入参数 - 原始需求: {original_requirement}")
            
            # 构建提示词
            prompt = self._build_assessment_prompt(test_description, test_method, original_requirement)
            
            # 异步调用AI
            result, raw_response = await self.call_ai_async(prompt)
            
            self.logger.info("AI响应解析成功")
            self.logger.info(f"解析结果 - 充分性要求: {result.get('adequacy_requirement', 'N/A')}")
            self.logger.info(f"解析结果 - 通过准则: {result.get('pass_criteria', 'N/A')}")
            
            return result
            
        except Exception as e:
            error_msg = f"生成评估内容时出错: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def call_ai(self, prompt: str) -> Dict[str, Any]:
        """
        同步调用AI（保持向后兼容）
        """
        import asyncio
        
        # 如果在异步上下文中，直接抛出异常
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError("请使用 call_ai_async 方法进行异步调用")
        except RuntimeError as e:
            if "no running event loop" in str(e):
                # 没有运行的事件循环，可以创建新的
                return asyncio.run(self.call_ai_async(prompt))[0]
            else:
                # 有运行的事件循环，不能使用同步调用
                raise RuntimeError("请使用 call_ai_async 方法进行异步调用")

    def _build_assessment_prompt(self, test_description: str, test_method: str, original_requirement: str = None) -> str:
        """
        构建评估提示词
        
        Args:
            test_description (str): 测试项描述
            test_method (str): 测试方法
            original_requirement (str, optional): 原始需求内容
            
        Returns:
            str: 构建的提示词
        """
        prompt = f"""你是一个专业的软件测试评估专家。请根据以下信息生成三方测评表单的相关内容：

测试项描述：{test_description}
测试方法：{test_method}"""

        if original_requirement:
            prompt += f"""
原始需求内容：{original_requirement}"""

        prompt += """

请生成以下内容，并以JSON格式返回：

1. 充分性要求：基于测试项描述和测试方法，简洁地定义测试的充分性标准。内容要精简，不超过50字，不要分条目或编号。

2. 通过准则：基于测试项描述和测试方法，简洁地定义测试通过的具体标准。内容要精简，不超过30字，不要分条目或编号。

返回格式：
{
    "adequacy_requirement": "充分性要求内容", 
    "pass_criteria": "通过准则内容"
}

注意：
- 充分性要求要简洁明了，重点说明测试覆盖要求
- 通过准则要简洁明了，重点说明判定标准
- 所有内容都不要使用条目编号（如1、2、3或a)、b)、c)等）
- 所有内容都要用自然语言表述，避免列表形式
- 返回的必须是有效的JSON格式"""

        return prompt

    async def call_ai_async(self, prompt: str, model_name: str = None) -> Tuple[Dict[str, Any], str]:
        """
        异步调用AI生成内容
        
        Args:
            prompt (str): 提示词
            model_name (str, optional): 模型名称，如果不指定则使用默认模型
            
        Returns:
            Tuple[Dict[str, Any], str]: (解析后的结果, 原始响应内容)
        """
        import httpx
        import asyncio
        
        start_time = time.time()
        
        try:
            # 确定使用的模型
            model_to_use = model_name or self.model_name
            
            # 准备请求参数
            request_data = {
                "model": model_to_use,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,  # 使用非流式响应简化处理
                **self.model_params
            }
            
            self.logger.info(f"开始调用AI - 模型: {model_to_use}")
            
            # 记录完整的请求提示词
            self.logger.info("=" * 80)
            self.logger.info("AI请求提示词（完整内容）:")
            self.logger.info(prompt)
            self.logger.info("=" * 80)
            
            # 使用异步HTTP客户端
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),  # 60秒超时
                proxies=self.proxies
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_data
                )
                
                response.raise_for_status()
                response_data = response.json()
            
            # 提取内容
            content = response_data["choices"][0]["message"]["content"]
            
            execution_time = time.time() - start_time
            self.logger.info(f"AI调用完成，耗时: {execution_time:.2f}秒")
            
            # 记录完整的AI响应内容
            self.logger.info("=" * 80)
            self.logger.info("AI响应内容（完整内容）:")
            self.logger.info(content)
            self.logger.info("=" * 80)
            
            # 处理响应
            result = self._process_model_response(content)
            return result, content
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"调用AI时出错: {str(e)}"
            self.logger.error(f"{error_msg}，耗时: {execution_time:.2f}秒")
            raise Exception(f"AI调用失败: {str(e)}")

    def _process_model_response(self, content: str) -> Dict[str, Any]:
        """处理模型响应"""
        try:
            # 清理JSON字符串
            cleaned_content = self._clean_json_string(content)
            
            # 尝试解析JSON
            result = json.loads(cleaned_content)
            
            # 验证必需字段
            required_fields = ["adequacy_requirement", "pass_criteria"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"缺少必需字段: {field}")
            
            self.logger.info("AI响应解析成功")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON解析失败，尝试修复: {str(e)}")
            return self._try_fix_json(content)
        except Exception as e:
            self.logger.error(f"处理AI响应时出错: {str(e)}")
            raise

    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串"""
        # 移除markdown代码块标记
        json_str = json_str.replace('```json', '').replace('```', '')
        
        # 移除多余的空白字符
        json_str = json_str.strip()
        
        # 查找JSON对象的开始和结束
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = json_str[start_idx:end_idx + 1]
        
        return json_str

    def _try_fix_json(self, content: str) -> Dict[str, Any]:
        """尝试修复损坏的JSON"""
        try:
            # 基本的JSON修复逻辑
            content = self._clean_json_string(content)
            
            # 尝试添加缺失的引号和括号
            if not content.startswith('{'):
                content = '{' + content
            if not content.endswith('}'):
                content = content + '}'
            
            result = json.loads(content)
            
            # 确保有必需的字段
            default_result = {
                "adequacy_requirement": "充分性要求生成失败",
                "pass_criteria": "通过准则生成失败"
            }
            
            for key, default_value in default_result.items():
                if key not in result:
                    result[key] = default_value
            
            self.logger.warning("JSON修复成功")
            return result
            
        except Exception as e:
            self.logger.error(f"JSON修复失败: {str(e)}")
            # 返回默认结果
            return {
                "adequacy_requirement": "AI响应解析失败，请重试",
                "pass_criteria": "AI响应解析失败，请重试"
            } 