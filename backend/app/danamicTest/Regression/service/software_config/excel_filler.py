"""
回归测试软件配置项信息Excel填充器

负责将回归测试软件配置项信息数据填充到Excel工作表中。
"""

import logging
import openpyxl
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionSoftwareConfigExcelFiller:
    """回归测试软件配置项信息Excel填充器"""
    
    def __init__(self):
        """初始化Excel填充器"""
        self.logger = logger
        self.cell_mapping = self._get_cell_mapping()
    
    def fill_software_config_sheet(
        self,
        excel_file_path: str,
        sheet_name: str,
        software_config_data: Dict[str, Any]
    ) -> bool:
        """
        填充回归测试软件配置项信息工作表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            software_config_data: 软件配置数据字典
            
        Returns:
            bool: 填充是否成功
        """
        try:
            self.logger.info(f"开始填充回归测试软件配置项信息表: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 填充数据
            self._fill_basic_software_info(sheet, software_config_data)
            self._fill_software_details(sheet, software_config_data)
            self._fill_environment_info(sheet, software_config_data)
            self._fill_statistics_info(sheet, software_config_data)
            self._fill_time_info(sheet, software_config_data)
            self._fill_fixed_values(sheet, software_config_data)
            self._fill_regression_specific_fields(sheet, software_config_data)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("回归测试软件配置项信息表填充完成")
            return True
            
        except Exception as e:
            self.logger.error(f"填充回归测试软件配置项信息表时发生错误: {str(e)}")
            return False
    
    def _fill_basic_software_info(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充基本软件信息"""
        basic_info = software_config_data.get('basic_info', {})
        software_details = software_config_data.get('software_details', {})
        code_statistics = software_config_data.get('code_statistics', {})
        
        # 1. 软件名称
        software_name = basic_info.get('software_name', '')
        sheet.cell(row=2, column=3, value=software_name)
        
        # 11. 软件规模（使用最终计算的代码行数）
        final_code_lines = code_statistics.get('final_code_lines', 0)
        sheet.cell(row=12, column=3, value=final_code_lines)
        
        self.logger.info(f"基本软件信息填充完成: 名称={software_name}, 规模={final_code_lines}")
    
    def _fill_software_details(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充软件详细信息"""
        software_details = software_config_data.get('software_details', {})
        data_sources = software_config_data.get('data_sources', {})
        basic_info = software_config_data.get('basic_info', {})
        
        # 检查是否有型号信息库数据
        if 'model_database' in data_sources:
            self._fill_from_model_database(sheet, software_details)
        else:
            # 使用AI生成或文档提取的信息
            self._fill_from_ai_or_document(sheet, software_details, basic_info)
        
        # 填充其他详细信息
        self._fill_other_software_details(sheet, software_details)
    
    def _fill_from_model_database(self, sheet, software_details: Dict[str, Any]) -> None:
        """从型号信息库填充"""
        sheet.cell(row=3, column=3, value=software_details.get('software_short_name', ''))     # 2. 软件简称
        sheet.cell(row=4, column=3, value=software_details.get('software_short_name_en', ''))  # 3. 软件简称（英文）
        sheet.cell(row=5, column=3, value=software_details.get('software_id', ''))             # 4. 软件标识
        sheet.cell(row=6, column=3, value=software_details.get('system_name', ''))             # 5. 系统名称
        sheet.cell(row=7, column=3, value=software_details.get('system_short_name', ''))       # 6. 系统简称
        sheet.cell(row=8, column=3, value=software_details.get('component', ''))               # 7. 组件
        sheet.cell(row=11, column=3, value=software_details.get('software_code', ''))          # 10. 软件代号
        sheet.cell(row=13, column=3, value=software_details.get('programming_language', 'C'))  # 12. 编程语言
        sheet.cell(row=16, column=3, value=software_details.get('software_level', '重要'))      # 15. 软件等级
        
        self.logger.info("从型号信息库填充软件详细信息完成")
    
    def _fill_from_ai_or_document(self, sheet, software_details: Dict[str, Any], basic_info: Dict[str, Any]) -> None:
        """从AI生成或文档提取填充"""
        try:
            # 尝试使用AI生成软件信息
            software_name = basic_info.get('software_name', '')
            
            if software_name:
                ai_info = self._generate_ai_software_info(software_name)
                if ai_info:
                    sheet.cell(row=3, column=3, value=ai_info.get('software_short_name', ''))
                    sheet.cell(row=4, column=3, value=ai_info.get('software_short_name_en', ''))
                    sheet.cell(row=6, column=3, value=ai_info.get('system_name', ''))
                    sheet.cell(row=7, column=3, value=ai_info.get('system_short_name', ''))
                    sheet.cell(row=8, column=3, value=ai_info.get('component', ''))
                    
                    self.logger.info(f"AI生成软件信息填充完成: {ai_info}")
                else:
                    self._fill_default_software_info(sheet, software_details)
            else:
                self._fill_default_software_info(sheet, software_details)
                
        except Exception as e:
            self.logger.error(f"AI生成软件信息失败: {e}")
            self._fill_default_software_info(sheet, software_details)
    
    def _generate_ai_software_info(self, software_name: str) -> Optional[Dict[str, str]]:
        """生成AI软件信息"""
        try:
            from . import generate_software_info_by_ai, format_software_info_for_excel
            
            self.logger.info(f"开始为软件 '{software_name}' 生成AI软件信息")
            
            # 调用AI生成软件信息
            ai_software_info = generate_software_info_by_ai(software_name)
            software_short_name, software_short_name_en, system_name, system_short_name, component = format_software_info_for_excel(ai_software_info)
            
            return {
                'software_short_name': software_short_name,
                'software_short_name_en': software_short_name_en,
                'system_name': system_name,
                'system_short_name': system_short_name,
                'component': component
            }
            
        except Exception as e:
            self.logger.error(f"AI生成软件信息失败: {e}")
            return None
    
    def _fill_default_software_info(self, sheet, software_details: Dict[str, Any]) -> None:
        """填充默认软件信息"""
        sheet.cell(row=3, column=3, value=software_details.get('software_short_name', ''))
        sheet.cell(row=4, column=3, value='')  # 英文简称
        sheet.cell(row=6, column=3, value=software_details.get('system_name', ''))
        sheet.cell(row=7, column=3, value=software_details.get('system_short_name', ''))
        sheet.cell(row=8, column=3, value='')  # 组件
        
        self.logger.info("填充默认软件信息完成")
    
    def _fill_other_software_details(self, sheet, software_details: Dict[str, Any]) -> None:
        """填充其他软件详细信息"""
        # 4. 软件标识
        software_id = software_details.get('software_id', '')
        sheet.cell(row=5, column=3, value=software_id)
        
        # 8. 被测软件基础版本（回归测试特有）
        base_version = software_details.get('base_version', '')
        sheet.cell(row=9, column=3, value=base_version)
        
        # 9. 被测软件版本
        software_version = software_details.get('software_version', '')
        sheet.cell(row=10, column=3, value=software_version)
        
        # 10. 软件代号
        software_code = software_details.get('software_code', software_id)
        sheet.cell(row=11, column=3, value=software_code)
        
        # 12. 编程语言
        programming_language = software_details.get('programming_language', 'C')
        sheet.cell(row=13, column=3, value=programming_language)
        
        # 15. 软件等级
        software_level = software_details.get('software_level', '重要')
        sheet.cell(row=16, column=3, value=software_level)
    
    def _fill_environment_info(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充环境信息（智能提取）"""
        try:
            # 导入环境信息提取器
            from .ai_generator.environment_extractor import EnvironmentExtractor
            
            # 获取默认值
            environment_info = software_config_data.get('environment_info', {})
            dev_env = environment_info.get('development_environment', 'AcoreIde')
            runtime_env = environment_info.get('runtime_environment', '飞腾2000（天脉3）')
            
            # 尝试从需求文档中智能提取环境信息
            try:
                # 这里需要获取需求文档路径和内容
                # 可以从software_config_data中获取requirement_doc_path
                requirement_doc_path = getattr(self, '_current_requirement_doc_path', None)
                
                if requirement_doc_path:
                    extractor = EnvironmentExtractor()
                    
                    # 读取需求文档内容
                    requirement_content = self._read_requirement_document(requirement_doc_path)
                    
                    if requirement_content:
                        # 获取AI分析函数（如果可用）
                        ai_function = getattr(self, '_ai_analysis_function', None)
                        
                        # 提取环境信息
                        extracted_info = extractor.extract_environment_info(
                            requirement_content, ai_function
                        )
                        
                        # 使用提取的信息（如果成功提取）
                        if extracted_info.get('development_environment'):
                            dev_env = extracted_info['development_environment']
                            self.logger.info(f"智能提取开发环境: {dev_env}")
                        
                        if extracted_info.get('runtime_environment'):
                            runtime_env = extracted_info['runtime_environment']
                            self.logger.info(f"智能提取运行环境: {runtime_env}")
                    else:
                        self.logger.warning("无法读取需求文档内容，使用默认环境信息")
                else:
                    self.logger.info("未提供需求文档路径，使用默认环境信息")
                    
            except Exception as extract_error:
                self.logger.warning(f"智能提取环境信息失败，使用默认值: {extract_error}")
            
            # 填充到Excel
            sheet.cell(row=14, column=3, value=dev_env)      # 13. 开发环境
            sheet.cell(row=15, column=3, value=runtime_env)  # 14. 运行环境
            
            self.logger.info(f"环境信息填充完成: 开发环境='{dev_env}', 运行环境='{runtime_env}'")
            
        except Exception as e:
            self.logger.error(f"环境信息填充失败: {e}")
            # 使用默认值作为兜底
            sheet.cell(row=14, column=3, value='AcoreIde')
            sheet.cell(row=15, column=3, value='飞腾2000（天脉3）')
    
    def _read_requirement_document(self, doc_path: str) -> Optional[str]:
        """读取需求文档内容"""
        try:
            from pathlib import Path
            import docx
            
            doc_path = Path(doc_path)
            if not doc_path.exists():
                self.logger.warning(f"需求文档不存在: {doc_path}")
                return None
            
            if doc_path.suffix.lower() == '.docx':
                # 读取Word文档
                doc = docx.Document(doc_path)
                content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                self.logger.info(f"成功读取需求文档，内容长度: {len(content)}")
                return content
            elif doc_path.suffix.lower() == '.txt':
                # 读取文本文档
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.logger.info(f"成功读取文本文档，内容长度: {len(content)}")
                return content
            else:
                self.logger.warning(f"不支持的文档格式: {doc_path.suffix}")
                return None
                
        except Exception as e:
            self.logger.error(f"读取需求文档时发生错误: {str(e)}")
            return None
    
    def set_requirement_doc_path(self, doc_path: str) -> None:
        """设置需求文档路径"""
        self._current_requirement_doc_path = doc_path
        self.logger.info(f"设置需求文档路径: {doc_path}")
    
    def set_ai_analysis_function(self, ai_function: callable) -> None:
        """设置AI分析函数"""
        self._ai_analysis_function = ai_function
        self.logger.info("设置AI分析函数")
    
    def _fill_statistics_info(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充统计信息"""
        basic_info = software_config_data.get('basic_info', {})
        statistics_info = software_config_data.get('statistics_info', {})
        
        # 16. 责任人（测试人员）
        if basic_info.get('is_same_person', False):
            sheet.cell(row=17, column=3, value=basic_info.get('manager_name', ''))
        else:
            tester_name = basic_info.get('tester_name', '')
            manager_name = basic_info.get('manager_name', '')
            sheet.cell(row=17, column=3, value=f"{manager_name}、{tester_name}")
        
        # 19-22. 规模相关信息
        sheet.cell(row=20, column=3, value=statistics_info.get('software_change_scale', 0))
        sheet.cell(row=21, column=3, value=statistics_info.get('test_scale', 0))
        sheet.cell(row=22, column=3, value=statistics_info.get('review_document_scale', 60))
        sheet.cell(row=23, column=3, value=statistics_info.get('test_document_scale', 0))
        
        # 27-31. 测试相关统计
        sheet.cell(row=28, column=3, value=statistics_info.get('actual_test_workload', 5))
        sheet.cell(row=29, column=3, value=statistics_info.get('remaining_issues_count', 0))
        sheet.cell(row=30, column=3, value=statistics_info.get('test_depth', '全面测试'))
        sheet.cell(row=31, column=3, value=statistics_info.get('planning_requirements_count', 0))
        
        # 38-41. 需求相关统计
        sheet.cell(row=39, column=3, value=statistics_info.get('effective_test_code_scale', 0))
        sheet.cell(row=40, column=3, value=statistics_info.get('planning_requirements_count', 0))
        sheet.cell(row=41, column=3, value=statistics_info.get('analysis_requirements_count', 0))
        
        # 42-44. 项目成员相关
        self._fill_team_member_info(sheet, basic_info, statistics_info)
        
        # 48. 标准需求数
        sheet.cell(row=48, column=3, value=statistics_info.get('standard_requirements_count', 0))
    
    def _fill_team_member_info(self, sheet, basic_info: Dict[str, Any], statistics_info: Dict[str, Any]) -> None:
        """填充团队成员信息"""
        if basic_info.get('is_same_person', False):
            sheet.cell(row=43, column=3, value='')  # 项目成员测试规模
            sheet.cell(row=44, column=3, value='')  # 项目成员投入工时
        else:
            test_scale = statistics_info.get('test_scale', 0)
            member_scale_1 = round(test_scale * 0.2)
            member_scale_2 = round(test_scale - member_scale_1)
            member_hours_1 = 1
            member_hours_2 = round(test_scale / 500) + 2
            
            sheet.cell(row=43, column=3, value=f"{member_scale_1}、{member_scale_2}")
            sheet.cell(row=44, column=3, value=f"{member_hours_1}、{member_hours_2}")
    
    def _fill_time_info(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充时间信息"""
        time_info = software_config_data.get('time_info', {})
        
        sheet.cell(row=24, column=3, value=time_info.get('planned_start_time', ''))    # 23. 计划开始时间
        sheet.cell(row=25, column=3, value=time_info.get('planned_end_time', ''))      # 24. 计划结束时间
        sheet.cell(row=26, column=3, value=time_info.get('actual_start_time', ''))     # 25. 启动时间（实际）
        sheet.cell(row=27, column=3, value=time_info.get('actual_end_time', ''))       # 26. 结束时间（实际）
    
    def _fill_fixed_values(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充固定值"""
        fixed_values = software_config_data.get('fixed_values', {})
        
        sheet.cell(row=18, column=3, value=fixed_values.get('is_closed', '是'))                    # 17. 是否闭项
        sheet.cell(row=19, column=3, value=fixed_values.get('is_urgent', '是'))                    # 18. 是否紧急
        sheet.cell(row=32, column=3, value=fixed_values.get('remarks', '无'))                      # 31. 备注
        sheet.cell(row=33, column=3, value=fixed_values.get('development_stage', 'S'))             # 32. 研制阶段
        sheet.cell(row=34, column=3, value=fixed_values.get('verification_status', '所内验证'))     # 33. 验证情况
        sheet.cell(row=35, column=3, value=fixed_values.get('config_management_status', '出库后更改')) # 34. 配置管理状态
        sheet.cell(row=36, column=3, value=fixed_values.get('purpose', '联试'))                    # 35. 用途
        sheet.cell(row=37, column=3, value=fixed_values.get('related_major_issues', '无'))         # 36. 关联重大事项
        sheet.cell(row=38, column=3, value=fixed_values.get('is_model_generated', '否'))           # 37. 是否模型生成项目
        sheet.cell(row=42, column=3, value='否')                                                   # 41. 是否合作项目
        sheet.cell(row=45, column=3, value=fixed_values.get('software_type', '应用软件'))           # 44. 软件类型
        sheet.cell(row=49, column=3, value=fixed_values.get('is_business_trip', '否'))             # 47. 是否出差项目
    
    def _fill_regression_specific_fields(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充回归测试特有字段"""
        fixed_values = software_config_data.get('fixed_values', {})
        statistics_info = software_config_data.get('statistics_info', {})
        
        # 46. 开发人员工作量（回归测试特有）
        developer_workload = fixed_values.get('developer_workload', '')
        if not developer_workload:
            # 根据测试规模计算开发人员工作量
            test_scale = statistics_info.get('test_scale', 0)
            developer_workload = max(round(test_scale / 1000), 1)
        
        sheet.cell(row=46, column=3, value=developer_workload)
        
        # 47. 标准需求数（回归测试可能有特殊计算）
        standard_requirements = statistics_info.get('standard_requirements_count', 2)
        if standard_requirements <= 0:
            standard_requirements = 2  # 默认值
        
        sheet.cell(row=47, column=3, value=standard_requirements)
        
        self.logger.info(f"回归测试特有字段填充完成: 开发人员工作量={developer_workload}, 标准需求数={standard_requirements}")
    
    def _get_cell_mapping(self) -> Dict[str, tuple]:
        """获取单元格映射关系"""
        return {
            'software_name': (2, 3),                    # 软件名称
            'software_short_name': (3, 3),              # 软件简称
            'software_short_name_en': (4, 3),           # 软件简称（英文）
            'software_id': (5, 3),                      # 软件标识
            'system_name': (6, 3),                      # 系统名称
            'system_short_name': (7, 3),                # 系统简称
            'component': (8, 3),                        # 组件
            'base_version': (9, 3),                     # 被测软件基础版本
            'software_version': (10, 3),                # 被测软件版本
            'software_code': (11, 3),                   # 软件代号
            'software_scale': (12, 3),                  # 软件规模
            'programming_language': (13, 3),            # 编程语言
            'development_environment': (14, 3),         # 开发环境
            'runtime_environment': (15, 3),             # 运行环境
            'software_level': (16, 3),                  # 软件等级
            'responsible_person': (17, 3),              # 责任人
            'is_closed': (18, 3),                       # 是否闭项
            'is_urgent': (19, 3),                       # 是否紧急
            'software_change_scale': (20, 3),           # 软件更改规模
            'test_code_scale': (21, 3),                 # 测试代码规模
            'review_document_scale': (22, 3),           # 审查文档规模
            'test_document_scale': (23, 3),             # 编写测试文档规模
            'planned_start_time': (24, 3),              # 计划开始时间
            'planned_end_time': (25, 3),                # 计划结束时间
            'actual_start_time': (26, 3),               # 启动时间（实际）
            'actual_end_time': (27, 3),                 # 结束时间（实际）
            'actual_test_workload': (28, 3),            # 实际测试工作量
            'remaining_issues_count': (29, 3),          # 遗留问题总数
            'test_depth': (30, 3),                      # 测试深度
            'test_item_count': (31, 3),                 # 测试项数量
            'remarks': (32, 3),                         # 备注
            'development_stage': (33, 3),               # 研制阶段
            'verification_status': (34, 3),             # 验证情况
            'config_management_status': (35, 3),        # 配置管理状态
            'purpose': (36, 3),                         # 用途
            'related_major_issues': (37, 3),            # 关联重大事项
            'is_model_generated': (38, 3),              # 是否模型生成项目
            'effective_test_code_scale': (39, 3),       # 有效测试代码规模
            'requirement_capture_count': (40, 3),       # 被测软件需求捕获总数
            'requirement_test_count': (41, 3),          # 被测软件需求测试总数
            'is_cooperation_project': (42, 3),          # 是否合作项目
            'member_test_scale': (43, 3),               # 项目成员测试规模
            'member_work_hours': (44, 3),               # 项目成员工时
            'software_type': (45, 3),                   # 软件类型
            'developer_workload': (46, 3),              # 开发人员工作量（回归测试特有）
            'standard_requirement_count': (47, 3),      # 标准需求数
            'is_business_trip': (48, 3)                 # 是否出差项目
        }
    
    def get_filled_data_summary(self, excel_file_path: str, sheet_name: str) -> Dict[str, str]:
        """获取已填充数据的摘要"""
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            summary = {}
            for field, (row, col) in self.cell_mapping.items():
                cell_value = sheet.cell(row=row, column=col).value
                summary[field] = str(cell_value) if cell_value else ""
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取填充数据摘要时发生错误: {str(e)}")
            return {}
