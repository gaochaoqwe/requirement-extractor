"""
测试用例反向推导AI客户端
"""
import json
import time
import asyncio
import httpx
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from ..utils.logger import get_session_logger

class TestCaseReverseAIClient:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_session_logger(session_id)
        self.config = self._load_config()
        self._init_client()
        
        # 超时和重试配置
        self.request_timeout = 180.0  # 3分钟超时
        self.max_retries = 3  # 最多重试3次
        self.retry_delay = 2.0  # 重试间隔2秒
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 从testTools/testCase2testMethod回到app目录
            config_path = Path(__file__).parent.parent.parent.parent / "config.json"
            
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
    
    def _load_prompt_template(self, mode: str) -> str:
        """加载提示词模板"""
        try:
            prompt_dir = Path(__file__).parent.parent / "prompts"
            
            if mode == "template":
                prompt_file = prompt_dir / "template_mode_prompt.md"
            else:
                prompt_file = prompt_dir / "normal_mode_prompt.md"
            
            if not prompt_file.exists():
                self.logger.error(f"提示词文件不存在: {prompt_file}")
                return ""
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()
                self.logger.info(f"提示词模板加载成功: {mode} 模式")
                return template
                
        except Exception as e:
            self.logger.error(f"加载提示词模板时出错: {str(e)}")
            return ""
    
    async def generate_test_content_and_method(self, test_item_name: str, test_cases: List[Dict[str, str]], mode: str = "normal", requirement_description: str = "") -> Dict[str, Any]:
        """
        根据测试用例反向推导测试内容和测试方法
        
        Args:
            test_item_name: 测试项名称
            test_cases: 测试用例列表，每个包含input_condition和expected_result
            mode: 处理模式，"normal" 或 "template"
            requirement_description: 原始需求子项描述，来源于需求分析表S列
            
        Returns:
            Dict[str, Any]: 生成结果，包含test_content、test_method和可选的用例模板字段
        """
        try:
            self.logger.info(f"开始为测试项 '{test_item_name}' 反向推导测试内容和测试方法 (模式: {mode})")
            
            # 构建提示词
            prompt = self._build_reverse_prompt(test_item_name, test_cases, mode, requirement_description)
            
            if not prompt:
                return {"success": False, "error": "提示词构建失败"}
            
            # 使用重试机制调用AI
            ai_response = await self._call_ai_with_retry(prompt)
            
            if ai_response["success"]:
                try:
                    # JSON已经在重试机制中验证过了，直接解析
                    response_json = json.loads(ai_response["content"])
                    
                    # 提取基础字段
                    test_content = response_json.get("test_content", {})
                    test_method = response_json.get("test_method", {})
                    
                    if not test_content or not test_method:
                        self.logger.error("AI响应缺少必要字段: test_content 或 test_method")
                        return {
                            "success": False,
                            "error": "AI响应缺少必要字段"
                        }
                    
                    # 验证基础条目数量是否一致
                    content_count = len(test_content) if isinstance(test_content, (dict, list)) else 0
                    method_count = len(test_method) if isinstance(test_method, (dict, list)) else 0
                    if content_count != method_count:
                        self.logger.warning(f"测试内容和测试方法条目数量不一致: {content_count} vs {method_count}")
                    
                    # 格式化为带编号的字符串
                    formatted_content = self._format_with_numbers(test_content)
                    formatted_method = self._format_with_numbers(test_method)
                    
                    result = {
                        "success": True,
                        "test_content": formatted_content,
                        "test_method": formatted_method,
                        "raw_response": ai_response["content"]
                    }

                    if mode == "normal":
                        case_name = response_json.get("case_name", {})
                        case_description = response_json.get("case_description", {})
                        result.update({
                            "case_name": self._format_with_numbers(case_name),
                            "case_description": self._format_with_numbers(case_description)
                        })
                    
                    # 如果是模板模式，添加用例模板字段
                    if mode == "template":
                        case_template_name = response_json.get("case_template_name", {})
                        case_template_input = response_json.get("case_template_input", {})
                        case_template_expected = response_json.get("case_template_expected", {})
                        
                        # 验证模板字段数量一致性
                        name_count = len(case_template_name) if isinstance(case_template_name, (dict, list)) else 0
                        input_count = len(case_template_input) if isinstance(case_template_input, (dict, list)) else 0
                        expected_count = len(case_template_expected) if isinstance(case_template_expected, (dict, list)) else 0
                        template_lengths = [name_count, input_count, expected_count]
                        if not all(length == content_count for length in template_lengths):
                            self.logger.warning(f"模板字段数量不一致: 内容{content_count}, 名称{name_count}, 输入{input_count}, 预期{expected_count}")
                        
                        result.update({
                            "case_template_name": self._format_with_numbers(case_template_name),
                            "case_template_input": self._format_with_numbers(case_template_input),
                            "case_template_expected": self._format_with_numbers(case_template_expected)
                        })
                    
                    self.logger.info(f"测试项 '{test_item_name}' 反向推导成功 (模式: {mode})")
                    return result
                    
                except json.JSONDecodeError as e:
                    # 这种情况理论上不应该发生，因为重试机制已经验证过JSON
                    self.logger.error(f"意外的JSON解析错误: {str(e)}")
                    return {
                        "success": False,
                        "error": f"JSON解析错误: {str(e)}"
                    }
            else:
                return {
                    "success": False,
                    "error": ai_response.get("error", "AI调用失败")
                }
                
        except Exception as e:
            error_msg = f"生成测试内容和测试方法时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _build_reverse_prompt(self, test_item_name: str, test_cases: List[Dict[str, str]], mode: str, requirement_description: str = "") -> str:
        """构建反向推导提示词"""
        try:
            # 加载提示词模板
            template = self._load_prompt_template(mode)
            if not template:
                return ""
            
            # 构建测试用例内容
            test_cases_content = []
            for i, case in enumerate(test_cases, 1):
                input_condition = case.get("input_condition", "").strip()
                expected_result = case.get("expected_result", case.get("test_result", "")).strip()
                
                if not input_condition and not expected_result:
                    continue

                test_cases_content.append(
                    f"用例{i}: 输入条件: {input_condition or '无'}, 预期结果: {expected_result or '无'}"
                )
            
            test_cases_str = "\n".join(test_cases_content)

            # 需求描述片段（无内容时留空占位符，让模板处理）
            requirement_section = requirement_description.strip() if requirement_description and requirement_description.strip() else "（未提供）"
            
            # 替换模板中的占位符
            prompt = template.format(
                test_item_name=test_item_name,
                test_cases=test_cases_str,
                requirement_description=requirement_section
            )
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"构建提示词时出错: {str(e)}")
            return ""
    
    def _format_with_numbers(self, items: Union[Dict[str, str], List[str], None]) -> str:
        """将列表或对象格式化为字符串"""
        if not items:
            return ""
        
        # 如果是字典对象格式
        if isinstance(items, dict):
            formatted_items = []
            # 按键的数字顺序排序
            sorted_keys = sorted(items.keys(), key=lambda x: int(x) if x.isdigit() else float('inf'))
            for key in sorted_keys:
                value = items[key]
                # 直接使用原始值，不做额外处理
                formatted_items.append(value)
            return "\n".join(formatted_items)
        
        # 兼容旧的列表格式
        elif isinstance(items, list):
            formatted_items = []
            for i, item in enumerate(items, 1):
                formatted_items.append(f"{i}、{item}")
            return "\n".join(formatted_items)
        
        return str(items)
    
    async def _call_ai_with_retry(self, prompt: str) -> Dict[str, Any]:
        """
        带重试机制的AI调用
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"AI调用尝试 {attempt + 1}/{self.max_retries}")
                
                # 调用AI
                response = await self.call_ai_async(prompt)
                
                if response["success"]:
                    # 验证响应是否为有效JSON
                    try:
                        content = response["content"].strip()
                        # 尝试提取JSON部分
                        if "```json" in content:
                            json_start = content.find("```json") + 7
                            json_end = content.find("```", json_start)
                            if json_end != -1:
                                content = content[json_start:json_end].strip()
                        elif content.startswith("```") and content.endswith("```"):
                            content = content[3:-3].strip()
                        
                        # 验证JSON格式
                        json.loads(content)
                        response["content"] = content
                        return response
                        
                    except json.JSONDecodeError as json_error:
                        self.logger.warning(f"AI响应JSON格式无效 (尝试 {attempt + 1}): {str(json_error)}")
                        last_error = f"JSON解析失败: {str(json_error)}"
                        
                        # 如果不是最后一次尝试，继续重试
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                else:
                    last_error = response.get("error", "AI调用失败")
                    self.logger.warning(f"AI调用失败 (尝试 {attempt + 1}): {last_error}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"AI调用异常 (尝试 {attempt + 1}): {last_error}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        # 所有重试都失败了
        return {
            "success": False,
            "error": f"AI调用失败，已重试{self.max_retries}次: {last_error}"
        }
    
    async def call_ai_async(self, prompt: str) -> Dict[str, Any]:
        """异步调用AI"""
        start_time = time.time()
        
        try:
            model_to_use = self.model_name
            
            self.logger.info(f"开始调用AI - 模型: {model_to_use}, 超时: {self.request_timeout}秒")
            
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
            
            # 使用httpx异步客户端，设置3分钟超时
            async with httpx.AsyncClient(
                timeout=self.request_timeout,
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
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"AI调用超时 ({self.request_timeout}秒)"
            self.logger.error(f"{error_msg}，耗时: {execution_time:.2f}秒")
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time
            }
            
        except httpx.TimeoutException:
            execution_time = time.time() - start_time
            error_msg = f"AI调用超时 ({self.request_timeout}秒)"
            self.logger.error(f"{error_msg}，耗时: {execution_time:.2f}秒")
            
            return {
                "success": False,
                "error": error_msg,
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