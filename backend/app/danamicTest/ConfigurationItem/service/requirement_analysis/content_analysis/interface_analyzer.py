"""
接口测试项提取器
用于从3.3.1章节的接口表格中提取接口测试项
"""

from typing import List, Dict, Any, Optional, Tuple
import re
from ....utils.logging_utils.logger import log_info, log_debug, log_warning, log_error


class InterfaceTestExtractor:
    """接口测试项提取器"""
    
    def __init__(self):
        """初始化接口测试提取器"""
        self.logger_name = "interface_extractor"
        
        # 接口表格的列名映射（与interface_table_parser.py保持一致）
        self.column_mapping = {
            '序号': ['序号', '编号', 'No', '号', '项'],
            '接口名称': ['接口名称', '接口名', 'Interface Name', '接口', '功能名称'],
            '接口标识': ['接口标识号','接口标识', '接口ID', 'Interface ID', '接口编号', '标识符', '标识', 'ID'],
            '源': ['源', '来源', '发起方', 'Source', 'From', '源系统', '发送方'],
            '目的地': ['目的地', '目标', '接收方', 'Target', 'To', 'Destination', '目标系统', '接收端'],
            '接口描述': ['数据内容','接口描述', '功能描述', 'Description', 'Desc', '备注', '详细说明', '描述', '说明']
        }
    
    def extract_interface_tests(self, interface_data: List[Dict[str, Any]], 
                              project_name: str = "软件需求规格说明",
                              base_identifier: str = "CT-388.222.JJK1-2.00",
                              software_name: str = "软件",
                              software_version: str = "1.0") -> List[Dict[str, Any]]:
        """
        从接口数据中提取接口测试项
        
        Args:
            interface_data: 接口表格数据列表
            project_name: 项目名称，用于构建追踪关系
            base_identifier: 基础标识符，用于构建测试项标识
            
        Returns:
            接口测试项列表
        """
        try:
            log_info(f"🔌 开始提取接口测试项，接口数量: {len(interface_data)}", self.logger_name)
            log_debug(f"项目名称: {project_name}", self.logger_name)
            log_debug(f"基础标识符: {base_identifier}", self.logger_name)
            
            interface_tests = []
            
            for i, interface_info in enumerate(interface_data):
                log_debug(f"处理第{i+1}个接口: {interface_info}", self.logger_name)
                
                # 提取接口基本信息
                interface_name = self._extract_interface_name(interface_info)
                interface_id = self._extract_interface_id(interface_info)
                interface_desc = self._extract_interface_description(interface_info)
                source, target = self._extract_source_target(interface_info)
                
                log_debug(f"接口基本信息提取结果:", self.logger_name)
                log_debug(f"  - 接口名称: {interface_name}", self.logger_name)
                log_debug(f"  - 接口标识: {interface_id}", self.logger_name)
                log_debug(f"  - 接口描述: {interface_desc}", self.logger_name)
                log_debug(f"  - 源: {source}", self.logger_name)
                log_debug(f"  - 目标: {target}", self.logger_name)
                
                if interface_name:
                    # 创建接口测试项
                    interface_test = self._create_interface_test_item(
                        interface_info=interface_info,
                        interface_name=interface_name,
                        interface_id=interface_id, 
                        interface_desc=interface_desc or f'{interface_name}接口',
                        index=i + 1,
                        chapter_number=f"3.3.{i + 1}",  # 接口章节编号
                        project_name=project_name,
                        base_identifier=base_identifier,
                        software_name=software_name,
                        software_version=software_version
                    )
                    
                    if interface_test:
                        interface_tests.append(interface_test)
                        log_info(f"✅ 创建接口测试项: {interface_test.get('name', '未知')}", self.logger_name)
                        log_debug(f"   标识符: {interface_test.get('test_item_identifier', '未设置')}", self.logger_name)
                        log_debug(f"   追踪关系: {interface_test.get('software_requirement_trace', '未设置')}", self.logger_name)
                    else:
                        log_warning(f"⚠️ 第{i+1}个接口测试项创建失败", self.logger_name)
                else:
                    log_warning(f"⚠️ 第{i+1}个接口缺少接口名称，跳过", self.logger_name)
            
            log_info(f"🎉 接口测试项提取完成，成功创建 {len(interface_tests)} 个接口测试项", self.logger_name)
            
            return interface_tests
            
        except Exception as e:
            log_error(f"接口测试项提取失败: {str(e)}", self.logger_name)
            import traceback
            log_error(f"错误详情: {traceback.format_exc()}", self.logger_name)
            return []
    
    def _extract_interface_name(self, interface_info: Dict[str, Any]) -> Optional[str]:
        """提取接口名称"""
        for key in self.column_mapping['接口名称']:
            if key in interface_info and interface_info[key]:
                return str(interface_info[key]).strip()
        return None
    
    def _extract_interface_id(self, interface_info: Dict[str, Any]) -> Optional[str]:
        """提取接口标识"""
        log_debug(f"尝试提取接口标识，可用字段: {list(interface_info.keys())}", self.logger_name)
        for key in self.column_mapping['接口标识']:
            if key in interface_info and interface_info[key]:
                interface_id = str(interface_info[key]).strip()
                log_debug(f"找到接口标识字段 '{key}': '{interface_id}'", self.logger_name)
                return interface_id
        log_debug(f"未找到接口标识，尝试的字段: {self.column_mapping['接口标识']}", self.logger_name)
        return None
    
    def _extract_interface_description(self, interface_info: Dict[str, Any]) -> Optional[str]:
        """提取接口描述"""
        for key in self.column_mapping['接口描述']:
            if key in interface_info and interface_info[key]:
                return str(interface_info[key]).strip()
        return None
    
    def _extract_source_target(self, interface_info: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """提取源和目的地信息"""
        source = None
        target = None
        
        for key in self.column_mapping['源']:
            if key in interface_info and interface_info[key]:
                source = str(interface_info[key]).strip()
                break
        
        for key in self.column_mapping['目的地']:
            if key in interface_info and interface_info[key]:
                target = str(interface_info[key]).strip()
                break
        
        return source, target
    
    def _create_interface_test_item(self, interface_info: Dict[str, Any], 
                                  interface_name: str,
                                  interface_id: str,
                                  interface_desc: str,
                                  index: int,
                                  chapter_number: str,
                                  project_name: str,
                                  base_identifier: str,
                                  software_name: str,
                                  software_version: str) -> Dict[str, Any]:
        """
        创建接口测试项
        
        Args:
            interface_info: 原始接口信息
            interface_name: 接口名称
            interface_id: 接口标识
            interface_desc: 接口描述
            index: 索引号
            chapter_number: 章节编号
            project_name: 项目名称
            base_identifier: 基础标识符
            
        Returns:
            接口测试项字典
        """
        try:
            # 🔧 修复：首先确定英文标识符（优先使用接口表格中的接口标识）
            english_identifier = interface_id if interface_id and interface_id.strip() else self._generate_ai_english_identifier(interface_name, index)
            
            # 🔧 修复：使用英文标识符构建测试项标识符和标准子需求标识符
            test_identifier = f"{base_identifier}-{english_identifier}-IN{index:02d}"
            standard_sub_requirement_identifier = f"{base_identifier}-{english_identifier}-IN{index:02d}"
            
            # 🔧 修复：构建正确的软件需求规格说明追踪格式
            # 格式：《xx软件需求规格说明》 3.3.x +测试项名称
            # 第一个接口测试项从3.3.2开始（3.3.1通常是接口概述）
            interface_chapter = f"3.3.{index + 1}"  # 从3.3.2开始
            software_requirement_trace = f"《{project_name}》 {interface_chapter} {interface_name}"
            
            # 获取源和目的地信息
            source, target = self._extract_source_target(interface_info)
            
            # 构建完整的接口描述（包含源和目的地信息）
            full_description = self._build_full_interface_description(
                interface_desc, source, target
            )
            
            # 创建接口测试项
            interface_test = {
                'index': index,
                'name': interface_name,
                'pure_name': interface_name,
                'test_item_name': interface_name,
                'test_item_identifier': test_identifier,
                'test_type': '接口测试',
                'software_requirement_trace': software_requirement_trace,  # 🔧 修复：使用正确格式
                'chapter_number': interface_chapter,  # 🔧 修复：使用正确的章节编号
                'software_requirement_trace_relation': software_requirement_trace,  # 🔧 修复：与追踪列保持一致
                'requirement_name': interface_name,
                'standard_sub_requirement_name': interface_name,
                'standard_sub_requirement_identifier': standard_sub_requirement_identifier,  # 🔧 新增：标准子需求标识符
                'standard_sub_requirement_unit': '0.2',  # 🔧 新增：标准子需求单元
                'task_requirement_trace': '无',  # 🔧 新增：任务需求追踪
                'software_requirement_name': interface_name,  # 🔧 新增：软件需求名称
                'requirement_description': full_description,
                'requirement_sub_description': full_description,
                'test_description': '',  # 将通过数据库匹配或AI生成
                'test_method': '',  # 将通过数据库匹配或AI生成
                'pass_criteria': '接口调用成功，返回数据符合预期格式和内容要求',
                'adequacy_requirement': '所有接口测试用例执行完毕，接口功能符合设计要求。',
                'english_identifier': english_identifier,  # 🔧 修复：使用已确定的英文标识符
                '_is_interface_item': True,  # 标记为接口测试项
                '_interface_id': interface_id,
                '_source': source,
                '_target': target,
                '_original_interface_info': interface_info,  # 保存原始接口信息
                'software_name': software_name,
                'software_version': software_version
            }
            
            log_debug(f"接口测试项创建完成: {interface_name}", self.logger_name)
            log_debug(f"  测试标识: {test_identifier}", self.logger_name)
            log_debug(f"  标准子需求标识: {standard_sub_requirement_identifier}", self.logger_name)
            log_debug(f"  软件需求追踪: {software_requirement_trace}", self.logger_name)
            log_debug(f"  章节编号: {interface_chapter}", self.logger_name)
            log_debug(f"  原始接口标识: {interface_id}", self.logger_name)
            log_debug(f"  最终英文标识符: {english_identifier}", self.logger_name)
            
            return interface_test
            
        except Exception as e:
            log_error(f"创建接口测试项失败: {e}", self.logger_name)
            # 🔧 修复：在异常情况下也使用正确的追踪格式
            fallback_chapter = f"3.3.{index + 1}"
            fallback_trace = f"《{project_name}》 {fallback_chapter} {interface_name}"
            
            # 返回基本的测试项结构
            return {
                'index': index,
                'name': interface_name,
                'test_type': '接口测试',
                'software_requirement_trace': fallback_trace,  # 🔧 修复：使用正确格式
                'requirement_description': interface_desc or '',
                '_is_interface_item': True
            }
    
    def _generate_ai_english_identifier(self, interface_name: str, index: int) -> str:
        """
        使用AI生成英文标识符
        
        Args:
            interface_name: 接口名称
            index: 索引号
            
        Returns:
            英文标识符
        """
        try:
            log_debug(f"开始AI翻译接口名称: {interface_name}", self.logger_name)
            
            # 尝试调用AI翻译
            try:
                from ...test_generation.ai_content.ai_content_optimizer import translate_chinese_to_english
                english_identifier = translate_chinese_to_english(interface_name)
                log_debug(f"AI翻译结果: '{interface_name}' -> '{english_identifier}'", self.logger_name)
                return english_identifier
            except Exception as e:
                log_warning(f"AI翻译失败: {e}", self.logger_name)
                # 回退到规则生成
                return self._generate_rule_based_identifier(interface_name, index)
                
        except Exception as e:
            log_warning(f"生成英文标识符失败: {e}", self.logger_name)
            return f"Interface{index:03d}"
    
    def _generate_rule_based_identifier(self, interface_name: str, index: int) -> str:
        """
        基于规则生成英文标识符（AI翻译失败时的回退方案）
        
        Args:
            interface_name: 接口名称
            index: 索引号
            
        Returns:
            英文标识符
        """
        try:
            # 移除常见的后缀词
            cleaned_name = interface_name.replace('接口', '').replace('服务', '').replace('API', '')
            
            # 转换为英文或拼音缩写（简化处理）
            if '认证' in cleaned_name:
                return 'AuthenticationInterface'
            elif '短信' in cleaned_name:
                return 'SMSInterface'
            elif '文件' in cleaned_name or '存储' in cleaned_name:
                return 'FileStorageInterface'
            else:
                # 默认使用简化的名称
                return f"Interface{index:03d}"
                
        except Exception as e:
            log_warning(f"生成规则标识符失败: {e}", self.logger_name)
            return f"Interface{index:03d}"
    
    def _build_full_interface_description(self, interface_desc: str, 
                                        source: Optional[str], 
                                        target: Optional[str]) -> str:
        """
        构建完整的接口描述
        
        Args:
            interface_desc: 基本接口描述
            source: 源系统（忽略）
            target: 目标系统（忽略）
            
        Returns:
            纯净的接口描述（只返回interface_desc本身）
        """
        try:
            # 🔧 用户要求：只要接口描述列的纯净内容，不要任何前缀或额外信息
            if interface_desc and interface_desc.strip():
                return interface_desc.strip()
            else:
                # 如果接口描述为空，返回默认描述
                return '接口功能描述'
                
        except Exception as e:
            log_warning(f"构建接口描述失败: {e}", self.logger_name)
            return '接口功能描述'
    
    def is_interface_test_item(self, test_item: Dict[str, Any]) -> bool:
        """
        检查是否为接口测试项
        
        Args:
            test_item: 测试项
            
        Returns:
            bool: 是否为接口测试项
        """
        return (
            test_item.get('_is_interface_item', False) or
            test_item.get('test_type', '') == '接口测试' or
            'IN' in test_item.get('test_item_identifier', '') and 
            test_item.get('test_item_identifier', '').endswith(('IN01', 'IN02', 'IN03'))
        ) 