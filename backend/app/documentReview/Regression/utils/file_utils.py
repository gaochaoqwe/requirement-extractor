import os
import glob
import logging
import traceback
from pathlib import Path
from fastapi import UploadFile, HTTPException
from docx import Document  # 用于读取Word文档
import docx2txt  # 备用的Word文档处理库

from pathlib import Path
# 修正 BASE_DIR 计算 - 需要上溯到 backend 目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPLOAD_ROOT = os.path.join(BASE_DIR, 'uploads', 'regression')
import sys
sys.stderr.write(f"[DEBUG] file_utils.py - 读取目录: {UPLOAD_ROOT}\n")
os.makedirs(UPLOAD_ROOT, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def save_upload_file(file: UploadFile, file_id: str):
    """保存上传的文件"""
    file_path = os.path.join(UPLOAD_ROOT, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as f_out:
        f_out.write(file.file.read())
    return file_path

def read_word_document(file_path: str) -> str:
    """
    读取Word文档内容（包含段落与表格，表格以Markdown格式输出）
    Args:
        file_path: Word文档路径
    Returns:
        str: 文档内容
    """
    try:
        doc = Document(file_path)
        from docx.text.paragraph import Paragraph
        from docx.table import Table

        def iter_block_items(parent):
            for child in parent.element.body.iterchildren():
                if child.tag.endswith('}p'):
                    yield Paragraph(child, parent)
                elif child.tag.endswith('}tbl'):
                    yield Table(child, parent)

        lines = []
        table_counter = 0

        def table_to_markdown(table, index: int) -> str:
            if not table.rows:
                return ""
            header_cells = [c.text.strip().replace("\n", " ") for c in table.rows[0].cells]
            md_lines = [f"【表 {index}】", f"| {' | '.join(header_cells)} |"]
            md_lines.append(f"| {' | '.join(['---'] * len(header_cells))} |")
            for row in table.rows[1:]:
                row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                md_lines.append(f"| {' | '.join(row_cells)} |")
            return "\n".join(md_lines)

        for block in iter_block_items(doc):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if text:
                    lines.append(text)
            elif isinstance(block, Table):
                table_counter += 1
                md = table_to_markdown(block, table_counter)
                if md:
                    lines.append(md)
        return '\n'.join(lines)
    except Exception as e:
        error_msg = f"读取Word文档失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

def read_uploaded_file(file_id: str) -> str:
    """读取上传的文件内容
    
    Args:
        file_id: 文件ID
        
    Returns:
        str: 文件内容
    """
    debug_log_path = os.path.join(BASE_DIR, 'logs', 'regression_debug.log')
    def debug_log(msg):
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    debug_log(f"[DEBUG] 正在查找文件ID为 {file_id} 的文件")
    # 打印查找模式
    pattern = os.path.join(UPLOAD_ROOT, f"{file_id}*")
    debug_log(f"[DEBUG] 查找模式 pattern: {pattern}")
    matching_files = glob.glob(pattern)
    debug_log(f"[DEBUG] 匹配到的文件 matching_files: {matching_files}")
    
    if not matching_files:
        error_msg = f"未找到文件ID为 {file_id} 的文件"
        debug_log(f"[DEBUG] {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)
    
    # 获取第一个匹配的文件
    file_path = matching_files[0]
    debug_log(f"[DEBUG] 实际读取的文件路径 file_path: {file_path}")
    
    # 检查文件扩展名
    file_ext = Path(file_path).suffix.lower()
    debug_log(f"[DEBUG] 文件扩展名 file_ext: {file_ext}")
    
    try:
        if file_ext == '.docx' or file_ext == '.doc':
            # 处理Word文档
            logger.info(f"正在读取Word文档: {file_path}")
            return read_word_document(file_path)
        elif file_ext in ['.txt', '.md', '.csv']:
            # 处理文本文件
            logger.info(f"正在读取文本文件: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
        elif file_ext == '.pdf':
            # PDF处理
            logger.info(f"PDF文件暂不支持直接读取内容，返回摘要信息: {file_path}")
            return f"[PDF文件] {os.path.basename(file_path)}\n此文件为PDF格式，已接收但无法直接提取内容进行分析。"
        else:
            # 其他文件类型，尝试以二进制模式读取并转换为文本
            logger.warning(f"不支持的文件类型: {file_ext}，尝试以二进制模式读取")
            with open(file_path, 'rb') as f:
                binary_content = f.read()
                try:
                    # 尝试解码为文本
                    return binary_content.decode('utf-8', errors='ignore')
                except:
                    # 如果解码失败，返回一个摘要
                    file_size = os.path.getsize(file_path)
                    return f"[二进制文件] {os.path.basename(file_path)}\n文件大小: {file_size} 字节\n文件类型: {file_ext}"
    except Exception as e:
        error_msg = f"读取文件失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)
