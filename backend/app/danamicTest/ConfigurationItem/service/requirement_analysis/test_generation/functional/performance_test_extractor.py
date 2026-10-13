"""
性能测试项和边界测试项分离模块

负责从功能测试项中分离出性能测试项和边界测试项，当需求描述中包含性能或边界相关内容时，
自动创建对应的专门测试项。
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from ....utils.logging_utils.logger import log_info, log_debug, log_warning, log_error
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_debug, log_warning, log_error
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_debug, log_warning, log_error


class PerformanceSeparator:
    """性能测试项和边界测试项分离器"""
    
    def __init__(self):
        """初始化分离器"""
        # 性能测试项关键词组1：性能指标关键词
        self.performance_keywords_group1 = ['≤', '≥', '<', '>', '秒', '毫秒', '微秒', '次/秒', 'ms', 's', '响应时间', '处理时间', '延迟']
        
        # 性能测试项关键词组2：性能描述关键词
        self.performance_keywords_group2 = ['性能', '效率', '速度', '吞吐量', '并发', '负载', '压力', 'TPS', 'QPS']
        
        # 边界测试项关键词组1：边界限制关键词
        self.boundary_keywords_group1 = ['至少', '最少', '不少于', '不超过', '最多', '范围', '区间', '边界', '限制', '约束']
        
        # 边界测试项关键词组2：数据类型关键词
        self.boundary_keywords_group2 = ['字符', '位', '个', '项', '条', '次', '值', '数据', '输入', '输出', '参数', '配置']
        
        # 余量测试项关键词组1：余量关键词
        self.allowance_keywords_group1 = ['余量', '剩余', '空闲', '可用', '预留']
        
        # 余量测试项关键词组2：资源关键词  
        self.allowance_keywords_group2 = ['内存', '存储', '磁盘', 'CPU', '处理器', '带宽', '资源', 'DDR', 'FLASH', 'RAM']

        
        self.boundary_exclude_keywords = ['初始化', '安全性', '可靠性', '边界', '接口', '接收', '发送', '时间', '校正系数', '参数设置']
        
        # 🔧 移除：不再初始化EnhancedTestContentGenerator
        # 让后续的ConfigurationItemTestContentGenerator统一处理AI生成
        log_info("性能测试项分离器初始化完成（不使用增强AI生成器）", "performance_separator")
    
    def separate_performance_and_boundary_tests(self, test_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分离性能测试项和边界测试项
        
        Args:
            test_items: 原始测试项列表
            
        Returns:
            List[Dict[str, Any]]: 增强后的测试项列表（包含原始、性能、边界、余量测试项）
        """
        try:
            log_info("[DEBUG-PERF-SORT] ===== 开始性能测试项分离 =====", "performance_separator")
            log_info(f"[DEBUG-PERF-SORT] 原始测试项数量: {len(test_items)}", "performance_separator")
            
            enhanced_test_items = []
            
            for i, test_item in enumerate(test_items):
                original_name = test_item.get('name', '未知')
                log_info(f"[DEBUG-PERF-SORT] 处理第{i+1}个功能测试项: {original_name}", "performance_separator")
                
                # 格式化原始功能测试项
                formatted_item = self._format_functional_test_item(test_item)
                enhanced_test_items.append(formatted_item)
                log_debug(f"[DEBUG-PERF-SORT] - 功能测试项已添加，当前总数: {len(enhanced_test_items)}", "performance_separator")
                
                # 检查并创建性能测试项
                if self._has_performance_content(test_item):
                    log_info(f"[DEBUG-PERF-SORT] - 检测到性能内容，提取性能测试项", "performance_separator")
                    performance_content = self._extract_performance_content(test_item)
                    if performance_content:
                        performance_item = self._create_performance_test_item(
                            formatted_item, performance_content, len(enhanced_test_items) + 1
                        )
                        enhanced_test_items.append(performance_item)
                        log_info(f"[DEBUG-PERF-SORT] - ✅性能测试项已创建: {performance_item.get('name')} (标识: {performance_item.get('test_item_identifier')})", "performance_separator")
                        log_debug(f"[DEBUG-PERF-SORT] - 当前总数: {len(enhanced_test_items)}", "performance_separator")
                    else:
                        log_warning(f"[DEBUG-PERF-SORT] - ❌性能内容提取失败", "performance_separator")
                else:
                    log_debug(f"[DEBUG-PERF-SORT] - 无性能内容", "performance_separator")
                
                # 检查并创建边界测试项
                if self._has_boundary_content(test_item):
                    log_info(f"[DEBUG-PERF-SORT] - 检测到边界内容，提取边界测试项", "performance_separator")
                    boundary_content = self._extract_boundary_content(test_item)
                    if boundary_content:
                        boundary_item = self._create_boundary_test_item(
                            formatted_item, boundary_content, len(enhanced_test_items) + 1
                        )
                        enhanced_test_items.append(boundary_item)
                        log_info(f"[DEBUG-PERF-SORT] - ✅边界测试项已创建: {boundary_item.get('name')} (标识: {boundary_item.get('test_item_identifier')})", "performance_separator")
                        log_debug(f"[DEBUG-PERF-SORT] - 当前总数: {len(enhanced_test_items)}", "performance_separator")
                    else:
                        log_warning(f"[DEBUG-PERF-SORT] - ❌边界内容提取失败", "performance_separator")
                else:
                    log_debug(f"[DEBUG-PERF-SORT] - 无边界内容", "performance_separator")
                
                # 🔧 新增：检查并创建余量测试项
                if self._has_allowance_content(test_item):
                    log_info(f"[DEBUG-PERF-SORT] - 检测到余量内容，提取余量测试项", "performance_separator")
                    allowance_content = self._extract_allowance_content(test_item)
                    if allowance_content:
                        allowance_item = self._create_allowance_test_item(
                            formatted_item, allowance_content, len(enhanced_test_items) + 1
                        )
                        enhanced_test_items.append(allowance_item)
                        log_info(f"[DEBUG-PERF-SORT] - ✅余量测试项已创建: {allowance_item.get('name')} (标识: {allowance_item.get('test_item_identifier')})", "performance_separator")
                        log_debug(f"[DEBUG-PERF-SORT] - 当前总数: {len(enhanced_test_items)}", "performance_separator")
                    else:
                        log_warning(f"[DEBUG-PERF-SORT] - ❌余量内容提取失败", "performance_separator")
                else:
                    log_debug(f"[DEBUG-PERF-SORT] - 无余量内容", "performance_separator")
                
                log_debug(f"[DEBUG-PERF-SORT] ---第{i+1}个功能测试项处理完成---", "performance_separator")
            
            log_info(f"[DEBUG-PERF-SORT] ===== 性能测试项分离完成 =====", "performance_separator")
            log_info(f"[DEBUG-PERF-SORT] 原始{len(test_items)}个 -> 增强后{len(enhanced_test_items)}个", "performance_separator")
            log_info(f"[DEBUG-PERF-SORT] 最终测试项列表:", "performance_separator")
            for idx, item in enumerate(enhanced_test_items):
                log_info(f"[DEBUG-PERF-SORT] {idx+1}. {item.get('name')} (标识: {item.get('test_item_identifier')})", "performance_separator")
            
            return enhanced_test_items
            
        except Exception as e:
            log_error(f"[DEBUG-PERF-SORT] ❌错误: 分离测试项时发生错误: {e}", "performance_separator")
            return test_items  # 返回原始列表作为备用
    
    def _extract_performance_content(self, test_item: Dict[str, Any]) -> Optional[str]:
        """
        从测试项中提取性能相关内容
        
        Args:
            test_item: 测试项
            
        Returns:
            性能内容字符串，如果没有则返回None
        """
        try:
            requirement_desc = test_item.get('requirement_description', '')
            if not requirement_desc:
                return None
            
            # 🔧 修复：处理字典类型的requirement_description
            if isinstance(requirement_desc, dict):
                # 如果是字典，直接获取performance字段
                performance_content = requirement_desc.get('performance', '')
                if performance_content and str(performance_content).strip().lower() not in ['无', 'none', 'n/a', '']:
                    log_debug(f"从字典中提取到性能内容: {str(performance_content)[:100]}...", "performance_separator")
                    return str(performance_content)
                return None
            
            # 🔧 保留原有的字符串处理逻辑作为备用
            if isinstance(requirement_desc, str):
                # 查找 g) 性能: 相关内容
                performance_pattern = r'g\)\s*性能[：:]\s*(.+?)(?=[a-h]\)|$|(?:\n[a-h]\)))'
                performance_match = re.search(performance_pattern, requirement_desc, re.DOTALL | re.IGNORECASE)
                
                if performance_match:
                    performance_content = performance_match.group(1).strip()
                    log_debug(f"从字符串中提取到性能内容: {performance_content[:100]}...", "performance_separator")
                    
                    # 验证性能内容不为空且不是"无"
                    if performance_content and performance_content.lower() not in ['无', 'none', 'n/a', '']:
                        return performance_content
                
                # 如果没有找到标准格式，尝试查找其他性能相关内容
                for keyword in self.performance_keywords_group1 + self.performance_keywords_group2:
                    if keyword in requirement_desc.lower():
                        # 尝试提取包含关键词的段落
                        lines = requirement_desc.split('\n')
                        for line in lines:
                            if keyword in line.lower() and '无' not in line:
                                log_debug(f"通过关键词 '{keyword}' 找到性能内容: {line[:50]}...", "performance_separator")
                                return line.strip()
            
            return None
            
        except Exception as e:
            log_warning(f"提取性能内容时出错: {e}", "performance_separator")
            return None
    
    def _create_performance_test_item(self, original_item: Dict[str, Any], performance_content: str, new_index: int) -> Dict[str, Any]:
        """
        创建性能测试项
        
        Args:
            original_item: 原始测试项
            performance_content: 性能相关内容
            new_index: 新的索引
            
        Returns:
            Dict[str, Any]: 性能测试项
        """
        try:
            # 基于原始测试项创建性能测试项
            performance_item = original_item.copy()
            
            # 生成性能测试项名称
            original_name = original_item.get('name', '未知功能')
            performance_name = f"{original_name}（性能测试）"
            
            # 生成新的标识符
            original_identifier = original_item.get('identifier', '')
            performance_identifier = self._generate_performance_identifier(original_identifier, new_index)
            
            # 🔧 修改：不再使用传统算法提取，而是标记为需要AI生成
            # 将完整的需求描述传递给AI，让AI来总结需求子项描述、测试项描述、测试方法
            
            # 获取完整的需求描述
            full_requirement_content = original_item.get('requirement_description', '')
            if isinstance(full_requirement_content, dict):
                full_requirement_content = self._dict_to_string(full_requirement_content)
            
            log_info(f"[PERFORMANCE_CREATE] 创建性能测试项，将由AI生成完整内容", "performance_separator")
            log_debug(f"[PERFORMANCE_CREATE] 完整需求内容长度: {len(str(full_requirement_content))}", "performance_separator")
            
            # 更新字段
            performance_item.update({
                'name': performance_name,
                'identifier': performance_identifier,
                'requirement_sub_description': '',  # 🔧 留空，让AI生成
                'test_description': '',  # 🔧 留空，让AI生成
                'test_method': '',       # 🔧 留空，让AI生成
                'test_type': '性能测试',
                'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，性能满足要求',  # 🔧 添加性能测试通过准则
                'original_test_item': original_name,
                'performance_content': performance_content,
                'full_requirement_for_ai': str(full_requirement_content),  # 🔧 新增：完整需求内容供AI使用
                'ai_generation_required': True  # 🔧 新增：标记需要AI生成完整内容
            })
            
            log_debug("创建性能测试项完成:", "performance_separator")
            log_debug(f"  原始名称: {original_name}", "performance_separator")
            log_debug(f"  性能名称: {performance_name}", "performance_separator")
            log_debug(f"  原始标识: {original_identifier}", "performance_separator")
            log_debug(f"  性能标识: {performance_identifier}", "performance_separator")
            log_debug(f"  追踪关系: {performance_item.get('traceability_relation', '')}", "performance_separator")
            log_debug(f"  章节编号: {performance_item.get('chapter_number', '')}", "performance_separator")
            log_debug(f"  AI生成标记: True（需要AI生成需求子项描述、测试描述、测试方法）", "performance_separator")
            
            return performance_item
            
        except Exception as e:
            log_error(f"创建性能测试项失败: {e}", "performance_separator")
            import traceback
            log_error(f"错误详情:\n{traceback.format_exc()}", "performance_separator")
            return original_item
    
    def _generate_performance_identifier(self, original_identifier: str, new_index: int) -> str:
        """
        生成性能测试项的标识符
        
        Args:
            original_identifier: 原始功能测试项的标识符
            new_index: 新的索引号（可能是浮点数）
            
        Returns:
            str: 生成的性能测试项标识符
        """
        # 🔧 修复：将浮点数转换为整数
        index_int = int(new_index)
        
        if not original_identifier:
            return f"PF{index_int:02d}"
        
        # 🔧 修复：性能测试项使用PF后缀，而不是FN后缀
        # 尝试从原始标识符中提取章节和编号
        match = re.search(r'-FN(\d+)$', original_identifier)
        if match:
            base_identifier = re.sub(r'-FN(\d+)$', '', original_identifier)
            return f"{base_identifier}-PF{index_int:02d}"
        else:
            return f"PF{index_int:02d}"
    
    def _dict_to_string(self, requirement_dict: Dict[str, Any]) -> str:
        """
        将字典格式的需求描述转换为字符串格式
        
        Args:
            requirement_dict: 需求描述字典
            
        Returns:
            str: 格式化后的需求描述字符串
        """
        try:
            if not isinstance(requirement_dict, dict):
                return str(requirement_dict)
            
            formatted_parts = []
            
            # 🔧 修复：按照标准格式输出，避免直接输出字段名
            # 定义字段映射关系，避免输出内部字段名
            field_mapping = [
                ('identifier', 'a) 标识号：'),
                ('description', 'b) 说明：'),
                ('entry_condition', 'c) 进入条件：'),
                ('input', 'd) 输入：'),
                ('output', 'e) 输出：'),
                ('processing', 'f) 处理：'),
                ('performance', 'g) 性能：'),
                ('constraints', 'h) 约束与限制：')
            ]
            
            # 按照标准格式组织内容
            for field_key, field_label in field_mapping:
                field_value = requirement_dict.get(field_key)
                if field_value and str(field_value).strip():
                    # 清理内容，移除可能的多余空白
                    clean_value = str(field_value).strip()
                    if clean_value and clean_value != '无' and clean_value != '':
                        formatted_parts.append(f"{field_label}{clean_value}")
            
            # 如果没有找到标准字段，尝试其他可能的字段
            if not formatted_parts:
                for key, value in requirement_dict.items():
                    # 🔧 修复：排除内部字段，避免出现constraints、chapter_number等字段名
                    if key not in ['constraints', 'chapter_number', 'identifier', 'description', 
                                 'entry_condition', 'input', 'output', 'processing', 'performance'] and value:
                        clean_value = str(value).strip()
                        if clean_value and clean_value != '无':
                            formatted_parts.append(clean_value)
            
            if formatted_parts:
                return '\n'.join(formatted_parts)
            else:
                # 🔧 修复：如果没有有效内容，返回空字符串而不是原字典的字符串表示
                return ""
            
        except Exception as e:
            log_warning(f"字典转字符串失败: {e}", "performance_separator")
            # 🔧 修复：出错时返回空字符串，避免输出原始字典内容
            return ""
    
    def is_performance_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断测试项是否为性能测试项
        
        Args:
            test_item: 测试项
            
        Returns:
            是否为性能测试项
        """
        return test_item.get('_is_performance_item', False) or \
               test_item.get('test_type', '') == '性能测试' or \
               '性能测试' in test_item.get('name', '')
    
    def get_performance_statistics(self, test_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取性能测试项和边界测试项统计信息
        
        Args:
            test_items: 测试项列表
            
        Returns:
            统计信息字典
        """
        try:
            total_items = len(test_items)
            performance_items = [item for item in test_items if self.is_performance_item(item)]
            boundary_items = [item for item in test_items if self.is_boundary_item(item)]
            functional_items = [item for item in test_items 
                               if not self.is_performance_item(item) and not self.is_boundary_item(item)]
            
            stats = {
                'total_items': total_items,
                'functional_items': len(functional_items),
                'performance_items': len(performance_items),
                'boundary_items': len(boundary_items),  # 新增边界测试项统计
                'performance_ratio': len(performance_items) / total_items if total_items > 0 else 0,
                'boundary_ratio': len(boundary_items) / total_items if total_items > 0 else 0,  # 新增边界测试项比例
                'performance_item_names': [item.get('name', '') for item in performance_items],
                'boundary_item_names': [item.get('name', '') for item in boundary_items]  # 新增边界测试项名称列表
            }
            
            log_info(f"测试项统计: 总计{total_items}项，功能{len(functional_items)}项，性能{len(performance_items)}项，边界{len(boundary_items)}项", "performance_separator")
            
            return stats
            
        except Exception as e:
            log_warning(f"获取测试统计失败: {e}", "performance_separator")
            return {
                'total_items': len(test_items),
                'functional_items': len(test_items),
                'performance_items': 0,
                'boundary_items': 0,
                'performance_ratio': 0,
                'boundary_ratio': 0,
                'performance_item_names': [],
                'boundary_item_names': []
            }
    
    def _extract_boundary_content(self, test_item: Dict[str, Any]) -> Optional[str]:
        """
        从测试项中提取边界相关内容（基于hanshutiqu_kaifa项目的识别逻辑）
        
        Args:
            test_item: 测试项
            
        Returns:
            边界内容字符串，如果没有则返回None
        """
        try:
            test_name = test_item.get('name', '')
            requirement_desc = test_item.get('requirement_description', '')
            
            if not requirement_desc:
                return None
            
            # 首先检查是否在排除列表中
            for exclude_keyword in self.boundary_exclude_keywords:
                if exclude_keyword in test_name:
                    log_debug(f"测试项 '{test_name}' 包含排除关键词 '{exclude_keyword}'，跳过边界测试", "performance_separator")
                    return None
            
            # 修复：处理字典类型的requirement_description，排除性能部分
            content_for_detection = ""
            content_for_extraction = requirement_desc  # 用于提取的完整内容
            
            if isinstance(requirement_desc, dict):
                # 如果是字典，排除performance字段后合并其他字段内容进行检测
                for key, value in requirement_desc.items():
                    if value:
                        if key == 'performance':
                            log_debug(f"排除性能内容进行边界检测", "performance_separator")
                        else:
                            content_for_detection += f"{key}: {str(value)} "
                log_debug(f"从字典构造检测文本（已排除性能）: {content_for_detection[:100]}...", "performance_separator")
            elif isinstance(requirement_desc, str):
                # 如果是字符串，排除 g) 性能: 部分进行检测
                import re
                performance_pattern = r'g\)\s*性能[：:]\s*(.+?)(?=[a-h]\)|$|(?:\n[a-h]\)))'
                performance_match = re.search(performance_pattern, requirement_desc, re.DOTALL | re.IGNORECASE)
                
                if performance_match:
                    log_debug(f"排除性能内容进行边界检测", "performance_separator")
                    # 从检测文本中移除性能部分
                    content_for_detection = re.sub(performance_pattern, '', requirement_desc, flags=re.DOTALL | re.IGNORECASE)
                else:
                    content_for_detection = requirement_desc
                log_debug(f"使用字符串检测文本（已排除性能）: {content_for_detection[:100]}...", "performance_separator")
            else:
                log_warning(f"未知的requirement_description类型: {type(requirement_desc)}", "performance_separator")
                return None
            
            # 检查两组边界关键词（基于排除性能后的内容）
            group1_found = False
            group2_found = False
            
            for keyword in self.boundary_keywords_group1:
                if keyword in content_for_detection:
                    group1_found = True
                    log_debug(f"在需求描述中找到边界关键词组1: '{keyword}'", "performance_separator")
                    break
            
            for keyword in self.boundary_keywords_group2:
                if keyword in content_for_detection:
                    group2_found = True
                    log_debug(f"在需求描述中找到边界关键词组2: '{keyword}'", "performance_separator")
                    break
            
            # 需要两组关键词都存在才认为是边界测试项
            if group1_found and group2_found:
                log_debug(f"测试项 '{test_name}' 满足边界测试条件（已排除性能内容）", "performance_separator")
                # 修复：返回完整的原始内容，让_extract_boundary_specific_content来精确提取
                return content_for_extraction  # 返回完整内容供后续精确提取
            
            return None
            
        except Exception as e:
            log_warning(f"提取边界内容时出错: {e}", "performance_separator")
            return None
    
    def _create_boundary_test_item(self, original_item: Dict[str, Any], boundary_content: str, new_index: int) -> Dict[str, Any]:
        """
        创建边界测试项
        
        Args:
            original_item: 原始测试项
            boundary_content: 边界相关内容
            new_index: 新的索引
            
        Returns:
            Dict[str, Any]: 边界测试项
        """
        try:
            # 基于原始测试项创建边界测试项
            boundary_item = original_item.copy()
            
            # 生成边界测试项名称
            original_name = original_item.get('name', '未知功能')
            boundary_name = f"{original_name}（边界测试）"
            
            # 生成新的标识符
            original_identifier = original_item.get('identifier', '')
            boundary_identifier = self._generate_boundary_identifier(original_identifier, new_index)
            
            # 🔧 修改：不再使用传统算法提取，而是标记为需要AI生成
            # 将完整的需求描述传递给AI，让AI来总结需求子项描述、测试项描述、测试方法
            
            # 获取完整的需求描述
            full_requirement_content = original_item.get('requirement_description', '')
            if isinstance(full_requirement_content, dict):
                full_requirement_content = self._dict_to_string(full_requirement_content)
            
            log_info(f"[BOUNDARY_CREATE] 创建边界测试项，将由AI生成完整内容", "performance_separator")
            log_debug(f"[BOUNDARY_CREATE] 完整需求内容长度: {len(str(full_requirement_content))}", "performance_separator")
            
            # 更新字段
            boundary_item.update({
                'name': boundary_name,
                'identifier': boundary_identifier,
                'requirement_sub_description': '',  # 🔧 留空，让AI生成
                'test_description': '',  # 🔧 留空，让AI生成
                'test_method': '',       # 🔧 留空，让AI生成
                'test_type': '边界测试',
                'pass_criteria': '各测试步骤、测试用例执行结果与预期一致，边界处理正确',  # 🔧 添加边界测试通过准则
                'original_test_item': original_name,
                'boundary_content': boundary_content,
                'full_requirement_for_ai': str(full_requirement_content),  # 🔧 新增：完整需求内容供AI使用
                'ai_generation_required': True  # 🔧 新增：标记需要AI生成完整内容
            })
            
            log_debug("创建边界测试项完成:", "performance_separator")
            log_debug(f"  原始名称: {original_name}", "performance_separator")
            log_debug(f"  边界名称: {boundary_name}", "performance_separator")
            log_debug(f"  原始标识: {original_identifier}", "performance_separator")
            log_debug(f"  边界标识: {boundary_identifier}", "performance_separator")
            log_debug(f"  追踪关系: {boundary_item.get('traceability_relation', '')}", "performance_separator")
            log_debug(f"  章节编号: {boundary_item.get('chapter_number', '')}", "performance_separator")
            log_debug(f"  AI生成标记: True（需要AI生成需求子项描述、测试描述、测试方法）", "performance_separator")
            
            return boundary_item
            
        except Exception as e:
            log_error(f"创建边界测试项失败: {e}", "performance_separator")
            import traceback
            log_error(f"错误详情:\n{traceback.format_exc()}", "performance_separator")
            return original_item
    
    def _generate_boundary_identifier(self, original_identifier: str, new_index: int) -> str:
        """
        生成边界测试项的标识符
        
        Args:
            original_identifier: 原始功能测试项的标识符
            new_index: 新的索引号（可能是浮点数）
            
        Returns:
            str: 生成的边界测试项标识符
        """
        # 🔧 修复：将浮点数转换为整数
        index_int = int(new_index)
        
        if not original_identifier:
            return f"BD{index_int:02d}"
        
        # 🔧 修复：边界测试项使用BD后缀，而不是BT后缀
        # 尝试从原始标识符中提取章节和编号
        match = re.search(r'-FN(\d+)$', original_identifier)
        if match:
            base_identifier = re.sub(r'-FN(\d+)$', '', original_identifier)
            return f"{base_identifier}-BD{index_int:02d}"
        else:
            return f"BD{index_int:02d}"
    
    def _dict_to_string(self, requirement_dict: Dict[str, Any]) -> str:
        """
        将字典格式的需求描述转换为字符串格式
        
        Args:
            requirement_dict: 需求描述字典
            
        Returns:
            str: 格式化后的需求描述字符串
        """
        try:
            if not isinstance(requirement_dict, dict):
                return str(requirement_dict)
            
            formatted_parts = []
            
            # 🔧 修复：按照标准格式输出，避免直接输出字段名
            # 定义字段映射关系，避免输出内部字段名
            field_mapping = [
                ('identifier', 'a) 标识号：'),
                ('description', 'b) 说明：'),
                ('entry_condition', 'c) 进入条件：'),
                ('input', 'd) 输入：'),
                ('output', 'e) 输出：'),
                ('processing', 'f) 处理：'),
                ('performance', 'g) 性能：'),
                ('constraints', 'h) 约束与限制：')
            ]
            
            # 按照标准格式组织内容
            for field_key, field_label in field_mapping:
                field_value = requirement_dict.get(field_key)
                if field_value and str(field_value).strip():
                    # 清理内容，移除可能的多余空白
                    clean_value = str(field_value).strip()
                    if clean_value and clean_value != '无' and clean_value != '':
                        formatted_parts.append(f"{field_label}{clean_value}")
            
            # 如果没有找到标准字段，尝试其他可能的字段
            if not formatted_parts:
                for key, value in requirement_dict.items():
                    # 🔧 修复：排除内部字段，避免出现constraints、chapter_number等字段名
                    if key not in ['constraints', 'chapter_number', 'identifier', 'description', 
                                 'entry_condition', 'input', 'output', 'processing', 'performance'] and value:
                        clean_value = str(value).strip()
                        if clean_value and clean_value != '无':
                            formatted_parts.append(clean_value)
            
            if formatted_parts:
                return '\n'.join(formatted_parts)
            else:
                # 🔧 修复：如果没有有效内容，返回空字符串而不是原字典的字符串表示
                return ""
            
        except Exception as e:
            log_warning(f"字典转字符串失败: {e}", "performance_separator")
            # 🔧 修复：出错时返回空字符串，避免输出原始字典内容
            return ""
    
    def is_performance_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断测试项是否为性能测试项
        
        Args:
            test_item: 测试项
            
        Returns:
            是否为性能测试项
        """
        return test_item.get('_is_performance_item', False) or \
               test_item.get('test_type', '') == '性能测试' or \
               '性能测试' in test_item.get('name', '')
    
    def get_performance_statistics(self, test_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取性能测试项和边界测试项统计信息
        
        Args:
            test_items: 测试项列表
            
        Returns:
            统计信息字典
        """
        try:
            total_items = len(test_items)
            performance_items = [item for item in test_items if self.is_performance_item(item)]
            boundary_items = [item for item in test_items if self.is_boundary_item(item)]
            functional_items = [item for item in test_items 
                               if not self.is_performance_item(item) and not self.is_boundary_item(item)]
            
            stats = {
                'total_items': total_items,
                'functional_items': len(functional_items),
                'performance_items': len(performance_items),
                'boundary_items': len(boundary_items),  # 新增边界测试项统计
                'performance_ratio': len(performance_items) / total_items if total_items > 0 else 0,
                'boundary_ratio': len(boundary_items) / total_items if total_items > 0 else 0,  # 新增边界测试项比例
                'performance_item_names': [item.get('name', '') for item in performance_items],
                'boundary_item_names': [item.get('name', '') for item in boundary_items]  # 新增边界测试项名称列表
            }
            
            log_info(f"测试项统计: 总计{total_items}项，功能{len(functional_items)}项，性能{len(performance_items)}项，边界{len(boundary_items)}项", "performance_separator")
            
            return stats
            
        except Exception as e:
            log_warning(f"获取测试统计失败: {e}", "performance_separator")
            return {
                'total_items': len(test_items),
                'functional_items': len(test_items),
                'performance_items': 0,
                'boundary_items': 0,
                'performance_ratio': 0,
                'boundary_ratio': 0,
                'performance_item_names': [],
                'boundary_item_names': []
            }
    
    def _extract_boundary_specific_content(self, requirement_description: str) -> str:
        """
        从需求描述中提取边界相关的具体内容
        
        Args:
            requirement_description: 完整的需求描述或排除性能后的内容
            
        Returns:
            str: 边界相关的具体条目内容
        """
        try:
            if not requirement_description:
                return ""
            
            boundary_items = []
            all_boundary_keywords = self.boundary_keywords_group1 + self.boundary_keywords_group2
            
            # 🔧 修复：字典格式处理，严格排除性能字段
            if isinstance(requirement_description, dict):
                # 定义字段映射关系，排除性能字段
                field_mapping = [
                    ('entry_condition', 'c) 进入条件：'),
                    ('input', 'd) 输入：'),
                    ('output', 'e) 输出：'),
                    ('processing', 'f) 处理：'),
                    ('constraints', 'h) 约束与限制：')
                ]
                
                for field_key, field_label in field_mapping:
                    field_value = requirement_description.get(field_key)
                    if field_value and str(field_value).strip():
                        value_str = str(field_value).strip()
                        if value_str and value_str != '无':
                            full_section = f"{field_label}{value_str}"
                            # 检查是否包含边界关键词且不包含性能关键词
                            has_boundary_keywords = any(keyword in full_section for keyword in all_boundary_keywords)
                            has_performance_keywords = any(keyword in full_section for keyword in ['性能', '响应时间', '处理时间', '延迟', '≤', '≥', '<', '>'])
                            
                            if has_boundary_keywords and not has_performance_keywords:
                                boundary_items.append(full_section)
                                log_debug(f"提取边界条目: {full_section[:50]}...", "performance_separator")
            
            # 🔧 修复：字符串格式处理，更精确地排除性能段落
            elif isinstance(requirement_description, str):
                import re
                
                # 更精确的性能段落排除模式
                performance_patterns = [
                    r'g\)\s*性能[：:]\s*[^h]*?(?=h\)|$)',  # g) 性能: ... 直到 h) 或结尾
                    r'g\)\s*性能[：:][^a-h]*?(?=[a-h]\)|$)',  # g) 性能: ... 直到下一个字母标识或结尾
                ]
                
                content_without_performance = requirement_description
                for pattern in performance_patterns:
                    content_without_performance = re.sub(pattern, '', content_without_performance, flags=re.DOTALL | re.IGNORECASE)
                
                log_debug(f"排除性能部分后的内容: {content_without_performance[:100]}...", "performance_separator")
                
                # 按标准格式段落分割（c, d, e, f, h）
                section_patterns = [
                    r'(c\)\s*进入条件[：:][^a-h]*?)(?=[a-h]\)|$)',
                    r'(d\)\s*输入[：:][^a-h]*?)(?=[a-h]\)|$)',
                    r'(e\)\s*输出[：:][^a-h]*?)(?=[a-h]\)|$)',
                    r'(f\)\s*处理[：:][^a-h]*?)(?=[a-h]\)|$)',
                    r'(h\)\s*约束[与和]?限制[：:][^a-h]*?)(?=[a-h]\)|$)'
                ]
                
                for pattern in section_patterns:
                    matches = re.findall(pattern, content_without_performance, re.DOTALL | re.IGNORECASE)
                    for match in matches:
                        section_content = match.strip()
                        if section_content:
                            # 检查是否包含边界关键词且不包含性能关键词
                            has_boundary_keywords = any(keyword in section_content for keyword in all_boundary_keywords)
                            has_performance_keywords = any(keyword in section_content for keyword in ['性能', '响应时间', '处理时间', '延迟', '≤', '≥', '<', '>'])
                            
                            if has_boundary_keywords and not has_performance_keywords:
                                boundary_items.append(section_content)
                                log_debug(f"提取边界条目: {section_content[:50]}...", "performance_separator")
                
                # 如果没有找到标准格式，尝试按句子提取
                if not boundary_items:
                    sentences = re.split(r'[。；\n]', content_without_performance)
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        
                        has_boundary_keywords = any(keyword in sentence for keyword in all_boundary_keywords)
                        has_performance_keywords = any(keyword in sentence for keyword in ['性能', '响应时间', '处理时间', '延迟', '≤', '≥', '<', '>'])
                        
                        if has_boundary_keywords and not has_performance_keywords:
                            boundary_items.append(sentence)
                            log_debug(f"按句子提取边界条目: {sentence[:50]}...", "performance_separator")
            
            # 返回提取的边界内容
            if boundary_items:
                result = '\n'.join(boundary_items)
                log_info(f"成功提取边界测试内容，共{len(boundary_items)}个条目", "performance_separator")
                return result
            else:
                log_warning("未找到边界测试相关内容", "performance_separator")
                return "未找到明确的边界限制条目，请参考需求文档中的边界条件相关描述。"
            
        except Exception as e:
            log_error(f"提取边界测试具体内容失败: {e}", "performance_separator")
            return "边界内容提取失败，请手动检查需求文档。"
    
    def _extract_boundary_items_from_text(self, text: str, prefix: str = "") -> list:
        """
        从文本中提取包含边界关键词的具体条目
        
        Args:
            text: 要分析的文本
            prefix: 可选的前缀（如字段名）- 通常不使用
            
        Returns:
            list: 包含边界关键词的条目列表
        """
        try:
            boundary_items = []
            all_boundary_keywords = self.boundary_keywords_group1 + self.boundary_keywords_group2
            
            # 按多种分隔符分割文本
            # 支持：换行符、分号、句号、破折号、项目符号等
            import re
            separators = ['\n', '；', '。', ';', '.', '- ', '•', '·', '○', '①', '②', '③', '④', '⑤']
            
            # 🔧 修复：更精确的分割逻辑
            # 先按换行符分割，然后按其他分隔符进一步分割
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 对每行按其他分隔符进一步分割
                parts = [line]  # 初始化为整行
                
                for separator in separators[1:]:  # 跳过换行符，已经处理过了
                    new_parts = []
                    for part in parts:
                        if separator in part:
                            split_parts = part.split(separator)
                            new_parts.extend([p.strip() for p in split_parts if p.strip()])
                        else:
                            new_parts.append(part)
                    parts = new_parts
                
                # 检查每个部分是否包含边界关键词
                for part in parts:
                    part = part.strip()
                    if part and any(keyword in part for keyword in all_boundary_keywords):
                        # 🔧 修复：清理格式，移除多余的符号
                        cleaned_part = part.strip('- •·○')
                        if cleaned_part and cleaned_part not in boundary_items:
                            boundary_items.append(cleaned_part)
            
            return boundary_items
            
        except Exception as e:
            log_warning(f"从文本提取边界条目时出错: {e}", "performance_separator")
            return []
    
    def is_boundary_item(self, test_item: Dict[str, Any]) -> bool:
        """
        判断测试项是否为边界测试项
        
        Args:
            test_item: 测试项
            
        Returns:
            是否为边界测试项
        """
        return test_item.get('_is_boundary_item', False) or \
               test_item.get('test_type', '') == '边界测试' or \
               '边界测试' in test_item.get('name', '') 

    def _format_functional_test_item(self, test_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化功能测试项，确保包含b)说明字段
        
        Args:
            test_item: 原始功能测试项
            
        Returns:
            格式化后的功能测试项
        """
        try:
            formatted_item = test_item.copy()
            requirement_desc = test_item.get('requirement_description', '')
            
            # 🔧 修复：如果是字典格式，需要转换为标准格式字符串
            if isinstance(requirement_desc, dict):
                formatted_parts = []
                
                # 1. 标识号
                if requirement_desc.get('identifier') or requirement_desc.get('标识号'):
                    identifier = requirement_desc.get('identifier') or requirement_desc.get('标识号')
                    formatted_parts.append(f"a) 标识号：{identifier}")
                
                # 2. 说明 - 🔧 关键修复：确保b)说明字段存在
                description_content = (
                    requirement_desc.get('description') or 
                    requirement_desc.get('说明') or
                    ''
                )
                
                # 特殊处理entry_condition中包含说明的情况
                if not description_content:
                    entry_condition_value = requirement_desc.get('entry_condition', '')
                    if entry_condition_value and entry_condition_value.startswith('说明：'):
                        description_content = entry_condition_value.replace('说明：', '').strip()
                
                if description_content and description_content.strip():
                    formatted_parts.append(f"b) 说明：{description_content.strip()}")
                
                # 3. 进入条件
                entry_condition = requirement_desc.get('entry_condition', '')
                if entry_condition and not entry_condition.startswith('说明：'):
                    formatted_parts.append(f"c) 进入条件：{entry_condition}")
                elif requirement_desc.get('进入条件'):
                    formatted_parts.append(f"c) 进入条件：{requirement_desc['进入条件']}")
                
                # 4. 输入
                input_content = requirement_desc.get('input') or requirement_desc.get('输入')
                if input_content:
                    formatted_parts.append(f"d) 输入：{input_content}")
                
                # 5. 输出
                output_content = requirement_desc.get('output') or requirement_desc.get('输出')
                if output_content:
                    formatted_parts.append(f"e) 输出：{output_content}")
                
                # 6. 处理
                processing_content = requirement_desc.get('processing') or requirement_desc.get('处理')
                if processing_content:
                    formatted_parts.append(f"f) 处理：{processing_content}")
                
                # 7. 性能
                performance_content = requirement_desc.get('performance') or requirement_desc.get('性能')
                if performance_content:
                    formatted_parts.append(f"g) 性能：{performance_content}")
                
                # 8. 约束与限制
                constraints_content = requirement_desc.get('constraints') or requirement_desc.get('约束与限制')
                if constraints_content:
                    formatted_parts.append(f"h) 约束与限制：{constraints_content}")
                
                # 更新为格式化后的字符串
                formatted_requirement_desc = '\n'.join(formatted_parts)
                formatted_item['requirement_description'] = formatted_requirement_desc
                formatted_item['requirement_sub_description'] = formatted_requirement_desc
                
                log_debug(f"功能测试项格式化完成: {formatted_item.get('name', '')}", "performance_separator")
                log_debug(f"  包含b)说明: {'✅' if 'b) 说明：' in formatted_requirement_desc else '❌'}", "performance_separator")
            
            return formatted_item
            
        except Exception as e:
            log_warning(f"格式化功能测试项失败: {e}", "performance_separator")
            return test_item.copy()  # 返回原始项的副本作为备用 

    def _has_performance_content(self, test_item: Dict[str, Any]) -> bool:
        """检查测试项是否包含性能测试内容"""
        try:
            requirement_description = test_item.get('requirement_description', '')
            if not requirement_description:
                return False
            
            # 使用性能测试检测逻辑
            return self._is_performance_test_item(requirement_description)
            
        except Exception as e:
            log_debug(f"检查性能内容时发生错误: {e}", "performance_separator")
            return False
    
    def _is_performance_test_item(self, requirement_description: str) -> bool:
        """
        判断是否为性能测试项
        
        Args:
            requirement_description: 需求描述
            
        Returns:
            bool: 是否为性能测试项
        """
        try:
            text_to_check = str(requirement_description)
            
            # 检查性能关键词组合
            has_group1 = any(keyword in text_to_check for keyword in self.performance_keywords_group1)
            has_group2 = any(keyword in text_to_check for keyword in self.performance_keywords_group2)
            
            return has_group1 or has_group2  # 性能测试只需满足其中一组即可
            
        except Exception as e:
            log_debug(f"性能测试项判断失败: {e}", "performance_separator")
            return False
    
    def _has_boundary_content(self, test_item: Dict[str, Any]) -> bool:
        """检查测试项是否包含边界测试内容"""
        try:
            requirement_description = test_item.get('requirement_description', '')
            if not requirement_description:
                return False
            
            test_name = test_item.get('name', '')
            
            # 首先检查是否在排除列表中
            for exclude_keyword in self.boundary_exclude_keywords:
                if exclude_keyword in test_name:
                    log_debug(f"测试项 '{test_name}' 包含排除关键词 '{exclude_keyword}'，跳过边界测试", "performance_separator")
                    return False
            
            # 处理字典类型的requirement_description，排除性能部分
            content_for_detection = ""
            
            if isinstance(requirement_description, dict):
                # 如果是字典，排除performance字段后合并其他字段内容进行检测
                for key, value in requirement_description.items():
                    if value:
                        if key == 'performance':
                            log_debug(f"排除性能内容进行边界检测", "performance_separator")
                        else:
                            content_for_detection += f"{key}: {str(value)} "
                log_debug(f"从字典构造检测文本（已排除性能）: {content_for_detection[:100]}...", "performance_separator")
            elif isinstance(requirement_description, str):
                # 如果是字符串，排除 g) 性能: 部分进行检测
                import re
                performance_pattern = r'g\)\s*性能[：:]\s*(.+?)(?=[a-h]\)|$|(?:\n[a-h]\)))'
                performance_match = re.search(performance_pattern, requirement_description, re.DOTALL | re.IGNORECASE)
                
                if performance_match:
                    log_debug(f"排除性能内容进行边界检测", "performance_separator")
                    # 从检测文本中移除性能部分
                    content_for_detection = re.sub(performance_pattern, '', requirement_description, flags=re.DOTALL | re.IGNORECASE)
                else:
                    content_for_detection = requirement_description
                log_debug(f"使用字符串检测文本（已排除性能）: {content_for_detection[:100]}...", "performance_separator")
            else:
                log_warning(f"未知的requirement_description类型: {type(requirement_description)}", "performance_separator")
                return False
            
            # 检查两组边界关键词（基于排除性能后的内容）
            group1_found = False
            group2_found = False
            
            for keyword in self.boundary_keywords_group1:
                if keyword in content_for_detection:
                    group1_found = True
                    log_debug(f"在需求描述中找到边界关键词组1: '{keyword}'", "performance_separator")
                    break
            
            for keyword in self.boundary_keywords_group2:
                if keyword in content_for_detection:
                    group2_found = True
                    log_debug(f"在需求描述中找到边界关键词组2: '{keyword}'", "performance_separator")
                    break
            
            # 需要两组关键词都存在才认为是边界测试项
            if group1_found and group2_found:
                log_debug(f"测试项 '{test_name}' 满足边界测试条件（已排除性能内容）", "performance_separator")
                return True
            
            return False
            
        except Exception as e:
            log_debug(f"检查边界内容时发生错误: {e}", "performance_separator")
            return False
    
    # 🔧 新增：余量测试检测方法
    def _has_allowance_content(self, test_item: Dict[str, Any]) -> bool:
        """检查测试项是否包含余量测试内容"""
        try:
            requirement_description = test_item.get('requirement_description', '')
            if not requirement_description:
                return False
            
            return self._is_allowance_test_item(requirement_description)
            
        except Exception as e:
            log_debug(f"检查余量内容时发生错误: {e}", "performance_separator")
            return False
    
    # 🔧 已删除：不再检测需求内容中的强度测试项
    # 强度测试项现在仅由固定定义提供 

    def _is_boundary_test_item(self, requirement_description: str) -> bool:
        """
        判断是否为边界测试项
        
        Args:
            requirement_description: 需求描述（字符串或字典）
            
        Returns:
            bool: 是否为边界测试项
        """
        try:
            # 🔧 修复：更严格地排除性能内容
            search_text = ""
            
            if isinstance(requirement_description, dict):
                # 如果是字典，排除性能字段后合并其他字段内容
                for key, value in requirement_description.items():
                    if key != 'performance' and value:  # 排除性能字段
                        search_text += f"{str(value)} "
            else:
                # 如果是字符串，排除 g) 性能: 部分
                import re
                # 🔧 增强：更精确的性能段落排除模式
                performance_patterns = [
                    r'g\)\s*性能[：:]\s*[^h]*?(?=h\)|$)',  # g) 性能: ... 直到 h) 或结尾
                    r'g\)\s*性能[：:][^a-h]*?(?=[a-h]\)|$)',  # g) 性能: ... 直到下一个字母标识或结尾
                    r'性能[：:][^。]*?[。\n]',  # 性能: ... 直到句号或换行
                ]
                
                search_text = str(requirement_description)
                for pattern in performance_patterns:
                    search_text = re.sub(pattern, '', search_text, flags=re.DOTALL | re.IGNORECASE)
            
            # 清理搜索文本
            search_text = search_text.strip()
            if not search_text:
                return False
            
            # 🔧 修复：更严格的边界关键词检查
            # 检查边界关键词组合，必须两组都有
            has_group1 = any(keyword in search_text for keyword in self.boundary_keywords_group1)
            has_group2 = any(keyword in search_text for keyword in self.boundary_keywords_group2)
            
            # 🔧 新增：额外检查，确保不包含性能相关关键词
            performance_check_keywords = ['≤', '≥', '<', '>', '秒', '毫秒', '微秒', '次/秒', 'ms', 's', '响应时间', '处理时间', '延迟', '性能', '效率', '速度', '吞吐量']
            has_performance_keywords = any(keyword in search_text for keyword in performance_check_keywords)
            
            # 只有在有边界关键词且没有性能关键词时才认为是边界测试项
            result = has_group1 and has_group2 and not has_performance_keywords
            
            if result:
                log_debug(f"检测到边界测试项 - 搜索文本: {search_text[:100]}...", "performance_separator")
            
            return result
            
        except Exception as e:
            log_debug(f"边界测试项判断失败: {e}", "performance_separator")
            return False
    
    # 🔧 新增：余量测试项判断方法
    def _is_allowance_test_item(self, requirement_description: str) -> bool:
        """
        判断是否为余量测试项
        
        Args:
            requirement_description: 需求描述
            
        Returns:
            bool: 是否为余量测试项
        """
        try:
            text_to_check = str(requirement_description)
            
            # 检查余量关键词组合
            has_group1 = any(keyword in text_to_check for keyword in self.allowance_keywords_group1)
            has_group2 = any(keyword in text_to_check for keyword in self.allowance_keywords_group2)
            
            return has_group1 and has_group2
            
        except Exception as e:
            log_debug(f"余量测试项判断失败: {e}", "performance_separator")
            return False
    
    # 🔧 已删除：不再从需求内容中判断强度测试项
    # 强度测试项现在仅由固定定义提供 

    def _extract_performance_requirement_from_content(self, full_content: str, performance_content: str) -> str:
        """
        从完整需求内容中提取性能需求描述
        
        Args:
            full_content: 完整的需求内容
            performance_content: 性能相关内容
            
        Returns:
            str: 提取的性能需求描述
        """
        try:
            # 优先查找"g) 性能:"段落
            if "g) 性能:" in full_content:
                # 提取g) 性能:段落的完整内容
                lines = full_content.split('\n')
                performance_lines = []
                in_performance_section = False
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("g) 性能:") or line.startswith("g)性能:"):
                        in_performance_section = True
                        performance_lines.append(line)
                    elif in_performance_section:
                        if line.startswith(("h)", "i)", "j)", "k)", "l)", "m)", "n)")):
                            # 遇到下一个段落，停止
                            break
                        elif line:
                            performance_lines.append(line)
                
                if performance_lines:
                    return '\n'.join(performance_lines)
            
            # 如果没有找到"g) 性能:"段落，使用传入的performance_content
            if performance_content:
                return f"g) 性能：\n{performance_content}"
            
            # 兜底：从完整内容中查找包含性能指标的内容
            performance_keywords = ['≤', '≥', '<', '>', '秒', '毫秒', '微秒', '次/秒', 'ms', 's', '响应时间', '处理时间', '延迟', 'TPS', 'QPS']
            lines = full_content.split('\n')
            performance_lines = []
            
            for line in lines:
                line = line.strip()
                if any(keyword in line for keyword in performance_keywords):
                    performance_lines.append(line)
            
            if performance_lines:
                return f"g) 性能：\n" + '\n'.join(performance_lines)
            
            # 最后兜底
            return f"g) 性能：\n{performance_content}" if performance_content else "g) 性能：\n未找到具体性能要求"
            
        except Exception as e:
            log_error(f"提取性能需求描述失败: {e}", "performance_separator")
            return f"g) 性能：\n{performance_content}" if performance_content else "g) 性能：\n未找到具体性能要求"
    
    # 🔧 已删除：不再从需求内容中提取强度测试项
    # 强度测试项现在仅由 data_processor.py 中的固定强度测试项提供 

    def _extract_boundary_requirement_from_content(self, full_content: str, boundary_content: str) -> str:
        """
        从完整需求内容中提取边界需求描述
        
        Args:
            full_content: 完整的需求内容
            boundary_content: 边界相关内容
            
        Returns:
            str: 提取的边界需求描述
        """
        try:
            # 查找包含边界关键词的内容，但排除性能段落
            lines = full_content.split('\n')
            boundary_lines = []
            in_performance_section = False
            
            boundary_keywords = ['至少', '最少', '不少于', '不超过', '最多', '范围', '区间', '边界', '限制', '约束']
            
            for line in lines:
                line = line.strip()
                
                # 检查是否进入性能段落
                if line.startswith("g) 性能:") or line.startswith("g)性能:"):
                    in_performance_section = True
                    continue
                elif line.startswith(("h)", "i)", "j)", "k)", "l)", "m)", "n)")):
                    in_performance_section = False
                
                # 跳过性能段落
                if in_performance_section:
                    continue
                
                # 检查是否包含边界关键词
                if line and any(keyword in line for keyword in boundary_keywords):
                    boundary_lines.append(line)
            
            if boundary_lines:
                return '\n'.join(boundary_lines)
            
            # 如果没有找到边界内容，使用传入的boundary_content
            if boundary_content:
                return boundary_content
            
            # 最后兜底
            return "未找到具体边界要求"
            
        except Exception as e:
            log_error(f"提取边界需求描述失败: {e}", "performance_separator")
            return boundary_content if boundary_content else "未找到具体边界要求" 