import json
from pathlib import Path

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 配置相关参数
from ..config_utils.config import OLLAMA_HOST, OLLAMA_MODEL

# OCR配置 - 默认使用传统算法
def get_use_traditional_algorithm():
    """获取是否使用传统算法的配置"""
    try:
        from .ocr_config import use_traditional_algorithm
        return use_traditional_algorithm()
    except (ImportError, Exception):
        return True  # 默认使用传统算法

import requests

class DataExtractor:
    def __init__(self, use_traditional_algorithm: bool = None):
        """
        初始化数据提取器
        
        Args:
            use_traditional_algorithm (bool): 是否使用传统算法
                                            None: 从配置文件读取（推荐）
                                            True: 强制使用传统算法（快速、准确）
                                            False: 强制使用AI算法（较慢）
        """  
        # 如果没有指定，从配置文件读取
        if use_traditional_algorithm is None:
            self.use_traditional = get_use_traditional_algorithm()
        else:
            self.use_traditional = use_traditional_algorithm
            
        print(f"正在初始化数据提取器... (模式: {'传统算法' if self.use_traditional else 'AI算法'})")
        log_info(f"正在初始化数据提取器... (模式: {'传统算法' if self.use_traditional else 'AI算法'})", Path(__file__).stem)
        
        self.config = self._load_config()
        
        # 如果使用传统算法，初始化传统提取器
        if self.use_traditional:
            try:
                from .traditional_data_extractor import get_traditional_extractor
                self.traditional_extractor = get_traditional_extractor()
                log_info("传统算法提取器初始化成功", Path(__file__).stem)
            except Exception as e:
                log_error(f"传统算法提取器初始化失败: {e}，回退到AI模式", Path(__file__).stem)
                self.use_traditional = False
        
        print("✓ 数据提取器初始化完成")
        log_info("数据提取器初始化完成", Path(__file__).stem)
    
    def _load_config(self):
        """加载部门-领域-测试人员映射配置"""
        try:
            config_path = Path(__file__).parent / "domain_mapping_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            log_info("成功加载部门-领域映射配置", Path(__file__).stem)
            return config
        except Exception as e:
            log_error(f"加载配置文件失败: {str(e)}", Path(__file__).stem)
            # 返回默认配置
            return {
                "department_to_domain": {
                    "图像部": "光电领域",
                    "光电部": "光电领域", 
                    "激光部": "光电领域",
                    "光电系统一部": "光电领域",
                    "光电系统二部": "光电领域",
                    "光电系统三部": "光电领域",
                    "光电系统四部": "光电领域",
                    "瞄准显示部": "显示领域",
                    "总体部": "火控领域",
                    "重点实验室": "火控领域",
                    "武控部": "外挂领域"
                },
                "domain_personnel": {
                    "光电领域": {"test_manager": "李玲子", "test_personnel": "王凯旋"},
                    "显示领域": {"test_manager": "牛婷婷", "test_personnel": "李岩岩"},
                    "火控领域": {"test_manager": "李佳真", "test_personnel": "王刚"},
                    "外挂领域": {"test_manager": "武慧莹", "test_personnel": "王星"}
                }
            }
    
    def extract_form_data(self, ocr_text: str) -> dict:
        """
        从OCR文本中提取表单数据
        
        Args:
            ocr_text (str): OCR识别的文本
            
        Returns:
            dict: 结构化的表单数据
        """
        try:
            log_info(f"开始从OCR文本提取表单数据，文本长度: {len(ocr_text)}, 使用模式: {'传统算法' if self.use_traditional else 'AI算法'}", Path(__file__).stem)
            
            if self.use_traditional:
                # 使用传统算法提取
                log_info("使用传统算法进行数据提取", Path(__file__).stem)
                return self.traditional_extractor.extract_form_data(ocr_text)
            else:
                # 使用AI算法提取
                log_info("使用AI算法进行数据提取", Path(__file__).stem)
                return self._extract_with_ai(ocr_text)
                
        except Exception as e:
            log_error(f"OCR数据提取失败: {str(e)}", Path(__file__).stem)
            # 返回空结构而不是None
            return {
                "basic_info": {
                    "domain": "",
                    "test_manager": "",
                    "test_personnel": "",
                    "developer": ""
                },
                "optional_info": {
                    "aircraft_model": "",
                    "project_director": "",
                    "development_department": "",
                    "chief_designer": "",
                    "project_manager": "",
                    "component": ""
                }
            }
    
    def _extract_with_ai(self, ocr_text: str) -> dict:
        """使用AI进行数据提取（原有逻辑）"""
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
                    "developer": ""
                },
                "optional_info": {
                    "aircraft_model": "",
                    "project_director": "",
                    "development_department": "",
                    "chief_designer": "",
                    "project_manager": "",
                    "component": ""
                }
            }
    
    def _call_ai_for_extraction(self, text: str) -> dict:
        """调用AI进行数据提取"""
        try:
            # 构建提示词
            prompt = f"""你是一个专业的OCR数据提取专家。请从以下OCR识别的文本中提取软件测试相关的信息，并严格按照JSON格式返回。

OCR文本内容：
{text}

📋 请提取以下字段的信息（如果文本中没有相关信息，请返回空字符串）：

🔤 重要：OCR识别错别字纠正规则（必须执行）
在提取信息前，请先检查和纠正以下常见OCR错别字：

**部门名称错别字纠正**：
- "总体剖" → "总体部"
- "图像剖" → "图像部"  
- "激光剖" → "激光部"
- "光电剖" → "光电部"
- "武控剖" → "武控部"
- "瞄准显示剖" → "瞄准显示部"
- "光电系统—部" → "光电系统一部"
- "光电系统二剖" → "光电系统二部"
- "光电系统三剖" → "光电系统三部"
- "光电系统四剖" → "光电系统四部"
- "重点实验宝" → "重点实验室"
- "重点实验至" → "重点实验室"

**其他常见错别字纠正**：
- "申请^" → "申请人"
- "申请A" → "申请人"
- "申请音门" → "申请部门"
- "申请剖门" → "申请部门"
- "机刑" → "机型"
- "项目主管总帅" → "项目主管总师"
- "项目主管怨师" → "项目主管总师"
- "主任设汁师" → "主任设计师"
- "主任设让师" → "主任设计师"

🎯 纠正策略：
1. 优先查找包含纠正前关键词的文本，自动替换为正确词汇
2. 对于部门名称，特别注意"剖"字通常应该是"部"字
3. 对于人员职位，注意"帅"、"怨师"通常应该是"总师"
4. 如果不确定是否为错别字，保持原文不变

基本信息字段：
• 所属领域 (domain)：留空，将根据申请部门自动推断
• 测试主管 (test_manager)：留空，将根据所属领域自动推断  
• 测试人员 (test_personnel)：留空，将根据所属领域自动推断
• 申请人 (developer)：申请人姓名，仅姓名，如"张三"、"李明"（注意纠正"申请^"为"申请人"）

可选信息字段：
• 机型 (aircraft_model)：飞机型号名称，如"雷霆"、"F-16"、"歼-20"（注意纠正"机刑"为"机型"）
• 项目主管总师 (project_director)：项目总负责人姓名，仅姓名，如"郭伟"、"李总师"（注意纠正"项目主管总帅"、"项目主管怨师"等错别字）
• 申请部门 (development_department)：申请部门名称，这是最关键的字段，必须准确识别！
  常见部门包括：图像部、光电部、激光部、光电系统一部、光电系统二部、光电系统三部、光电系统四部、瞄准显示部、总体部、重点实验室、武控部等
  
  🚨 超重要提取规则（申请部门是推断所属领域的关键）：
  - 🔍 优先查找包含"申请部门"的完整文本行，如"申请部门: 光电系统二部/控制室"
  - 🔍 查找"申请部门:"、"部门:"、"申请单位:"等关键词后的内容
  - 🔤 **必须纠正OCR错别字**：如"总体剖"→"总体部"，"光电系统二剖"→"光电系统二部"
  - 🔍 注意部门名称可能包含"/"分隔的子部门，如"光电系统二部/控制室"，完整保留
  - 🔍 如果"申请部门:"后面紧跟的是部门名称，直接提取，不要省略任何部分
  - 🔍 如果文本分散，尝试拼接相关文本：
    * "光电" + "系统" + "二部" = "光电系统二部"
    * "光电系统" + "二部" + "/控制室" = "光电系统二部/控制室"
  - 🔍 如果只看到部分信息（如"图像"、"激光"），可推断为"图像部"、"激光部"
  
  📋 部门识别优先级：
  1. 完整的"申请部门: XXX"格式 → 直接提取XXX（最高优先级，记得纠错）
  2. 分散的部门关键词 → 尝试拼接
  3. 部分部门信息 → 智能推断完整部门名
• 主任设计师 (chief_designer)：主任设计师姓名，仅姓名，如"李棕恒"、"王设计师"（注意纠正"主任设汁师"等错别字）
• 项目主管 (project_manager)：项目主管姓名，仅姓名，如"张主管"、"李主管"
  
  🚨 项目主管提取特别规则：
  - 优先查找"项目主管:"后的姓名
  - 如果"项目主管:"后面是空行，查找下一行的2-4个中文字符
  - 如果看到"项目主管" "雷飞鸟"分行，识别为project_manager: "雷飞鸟"
  - 如果看到"项目主管 雷飞鸟"（无冒号），识别为project_manager: "雷飞鸟"
  - 注意：不要与"项目主管总师"混淆，"项目主管总师"对应project_director字段
  
• 组件 (component)：组件/产品类型名称，如"转塔"、"对抗告警"、"光电雷达"、"吊舱"、"火控"、"外挂"、"显示"

🔥 关键分离规则 - 请严格遵守：

1. **字段独立性**：每个字段只填写该字段对应的内容，绝对不能包含其他字段的信息
2. **人名vs部门**：人名字段只填人名，部门字段只填部门名称，两者不能混合
3. **连续文本分离**：如果遇到连续文本，必须正确分离各字段

示例分离（重要参考）：
❌ 错误：research_department: "软件测试部主任设计师李棕恒"
✅ 正确：development_department: "软件测试部", chief_designer: "李棕恒"

❌ 错误：project_director: "郭伟研制部门软件测试部"
✅ 正确：project_director: "郭伟", development_department: "软件测试部"

4. **文本解析策略**：
   - 当看到"研制部门软件测试部主任设计师李棕恒"时
   - 识别为：研制部门="软件测试部" + 主任设计师="李棕恒"
   - 当看到"项目总师郭伟研制部门软件测试部"时  
   - 识别为：项目总师="郭伟" + 研制部门="软件测试部"

5. **部门识别特别策略**：
   - 如果看到"申请部门:"后面是空行或其他内容，查找文本中是否有部门相关信息
   - 例如：文本包含"申请部门: \n 图像" -> development_department: "图像部"
   - 例如：文本包含"光电系统" "一部" -> development_department: "光电系统一部" 
   - 例如：文本只有"图像"或"激光" -> 推断为"图像部"或"激光部"

6. **质量检查**：提取完成后，请自检每个字段是否只包含该字段应有的内容

请严格按照以下JSON格式返回，不要添加任何解释或注释：
{{
    "basic_info": {{
        "domain": "",
        "test_manager": "",
        "test_personnel": "",
        "developer": "申请人姓名"
    }},
    "optional_info": {{
        "aircraft_model": "机型",
        "project_director": "项目主管总师姓名",
        "development_department": "申请部门名称", 
        "chief_designer": "主任设计师姓名",
        "project_manager": "项目主管姓名",
        "component": "组件名称"
    }}
}}

/nothink"""
            
            # 构建请求参数
            params = {
                'system': '你是一个专业的OCR数据提取专家，擅长从混合文本中准确分离各个字段。核心原则：1）每个字段绝对独立，不能包含其他字段内容；2）人名字段只填人名，部门字段只填部门名；3）连续文本必须正确分离，如"研制部门软件测试部主任设计师李棕恒"要分离为development_department="软件测试部"和chief_designer="李棕恒"；4）智能纠正OCR识别错别字，特别是"总体剖"→"总体部"、"机刑"→"机型"等常见错误；5）返回标准JSON格式，字段缺失则填空字符串。',
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
                                # 根据申请部门推断领域和测试人员
                                extracted_data = self._infer_domain_and_personnel(extracted_data)
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

    def _correct_department_typos(self, department_name: str) -> str:
        """
        纠正部门名称中的常见错别字。
        
        Args:
            department_name (str): 待纠正的部门名称
            
        Returns:
            str: 纠正后的部门名称
        """
        corrections = {
            "总体剖": "总体部",
            "图像剖": "图像部",
            "激光剖": "激光部",
            "光电剖": "光电部",
            "武控剖": "武控部",
            "瞄准显示剖": "瞄准显示部",
            "光电系统—部": "光电系统一部",
            "光电系统二剖": "光电系统二部",
            "光电系统三剖": "光电系统三部",
            "光电系统四剖": "光电系统四部",
            "重点实验宝": "重点实验室",
            "重点实验至": "重点实验室"
        }
        for wrong, correct in corrections.items():
            if wrong in department_name:
                return department_name.replace(wrong, correct)
        return department_name

    def _infer_domain_and_personnel(self, extracted_data: dict) -> dict:
        """根据申请部门推断所属领域和测试人员"""
        try:
            development_department = extracted_data.get('optional_info', {}).get('development_department', '')
            
            if development_department:
                log_info(f"尝试为申请部门'{development_department}'推断领域", Path(__file__).stem)
                
                # 🔤 兜底处理：在推断前先纠正可能的错别字
                corrected_department = self._correct_department_typos(development_department)
                if corrected_department != development_department:
                    log_info(f"纠正部门名称错别字：'{development_department}' → '{corrected_department}'", Path(__file__).stem)
                    # 更新纠正后的部门名称
                    extracted_data['optional_info']['development_department'] = corrected_department
                    development_department = corrected_department
                
                # 1. 精确匹配
                domain = self.config['department_to_domain'].get(development_department, '')
                
                # 2. 如果精确匹配失败，尝试部分匹配
                if not domain:
                    log_info(f"精确匹配失败，尝试部分匹配", Path(__file__).stem)
                    
                    for config_dept, config_domain in self.config['department_to_domain'].items():
                        # 检查是否包含关键词
                        if config_dept in development_department or development_department in config_dept:
                            domain = config_domain
                            log_info(f"部分匹配成功：'{development_department}' 匹配到 '{config_dept}' -> '{domain}'", Path(__file__).stem)
                            break
                    
                # 3. 如果还是没找到，尝试关键词匹配
                if not domain:
                    log_info(f"部分匹配失败，尝试关键词匹配", Path(__file__).stem)
                    
                    # 光电领域关键词
                    optoelectronic_keywords = ['光电', '图像', '激光', '光电系统']
                    # 显示领域关键词  
                    display_keywords = ['瞄准', '显示']
                    # 火控领域关键词
                    fire_control_keywords = ['总体', '火控', '重点实验室']
                    # 外挂领域关键词
                    external_keywords = ['武控', '外挂']
                    
                    dept_lower = development_department.lower()
                    
                    if any(keyword in development_department for keyword in optoelectronic_keywords):
                        domain = "光电领域"
                        log_info(f"关键词匹配：'{development_department}' -> 光电领域", Path(__file__).stem)
                    elif any(keyword in development_department for keyword in display_keywords):
                        domain = "显示领域"
                        log_info(f"关键词匹配：'{development_department}' -> 显示领域", Path(__file__).stem)
                    elif any(keyword in development_department for keyword in fire_control_keywords):
                        domain = "火控领域"
                        log_info(f"关键词匹配：'{development_department}' -> 火控领域", Path(__file__).stem)
                    elif any(keyword in development_department for keyword in external_keywords):
                        domain = "外挂领域"
                        log_info(f"关键词匹配：'{development_department}' -> 外挂领域", Path(__file__).stem)
                
                if domain:
                    # 设置所属领域
                    extracted_data['basic_info']['domain'] = domain
                    
                    # 根据领域设置测试主管和测试人员
                    personnel = self.config['domain_personnel'].get(domain, {})
                    if personnel:
                        extracted_data['basic_info']['test_manager'] = personnel.get('test_manager', '')
                        extracted_data['basic_info']['test_personnel'] = personnel.get('test_personnel', '')
                        
                    log_info(f"✅ 成功推断 - 申请部门：'{development_department}' → 领域：'{domain}' → 测试主管：{personnel.get('test_manager', '')} → 测试人员：{personnel.get('test_personnel', '')}", Path(__file__).stem)
                else:
                    log_warning(f"❌ 所有匹配策略都失败，无法为申请部门'{development_department}'推断领域", Path(__file__).stem)
            else:
                log_warning("❌ 未提取到申请部门信息，无法推断领域和测试人员", Path(__file__).stem)
                
        except Exception as e:
            log_error(f"推断领域和测试人员失败: {str(e)}", Path(__file__).stem)
            
        return extracted_data

# 全局数据提取器实例（延迟加载）
_data_extractor = None

def get_data_extractor():
    """获取全局数据提取器实例（延迟加载）"""
    global _data_extractor
    if _data_extractor is None:
        log_info("正在创建数据提取器实例...", "data_extractor")
        try:
            _data_extractor = DataExtractor()
            log_info("数据提取器实例创建成功", "data_extractor")
        except Exception as e:
            log_error(f"创建数据提取器实例失败: {str(e)}", "data_extractor")
            raise
    return _data_extractor

# 数据提取器代理类，实现延迟加载
class _DataExtractorProxy:
    """数据提取器代理类，实现延迟加载"""
    def __init__(self):
        self._real_extractor = None
    
    def _get_real_extractor(self):
        """获取真实的数据提取器实例"""
        if self._real_extractor is None:
            self._real_extractor = get_data_extractor()
        return self._real_extractor
    
    def __getattr__(self, name):
        real_extractor = self._get_real_extractor()
        return getattr(real_extractor, name)
        
    def __call__(self, *args, **kwargs):
        real_extractor = self._get_real_extractor()
        return real_extractor(*args, **kwargs)

# 创建全局代理对象
data_extractor = _DataExtractorProxy() 