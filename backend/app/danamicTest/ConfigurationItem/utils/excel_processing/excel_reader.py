
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

"""
Excel文件读取工具模块
使用openpyxl替代pandas，避免杀毒软件误报问题
"""
import openpyxl
from typing import List, Dict, Any, Tuple


def read_excel_columns(excel_file_path: str, columns: List[int] = None) -> List[List[Any]]:
    """
    读取Excel文件的指定列
    
    Args:
        excel_file_path: Excel文件路径
        columns: 要读取的列索引列表（从0开始），如果为None则读取所有列
        
    Returns:
        列表的列表，每个子列表代表一列数据
    """
    try:
        workbook = openpyxl.load_workbook(excel_file_path)
        worksheet = workbook.active
        
        # 获取数据范围
        max_row = worksheet.max_row
        max_col = worksheet.max_column
        
        if columns is None:
            columns = list(range(max_col))
        
        result = []
        for col_idx in columns:
            if col_idx >= max_col:
                continue
                
            column_data = []
            for row in range(1, max_row + 1):
                cell_value = worksheet.cell(row=row, column=col_idx + 1).value
                column_data.append(cell_value)
            result.append(column_data)
        
        workbook.close()
        return result
        
    except Exception as e:
        log_info(f"读取Excel时发生错误：{e}", Path(__file__).stem)
        return []


def read_excel_columns1(excel_file_path: str) -> Tuple[List[Any], List[Any]]:
    """
    读取Excel文件的第一列和第二列数据
    兼容原pandas版本的函数
    
    Args:
        excel_file_path: Excel文件路径
        
    Returns:
        (第一列数据, 第二列数据)
    """
    try:
        columns = read_excel_columns(excel_file_path, [0, 1])
        if len(columns) >= 2:
            return columns[0], columns[1]
        elif len(columns) == 1:
            return columns[0], []
        else:
            return [], []
    except Exception as e:
        log_info(f"读取Excel时发生错误：{e}", Path(__file__).stem)
        return ['0'], ['0']


def xinghaoxinxi_excel_to_dict(file_path: str) -> Dict[str, List[Any]]:
    """
    将Excel表格中的第1列作为键，将后面的17列作为值，形成一个字典
    兼容原pandas版本的函数
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        字典，键为第一列的值，值为后续列的数据列表
    """
    try:
        workbook = openpyxl.load_workbook(file_path)
        worksheet = workbook.active
        
        data_dict = {}
        max_row = worksheet.max_row
        
        # 读取前19列数据
        for row in range(1, max_row + 1):
            # 第一列作为键
            key = worksheet.cell(row=row, column=1).value
            if key is None:
                continue
                
            # 后面18列作为值
            values = []
            for col in range(2, min(20, worksheet.max_column + 1)):
                cell_value = worksheet.cell(row=row, column=col).value
                values.append(cell_value)
            
            data_dict[key] = values
        
        workbook.close()
        return data_dict
        
    except Exception as e:
        log_info(f"读取Excel时发生错误：{e}", Path(__file__).stem)
        return {}


def read_excel_to_dataframe_like(excel_file_path: str, usecols: range = None) -> Dict[str, List[Any]]:
    """
    读取Excel文件并返回类似DataFrame的字典结构
    
    Args:
        excel_file_path: Excel文件路径
        usecols: 要读取的列范围
        
    Returns:
        字典，键为列名，值为列数据
    """
    try:
        workbook = openpyxl.load_workbook(excel_file_path)
        worksheet = workbook.active
        
        # 获取列名（第一行）
        max_row = worksheet.max_row
        max_col = worksheet.max_column
        
        if usecols is not None:
            max_col = min(max_col, max(usecols) + 1)
            start_col = min(usecols) + 1
        else:
            start_col = 1
            usecols = range(max_col)
        
        # 读取列名
        column_names = []
        for col in range(start_col, max_col + 1):
            header = worksheet.cell(row=1, column=col).value
            column_names.append(header if header is not None else f"Column_{col}")
        
        # 读取数据
        data_dict = {}
        for i, col in enumerate(range(start_col, max_col + 1)):
            column_data = []
            for row in range(2, max_row + 1):  # 从第二行开始（跳过标题行）
                cell_value = worksheet.cell(row=row, column=col).value
                column_data.append(cell_value)
            data_dict[column_names[i]] = column_data
        
        workbook.close()
        return data_dict
        
    except Exception as e:
        log_info(f"读取Excel时发生错误：{e}", Path(__file__).stem)
        return {}


