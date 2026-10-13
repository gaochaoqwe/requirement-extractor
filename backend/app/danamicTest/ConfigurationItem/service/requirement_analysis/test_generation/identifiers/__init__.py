"""
测试标识符生成模块
"""

from .test_identifier_generator import (
    check_word_document_xuqiushuoming1,
    extract_software_name1,
    read_excel_columns,
    read_excel_columns_three,
    read_xuqiu_wendang_biaoshihao,
    ceshibiaoshi_duqu
)

# 为向后兼容，创建一个包装类
class TestIdentifierGenerator:
    """测试标识符生成器（向后兼容包装）"""
    @staticmethod
    def check_word_document(folder_path):
        return check_word_document_xuqiushuoming1(folder_path)
    
    @staticmethod
    def extract_software_name(file_path):
        return extract_software_name1(file_path)
    
    @staticmethod
    def read_excel_columns(excel_file_path):
        return read_excel_columns(excel_file_path)

__all__ = [
    'TestIdentifierGenerator',
    'check_word_document_xuqiushuoming1',
    'extract_software_name1', 
    'read_excel_columns',
    'read_excel_columns_three',
    'read_xuqiu_wendang_biaoshihao',
    'ceshibiaoshi_duqu'
] 