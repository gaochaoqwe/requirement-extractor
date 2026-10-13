"""
测试用例总结AI客户端
"""
import json
import time
import httpx
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..utils.logger import get_session_logger

class TestCaseSummaryAIClient:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_session_logger(session_id)
        self.config = self._load_config()
        self._init_client()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 从testTools/test_case_summary回到app目录
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
            
            client_kwargs = {
                "api_key": self.api_key,
                "base_url": self.base_url,
                "timeout": openai_config.get("connect_timeout", 10.0)
            }
            
            if self.proxies:
                client_kwargs["proxies"] = self.proxies
            
            self.logger.info(f"AI客户端初始化成功 - 模型: {self.model_name}, 基础URL: {self.base_url}")
            
        except Exception as e:
            self.logger.error(f"初始化AI客户端时出错: {str(e)}")
    
    async def generate_test_case_summary(self, test_item_name: str, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        生成测试用例总结
        
        Args:
            test_item_name: 测试项名称
            test_cases: 测试用例列表，每个包含input_condition和test_result
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            self.logger.info(f"开始为测试项 '{test_item_name}' 生成总结")
            
            # 构建提示词
            prompt = self._build_summary_prompt(test_item_name, test_cases)
            
            # 调用AI
            ai_response = await self.call_ai_async(prompt)
            
            if ai_response["success"]:
                summary = ai_response["content"].strip()
                
                self.logger.info(f"测试项 '{test_item_name}' 总结生成成功")
                
                return {
                    "success": True,
                    "summary": summary,
                    "raw_response": ai_response["content"]
                }
            else:
                return {
                    "success": False,
                    "error": ai_response.get("error", "AI调用失败")
                }
                
        except Exception as e:
            error_msg = f"生成测试用例总结时出错: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _build_summary_prompt(self, test_item_name: str, test_cases: List[Dict[str, str]]) -> str:
        """构建测试用例总结提示词"""
        
        # 构建测试用例内容
        test_cases_content = []
        for i, case in enumerate(test_cases, 1):
            input_condition = case.get("input_condition", "").strip()
            test_result = case.get("test_result", "").strip()
            
            if input_condition and test_result:
                test_cases_content.append(f"{test_item_name}({i})\"{input_condition}\"\"{test_result}\"")
        
        test_cases_str = "\n".join(test_cases_content)
        
        # 使用提供的提示词模板
        prompt = f"""现在我正在编写鉴定测评报告的功能性能指标符合性情况对照表，你需要根据我对当前测试项执行的测试用例名称和用例的执行步骤和执行结果进行	
总结(将测试步骤和结果连起来，每个用例分开描述)，表明这个需求的测试过程和结果(分开总结多个用例)
举例说明:	

测试用例包括下列几条:	
制冷到温“步骤1:产品上电，观察屏幕上是否显示制冷到温时间;	
步骤2:等待探测器到温，观察屏幕上是否显示四杆靶图像。”“完成步骤1:画面显示制冷到温时间;
完成步骤2:画面显示四杆靶图像。"	
制冷和制冷到温(不响应NUC关命令)	“步骤1:在制冷计时过程中，通过检测仪软件发送NUC关指令;	
步骤2:监控软件内部是否响应NUC关指令;”完成步骤2:不响应NUC关指令，制冷等待中;	
制冷和制冷到温(不响应两点校正命令)“步骤1:在制冷计时过程中，通过检测仪软件发送两点校正指令

步骤2:监控软件内部是否响应两点校正指令"	完成步骤2:不响应两点校正指令，制冷等待中;	
制冷和制冷到温(不响应十字消隐)“步骤1:在制冷计时过程中，通过检测仪软件发送十字消隐指令;	
步骤2:监控软件内部是否响应两点校正指令”	完成步骤2:不响应十字消隐指令，制冷等待中;	
制冷和制冷到温(不响应读系数命令)“步骤1:在制冷计时过程中，通过检测仪软件发送读系数指令	
步骤2:监控软件内部是否响应两点校正指令”	完成步骤2:不响应读系数指令，制冷等待中	

针对上述5个用例给出的总结测评结果为:	
1.产品上电后观察到屏幕上显示制冷到温时间，等待探测器到温后，观察到屏幕上显示了四杆靶图像	
2.在制冷计时过程中，通过检测仪软件发送NUC关指令，监控到软件内部不响应NUC关指令，并显示制冷等待中;	
3.在制冷计时过程中，通过检测仪软件发送两点校正指令，监控软件内部不响应两点校正指令，并显示制冷等待中;	
4.在制冷计时过程中，通过检测仪软件发送十字消隐指令，监控到软件内部不响应十字消隐指令，并显示制冷等待中;	
5.在制冷计时过程中，通过检测仪软件发送读系数指令，监控软件内部不响应读系数指令，并显示制冷等待中;	

你当前需要总结的测试用例包括下列几条:
{test_cases_str}

你的总结应该逐条将测试步骤和结果连起来顺畅的描述出来即可，不要过多的发挥，并且每一条前面加上1. 2. 3.等序号。不要出现markdown格式。"""
        
        return prompt
    
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