"""
环境信息提取器 - 回归测试模块

从需求规格说明文档中智能提取开发环境和运行环境信息。
通过关键词匹配和AI分析，准确识别开发工具和硬件平台信息。
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

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
        ai_analysis_function: Optional[callable] = None
    ) -> Dict[str, str]:
        """
        从需求文档中提取环境信息
        
        Args:
            requirement_doc_content: 需求文档内容
            ai_analysis_function: AI分析函数（可选）
            
        Returns:
            Dict[str, str]: 包含development_environment和runtime_environment的字典
        """
        try:
            self.logger.info("开始提取环境信息")
            
            # 第一步：关键词匹配和上下文提取
            dev_contexts = self._extract_keyword_contexts(
                requirement_doc_content, 
                self.development_keywords,
                "开发环境"
            )
            
            runtime_contexts = self._extract_keyword_contexts(
                requirement_doc_content, 
                self.runtime_keywords,
                "运行环境"
            )
            
            # 第二步：使用AI分析上下文（如果提供了AI函数）
            development_environment = "AcoreIde"  # 默认值
            runtime_environment = "飞腾2000（天脉3）"  # 默认值
            
            if ai_analysis_function and (dev_contexts or runtime_contexts):
                ai_result = self._analyze_with_ai(
                    dev_contexts, runtime_contexts, ai_analysis_function
                )
                if ai_result:
                    development_environment = ai_result.get('development_environment', development_environment)
                    runtime_environment = ai_result.get('runtime_environment', runtime_environment)
            else:
                # 第三步：基于规则的智能匹配
                if dev_contexts:
                    development_environment = self._smart_match_development(dev_contexts)
                
                if runtime_contexts:
                    runtime_environment = self._smart_match_runtime(runtime_contexts)
            
            result = {
                'development_environment': development_environment,
                'runtime_environment': runtime_environment
            }
            
            self.logger.info(f"环境信息提取完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"提取环境信息时发生错误: {str(e)}")
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
        
        for keyword in keywords:
            # 不区分大小写的匹配
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = pattern.finditer(content)
            
            for match in matches:
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
                
                self.logger.debug(f"找到{context_type}关键词 '{keyword}': {context_text[:50]}...")
        
        self.logger.info(f"提取到{len(contexts)}个{context_type}上下文")
        return contexts
    
    def _analyze_with_ai(
        self, 
        dev_contexts: List[Dict[str, Any]], 
        runtime_contexts: List[Dict[str, Any]],
        ai_function: callable
    ) -> Optional[Dict[str, str]]:
        """
        使用AI分析上下文信息
        
        Args:
            dev_contexts: 开发环境上下文列表
            runtime_contexts: 运行环境上下文列表
            ai_function: AI分析函数
            
        Returns:
            Optional[Dict[str, str]]: AI分析结果
        """
        try:
            # 构建AI分析的提示词
            prompt = self._build_ai_prompt(dev_contexts, runtime_contexts)
            
            self.logger.info(f"调用AI分析环境信息，提示词长度: {len(prompt)}")
            
            # 调用AI函数
            ai_response = ai_function(prompt)
            
            if ai_response:
                # 解析AI响应
                result = self._parse_ai_response(ai_response)
                self.logger.info(f"AI分析结果: {result}")
                return result
            else:
                self.logger.warning("AI分析返回空结果")
                return None
                
        except Exception as e:
            self.logger.error(f"AI分析环境信息时发生错误: {str(e)}")
            return None
    
    def _build_ai_prompt(
        self, 
        dev_contexts: List[Dict[str, Any]], 
        runtime_contexts: List[Dict[str, Any]]
    ) -> str:
        """构建AI分析提示词"""
        prompt = """请根据以下需求规格说明文档的内容片段，提取开发环境和运行环境信息：

开发环境说明：
- 开发环境是一个开发软件的名称，例如：AcoreIDE、Workbench、CSS（Code Composer Studio）、IAR、Keil等
- 请从上下文中识别具体的开发工具名称

运行环境说明：
- 运行环境通常是硬件平台（操作系统），例如：飞腾2000（天脉3）、PowerPC(VxWorks)等
- 有的硬件平台没有操作系统，就只有硬件平台，例如：DSP2812、DSP6657
- 请从上下文中识别具体的硬件平台和操作系统

文档内容片段：

"""
        
        # 添加开发环境上下文
        if dev_contexts:
            prompt += "=== 开发环境相关内容 ===\n"
            for i, context in enumerate(dev_contexts[:5]):  # 最多5个上下文
                prompt += f"{i+1}. 关键词: {context['keyword']}\n"
                prompt += f"   上下文: {context['context']}\n\n"
        
        # 添加运行环境上下文
        if runtime_contexts:
            prompt += "=== 运行环境相关内容 ===\n"
            for i, context in enumerate(runtime_contexts[:5]):  # 最多5个上下文
                prompt += f"{i+1}. 关键词: {context['keyword']}\n"
                prompt += f"   上下文: {context['context']}\n\n"
        
        prompt += """
请以JSON格式返回结果：
{
    "development_environment": "具体的开发环境名称",
    "runtime_environment": "具体的运行环境描述"
}

如果无法确定，请返回最可能的选项。"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Optional[Dict[str, str]]:
        """解析AI响应"""
        try:
            import json
            
            # 尝试提取JSON部分
            json_match = re.search(r'\{[^}]*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                return {
                    'development_environment': result.get('development_environment', ''),
                    'runtime_environment': result.get('runtime_environment', '')
                }
            else:
                self.logger.warning("AI响应中未找到JSON格式结果")
                return None
                
        except Exception as e:
            self.logger.error(f"解析AI响应时发生错误: {str(e)}")
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