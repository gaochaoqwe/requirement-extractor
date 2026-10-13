"""
静态分析过滤工具 - AI客户端
用于调用AI分析不确定规则的代码问题
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from openai import OpenAI
import httpx
import logging
from app.staticAnalysis.filter.utils.logger import get_session_logger


class StaticAnalysisAIClient:
    """静态分析AI客户端 - 用于分析代码问题的真实性"""
    
    def __init__(self, session_id: str = None, logger: logging.Logger = None):
        self.session_id = session_id
        # 优先使用传入的logger（任务专属logger），否则使用session logger
        self.logger = logger if logger is not None else (get_session_logger(session_id) if session_id else logging.getLogger("static_analysis_ai"))
        self.config = self._load_config()
        self._init_client()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 从 static_analysis_filter/services 回到 app 目录
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
            
            # 获取基础URL
            base_url = openai_config.get("base_url", "")
            
            # 检查是否需要绕过代理
            self._configure_proxy_bypass(base_url)
            
            # 设置客户端属性
            self.api_key = openai_config.get("api_key")
            self.base_url = base_url
            self.model_name = openai_config.get("model_name", "gpt-4")
            self.model_params = self.config.get("model_params", {
                "temperature": 0.3,  # 降低温度以获得更确定的结果
                "max_tokens": 2000
            })
            
            # 设置代理（如果需要）
            self.proxies = self._get_proxy_config(base_url)
            
            # 创建客户端
            client_kwargs = {
                "api_key": self.api_key,
                "base_url": self.base_url,
                "timeout": openai_config.get("connect_timeout", 60.0)
            }
            
            # 移除None值
            client_kwargs = {k: v for k, v in client_kwargs.items() if v is not None}
            
            self.client = OpenAI(**client_kwargs)
            
            self.logger.info(f"AI客户端初始化完成 - 模型: {self.model_name}, base_url: {self.base_url}")
            
        except Exception as e:
            self.logger.error(f"AI客户端初始化失败: {str(e)}")
            raise

    def _configure_proxy_bypass(self, base_url: str):
        """配置代理绕过"""
        # 支持的需要绕过代理的域名列表（国内AI服务商）
        bypass_proxy_domains = [
            'dashscope.aliyuncs.com',
            'api.dashscope.aliyuncs.com',
            'modelscope.cn',
            'api-inference.modelscope.cn',
            'siliconflow.cn',
            'api.siliconflow.cn',
            'hyperbolic.xyz',
            'api.hyperbolic.xyz',
            'openai.com',
            'api.openai.com'
        ]
        
        # 检查是否匹配任何需要绕过代理的域名
        should_bypass_proxy = any(domain in base_url for domain in bypass_proxy_domains)
        
        if should_bypass_proxy:
            # 设置环境变量绕过代理（添加所有支持的域名）
            no_proxy_list = ','.join(bypass_proxy_domains)
            os.environ['NO_PROXY'] = no_proxy_list
            os.environ['no_proxy'] = no_proxy_list
            self.logger.info(f"检测到需要绕过代理的API - base_url: {base_url}")
            self.logger.info(f"已设置NO_PROXY环境变量: {no_proxy_list}")

    def _get_proxy_config(self, base_url: str) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        # 支持的需要绕过代理的域名列表（与 _configure_proxy_bypass 保持一致）
        bypass_proxy_domains = [
            'dashscope.aliyuncs.com',
            'api.dashscope.aliyuncs.com',
            'modelscope.cn',
            'api-inference.modelscope.cn',
            'siliconflow.cn',
            'api.siliconflow.cn',
            'hyperbolic.xyz',
            'api.hyperbolic.xyz',
            'openai.com',
            'api.openai.com'
        ]
        
        # 如果是需要绕过代理的域名，不使用代理
        if any(domain in base_url for domain in bypass_proxy_domains):
            self.logger.info(f"URL匹配代理绕过列表，不使用代理: {base_url}")
            return None
        
        # 对于其他API，检查是否配置了代理
        proxy_config = self.config.get("proxy", {})
        if proxy_config.get("enabled", False):
            self.logger.info(f"使用配置的代理: {proxy_config}")
            return {
                "http://": proxy_config.get("http"),
                "https://": proxy_config.get("https")
            }
        
        return None

    async def analyze_code_issue(
        self, 
        issue_data: Dict[str, Any],
        rule_info: Dict[str, Any],
        code_context: str
    ) -> Dict[str, Any]:
        """
        分析代码问题是否为真实问题
        
        Args:
            issue_data: 问题数据 {issue_name, issue_file, issue_line, issue_description}
            rule_info: 规则信息 {rule_code, rule_name, rule_description}
            code_context: 代码上下文
            
        Returns:
            Dict[str, Any]: {
                "is_real_issue": bool,  # 是否为真实问题
                "confidence": float,    # 置信度 0-1
                "analysis_result": str, # 分析结果说明
                "reasoning": str,       # 推理过程
                "evidence": List[str],  # 证据列表
                "recommendations": str  # 建议
            }
        """
        try:
            self.logger.info(f"开始AI分析问题: {issue_data.get('issue_name')}")
            
            # 构建分析提示词
            prompt = self._build_analysis_prompt(issue_data, rule_info, code_context)
            
            # 调用AI
            result, raw_response = await self._call_ai_async(prompt)
            
            self.logger.info(f"AI分析完成: is_real_issue={result.get('is_real_issue')}, confidence={result.get('confidence')}")
            
            return result
            
        except Exception as e:
            error_msg = f"AI分析问题时出错: {str(e)}"
            self.logger.error(error_msg)
            # 返回默认结果（保守策略：认为是真实问题）
            return {
                "is_real_issue": True,
                "confidence": 0.5,
                "analysis_result": f"AI分析失败: {str(e)}",
                "reasoning": "由于AI分析失败，采用保守策略认为是真实问题",
                "evidence": [],
                "recommendations": "建议人工审查"
            }

    def _build_analysis_prompt(
        self,
        issue_data: Dict[str, Any],
        rule_info: Dict[str, Any],
        code_context: str
    ) -> str:
        """构建代码问题分析提示词"""
        
        issue_name = issue_data.get('issue_name', '未知问题')
        issue_file = issue_data.get('issue_file', '未知文件')
        issue_line = issue_data.get('issue_line', '未知行号')
        issue_desc = issue_data.get('issue_description', '无描述')
        
        rule_code = rule_info.get('rule_code', '未知规则')
        rule_name = rule_info.get('rule_name', '未知规则名称')
        rule_desc = rule_info.get('rule_description', '无规则描述')
        
        prompt = f"""你是一个专业的C/C++代码静态分析专家。请分析以下代码问题是否为真实问题。

