"""
配置项测试项目策划表Excel填充器

负责将配置项测试项目策划表数据填充到Excel文件中。
"""

import logging
import os
import shutil
import openpyxl
from openpyxl.styles import PatternFill, Alignment
from openpyxl.styles.borders import Border, Side
import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemProjectPlanExcelFiller:
    """配置项测试项目策划表Excel填充器"""
    
    def __init__(self):
        """初始化Excel填充器"""
        self.logger = logger
        self.column_mapping = self._get_column_mapping()
    
    def fill_project_plan_sheet_legacy(
        self,
        excel_file_path: str,
        sheet_name: str,
        ruanjian_xinxi: Dict[str, List[str]],
        ruanjian_name: str,
        diama_biangeng_xuqiu: List[str],
        ceshileixing: str,
        neirong_dict: List[str],
        AI_fenx_flag_Anniu: int
    ) -> List[str]:
        """
        填充项目策划表内容（兼容原有接口）

        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            ruanjian_xinxi: 软件信息字典
            ruanjian_name: 软件名称
            diama_biangeng_xuqiu: 代码变更需求列表
            ceshileixing: 测试类型
            neirong_dict: 内容描述列表
            AI_fenx_flag_Anniu: AI分析标志

        Returns:
            List[str]: 生成的英文标识号列表
        """
        try:
            self.logger.info(f"开始填充项目策划表（兼容模式）: {sheet_name}")

            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)

            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return [f'SRC-name{i}' for i in range(len(diama_biangeng_xuqiu))]

            sheet = wb[sheet_name]

            # 基本信息
            len_dict = len(diama_biangeng_xuqiu)
            allkeys = diama_biangeng_xuqiu
            ruanjian_biaoshi = ruanjian_xinxi.get('软件标识', [''])[0]
            ruanjian_version = ruanjian_xinxi.get('被测软件版本', [''])[0]

            # 对异常数据进行判断
            if len(neirong_dict) != len_dict:
                self.logger.warning('测试项数量与文档数量不一致！')
                neirong_dict = ['' for _ in range(len_dict)]

            # 生成英文标识和测试类型标识
            english_identifiers, type_identifiers = self._generate_identifiers_legacy(
                allkeys, AI_fenx_flag_Anniu
            )

            # 填充测试项数据
            self._fill_test_items_legacy(
                sheet, allkeys, english_identifiers, type_identifiers,
                ruanjian_name, ruanjian_version, neirong_dict
            )

            # 保存文件
            wb.save(excel_file_path)

            self.logger.info("项目策划表填充完成（兼容模式）")
            return english_identifiers

        except Exception as e:
            self.logger.error(f"填充项目策划表时发生错误: {str(e)}")
            return [f'SRC-name{i}' for i in range(len(diama_biangeng_xuqiu))]

    def fill_project_plan_sheet(
        self,
        excel_file_path: str,
        sheet_name: str,
        project_plan_data: Dict[str, Any],
        neirong_dict: Optional[List[str]] = None
    ) -> bool:
        """
        填充项目策划表工作表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            project_plan_data: 项目策划表数据
            neirong_dict: 内容描述列表（可选）
            
        Returns:
            bool: 填充是否成功
        """
        try:
            self.logger.info(f"开始填充项目策划表: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 获取数据
            basic_info = project_plan_data.get('basic_info', {})
            test_items = project_plan_data.get('test_items', [])
            test_types = project_plan_data.get('test_types', [])
            
            # 生成英文标识和测试类型标识
            english_identifiers, type_identifiers = self._generate_identifiers(
                test_items, project_plan_data.get('identifier_config', {})
            )
            
            # 填充测试项数据
            self._fill_test_items(
                sheet, test_items, english_identifiers, type_identifiers,
                basic_info, neirong_dict
            )
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("项目策划表填充完成")
            return True
            
        except Exception as e:
            self.logger.error(f"填充项目策划表时发生错误: {str(e)}")
            return False
    
    def _generate_identifiers(
        self,
        test_items: List[Dict[str, Any]],
        identifier_config: Dict[str, Any]
    ) -> tuple:
        """生成英文标识和测试类型标识"""
        try:
            from .identifier_generator import ConfigurationItemTestIdentifierGenerator
            
            generator = ConfigurationItemTestIdentifierGenerator()
            
            # 提取测试项名称
            test_item_names = [item.get('name', '') for item in test_items]
            
            # 生成英文标识
            use_ai = identifier_config.get('use_ai_translation', False)
            english_identifiers = generator.generate_english_identifiers(
                test_item_names, use_ai
            )
            
            # 生成测试类型标识
            type_identifiers = generator.generate_test_type_identifiers(test_item_names)
            
            return english_identifiers, type_identifiers
            
        except Exception as e:
            self.logger.error(f"生成标识时发生错误: {str(e)}")
            # 返回默认标识
            count = len(test_items)
            english_identifiers = [f'SRC-name{i}' for i in range(count)]
            type_identifiers = ['FN'] * count
            return english_identifiers, type_identifiers
    
    def _fill_test_items(
        self,
        sheet,
        test_items: List[Dict[str, Any]],
        english_identifiers: List[str],
        type_identifiers: List[str],
        basic_info: Dict[str, str],
        neirong_dict: Optional[List[str]]
    ):
        """填充测试项数据"""
        start_row = 2  # 数据从第2行开始
        
        for i, test_item in enumerate(test_items):
            current_row = start_row + i
            
            # 基本信息
            sheet.cell(row=current_row, column=self.column_mapping['index']).value = test_item.get('index', i + 1)
            sheet.cell(row=current_row, column=self.column_mapping['software_name']).value = basic_info.get('software_name', '')
            sheet.cell(row=current_row, column=self.column_mapping['software_version']).value = basic_info.get('software_version', '')
            sheet.cell(row=current_row, column=self.column_mapping['test_item_name']).value = test_item.get('name', '')
            
            # 标识信息
            sheet.cell(row=current_row, column=self.column_mapping['english_identifier']).value = english_identifiers[i] if i < len(english_identifiers) else f'SRC-name{i}'
            sheet.cell(row=current_row, column=self.column_mapping['test_type']).value = type_identifiers[i] if i < len(type_identifiers) else 'FN'
            
            # 描述信息
            description = ''
            if neirong_dict and i < len(neirong_dict):
                description = neirong_dict[i]
            elif test_item.get('description'):
                description = test_item.get('description')
            
            sheet.cell(row=current_row, column=self.column_mapping['description']).value = description
            sheet.cell(row=current_row, column=self.column_mapping['is_executed']).value = test_item.get('is_executed', '是')
            sheet.cell(row=current_row, column=self.column_mapping['remarks']).value = test_item.get('remarks', '无')
        
        self.logger.debug(f"填充了{len(test_items)}个测试项")
    
    def _get_column_mapping(self) -> Dict[str, int]:
        """获取列映射"""
        return {
            'index': 2,                    # 编号
            'software_name': 3,            # 软件配置项名称
            'software_version': 4,         # 被测软件版本
            'test_item_name': 5,           # 测试项名称
            'english_identifier': 6,       # 测试项英文标识
            'test_type': 7,                # 测试类型
            'description': 8,              # 测试项描述
            'is_executed': 9,              # 是否执行
            'remarks': 10                  # 备注
        }
    
    def update_single_test_item(
        self,
        excel_file_path: str,
        sheet_name: str,
        item_index: int,
        field_name: str,
        field_value: str
    ) -> bool:
        """
        更新单个测试项的字段
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            item_index: 测试项索引（从1开始）
            field_name: 字段名称
            field_value: 字段值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self.logger.info(f"更新测试项{item_index}的字段{field_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 计算行号
            row = item_index + 1  # 数据从第2行开始，所以索引+1
            
            # 获取列号
            if field_name not in self.column_mapping:
                self.logger.error(f"未知的字段名称: {field_name}")
                return False
            
            col = self.column_mapping[field_name]
            
            # 更新单元格
            sheet.cell(row=row, column=col).value = field_value
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info(f"测试项{item_index}的字段{field_name}更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"更新单个测试项字段时发生错误: {str(e)}")
            return False
    
    def get_filled_data_summary(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int
    ) -> Dict[str, Any]:
        """
        获取已填充数据的摘要
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            Dict[str, Any]: 数据摘要
        """
        try:
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            filled_items = 0
            test_details = []
            
            start_row = 2
            for i in range(test_count):
                current_row = start_row + i
                
                # 检查关键字段是否已填充
                test_item_name = sheet.cell(row=current_row, column=self.column_mapping['test_item_name']).value
                english_identifier = sheet.cell(row=current_row, column=self.column_mapping['english_identifier']).value
                
                if test_item_name and english_identifier:
                    filled_items += 1
                
                # 收集详细信息
                detail = {
                    'index': i + 1,
                    'test_item_name': test_item_name or '',
                    'english_identifier': english_identifier or '',
                    'test_type': sheet.cell(row=current_row, column=self.column_mapping['test_type']).value or '',
                    'description': sheet.cell(row=current_row, column=self.column_mapping['description']).value or '',
                    'is_executed': sheet.cell(row=current_row, column=self.column_mapping['is_executed']).value or '',
                    'remarks': sheet.cell(row=current_row, column=self.column_mapping['remarks']).value or ''
                }
                test_details.append(detail)
            
            summary = {
                'total_items': test_count,
                'filled_items': filled_items,
                'completion_rate': round(filled_items / test_count * 100, 2) if test_count > 0 else 0,
                'test_details': test_details
            }
            
            self.logger.info(f"数据摘要: 共{test_count}项，已填充{filled_items}项")
            return summary
            
        except Exception as e:
            self.logger.error(f"获取数据摘要时发生错误: {str(e)}")
            return {}
    
    def clear_sheet_data(
        self,
        excel_file_path: str,
        sheet_name: str,
        test_count: int
    ) -> bool:
        """
        清空工作表数据
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            test_count: 测试项数量
            
        Returns:
            bool: 清空是否成功
        """
        try:
            self.logger.info(f"清空项目策划表数据: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            # 清空数据行
            start_row = 2
            max_col = max(self.column_mapping.values())
            
            for i in range(test_count):
                current_row = start_row + i
                for col in range(1, max_col + 1):
                    sheet.cell(row=current_row, column=col).value = None
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("项目策划表数据清空完成")
            return True
            
        except Exception as e:
            self.logger.error(f"清空项目策划表数据时发生错误: {str(e)}")
            return False
    
    def validate_excel_structure(
        self,
        excel_file_path: str,
        sheet_name: str
    ) -> bool:
        """
        验证Excel文件结构
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            bool: 结构是否有效
        """
        try:
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 检查工作表是否存在
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 检查列数
            max_col = max(self.column_mapping.values())
            if sheet.max_column < max_col:
                self.logger.error(f"工作表列数不足，需要至少{max_col}列")
                return False
            
            self.logger.info("Excel文件结构验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证Excel文件结构时发生错误: {str(e)}")
            return False
    
    def backup_sheet_data(
        self,
        excel_file_path: str,
        sheet_name: str,
        backup_file_path: str
    ) -> bool:
        """
        备份工作表数据
        
        Args:
            excel_file_path: 源Excel文件路径
            sheet_name: 工作表名称
            backup_file_path: 备份文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            import shutil
            
            self.logger.info(f"备份项目策划表数据: {sheet_name}")
            
            # 复制整个文件
            shutil.copy2(excel_file_path, backup_file_path)
            
            self.logger.info(f"项目策划表数据备份完成: {backup_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"备份项目策划表数据时发生错误: {str(e)}")
            return False

    def _generate_identifiers_legacy(
        self,
        test_item_names: List[str],
        AI_fenx_flag_Anniu: int
    ) -> tuple:
        """生成英文标识和测试类型标识（兼容模式）"""
        try:
            from .identifier_generator import ConfigurationItemTestIdentifierGenerator
            from .test_type_classifier import ceshi_leixing_biaoshi_choose

            generator = ConfigurationItemTestIdentifierGenerator()

            # 生成英文标识
            use_ai = AI_fenx_flag_Anniu == 1
            english_identifiers = generator.generate_english_identifiers(
                test_item_names, use_ai
            )

            # 生成测试类型标识（使用原有逻辑）
            type_identifiers = []
            for test_item_name in test_item_names:
                try:
                    leixing_biaoshi, ceshileixing_remp = ceshi_leixing_biaoshi_choose(test_item_name)
                    type_identifiers.append(ceshileixing_remp)
                except Exception:
                    type_identifiers.append('FN')  # 默认为功能测试

            return english_identifiers, type_identifiers

        except Exception as e:
            self.logger.error(f"生成标识时发生错误（兼容模式）: {str(e)}")
            # 返回默认标识
            count = len(test_item_names)
            english_identifiers = [f'SRC-name{i}' for i in range(count)]
            type_identifiers = ['FN'] * count
            return english_identifiers, type_identifiers

    def _fill_test_items_legacy(
        self,
        sheet,
        test_item_names: List[str],
        english_identifiers: List[str],
        type_identifiers: List[str],
        ruanjian_name: str,
        ruanjian_version: str,
        neirong_dict: List[str]
    ):
        """填充测试项数据（兼容模式）"""
        row_xuhao = 2  # 从第2行开始

        for index, test_item_name in enumerate(test_item_names):
            # 基本信息填充
            sheet.cell(row=row_xuhao, column=2).value = index + 1  # 编号
            sheet.cell(row=row_xuhao, column=3).value = ruanjian_name  # 软件配置项名称
            sheet.cell(row=row_xuhao, column=4).value = ruanjian_version  # 被测软件版本
            sheet.cell(row=row_xuhao, column=5).value = test_item_name  # 测试项名称
            sheet.cell(row=row_xuhao, column=6).value = english_identifiers[index] if index < len(english_identifiers) else f'SRC-name{index}'  # 测试项英文标识
            sheet.cell(row=row_xuhao, column=7).value = type_identifiers[index] if index < len(type_identifiers) else 'FN'  # 测试类型
            sheet.cell(row=row_xuhao, column=8).value = neirong_dict[index] if index < len(neirong_dict) else ''  # 测试项描述
            sheet.cell(row=row_xuhao, column=9).value = '是'  # 是否执行
            sheet.cell(row=row_xuhao, column=10).value = '无'  # 备注

            # 应用格式
            self._apply_legacy_formatting(sheet, index + 1)

            row_xuhao += 1

        # 应用边框格式
        self._apply_legacy_border_formatting(sheet, len(test_item_names))

        self.logger.debug(f"填充了{len(test_item_names)}个测试项（兼容模式）")

    def _apply_legacy_formatting(self, sheet, item):
        """应用策划表单元格格式（兼容模式）"""
        from openpyxl.styles import PatternFill

        light_yellow_fill = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
        light_green_fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
        light_blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")

        # 应用颜色填充
        for col in range(2, 6):
            sheet.cell(row=item + 1, column=col).fill = light_yellow_fill
        sheet.cell(row=item + 1, column=6).fill = light_green_fill
        sheet.cell(row=item + 1, column=7).fill = light_green_fill
        for col in range(8, 11):
            sheet.cell(row=item + 1, column=col).fill = light_blue_fill

    def _apply_legacy_border_formatting(self, sheet, len_dict):
        """应用策划表边框格式（兼容模式）"""
        from openpyxl.styles import Border, Side, Alignment

        border_style = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )

        for row in sheet.iter_rows(min_row=1, max_row=len_dict + 1, min_col=1, max_col=10):
            for cell in row:
                cell.border = border_style
                cell.alignment = Alignment(wrap_text=True, vertical='center')
    
    def write_to_excel_cell_cehuabiao_peizhixing(self, excel_file_path: str, sheet_name: str,
                                               ruanjian_name: str, xinghao_xinxi_list: List[str],
                                               daima_chayi_hangshu: int, ceshixiang_neirong_dict: Dict = None,
                                               zhuguan_name: str = '', ceshiren_name: str = '') -> bool:
        """
        向项目策划表中填充内容（从forms/form_generator.py重构而来）
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            ruanjian_name: 软件名称
            xinghao_xinxi_list: 型号信息列表
            daima_chayi_hangshu: 代码差异行数
            ceshixiang_neirong_dict: 测试项内容字典
            zhuguan_name: 主管姓名
            ceshiren_name: 测试人员姓名
            
        Returns:
            bool: 填充是否成功
        """
        try:
            # 🔧 增加文件完整性检查和错误恢复机制
            # 首先检查文件是否存在
            if not os.path.exists(excel_file_path):
                log_error(f"Excel文件不存在: {excel_file_path}", "project_plan_excel_filler")
                return False
            
            # 检查文件大小，如果太小可能是损坏的
            file_size = os.path.getsize(excel_file_path)
            if file_size < 1024:  # 小于1KB可能是损坏的Excel文件
                log_error(f"Excel文件可能损坏，文件大小过小: {file_size} bytes", "project_plan_excel_filler")
                return False
            
            # 尝试加载Excel文件，如果失败则尝试重新复制模板
            try:
                wb = openpyxl.load_workbook(excel_file_path)
                log_debug(f"成功加载Excel文件: {excel_file_path}", "project_plan_excel_filler")
            except Exception as load_error:
                log_warning(f"Excel文件损坏，尝试重新创建: {load_error}", "project_plan_excel_filler")
                
                # 尝试重新复制模板文件
                if self._recreate_excel_template(excel_file_path):
                    wb = openpyxl.load_workbook(excel_file_path)
                    log_info("成功重新创建Excel模板文件", "project_plan_excel_filler")
                else:
                    raise load_error
            
            # 计算测试时间和规模
            ceshi_start_time, ceshi_end_time = self._calculate_test_time(daima_chayi_hangshu)
            ceshiguimo_jisuan = self._calculate_test_scale(daima_chayi_hangshu)
            
            # [ALERT] 处理测试项数据 - 关键数据监控
            if ceshixiang_neirong_dict:
                len_dict = len(ceshixiang_neirong_dict)
                allkeys = list(ceshixiang_neirong_dict.keys())
                log_info(f"[SUCCESS] [项目策划表] 使用传入的测试项数据 ({len_dict}个)", "project_plan_excel_filler")
                log_debug(f"   测试项字典键: {allkeys}", "project_plan_excel_filler")
                log_debug(f"   测试项字典内容: {ceshixiang_neirong_dict}", "project_plan_excel_filler")
            else:
                len_dict = 5
                allkeys = ['功能测试1', '功能测试2', '功能测试3', '功能测试4', '功能测试5']
                log_warning("[WARNING] [项目策划表] 未提供测试项数据，使用默认测试项", "project_plan_excel_filler")
            
            # [FIX] 用户要求：不再需要生成英文标识
            # 生成功能点英文标识
            # english_identifiers = self._generate_english_identifiers(allkeys)
            english_identifiers = []  # 空列表，不再生成英文标识
            
            # 填充工作表
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                self._fill_project_plan_cells(ws, ruanjian_name, xinghao_xinxi_list, 
                                            ceshi_start_time, ceshi_end_time, 
                                            ceshiguimo_jisuan, allkeys, english_identifiers,
                                            zhuguan_name, ceshiren_name)
                
                # 保存文件
                wb.save(excel_file_path)
                log_info(f"成功填充项目策划表: {excel_file_path}", "project_plan_excel_filler")
                return True
            else:
                log_error(f"工作表 {sheet_name} 不存在", "project_plan_excel_filler")
                return False
                
        except Exception as e:
            log_error(f"填充项目策划表失败", "project_plan_excel_filler", e)
            return False
    
    def _calculate_test_time(self, daima_chayi_hangshu: int) -> tuple:
        """计算测试开始和结束时间"""
        try:
            # 根据代码行数计算测试时间
            if daima_chayi_hangshu <= 100:
                test_days = 7
            elif daima_chayi_hangshu <= 500:
                test_days = 14
            elif daima_chayi_hangshu <= 1000:
                test_days = 21
            else:
                test_days = 30
            
            start_time = datetime.datetime.now()
            end_time = start_time + relativedelta(days=test_days)
            
            return start_time.strftime("%Y-%m-%d"), end_time.strftime("%Y-%m-%d")
            
        except Exception as e:
            log_error(f"计算测试时间失败: {e}", "project_plan_excel_filler")
            return "2024-01-01", "2024-01-31"
    
    def _calculate_test_scale(self, daima_chayi_hangshu: int) -> str:
        """计算测试规模"""
        try:
            if daima_chayi_hangshu <= 100:
                return "小型"
            elif daima_chayi_hangshu <= 500:
                return "中型"
            elif daima_chayi_hangshu <= 1000:
                return "大型"
            else:
                return "超大型"
        except Exception as e:
            log_error(f"计算测试规模失败: {e}", "project_plan_excel_filler")
            return "中型"
    
    def _generate_english_identifiers(self, allkeys: List[str]) -> List[str]:
        """生成英文标识"""
        try:
            # AI翻译模块已删除，直接使用默认标识
            english_identifiers = []
            for i, key in enumerate(allkeys):
                try:
                    # 使用默认标识
                    default_id = f"TEST_{i+1:03d}"
                    english_identifiers.append(default_id)
                except Exception as e:
                    log_warning(f"AI翻译失败: {e}，使用默认标识", "project_plan_excel_filler")
                    default_id = f"TEST_{len(english_identifiers)+1:03d}"
                    english_identifiers.append(default_id)
            
            return english_identifiers
            
        except Exception as e:
            log_error(f"生成英文标识失败: {e}", "project_plan_excel_filler")
            # 返回默认标识
            return [f"TEST_{i+1:03d}" for i in range(len(allkeys))]
    
    def _safe_set_cell_value(self, ws, cell_address: str, value):
        """安全地设置单元格值，处理合并单元格的情况"""
        try:
            cell = ws[cell_address]
            # 检查是否是合并单元格
            if hasattr(cell, 'coordinate'):
                # 尝试直接设置值
                cell.value = value
            else:
                # 如果是合并单元格，可能需要特殊处理
                ws[cell_address] = value
        except Exception as e:
            # 如果设置失败，记录警告但不中断程序
            log_warning(f"设置单元格 {cell_address} 值失败 (可能是合并单元格): {e}", "project_plan_excel_filler")
    
    def _safe_set_cell_value_with_style(self, ws, cell_address: str, value):
        """安全地设置单元格值和蓝色样式"""
        try:
            # 先设置值
            self._safe_set_cell_value(ws, cell_address, value)
            # 再设置样式
            self._safe_set_cell_style(ws, cell_address)
            log_debug(f"      {cell_address}: '{value}' (蓝色样式)", "project_plan_excel_filler")
        except Exception as e:
            log_warning(f"设置单元格 {cell_address} 值和样式失败: {e}", "project_plan_excel_filler")
            
    def _fill_project_plan_cells(self, ws, ruanjian_name: str, xinghao_xinxi_list: List[str],
                                ceshi_start_time: str, ceshi_end_time: str, ceshiguimo_jisuan: str,
                                allkeys: List[str], english_identifiers: List[str],
                                zhuguan_name: str, ceshiren_name: str):
        """填充项目策划表的单元格（根据真实表格结构）"""
        try:
            # 基础信息填充（根据真实截图的位置）
            # [ALERT] 修正：不填充上方项目信息区域，保持空白
            log_debug("[WARNING] [项目策划表] 按要求不填充上方项目信息区域，保持空白", "project_plan_excel_filler")
            
            # 测试项列表填充 - 从第18行开始
            len_value = len(allkeys)
            start_row = 18
            # [FIX] 修改遍历逻辑：不再使用english_identifiers
            for i, test_item in enumerate(allkeys):
                row = start_row + i
                
                # [ALERT] 关键数据填充监控
                log_debug(f"   第{row}行数据填充: test_item='{test_item}'", "project_plan_excel_filler")
                
                # [ALERT] 修正：ID列（A列）不填充任何数据，序号列（B列）从1开始
                # self._safe_set_cell_value(ws, f'A{row}', i + 1)  # ID列不填充数据
                self._safe_set_cell_value_with_style(ws, f'B{row}', i + 1)  # 序号从1开始 + 蓝色样式
                log_debug(f"      列A(ID): 保持空白", "project_plan_excel_filler")
                
                # [ALERT] 关键列：软件需求列（C列）- 应该与需求分析表的软件需求规格说明需求名称列一样
                self._safe_set_cell_value_with_style(ws, f'C{row}', test_item)  # 软件需求列 + 蓝色样式
                
                # 标准子需求名称列和软件需求列一模一样
                self._safe_set_cell_value_with_style(ws, f'D{row}', test_item)  # 标准子需求名称 + 蓝色样式
                
                # 标准子需求单位默认都填0.2
                self._safe_set_cell_value_with_style(ws, f'E{row}', "0.2")  # 标准子需求单位 + 蓝色样式
                
                # 软件需求规格说明/影响域分析报告追踪列
                # 🔧 修复：使用与需求分析表相同的格式，确保包含编号信息
                # 格式：《软件名称软件需求规格说明》 + 完整的需求内容（包含编号）
                # test_item 可能已经包含编号信息（取决于extract_requirements_from_catalog的提取结果）
                tracking_info = f"《{ruanjian_name}软件需求规格说明》 {test_item}"
                log_debug(f"      列F(软件需求规格说明追踪): '{tracking_info}' (与需求分析表格式保持一致)", "project_plan_excel_filler")
                self._safe_set_cell_value_with_style(ws, f'F{row}', tracking_info)  # 软件需求规格说明/影响域分析报告追踪 + 蓝色样式
                
                # 重要性、是否完成测试等（根据截图的列）
                self._safe_set_cell_value_with_style(ws, f'G{row}', "重要")  # 重要性 + 蓝色样式
                self._safe_set_cell_value_with_style(ws, f'H{row}', "是")  # 是否完成测试 + 蓝色样式
                
                # [ALERT] 关键修复：测试工序人员填充 - 填入具体人名而不是通用字符串
                log_debug(f"   第{row}行测试工序人员填充: 测试主管='{zhuguan_name}', 测试人员='{ceshiren_name}'", "project_plan_excel_filler")
                
                # 需求分析列填入测试主管的具体姓名
                actual_zhuguan = zhuguan_name.strip() if zhuguan_name else ""
                self._safe_set_cell_value_with_style(ws, f'I{row}', actual_zhuguan)  # 需求分析 + 蓝色样式
                
                # 文档审查到动态测试都填入测试人员的具体姓名
                actual_ceshiren = ceshiren_name.strip() if ceshiren_name else ""
                self._safe_set_cell_value_with_style(ws, f'J{row}', actual_ceshiren)  # 文档审查 + 蓝色样式
                self._safe_set_cell_value_with_style(ws, f'K{row}', actual_ceshiren)  # 静态分析 + 蓝色样式
                self._safe_set_cell_value_with_style(ws, f'L{row}', actual_ceshiren)  # 代码审查 + 蓝色样式
                self._safe_set_cell_value_with_style(ws, f'M{row}', actual_ceshiren)  # 动态测试 + 蓝色样式
                
                # [FIX] 用户要求：不再填充英文标识到最后一列
                # self._safe_set_cell_value_with_style(ws, f'N{row}', english_id)  # AI翻译的英文标识 + 蓝色样式
                
                # [ALERT] 样式设置已在_safe_set_cell_value_with_style中完成，无需重复设置
            
            # 填充额外信息（在测试项列表后添加）+ 蓝色样式
            end_row = start_row + len_value
            self._safe_set_cell_value_with_style(ws, f'C{end_row + 1}', f"文档审查范围：1.《{ruanjian_name}需求规格说明》；2.《{ruanjian_name}研制任务书》；3.《{ruanjian_name}设计说明》；")
            self._safe_set_cell_value_with_style(ws, f'C{end_row + 2}', "静态分析范围:全部手写代码；")
            self._safe_set_cell_value_with_style(ws, f'C{end_row + 3}', "代码审查范围:全部手写代码；")
            
            log_info(f"[SUCCESS] [项目策划表] 所有填充的单元格已设置蓝色背景样式", "project_plan_excel_filler")
                
        except Exception as e:
            log_error(f"填充项目策划表单元格失败: {e}", "project_plan_excel_filler")
    
    def _safe_set_cell_style(self, ws, cell_address: str):
        """安全地设置单元格样式"""
        try:
            cell = ws[cell_address]
            self._set_cell_style(cell)
        except Exception as e:
            log_warning(f"设置单元格 {cell_address} 样式失败: {e}", "project_plan_excel_filler")
    
    def _set_cell_style(self, cell):
        """设置单元格样式"""
        try:
            # 设置边框
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            cell.border = thin_border
            
            # 设置对齐
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 🎨 设置蓝色背景（填充过数据的单元格）
            blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")  # 与软件配置项信息表保持一致的蓝色
            cell.fill = blue_fill
            
        except Exception as e:
            log_error(f"设置单元格样式失败: {e}", "project_plan_excel_filler")
    
    def _recreate_excel_template(self, excel_file_path: str) -> bool:
        """重新创建Excel模板文件"""
        try:
            # 获取资源管理器来重新复制模板
            from ...utils.resource_manager import ResourceManager
            resource_manager = ResourceManager()
            
            # 获取模板文件路径
            template_file = resource_manager.get_template_path('需求分析表(精准测试工具生成).xlsx')
            
            if not os.path.exists(template_file):
                log_error(f"模板文件不存在: {template_file}", "project_plan_excel_filler")
                return False
            
            # 确保目标目录存在
            target_dir = os.path.dirname(excel_file_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # 删除损坏的文件（如果存在）
            if os.path.exists(excel_file_path):
                try:
                    os.remove(excel_file_path)
                    log_debug(f"删除损坏的Excel文件: {excel_file_path}", "project_plan_excel_filler")
                except Exception as e:
                    log_warning(f"删除损坏文件失败: {e}", "project_plan_excel_filler")
            
            # 重新复制模板文件
            shutil.copy2(template_file, excel_file_path)
            log_info(f"成功重新复制模板文件: {template_file} -> {excel_file_path}", "project_plan_excel_filler")
            
            # 验证新文件是否可以正常加载
            try:
                test_wb = openpyxl.load_workbook(excel_file_path)
                test_wb.close()
                log_debug("新创建的Excel文件验证成功", "project_plan_excel_filler")
                return True
            except Exception as e:
                log_error(f"新创建的Excel文件验证失败: {e}", "project_plan_excel_filler")
                return False
                
        except Exception as e:
            log_error(f"重新创建Excel模板失败: {e}", "project_plan_excel_filler")
            return False
