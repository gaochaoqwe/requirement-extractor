import json
from pathlib import Path
import requests

# 导入日志模块
from ..logging_utils.logger import log_info, log_error, log_warning

# 导入配置
try:
    from ..config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
except ImportError:
    # 默认配置
    OLLAMA_HOST = "http://localhost:11434"
    OLLAMA_MODEL = "qwen3:0.6b"

class DataExtractor:
    def __init__(self):
        """初始化数据提取器"""
        pass

    def extract_form_data(self, ocr_text: str) -> dict:
        """
        从OCR文本中提取表单数据
        
        Args:
            ocr_text (str): OCR识别的文本
            
        Returns:
            dict: 结构化的表单数据
        """
        try:
            log_info(f"开始从OCR文本提取回归测试表单数据，文本长度: {len(ocr_text)}", Path(__file__).stem)

            # 调用AI进行数据结构化
            structured_data = self._call_ai_for_extraction(ocr_text)

            if structured_data:
                log_info(f"AI数据提取成功: {structured_data}", Path(__file__).stem)
                return structured_data
            else:
                # AI提取失败，返回空结构
                log_warning("AI提取失败，返回空数据结构", Path(__file__).stem)
                return {
                    "basic_info": {
                        "domain": "",
                        "test_manager": "",
                        "test_personnel": "",
                        "developer": "",
                        "software_name": "",
                        "software_version": "",
                        "software_id": ""
                    },
                    "optional_info": {
                        "aircraft_model": "",
                        "project_director": "",
                        "development_department": "",
                        "chief_designer": ""
                    }
                }

        except Exception as e:
            log_error(f"OCR数据提取失败: {str(e)}", Path(__file__).stem)
            # 返回空结构而不是None
            return {
                "basic_info": {
                    "domain": "",
                    "test_manager": "",
                    "test_personnel": "",
                    "developer": "",
                    "software_name": "",
                    "software_version": "",
                    "software_id": ""
                },
                "optional_info": {
                    "aircraft_model": "",
                    "project_director": "",
                    "development_department": "",
                    "chief_designer": ""
                }
            }

    def _call_ai_for_extraction(self, text: str) -> dict:
        """调用AI进行数据提取"""
        try:
            # 构建提示词
            prompt = f"""你是一个专业的OCR数据提取专家。请从以下OCR识别的文本中提取软件回归测试相关的信息，并严格按照JSON格式返回。

OCR文本内容：
{text}

📋 请提取以下字段的信息（如果文本中没有相关信息，请返回空字符串）：

基本信息字段：
• 所属领域 (domain)：软件技术领域，如"光电领域"、"嵌入式软件"、"Web应用"等
• 测试主管 (test_manager)：负责回归测试的主管姓名，仅姓名，如"高超"、"张三"
• 测试人员 (test_personnel)：具体回归测试人员姓名，仅姓名，如"李四"、"王五"
• 开发人员 (developer)：软件开发人员姓名，仅姓名，如"张三"、"李明"
• 软件名称 (software_name)：软件完整名称，如"雷达探测系统运动控制"
• 软件版本 (software_version)：版本号，如"2.00"、"1.0.0"、"V3.1"
• 软件标识 (software_id)：软件标识符，如"LDKZRJ"、"SYS001"

可选信息字段：
• 飞机型号 (aircraft_model)：飞机型号名称，如"雷霆"、"F-16"、"歼-20"
• 项目总师 (project_director)：项目总负责人姓名，仅姓名，如"郭伟"、"李总师"
• 研制部门 (development_department)：研制部门名称，如"软件测试部"、"软件开发部"、"技术部"
• 主任设计师 (chief_designer)：主任设计师姓名，仅姓名，如"李棕恒"、"王设计师"

🔥 关键分离规则 - 请严格遵守：

1. **字段独立性**：每个字段只填写该字段对应的内容，绝对不能包含其他字段的信息
2. **人名vs部门**：人名字段只填人名，部门字段只填部门名称，两者不能混合
3. **连续文本分离**：如果遇到连续文本，必须正确分离各字段

示例分离（重要参考）：
❌ 错误：development_department: "软件测试部主任设计师李棕恒"
✅ 正确：development_department: "软件测试部", chief_designer: "李棕恒"

❌ 错误：project_director: "郭伟研制部门软件测试部"
✅ 正确：project_director: "郭伟", development_department: "软件测试部"

4. **文本解析策略**：
   - 当看到"研制部门软件测试部主任设计师李棕恒"时
   - 识别为：研制部门="软件测试部" + 主任设计师="李棕恒"
   - 当看到"项目总师郭伟研制部门软件测试部"时
   - 识别为：项目总师="郭伟" + 研制部门="软件测试部"

5. **质量检查**：提取完成后，请自检每个字段是否只包含该字段应有的内容

请严格按照以下JSON格式返回，不要添加任何解释或注释：
{{
    "basic_info": {{
        "domain": "所属领域",
        "test_manager": "测试主管姓名",
        "test_personnel": "测试人员姓名",
        "developer": "开发人员姓名",
        "software_name": "软件名称",
        "software_version": "软件版本",
        "software_id": "软件标识"
    }},
    "optional_info": {{
        "aircraft_model": "飞机型号",
        "project_director": "项目总师姓名",
        "development_department": "研制部门名称",
        "chief_designer": "主任设计师姓名"
    }}
}}

/nothink"""

            # 构建请求参数
            params = {
                'system': '你是一个专业的OCR数据提取专家，擅长从混合文本中准确分离各个字段。核心原则：1）每个字段绝对独立，不能包含其他字段内容；2）人名字段只填人名，部门字段只填部门名；3）连续文本必须正确分离，如"研制部门软件测试部主任设计师李棕恒"要分离为development_department="软件测试部"和chief_designer="李棕恒"；4）返回标准JSON格式，字段缺失则填空字符串。',
                'prompt': prompt,
                'model': OLLAMA_MODEL,
                'stream': False
            }

            max_loop = 3  # 设置最大重试次数为 3 次

            while max_loop > 0:
                try:
                    log_info(f"正在调用AI提取数据，剩余重试次数: {max_loop}", Path(__file__).stem)

                    # 发送请求到Ollama
                    res = requests.post(url=f'{OLLAMA_HOST}/api/generate', json=params, verify=False, timeout=30)

                    if res.status_code == 200:
                        response_text = res.json()["response"]
                        log_info(f"AI响应原始内容: {response_text}", Path(__file__).stem)

                        # 过滤think标签内容
                        if response_text:
                            # 查找最后一个</think>标签的位置
                            last_think_end_tag_index = response_text.rfind("</think>")
                            if last_think_end_tag_index != -1:
                                # 提取</think>标签之后的内容
                                response_text = response_text[last_think_end_tag_index + len("</think>"):]
                                response_text = response_text.lstrip()  # 去除左侧空白字符

                        # 尝试解析JSON
                        # 清理响应文本，移除可能的markdown格式
                        cleaned_response = response_text.strip()
                        if cleaned_response.startswith("```json"):
                            cleaned_response = cleaned_response[7:]
                        if cleaned_response.endswith("```"):
                            cleaned_response = cleaned_response[:-3]
                        cleaned_response = cleaned_response.strip()

                        # 尝试解析JSON
                        try:
                            extracted_data = json.loads(cleaned_response)

                            # 验证返回的数据结构
                            if 'basic_info' in extracted_data and 'optional_info' in extracted_data:
                                log_info(f"AI成功提取数据: {extracted_data}", Path(__file__).stem)
                                return extracted_data
                            else:
                                log_warning(f"AI返回的JSON结构不正确: {extracted_data}", Path(__file__).stem)

                        except json.JSONDecodeError as e:
                            log_warning(f"AI响应JSON解析失败: {e}, 原始响应: {cleaned_response}", Path(__file__).stem)
                    else:
                        log_error(f"AI API请求失败，状态码: {res.status_code}", Path(__file__).stem)

                except Exception as e:
                    log_error(f"AI数据提取时发生错误: {str(e)}", Path(__file__).stem)

                max_loop -= 1

            return None

        except Exception as e:
            log_error(f"调用AI提取数据失败: {str(e)}", Path(__file__).stem)
            return None

# 全局数据提取器实例（延迟加载）
_data_extractor = None

def get_data_extractor():
    """获取全局数据提取器实例（延迟加载）"""
    global _data_extractor
    if _data_extractor is None:
        _data_extractor = DataExtractor()
    return _data_extractor

# 向后兼容的代理类
class _DataExtractorProxy:
    """数据提取器代理类，实现延迟加载"""
    def __getattr__(self, name):
        real_extractor = get_data_extractor()
        return getattr(real_extractor, name)
        
    def __call__(self, *args, **kwargs):
        real_extractor = get_data_extractor()
        return real_extractor(*args, **kwargs)

# 设置data_extractor为代理对象
data_extractor = _DataExtractorProxy() 