**问题信息：**
- 规则编号：{rule_code}
- 规则名称：{rule_name}
- 规则描述：{rule_desc}
- 问题位置：{issue_file}:{issue_line}
- 问题描述：{issue_desc}

**代码上下文：**
```c
{code_context}
```

**分析要求：**
1. 仔细阅读代码上下文，理解代码的实际逻辑
2. 判断报告的问题是否为真实问题，还是误报
3. 考虑以下因素：
   - 变量是否在所有代码路径中都已初始化
   - 数组访问是否真的越界（考虑边界检查和实际数组大小）
   - 内存是否真的在释放后被使用（考虑指针置空等安全措施）
   - 是否有其他保护措施使得代码实际上是安全的

**判断标准：**
- 真实问题：代码确实存在违反规则的行为，可能导致运行时错误
- 误报：代码看起来违反规则，但实际上有保护措施或边界检查，是安全的

请以JSON格式返回分析结果：
{{
    "is_real_issue": true/false,
    "confidence": 0.0-1.0,
    "analysis_result": "简要说明是否为真实问题",
    "reasoning": "详细的推理过程，说明为什么是/不是真实问题",
    "evidence": ["证据1", "证据2", ...],
    "recommendations": "如果是真实问题，给出修复建议；如果是误报，说明为什么是安全的"
}}

