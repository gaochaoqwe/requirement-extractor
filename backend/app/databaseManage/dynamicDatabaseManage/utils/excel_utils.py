from openpyxl import load_workbook, Workbook
from typing import List, Dict, Any, Tuple
import sys
import os
import logging
import io

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.app.databaseManage.dynamicDatabaseManage.schemas import schemas
except ImportError:
    try:
        from ..schemas import schemas
    except ImportError:
        try:
            import schemas
        except ImportError:
            print("警告: 无法导入schemas模块")
            schemas = None

logger = logging.getLogger(__name__)

# 软件类别排序映射
CATEGORY_ORDER_MAP = {
    # 旧映射（保留兼容）
    "通用": 1,
    "随动": 2,
    "图像": 3,
    "红外": 4,
    "激光": 5,
    "分色滤光": 6,
    "手柄": 7,
}

# 新排序映射（含“/主控”变体；若命中则优先生效）
CATEGORY_ORDER_MAP_EXT = {
    "通用": 1,
    "主控": 2,
    "随动/主控": 3,
    "图像/主控": 4,
    "红外/主控": 5,
    "激光/主控": 6,
    "手柄": 7,
    "分色滤光": 8,
    "分色虑光": 8,  # 兼容可能的误写
}

def get_category_order(category: str) -> int:
    """返回类别排序值。优先使用新映射，其次旧映射，默认999。"""
    if category in CATEGORY_ORDER_MAP_EXT:
        return CATEGORY_ORDER_MAP_EXT[category]
    return CATEGORY_ORDER_MAP.get(category, 999)


def parse_excel_file(file_content: bytes, sheet_name: str = None) -> List[schemas.OptoelectronicRequirementCreate]:
    """
    解析Excel文件并转换为需求记录列表
    
    Args:
        file_content: Excel文件的字节内容
        sheet_name: 工作表名称，如果为None则使用第一个工作表
    
    Returns:
        需求记录列表
    
    Raises:
        ValueError: 当文件格式不正确或缺少必要列时
    """
    try:
        # 读取Excel文件
        file_stream = io.BytesIO(file_content)
        workbook = load_workbook(file_stream, data_only=True)
        
        # 如果没有指定工作表名称，使用第一个工作表
        if sheet_name is None:
            worksheet = workbook.active
        else:
            if sheet_name not in workbook.sheetnames:
                raise ValueError(f"找不到工作表: {sheet_name}")
            worksheet = workbook[sheet_name]
        
        # 获取表头行
        header_row = 1
        headers = {}
        for col in range(1, worksheet.max_column + 1):
            cell_value = worksheet.cell(row=header_row, column=col).value
            if cell_value:
                headers[str(cell_value).strip()] = col
        
        # 检查必要的列是否存在
        required_columns = ["软件类别", "测试项名称", "测试内容", "测试方法"]
        missing_columns = [col for col in required_columns if col not in headers]
        
        if missing_columns:
            raise ValueError(f"Excel文件缺少必要的列: {missing_columns}")
        
        # 解析数据行
        requirements = []
        for row in range(header_row + 1, worksheet.max_row + 1):
            # 检查必填字段是否为空
            software_category_val = worksheet.cell(row=row, column=headers["软件类别"]).value
            test_item_name_val = worksheet.cell(row=row, column=headers["测试项名称"]).value
            
            if not software_category_val or not test_item_name_val:
                continue  # 跳过空行
            
            try:
                # 获取其他字段
                test_content_val = worksheet.cell(row=row, column=headers["测试内容"]).value
                test_method_val = worksheet.cell(row=row, column=headers["测试方法"]).value
                
                requirement = schemas.OptoelectronicRequirementCreate(
                    software_category=str(software_category_val).strip(),
                    test_item_name=str(test_item_name_val).strip(),
                    test_item_description=str(test_content_val).strip() if test_content_val else None,
                    test_method=str(test_method_val).strip() if test_method_val else None
                )
                requirements.append(requirement)
            except Exception as e:
                logger.warning(f"跳过第{row}行无效数据, 错误: {str(e)}")
                continue
        
        if not requirements:
            raise ValueError("Excel文件中没有有效的数据行")
        
        return requirements
        
    except Exception as e:
        logger.error(f"解析Excel文件失败: {str(e)}")
        raise ValueError(f"解析Excel文件失败: {str(e)}")


