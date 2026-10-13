"""
调试工具：分析Excel文件中的测试项数据
用于诊断智能导出功能的匹配问题
"""
import io
import logging
from typing import List, Dict, Any
from openpyxl import load_workbook

logger = logging.getLogger(__name__)

def debug_excel_test_items(file_content: bytes, sheet_index: int = 9, test_item_col: int = 7):
    """
    调试Excel文件中的测试项数据
    
    Args:
        file_content: Excel文件内容
        sheet_index: 工作表索引（测试用例表默认为9）
        test_item_col: 测试项名称列号
    """
    try:
        # 加载Excel文件
        file_stream = io.BytesIO(file_content)
        workbook = load_workbook(file_stream, data_only=True)
        
        print(f"🔍 Excel文件信息:")
        print(f"   工作表数量: {len(workbook.sheetnames)}")
        print(f"   工作表名称: {workbook.sheetnames}")
        
        if len(workbook.sheetnames) <= sheet_index:
            print(f"❌ 工作表索引 {sheet_index} 超出范围")
            return
        
        # 获取目标工作表
        target_sheet_name = workbook.sheetnames[sheet_index]
        worksheet = workbook[target_sheet_name]
        
        print(f"\n📋 分析工作表: '{target_sheet_name}' (索引 {sheet_index})")
        print(f"   最大行数: {worksheet.max_row}")
        print(f"   最大列数: {worksheet.max_column}")
        
        # 分析表头
        print(f"\n📝 表头信息 (第1行):")
        for col in range(1, min(worksheet.max_column + 1, 20)):  # 最多显示20列
            cell_value = worksheet.cell(row=1, column=col).value
            print(f"   列{col}: '{cell_value}'")
        
        # 分析测试项数据
        print(f"\n🎯 测试项数据分析 (列{test_item_col}):")
        test_items_found = []
        
        for row_idx in range(2, min(worksheet.max_row + 1, 50)):  # 最多显示50行数据
            test_item_cell = worksheet.cell(row=row_idx, column=test_item_col)
            test_item_value = test_item_cell.value
            test_item_name = str(test_item_value).strip() if test_item_value else ""
            
            if test_item_name:
                test_items_found.append({
                    'row': row_idx,
                    'raw_value': test_item_value,
                    'processed_value': test_item_name
                })
                print(f"   行{row_idx}: 原始值='{test_item_value}' | 处理后='{test_item_name}'")
        
        # 统计测试项
        unique_test_items = {}
        for item in test_items_found:
            name = item['processed_value']
            if name not in unique_test_items:
                unique_test_items[name] = []
            unique_test_items[name].append(item['row'])
        
        print(f"\n📊 测试项统计:")
        print(f"   共找到 {len(test_items_found)} 个测试项记录")
        print(f"   去重后有 {len(unique_test_items)} 个不同的测试项:")
        
        for test_item_name, rows in unique_test_items.items():
            print(f"   '{test_item_name}': 出现在行 {rows}")
            
        return {
            'total_sheets': len(workbook.sheetnames),
            'sheet_names': workbook.sheetnames,
            'target_sheet': target_sheet_name,
            'max_row': worksheet.max_row,
            'max_column': worksheet.max_column,
            'test_items': unique_test_items,
            'test_item_records': test_items_found
        }
        
    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")
        logger.error(f"Debug Excel failed: {str(e)}")
        return None

def debug_database_test_items(asset_data: List[Dict]):
    """
    调试数据库中的测试项数据
    
    Args:
        asset_data: 数据库中的资产数据
    """
    print(f"\n🏢 数据库测试项调试:")
    print(f"   总记录数: {len(asset_data)}")
    
    test_item_names = []
    for record in asset_data:
        test_item_name = record.get('test_item_name', '')
        if test_item_name:
            # 处理 || 分隔的名称
            names = [name.strip() for name in str(test_item_name).split('||')]
            test_item_names.extend(names)
            
            print(f"   记录: '{test_item_name}' -> 分解后: {names}")
    
    unique_names = list(set(test_item_names))
    unique_names.sort()
    
    print(f"\n📋 数据库中的测试项名称 (共{len(unique_names)}个):")
    for name in unique_names:
        print(f"   '{name}'")
        
    return {
        'total_records': len(asset_data),
        'unique_test_items': unique_names,
        'test_item_count': len(unique_names)
    } 