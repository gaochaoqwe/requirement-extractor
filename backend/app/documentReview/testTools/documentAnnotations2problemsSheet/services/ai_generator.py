"""
AI生成服务 - 用于生成问题名称、需求描述和测评单位意见
"""
import json
import time
import httpx
from typing import Dict, Any, Optional
from pathlib import Path

from ..utils.logger import get_session_logger


class AIGenerator:
    """AI生成器，用于生成问题相关内容"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_session_logger(session_id)
        self.config = self._load_config()
        self._init_client()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 从testTools/documentAnnotations2problemsSheet/services回到app目录
            config_path = Path(__file__).parent.parent.parent.parent.parent / "config.json"
            
            if not config_path.exists():
                self.logger.error(f"配置文件不存在: {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.logger.info("配置文件加载成功")
                return config
                
        except Exception as e:
            self.logger.error(f"加载配置文件时出错: {str(e)}")
            return {}
    
    def _init_client(self):
        """初始化AI客户端"""
        try:
            openai_config = self.config.get("openai", {})
            
            if not openai_config:
                self.logger.error("未找到OpenAI配置")
                return
            
            base_url = openai_config.get("base_url", "https://api.openai.com/v1")
            
            # 设置属性
            self.api_key = openai_config.get("api_key")
            self.base_url = base_url
            self.model_name = openai_config.get("model_name", "gpt-3.5-turbo")
            self.model_params = self.config.get("model_params", {})
            
            self.proxies = None
            if "hyperbolic.xyz" not in base_url:
                proxy_config = self.config.get("proxy", {})
                if proxy_config.get("enabled", False):
                    self.proxies = {
                        "http://": proxy_config.get("http"),
                        "https://": proxy_config.get("https")
                    }
            
            self.logger.info(f"AI客户端初始化成功 - 模型: {self.model_name}, 基础URL: {self.base_url}")
            
        except Exception as e:
            self.logger.error(f"初始化AI客户端时出错: {str(e)}")
    
    async def generate_problem_name(self, location: str, description: str, original_text: str) -> Dict[str, Any]:
        """
        生成问题名称
        
        Args:
            location: 问题位置（章节号）
            description: 问题说明
            original_text: 原文内容
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            self.logger.info(f"开始生成问题名称 - 位置: {location}")
            
            prompt = f"""你是一个专业的软件测试工程师，负责审查软件需求文档。现在需要你根据文档批注信息，生成一个简洁明确的问题名称。

问题位置：{location}
问题说明：{description}
原文内容：{original_text}

请根据以上信息，生成一个简洁、准确的问题名称（10-20字以内），直接输出问题名称即可，不要有任何额外的解释或标点符号。

示例：
- 需求描述不清晰
- 章节编号不一致
- 缺少必要的接口说明
- 功能描述存在歧义
"""
            
            ai_response = await self.call_ai_async(prompt)
            
            if ai_response["success"]:
                problem_name = ai_response["content"].strip()
                # 清理可能的引号和多余符号
                problem_name = problem_name.strip('"\'。，、')
                
                self.logger.info(f"问题名称生成成功: {problem_name}")
                
                return {
                    "success": True,
                    "problem_name": problem_name,
                    "raw_response": ai_response["content"]
                }
            else:
                return {
                    "success": False,
                    "error": ai_response.get("error", "AI调用失败")
                }
                
        except Exception as e:
            error_msg = f"生成问题名称时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def generate_requirement_description(self, problem_name: str, location: str, description: str) -> Dict[str, Any]:
        """
        生成需求描述（四段式的第一段）
        
        Args:
            problem_name: 问题名称
            location: 问题位置
            description: 问题说明
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            self.logger.info(f"开始生成需求描述 - 问题: {problem_name}")
            
            prompt = f"""你是一个专业的软件测试工程师，负责编写问题报告单。现在需要你根据问题信息，生成"需求描述"部分。

问题名称：{problem_name}
问题位置：{location}
问题说明：{description}