def parse_excel_for_normal_import(
    file_content: bytes, 
    sheet_name: str = None
) -> List[Dict[str, Any]]:
    """
    解析Excel文件用于普通导入，返回带行号的数据
    
    Args:
        file_content: Excel文件的字节内容
        sheet_name: 工作表名称，如果为None则使用第一个工作表
    
    Returns:
        包含行号的数据列表
    
    Raises:
        ValueError: 当文件格式不正确或缺少必要列时
    """
    try:
        # 读取Excel文件
        file_stream = io.BytesIO(file_content)
        workbook = load_workbook(file_stream, data_only=True)
        
        # 如果没有指定工作表名称，使用第一个工作表
        if sheet_name is None:
            worksheet = workbook.active
        else:
            if sheet_name not in workbook.sheetnames:
                raise ValueError(f"找不到工作表: {sheet_name}")
            worksheet = workbook[sheet_name]
        
        # 获取表头行
        header_row = 1
        headers = {}
        for col in range(1, worksheet.max_column + 1):
            cell_value = worksheet.cell(row=header_row, column=col).value
            if cell_value:
                headers[str(cell_value).strip()] = col
        
        # 检查必要的列是否存在
        required_columns = ["软件类别", "测试项名称", "测试内容", "测试方法"]
        missing_columns = [col for col in required_columns if col not in headers]
        
        if missing_columns:
            raise ValueError(f"Excel文件缺少必要的列: {missing_columns}")
        
        # 解析数据行
        data_list = []
        for row in range(header_row + 1, worksheet.max_row + 1):
            # 检查必填字段是否为空
            software_category_val = worksheet.cell(row=row, column=headers["软件类别"]).value
            test_item_name_val = worksheet.cell(row=row, column=headers["测试项名称"]).value
            
            if not software_category_val or not test_item_name_val:
                continue  # 跳过空行
            
            try:
                # 获取其他字段
                test_content_val = worksheet.cell(row=row, column=headers["测试内容"]).value
                test_method_val = worksheet.cell(row=row, column=headers["测试方法"]).value
                
                data_dict = {
                    "row_number": row,
                    "software_category": str(software_category_val).strip(),
                    "test_item_name": str(test_item_name_val).strip(),
                    "test_item_description": str(test_content_val).strip() if test_content_val else "",
                    "test_method": str(test_method_val).strip() if test_method_val else ""
                }
                data_list.append(data_dict)
            except Exception as e:
                logger.warning(f"跳过第{row}行无效数据, 错误: {str(e)}")
                continue
        
        if not data_list:
            raise ValueError("Excel文件中没有有效的数据行")
        
        return data_list
        
    except Exception as e:
        logger.error(f"解析Excel文件失败: {str(e)}")
        raise ValueError(f"解析Excel文件失败: {str(e)}")


