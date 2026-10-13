import io
import os
from typing import List, Dict, Any, Optional, Tuple, Callable
from sqlalchemy.orm import Session
import logging
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Border, Side, Alignment
from ..db.models import TurretRequirement, CountermeasureAlarmRequirement, OptoRadarRequirement, PodRequirement

logger = logging.getLogger(__name__)

class IntelligentExportService:
    """智能导出服务类"""
    
    # 数据库表映射
    MODEL_MAP = {
        "转塔": TurretRequirement,
        "对抗告警": CountermeasureAlarmRequirement,
        "光雷": OptoRadarRequirement,
        "吊舱": PodRequirement,
    }
    
    # 黄色背景填充样式
    @classmethod
    def get_yellow_fill(cls):
        """获取黄色背景填充样式"""
        return PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    # 蓝色背景填充样式
    @classmethod
    def get_blue_fill(cls):
        """获取蓝色背景填充样式"""
        return PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
    
    # 边框样式
    @classmethod
    def get_border_style(cls):
        """获取单元格边框样式"""
        thin_border = Side(style="thin", color="000000")
        return Border(
            left=thin_border,
            right=thin_border,
            top=thin_border,
            bottom=thin_border
        )
    
    # 自动换行对齐样式
    @classmethod
    def get_wrap_alignment(cls):
        """获取自动换行对齐样式"""
        return Alignment(wrap_text=True, vertical="top", horizontal="left")
    
    # 应用完整样式到单元格
    @classmethod
    def apply_cell_style(cls, cell, fill_color="yellow"):
        """为单元格应用完整样式（背景色、边框、自动换行）"""
        # 设置背景色
        if fill_color == "yellow":
            cell.fill = cls.get_yellow_fill()
        elif fill_color == "blue":
            cell.fill = cls.get_blue_fill()
        
        # 设置边框
        cell.border = cls.get_border_style()
        
        # 设置自动换行
        cell.alignment = cls.get_wrap_alignment()
    
    @classmethod
    def process_intelligent_export_with_progress(
        cls, 
        db: Session, 
        file_content: bytes, 
        selected_type: str,
        selected_software_type: str,
        progress_callback: Callable[[int, str], None] = None
    ) -> bytes:
        """
        处理智能导出（带进度回调）
        
        Args:
            db: 数据库会话
            file_content: 上传的Excel文件内容
            selected_type: 用户选择的类型（转塔、对抗告警、光雷、吊舱）
            selected_software_type: 用户选择的软件类型
            progress_callback: 进度回调函数
            
        Returns:
            处理后的Excel文件内容
        """
        try:
            # 立即测试调试日志器是否工作
            debug_logger = cls._get_debug_logger()
            debug_logger.info("=" * 60)
            debug_logger.info("=== 智能导出开始 ===")
            debug_logger.info(f"导出类型: {selected_type}")
            debug_logger.info(f"软件类型: {selected_software_type}")
            debug_logger.info(f"文件大小: {len(file_content)} bytes")
            debug_logger.info("=" * 60)
            
            if progress_callback:
                progress_callback(5, "开始读取Excel文件...")
                logger.info("Progress callback called: 5% - 开始读取Excel文件...")
            
            logger.info(f"Starting intelligent export, type: {selected_type}, software_type: {selected_software_type}, file size: {len(file_content)} bytes")
            
            # 读取Excel文件
            workbook = cls._read_excel_file(file_content)
            logger.info(f"Excel file loaded successfully, sheets count: {len(workbook.sheetnames)}")
            
            if progress_callback:
                progress_callback(15, "Excel文件读取完成，获取数据库数据...")
                logger.info("Progress callback called: 15% - Excel文件读取完成，获取数据库数据...")
            
            # 获取对应的数据库模型
            model = cls.MODEL_MAP.get(selected_type)
            if not model:
                raise ValueError(f"Unsupported type: {selected_type}")
            
            # 获取组织资产库数据
            asset_data = cls._get_asset_data(db, model)
            logger.info(f"Retrieved {len(asset_data)} asset records")
            
            if progress_callback:
                progress_callback(25, f"获取到{len(asset_data)}条数据库记录，开始处理需求分析表...")
                logger.info(f"Progress callback called: 25% - 获取到{len(asset_data)}条数据库记录，开始处理需求分析表...")
            
            # 处理需求分析表（第4个sheet）
            cls._process_requirement_analysis_sheet(workbook, asset_data, selected_software_type)
            logger.info("Requirements analysis sheet processed")
            
            if progress_callback:
                progress_callback(50, "需求分析表处理完成，开始处理测试用例表...")
            
            # 处理测试用例单（第5个sheet）
            cls._process_test_case_sheet_optimized(workbook, asset_data, selected_software_type, progress_callback)
            logger.info("Test case sheet processed")
            debug_logger = cls._get_debug_logger()
            debug_logger.info("测试用例表处理完成")
            
            if progress_callback:
                progress_callback(90, "测试用例表处理完成，生成最终文件...")
            
            # 生成处理后的Excel文件
            output_content = cls._generate_excel_output(workbook)
            
            if progress_callback:
                progress_callback(100, "智能导出完成")
            
            return output_content
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Intelligent export failed: {error_msg}", exc_info=True)
            if progress_callback:
                progress_callback(0, f"导出失败: {error_msg}")
            raise Exception(f"Intelligent export failed: {error_msg}")

    @classmethod
    def process_intelligent_export(
        cls, 
        db: Session, 
        file_content: bytes, 
        selected_type: str
    ) -> bytes:
        """
        处理智能导出（兼容旧接口）
        """
        return cls.process_intelligent_export_with_progress(db, file_content, selected_type, None)
    
    @classmethod
    def _read_excel_file(cls, file_content: bytes):
        """读取Excel文件"""
        try:
            # 使用BytesIO包装文件内容
            file_stream = io.BytesIO(file_content)
            # 加载工作簿，指定读取模式
            workbook = load_workbook(file_stream, read_only=False, keep_vba=False)
            return workbook
        except Exception as e:
            logger.error(f"Excel file read failed, file size: {len(file_content)} bytes")
            raise ValueError(f"Excel file read failed: {str(e)}")
    
    @classmethod
    def _get_asset_data(cls, db: Session, model) -> List[Dict]:
        """获取组织资产库数据"""
        try:
            records = db.query(model).all()
            asset_data = []
            
            for record in records:
                asset_data.append({
                    'software_category': record.software_category,  # 第一列：软件类别
                    'test_item_name': record.test_item_name,
                    'test_content': record.test_content,
                    'test_method': record.test_method,
                    'case_template_name': record.case_template_name,
                    'case_template_input': record.case_template_input,
                    'case_template_expected': record.case_template_expected
                })
            
            return asset_data
        except Exception as e:
            logger.error(f"Failed to get asset data: {str(e)}")
            raise
    
    @classmethod
    def _process_requirement_analysis_sheet(cls, workbook, asset_data: List[Dict], selected_software_type: str):
        """处理需求分析表（根据名称查找）"""
        try:
            # 根据名称查找需求分析表sheet
            sheet_names = workbook.sheetnames
            debug_logger = cls._get_debug_logger()
            debug_logger.info(f"所有sheet名称: {sheet_names}")
            
            # 查找需求分析表sheet（只支持精确匹配）
            target_sheet_name = '需求分析表'
            worksheet = None
            requirement_sheet_name = None
            
            debug_logger.info(f"寻找名为 '{target_sheet_name}' 的sheet...")
            
            # 精确匹配（忽略前后空格）
            for sheet_name in sheet_names:
                if sheet_name.strip() == target_sheet_name:
                    requirement_sheet_name = sheet_name
                    worksheet = workbook[sheet_name]
                    debug_logger.info(f"✓ 找到需求分析表: '{sheet_name}'")
                    break
            
            # 如果没有找到，直接报错
            if not worksheet:
                error_msg = f"❌ 未找到名为 '{target_sheet_name}' 的工作表"
                debug_logger.error(error_msg)
                debug_logger.error("当前表单包含的所有sheet:")
                for i, name in enumerate(sheet_names, 1):
                    debug_logger.error(f"  {i}. '{name}'")
                raise ValueError(f"表单中缺少必需的 '{target_sheet_name}' 工作表，请检查表单格式")
            
            # 记录详细的sheet信息到日志
            debug_logger.info(f"=== 需求分析表处理开始 ===")
            debug_logger.info(f"选择的sheet: '{requirement_sheet_name}' (在所有sheet中的位置: 第{sheet_names.index(requirement_sheet_name)+1}个)")
            debug_logger.info(f"该sheet的行数: {worksheet.max_row}, 列数: {worksheet.max_column}")
            debug_logger.info(f"用户选择的软件类型: '{selected_software_type}'")
            debug_logger.info(f"该sheet第一行内容预览:")
            
            # 记录前10列的标题信息
            for col_idx in range(1, min(worksheet.max_column + 1, 11)):
                cell_value = worksheet.cell(row=1, column=col_idx).value
                debug_logger.info(f"  列{col_idx}: '{cell_value}'")
            
            # 根据实际表头查找关键列
            # 列15: 测试项名称, 列20: 测试项描述, 列21: 测试方法
            test_item_col = 15  # 测试项名称
            test_desc_col = 20  # 测试项描述  
            test_method_col = 21  # 测试方法
            
            debug_logger.info(f"目标列设置: 测试项名称=列{test_item_col}, 测试项描述=列{test_desc_col}, 测试方法=列{test_method_col}")
            
            # 验证列号是否有效
            if worksheet.max_column < test_item_col:
                debug_logger.error(f"列数不足！当前sheet只有{worksheet.max_column}列，无法访问测试项名称列(第{test_item_col}列)")
                logger.warning("Test item name column not found, skipping requirements analysis sheet")
                return
            
            # 记录关键列的实际标题
            if test_item_col <= worksheet.max_column:
                test_item_header = worksheet.cell(row=1, column=test_item_col).value
                debug_logger.info(f"测试项名称列(第{test_item_col}列)的标题: '{test_item_header}'")
            if test_desc_col <= worksheet.max_column:
                test_desc_header = worksheet.cell(row=1, column=test_desc_col).value
                debug_logger.info(f"测试项描述列(第{test_desc_col}列)的标题: '{test_desc_header}'")
            if test_method_col <= worksheet.max_column:
                test_method_header = worksheet.cell(row=1, column=test_method_col).value
                debug_logger.info(f"测试方法列(第{test_method_col}列)的标题: '{test_method_header}'")
            
            # 遍历每一行，进行匹配和填充
            for row_idx in range(2, worksheet.max_row + 1):  # 从第2行开始（跳过标题行）
                test_item_cell = worksheet.cell(row=row_idx, column=test_item_col)
                test_item_name = str(test_item_cell.value).strip() if test_item_cell.value else ""
                
                if not test_item_name:
                    continue
                
                # 匹配组织资产库数据（增加软件类型匹配）
                matched_records = cls._match_test_items(test_item_name, asset_data, selected_software_type)
                
                if matched_records:
                    # 合并测试内容和测试方法
                    merged_test_content = cls._merge_field_content([r['test_content'] for r in matched_records])
                    merged_test_method = cls._merge_field_content([r['test_method'] for r in matched_records])
                    
                    # 填充到表格并设置完整样式（背景色、边框、自动换行）
                    if test_desc_col <= worksheet.max_column:
                        cell = worksheet.cell(row=row_idx, column=test_desc_col, value=merged_test_content)
                        cls.apply_cell_style(cell, "yellow")
                        debug_logger.info(f"  -> 已填充测试项描述到行{row_idx}")
                    if test_method_col <= worksheet.max_column:
                        cell = worksheet.cell(row=row_idx, column=test_method_col, value=merged_test_method)
                        cls.apply_cell_style(cell, "yellow")
                        debug_logger.info(f"  -> 已填充测试方法到行{row_idx}")
            
            debug_logger.info("=== 需求分析表处理完成 ===")
            
        except Exception as e:
            debug_logger.error(f"需求分析表处理失败: {str(e)}")
            logger.error(f"Failed to process requirements analysis sheet: {str(e)}")
            raise
    
    @classmethod
    def _process_test_case_sheet_optimized(cls, workbook, asset_data: List[Dict], selected_software_type: str, progress_callback: Callable[[int, str], None] = None):
        """处理测试用例单（根据名称查找），优化性能"""
        try:
            # 根据名称查找测试用例单sheet
            sheet_names = workbook.sheetnames
            debug_logger = cls._get_debug_logger()
            debug_logger.info(f"查找测试用例单，所有sheet名称: {sheet_names}")
            debug_logger.info(f"用户选择的软件类型: '{selected_software_type}'")
            
            # 查找测试用例单sheet（只支持精确匹配）
            target_sheet_name = '测试用例单'
            worksheet = None
            test_case_sheet_name = None
            
            debug_logger.info(f"寻找名为 '{target_sheet_name}' 的sheet...")
            
            # 精确匹配（忽略前后空格）
            for sheet_name in sheet_names:
                if sheet_name.strip() == target_sheet_name:
                    test_case_sheet_name = sheet_name
                    worksheet = workbook[sheet_name]
                    debug_logger.info(f"✓ 找到测试用例单: '{sheet_name}'")
                    break
            
            # 如果没有找到，直接报错
            if not worksheet:
                error_msg = f"❌ 未找到名为 '{target_sheet_name}' 的工作表"
                debug_logger.error(error_msg)
                debug_logger.error("当前表单包含的所有sheet:")
                for i, name in enumerate(sheet_names, 1):
                    debug_logger.error(f"  {i}. '{name}'")
                raise ValueError(f"表单中缺少必需的 '{target_sheet_name}' 工作表，请检查表单格式")
            
            logger.info(f"Processing test case sheet: {worksheet.title}")
            
            # 记录详细的sheet信息到日志
            debug_logger.info(f"=== 测试用例单处理开始 ===")
            debug_logger.info(f"选择的sheet: '{test_case_sheet_name}' (在所有sheet中的位置: 第{sheet_names.index(test_case_sheet_name)+1}个)")
            debug_logger.info(f"该sheet的行数: {worksheet.max_row}, 列数: {worksheet.max_column}")
            debug_logger.info(f"该sheet第一行内容预览:")
            
            # 记录前17列的标题信息（测试用例单列数较多）
            for col_idx in range(1, min(worksheet.max_column + 1, 18)):
                cell_value = worksheet.cell(row=1, column=col_idx).value
                debug_logger.info(f"  列{col_idx}: '{cell_value}'")
            
            # 目标列定义
            test_item_col = 7  # 第7列是测试项列
            case_name_col = 9
            test_desc_col = 12
            input_condition_col = 16
            expected_result_col = 17
            
            debug_logger.info(f"目标列设置: 测试项=列{test_item_col}, 用例名称=列{case_name_col}, 测试描述=列{test_desc_col}, 输入条件=列{input_condition_col}, 预期结果=列{expected_result_col}")
            
            # 记录关键列的实际标题
            key_columns = [
                (test_item_col, "测试项"),
                (case_name_col, "用例名称"), 
                (test_desc_col, "测试描述"),
                (input_condition_col, "输入条件"),
                (expected_result_col, "预期结果")
            ]
            
            for col_idx, col_name in key_columns:
                if col_idx <= worksheet.max_column:
                    header = worksheet.cell(row=1, column=col_idx).value
                    debug_logger.info(f"{col_name}列(第{col_idx}列)的标题: '{header}'")
                else:
                    debug_logger.warning(f"{col_name}列(第{col_idx}列)超出sheet列数范围")
            
            if progress_callback:
                progress_callback(52, "分析测试用例表结构...")
            
            # 第一步：分析测试项分组
            test_item_groups = cls._analyze_test_item_groups(worksheet, 7)  # 第7列是测试项列
            logger.info(f"发现 {len(test_item_groups)} 个测试项分组")
            
            if progress_callback:
                progress_callback(60, f"发现{len(test_item_groups)}个测试项，开始匹配数据库记录...")
            
            # 第二步：精确位置计算策略 - 逐个处理测试项，精确计算后续位置偏移
            matched_count = 0
            
            debug_logger.info(f"[INSERTION_STRATEGY] 使用精确位置计算策略：逐个处理测试项，精确计算位置偏移")
            
            # 预先匹配所有测试项，了解哪些需要插入
            all_matches = {}
            debug_logger.info(f"[PRE_MATCH] 预先匹配所有测试项...")
            for test_item_name, group_info in test_item_groups.items():
                matched_records = cls._match_test_items(test_item_name, asset_data, selected_software_type)
                if matched_records:
                    all_matches[test_item_name] = matched_records
                    debug_logger.info(f"[PRE_MATCH] 测试项'{test_item_name}' 匹配到{len(matched_records)}条记录")
                else:
                    debug_logger.info(f"[PRE_MATCH] 测试项'{test_item_name}' 无匹配记录")
            
            debug_logger.info(f"[PRE_MATCH] 总共有{len(all_matches)}个测试项需要插入用例")
            
            # 创建一个工作副本，用于跟踪位置变化
            working_groups = {k: v.copy() for k, v in test_item_groups.items()}
            
            # 按测试项的first_row正序排序，从前往后逐个处理
            while all_matches:
                # 找到下一个要处理的测试项（按first_row排序的第一个）
                next_test_item = None
                next_group_info = None
                min_first_row = float('inf')
                
                for test_item_name in all_matches.keys():
                    if test_item_name in working_groups:
                        current_first_row = working_groups[test_item_name]['first_row']
                        if current_first_row < min_first_row:
                            min_first_row = current_first_row
                            next_test_item = test_item_name
                            next_group_info = working_groups[test_item_name]
                
                if not next_test_item:
                    debug_logger.warning(f"[ERROR] 找不到下一个要处理的测试项，剩余: {list(all_matches.keys())}")
                    break
                
                # 处理选中的测试项
                matched_records = all_matches[next_test_item]
                matched_count += len(matched_records)
                
                debug_logger.info(f"[PROCESS] 处理测试项'{next_test_item}'")
                debug_logger.info(f"[CURRENT_POS] 当前位置: 第{next_group_info['first_row']}-{next_group_info['last_row']}行")
                
                # 计算该测试项原有的用例行数
                original_rows_count = next_group_info['last_row'] - next_group_info['first_row'] + 1
                debug_logger.info(f"[ORIGINAL_ROWS] 该测试项原有{original_rows_count}行用例")
                debug_logger.info(f"[REPLACE_PLAN] 将删除原有{original_rows_count}行，替换为{len(matched_records)}条匹配的用例")
                
                # 记录匹配到的具体数据库记录
                for j, record in enumerate(matched_records):
                    debug_logger.info(f"  匹配记录{j+1}: {record.get('test_item_name', 'N/A')} - {record.get('case_template_name', 'N/A')}")
                
                # 准备该测试项的替换操作
                test_item_insertions = []
                replace_start_row = next_group_info['first_row']
                
                for i, record in enumerate(matched_records):
                    insert_row_idx = replace_start_row + i
                    row_data = cls._prepare_test_case_row_data(worksheet, next_group_info['first_row'], record)
                    test_item_insertions.append((insert_row_idx, row_data, record, next_test_item))
                    case_name = record.get('case_template_name', 'N/A')
                    debug_logger.info(f"  计划替换第{i+1}条: '{case_name}' → 第{insert_row_idx}行")
                
                # 执行替换操作：先删除原有行，再插入新行
                debug_logger.info(f"[EXECUTE_REPLACE] 执行测试项'{next_test_item}'的替换操作")
                cls._replace_test_item_rows(worksheet, next_group_info['first_row'], original_rows_count, test_item_insertions, progress_callback)
                
                # 精确计算位置偏移：行数变化 = 新行数 - 原行数
                rows_delta = len(matched_records) - original_rows_count
                debug_logger.info(f"[POSITION_UPDATE] 行数变化: {rows_delta} (新增{len(matched_records)}行 - 删除{original_rows_count}行)")
                
                # 更新所有在当前测试项之后的测试项位置
                for item_name, item_info in working_groups.items():
                    if item_name != next_test_item and item_info['first_row'] > next_group_info['last_row']:
                        old_first = item_info['first_row']
                        old_last = item_info['last_row']
                        item_info['first_row'] += rows_delta
                        item_info['last_row'] += rows_delta
                        debug_logger.info(f"[UPDATE_POS] 测试项'{item_name}': {old_first}-{old_last} → {item_info['first_row']}-{item_info['last_row']}")
                
                # 从待处理列表中移除已处理的测试项
                del all_matches[next_test_item]
                
                # 每处理完一个测试项后立即更新进度
                processed_items = len([name for name in test_item_groups.keys() if name not in all_matches])
                total_items = len(test_item_groups)
                progress = 60 + int((processed_items / total_items) * 25)  # 60-85%进度区间
                if progress_callback:
                    progress_callback(progress, f"已完成{processed_items}/{total_items}个测试项，正在处理...")
                
                debug_logger.info(f"[COMPLETE] 测试项'{next_test_item}'处理完成，剩余{len(all_matches)}个测试项")
            
            debug_logger.info(f"[ALL_COMPLETE] 所有测试项处理完成！共插入{matched_count}条记录")
            
            logger.info(f"所有测试项处理完成，共插入 {matched_count} 条记录")
            
            if progress_callback:
                progress_callback(85, f"测试用例表处理完成，共插入{matched_count}条记录")
                
        except Exception as e:
            logger.error(f"Failed to process test case sheet: {str(e)}")
            if progress_callback:
                progress_callback(50, f"测试用例表处理失败: {str(e)}")
            raise
    
    @classmethod
    def _prepare_test_case_row_data(cls, worksheet, template_row_idx: int, record: Dict) -> List:
        """准备测试用例行数据"""
        # 复制模板行的基础数据
        row_data = []
        for col_idx in range(1, worksheet.max_column + 1):
            template_value = worksheet.cell(row=template_row_idx, column=col_idx).value
            row_data.append(template_value or "")
        # 填入数据库记录的特定数据（只在需要的列）
        # 这里可以根据需要设置特定列的值
        
        return row_data
    
    @classmethod
    def _replace_test_item_rows(cls, worksheet, start_row: int, original_rows_count: int, insertions: List[Tuple], progress_callback: Callable[[int, str], None] = None):
        """替换测试项的所有用例行：先删除原有行，再插入新行"""
        try:
            if not insertions:
                return
            
            debug_logger = cls._get_debug_logger()
            total_insertions = len(insertions)
            test_item_name = insertions[0][3] if len(insertions[0]) == 4 else "未知测试项"
            
            debug_logger.info(f"[REPLACE_START] 测试项'{test_item_name}' 开始替换操作")
            debug_logger.info(f"[DELETE_ROWS] 删除第{start_row}行开始的{original_rows_count}行原有用例")
            
            # 第一步：删除原有的所有行
            worksheet.delete_rows(start_row, original_rows_count)
            debug_logger.info(f"[DELETE_COMPLETE] 删除完成")
            
            # 第二步：在相同位置插入新的匹配用例
            debug_logger.info(f"[INSERT_NEW] 在第{start_row}行开始插入{total_insertions}行新用例")
            worksheet.insert_rows(start_row, total_insertions)
            debug_logger.info(f"[INSERT_COMPLETE] 插入完成")
            
            # 获取列索引
            case_name_col = 9
            test_desc_col = 12
            input_condition_col = 16
            expected_result_col = 17
            
            # 第三步：设置每一行的内容和样式
            for i, insertion_data in enumerate(insertions):
                # 兼容新旧格式
                if len(insertion_data) == 4:
                    insert_row_idx, row_data, record, _ = insertion_data
                else:
                    insert_row_idx, row_data, record = insertion_data
                
                # 实际行号是连续的
                actual_row = start_row + i
                debug_logger.info(f"[SET_ROW_DATA] 第{i+1}行: 设置第{actual_row}行数据")
                
                # 批量设置单元格值和样式
                for col_idx, value in enumerate(row_data, 1):
                    cell = worksheet.cell(row=actual_row, column=col_idx, value=value)
                    
                    # 设置样式和填入数据库数据
                    if col_idx in [case_name_col, test_desc_col, input_condition_col, expected_result_col]:
                        # 重要列使用黄色背景，并添加边框和自动换行
                        cls.apply_cell_style(cell, "yellow")
                        # 填入数据库数据
                        if col_idx == case_name_col and record.get('case_template_name'):
                            cell.value = record.get('case_template_name')
                        elif col_idx == test_desc_col and record.get('test_content'):
                            cell.value = record.get('test_content')
                        elif col_idx == input_condition_col and record.get('case_template_input'):
                            cell.value = record.get('case_template_input')
                        elif col_idx == expected_result_col and record.get('case_template_expected'):
                            cell.value = record.get('case_template_expected')
                    else:
                        # 其他列使用蓝色背景，并添加边框
                        cls.apply_cell_style(cell, "blue")
                
                # 定期更新进度（减少更新频率，避免影响性能）
                if progress_callback and i % 20 == 0:
                    progress = 70 + int((i / total_insertions) * 10)  # 70-80%的进度区间
                    progress_callback(progress, f"正在设置测试项'{test_item_name}'第{i+1}/{total_insertions}行数据...")
            
            logger.info(f"替换完成，删除{original_rows_count}行，插入{total_insertions}行")
            debug_logger.info(f"[REPLACE_COMPLETE] 测试项'{test_item_name}' 替换完成：删除{original_rows_count}行 → 插入{total_insertions}行")
            
        except Exception as e:
            logger.error(f"替换测试项行失败: {str(e)}")
            raise

    @classmethod
    def _batch_insert_rows(cls, worksheet, insertions: List[Tuple], progress_callback: Callable[[int, str], None] = None):
        """批量插入行（性能优化）"""
        try:
            # 按插入位置从大到小排序，从后往前插入
            insertions.sort(key=lambda x: x[0], reverse=True)
            
            total_insertions = len(insertions)
            logger.info(f"开始批量插入 {total_insertions} 行")
            
            # 获取列索引
            case_name_col = 9
            test_desc_col = 12
            input_condition_col = 16
            expected_result_col = 17
            
            # 批量插入（减少日志输出）
            for i, insertion_data in enumerate(insertions):
                # 兼容新旧格式：(insert_row_idx, row_data, record) 或 (insert_row_idx, row_data, record, test_item_name)
                if len(insertion_data) == 4:
                    insert_row_idx, row_data, record, test_item_name = insertion_data
                else:
                    insert_row_idx, row_data, record = insertion_data
                    test_item_name = "未知测试项"
                # 插入新行
                worksheet.insert_rows(insert_row_idx)
                
                # 调试日志：记录插入操作
                if i < 20:  # 只记录前20次插入操作，避免日志过多
                    debug_logger = cls._get_debug_logger()
                    debug_logger.info(f"[INSERT_ROW] 第{i+1}次插入: 测试项'{test_item_name}' 在第{insert_row_idx}行插入用例")
                
                # 批量设置单元格值和样式
                for col_idx, value in enumerate(row_data, 1):
                    cell = worksheet.cell(row=insert_row_idx, column=col_idx, value=value)
                    
                    # 设置样式和填入数据库数据
                    if col_idx in [case_name_col, test_desc_col, input_condition_col, expected_result_col]:
                        # 重要列使用黄色背景，并添加边框和自动换行
                        cls.apply_cell_style(cell, "yellow")
                        # 填入数据库数据
                        if col_idx == case_name_col and record.get('case_template_name'):
                            cell.value = record.get('case_template_name')
                        elif col_idx == test_desc_col and record.get('test_content'):
                            cell.value = record.get('test_content')
                    elif col_idx == input_condition_col and record.get('case_template_input'):
                            cell.value = record.get('case_template_input')
                    elif col_idx == expected_result_col and record.get('case_template_expected'):
                            cell.value = record.get('case_template_expected')
                    else:
                        # 其他列使用蓝色背景，并添加边框
                        cls.apply_cell_style(cell, "blue")
                
                # 定期更新进度（每20行更新一次，减少频率）
                if progress_callback and i % 20 == 0:
                    progress = 70 + int((i / total_insertions) * 10)  # 70-80%的进度区间
                    progress_callback(progress, f"正在插入测试项'{test_item_name}'第{i+1}/{total_insertions}行...")
            
            logger.info(f"批量插入完成，共插入 {total_insertions} 行")
            
        except Exception as e:
            logger.error(f"Batch insert failed: {str(e)}")
            raise
    
    @classmethod
    def _analyze_test_item_groups(cls, worksheet, test_item_col: int) -> Dict[str, Dict]:
        """分析测试项的分组，返回每个测试项的第一行和最后一行"""
        test_item_groups = {}
        current_test_item = None
        
        # 调试：记录列号和工作表信息
        logger.info(f"开始分析测试用例表分组 - 测试项列号: {test_item_col}, 最大行数: {worksheet.max_row}, 最大列数: {worksheet.max_column}")
        
        for row_idx in range(2, worksheet.max_row + 1):  # 从第2行开始（跳过标题行）
            test_item_cell = worksheet.cell(row=row_idx, column=test_item_col)
            test_item_name = str(test_item_cell.value).strip() if test_item_cell.value else ""
            
            # 调试：记录每行的测试项名称
            if row_idx <= 10:  # 只记录前10行以避免日志过多
                logger.debug(f"   行{row_idx}: 列{test_item_col}的值 = '{test_item_cell.value}' -> 标准化后 = '{test_item_name}'")
            
            if test_item_name:
                # 新的测试项
                if test_item_name != current_test_item:
                    current_test_item = test_item_name
                    test_item_groups[test_item_name] = {
                        'first_row': row_idx,
                        'last_row': row_idx
                    }
                    logger.debug(f"   [NEW] 发现新测试项: '{test_item_name}' (行{row_idx})")
                else:
                    # 同一个测试项，更新最后一行
                    test_item_groups[test_item_name]['last_row'] = row_idx
                    logger.debug(f"   [UPDATE] 更新测试项 '{test_item_name}' 最后一行为: {row_idx}")
            else:
                # 空行处理：使用智能策略避免性能问题
                if current_test_item and current_test_item in test_item_groups:
                    current_last_row = test_item_groups[current_test_item]['last_row']
                    
                    # 策略1: 如果当前行距离测试项起始行不远，可能是该测试项的内容行
                    # 策略2: 如果连续空行太多（超过50行），停止扩展，避免性能问题
                    if (row_idx - current_last_row) <= 50:
                        # 只对近距离的行进行内容检查，避免检查大量无关空行
                        has_content = False
                        
                        # 快速检查：只检查最关键的测试用例名称列（第9列）
                        if 9 <= worksheet.max_column:
                            case_name_value = worksheet.cell(row=row_idx, column=9).value
                            if case_name_value and str(case_name_value).strip():
                                has_content = True
                        
                        if has_content:
                            test_item_groups[current_test_item]['last_row'] = row_idx
                            logger.debug(f"   [CONTENT] 有内容行更新测试项 '{current_test_item}' 最后一行为: {row_idx}")
                        else:
                            logger.debug(f"   [SKIP] 跳过空行: {row_idx}")
                    else:
                        # 距离太远的空行，不再归属到当前测试项，避免性能问题
                        logger.debug(f"   [DISTANCE] 距离过远，跳过行: {row_idx} (距离: {row_idx - current_last_row})")
                        pass
                else:
                    logger.debug(f"   [NO_ITEM] 无当前测试项，跳过空行: {row_idx}")
        
        # 调试：记录分析结果
        logger.info(f"测试项分组分析完成，共识别到 {len(test_item_groups)} 个测试项:")
        for item_name, item_info in test_item_groups.items():
            logger.info(f"   [ITEM] '{item_name}': 行{item_info['first_row']}-{item_info['last_row']}")
        
        return test_item_groups
    
    @classmethod
    def _find_column_in_worksheet(cls, worksheet, possible_names: List[str]) -> Optional[int]:
        """在工作表中查找列名，返回列号（1-based）"""
        if worksheet.max_row == 0:
            return None
            
        # 检查第一行的标题
        for col_idx in range(1, worksheet.max_column + 1):
            cell_value = worksheet.cell(row=1, column=col_idx).value
            if cell_value:
                for name in possible_names:
                    if name in str(cell_value):
                        return col_idx
        return None
    
    @classmethod  
    def _get_debug_logger(cls):
        """获取调试日志器，确保总是附加文件处理器到 backend/logs/intelligent_export_debug.log"""
        debug_logger = logging.getLogger('intelligent_export_debug')
        debug_logger.setLevel(logging.DEBUG)
        # 禁止向上冒泡，避免被全局配置劫持
        debug_logger.propagate = False

        # 目标日志文件
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logs'))
        os.makedirs(log_dir, exist_ok=True)
        target_logfile = os.path.join(log_dir, 'intelligent_export_debug.log')

        # 判断是否已经存在指向同一文件的 FileHandler
        has_target_file_handler = False
        for h in debug_logger.handlers:
            try:
                if isinstance(h, logging.FileHandler) and os.path.abspath(getattr(h, 'baseFilename', '')) == target_logfile:
                    has_target_file_handler = True
                    break
            except Exception:
                continue

        if not has_target_file_handler:
            file_handler = logging.FileHandler(target_logfile, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            debug_logger.addHandler(file_handler)

        return debug_logger
    
    @classmethod
    def _match_test_items(cls, test_item_name: str, asset_data: List[Dict], selected_software_type: str) -> List[Dict]:
        """
        智能匹配测试项名称
        使用分层双向匹配策略：
        1. 首先匹配软件类别：检查数据库记录的软件类别是否与用户选择的软件类型匹配
           - 支持"||"分隔的多个软件类别，只要有一个匹配即可
        2. 然后匹配测试项名称：
           - 检查表单测试项是否包含特殊关键词（边界测试、性能测试等）
           - 如果包含，则允许匹配同样包含这些关键词的数据库项
           - 如果不包含，则过滤掉数据库中包含这些关键词的项  
           - 支持双向包含匹配：
             * 正向匹配：表单名称包含在数据库名称中（如：手动搜索 → 手动搜索功能）
             * 反向匹配：数据库名称包含在表单名称中（如：自动扫描好 ← 自动扫描）
           - 支持"||"分隔的多个等价名称
        """
        matched_records = []
        
        # 定义特殊测试关键词
        special_keywords = ['边界测试', '性能测试', '压力测试', '负载测试', '稳定性测试']
        
        # 标准化表单测试项名称（去除首尾空格）
        form_test_name = test_item_name.strip()
        
        debug_logger = cls._get_debug_logger()
        debug_logger.info(f"[MATCH_START] 开始智能匹配测试项: '{form_test_name}'")
        debug_logger.info(f"[SOFTWARE_TYPE] 用户选择的软件类型: '{selected_software_type}'")
        debug_logger.info(f"[DATABASE_SIZE] 资产库总记录数: {len(asset_data)}")
        
        # 检查表单测试项是否包含特殊关键词
        form_has_special_keyword = False
        form_special_keywords = []
        form_core_name = form_test_name
        
        for keyword in special_keywords:
            if keyword in form_test_name:
                form_has_special_keyword = True
                form_special_keywords.append(keyword)
                # 提取核心测试项名称（去除特殊关键词部分）
                form_core_name = form_test_name.replace(f'（{keyword}）', '').replace(f'({keyword})', '').strip()
        
        if form_has_special_keyword:
            debug_logger.info(f"[SPECIAL_FORM] 表单测试项包含特殊关键词: {form_special_keywords}")
            debug_logger.info(f"[CORE_NAME] 提取的核心测试项名称: '{form_core_name}'")
            debug_logger.info(f"[MATCH_STRATEGY] 使用特殊双向匹配策略：优先完整匹配，其次双向核心匹配")
        else:
            debug_logger.info(f"[NORMAL_FORM] 表单测试项为普通测试项，使用双向包含匹配并过滤特殊关键词")
        
        # 统计变量
        total_checked = 0
        filtered_count = 0
        software_filtered_count = 0  # 软件类别过滤计数
        exact_matches = []  # 完整匹配结果
        core_matches = []   # 核心匹配结果
        
        for record in asset_data:
            asset_test_name = record['test_item_name']
            if not asset_test_name:
                continue
            
            # ===== 第一层匹配：软件类别匹配 =====
            asset_software_category = record.get('software_category', '')
            if not asset_software_category:
                debug_logger.info(f"[SOFTWARE_FILTER] 跳过记录'{asset_test_name}'：软件类别为空")
                continue
            
            # 处理多个软件类别（用 || 分隔）
            asset_categories = [cat.strip() for cat in str(asset_software_category).split('||')]
            
            # 检查是否有任何一个软件类别与用户选择的匹配
            # 注意："通用"类别应该匹配任何用户选择的软件类型
            software_matched = False
            matched_category = None
            for category in asset_categories:
                if category == selected_software_type or category == "通用":
                    software_matched = True
                    matched_category = category
                    if category == "通用":
                        debug_logger.info(f"[SOFTWARE_MATCH] 软件类别匹配成功: 数据库'通用' 匹配任何软件类型 (用户选择: '{selected_software_type}')")
                    else:
                        debug_logger.info(f"[SOFTWARE_MATCH] 软件类别匹配成功: 数据库'{category}' = 用户选择'{selected_software_type}'")
                    break
            
            if not software_matched:
                debug_logger.debug(f"[SOFTWARE_FILTER] 软件类别不匹配，跳过记录'{asset_test_name}' (数据库类别: {asset_software_category}, 用户选择: {selected_software_type})")
                software_filtered_count += 1
                continue
            
            # ===== 第二层匹配：测试项名称匹配 =====
            # 处理多个并列的测试项名称（用 || 分隔）
            asset_names = [name.strip() for name in str(asset_test_name).split('||')]
            
            # 标记当前记录是否已经匹配，避免重复添加
            record_matched = False
            match_info = []  # 记录匹配信息用于调试
            
            for asset_name in asset_names:
                if not asset_name:
                    continue
                
                # 如果当前记录已经匹配过，跳过后续检查
                if record_matched:
                    continue
                
                if form_has_special_keyword:
                    # 特殊情况：表单测试项包含特殊关键词
                    # 策略1：完整匹配（优先级最高）
                    if form_test_name == asset_name:
                        exact_matches.append(record)
                        debug_logger.info(f"[EXACT_MATCH] 完整匹配成功: '{form_test_name}' = '{asset_name}'")
                        total_checked += 1
                        record_matched = True
                        match_info.append(f"完整匹配: '{asset_name}'")
                        continue
                        
                    # 策略2：特殊关键词严格匹配
                    # 要求：核心名称匹配 + 数据库项必须包含表单的特殊关键词
                    # 方向1：表单核心名称包含在数据库名称中
                    # 方向2：数据库名称包含在表单核心名称中
                    is_forward_match = form_core_name in asset_name  # 表单核心 → 数据库
                    is_reverse_match = asset_name in form_core_name  # 数据库 → 表单核心
                    
                    if is_forward_match or is_reverse_match:
                        # 检查数据库项是否包含表单的特殊关键词
                        contains_form_keywords = any(keyword in asset_name for keyword in form_special_keywords)
                        
                        match_direction = "正向" if is_forward_match else "反向"
                        
                        if contains_form_keywords:
                            # 数据库项包含表单的特殊关键词，才认为匹配成功
                            exact_matches.append(record)
                            debug_logger.info(f"[SPECIAL_STRICT_MATCH] 特殊关键词严格匹配({match_direction}): 表单核心'{form_core_name}' 与数据库'{asset_name}' 匹配，且包含特殊关键词{form_special_keywords}")
                            match_info.append(f"特殊关键词严格匹配({match_direction}): '{asset_name}'")
                            total_checked += 1
                            record_matched = True
                        else:
                            # 数据库项不包含表单的特殊关键词，不匹配（过滤掉）
                            debug_logger.info(f"[SPECIAL_FILTER] 过滤不匹配项: 表单'{form_test_name}'包含特殊关键词{form_special_keywords}，但数据库'{asset_name}'不包含，跳过")
                            filtered_count += 1
                        continue
                        
                else:
                    # 普通情况：表单测试项不包含特殊关键词
                    # 使用双向包含匹配，但过滤掉包含特殊关键词的数据库项
                    
                    # 方向1：表单包含在数据库中
                    is_forward_match = form_test_name in asset_name
                    # 方向2：数据库包含在表单中
                    is_reverse_match = asset_name in form_test_name
                    
                    if is_forward_match or is_reverse_match:
                        total_checked += 1
                        match_direction = "正向" if is_forward_match else "反向"
                        
                        debug_logger.info(f"[CANDIDATE_MATCH] 候选匹配({match_direction}): 表单'{form_test_name}' 与数据库'{asset_name}' 匹配")
                        
                        # 检查数据库项是否包含需要过滤的特殊关键词
                        should_filter = False
                        filtered_keyword = None
                        for keyword in special_keywords:
                            if keyword in asset_name:
                                debug_logger.info(f"[FILTER_OUT] 过滤测试项 '{asset_name}' (包含关键词: '{keyword}')")
                                should_filter = True
                                filtered_keyword = keyword
                                filtered_count += 1
                                break
                        
                        if not should_filter:
                            matched_records.append(record)
                            logger.debug(f"[CONTAIN_MATCH] 双向包含匹配成功({match_direction}): 表单'{form_test_name}' 与数据库'{asset_name}' (来源: {asset_test_name})")
                            debug_logger.info(f"[CONTAIN_MATCH] 双向包含匹配成功({match_direction}): 表单'{form_test_name}' 与数据库'{asset_name}'")
                            record_matched = True
                            match_info.append(f"双向包含匹配({match_direction}): '{asset_name}'")
                        else:
                            debug_logger.info(f"[FILTERED] 跳过匹配项: '{asset_name}' (包含过滤关键词: '{filtered_keyword}')")
            
            # 记录当前数据库记录的匹配情况
            if match_info:
                debug_logger.info(f"[RECORD_MATCH] 数据库记录'{asset_test_name}' 匹配情况: {'; '.join(match_info)}")
            else:
                debug_logger.debug(f"[RECORD_NO_MATCH] 数据库记录'{asset_test_name}' 无匹配")
        
        # 对于特殊关键词的表单测试项，只使用完整匹配结果（不再使用核心匹配作为备选）
        if form_has_special_keyword:
            if exact_matches:
                matched_records = exact_matches
                debug_logger.info(f"[RESULT] 使用特殊关键词严格匹配结果，共 {len(exact_matches)} 项")
            else:
                debug_logger.info(f"[RESULT] 无任何匹配结果（特殊关键词严格匹配模式）")
        
        # 记录匹配结果和统计信息（同时写入调试日志文件）
        if form_has_special_keyword:
            debug_logger.info(f"[MATCH_STATS] 特殊匹配统计: 软件类型='{selected_software_type}', 资产库总数={len(asset_data)}, 软件类别过滤={software_filtered_count}, 检查了 {total_checked} 个候选项，完整匹配 {len(exact_matches)} 个，核心匹配 {len(core_matches)} 个，最终使用 {len(matched_records)} 个")
            match_type = "特殊匹配"
        else:
            debug_logger.info(f"[MATCH_STATS] 普通匹配统计: 软件类型='{selected_software_type}', 资产库总数={len(asset_data)}, 软件类别过滤={software_filtered_count}, 检查了 {total_checked} 个候选项，过滤了 {filtered_count} 个，最终匹配 {len(matched_records)} 个")
            match_type = "包含匹配"
        
        if matched_records:
            logger.info(f"测试项 '{form_test_name}' (软件类型: {selected_software_type}) 找到 {len(matched_records)} 个{match_type} (检查了{total_checked}个候选项)")
            debug_logger.info(f"测试项 '{form_test_name}' (软件类型: {selected_software_type}) 找到 {len(matched_records)} 个{match_type}")
            for i, record in enumerate(matched_records):
                logger.info(f"   [MATCH_{i+1}] 测试项名称: {record.get('test_item_name', 'N/A')}")
                logger.info(f"   [MATCH_{i+1}] 测试内容: {record.get('test_content', 'N/A')}")
                logger.info(f"   [MATCH_{i+1}] 测试方法: {record.get('test_method', 'N/A')}")
                logger.info(f"   [MATCH_{i+1}] 用例模板名称: {record.get('case_template_name', 'N/A')}")
                logger.info(f"   [MATCH_{i+1}] 用例输入条件: {record.get('case_template_input', 'N/A')}")
                logger.info(f"   [MATCH_{i+1}] 用例预期结果: {record.get('case_template_expected', 'N/A')}")
                
                # 写入调试日志文件
                debug_logger.info(f"   [MATCH_{i+1}] 测试项名称: {record.get('test_item_name', 'N/A')}")
                debug_logger.info(f"   [MATCH_{i+1}] 软件类别: {record.get('software_category', 'N/A')}")
                debug_logger.info(f"   [MATCH_{i+1}] 测试内容: {record.get('test_content', 'N/A')}")
                debug_logger.info(f"   [MATCH_{i+1}] 测试方法: {record.get('test_method', 'N/A')}")
                debug_logger.info(f"   [MATCH_{i+1}] 用例模板名称: {record.get('case_template_name', 'N/A')}")
                debug_logger.info(f"   [MATCH_{i+1}] 用例输入条件: {record.get('case_template_input', 'N/A')}")
                debug_logger.info(f"   [MATCH_{i+1}] 用例预期结果: {record.get('case_template_expected', 'N/A')}")
        else:
            logger.warning(f"测试项 '{form_test_name}' 未找到任何匹配的数据库记录")
            debug_logger.warning(f"测试项 '{form_test_name}' 未找到任何匹配的数据库记录")
            debug_logger.warning(f"[FILTER_SUMMARY] 软件类别过滤了 {software_filtered_count} 条记录")
            
            # 显示被软件类别过滤掉的相关记录（用于调试）
            if software_filtered_count > 0:
                debug_logger.warning(f"[FILTERED_RECORDS] 以下是被软件类别过滤掉但测试项名称可能相关的记录:")
                filtered_shown = 0
                for record in asset_data:
                    if filtered_shown >= 5:  # 最多显示5条
                        break
                    asset_test_name = record['test_item_name']
                    asset_software_category = record.get('software_category', '')
                    
                    # 检查测试项名称是否相关
                    if form_test_name in str(asset_test_name) or str(asset_test_name) in form_test_name:
                        # 检查软件类别是否不匹配
                        asset_categories = [cat.strip() for cat in str(asset_software_category).split('||')]
                        if selected_software_type not in asset_categories and "通用" not in asset_categories:
                            debug_logger.warning(f"  - 测试项: '{asset_test_name}', 软件类别: '{asset_software_category}' (需要: '{selected_software_type}')")
                            filtered_shown += 1
            
            # 调试：显示数据库中的测试项名称供参考
            if len(asset_data) > 0:
                logger.debug("数据库中前10个测试项名称供参考:")
                debug_logger.debug("数据库中前10个测试项名称供参考:")
                for i, record in enumerate(asset_data[:10]):
                    db_test_name = record.get('test_item_name', 'N/A')
                    db_software_cat = record.get('software_category', 'N/A')
                    logger.debug(f"   {i+1}. '{db_test_name}' (软件类别: {db_software_cat})")
                    debug_logger.debug(f"   {i+1}. '{db_test_name}' (软件类别: {db_software_cat})")
                    if '||' in str(db_test_name):
                        names = [name.strip() for name in str(db_test_name).split('||')]
                        logger.debug(f"      分解后: {names}")
                        debug_logger.debug(f"      分解后: {names}")
        
        return matched_records
    
    @classmethod
    def _merge_field_content(cls, contents: List[str]) -> str:
        """合并字段内容，用换行符分隔"""
        valid_contents = [str(content).strip() for content in contents if content and str(content).strip()]
        return '\n'.join(valid_contents) if valid_contents else ""
    
    @classmethod
    def _generate_excel_output(cls, workbook) -> bytes:
        """生成处理后的Excel文件"""
        try:
            debug_logger = cls._get_debug_logger()
            debug_logger.info("开始生成最终Excel文件...")
            
            output = io.BytesIO()
            # 保存工作簿到内存流
            workbook.save(output)
            output.seek(0)
            content = output.getvalue()
            
            debug_logger.info("=" * 60)
            debug_logger.info("=== 智能导出完成 ===")
            debug_logger.info(f"结果文件大小: {len(content)} bytes")
            debug_logger.info("=" * 60)
            
            logger.info(f"成功生成Excel文件，大小: {len(content)} bytes")
            return content
            
        except Exception as e:
            debug_logger = cls._get_debug_logger()
            debug_logger.error(f"生成Excel文件失败: {str(e)}")
            logger.error(f"Failed to generate Excel file: {str(e)}")
            raise ValueError(f"Excel generation failed: {str(e)}") 