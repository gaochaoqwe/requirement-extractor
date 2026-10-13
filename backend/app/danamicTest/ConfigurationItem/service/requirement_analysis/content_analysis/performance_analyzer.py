"""
性能需求AI分析器
使用AI分析性能需求章节内容，识别余量测试项和性能测试项
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
import requests
from ....utils.logging_utils.logger import log_info, log_warning, log_error, log_debug

# 引入在线大模型配置
from ....utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL


class PerformanceAIAnalyzer:
    """性能需求AI分析器"""
    
    def __init__(self):
        self.logger_name = "performance_ai_analyzer"
        
        # 默认的余量测试项定义（扩展关键词和别名）
        self.default_allowance_tests = {
            "DDR内存余量": {
                "keywords": ["内存", "DDR", "RAM", "SDRAM", "动态内存", "随机存取存储器", "内存空间", "内存占用", "内存使用率", "内存资源"],
                "description": "DDR内存余量测试：测试软件运行时DDR内存的使用情况，确保内存余量满足要求（通常>30%）",
                "aliases": ["DDR余量", "内存余量", "RAM余量", "动态内存余量", "系统内存余量"]
            },
            "FLASH内存余量": {
                "keywords": ["FLASH", "闪存", "存储器", "存储", "Flash", "NOR", "NAND", "程序存储器", "代码存储", "固化存储", "非易失性存储", "存储空间", "存储占用"],
                "description": "FLASH内存余量测试：测试软件代码和数据在FLASH存储器中的占用情况，确保存储余量满足要求（通常>30%）",
                "aliases": ["FLASH余量", "闪存余量", "存储余量", "程序存储余量", "代码存储余量", "固化存储余量"]
            },
            "CPU余量": {
                "keywords": ["CPU", "处理器", "运行时间", "处理时间", "计算", "运算", "执行时间", "处理能力", "计算资源", "处理负载", "CPU占用率", "处理器负载"],
                "description": "CPU余量测试：测试软件运行时CPU的使用情况和处理能力，确保CPU余量满足要求（通常>30%）",
                "aliases": ["CPU余量", "处理器余量", "计算余量", "运算余量", "处理能力余量", "计算资源余量"]
            }
        }
    
    def analyze_performance_requirements(self, chapter_content: str, chapter_info: Dict[str, str]) -> Dict[str, Any]:
        """
        分析性能需求章节内容，提取余量测试项和性能测试项
        
        Args:
            chapter_content: 性能需求章节内容
            chapter_info: 章节信息（编号、标题等）
            
        Returns:
            包含余量测试项和性能测试项的分析结果
        """
        try:
            log_info("开始AI分析性能需求内容", self.logger_name)
            log_debug(f"章节信息: {chapter_info}", self.logger_name)
            log_debug(f"内容长度: {len(chapter_content)} 字符", self.logger_name)
            
            if not chapter_content.strip():
                log_warning("性能需求章节内容为空", self.logger_name)
                return self._create_empty_result()
            
            # 使用AI分析内容
            ai_result = self._analyze_with_ai(chapter_content, chapter_info)
            
            if not ai_result:
                log_warning("AI分析失败，使用规则分析", self.logger_name)
                ai_result = self._analyze_with_rules(chapter_content, chapter_info)
            
            # 处理分析结果
            result = self._process_analysis_result(ai_result, chapter_info)
            
            log_info(f"性能需求分析完成: {len(result.get('allowance_tests', []))}个余量测试项, {len(result.get('performance_tests', []))}个性能测试项", self.logger_name)
            
            return result
            
        except Exception as e:
            log_error(f"性能需求分析失败: {e}", self.logger_name)
            import traceback
            log_error(f"详细错误: {traceback.format_exc()}", self.logger_name)
            return self._create_empty_result()
    
    def _analyze_with_ai(self, content: str, chapter_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        使用AI分析性能需求内容
        
        Args:
            content: 性能需求内容
            chapter_info: 章节信息
            
        Returns:
            AI分析结果，失败返回None
        """
        try:
            log_info("开始调用AI分析性能需求", self.logger_name)
            
            # 构建提示词
            prompt = self._build_analysis_prompt(content, chapter_info)
            
            # 🔧 记录完整的提示词
            log_info(f"[AI_PROMPT_FULL] 完整提示词:\n{prompt}", self.logger_name)
            
            # 调用OLLAMA API
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            log_debug(f"发送AI请求: {OLLAMA_HOST}/api/generate", self.logger_name)
            log_debug(f"使用模型: {OLLAMA_MODEL}", self.logger_name)
            
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                log_warning(f"AI请求失败，状态码: {response.status_code}", self.logger_name)
                return None
            
            result_text = response.json().get('response', '').strip()
            
            # 🔧 记录完整的AI响应
            log_info(f"[AI_RESPONSE_FULL] 完整AI响应:\n{result_text}", self.logger_name)
            log_debug(f"AI返回内容前200字符: {result_text[:200]}", self.logger_name)
            
            # 解析AI返回的JSON结果
            ai_result = self._parse_ai_response(result_text)
            
            if ai_result:
                log_info("AI分析成功", self.logger_name)
                # 🔧 记录解析后的结果结构
                log_info(f"[AI_PARSED_RESULT] 解析结果: 余量测试项={len(ai_result.get('allowance_tests', []))}个, 性能测试项={len(ai_result.get('performance_tests', []))}个", self.logger_name)
                return ai_result
            else:
                log_warning("AI返回结果解析失败", self.logger_name)
                return None
                
        except Exception as e:
            log_warning(f"AI分析出错: {e}", self.logger_name)
            import traceback
            log_warning(f"AI分析详细错误: {traceback.format_exc()}", self.logger_name)
            return None
    
    def _build_analysis_prompt(self, content: str, chapter_info: Dict[str, str]) -> str:
        """
        构建AI分析的提示词
        
        Args:
            content: 性能需求内容
            chapter_info: 章节信息
            
        Returns:
            完整的提示词
        """
        # 构建余量测试项的详细说明
        allowance_details = []
        for name, info in self.default_allowance_tests.items():
            keywords_str = "、".join(info["keywords"])
            aliases_str = "、".join(info["aliases"])
            detail = f"""   {name}：
     - 定义：{info["description"]}
     - 关键词：{keywords_str}
     - 别名：{aliases_str}"""
            allowance_details.append(detail)
        
        allowance_section = "\n".join(allowance_details)
        
        # 🔧 新增：余量测试项的默认模板，供AI参考
        allowance_templates = """
余量测试项默认模板（供AI参考，需要根据实际需求用词调整）：

DDR内存余量模板：
- 测试描述模板：1测试软件的DDR内存余量是否满足需求大于30%的要求
- 测试方法模板：1查看软件DDR存储空间的大小，以及软件编译后的软件的大小，两者相除，即为DDR空间的占有率，用1减去这个数即为软件的DDR存储余量

FLASH内存余量模板：
- 测试描述模板：1测试软件的FLASH内存余量是否满足需求大于30%的要求
- 测试方法模板：1软件通过代码审查计算软件，运行时需要占用的flash内存的大小，然后与FLASH的内存相除，用1减去这个数即为软件的FLASH存储余量

CPU余量模板：
- 测试描述模板：1测试软件的CPU运行余量是否满足需求大于30%的要求
- 测试方法模板：1软件正常运行，通过调试计算机中软件编译环境的内存监控功能查看软件的运行余量是否大于30%

注意：AI需要根据原文中的实际用词调整模板，例如：
- 如果原文用"存储器"，则将模板中的"FLASH"替换为"存储器"
- 如果原文用"处理器"，则将模板中的"CPU"替换为"处理器"
- 如果原文用"剩余率"，则将模板中的"余量"替换为"剩余率"
- 百分比数值要根据原文中的具体数值调整
- **重要：测试描述和测试方法都必须以数字开头（如：1测试xxx、1通过xxx），即使只有一条内容也要加上编号**
"""
        
        prompt = f"""你是软件测试需求分析专家。请分析以下性能需求内容，提取余量测试项和性能测试项。

章节信息：
标题：{chapter_info.get('chapter_title', '')}
编号：{chapter_info.get('chapter_number', '')}

性能需求内容：
{content}

余量测试项详细说明：
{allowance_section}

{allowance_templates}

分析要求：
1. 余量测试项分析：
   - 余量测试项只有且仅有上述3类：DDR内存余量、FLASH内存余量、CPU余量
   - 根据定义、关键词和别名，判断性能需求内容中哪些条目对应这3类余量测试项
   - 注意识别各种表述方式，如"内存占用率"、"存储空间使用"、"处理器负载"等
   - 对于每个余量测试项，在match_reason中说明匹配判断的原因：
     * 如果matched为true：说明在原文中找到了哪些关键词或表述，引用具体内容
     * 如果matched为false：说明为什么没有找到相关内容，缺少哪些关键词
   - 🔧 新增：对于matched为true的余量测试项，需要生成测试描述和测试方法：
     * 参考上述默认模板，但必须根据原文中的实际用词进行调整
     * 例如：原文用"存储器"就用"存储器"，不要用"FLASH"
     * 百分比数值要与原文保持一致
   - 重要：除了这3类余量测试项外，其他所有内容都应归类为性能测试项

2. 性能测试项分析：
   - 除上述3类余量测试相关的条目外，其他所有性能需求条目都归类为性能测试项
   - 包括但不限于：响应时间、吞吐量、并发性能、实时性要求、定时器性能、中断响应等
   - 每个性能测试项要单独列出，不要合并
   - 性能测试项名称要贴近原文的性能描述，通过名称就能看出测试的具体性能指标
   - 为每个性能测试项提供：测试项名称、需求描述、测试项描述、测试方法

请严格按照以下JSON格式返回结果：
{{
    "allowance_tests": [
        {{
            "name": "余量测试项名称",
            "matched": true,
            "match_reason": "匹配原因（说明为什么判断为true或false，引用原文关键词）",
            "extracted_requirement": "从原文中提取的与该余量测试项相关的具体需求内容（仅在matched为true时提供）",
            "test_description": "测试项描述（参考默认模板，但根据原文用词调整，仅在matched为true时提供）",
            "test_method": "测试方法（参考默认模板，但根据原文用词调整，仅在matched为true时提供）"
        }}
    ],
    "performance_tests": [
        {{
            "name": "具体的性能测试项名称（贴近原文描述）",
            "requirement_description": "从原文提取的需求描述",
            "test_description": "测试项描述（说明测试什么）",
            "test_method": "测试方法（说明如何测试）"
        }}
    ]
}}

注意：
- 只返回JSON格式，不要添加其他解释文字
- match_reason要具体说明判断依据，引用原文关键词或说明缺失原因
- 余量测试项只有3类，其他都是性能测试项
- 🔧 新增：对于matched为true的余量测试项，必须提供test_description和test_method字段
- 余量测试项的test_description和test_method要参考默认模板，但根据原文实际用词调整
- 例如：原文用"存储器剩余率不小于30%"，则测试描述应为"1测试软件的存储器剩余率是否满足需求不小于30%的要求"
- 性能测试项名称要具体明确，如"定时器中断周期性能测试"、"系统响应时间测试"等
- 每个性能测试项都要包含完整的4个字段：name、requirement_description、test_description、test_method
- 多个性能测试项要分别列出，不要合并
- **重要：所有测试项的test_description和test_method都必须以数字开头（如：1测试xxx、1通过xxx），即使只有一条内容也要加上编号**"""

        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        解析AI返回的JSON响应
        
        Args:
            response_text: AI返回的文本
            
        Returns:
            解析后的字典，失败返回None
        """
        try:
            # 🔧 记录开始解析
            log_debug(f"[AI_PARSE] 开始解析AI响应，长度: {len(response_text)} 字符", self.logger_name)
            
            # 🔧 新增：处理<think>标签，移除思考过程
            cleaned_response = response_text
            if "<think>" in response_text and "</think>" in response_text:
                # 移除<think>...</think>标签及其内容
                import re
                cleaned_response = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
                log_debug(f"[AI_PARSE] 移除<think>标签后的响应长度: {len(cleaned_response)}", self.logger_name)
            
            # 🔧 新增：尝试提取JSON内容（处理```json标记）
            json_content = cleaned_response
            if "```json" in cleaned_response and "```" in cleaned_response[cleaned_response.index("```json")+7:]:
                start_idx = cleaned_response.index("```json") + 7  # 跳过```json
                end_idx = cleaned_response.rindex("```")
                json_content = cleaned_response[start_idx:end_idx].strip()
                log_debug(f"[AI_PARSE] 从```json标记中提取JSON，长度: {len(json_content)}", self.logger_name)
            elif "{" in cleaned_response and "}" in cleaned_response:
                # 提取JSON对象
                start_idx = cleaned_response.index("{")
                end_idx = cleaned_response.rindex("}") + 1
                json_content = cleaned_response[start_idx:end_idx].strip()
                log_debug(f"[AI_PARSE] 提取JSON对象，长度: {len(json_content)}", self.logger_name)
            
            # 尝试解析JSON
            result = json.loads(json_content)
            
            # 验证结果格式
            if not isinstance(result, dict):
                log_warning("AI返回结果不是字典格式", self.logger_name)
                return None
                
            if 'allowance_tests' not in result or 'performance_tests' not in result:
                log_warning("AI返回结果缺少必要字段", self.logger_name)
                # 🔧 记录实际包含的字段
                log_warning(f"[AI_PARSE] 实际字段: {list(result.keys())}", self.logger_name)
                return None
            
            # 🔧 记录详细的解析结果
            allowance_count = len(result.get('allowance_tests', []))
            performance_count = len(result.get('performance_tests', []))
            log_debug(f"AI结果解析成功: {allowance_count}个余量项, {performance_count}个性能项", self.logger_name)
            
            # 🔧 记录每个测试项的名称
            if allowance_count > 0:
                allowance_names = [item.get('name', '未知') for item in result['allowance_tests']]
                log_info(f"[AI_PARSE] 余量测试项: {allowance_names}", self.logger_name)
            
            if performance_count > 0:
                performance_names = [item.get('name', '未知') for item in result['performance_tests']]
                log_info(f"[AI_PARSE] 性能测试项: {performance_names}", self.logger_name)
            
            return result
            
        except json.JSONDecodeError as e:
            log_warning(f"AI返回结果JSON解析失败: {e}", self.logger_name)
            # 🔧 记录JSON解析失败的具体位置
            log_warning(f"[AI_PARSE] JSON错误位置: 行{getattr(e, 'lineno', '未知')}, 列{getattr(e, 'colno', '未知')}", self.logger_name)
            
            # 尝试提取JSON部分（备用方案）
            log_info("[AI_PARSE] 尝试从响应中提取JSON片段", self.logger_name)
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                try:
                    extracted_json = json_match.group()
                    log_debug(f"[AI_PARSE] 提取到JSON片段，长度: {len(extracted_json)} 字符", self.logger_name)
                    result = json.loads(extracted_json)
                    log_info("从AI响应中提取JSON成功", self.logger_name)
                    return result
                except Exception as extract_error:
                    log_warning(f"[AI_PARSE] JSON片段解析也失败: {extract_error}", self.logger_name)
            else:
                log_warning("[AI_PARSE] 未找到JSON格式的内容", self.logger_name)
            
            return None
            
        except Exception as e:
            log_warning(f"解析AI响应时出错: {e}", self.logger_name)
            # 🔧 记录详细错误
            import traceback
            log_warning(f"[AI_PARSE] 解析错误详情: {traceback.format_exc()}", self.logger_name)
            return None
    
    def _analyze_with_rules(self, content: str, chapter_info: Dict[str, str]) -> Dict[str, Any]:
        """
        使用规则分析性能需求内容（AI失败时的备用方案）
        
        Args:
            content: 性能需求内容
            chapter_info: 章节信息
            
        Returns:
            规则分析结果
        """
        log_info("使用规则分析性能需求内容", self.logger_name)
        
        allowance_tests = []
        performance_requirements = []
        
        # 按行分析内容
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # 跳过空行和过短的行
                continue
            
            # 检查是否匹配余量测试项
            matched_allowance = None
            for allowance_name, allowance_info in self.default_allowance_tests.items():
                for keyword in allowance_info['keywords']:
                    if keyword in line:
                        matched_allowance = allowance_name
                        break
                if matched_allowance:
                    break
            
            if matched_allowance:
                allowance_tests.append({
                    'name': matched_allowance,
                    'matched': True,
                    'match_reason': f'规则匹配：在内容"{line}"中找到关键词"{keyword}"'
                })
            else:
                # 不匹配余量测试的归类为性能测试
                performance_requirements.append(line)
        
        # 为未匹配的余量测试项添加记录
        matched_names = [test['name'] for test in allowance_tests]
        for allowance_name in self.default_allowance_tests:
            if allowance_name not in matched_names:
                allowance_tests.append({
                    'name': allowance_name,
                    'matched': False,
                    'match_reason': f'规则分析：在性能需求内容中未找到与{allowance_name}相关的关键词'
                })
        
        # 整合性能测试项
        performance_tests = []
        if performance_requirements:
            performance_tests.append({
                'name': '系统性能测试',
                'requirement_description': '；'.join(performance_requirements)
            })
        
        result = {
            'allowance_tests': allowance_tests,
            'performance_tests': performance_tests
        }
        
        log_info(f"规则分析完成: {len(allowance_tests)}个余量项, {len(performance_tests)}个性能项", self.logger_name)
        return result
    
    def _process_analysis_result(self, ai_result: Dict[str, Any], chapter_info: Dict[str, str]) -> Dict[str, Any]:
        """
        处理分析结果，生成标准格式的测试项
        
        Args:
            ai_result: AI或规则分析的结果
            chapter_info: 章节信息
            
        Returns:
            处理后的结果
        """
        try:
            processed_result = {
                'allowance_tests': [],
                'performance_tests': [],
                'source_chapter': chapter_info
            }
            
            # 处理余量测试项
            for allowance_item in ai_result.get('allowance_tests', []):
                if allowance_item.get('matched', False):
                    # 🔧 关键修改：确保extracted_requirement字段能够正确传递
                    extracted_requirement = allowance_item.get('extracted_requirement', allowance_item.get('requirement_description', ''))
                    # 🔧 新增：传递AI生成的测试描述和方法
                    ai_test_description = allowance_item.get('test_description', '')
                    ai_test_method = allowance_item.get('test_method', '')
                    
                    processed_result['allowance_tests'].append({
                        'name': allowance_item['name'],
                        'requirement_description': extracted_requirement,  # 使用提取的具体需求内容
                        'extracted_requirement': extracted_requirement,  # 🔧 新增：保留原始提取内容
                        'test_description': ai_test_description,  # 🔧 新增：AI生成的测试描述
                        'test_method': ai_test_method,  # 🔧 新增：AI生成的测试方法
                        'source': 'performance_chapter',
                        'chapter_number': chapter_info.get('chapter_number', ''),
                        'chapter_title': chapter_info.get('chapter_title', ''),
                        'match_reason': allowance_item.get('match_reason', '')  # 保留匹配原因
                    })
            
            # 处理性能测试项
            for performance_item in ai_result.get('performance_tests', []):
                processed_result['performance_tests'].append({
                    'name': performance_item['name'],
                    'requirement_description': performance_item.get('requirement_description', ''),
                    'test_description': performance_item.get('test_description', ''),  # 🔧 新增：传递AI生成的测试描述
                    'test_method': performance_item.get('test_method', ''),  # 🔧 新增：传递AI生成的测试方法
                    'source': 'performance_chapter',
                    'chapter_number': chapter_info.get('chapter_number', ''),
                    'chapter_title': chapter_info.get('chapter_title', '')
                })
            
            return processed_result
            
        except Exception as e:
            log_error(f"处理分析结果时出错: {e}", self.logger_name)
            return self._create_empty_result()
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """
        创建空的分析结果
        
        Returns:
            空的结果字典
        """
        return {
            'allowance_tests': [],
            'performance_tests': [],
            'source_chapter': {}
        } 