需求描述是将问题转换为正面的需求表述，说明应该如何正确。请生成一段简洁的需求描述（30-80字），直接输出需求描述内容即可，不要有"需求描述："等前缀。

转换规则示例：
- "需求描述不清晰" → "需求描述应当清晰明确，便于开发人员理解和实现"
- "章节编号不一致" → "文档章节编号应当保持一致，遵循统一的编号规范"
- "缺少必要的接口说明" → "文档应当包含完整的接口说明，明确接口的输入输出参数"
- "功能描述存在歧义" → "功能描述应当准确无歧义，确保理解的一致性"
"""
            
            ai_response = await self.call_ai_async(prompt)
            
            if ai_response["success"]:
                requirement_desc = ai_response["content"].strip()
                
                self.logger.info(f"需求描述生成成功")
                
                return {
                    "success": True,
                    "requirement_description": requirement_desc,
                    "raw_response": ai_response["content"]
                }
            else:
                return {
                    "success": False,
                    "error": ai_response.get("error", "AI调用失败")
                }
                
        except Exception as e:
            error_msg = f"生成需求描述时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def generate_evaluation_opinion(self, problem_name: str, test_activity: str, problem_type: str) -> Dict[str, Any]:
        """
        生成测评单位意见
        
        Args:
            problem_name: 问题名称
            test_activity: 测试活动
            problem_type: 问题类型
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            self.logger.info(f"开始生成测评单位意见 - 问题: {problem_name}")
            
            prompt = f"""你是一个专业的软件测评工程师，负责编写问题报告单的测评单位意见。

问题名称：{problem_name}
测试活动：{test_activity}
问题类型：{problem_type}

请根据以上信息，生成一段专业的测评单位意见（40-100字），说明开发人员应该如何修改和改进。直接输出意见内容即可，不要有"测评单位意见："等前缀。

参考模板：
- 文档问题："请开发人员对文档问题进行修改，确保文档描述正确且测试人员能够理解测试需求。"
- 代码问题："请开发人员针对{problem_name}问题对代码进行修改，保证代码实现正确。"
- 需求问题："请开发人员完善需求描述，确保需求清晰明确，便于后续开发和测试工作的开展。"
"""
            
            ai_response = await self.call_ai_async(prompt)
            
            if ai_response["success"]:
                opinion = ai_response["content"].strip()
                
                self.logger.info(f"测评单位意见生成成功")
                
                return {
                    "success": True,
                    "evaluation_opinion": opinion,
                    "raw_response": ai_response["content"]
                }
            else:
                return {
                    "success": False,
                    "error": ai_response.get("error", "AI调用失败")
                }
                
        except Exception as e:
            error_msg = f"生成测评单位意见时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def call_ai_async(self, prompt: str) -> Dict[str, Any]:
        """异步调用AI"""
        start_time = time.time()
        
        try:
            model_to_use = self.model_name
            
            self.logger.info(f"开始调用AI - 模型: {model_to_use}")
            
            # 记录完整的请求提示词
            self.logger.info("=" * 80)
            self.logger.info("AI请求提示词（完整内容）:")
            self.logger.info(prompt)
            self.logger.info("=" * 80)
            
            # 构建请求数据
            request_data = {
                "model": model_to_use,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                **self.model_params
            }
            
            # 使用httpx异步客户端
            async with httpx.AsyncClient(
                timeout=30.0,
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
                result = response.json()
            
            # 提取内容
            content = result["choices"][0]["message"]["content"]
            
            execution_time = time.time() - start_time
            self.logger.info(f"AI调用完成，耗时: {execution_time:.2f}秒")
            
            # 记录完整的AI响应内容
            self.logger.info("=" * 80)
            self.logger.info("AI响应内容（完整内容）:")
            self.logger.info(content)
            self.logger.info("=" * 80)
            
            return {
                "success": True,
                "content": content,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"AI调用失败: {str(e)}"
            self.logger.error(f"{error_msg}，耗时: {execution_time:.2f}秒")
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time
            }