注意：
- is_real_issue: true表示真实问题，false表示误报
- confidence: 0.0-1.0之间的浮点数，表示判断的置信度
- 返回的必须是有效的JSON格式
- 分析要基于代码的实际逻辑，不要仅凭规则名称判断
"""
        
        return prompt

    async def _call_ai_async(self, prompt: str, model_name: str = None) -> Tuple[Dict[str, Any], str]:
        """
        异步调用AI生成分析结果
        
        Args:
            prompt: 提示词
            model_name: 模型名称（可选）
            
        Returns:
            Tuple[Dict[str, Any], str]: (解析后的结果, 原始响应内容)
        """
        start_time = time.time()
        
        try:
            # 确定使用的模型
            model_to_use = model_name or self.model_name
            
            # 准备请求参数
            request_data = {
                "model": model_to_use,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的C/C++代码静态分析专家，擅长判断代码问题的真实性。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                **self.model_params
            }
            
            self.logger.info(f"开始调用AI - 模型: {model_to_use}")
            self.logger.info("=" * 80)
            self.logger.info("AI请求提示词（完整内容）:")
            self.logger.info(prompt)
            self.logger.info("=" * 80)
            self.logger.info(f"请求参数: temperature={request_data.get('temperature')}, max_tokens={request_data.get('max_tokens')}")
            
            # 使用异步HTTP客户端
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),  # 120秒超时
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
            
            self.logger.info("=" * 80)
            self.logger.info("AI响应内容（完整内容）:")
            self.logger.info(content)
            self.logger.info("=" * 80)
            
            # 解析响应
            result = self._parse_analysis_response(content)
            return result, content
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"调用AI时出错: {str(e)}"
            self.logger.error(f"{error_msg}，耗时: {execution_time:.2f}秒")
            raise Exception(f"AI调用失败: {str(e)}")

    async def chat_completion(self, messages, temperature: float = 0.3, max_tokens: int = 1000) -> Dict[str, Any]:
        """兼容接口：根据消息调用聊天补全，返回包含'content'字段的结果"""
        start_time = time.time()
        try:
            model_to_use = self.model_name
            request_data = {
                "model": model_to_use,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }
            self.logger.info(f"[chat_completion] 开始调用 - 模型: {model_to_use}, temperature={temperature}, max_tokens={max_tokens}")
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),
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
                data = response.json()
            content = data["choices"][0]["message"]["content"]
            elapsed = time.time() - start_time
            self.logger.info(f"[chat_completion] 调用完成，耗时 {elapsed:.2f}s")
            return {"content": content, "raw": data}
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[chat_completion] 失败: {e}，耗时 {elapsed:.2f}s")
            raise

    def _parse_analysis_response(self, content: str) -> Dict[str, Any]:
        """解析AI分析响应"""
        try:
            # 清理JSON字符串
            cleaned_content = self._clean_json_string(content)
            
            # 解析JSON
            result = json.loads(cleaned_content)
            
            # 验证必需字段
            required_fields = ["is_real_issue", "confidence", "analysis_result", "reasoning"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 确保类型正确
            result["is_real_issue"] = bool(result["is_real_issue"])
            result["confidence"] = float(result["confidence"])
            
            # 确保可选字段存在
            if "evidence" not in result:
                result["evidence"] = []
            if "recommendations" not in result:
                result["recommendations"] = ""
            
            self.logger.info("AI响应解析成功")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON解析失败: {str(e)}")
            return self._create_fallback_result(content)
        except Exception as e:
            self.logger.error(f"解析AI响应时出错: {str(e)}")
            return self._create_fallback_result(content)

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

    def _create_fallback_result(self, content: str) -> Dict[str, Any]:
        """创建后备结果（当解析失败时）"""
        self.logger.warning("使用后备结果")
        
        # 尝试从文本中提取关键信息
        is_real_issue = True  # 默认认为是真实问题（保守策略）
        confidence = 0.5
        
        # 简单的关键词检测
        content_lower = content.lower()
        if any(word in content_lower for word in ['误报', 'false positive', '不是问题', 'not an issue', '安全']):
            is_real_issue = False
            confidence = 0.6
        elif any(word in content_lower for word in ['真实问题', 'real issue', '确实存在', '违反规则']):
            is_real_issue = True
            confidence = 0.7
        
        return {
            "is_real_issue": is_real_issue,
            "confidence": confidence,
            "analysis_result": "AI响应解析失败，使用后备判断",
            "reasoning": f"原始响应: {content[:200]}...",
            "evidence": [],
            "recommendations": "建议人工审查"
        }
