"""
配置项测试项目策划表服务

提供配置项测试项目策划表的完整服务接口，整合数据处理、Excel填充、格式设置和读取功能。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .data_processor import ConfigurationItemProjectPlanDataProcessor
from .excel_filler import ConfigurationItemProjectPlanExcelFiller
from .formatter import ConfigurationItemProjectPlanFormatter
from .reader import ConfigurationItemProjectPlanReader
from .identifier_generator import ConfigurationItemTestIdentifierGenerator

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemProjectPlanService:
    """配置项测试项目策划表服务"""
    
    def __init__(self):
        """初始化配置项测试项目策划表服务"""
        self.logger = logger
        self.data_processor = ConfigurationItemProjectPlanDataProcessor()
        self.excel_filler = ConfigurationItemProjectPlanExcelFiller()
        self.formatter = ConfigurationItemProjectPlanFormatter()
        self.reader = ConfigurationItemProjectPlanReader()
        self.identifier_generator = ConfigurationItemTestIdentifierGenerator()
    
    def generate_project_plan_table(
        self,
        excel_file_path: str,
        sheet_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: List[str],
        ceshileixing: str = "配置项测试",
        AI_fenx_flag_Anniu: int = 0,
        neirong_dict: Optional[List[str]] = None,
        apply_formatting: bool = True
    ) -> bool:
        """
        生成配置项测试项目策划表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求列表
            ceshileixing: 测试类型
            AI_fenx_flag_Anniu: AI分析标志
            neirong_dict: 内容描述列表（可选）
            apply_formatting: 是否应用格式设置
            
        Returns:
            bool: 生成是否成功
        """
        try:
            self.logger.info(f"开始生成配置项测试项目策划表: {sheet_name}")
            
            # 第一步：组织数据
            project_plan_data = self.data_processor.organize_project_plan_data(
                ruanjian_xinxi=ruanjian_xinxi,
                ruanjian_name=ruanjian_name,
                diama_biangeng_xuqiu=diama_biangeng_xuqiu,
                ceshileixing=ceshileixing,
                AI_fenx_flag_Anniu=AI_fenx_flag_Anniu
            )
            
            # 验证数据
            if not self.data_processor.validate_project_plan_data(project_plan_data):
                self.logger.error("配置项测试项目策划表数据验证失败")
                return False
            
            # 第二步：填充Excel
            if not self.excel_filler.fill_project_plan_sheet(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                project_plan_data=project_plan_data,
                neirong_dict=neirong_dict
            ):
                self.logger.error("Excel填充失败")
                return False
            
            # 第三步：应用格式（可选）
            if apply_formatting:
                test_count = project_plan_data.get('test_count', 0)
                if not self.formatter.apply_formatting(
                    excel_file_path=excel_file_path,
                    sheet_name=sheet_name,
                    test_count=test_count,
                    project_plan_data=project_plan_data
                ):
                    self.logger.warning("格式设置失败，但数据填充成功")
            
            # 记录统计信息
            statistics = self.data_processor.get_project_plan_statistics(project_plan_data)
            self.logger.info(f"项目策划表统计: {statistics}")
            
            self.logger.info("配置项测试项目策划表生成完成")
            return True
            
        except Exception as e:
            self.logger.error(f"生成配置项测试项目策划表时发生错误: {str(e)}")
            return False
    
    def generate_project_plan_table_legacy(
        self,
        excel_file_path: str,
        sheet_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: List[str],
        ceshileixing: str = "配置项测试",
        AI_fenx_flag_Anniu: int = 0,
        neirong_dict: Optional[List[str]] = None
    ) -> List[str]:
        """
        生成配置项测试项目策划表（兼容原有接口）

        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求列表
            ceshileixing: 测试类型
            AI_fenx_flag_Anniu: AI分析标志
            neirong_dict: 内容描述列表（可选）

        Returns:
            List[str]: 生成的英文标识号列表
        """
        try:
            self.logger.info(f"开始生成项目策划表（兼容模式）: {sheet_name}")

            # 使用兼容模式的填充方法
            if neirong_dict is None:
                neirong_dict = ['' for _ in range(len(diama_biangeng_xuqiu))]

            english_identifiers = self.excel_filler.fill_project_plan_sheet_legacy(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                ruanjian_xinxi=ruanjian_xinxi,
                ruanjian_name=ruanjian_name,
                diama_biangeng_xuqiu=diama_biangeng_xuqiu,
                ceshileixing=ceshileixing,
                neirong_dict=neirong_dict,
                AI_fenx_flag_Anniu=AI_fenx_flag_Anniu
            )

            self.logger.info(f"项目策划表生成完成（兼容模式），生成了{len(english_identifiers)}个标识")
            return english_identifiers

        except Exception as e:
            self.logger.error(f"生成项目策划表时发生错误（兼容模式）: {str(e)}")
            return [f'SRC-name{i}' for i in range(len(diama_biangeng_xuqiu))]
    
    def read_project_plan_data(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表'
    ) -> Tuple[List[List[str]], str]:
        """
        读取项目策划表数据
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Tuple[List[List[str]], str]: (策划表数据, 状态信息)
        """
        try:
            return self.reader.read_project_plan_data(excel_file_path, sheet_name)
        except Exception as e:
            self.logger.error(f"读取项目策划表数据时发生错误: {str(e)}")
            return [[], [], [], [], [], []], f"读取失败: {e}"
    
    def update_test_item_field(
        self,
        excel_file_path: str,
        sheet_name: str,
        item_index: int,
        field_name: str,
        field_value: str,
        apply_formatting: bool = True
    ) -> bool:
        """
        更新配置项测试项目策划表中的单个字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            item_index: 测试项索引（从1开始）
            field_name: 字段名称
            field_value: 字段值
            apply_formatting: 是否重新应用格式设置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self.logger.info(f"更新项目策划表字段: 测试项{item_index}, {field_name} = {field_value}")
            
            # 更新单个字段
            if not self.excel_filler.update_single_test_item(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                item_index=item_index,
                field_name=field_name,
                field_value=field_value
            ):
                return False
            
            # 重新应用格式（可选）
            if apply_formatting:
                # 需要知道测试项数量来应用格式
                summary = self.excel_filler.get_filled_data_summary(excel_file_path, sheet_name, 50)  # 假设最多50项
                test_count = summary.get('total_items', 0)
                self.formatter.apply_formatting(excel_file_path, sheet_name, test_count)
            
            self.logger.info(f"测试项{item_index}的字段{field_name}更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"更新项目策划表字段时发生错误: {str(e)}")
            return False
    
    def get_project_plan_status(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表'
    ) -> Dict[str, Any]:
        """
        获取配置项测试项目策划表的状态
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            return self.reader.get_project_plan_summary(excel_file_path, sheet_name)
        except Exception as e:
            self.logger.error(f"获取项目策划表状态时发生错误: {str(e)}")
            return {}
    
    def validate_project_plan_table(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表',
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        验证配置项测试项目策划表的完整性
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            required_fields: 必需字段列表
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 检查结构
            if not self.reader.validate_project_plan_structure(excel_file_path, sheet_name):
                return {
                    'is_valid': False,
                    'error': '项目策划表结构无效',
                    'table_type': '配置项测试项目策划表'
                }
            
            # 检查标识完整性
            identifier_check = self.reader.check_identifier_completeness(excel_file_path, sheet_name)
            
            validation_result = {
                'is_valid': identifier_check.get('is_complete', False),
                'missing_identifiers': identifier_check.get('missing_indices', []),
                'duplicate_identifiers': identifier_check.get('duplicate_identifiers', []),
                'total_requirements': identifier_check.get('total_requirements', 0),
                'completion_rate': 0,
                'validation_message': self._get_validation_message(identifier_check),
                'table_type': '配置项测试项目策划表'
            }
            
            # 计算完成率
            if validation_result['total_requirements'] > 0:
                missing_count = len(validation_result['missing_identifiers'])
                completed = validation_result['total_requirements'] - missing_count
                validation_result['completion_rate'] = round(completed / validation_result['total_requirements'] * 100, 2)
            
            self.logger.info(f"项目策划表验证结果: {validation_result}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证项目策划表时发生错误: {str(e)}")
            return {'is_valid': False, 'error': str(e)}
    
    def _get_validation_message(self, identifier_check: Dict[str, Any]) -> str:
        """
        生成验证消息
        
        Args:
            identifier_check: 标识检查结果
            
        Returns:
            str: 验证消息
        """
        if identifier_check.get('is_complete', False):
            return "配置项测试项目策划表验证通过，所有标识都已生成"
        
        messages = []
        
        missing_count = identifier_check.get('missing_count', 0)
        if missing_count > 0:
            messages.append(f"有 {missing_count} 个测试项缺失标识")
        
        duplicate_count = identifier_check.get('duplicate_count', 0)
        if duplicate_count > 0:
            messages.append(f"有 {duplicate_count} 个重复标识")
        
        return "; ".join(messages) if messages else "项目策划表状态未知"
    
    def generate_identifiers_for_existing_table(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表',
        use_ai_translation: bool = True
    ) -> bool:
        """
        为现有的项目策划表生成标识
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            use_ai_translation: 是否使用AI翻译
            
        Returns:
            bool: 生成是否成功
        """
        try:
            self.logger.info("为现有项目策划表生成标识")
            
            # 读取现有数据
            project_plan_data, status_msg = self.reader.read_project_plan_data(excel_file_path, sheet_name)
            ruanjian_xuqiu = project_plan_data[0]
            
            if not ruanjian_xuqiu:
                self.logger.error("未找到测试需求数据")
                return False
            
            # 生成新标识
            identifiers = self.identifier_generator.generate_english_identifiers(
                ruanjian_xuqiu, use_ai_translation
            )
            
            # 更新Excel中的标识
            import openpyxl
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            start_row = 17  # 标识从第17行开始（基于原有逻辑）
            for i, identifier in enumerate(identifiers):
                sheet.cell(row=start_row + i, column=14).value = identifier  # 第14列是标识列
            
            wb.save(excel_file_path)
            
            self.logger.info(f"成功为{len(identifiers)}个测试项生成标识")
            return True
            
        except Exception as e:
            self.logger.error(f"为现有项目策划表生成标识时发生错误: {str(e)}")
            return False
    
    def highlight_configuration_item_specific_content(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int
    ) -> bool:
        """
        高亮显示配置项测试特有的内容
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            return self.formatter.highlight_configuration_item_specific_fields(excel_file_path, sheet_name, test_count)
        except Exception as e:
            self.logger.error(f"高亮配置项测试特有内容时发生错误: {str(e)}")
            return False
    
    def highlight_auto_generated_content(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int
    ) -> bool:
        """
        高亮显示自动生成的内容
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            bool: 高亮设置是否成功
        """
        try:
            return self.formatter.highlight_auto_generated_fields(excel_file_path, sheet_name, test_count)
        except Exception as e:
            self.logger.error(f"高亮自动生成内容时发生错误: {str(e)}")
            return False
    
    def extract_test_requirements(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表'
    ) -> List[str]:
        """
        提取测试需求列表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            List[str]: 测试需求列表
        """
        try:
            return self.reader.extract_test_requirements_only(excel_file_path, sheet_name)
        except Exception as e:
            self.logger.error(f"提取测试需求时发生错误: {str(e)}")
            return []
    
    def backup_project_plan_table(
        self,
        excel_file_path: str,
        sheet_name: str,
        backup_file_path: str
    ) -> bool:
        """
        备份项目策划表
        
        Args:
            excel_file_path: 源Excel文件路径
            sheet_name: 工作表名称
            backup_file_path: 备份文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            return self.excel_filler.backup_sheet_data(excel_file_path, sheet_name, backup_file_path)
        except Exception as e:
            self.logger.error(f"备份项目策划表时发生错误: {str(e)}")
            return False
