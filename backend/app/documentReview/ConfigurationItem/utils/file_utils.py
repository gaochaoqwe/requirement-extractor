import os
import glob
import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException
from docx import Document  # 用于读取Word文档

# 设置日志
logger = logging.getLogger(__name__)

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPLOAD_ROOT = os.path.join(BASE_DIR, 'uploads', 'configuration_item')
REQUIREMENT_SPEC_DIR = os.path.join(UPLOAD_ROOT, 'requirement_specs')
TASK_BOOK_DIR = os.path.join(UPLOAD_ROOT, 'task_books')
os.makedirs(REQUIREMENT_SPEC_DIR, exist_ok=True)
os.makedirs(TASK_BOOK_DIR, exist_ok=True)

def save_upload_file(file: UploadFile, file_id: str, doc_type: str):
    """
    根据doc_type保存到不同目录
    """
    if doc_type == "requirementSpec":
        save_dir = REQUIREMENT_SPEC_DIR
    elif doc_type == "taskBook":
        save_dir = TASK_BOOK_DIR
    else:
        raise ValueError(f"未知文档类型: {doc_type}")
    file_path = os.path.join(save_dir, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path


def read_word_document(file_path: str) -> str:
    """
    读取Word文档内容
    
    Args:
        file_path: Word文档路径
        
    Returns:
        str: 文档内容
    """
    try:
        doc = Document(file_path)

        # 内部函数：按文档顺序遍历段落和表格
        from docx.text.paragraph import Paragraph
        from docx.table import Table

        def iter_block_items(parent):
            """按出现顺序依次产出 Paragraph 或 Table 对象"""
            for child in parent.element.body.iterchildren():
                # 段落
                if child.tag.endswith('}p'):
                    yield Paragraph(child, parent)
                # 表格
                elif child.tag.endswith('}tbl'):
                    yield Table(child, parent)

        lines = []
        table_counter = 0  # 用于给表格编号，方便引用

        def table_to_markdown(table, index: int) -> str:
            """将 python-docx 的 Table 转为 Markdown 字符串，并添加表编号"""
            if not table.rows:
                return ""

            # 处理首行作为表头
            header_cells = [c.text.strip().replace("\n", " ") for c in table.rows[0].cells]
            md_lines = [f"【表 {index}】", f"| {' | '.join(header_cells)} |"]
            md_lines.append(f"| {' | '.join(['---'] * len(header_cells))} |")

            # 其余行作为数据行
            for row in table.rows[1:]:
                row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                md_lines.append(f"| {' | '.join(row_cells)} |")
            return "\n".join(md_lines)

        for block in iter_block_items(doc):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if text:
                    # 确保段落之间有双换行符
                    lines.append(text + "\n\n")
            elif isinstance(block, Table):
                table_counter += 1
                md = table_to_markdown(block, table_counter)
                if md:
                    # 表格前后也添加双换行符
                    lines.append("\n\n" + md + "\n\n")

        return ''.join(lines).strip()
    except Exception as e:
        logger.error(f"读取Word文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"读取Word文档失败: {str(e)}")

def read_uploaded_file(file_id: str, doc_type: str) -> str:
    """
    根据file_id和doc_type查找并读取上传的文件内容
    
    Args:
        file_id: 文件ID
        doc_type: 文档类型 (requirementSpec 或 taskBook)
        
    Returns:
        str: 文件内容
        
    Raises:
        HTTPException: 当文件不存在或读取失败时
    """
    logger.debug(f"进入read_uploaded_file函数: file_id={file_id}, doc_type={doc_type}")
    
    # 确定要查找的目录
    if doc_type == "requirementSpec":
        search_dir = REQUIREMENT_SPEC_DIR
    elif doc_type == "taskBook":
        search_dir = TASK_BOOK_DIR
    else:
        raise HTTPException(status_code=400, detail=f"未知文档类型: {doc_type}")
    
    logger.debug(f"开始在目录中查找文件: {search_dir}")
    
    # 使用glob模式查找匹配的文件
    pattern = os.path.join(search_dir, f"{file_id}_*")
    matching_files = glob.glob(pattern)
    
    logger.debug(f"查找模式: {pattern}")
    logger.debug(f"匹配的文件: {matching_files}")
    
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"未找到文件ID为 {file_id} 的文件")
    
    # 获取第一个匹配的文件
    file_path = matching_files[0]
    logger.info(f"找到文件: {file_path}")
    
    # 检查文件扩展名
    file_ext = Path(file_path).suffix.lower()
    
    try:
        if file_ext == '.docx':
            # 处理Word文档
            logger.info(f"正在读取Word文档: {file_path}")
            return read_word_document(file_path)
        elif file_ext in ['.txt', '.md', '.csv']:
            # 处理文本文件
            logger.info(f"正在读取文本文件: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # 其他文件类型，尝试以二进制模式读取
            logger.warning(f"不支持的文件类型: {file_ext}，尝试以二进制模式读取")
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')
                
    except Exception as e:
        error_msg = f"读取文件失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)
