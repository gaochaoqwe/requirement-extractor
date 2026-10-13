"""
环境信息提取器

从需求规格说明文档中智能提取开发环境和运行环境信息。
通过关键词匹配和AI分析，准确识别开发工具和硬件平台信息。
优先使用标准化文档的3.9章节内容进行分析。
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from docx import Document

# 导入任务日志函数
from ....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

# 配置日志
logger = logging.getLogger(__name__)

class EnvironmentExtractor:
    """环境信息提取器"""
    
    def __init__(self):
        """初始化环境信息提取器"""
        self.logger = logger
        self.development_keywords = self._get_development_keywords()
        self.runtime_keywords = self._get_runtime_keywords()
        
    def _get_development_keywords(self) -> List[str]:
        """获取开发环境关键词列表"""
        return [
            # 开发工具
            'acoreide', 'acore ide', 'workbench', 'css', 
            'code composer studio', 'ccs', 'iar', 'keil',
            'visual studio', 'eclipse', 'qtcreator',
            'dev-cpp', 'codeblocks', 'clion'
        ]
    
    def _get_runtime_keywords(self) -> List[str]:
        """获取运行环境关键词列表"""
        return [
            # 硬件平台和操作系统
            '天脉3', '天脉', 'tianmai3', 'tianmai', 
            '飞腾', '飞腾2000', 'phytium', 'ft2000',
            'powerpc', 'vxwork', 'vxworks', 
            'dsp', 'dsp2812', 'dsp6657', 'dsp2833',
            'arm', 'cortex', 'stm32', 'ti', 'texas instruments',
            'linux', 'windows', 'rtos', 'freertos'
        ]
    
    def extract_environment_info(
        self, 
        requirement_doc_content: str,
        ai_analysis_function: Optional[callable] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        从需求文档中提取环境信息
        
        Args:
            requirement_doc_content: 需求文档内容
            ai_analysis_function: AI分析函数（可选）
            session_id: 会话ID，用于查找标准化文档（可选）
            
        Returns:
            Dict[str, str]: 包含development_environment和runtime_environment的字典
        """
        try:
            log_info("开始提取环境信息", "environment_extractor")
            
            # 🔧 新增：优先尝试从标准化文档提取3.9章节内容
            standardized_content = None
            if session_id:
                standardized_content = self._extract_from_standardized_document(session_id)
            
            # 选择要分析的内容
            if standardized_content:
                log_info("使用标准化文档的3.9章节内容进行环境分析", "environment_extractor")
                analysis_content = standardized_content
                log_debug(f"标准化文档3.9章节内容长度: {len(analysis_content)} 字符", "environment_extractor")
            else:
                log_info("未找到标准化文档，使用原始文档内容", "environment_extractor")
                analysis_content = requirement_doc_content
                log_debug(f"原始需求文档内容长度: {len(analysis_content)} 字符", "environment_extractor")
            
            log_debug(f"AI分析函数: {'已提供' if ai_analysis_function else '未提供'}", "environment_extractor")
            
            # 第一步：关键词匹配和上下文提取
            log_debug("开始提取开发环境关键词上下文", "environment_extractor")
            dev_contexts = self._extract_keyword_contexts(
                analysis_content, 
                self.development_keywords,
                "开发环境"
            )
            log_info(f"开发环境关键词匹配结果: 找到 {len(dev_contexts)} 个匹配", "environment_extractor")
            
            log_debug("开始提取运行环境关键词上下文", "environment_extractor")
            runtime_contexts = self._extract_keyword_contexts(
                analysis_content, 
                self.runtime_keywords,
                "运行环境"
            )
            log_info(f"运行环境关键词匹配结果: 找到 {len(runtime_contexts)} 个匹配", "environment_extractor")
            
            # 第二步：使用AI分析上下文（如果提供了AI函数）
            development_environment = "AcoreIde"  # 默认值
            runtime_environment = "飞腾2000（天脉3）"  # 默认值
            
            log_debug(f"初始默认值 - 开发环境: {development_environment}, 运行环境: {runtime_environment}", "environment_extractor")
            
            if ai_analysis_function:
                # 🔧 优化：无论是否找到关键词，都使用AI分析整个3.9章节内容
                log_info("使用AI分析环境信息", "environment_extractor")
                ai_result = self._analyze_with_ai(
                    dev_contexts, runtime_contexts, ai_analysis_function, analysis_content
                )
                if ai_result:
                    log_info(f"AI分析结果: {ai_result}", "environment_extractor")
                    development_environment = ai_result.get('development_environment', development_environment)
                    runtime_environment = ai_result.get('runtime_environment', runtime_environment)
                    log_info(f"AI更新后 - 开发环境: {development_environment}, 运行环境: {runtime_environment}", "environment_extractor")
                else:
                    log_warning("AI分析返回空结果", "environment_extractor")
            else:
                log_debug("未提供AI分析函数，使用基于规则的匹配", "environment_extractor")
                
                # 第三步：基于规则的智能匹配
                if dev_contexts:
                    log_debug("使用规则匹配开发环境", "environment_extractor")
                    development_environment = self._smart_match_development(dev_contexts)
                    log_info(f"规则匹配开发环境结果: {development_environment}", "environment_extractor")
                
                if runtime_contexts:
                    log_debug("使用规则匹配运行环境", "environment_extractor")
                    runtime_environment = self._smart_match_runtime(runtime_contexts)
                    log_info(f"规则匹配运行环境结果: {runtime_environment}", "environment_extractor")
            
            result = {
                'development_environment': development_environment,
                'runtime_environment': runtime_environment
            }
            
            log_info(f"环境信息提取完成: {result}", "environment_extractor")
            return result
            
        except Exception as e:
            log_error(f"提取环境信息时发生错误: {str(e)}", "environment_extractor")
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}", "environment_extractor")
            return {
                'development_environment': 'AcoreIde',
                'runtime_environment': '飞腾2000（天脉3）'
            }
    
    def _extract_keyword_contexts(
        self, 
        content: str, 
        keywords: List[str],
        context_type: str
    ) -> List[Dict[str, Any]]:
        """
        提取关键词上下文
        
        Args:
            content: 文档内容
            keywords: 关键词列表
            context_type: 上下文类型（开发环境/运行环境）
            
        Returns:
            List[Dict]: 匹配的上下文信息列表
        """
        contexts = []
        
        log_debug(f"开始提取{context_type}关键词上下文，关键词数量: {len(keywords)}", "environment_extractor")
        log_debug(f"{context_type}关键词列表: {keywords}", "environment_extractor")
        
        for keyword in keywords:
            log_debug(f"搜索关键词: '{keyword}'", "environment_extractor")
            
            # 不区分大小写的匹配
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = list(pattern.finditer(content))
            
            log_debug(f"关键词 '{keyword}' 找到 {len(matches)} 个匹配", "environment_extractor")
            
            for match_idx, match in enumerate(matches):
                start_pos = max(0, match.start() - 100)  # 前100个字符
                end_pos = min(len(content), match.end() + 100)  # 后100个字符
                
                context_text = content[start_pos:end_pos]
                
                context_info = {
                    'keyword': keyword,
                    'matched_text': match.group(),
                    'context': context_text,
                    'position': match.start(),
                    'type': context_type
                }
                
                contexts.append(context_info)
                
                log_debug(f"匹配 {match_idx+1}: 关键词 '{keyword}' 在位置 {match.start()}", "environment_extractor")
                log_debug(f"匹配文本: '{match.group()}'", "environment_extractor") 
                log_debug(f"上下文: '{context_text[:100]}...'", "environment_extractor")
        
        log_info(f"提取到{len(contexts)}个{context_type}上下文", "environment_extractor")
        
        if contexts:
            log_debug(f"{context_type}匹配详情:", "environment_extractor")
            for i, ctx in enumerate(contexts):
                log_debug(f"  {i+1}. 关键词: {ctx['keyword']}, 位置: {ctx['position']}", "environment_extractor")
        else:
            log_warning(f"未找到任何{context_type}关键词匹配", "environment_extractor")
        
        return contexts
    
    def _analyze_with_ai(
        self, 
        dev_contexts: List[Dict[str, Any]], 
        runtime_contexts: List[Dict[str, Any]],
        ai_function: callable,
        full_document_content: str
    ) -> Optional[Dict[str, str]]:
        """
        使用AI分析上下文信息
        
        Args:
            dev_contexts: 开发环境上下文列表
            runtime_contexts: 运行环境上下文列表
            ai_function: AI分析函数
            full_document_content: 整个文档的原始内容，用于上下文
            
        Returns:
            Optional[Dict[str, str]]: AI分析结果
        """
        try:
            log_debug(f"开始AI分析 - 开发环境上下文: {len(dev_contexts)} 个, 运行环境上下文: {len(runtime_contexts)} 个", "environment_extractor")
            
            # 构建AI分析的提示词
            prompt = self._build_ai_prompt(dev_contexts, runtime_contexts, full_document_content)
            
            log_info(f"构建AI提示词完成，长度: {len(prompt)} 字符", "environment_extractor")
            log_debug(f"AI提示词内容: {prompt[:500]}...", "environment_extractor")
            
            # 调用AI函数
            log_debug("开始调用AI分析函数", "environment_extractor")
            ai_response = ai_function(prompt)
            
            log_debug(f"AI函数返回: {type(ai_response)}", "environment_extractor")
            
            # 显示完整的AI响应内容
            full_response_str = str(ai_response)
            log_debug(f"AI响应完整内容: {full_response_str}", "environment_extractor")
            
            if ai_response:
                # 过滤think标签并解析AI响应
                log_debug("开始解析AI响应", "environment_extractor")
                result = self._parse_ai_response(ai_response)
                log_info(f"AI分析解析结果: {result}", "environment_extractor")
                return result
            else:
                log_warning("AI分析返回空结果", "environment_extractor")
                return None
                
        except Exception as e:
            log_error(f"AI分析环境信息时发生错误: {str(e)}", "environment_extractor")
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}", "environment_extractor")
            return None
    
    def _build_ai_prompt(
        self, 
        dev_contexts: List[Dict[str, Any]], 
        runtime_contexts: List[Dict[str, Any]],
        full_document_content: str
    ) -> str:
        """构建AI分析提示词"""
        prompt = """请根据以下需求规格说明文档的内容，提取开发环境和运行环境信息：

开发环境说明：
- 开发环境是一个开发软件的名称，例如：AcoreIDE、Workbench、CSS（Code Composer Studio）、IAR、Keil等
- 请从文档内容中识别具体的开发工具名称

运行环境说明：
- 运行环境通常是硬件平台（操作系统），例如：飞腾2000（天脉3）、PowerPC(VxWorks)等
- 有的硬件平台没有操作系统，就只有硬件平台，例如：DSP2812、DSP6657
- 请从文档内容中识别具体的硬件平台和操作系统

"""
        
        # 🔧 新增：优先展示3.9章节的完整内容
        if "3.9" in full_document_content:
            prompt += "=== 计算机资源需求章节内容（重点分析） ===\n"
            prompt += full_document_content + "\n\n"
        else:
            prompt += "=== 文档内容 ===\n"
            prompt += full_document_content[:2000] + "...\n\n"  # 如果不是3.9章节，只取前2000字符
        
        # 添加关键词匹配上下文（作为补充）
        if dev_contexts:
            prompt += "=== 开发环境关键词匹配上下文 ===\n"
            for i, context in enumerate(dev_contexts[:3]):  # 最多3个上下文
                prompt += f"{i+1}. 关键词: {context['keyword']}\n"
                prompt += f"   上下文: {context['context']}\n\n"
        
        if runtime_contexts:
            prompt += "=== 运行环境关键词匹配上下文 ===\n"
            for i, context in enumerate(runtime_contexts[:3]):  # 最多3个上下文
                prompt += f"{i+1}. 关键词: {context['keyword']}\n"
                prompt += f"   上下文: {context['context']}\n\n"
        
        prompt += """
请仔细分析上述内容，特别关注：
1. 3.9.1 计算机硬件需求 - 可能包含运行环境信息
2. 3.9.2 计算机硬件资源使用需求 - 可能包含硬件平台信息  
3. 3.9.3 计算机软件需求 - 可能包含开发环境和运行环境信息
4. 3.9.4 计算机通信需求 - 可能包含系统环境信息

请以JSON格式返回结果：
{
    "development_environment": "具体的开发环境名称",
    "runtime_environment": "具体的运行环境描述"
}

如果无法确定，请返回最可能的选项。"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: Any) -> Optional[Dict[str, str]]:
        """解析AI响应"""
        try:
            import json
            import re
            
            # 处理不同类型的AI响应
            response_text = ""
            
            if isinstance(ai_response, tuple):
                # 如果是元组，合并所有元素
                response_text = " ".join(str(item) for item in ai_response)
                log_debug(f"AI响应是元组格式，合并后: {response_text}", "environment_extractor")
            elif isinstance(ai_response, str):
                response_text = ai_response
            else:
                response_text = str(ai_response)
            
            # 过滤think标签
            response_text = self._filter_think_tags(response_text)
            log_debug(f"过滤think标签后: {response_text}", "environment_extractor")
            
            # 尝试提取JSON部分
            json_match = re.search(r'\{[^}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                return {
                    'development_environment': result.get('development_environment', ''),
                    'runtime_environment': result.get('runtime_environment', '')
                }
            
            # 如果没有JSON格式，尝试从文本中提取环境信息
            return self._extract_environment_from_text(response_text)
                
        except Exception as e:
            log_error(f"解析AI响应时发生错误: {str(e)}", "environment_extractor")
            return None
    
    def _filter_think_tags(self, text: str) -> str:
        """过滤think标签内容"""
        import re
        
        # 移除<think>...</think>标签及其内容
        filtered_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除多余的空白字符
        filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
        
        return filtered_text
    
    def _extract_environment_from_text(self, text: str) -> Optional[Dict[str, str]]:
        """从文本中提取环境信息"""
        try:
            import re
            
            result = {}
            
            # 提取开发环境
            dev_patterns = [
                r'开发环境[：:]\s*([^\n\r,，。]+)',
                r'development[_\s]*environment[：:]\s*([^\n\r,，。]+)',
                r'workbench|iar|keil|css|ccs|acoreide'
            ]
            
            for pattern in dev_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    dev_env = match.group(1) if match.groups() else match.group(0)
                    result['development_environment'] = dev_env.strip()
                    break
            
            # 提取运行环境
            runtime_patterns = [
                r'运行环境[：:]\s*([^\n\r,，。]+)',
                r'runtime[_\s]*environment[：:]\s*([^\n\r,，。]+)',
                r'powerpc\([^)]+\)|飞腾\d+|天脉\d+|vxwork|linux|windows'
            ]
            
            for pattern in runtime_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    runtime_env = match.group(1) if match.groups() else match.group(0)
                    result['runtime_environment'] = runtime_env.strip()
                    break
            
            if result:
                log_info(f"从文本中提取到环境信息: {result}", "environment_extractor")
                return result
            else:
                log_warning("AI响应中未找到环境信息", "environment_extractor")
                return None
                
        except Exception as e:
            log_error(f"从文本提取环境信息时发生错误: {str(e)}", "environment_extractor")
            return None
    
    def _smart_match_development(self, contexts: List[Dict[str, Any]]) -> str:
        """智能匹配开发环境"""
        # 基于关键词优先级的智能匹配
        priority_map = {
            'acoreide': 'AcoreIDE',
            'acore ide': 'AcoreIDE', 
            'workbench': 'Workbench',
            'css': 'CSS',
            'code composer studio': 'Code Composer Studio',
            'ccs': 'CCS',
            'iar': 'IAR',
            'keil': 'Keil'
        }
        
        for context in contexts:
            keyword_lower = context['keyword'].lower()
            if keyword_lower in priority_map:
                self.logger.info(f"匹配到开发环境: {priority_map[keyword_lower]}")
                return priority_map[keyword_lower]
        
        return 'AcoreIde'  # 默认值
    
    def _smart_match_runtime(self, contexts: List[Dict[str, Any]]) -> str:
        """智能匹配运行环境"""
        # 基于关键词优先级的智能匹配
        for context in contexts:
            keyword_lower = context['keyword'].lower()
            context_lower = context['context'].lower()
            
            # 飞腾系列
            if any(k in keyword_lower for k in ['飞腾', 'phytium', 'ft2000']):
                if any(k in context_lower for k in ['天脉', 'tianmai']):
                    return '飞腾2000（天脉3）'
                else:
                    return '飞腾2000'
            
            # PowerPC系列
            elif 'powerpc' in keyword_lower:
                if 'vxwork' in context_lower:
                    return 'PowerPC(VxWorks)'
                else:
                    return 'PowerPC'
            
            # DSP系列
            elif keyword_lower.startswith('dsp'):
                return keyword_lower.upper()
            
            # ARM系列
            elif any(k in keyword_lower for k in ['arm', 'cortex', 'stm32']):
                return 'ARM'
        
        return '飞腾2000（天脉3）'  # 默认值 

    def _extract_from_standardized_document(self, session_id: str) -> Optional[str]:
        """
        从标准化需求文档中提取3.9章节的内容（使用标准化管理器）
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[str]: 3.9章节的内容，如果没有找到则返回None
        """
        try:
            # 🚀 使用标准化管理器
            from ...utils.standardization_manager import get_standardization_manager
            standardization_manager = get_standardization_manager()
            
            # 查找标准化文档
            standardized_doc_path = standardization_manager.get_standardized_document_path(session_id)
            
            if not standardized_doc_path:
                log_warning(f"未找到标准化文档，会话ID: {session_id}", "environment_extractor")
                return None
            
            log_info(f"找到标准化文档: {standardized_doc_path}", "environment_extractor")
            
            # 读取标准化文档
            try:
                doc = Document(standardized_doc_path)
                full_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                log_debug(f"标准化文档总长度: {len(full_text)} 字符", "environment_extractor")
                
                # 提取3.9章节及其子章节的内容
                chapter_content = self._extract_39_chapter_content(full_text)
                
                if chapter_content:
                    log_info(f"成功提取3.9章节内容，长度: {len(chapter_content)} 字符", "environment_extractor")
                    return chapter_content
                else:
                    log_warning("未在标准化文档中找到3.9章节内容", "environment_extractor")
                    return None
                    
            except Exception as e:
                log_error(f"读取标准化文档失败: {e}", "environment_extractor")
                return None
                
        except Exception as e:
            log_error(f"提取标准化文档内容时发生错误: {e}", "environment_extractor")
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}", "environment_extractor")
            return None
    
    def _extract_39_chapter_content(self, document_content: str) -> Optional[str]:
        """
        从文档内容中提取3.9章节的内容
        
        Args:
            document_content: 文档全文内容
            
        Returns:
            Optional[str]: 3.9章节的内容
        """
        try:
            log_debug("开始提取3.9章节内容", "environment_extractor")
            
            # 3.9章节可能的标题模式（容错处理）
            chapter_39_patterns = [
                r'3\.9\s*计算机资源需求',
                r'3\.9\s*计算机资源',
                r'3\.9\s*资源需求',
                r'3\.9\s*硬件资源需求',
                r'3\.9\s*软件资源需求',
                r'3\.9\s*环境需求',
                r'3\.9\s*[^\n]*资源[^\n]*需求',
                r'3\.9\s*[^\n]*环境[^\n]*需求'
            ]
            
            # 查找3.9章节开始位置
            start_pos = None
            matched_pattern = None
            
            for pattern in chapter_39_patterns:
                match = re.search(pattern, document_content, re.IGNORECASE)
                if match:
                    start_pos = match.start()
                    matched_pattern = match.group()
                    log_info(f"找到3.9章节: '{matched_pattern}' 在位置 {start_pos}", "environment_extractor")
                    break
            
            if start_pos is None:
                log_warning("未找到3.9章节", "environment_extractor")
                return None
            
            # 查找3.9章节结束位置（下一个同级或更高级章节）
            end_patterns = [
                r'3\.10\s',    # 3.10章节
                r'3\.[1-9]\d+\s',  # 3.11, 3.12等
                r'4\.\s',      # 第4章
                r'[4-9]\.\s',  # 第4-9章
                r'1[0-9]\.\s'  # 第10章以上
            ]
            
            end_pos = len(document_content)  # 默认到文档末尾
            
            for pattern in end_patterns:
                match = re.search(pattern, document_content[start_pos:], re.IGNORECASE)
                if match:
                    end_pos = start_pos + match.start()
                    log_debug(f"找到3.9章节结束位置: {end_pos}", "environment_extractor")
                    break
            
            # 提取3.9章节内容
            chapter_content = document_content[start_pos:end_pos].strip()
            
            if chapter_content:
                log_info(f"成功提取3.9章节内容，长度: {len(chapter_content)} 字符", "environment_extractor")
                
                # 记录找到的子章节
                sub_chapters = self._identify_sub_chapters(chapter_content)
                if sub_chapters:
                    log_info(f"3.9章节包含子章节: {sub_chapters}", "environment_extractor")
                else:
                    log_debug("3.9章节未找到明确的子章节结构", "environment_extractor")
                
                return chapter_content
            else:
                log_warning("3.9章节内容为空", "environment_extractor")
                return None
                
        except Exception as e:
            log_error(f"提取3.9章节内容时发生错误: {e}", "environment_extractor")
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}", "environment_extractor")
            return None
    
    def _identify_sub_chapters(self, chapter_content: str) -> List[str]:
        """
        识别3.9章节中的子章节
        
        Args:
            chapter_content: 3.9章节内容
            
        Returns:
            List[str]: 找到的子章节列表
        """
        try:
            sub_chapter_patterns = [
                r'3\.9\.\d+\s*[^\n]*硬件[^\n]*需求',
                r'3\.9\.\d+\s*[^\n]*软件[^\n]*需求', 
                r'3\.9\.\d+\s*[^\n]*通信[^\n]*需求',
                r'3\.9\.\d+\s*[^\n]*资源[^\n]*使用[^\n]*需求',
                r'3\.9\.\d+\s*[^\n]*环境[^\n]*需求',
                r'3\.9\.\d+\s*[^\n]*'  # 通用的3.9.x模式
            ]
            
            found_sub_chapters = []
            
            for pattern in sub_chapter_patterns:
                matches = re.findall(pattern, chapter_content, re.IGNORECASE)
                for match in matches:
                    if match.strip() not in found_sub_chapters:
                        found_sub_chapters.append(match.strip())
            
            return found_sub_chapters
            
        except Exception as e:
            log_error(f"识别子章节时发生错误: {e}", "environment_extractor")
            return [] 