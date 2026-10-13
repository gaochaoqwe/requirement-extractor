"""
回归测试项目策划表数据处理器

负责处理和组织回归测试中项目策划表所需的数据。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionProjectPlanDataProcessor:
    """回归测试项目策划表数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.logger = logger
    
    def organize_project_plan_data(
        self,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: Dict[str, str],
        file_path: str,
        ceshiren_name: str,
        kaifarenxinxi: List[str],
        zhuguan_name: str,
        biaoshihao_ceshixianng: List[str],
        daima_chayi_hangshu: int,
        ceshileixing: str = "回归测试"
    ) -> Dict[str, Any]:
        """
        组织回归测试项目策划表数据
        
        Args:
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求字典
            file_path: 文档文件路径
            ceshiren_name: 测试人员名称
            kaifarenxinxi: 开发人员信息列表
            zhuguan_name: 主管名称
            biaoshihao_ceshixianng: 标识号测试项列表
            daima_chayi_hangshu: 代码差异行数
            ceshileixing: 测试类型
            
        Returns:
            Dict[str, Any]: 组织好的项目策划表数据
        """
        try:
            self.logger.info("开始组织回归测试项目策划表数据")
            
            # 基本信息
            basic_info = self._organize_basic_info(
                ruanjian_xinxi, ruanjian_name, ceshileixing, kaifarenxinxi, daima_chayi_hangshu
            )
            
            # 测试项信息
            test_items = self._organize_test_items(diama_biangeng_xuqiu, biaoshihao_ceshixianng)
            
            # 项目信息
            project_info = self._organize_project_info(
                ruanjian_name, ruanjian_xinxi, kaifarenxinxi, daima_chayi_hangshu, len(diama_biangeng_xuqiu)
            )
            
            # 人员信息
            personnel_info = self._organize_personnel_info(ceshiren_name, zhuguan_name, kaifarenxinxi)
            
            # 文档信息
            document_info = self._organize_document_info(file_path, ruanjian_name)
            
            # 格式设置配置
            formatting_config = self._get_formatting_config()
            
            project_plan_data = {
                'basic_info': basic_info,
                'test_items': test_items,
                'project_info': project_info,
                'personnel_info': personnel_info,
                'document_info': document_info,
                'formatting_config': formatting_config,
                'test_count': len(diama_biangeng_xuqiu),
                'table_type': '回归测试项目策划表'
            }
            
            self.logger.info(f"项目策划表数据组织完成，共{len(diama_biangeng_xuqiu)}个测试项")
            return project_plan_data
            
        except Exception as e:
            self.logger.error(f"组织回归测试项目策划表数据时发生错误: {str(e)}")
            return {}
    
    def _organize_basic_info(
        self,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        ceshileixing: str,
        kaifarenxinxi: List[str],
        daima_chayi_hangshu: int
    ) -> Dict[str, str]:
        """组织基本信息"""
        return {
            'software_name': ruanjian_name,
            'software_identifier': ruanjian_xinxi.get('软件标识', [''])[0],
            'software_version': ruanjian_xinxi.get('被测软件版本', [''])[0],
            'test_type': ceshileixing,
            'programming_language': ruanjian_xinxi.get('编程语言', ['C'])[0],
            'development_environment': ruanjian_xinxi.get('开发环境', ['SDK'])[0],
            'runtime_environment': ruanjian_xinxi.get('运行环境', ['Linux'])[0],
            'software_level': ruanjian_xinxi.get('软件等级', ['AAAA'])[0],
            'project_source': kaifarenxinxi[1] if len(kaifarenxinxi) > 1 else '',
            'code_change_lines': str(daima_chayi_hangshu)
        }
    
    def _organize_test_items(
        self,
        diama_biangeng_xuqiu: Dict[str, str],
        biaoshihao_ceshixianng: List[str]
    ) -> List[Dict[str, Any]]:
        """组织测试项信息"""
        test_items = []
        allkeys = list(diama_biangeng_xuqiu.keys())
        
        for i, test_item_name in enumerate(allkeys):
            test_item = {
                'index': i + 1,
                'name': test_item_name,
                'standard_name': test_item_name,  # 标准子需求名称
                'standard_unit': 0.2,  # 标准子需求单位
                'chapter_number': '',  # 将在文档读取时填充
                'importance': '重要',
                'full_test': '是',
                'test_identifier': biaoshihao_ceshixianng[i] if i < len(biaoshihao_ceshixianng) else f'SRC-NAME{i+1}'
            }
            test_items.append(test_item)
        
        return test_items
    
    def _organize_project_info(
        self,
        ruanjian_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        kaifarenxinxi: List[str],
        daima_chayi_hangshu: int,
        test_count: int
    ) -> Dict[str, Any]:
        """组织项目信息"""
        # 计算测试规模
        from ...forms.formFilter.project_info_form_filler import ceshiguimo_fenxi
        ceshiguimo_jisuan = ceshiguimo_fenxi(daima_chayi_hangshu)
        
        # 计算测试时间
        from ...forms.formFilter.time_calculator import ceshi_start_end_time
        ceshi_start_time, ceshi_end_time = ceshi_start_end_time(daima_chayi_hangshu)
        
        return {
            'project_name': ruanjian_name,
            'project_number': ruanjian_xinxi.get('软件标识', [''])[0],
            'project_source': kaifarenxinxi[1] if len(kaifarenxinxi) > 1 else '',
            'professional_direction': '光电',
            'settlement_code_lines': str(daima_chayi_hangshu),
            'actual_code_lines': str(ceshiguimo_jisuan),
            'original_requirements_count': test_count,
            'planned_start_date': ceshi_start_time,
            'planned_end_date': ceshi_end_time,
            'test_requirements_count': test_count,
            'is_urgent': '是'
        }
    
    def _organize_personnel_info(
        self,
        ceshiren_name: str,
        zhuguan_name: str,
        kaifarenxinxi: List[str]
    ) -> Dict[str, str]:
        """组织人员信息"""
        return {
            'tester_name': ceshiren_name,
            'supervisor_name': zhuguan_name,
            'developer_info': kaifarenxinxi,
            'requirements_analyst': zhuguan_name,
            'document_reviewer': ceshiren_name,
            'static_analyst': ceshiren_name,
            'code_reviewer': ceshiren_name,
            'dynamic_tester': ceshiren_name
        }
    
    def _organize_document_info(self, file_path: str, ruanjian_name: str) -> Dict[str, str]:
        """组织文档信息"""
        return {
            'document_path': file_path,
            'software_name': ruanjian_name,
            'document_review_scope': f"文档审查范围：\n1.《{ruanjian_name}软件变更与影响域分析报告》；\n2.《{ruanjian_name}需求规格说明》；",
            'static_analysis_scope': "静态分析范围:\n全部手写代码；",
            'code_review_scope': "代码审查范围:\n全部手写代码；",
            'environment_requirements': "环境其他要求:\n本次测试使用产品加检测仪环境；",
            'other_requirements': "其他要求:\n无；"
        }
    
    def _get_formatting_config(self) -> Dict[str, Any]:
        """获取格式设置配置"""
        return {
            'colors': {
                'light_yellow': "FFFF99",
                'red': "FF0000"
            },
            'column_ranges': {
                'test_items': [1, 14],  # 测试项数据范围
                'project_info': [2, 12]  # 项目信息范围
            },
            'border_style': 'thin',
            'alignment': {
                'wrap_text': True,
                'vertical': 'center'
            }
        }
    
    def validate_project_plan_data(self, project_plan_data: Dict[str, Any]) -> bool:
        """
        验证回归测试项目策划表数据的完整性
        
        Args:
            project_plan_data: 项目策划表数据字典
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查必需的顶级键
            required_keys = ['basic_info', 'test_items', 'project_info', 'personnel_info', 'test_count']
            for key in required_keys:
                if key not in project_plan_data:
                    self.logger.error(f"缺少必需的数据键: {key}")
                    return False
            
            # 检查基本信息
            basic_info = project_plan_data['basic_info']
            required_basic_keys = ['software_name', 'software_identifier', 'test_type']
            for key in required_basic_keys:
                if key not in basic_info or not basic_info[key]:
                    self.logger.error(f"基本信息缺少必需字段: {key}")
                    return False
            
            # 检查测试项数量一致性
            test_items = project_plan_data['test_items']
            test_count = project_plan_data['test_count']
            
            if len(test_items) != test_count:
                self.logger.error(f"测试项数量不一致: {len(test_items)} != {test_count}")
                return False
            
            # 检查测试项完整性
            for i, test_item in enumerate(test_items):
                required_item_keys = ['index', 'name', 'test_identifier']
                for key in required_item_keys:
                    if key not in test_item or not test_item[key]:
                        self.logger.error(f"测试项{i+1}缺少必需字段: {key}")
                        return False
            
            self.logger.info("回归测试项目策划表数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证回归测试项目策划表数据时发生错误: {str(e)}")
            return False
    
    def get_project_plan_statistics(self, project_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取回归测试项目策划表统计信息
        
        Args:
            project_plan_data: 项目策划表数据字典
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            test_items = project_plan_data.get('test_items', [])
            project_info = project_plan_data.get('project_info', {})
            
            # 基本统计
            statistics = {
                'total_test_items': project_plan_data.get('test_count', 0),
                'software_name': project_plan_data.get('basic_info', {}).get('software_name', ''),
                'test_type': project_plan_data.get('basic_info', {}).get('test_type', ''),
                'code_change_lines': project_info.get('settlement_code_lines', '0'),
                'actual_code_lines': project_info.get('actual_code_lines', '0'),
                'planned_start_date': project_info.get('planned_start_date', ''),
                'planned_end_date': project_info.get('planned_end_date', ''),
                'table_type': '回归测试项目策划表'
            }
            
            self.logger.info(f"项目策划表统计: 共{statistics['total_test_items']}个测试项")
            return statistics
            
        except Exception as e:
            self.logger.error(f"获取回归测试项目策划表统计信息时发生错误: {str(e)}")
            return {}
    
    def extract_test_requirements(self, project_plan_data: Dict[str, Any]) -> List[str]:
        """
        从项目策划表数据中提取测试需求列表
        
        Args:
            project_plan_data: 项目策划表数据字典
            
        Returns:
            List[str]: 测试需求列表
        """
        try:
            test_items = project_plan_data.get('test_items', [])
            requirements = [item.get('name', '') for item in test_items if item.get('name')]
            
            self.logger.info(f"提取到{len(requirements)}个测试需求")
            return requirements
            
        except Exception as e:
            self.logger.error(f"提取测试需求时发生错误: {str(e)}")
            return []
    
    def update_chapter_numbers(
        self,
        project_plan_data: Dict[str, Any],
        chapter_numbers: List[str]
    ) -> bool:
        """
        更新测试项的章节号
        
        Args:
            project_plan_data: 项目策划表数据字典
            chapter_numbers: 章节号列表
            
        Returns:
            bool: 更新是否成功
        """
        try:
            test_items = project_plan_data.get('test_items', [])
            
            for i, chapter_number in enumerate(chapter_numbers):
                if i < len(test_items):
                    test_items[i]['chapter_number'] = chapter_number
            
            self.logger.info(f"更新了{len(chapter_numbers)}个章节号")
            return True
            
        except Exception as e:
            self.logger.error(f"更新章节号时发生错误: {str(e)}")
            return False