def validate_excel_structure(file_content: bytes, sheet_name: str = None) -> dict:
    """
    验证Excel文件结构
    
    Args:
        file_content: Excel文件的字节内容
        sheet_name: 工作表名称，如果为None则使用第一个工作表
    
    Returns:
        验证结果字典
    """
    try:
        # 读取Excel文件
        file_stream = io.BytesIO(file_content)
        workbook = load_workbook(file_stream, data_only=True)
        
        # 如果没有指定工作表名称，使用第一个工作表
        if sheet_name is None:
            worksheet = workbook.active
            sheet_name = worksheet.title
        else:
            if sheet_name not in workbook.sheetnames:
                return {
                    "valid": False,
                    "message": f"找不到工作表: {sheet_name}",
                    "available_sheets": workbook.sheetnames
                }
            worksheet = workbook[sheet_name]
        
        # 获取表头行
        header_row = 1
        headers = {}
        for col in range(1, worksheet.max_column + 1):
            cell_value = worksheet.cell(row=header_row, column=col).value
            if cell_value:
                headers[str(cell_value).strip()] = col
        
        # 检查必要的列是否存在
        required_columns = ["软件类别", "测试项名称", "测试内容", "测试方法"]
        missing_columns = [col for col in required_columns if col not in headers]
        
        if missing_columns:
            return {
                "valid": False,
                "message": f"Excel文件缺少必要的列: {missing_columns}",
                "found_headers": list(headers.keys()),
                "required_headers": required_columns,
                "sheet_name": sheet_name
            }
        
        # 统计数据行数
        data_rows = 0
        for row in range(header_row + 1, worksheet.max_row + 1):
            software_category_val = worksheet.cell(row=row, column=headers["软件类别"]).value
            test_item_name_val = worksheet.cell(row=row, column=headers["测试项名称"]).value
            
            if software_category_val and test_item_name_val:
                data_rows += 1
        
        return {
            "valid": True,
            "message": "Excel文件结构验证通过",
            "sheet_name": sheet_name,
            "found_headers": list(headers.keys()),
            "data_rows": data_rows
        }
        
    except Exception as e:
        logger.error(f"验证Excel文件结构失败: {str(e)}")
        return {
            "valid": False,
            "message": f"验证Excel文件结构失败: {str(e)}"
        }


def export_to_excel(requirements: List[schemas.OptoelectronicRequirement]) -> bytes:
    """
    将需求记录导出为Excel文件
    
    Args:
        requirements: 需求记录列表
    
    Returns:
        Excel文件的字节内容
    """
    # 创建工作簿
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "光电需求分析表"
    
    # 设置表头
    headers = ["软件类别", "测试项名称", "测试内容", "测试方法"]
    for col, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col, value=header)
    
    # 按软件类别排序
    sorted_requirements = sorted(requirements, key=lambda x: (x.category_order, x.item_order))
    
    # 写入数据
    for row, req in enumerate(sorted_requirements, 2):
        worksheet.cell(row=row, column=1, value=req.software_category)
        worksheet.cell(row=row, column=2, value=req.test_item_name)
        worksheet.cell(row=row, column=3, value=req.test_item_description or "")
        worksheet.cell(row=row, column=4, value=req.test_method or "")
    
    # 调整列宽
    column_widths = [15, 25, 40, 40]
    for col, width in enumerate(column_widths, 1):
        worksheet.column_dimensions[worksheet.cell(row=1, column=col).column_letter].width = width
    
    # 保存到字节流
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output.getvalue() 


# ================= 新增：多工作表（7列）解析 =================

SEVEN_HEADERS = [
    "软件类别",
    "测试项名称",
    "测试内容",
    "测试方法",
    "用例模板（用例名称）",
    "用例模板（输入条件）",
    "用例模板（预期结果）",
    "提交人",
]


