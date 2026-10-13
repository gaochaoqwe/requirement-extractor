"""
FPGA代码解析器

专门用于解析Verilog HDL和VHDL代码文件
由于FPGA代码不需要按函数分解，这里实现文件级别的解析
"""
import os
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

def log_debug(msg):
    """调试日志记录"""
    try:
        # Path is relative to this file's location (.../parser/fpga)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate 7 levels up from 'fpga' to 'backend'
        backend_dir = os.path.abspath(os.path.join(base_dir, '..', '..', '..', '..', '..', '..', '..'))
        log_dir = os.path.join(backend_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'bg_debug.txt')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("[fpga_parser] " + msg + "\n")
    except Exception:
        # Suppress logging errors if path resolution or writing fails
        pass

# 使用chardet进行编码检测
try:
    import chardet
    _CHARDET_AVAILABLE = True
except ImportError:
    _CHARDET_AVAILABLE = False

def read_file_with_encoding(filepath: str) -> Tuple[str, str]:
    """
    自动识别文件编码并读取内容
    返回: (文件内容, 编码格式)
    """
    if not _CHARDET_AVAILABLE:
        # 如果没有chardet，尝试常见编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                return content, encoding
            except UnicodeDecodeError:
                continue
        # 如果都失败，使用utf-8并忽略错误
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content, 'utf-8'
    
    # 使用chardet检测编码
    with open(filepath, 'rb') as f:
        raw = f.read()
    result = chardet.detect(raw)
    encoding = result['encoding'] or 'utf-8'
    try:
        return raw.decode(encoding), encoding
    except Exception:
        return raw.decode('utf-8', errors='ignore'), 'utf-8'

def detect_fpga_language(filepath: str, content: str) -> str:
    """
    检测FPGA代码语言类型
    返回: 'verilog' 或 'vhdl'
    """
    ext = Path(filepath).suffix.lower()
    
    # 根据文件扩展名判断
    if ext in ['.v', '.sv']:
        return 'verilog'
    elif ext in ['.vhd', '.vhdl']:
        return 'vhdl'
    
    # 如果扩展名不明确，根据内容特征判断
    content_lower = content.lower()
    
    # VHDL特征关键词
    vhdl_keywords = ['entity', 'architecture', 'library', 'use', 'port map', 'signal']
    # Verilog特征关键词
    verilog_keywords = ['module', 'endmodule', 'always', 'wire', 'reg', 'assign']
    
    vhdl_score = sum(1 for keyword in vhdl_keywords if keyword in content_lower)
    verilog_score = sum(1 for keyword in verilog_keywords if keyword in content_lower)
    
    return 'vhdl' if vhdl_score > verilog_score else 'verilog'

def extract_fpga_module_info(content: str, language: str) -> Dict:
    """
    提取FPGA模块的基本信息
    """
    module_info = {
        'modules': [],
        'entities': [],
        'language': language
    }
    
    if language == 'verilog':
        # 提取Verilog模块信息
        module_pattern = r'module\s+(\w+)\s*(?:\(.*?\))?\s*;'
        matches = re.finditer(module_pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            module_info['modules'].append(match.group(1))
    
    elif language == 'vhdl':
        # 提取VHDL实体信息
        entity_pattern = r'entity\s+(\w+)\s+is'
        matches = re.finditer(entity_pattern, content, re.IGNORECASE)
        for match in matches:
            module_info['entities'].append(match.group(1))
    
    return module_info

def extract_fpga_files_from_code(content: str, filepath: str) -> List[Dict]:
    """
    从FPGA代码中提取文件信息
    
    Args:
        content: 文件内容
        filepath: 文件路径
        
    Returns:
        包含文件信息的字典列表，每个文件作为一个"函数"单元处理
    """
    log_debug(f"extract_fpga_files_from_code called, filepath={filepath}, content_len={len(content)}")
    
    # 检测语言类型
    language = detect_fpga_language(filepath, content)
    log_debug(f"检测到FPGA语言类型: {language}")
    
    # 提取模块信息
    module_info = extract_fpga_module_info(content, language)
    log_debug(f"提取到模块信息: {module_info}")
    
    # 获取文件名（不含路径）
    filename = Path(filepath).name
    
    # 生成模块名称用于显示
    if language == 'verilog' and module_info['modules']:
        display_name = f"{filename} (modules: {', '.join(module_info['modules'])})"
    elif language == 'vhdl' and module_info['entities']:
        display_name = f"{filename} (entities: {', '.join(module_info['entities'])})"
    else:
        display_name = filename
    
    # 计算行数
    lines = content.split('\n')
    line_count = len(lines)
    
    # 返回文件级别的"函数"信息
    file_info = {
        'function_name': display_name,
        'source_code': content,
        'start_line': 1,
        'end_line': line_count,
        'language': language,
        'module_info': module_info,
        'file_path': filepath
    }
    
    log_debug(f"FPGA文件解析完成: {display_name}, 行数: {line_count}")
    return [file_info]

def get_fpga_file_summary(filepath: str) -> Optional[Dict]:
    """
    获取FPGA文件的摘要信息
    """
    try:
        content, encoding = read_file_with_encoding(filepath)
        language = detect_fpga_language(filepath, content)
        module_info = extract_fpga_module_info(content, language)
        
        return {
            'filepath': filepath,
            'language': language,
            'encoding': encoding,
            'line_count': len(content.split('\n')),
            'module_info': module_info
        }
    except Exception as e:
        log_debug(f"获取FPGA文件摘要失败: {filepath}, 错误: {e}")
        return None 