class ExcelDataFrame:
    """
    简化的DataFrame类，提供基本的pandas兼容接口
    """
    
    def __init__(self, data_dict: Dict[str, List[Any]]):
        self.data = data_dict
        self.columns = list(data_dict.keys()) if data_dict else []
        self.shape = (len(next(iter(data_dict.values()))) if data_dict else 0, len(self.columns))
    
    def iloc(self, row_slice, col_slice):
        """模拟pandas的iloc功能"""
        if isinstance(col_slice, int):
            col_name = self.columns[col_slice]
            return self.data[col_name]
        elif isinstance(col_slice, slice):
            selected_cols = self.columns[col_slice]
            result = {}
            for col in selected_cols:
                result[col] = self.data[col]
            return ExcelDataFrame(result)
        else:
            raise ValueError("不支持的列选择方式")
    
    def tolist(self):
        """转换为列表"""
        if len(self.columns) == 1:
            return self.data[self.columns[0]]
        else:
            return [self.data[col] for col in self.columns]


def read_excel(file_path: str, usecols: range = None) -> ExcelDataFrame:
    """
    pandas.read_excel的替代函数
    
    Args:
        file_path: Excel文件路径
        usecols: 要读取的列范围
        
    Returns:
        ExcelDataFrame对象
    """
    data_dict = read_excel_to_dataframe_like(file_path, usecols)
    return ExcelDataFrame(data_dict)


def read_excel_columns_to_array(file_path: str) -> List[List[Any]]:
    """
    读取Excel文件的第1列到第7列，返回二维数组
    兼容原pandas版本的函数
    
    Args:
        file_path: Excel文件路径
        
    Returns:
        二维数组（列表的列表）
    """
    try:
        workbook = openpyxl.load_workbook(file_path)
        worksheet = workbook.active
        
        max_row = worksheet.max_row
        max_col = min(worksheet.max_column, 7)  # 最多读取7列 (A:G)
        
        data_array = []
        for row in range(1, max_row + 1):
            row_data = []
            for col in range(1, max_col + 1):
                cell_value = worksheet.cell(row=row, column=col).value
                row_data.append(cell_value)
            data_array.append(row_data)
        
        workbook.close()
        return data_array
        
    except Exception as e:
        log_info(f"读取Excel时发生错误：{e}", Path(__file__).stem)
        return []


def read_excel_specific_rows_to_arrays(file_path: str, rows_to_read: List[int]) -> List[List[Any]]:
    """
    读取Excel文件中指定行和前12个列的内容，并以每一行为单位形成数组列表
    兼容原pandas版本的函数
    
    Args:
        file_path: Excel文件路径
        rows_to_read: 要读取的行的索引列表（从0开始）
        
    Returns:
        每个数组包含指定行中前12列的值
    """
    try:
        workbook = openpyxl.load_workbook(file_path)
        worksheet = workbook.active
        
        max_col = min(worksheet.max_column, 12)  # 最多读取12列 (A:L)
        
        rows_as_arrays = []
        for row_index in rows_to_read:
            # 转换为1基索引
            actual_row = row_index + 1
            if actual_row <= worksheet.max_row:
                row_data = []
                for col in range(1, max_col + 1):
                    cell_value = worksheet.cell(row=actual_row, column=col).value
                    row_data.append(cell_value)
                rows_as_arrays.append(row_data)
        
        workbook.close()
        return rows_as_arrays
        
    except Exception as e:
        log_info(f"读取Excel时发生错误：{e}", Path(__file__).stem)
        return []


def read_excel_with_sheet(file_path: str, sheet_name: str = None) -> 'SimpleDataFrame':
    """
    读取Excel文件的指定工作表
    
    Args:
        file_path: Excel文件路径
        sheet_name: 工作表名称，如果为None则读取活动工作表
        
    Returns:
        SimpleDataFrame对象
    """
    try:
        workbook = openpyxl.load_workbook(file_path)
        
        if sheet_name:
            worksheet = workbook[sheet_name]
        else:
            worksheet = workbook.active
            
        # 读取所有数据
        data = []
        for row in worksheet.iter_rows(values_only=True):
            data.append(list(row))
        
        workbook.close()
        return SimpleDataFrame(data)
        
    except Exception as e:
        log_info(f"读取Excel时发生错误：{e}", Path(__file__).stem)
        return SimpleDataFrame([])