def export_sevencols_to_excel(records: List[object], sheet_title: str = None) -> bytes:
    """将七列表记录导出为Excel（单Sheet）。records 为 ORM 实例列表。"""
    workbook = Workbook()
    ws = workbook.active
    ws.title = sheet_title or "七列需求表"

    # 表头
    for col, header in enumerate(SEVEN_HEADERS, 1):
        ws.cell(row=1, column=col, value=header)

    # 排序：类别序 + 行序
    sorted_records = sorted(records, key=lambda r: (getattr(r, "category_order", 999), getattr(r, "item_order", 0)))

    # 数据
    for idx, r in enumerate(sorted_records, start=2):
        ws.cell(row=idx, column=1, value=getattr(r, "software_category", None))
        ws.cell(row=idx, column=2, value=getattr(r, "test_item_name", None))
        ws.cell(row=idx, column=3, value=getattr(r, "test_content", None) or "")
        ws.cell(row=idx, column=4, value=getattr(r, "test_method", None) or "")
        ws.cell(row=idx, column=5, value=getattr(r, "case_template_name", None) or "")
        ws.cell(row=idx, column=6, value=getattr(r, "case_template_input", None) or "")
        ws.cell(row=idx, column=7, value=getattr(r, "case_template_expected", None) or "")
        ws.cell(row=idx, column=8, value=getattr(r, "submitter", None) or "")

    # 列宽（大致）
    widths = [15, 22, 40, 40, 30, 35, 35, 14]
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = w

    buf = io.BytesIO()
    workbook.save(buf)
    buf.seek(0)
    return buf.getvalue()

def parse_multisheet_requirements(file_content: bytes) -> Dict[str, List[Dict[str, Any]]]:
    """
    解析含多个工作表的Excel，要求每个Sheet都具备8列表头（中文）。
    返回：{ sheet_name: [ {software_category, test_item_name, test_content, test_method, case_template_name, case_template_input, case_template_expected, submitter} ] }
    """
    try:
        file_stream = io.BytesIO(file_content)
        workbook = load_workbook(file_stream, data_only=True)

        result: Dict[str, List[Dict[str, Any]]] = {}
        for sheet_name in workbook.sheetnames:
            ws = workbook[sheet_name]

            # 读取表头
            header_row = 1
            headers: Dict[str, int] = {}
            for col in range(1, ws.max_column + 1):
                cell_value = ws.cell(row=header_row, column=col).value
                if cell_value:
                    headers[str(cell_value).strip()] = col

            missing = [h for h in SEVEN_HEADERS if h not in headers]
            if missing:
                logger.warning(f"工作表'{sheet_name}'缺少列: {missing}，跳过该Sheet")
                continue

            rows: List[Dict[str, Any]] = []
            for row in range(header_row + 1, ws.max_row + 1):
                sc = ws.cell(row=row, column=headers["软件类别"]).value
                name = ws.cell(row=row, column=headers["测试项名称"]).value
                if not sc or not name:
                    continue

                # 🚀 优化1: 保持Excel中的原始行号，确保排序一致性
                rows.append({
                    "software_category": str(sc).strip(),
                    "test_item_name": str(name).strip(),
                    "test_content": (str(ws.cell(row=row, column=headers["测试内容"]).value).strip() if ws.cell(row=row, column=headers["测试内容"]).value else None),
                    "test_method": (str(ws.cell(row=row, column=headers["测试方法"]).value).strip() if ws.cell(row=row, column=headers["测试方法"]).value else None),
                    "case_template_name": (str(ws.cell(row=row, column=headers["用例模板（用例名称）"]).value).strip() if ws.cell(row=row, column=headers["用例模板（用例名称）"]).value else None),
                    "case_template_input": (str(ws.cell(row=row, column=headers["用例模板（输入条件）"]).value).strip() if ws.cell(row=row, column=headers["用例模板（输入条件）"]).value else None),
                    "case_template_expected": (str(ws.cell(row=row, column=headers["用例模板（预期结果）"]).value).strip() if ws.cell(row=row, column=headers["用例模板（预期结果）"]).value else None),
                    "submitter": (str(ws.cell(row=row, column=headers["提交人"]).value).strip() if ws.cell(row=row, column=headers["提交人"]).value else None),
                    "_excel_row_number": row,  # 保存Excel原始行号
                })

            if rows:
                result[sheet_name] = rows

        if not result:
            raise ValueError("未解析到任何有效的工作表数据（8列表头）")

        return result
    except Exception as e:
        logger.error(f"解析多工作表(8列)失败: {e}")
        raise