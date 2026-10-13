"""
文档页数计算器

从需求规格说明文档中计算文档页数，用于填充软件配置项信息表的审查文档规模字段。
支持.docx和.pdf格式的文档页数计算。
"""

import logging
import os
from typing import Optional
from pathlib import Path

# 导入任务日志函数  
try:
    from ....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_debug, log_error, log_warning
    except ImportError:
        # 提供默认的日志函数作为备用
        import logging
        logger = logging.getLogger(__name__)
        def log_info(msg, source="document_page_counter"):
            logger.info(f"[{source}] {msg}")
        def log_debug(msg, source="document_page_counter"):  
            logger.debug(f"[{source}] {msg}")
        def log_error(msg, source="document_page_counter"):
            logger.error(f"[{source}] {msg}")
        def log_warning(msg, source="document_page_counter"):
            logger.warning(f"[{source}] {msg}")

# 配置日志
logger = logging.getLogger(__name__)

class DocumentPageCounter:
    """文档页数计算器"""
    
    def __init__(self):
        """初始化文档页数计算器"""
        self.logger = logger
        
    def calculate_document_pages(self, document_path: str) -> Optional[int]:
        """
        计算文档页数
        
        Args:
            document_path: 文档路径
            
        Returns:
            Optional[int]: 文档页数，如果计算失败返回None
        """
        try:
            log_debug(f"[DEBUG] 开始计算文档页数流程", "document_page_counter")
            log_debug(f"[DEBUG] 输入参数 - document_path: '{document_path}'", "document_page_counter")
            
            if not document_path:
                log_warning(f"文档路径为空", "document_page_counter")
                log_debug(f"[DEBUG] 返回值: None (路径为空)", "document_page_counter")
                return None
                
            if not os.path.exists(document_path):
                log_warning(f"文档文件不存在: {document_path}", "document_page_counter")
                log_debug(f"[DEBUG] 返回值: None (文件不存在)", "document_page_counter")
                return None
                
            log_info(f"开始计算文档页数: {document_path}", "document_page_counter")
            
            # 获取文件扩展名
            file_path = Path(document_path)
            file_extension = file_path.suffix.lower()
            file_size = file_path.stat().st_size
            
            log_debug(f"[DEBUG] 文档信息分析:", "document_page_counter")
            log_debug(f"[DEBUG]   - 文件路径: {file_path}", "document_page_counter")
            log_debug(f"[DEBUG]   - 文件扩展名: {file_extension}", "document_page_counter")
            log_debug(f"[DEBUG]   - 文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)", "document_page_counter")
            
            # 根据文件类型选择计算方法
            if file_extension == '.docx':
                log_debug(f"[DEBUG] 选择DOCX文档页数计算方法", "document_page_counter")
                page_count = self._calculate_docx_pages(document_path)
            elif file_extension == '.pdf':
                log_debug(f"[DEBUG] 选择PDF文档页数计算方法", "document_page_counter")
                page_count = self._calculate_pdf_pages(document_path)
            else:
                log_warning(f"不支持的文档格式: {file_extension}", "document_page_counter")
                log_debug(f"[DEBUG] 支持的格式: .docx, .pdf", "document_page_counter")
                log_debug(f"[DEBUG] 返回值: None (格式不支持)", "document_page_counter")
                return None
                
            if page_count is not None:
                log_info(f"文档页数计算完成: {page_count} 页", "document_page_counter")
                log_debug(f"[DEBUG] 页数计算成功 - 最终结果: {page_count}页", "document_page_counter")
            else:
                log_error("文档页数计算失败", "document_page_counter")
                log_debug(f"[DEBUG] 页数计算失败 - 返回值: None", "document_page_counter")
                
            log_debug(f"[DEBUG] 计算文档页数流程结束", "document_page_counter")
            return page_count
            
        except Exception as e:
            log_error(f"计算文档页数时发生错误: {str(e)}", "document_page_counter")
            log_debug(f"[DEBUG] 异常详情: {type(e).__name__}: {str(e)}", "document_page_counter")
            import traceback
            log_debug(f"[DEBUG] 异常堆栈: {traceback.format_exc()}", "document_page_counter")
            return None
    
    def _calculate_docx_pages(self, docx_path: str) -> Optional[int]:
        """
        计算DOCX文档页数
        
        Args:
            docx_path: DOCX文档路径
            
        Returns:
            Optional[int]: 页数，失败返回None
        """
        try:
            log_debug(f"[DEBUG] 开始DOCX文档页数计算流程: {docx_path}", "document_page_counter")
            
            # 尝试导入python-docx库
            try:
                from docx import Document
                log_debug(f"[DEBUG] python-docx库导入成功", "document_page_counter")
            except ImportError:
                log_error("python-docx库未安装，无法计算DOCX页数", "document_page_counter")
                log_debug(f"[DEBUG] 需要安装python-docx: pip install python-docx", "document_page_counter")
                return None
            
            # 读取文档
            log_debug(f"[DEBUG] 正在读取DOCX文档...", "document_page_counter")
            doc = Document(docx_path)
            log_debug(f"[DEBUG] DOCX文档读取成功", "document_page_counter")
            
            # 方法1：尝试从文档属性中获取页数
            log_debug(f"[DEBUG] 方法1: 尝试从文档属性获取页数", "document_page_counter")
            page_count = self._get_docx_page_count_from_properties(doc)
            if page_count is not None:
                log_debug(f"[DEBUG] 方法1成功 - 从文档属性获取页数: {page_count}", "document_page_counter")
                log_info(f"使用文档属性方法获取页数: {page_count}", "document_page_counter")
                return page_count
            else:
                log_debug(f"[DEBUG] 方法1失败 - 无法从文档属性获取页数", "document_page_counter")
            
            # 方法2：通过分页符计算页数
            log_debug(f"[DEBUG] 方法2: 尝试通过分页符计算页数", "document_page_counter")
            page_count = self._estimate_docx_pages_by_page_breaks(doc)
            if page_count is not None:
                log_debug(f"[DEBUG] 方法2成功 - 通过分页符估算页数: {page_count}", "document_page_counter")
                log_info(f"使用分页符方法估算页数: {page_count}", "document_page_counter")
                return page_count
            else:
                log_debug(f"[DEBUG] 方法2失败 - 未找到有效分页符", "document_page_counter")
            
            # 方法3：通过内容长度估算页数
            log_debug(f"[DEBUG] 方法3: 通过内容长度估算页数", "document_page_counter")
            page_count = self._estimate_docx_pages_by_content(doc)
            log_debug(f"[DEBUG] 方法3结果 - 通过内容长度估算页数: {page_count}", "document_page_counter")
            log_info(f"使用内容分析方法估算页数: {page_count}", "document_page_counter")
            return page_count
            
        except Exception as e:
            log_error(f"计算DOCX页数时发生错误: {str(e)}", "document_page_counter")
            log_debug(f"[DEBUG] DOCX计算异常: {type(e).__name__}: {str(e)}", "document_page_counter")
            import traceback
            log_debug(f"[DEBUG] DOCX异常堆栈: {traceback.format_exc()}", "document_page_counter")
            return None
    
    def _get_docx_page_count_from_properties(self, doc) -> Optional[int]:
        """
        从文档属性中获取页数
        
        Args:
            doc: Document对象
            
        Returns:
            Optional[int]: 页数，获取失败返回None
        """
        try:
            # 尝试从核心属性中获取页数
            if hasattr(doc, 'core_properties'):
                core_props = doc.core_properties
                if hasattr(core_props, 'pages') and core_props.pages:
                    return core_props.pages
            
            # 尝试从扩展属性中获取页数
            if hasattr(doc, 'part') and hasattr(doc.part, 'package'):
                package = doc.part.package
                if hasattr(package, 'part_related_by'):
                    try:
                        # 查找扩展属性部分
                        extended_props_part = None
                        for rel in package.part_related_by('http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties'):
                            extended_props_part = rel
                            break
                        
                        if extended_props_part:
                            # 解析扩展属性XML
                            import xml.etree.ElementTree as ET
                            root = ET.fromstring(extended_props_part.blob)
                            
                            # 查找Pages元素
                            for elem in root.iter():
                                if elem.tag.endswith('Pages') and elem.text:
                                    return int(elem.text)
                    except Exception:
                        pass
            
            return None
            
        except Exception as e:
            log_debug(f"从文档属性获取页数失败: {str(e)}", "document_page_counter")
            return None
    
    def _estimate_docx_pages_by_page_breaks(self, doc) -> Optional[int]:
        """
        通过分页符估算页数
        
        Args:
            doc: Document对象
            
        Returns:
            Optional[int]: 估算页数
        """
        try:
            page_count = 1  # 至少有一页
            
            # 统计手动分页符
            for para in doc.paragraphs:
                if para._element.xpath('.//w:br[@w:type="page"]'):
                    page_count += 1
            
            # 统计章节分页符
            for section in doc.sections:
                if hasattr(section, '_sectPr'):
                    sectPr = section._sectPr
                    if sectPr.xpath('.//w:type[@w:val="nextPage"]'):
                        page_count += 1
            
            return page_count if page_count > 1 else None
            
        except Exception as e:
            log_debug(f"通过分页符估算页数失败: {str(e)}", "document_page_counter")
            return None
    
    def _estimate_docx_pages_by_content(self, doc) -> Optional[int]:
        """
        通过内容长度估算页数
        
        Args:
            doc: Document对象
            
        Returns:
            Optional[int]: 估算页数
        """
        try:
            log_debug(f"[DEBUG] 开始内容分析统计", "document_page_counter")
            
            # 统计总字符数
            total_chars = 0
            total_paragraphs = 0
            paragraph_count = 0
            non_empty_paragraphs = 0
            
            log_debug(f"[DEBUG] 统计段落内容...", "document_page_counter")
            for para in doc.paragraphs:
                paragraph_count += 1
                total_chars += len(para.text)
                if para.text.strip():  # 非空段落
                    non_empty_paragraphs += 1
                    total_paragraphs += 1
            
            log_debug(f"[DEBUG] 段落统计结果:", "document_page_counter")
            log_debug(f"[DEBUG]   - 总段落数: {paragraph_count}", "document_page_counter")
            log_debug(f"[DEBUG]   - 非空段落数: {non_empty_paragraphs}", "document_page_counter")
            log_debug(f"[DEBUG]   - 段落字符数: {total_chars}", "document_page_counter")
            
            # 统计表格中的字符数
            table_count = len(doc.tables)
            table_chars = 0
            table_paragraphs = 0
            
            log_debug(f"[DEBUG] 统计表格内容... (表格数量: {table_count})", "document_page_counter")
            for table_idx, table in enumerate(doc.tables):
                table_cell_count = 0
                for row in table.rows:
                    for cell in row.cells:
                        table_cell_count += 1
                        cell_text_len = len(cell.text)
                        table_chars += cell_text_len
                        table_paragraphs += len(cell.paragraphs)
                log_debug(f"[DEBUG]   - 表格{table_idx+1}: {table_cell_count}个单元格", "document_page_counter")
            
            total_chars += table_chars
            total_paragraphs += table_paragraphs
            
            log_debug(f"[DEBUG] 表格统计结果:", "document_page_counter")
            log_debug(f"[DEBUG]   - 表格字符数: {table_chars}", "document_page_counter")
            log_debug(f"[DEBUG]   - 表格段落数: {table_paragraphs}", "document_page_counter")
            
            log_debug(f"[DEBUG] 综合统计结果:", "document_page_counter")
            log_debug(f"[DEBUG]   - 总字符数: {total_chars}", "document_page_counter")
            log_debug(f"[DEBUG]   - 总段落数: {total_paragraphs}", "document_page_counter")
            log_info(f"文档内容统计 - 总字符数: {total_chars}, 总段落数: {total_paragraphs}", "document_page_counter")
            
            # 基于经验公式估算页数
            # 一般A4页面约包含2000-3000个中文字符或3000-4000个英文字符
            # 考虑到需求文档通常包含图表和格式，使用较宽松的估算
            estimated_pages_by_chars = max(1, total_chars // 2500)
            estimated_pages_by_paragraphs = max(1, total_paragraphs // 25)  # 每页约25段落
            
            # 取两种估算方法的较大值
            estimated_pages = max(estimated_pages_by_chars, estimated_pages_by_paragraphs)
            
            log_debug(f"[DEBUG] 页数估算计算:", "document_page_counter")
            log_debug(f"[DEBUG]   - 按字符数估算: {total_chars} ÷ 2500 = {estimated_pages_by_chars}页", "document_page_counter")
            log_debug(f"[DEBUG]   - 按段落数估算: {total_paragraphs} ÷ 25 = {estimated_pages_by_paragraphs}页", "document_page_counter")
            log_debug(f"[DEBUG]   - 最终估算结果: max({estimated_pages_by_chars}, {estimated_pages_by_paragraphs}) = {estimated_pages}页", "document_page_counter")
            
            log_info(f"页数估算结果 - 按字符数: {estimated_pages_by_chars}页, 按段落数: {estimated_pages_by_paragraphs}页, 最终: {estimated_pages}页", "document_page_counter")
            
            return estimated_pages
            
        except Exception as e:
            log_error(f"通过内容长度估算页数失败: {str(e)}", "document_page_counter")
            log_debug(f"[DEBUG] 内容分析异常: {type(e).__name__}: {str(e)}", "document_page_counter")
            return 1  # 默认返回1页
    
    def _calculate_pdf_pages(self, pdf_path: str) -> Optional[int]:
        """
        计算PDF文档页数
        
        Args:
            pdf_path: PDF文档路径
            
        Returns:
            Optional[int]: 页数，失败返回None
        """
        try:
            log_debug(f"开始计算PDF文档页数: {pdf_path}", "document_page_counter")
            
            # 尝试使用PyPDF2
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    page_count = len(pdf_reader.pages)
                    log_debug(f"使用PyPDF2计算PDF页数: {page_count}", "document_page_counter")
                    return page_count
            except ImportError:
                log_debug("PyPDF2库未安装，尝试其他方法", "document_page_counter")
            except Exception as e:
                log_debug(f"PyPDF2计算失败: {str(e)}", "document_page_counter")
            
            # 尝试使用pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    page_count = len(pdf.pages)
                    log_debug(f"使用pdfplumber计算PDF页数: {page_count}", "document_page_counter")
                    return page_count
            except ImportError:
                log_debug("pdfplumber库未安装，尝试其他方法", "document_page_counter")
            except Exception as e:
                log_debug(f"pdfplumber计算失败: {str(e)}", "document_page_counter")
            
            # 如果所有方法都失败，返回None
            log_error("所有PDF页数计算方法都失败", "document_page_counter")
            return None
            
        except Exception as e:
            log_error(f"计算PDF页数时发生错误: {str(e)}", "document_page_counter")
            return None
    
    def get_review_document_scale(self, document_path: str, default_value: int = 60) -> int:
        """
        获取审查文档规模
        
        Args:
            document_path: 文档路径
            default_value: 默认值
            
        Returns:
            int: 审查文档规模（页数）
        """
        try:
            log_debug(f"[DEBUG] 开始获取审查文档规模流程", "document_page_counter")
            log_debug(f"[DEBUG] 输入参数:", "document_page_counter")
            log_debug(f"[DEBUG]   - document_path: '{document_path}'", "document_page_counter")
            log_debug(f"[DEBUG]   - default_value: {default_value}", "document_page_counter")
            
            log_info(f"获取审查文档规模，文档路径: {document_path}", "document_page_counter")
            
            if not document_path:
                log_warning("文档路径为空，使用默认值", "document_page_counter")
                log_debug(f"[DEBUG] 返回默认值: {default_value} (路径为空)", "document_page_counter")
                return default_value
            
            # 计算文档页数
            log_debug(f"[DEBUG] 调用文档页数计算方法", "document_page_counter")
            page_count = self.calculate_document_pages(document_path)
            log_debug(f"[DEBUG] 文档页数计算结果: {page_count}", "document_page_counter")
            
            if page_count is not None and page_count > 0:
                log_info(f"成功计算审查文档规模: {page_count}页", "document_page_counter")
                log_debug(f"[DEBUG] 页数计算成功，返回实际页数: {page_count}", "document_page_counter")
                
                # 记录详细的审查文档规模信息
                log_debug(f"[DEBUG] 审查文档规模详情:", "document_page_counter")
                log_debug(f"[DEBUG]   - 文档路径: {document_path}", "document_page_counter")
                log_debug(f"[DEBUG]   - 计算方式: 自动计算", "document_page_counter")
                log_debug(f"[DEBUG]   - 页数结果: {page_count}页", "document_page_counter")
                log_debug(f"[DEBUG]   - 是否使用默认值: 否", "document_page_counter")
                
                return page_count
            else:
                log_warning(f"文档页数计算失败，使用默认值: {default_value}", "document_page_counter")
                log_debug(f"[DEBUG] 页数计算失败，返回默认值: {default_value}", "document_page_counter")
                log_debug(f"[DEBUG] 失败原因: page_count = {page_count}", "document_page_counter")
                
                # 记录使用默认值的详细信息
                log_debug(f"[DEBUG] 审查文档规模详情:", "document_page_counter")
                log_debug(f"[DEBUG]   - 文档路径: {document_path}", "document_page_counter")
                log_debug(f"[DEBUG]   - 计算方式: 使用默认值", "document_page_counter")
                log_debug(f"[DEBUG]   - 页数结果: {default_value}页", "document_page_counter")
                log_debug(f"[DEBUG]   - 是否使用默认值: 是", "document_page_counter")
                
                return default_value
                
        except Exception as e:
            log_error(f"获取审查文档规模时发生错误: {str(e)}", "document_page_counter")
            log_debug(f"[DEBUG] 审查文档规模获取异常: {type(e).__name__}: {str(e)}", "document_page_counter")
            import traceback
            log_debug(f"[DEBUG] 异常堆栈: {traceback.format_exc()}", "document_page_counter")
            log_debug(f"[DEBUG] 异常发生，返回默认值: {default_value}", "document_page_counter")
            return default_value 