class SimpleDataFrame:
    """
    简化的DataFrame类，支持基本的pandas操作
    """
    
    def __init__(self, data: List[List[Any]]):
        self.data = data if data else []
        self.shape = (len(self.data), len(self.data[0]) if self.data else 0)
        self._iloc = SimpleDataFrameIloc(self)
    
    @property
    def iloc(self):
        """模拟pandas的iloc属性"""
        return self._iloc
    
    def reset_index(self, drop=True):
        """重置索引"""
        return self
    
    def tolist(self):
        """转换为列表"""
        if self.shape[1] == 1:
            return [row[0] for row in self.data]
        else:
            return self.data
    
    def to_excel(self, file_path: str, index: bool = False, columns: List[str] = None):
        """保存到Excel文件"""
        try:
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            
            # 如果指定了列名，写入标题行
            if columns:
                for col_idx, col_name in enumerate(columns, 1):
                    worksheet.cell(row=1, column=col_idx, value=col_name)
                start_row = 2
            else:
                start_row = 1
            
            # 写入数据
            for row_idx, row_data in enumerate(self.data, start_row):
                if columns:
                    # 只写入指定的列
                    for col_idx, col_name in enumerate(columns, 1):
                        if col_idx - 1 < len(row_data):
                            worksheet.cell(row=row_idx, column=col_idx, value=row_data[col_idx - 1])
                else:
                    # 写入所有数据
                    for col_idx, cell_value in enumerate(row_data, 1):
                        worksheet.cell(row=row_idx, column=col_idx, value=cell_value)
            
            workbook.save(file_path)
            
        except Exception as e:
            log_info(f"保存Excel文件时发生错误：{e}", Path(__file__).stem)
    
    @property
    def columns(self):
        """获取列名（模拟）"""
        if self.data and len(self.data) > 0:
            return [f"Column_{i}" for i in range(len(self.data[0]))]
        return []


class SimpleDataFrameColumn:
    """
    简化的DataFrame列类
    """
    
    def __init__(self, data: List[Any]):
        self.data = data
    
    def __getitem__(self, index):
        """支持索引访问"""
        return self.data[index]
    
    def __len__(self):
        """支持len()函数"""
        return len(self.data)
    
    def reset_index(self, drop=True):
        """重置索引"""
        return self
    
    def tolist(self):
        """转换为列表"""
        return self.data


def create_dataframe(data: List[List[Any]]) -> SimpleDataFrame:
    """
    创建SimpleDataFrame，替代pd.DataFrame
    
    Args:
        data: 二维数据列表
        
    Returns:
        SimpleDataFrame对象
    """
    return SimpleDataFrame(data)


def concat_dataframes(dataframes: List[SimpleDataFrame], ignore_index: bool = True) -> SimpleDataFrame:
    """
    合并多个DataFrame，替代pd.concat
    
    Args:
        dataframes: DataFrame列表
        ignore_index: 是否忽略索引
        
    Returns:
        合并后的SimpleDataFrame
    """
    if not dataframes:
        return SimpleDataFrame([])
    
    combined_data = []
    for df in dataframes:
        combined_data.extend(df.data)
    
    return SimpleDataFrame(combined_data) 


class SimpleDataFrameIloc:
    """
    简化的DataFrame iloc访问器
    """
    
    def __init__(self, dataframe):
        self.df = dataframe
    
    def __getitem__(self, key):
        """支持iloc[row_slice, col_slice]语法"""
        if isinstance(key, tuple) and len(key) == 2:
            row_slice, col_slice = key
            
            # 处理行切片
            if isinstance(row_slice, slice):
                row_data = self.df.data[row_slice]
            elif isinstance(row_slice, int):
                if 0 <= row_slice < len(self.df.data):
                    row_data = [self.df.data[row_slice]]
                else:
                    return None
            else:
                return None
            
            # 处理列切片
            if isinstance(col_slice, int):
                result = []
                for row in row_data:
                    if 0 <= col_slice < len(row):
                        result.append(row[col_slice])
                return SimpleDataFrameColumn(result)
            elif isinstance(col_slice, slice):
                result = []
                for row in row_data:
                    result.append(row[col_slice])
                return SimpleDataFrame(result)
            else:
                return SimpleDataFrame(row_data)
        
        elif isinstance(key, (int, slice)):
            # 只有行索引
            if isinstance(key, int):
                if 0 <= key < len(self.df.data):
                    return self.df.data[key]
                return None
            else:  # slice
                return SimpleDataFrame(self.df.data[key])
        
        return None 