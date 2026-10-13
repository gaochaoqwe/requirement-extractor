"""
配置项测试问题报告单数据处理器

负责处理和组织配置项测试中问题报告单所需的数据。
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemIssueReportDataProcessor:
    """配置项测试问题报告单数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.logger = logger
    
    def organize_issue_report_data(
        self,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: List[str],
        ceshiren_name: str,
        kaifarenxinxi: List[str],
        ceshileixing: str = "配置项测试",
        issue_count: int = 16
    ) -> Dict[str, Any]:
        """
        组织配置项测试问题报告单数据
        
        Args:
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求列表
            ceshiren_name: 测试人员姓名
            kaifarenxinxi: 开发人员信息列表 [姓名, 研制部门]
            ceshileixing: 测试类型
            issue_count: 问题数量
            
        Returns:
            Dict[str, Any]: 组织后的问题报告数据
        """
        try:
            # 组织基本信息
            basic_info = self._organize_basic_info(
                ruanjian_xinxi, ruanjian_name, ceshiren_name, 
                kaifarenxinxi, ceshileixing
            )
            
            # 组织问题编号信息
            issue_numbering = self._organize_issue_numbering(
                ruanjian_xinxi, ceshileixing, issue_count
            )
            
            # 组织问题分类信息
            issue_classification = self._organize_issue_classification(issue_count)
            
            # 组织时间信息
            time_info = self._organize_time_info()
            
            # 组织问题描述模板
            description_templates = self._get_description_templates()
            
            # 组织固定值信息
            fixed_values = self._get_fixed_values()
            
            # 组织完整的问题报告数据
            issue_report_data = {
                'basic_info': basic_info,
                'issue_numbering': issue_numbering,
                'issue_classification': issue_classification,
                'time_info': time_info,
                'description_templates': description_templates,
                'fixed_values': fixed_values,
                'issue_count': issue_count,
                'change_requirements': diama_biangeng_xuqiu
            }
            
            self.logger.debug(f"配置项测试问题报告单数据组织完成: {issue_report_data}")
            return issue_report_data
            
        except Exception as e:
            self.logger.error(f"组织配置项测试问题报告单数据时发生错误: {str(e)}")
            raise
    
    def _organize_basic_info(
        self, 
        ruanjian_xinxi: Dict[str, List[str]], 
        ruanjian_name: str, 
        ceshiren_name: str, 
        kaifarenxinxi: List[str], 
        ceshileixing: str
    ) -> Dict[str, Any]:
        """组织基本信息"""
        ruanjian_version = ruanjian_xinxi.get('被测软件版本', [''])[0]
        ruanjian_biaoshi = ruanjian_xinxi.get('软件标识', [''])[0]
        kaifaren = kaifarenxinxi[0] if kaifarenxinxi else ""
        
        return {
            'software_name': ruanjian_name,
            'software_version': ruanjian_version,
            'software_id': ruanjian_biaoshi,
            'tester_name': ceshiren_name,
            'developer_name': kaifaren,
            'test_type': ceshileixing
        }
    
    def _organize_issue_numbering(
        self, 
        ruanjian_xinxi: Dict[str, List[str]], 
        ceshileixing: str, 
        issue_count: int
    ) -> Dict[str, Any]:
        """组织问题编号信息"""
        ruanjian_version = ruanjian_xinxi.get('被测软件版本', [''])[0]
        ruanjian_biaoshi = ruanjian_xinxi.get('软件标识', [''])[0]
        
        # 如果软件标识为空，使用软件名称作为后备方案
        if not ruanjian_biaoshi:
            ruanjian_name = ruanjian_xinxi.get('软件名称', [''])[0]
            if ruanjian_name:
                # 取软件名称的前8个字符作为标识
                ruanjian_biaoshi = ruanjian_name[:8] if len(ruanjian_name) > 8 else ruanjian_name
                self.logger.warning(f"软件标识为空，使用软件名称作为标识: {ruanjian_biaoshi}")
            else:
                ruanjian_biaoshi = 'UNKNOWN'
                self.logger.warning("软件标识和软件名称都为空，使用默认标识: UNKNOWN")
        
        # 生成问题报告单编号前缀（配置项测试使用CT-前缀）
        # 🔧 修改：格式：CT-软件标识-版本号-DFT-n (包含版本号)
        if ceshileixing == '配置项测试':
            wentidan_bianhao_prefix = f'CT-{ruanjian_biaoshi}-{ruanjian_version}-DFT-'
        else:
            wentidan_bianhao_prefix = f'CT-{ruanjian_biaoshi}-{ruanjian_version}-DFT-'
        
        # 生成所有问题编号
        issue_numbers = []
        for i in range(issue_count):
            issue_numbers.append(f"{wentidan_bianhao_prefix}{i+1}")
        
        return {
            'prefix': wentidan_bianhao_prefix,
            'issue_numbers': issue_numbers,
            'total_count': issue_count
        }
    
    def _organize_issue_classification(self, issue_count: int) -> List[Dict[str, str]]:
        """组织问题分类信息（配置项测试的分类逻辑）"""
        classifications = []
        
        for i in range(1, issue_count + 1):
            if i <= 4:
                # 前4个问题：文档审查
                classification = {
                    'test_activity': '文档审查',
                    'issue_type': '软件需求问题',  # 🔧 修改：由"用户需求问题"改为"软件需求问题"
                    'description_type': 'document'
                }
            elif i <= 8:
                # 第5-8个问题：静态分析（原代码审查）
                classification = {
                    'test_activity': '静态分析',  # 🔧 修改：由"代码审查"改为"静态分析"
                    'issue_type': '程序问题',
                    'description_type': 'code'
                }
            elif i <= 12:
                # 第9-12个问题：代码审查
                classification = {
                    'test_activity': '代码审查',
                    'issue_type': '程序问题',
                    'description_type': 'code'
                }
            else:
                # 第13-16个问题：动态测试
                classification = {
                    'test_activity': '动态测试',
                    'issue_type': '程序问题',
                    'description_type': 'code'
                }
            
            classifications.append(classification)
        
        return classifications
    
    def _organize_time_info(self) -> Dict[str, str]:
        """组织时间信息"""
        try:
            # 移除不存在的forms模块导入，提供默认时间信息
            import datetime
            current_date = datetime.date.today()
            
            return {
                'design_time': current_date.strftime('%Y/%m/%d'),
                'test_time': current_date.strftime('%Y/%m/%d'),
                'completion_year_month': current_date.strftime('%Y年%m月')
            }
        except Exception as e:
            self.logger.warning(f"时间计算失败，使用默认值: {e}")
            return {
                'design_time': '',
                'test_time': '',
                'completion_year_month': ''
            }
    
    def _get_description_templates(self) -> Dict[str, str]:
        """获取问题描述模板"""
        return {
            'document': '需求描述: 。\n问题描述: 。\n问题定位: 。\n影响分析:文档描述错误，不利于代码维护以及测试人员进行测试需求的提取；',
            'code': '需求描述: 。\n问题描述: 。\n问题定位: 。\n影响分析: 。'
        }
    
    def _get_fixed_values(self) -> Dict[str, str]:
        """获取固定值配置"""
        return {
            'test_round': '第一轮',
            'is_historical_issue': '否',
            'related_version': '',
            'related_issue_number': ' ',
            'issue_level': '一般问题',
            'issue_count': '1',
            'issue_name': '',
            'issue_source': ' ',
            'evaluation_opinion': '请开发人员',
            'fix_priority': '立即修复',
            'development_opinion': '确认是问题，已经在',
            'fix_time': '立即修复',
            'designer_opinion': '',
            'processing_result': '已归零',
            'confirmation_opinion': '开发人员已经在，问题已归零',
            'is_typical_issue': '否',
            'is_low_level_error': '否'
        }
    
    def validate_issue_report_data(self, issue_report_data: Dict[str, Any]) -> bool:
        """
        验证配置项测试问题报告单数据的完整性
        
        Args:
            issue_report_data: 问题报告数据字典
            
        Returns:
            bool: 验证结果
        """
        try:
            required_keys = ['basic_info', 'issue_numbering', 'issue_classification', 'time_info', 'fixed_values']
            
            for key in required_keys:
                if key not in issue_report_data:
                    self.logger.warning(f"缺少必需的数据字段: {key}")
                    return False
            
            # 验证基本信息
            basic_info = issue_report_data['basic_info']
            if not basic_info.get('software_name'):
                self.logger.warning("缺少软件名称")
                return False
            
            # 验证问题数量
            issue_count = issue_report_data.get('issue_count', 0)
            if issue_count <= 0:
                self.logger.warning("问题数量无效")
                return False
            
            # 验证问题分类数量
            classifications = issue_report_data.get('issue_classification', [])
            if len(classifications) != issue_count:
                self.logger.warning(f"问题分类数量({len(classifications)})与问题总数({issue_count})不匹配")
                return False
            
            self.logger.debug("配置项测试问题报告单数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证配置项测试问题报告单数据时发生错误: {str(e)}")
            return False
    
    def get_issue_statistics(self, issue_report_data: Dict[str, Any]) -> Dict[str, int]:
        """
        获取问题统计信息
        
        Args:
            issue_report_data: 问题报告数据字典
            
        Returns:
            Dict[str, int]: 统计信息
        """
        try:
            classifications = issue_report_data.get('issue_classification', [])
            
            statistics = {
                'total_issues': len(classifications),
                'document_review_issues': 0,
                'code_review_issues': 0,
                'static_analysis_issues': 0,  # 🔧 新增：静态分析问题统计
                'dynamic_test_issues': 0,
                'user_requirement_issues': 0,
                'software_requirement_issues': 0,  # 🔧 新增：软件需求问题统计
                'program_issues': 0
            }
            
            for classification in classifications:
                test_activity = classification.get('test_activity', '')
                issue_type = classification.get('issue_type', '')
                
                if test_activity == '文档审查':
                    statistics['document_review_issues'] += 1
                elif test_activity == '代码审查':
                    statistics['code_review_issues'] += 1
                elif test_activity == '静态分析':  # 🔧 新增：静态分析统计
                    statistics['static_analysis_issues'] += 1
                elif test_activity == '动态测试':
                    statistics['dynamic_test_issues'] += 1
                
                if issue_type == '用户需求问题':
                    statistics['user_requirement_issues'] += 1
                elif issue_type == '软件需求问题':  # 🔧 新增：软件需求问题统计
                    statistics['software_requirement_issues'] += 1
                elif issue_type == '程序问题':
                    statistics['program_issues'] += 1
            
            self.logger.info(f"问题统计信息: {statistics}")
            return statistics
            
        except Exception as e:
            self.logger.error(f"获取问题统计信息时发生错误: {str(e)}")
            return {}
    
    def adapt_for_configuration_item_test(self, issue_report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        为配置项测试调整问题报告数据
        
        Args:
            issue_report_data: 原始问题报告数据
            
        Returns:
            Dict[str, Any]: 调整后的问题报告数据
        """
        # 配置项测试特有的调整
        adapted_data = issue_report_data.copy()
        
        # 调整问题编号前缀为配置项测试专用
        basic_info = adapted_data.get('basic_info', {})
        if basic_info.get('test_type') == '配置项测试':
            # 确保使用配置项测试的编号格式
            issue_numbering = adapted_data.get('issue_numbering', {})
            prefix = issue_numbering.get('prefix', '')
            if not prefix.startswith('CT-'):
                # 重新生成配置项测试编号
                software_id = basic_info.get('software_id', '')
                software_version = basic_info.get('software_version', '')
                new_prefix = f'CT-{software_id}_{software_version}-DFT-'
                issue_numbering['prefix'] = new_prefix
                
                # 重新生成所有问题编号
                issue_count = adapted_data.get('issue_count', 16)
                new_issue_numbers = []
                for i in range(issue_count):
                    new_issue_numbers.append(f"{new_prefix}{i+1}")
                issue_numbering['issue_numbers'] = new_issue_numbers
        
        self.logger.info("问题报告数据已调整为配置项测试模式")
        return adapted_data
