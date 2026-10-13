 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyWin32文档处理器
替代原有的spire_doc方案，提供更稳定的文档处理功能

主要功能：
1. 快速目录提取（用于前端显示）
2. 文档标准化（保持格式完整性）
3. 兼容现有接口格式
"""

import os
import sys
import shutil
import asyncio
import time
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

try:
    import win32com.client as win32
    from win32com.client import constants
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    print("PyWin32不可用，将使用回退机制", file=sys.stderr)

try:
    from ..logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    # 简单的日志回退
    def log_info(msg, module="pywin32_processor"): print(f"[INFO] {msg}")
    def log_error(msg, module="pywin32_processor"): print(f"[ERROR] {msg}")
    def log_warning(msg, module="pywin32_processor"): print(f"[WARNING] {msg}")
    def log_debug(msg, module="pywin32_processor"): print(f"[DEBUG] {msg}")


class PyWin32DocumentProcessor:
    """PyWin32文档处理器 - 方法A实现"""
    
    def __init__(self):
        self.word_app = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def _ensure_word_app(self):
        """确保Word应用程序已启动"""
        if not PYWIN32_AVAILABLE:
            raise Exception("PyWin32不可用，无法启动Word应用程序")
            
        if self.word_app is None:
            try:
                self.word_app = win32.gencache.EnsureDispatch("Word.Application")
                self.word_app.Visible = False
                self.word_app.DisplayAlerts = 0
                log_info("Word应用程序启动成功", "pywin32_processor")
            except Exception as e:
                log_error(f"启动Word应用程序失败: {e}", "pywin32_processor")
                raise
    
    def _cleanup_word_app(self):
        """清理Word应用程序和临时文件"""
        # 清理临时文件
        if hasattr(self, '_temp_files'):
            for temp_file in self._temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        log_debug(f"临时文件已清理: {temp_file}", "pywin32_processor")
                    
                    # 清理临时目录（如果为空）
                    temp_dir = os.path.dirname(temp_file)
                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
                        log_debug(f"临时目录已清理: {temp_dir}", "pywin32_processor")
                except Exception as e:
                    log_warning(f"清理临时文件失败: {e}", "pywin32_processor")
            
            self._temp_files = []
        
        # 清理Word应用程序
        if self.word_app:
            try:
                self.word_app.Quit()
                self.word_app = None
                log_debug("Word应用程序已清理", "pywin32_processor")
            except Exception as e:
                log_warning(f"清理Word应用程序时出错: {e}", "pywin32_processor")
    
    def _prepare_document_path(self, doc_path: str) -> str:
        """
        处理文档路径，解决中文路径和长路径问题
        
        Args:
            doc_path: 原始文档路径
            
        Returns:
            处理后的文档路径
        """
        import tempfile
        import shutil
        from pathlib import Path
        
        try:
            original_path = Path(doc_path)
            
            # 检查路径是否包含中文或特殊字符，或路径过长
            path_str = str(original_path.absolute())
            
            # 检查是否需要创建临时副本
            needs_temp_copy = False
            
            # 1. 检查路径长度（Windows路径限制）
            if len(path_str) > 200:
                needs_temp_copy = True
                log_info("检测到长路径，创建临时副本...", "pywin32_processor")
            
            # 2. 检查是否包含非ASCII字符
            try:
                path_str.encode('ascii')
            except UnicodeEncodeError:
                needs_temp_copy = True
                log_info("检测到中文路径，创建临时副本...", "pywin32_processor")
            
            if needs_temp_copy:
                # 创建临时文件
                temp_dir = tempfile.mkdtemp()
                temp_filename = f"temp_doc_{int(time.time())}.docx"
                temp_path = os.path.join(temp_dir, temp_filename)
                
                # 复制文件到临时位置
                shutil.copy2(doc_path, temp_path)
                log_info(f"临时副本创建成功: {temp_path}", "pywin32_processor")
                
                # 记录临时文件路径，用于后续清理
                if not hasattr(self, '_temp_files'):
                    self._temp_files = []
                self._temp_files.append(temp_path)
                
                return os.path.abspath(temp_path)
            else:
                # 使用原始绝对路径
                return os.path.abspath(doc_path)
                
        except Exception as e:
            log_error(f"处理文档路径失败: {e}", "pywin32_processor")
            # 回退到原始路径
            return os.path.abspath(doc_path)
    
    def is_heading_style(self, style_name: str) -> bool:
        """判断是否为标题样式"""
        if not style_name:
            return False
        name = str(style_name).strip().lower()
        return ("heading" in name) or ("标题" in name)
    
    def extract_catalog_info_fast(self, doc_path: str) -> List[Dict[str, Any]]:
        """
        快速提取文档目录信息（用于前端显示）
        返回格式兼容现有的spire_doc格式
        """
        results = []
        
        if not PYWIN32_AVAILABLE:
            raise Exception("PyWin32不可用，无法提取目录信息")
        
        self._ensure_word_app()
        doc = None
        
        try:
            log_info(f"开始提取目录信息: {doc_path}", "pywin32_processor")
            
            # 🔧 修复：处理中文路径问题
            processed_path = self._prepare_document_path(doc_path)
            
            doc = self.word_app.Documents.Open(processed_path, ReadOnly=True)
            paragraphs = doc.Paragraphs
            
            for p in paragraphs:
                try:
                    rng = p.Range
                    style_name = getattr(rng, "Style", None)
                    style_name = getattr(style_name, "NameLocal", style_name) if style_name is not None else None
                    
                    if not self.is_heading_style(style_name):
                        continue
                    
                    list_str = str(rng.ListFormat.ListString or "").strip()
                    
                    if list_str:
                        text = (rng.Text or "").strip().replace("\r", " ").replace("\n", " ")
                        level = self._infer_heading_level(list_str)
                        
                        # 兼容现有格式
                        catalog_item = {
                            "level": level,
                            "number": list_str,
                            "title": text,
                            "full_text": f"{list_str} {text}" if text else list_str,
                            # 兼容spire_doc格式
                            "text": f"{list_str} {text}" if text else list_str,
                            "outline_level": level
                        }
                        results.append(catalog_item)
                        
                except Exception:
                    continue
                    
        except Exception as e:
            log_error(f"提取目录信息失败: {e}", "pywin32_processor")
            raise Exception(f"提取目录信息失败: {e}")
        finally:
            if doc:
                try:
                    doc.Close(SaveChanges=False)
                except Exception:
                    pass
        
        log_info(f"目录提取完成，找到 {len(results)} 个标题", "pywin32_processor")
        return results
    
    def _infer_heading_level(self, list_str: str) -> int:
        """根据编号格式推断标题级别"""
        if not list_str:
            return 1
        
        dot_count = list_str.count('.')
        if dot_count == 0:
            return 1
        elif dot_count == 1:
            return 2
        elif dot_count == 2:
            return 3
        else:
            return min(dot_count + 1, 6)
    
    def standardize_document_preserve_format(self, input_path: str, output_path: str = None) -> str:
        """
        标准化文档：保持格式的同时添加手动编号（方法A）
        """
        if not PYWIN32_AVAILABLE:
            raise Exception("PyWin32不可用，无法进行文档标准化")
            
        if output_path is None:
            input_file = Path(input_path)
            output_path = str(input_file.parent / f"standardized_{input_file.name}")
        
        # 先复制文件
        shutil.copy2(input_path, output_path)
        
        self._ensure_word_app()
        doc = None
        
        try:
            log_info(f"开始标准化文档: {input_path} -> {output_path}", "pywin32_processor")
            
            # 🔧 修复：处理中文路径问题
            processed_output_path = self._prepare_document_path(output_path)
            
            doc = self.word_app.Documents.Open(processed_output_path)
            
            # 收集需要处理的段落信息
            paragraphs_to_process = []
            total_paragraphs = doc.Paragraphs.Count
            
            for i, p in enumerate(doc.Paragraphs):
                try:
                    rng = p.Range
                    style_name = getattr(rng, "Style", None)
                    style_name = getattr(style_name, "NameLocal", style_name) if style_name is not None else None
                    
                    # 仅处理标题样式的段落
                    if not self.is_heading_style(style_name):
                        continue
                    
                    list_str = str(rng.ListFormat.ListString or "").strip()
                    
                    if list_str:
                        # 获取纯文本内容（不包含段落标记）
                        text = rng.Text
                        if text and text.endswith('\r'):
                            text = text[:-1]  # 移除段落结束符
                        
                        text = text.strip() if text else ""
                        
                        paragraphs_to_process.append({
                            'paragraph': p,
                            'range': rng,
                            'list_str': list_str,
                            'text': text,
                            'style_name': style_name
                        })
                        
                except Exception:
                    continue
            
            log_info(f"找到 {len(paragraphs_to_process)} 个标题段落需要标准化", "pywin32_processor")
            
            # 处理每个段落 - 使用改进的方法
            processed_count = 0
            for i, item in enumerate(paragraphs_to_process):
                try:
                    success = self._standardize_paragraph_improved(item, i+1)
                    if success:
                        processed_count += 1
                        
                except Exception as e:
                    log_warning(f"处理标题{i+1}时出错: {e}", "pywin32_processor")
                    continue
            
            log_info(f"成功标准化 {processed_count} 个标题段落", "pywin32_processor")
            
            # 保存文档
            doc.Save()
            
        except Exception as e:
            log_error(f"标准化文档失败: {e}", "pywin32_processor")
            raise Exception(f"标准化文档失败: {e}")
        finally:
            if doc:
                try:
                    doc.Close()
                except Exception:
                    pass
        
        return output_path
    
    def _standardize_paragraph_improved(self, item, index) -> bool:
        """
        改进的段落标准化方法
        策略：保持自动编号，在文本开头插入手动编号
        """
        try:
            rng = item['range']
            list_str = item['list_str']
            text = item['text']
            
            # 检查是否已经标准化（文本开头已包含编号）
            if text.startswith(list_str + " "):
                return False
            
            # 方法1：尝试在文本开头插入编号
            try:
                # 创建一个新的范围，只包含文本部分（不包含段落标记）
                text_range = rng.Duplicate
                
                # 确保范围不包含段落结束符
                if text_range.Text and text_range.Text.endswith('\r'):
                    text_range.End = text_range.End - 1
                
                # 构建新文本：编号 + 空格 + 原文本
                new_text = f"{list_str} {text}"
                
                # 替换文本内容
                text_range.Text = new_text
                
                return True
                
            except Exception:
                # 方法2：使用InsertBefore方法
                try:
                    # 在段落开头插入编号
                    rng.InsertBefore(f"{list_str} ")
                    return True
                    
                except Exception:
                    # 方法3：直接替换但保持格式
                    try:
                        original_style = rng.Style
                        
                        new_text = f"{list_str} {text}"
                        rng.Text = new_text
                        
                        # 恢复格式
                        rng.Style = original_style
                        
                        return True
                        
                    except Exception:
                        return False
                        
        except Exception:
            return False


# 兼容接口函数
def extract_testing_requirements_with_spire(docx_path: str, debug_mode: bool = False) -> Dict[str, Any]:
    """
    兼容原有spire_doc接口的目录提取函数
    """
    try:
        if not PYWIN32_AVAILABLE:
            # 回退到原有方法
            log_warning("PyWin32不可用，回退到原有spire_doc方法", "pywin32_processor")
            from ..spire_doc import extract_testing_requirements_with_spire as original_extract
            return original_extract(docx_path, debug_mode)
        
        processor = PyWin32DocumentProcessor()
        
        # 提取目录信息
        catalog_info = processor.extract_catalog_info_fast(docx_path)
        
        # 过滤3.2章节
        filtered_items = []
        for item in catalog_info:
            number = item.get('number', '')
            if number.startswith('3.2') and (number == '3.2' or number.startswith('3.2.')):
                filtered_items.append(item)
        
        # 分析级别分布
        level_distribution = {}
        for item in catalog_info:
            level = item.get('level', 1)
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        return {
            "status": "success",
            "message": f"成功提取 {len(catalog_info)} 个标题，其中 {len(filtered_items)} 个3.2章节标题",
            "catalog_items": catalog_info,
            "filtered_items": filtered_items,
            "total_headings": len(catalog_info),
            "filtered_count": len(filtered_items),
            "level_distribution": level_distribution,
            "extraction_method": "pywin32_enhanced"
        }
        
    except Exception as e:
        log_error(f"PyWin32提取失败: {e}", "pywin32_processor")
        
        # 回退到原有方法
        try:
            log_info("回退到原有spire_doc方法", "pywin32_processor")
            from ..spire_doc import extract_testing_requirements_with_spire as original_extract
            result = original_extract(docx_path, debug_mode)
            result["extraction_method"] = "spire_fallback"
            return result
        except Exception as fallback_error:
            log_error(f"回退方法也失败: {fallback_error}", "pywin32_processor")
            return {
                "status": "error",
                "message": f"目录提取失败: {str(e)}，回退方法也失败: {str(fallback_error)}",
                "catalog_items": [],
                "filtered_items": [],
                "total_headings": 0,
                "filtered_count": 0,
                "level_distribution": {},
                "extraction_method": "failed"
            }


def create_standardized_document_from_single_file(document_path: str, 
                                                 output_path: str = None,
                                                 debug_mode: bool = False) -> str:
    """
    兼容原有spire_doc接口的文档标准化函数
    """
    try:
        if not PYWIN32_AVAILABLE:
            # 回退到原有方法
            log_warning("PyWin32不可用，回退到原有spire_doc方法", "pywin32_processor")
            from ..spire_doc import create_standardized_document_from_single_file as original_create
            return original_create(document_path, output_path, debug_mode)
        
        processor = PyWin32DocumentProcessor()
        return processor.standardize_document_preserve_format(document_path, output_path)
        
    except Exception as e:
        log_error(f"PyWin32标准化失败: {e}", "pywin32_processor")
        
        # 回退到原有方法
        try:
            log_info("回退到原有spire_doc方法", "pywin32_processor")
            from ..spire_doc import create_standardized_document_from_single_file as original_create
            return original_create(document_path, output_path, debug_mode)
        except Exception as fallback_error:
            log_error(f"回退方法也失败: {fallback_error}", "pywin32_processor")
            raise Exception(f"文档标准化失败: {str(e)}，回退方法也失败: {str(fallback_error)}")


# 新增：并发处理函数
async def process_document_concurrent(file_path: str, session_id: str) -> Dict[str, Any]:
    """
    并发处理文档：快速返回目录信息 + 后台标准化文档
    """
    try:
        # 1. 快速提取目录信息（优先返回给前端）
        start_time = time.time()

        # ✅ 关键修复：目录提取是Word COM阻塞操作，必须放到线程池，否则会阻塞事件循环导致“并发”失效
        def _extract_catalog_in_thread(path: str) -> List[Dict[str, Any]]:
            import pythoncom
            pythoncom.CoInitialize()
            proc = PyWin32DocumentProcessor()
            try:
                return proc.extract_catalog_info_fast(path)
            finally:
                try:
                    proc._cleanup_word_app()
                except Exception:
                    pass
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        # 🔧 使用线程池执行目录提取
        try:
            loop = asyncio.get_event_loop()
            catalog_items = await loop.run_in_executor(None, _extract_catalog_in_thread, file_path)
            catalog_result = {
                "status": "success",
                "message": f"成功提取 {len(catalog_items)} 个标题",
                "catalog_items": catalog_items,
                "filtered_items": [item for item in catalog_items if item.get('level') >= 3 and (item.get('number', '').startswith('3.2.') or item.get('number', '') == '3.2')],
                "filtered_count": len([item for item in catalog_items if item.get('level') >= 3 and (item.get('number', '').startswith('3.2.') or item.get('number', '') == '3.2')]),
                "extraction_method": "pywin32_enhanced"
            }
            catalog_result["filtered_count"] = len(catalog_result["filtered_items"])
        except Exception as e:
            log_error(f"PyWin32提取失败: {e}", "pywin32_processor")
            raise Exception(f"目录提取失败: {e}")
        
        catalog_time = time.time() - start_time
        
        # 2. 启动后台标准化任务（顺序执行，避免Word实例冲突）
        session_dir = Path(file_path).parent
        
        # 🔧 修复：使用延迟启动，确保目录提取完全结束后再开始标准化
        async def delayed_standardization():
            """延迟启动标准化，确保目录提取完全结束"""
            # 等待一小段时间，确保当前Word实例完全清理
            await asyncio.sleep(0.5)
            await background_standardize_document(file_path, session_id, session_dir)
        
        # 启动延迟标准化任务
        asyncio.create_task(delayed_standardization())
        log_info("后台标准化已启动（延迟执行，避免实例冲突）", "pywin32_processor")
        
        # 3. 立即返回目录信息
        return {
            "status": "success",
            "catalog_extraction": catalog_result,
            "standardization_status": "processing",
            "timing": {
                "catalog_extraction": catalog_time
            }
        }
        
    except Exception as e:
        log_error(f"并发处理失败: {e}", "pywin32_processor")
        return {
            "status": "error",
            "message": str(e),
            "catalog_extraction": {
                "status": "error",
                "message": str(e),
                "catalog_items": [],
                "filtered_items": []
            },
            "standardization_status": "failed"
        }
    finally:
        # 提取已在独立线程内清理，无需这里再清理（防止引用未定义）
        pass


async def background_standardize_document(file_path: str, session_id: str, session_dir: Path):
    """后台执行文档标准化"""
    try:
        log_info(f"开始后台标准化文档: {file_path}", "pywin32_processor")
        
        # 🔧 修复：使用独立的处理器实例避免Word连接冲突
        # 在线程池中执行，避免异步任务间的Word实例冲突
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def _standardize_in_thread():
            """在独立线程中执行标准化，使用完全独立的Word实例"""
            import pythoncom
            import win32com.client as win32
            import tempfile
            import shutil
            import time
            
            word_app = None
            temp_files = []
            
            try:
                # 🔧 修复1：在新线程中初始化COM
                pythoncom.CoInitialize()
                log_info("线程中COM初始化完成", "pywin32_processor")
                
                # 🔧 修复2：使用DispatchEx创建完全独立的Word实例
                try:
                    # 使用DispatchEx而不是Dispatch，确保创建新的独立实例
                    word_app = win32.DispatchEx("Word.Application")
                    log_info("使用DispatchEx创建独立Word实例", "pywin32_processor")
                except Exception as dispatch_error:
                    log_warning(f"DispatchEx失败，尝试EnsureDispatch: {dispatch_error}", "pywin32_processor")
                    # 如果DispatchEx失败，尝试EnsureDispatch
                    try:
                        word_app = win32.gencache.EnsureDispatch("Word.Application")
                    except Exception as cache_error:
                        log_warning(f"EnsureDispatch也失败，使用普通Dispatch: {cache_error}", "pywin32_processor")
                        word_app = win32.Dispatch("Word.Application")
                
                # 🔧 修复3：确保Word实例完全独立且稳定
                word_app.Visible = False
                word_app.DisplayAlerts = 0
                word_app.ScreenUpdating = False  # 禁用屏幕更新提高性能和稳定性
                log_info("独立Word应用程序配置完成", "pywin32_processor")
                
                # 🔧 修复3：处理文档路径，避免中文路径问题
                original_path = Path(file_path)
                if len(str(original_path.absolute())) > 200 or not str(original_path).isascii():
                    # 创建临时副本
                    temp_dir = tempfile.mkdtemp()
                    temp_filename = f"temp_standardize_{int(time.time())}.docx"
                    temp_path = os.path.join(temp_dir, temp_filename)
                    shutil.copy2(file_path, temp_path)
                    temp_files.append(temp_path)
                    working_path = temp_path
                    log_info(f"创建标准化临时副本: {temp_path}", "pywin32_processor")
                else:
                    working_path = str(original_path.absolute())
                
                # 🔧 修复4：安全打开文档
                try:
                    doc = word_app.Documents.Open(working_path, ReadOnly=False)
                    log_info(f"文档打开成功: {working_path}", "pywin32_processor")
                except Exception as open_error:
                    log_error(f"打开文档失败: {open_error}", "pywin32_processor")
                    raise open_error
                
                # 🔧 修复5：执行标准化 - 使用索引而不是直接迭代
                standardized_count = 0
                try:
                    paragraphs_count = doc.Paragraphs.Count
                    log_info(f"找到 {paragraphs_count} 个段落需要处理", "pywin32_processor")
                    
                    # 使用索引迭代，因为Word COM的Paragraphs集合不支持直接迭代
                    for i in range(1, paragraphs_count + 1):  # Word使用1基索引
                        try:
                            p = doc.Paragraphs.Item(i)
                            style_name = getattr(p.Range, "Style", None)
                            style_name = getattr(style_name, "NameLocal", style_name) if style_name is not None else None
                            
                            # 检查是否为标题样式
                            if style_name and (("heading" in str(style_name).lower()) or ("标题" in str(style_name))):
                                list_str = str(p.Range.ListFormat.ListString or "").strip()
                                if list_str:
                                    # 在标题文字前插入编号
                                    p.Range.InsertBefore(list_str + " ")
                                    standardized_count += 1
                        except Exception as para_error:
                            log_debug(f"处理段落 {i} 时出错: {para_error}", "pywin32_processor")
                            continue
                    
                    log_info(f"段落处理完成，标准化了 {standardized_count} 个标题", "pywin32_processor")
                    
                except Exception as process_error:
                    log_error(f"处理段落时出错: {process_error}", "pywin32_processor")
                    # 即使处理出错，也尝试保存已处理的部分
                
                # 🔧 修复6：保存到正确的会话目录
                try:
                    # 从文件路径中提取会话ID，构建正确的保存路径
                    if 'uploads' in str(original_path) and 'dynamic' in str(original_path):
                        # 提取会话目录路径
                        path_parts = str(original_path).split(os.sep)
                        if 'configuration' in path_parts:
                            config_idx = path_parts.index('configuration')
                            if config_idx + 1 < len(path_parts):
                                session_id = path_parts[config_idx + 1]
                                # 修复路径指向backend目录下的uploads
                                backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
                                session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
                                session_dir.mkdir(parents=True, exist_ok=True)
                                output_path = str(session_dir / f"standardized_{original_path.name}")
                            else:
                                output_path = str(original_path.parent / f"standardized_{original_path.name}")
                        else:
                            output_path = str(original_path.parent / f"standardized_{original_path.name}")
                    else:
                        output_path = str(original_path.parent / f"standardized_{original_path.name}")
                    
                    doc.SaveAs2(output_path)
                    log_info(f"标准化文档保存成功: {output_path}", "pywin32_processor")
                except Exception as save_error:
                    log_error(f"保存到会话目录失败: {save_error}", "pywin32_processor")
                    # 尝试保存到临时位置作为备用
                    try:
                        import tempfile
                        temp_output = os.path.join(tempfile.gettempdir(), f"standardized_{original_path.name}")
                        doc.SaveAs2(temp_output)
                        output_path = temp_output
                        log_warning(f"文档保存到临时位置: {temp_output}", "pywin32_processor")
                    except Exception as temp_save_error:
                        log_error(f"临时保存也失败: {temp_save_error}", "pywin32_processor")
                        raise temp_save_error
                
                # 🔧 修复7：安全关闭文档
                try:
                    doc.Close(SaveChanges=False)
                    log_debug("文档已关闭", "pywin32_processor")
                except Exception as close_error:
                    log_warning(f"关闭文档时出错: {close_error}", "pywin32_processor")
                
                log_info(f"标准化完成，处理了 {standardized_count} 个标题段落", "pywin32_processor")
                return output_path
                
            except Exception as e:
                log_error(f"独立线程标准化失败: {e}", "pywin32_processor")
                raise e
            finally:
                # 🔧 修复8：确保资源清理 - 按正确顺序
                try:
                    if word_app:
                        # 先尝试关闭所有文档
                        try:
                            for doc in word_app.Documents:
                                try:
                                    doc.Close(SaveChanges=False)
                                except:
                                    pass
                        except:
                            pass
                        
                        # 然后退出Word应用程序
                        try:
                            word_app.Quit()
                            log_debug("独立Word应用程序已关闭", "pywin32_processor")
                        except Exception as quit_error:
                            log_warning(f"Word退出时出错: {quit_error}", "pywin32_processor")
                        
                        word_app = None
                        
                        # 给Word一些时间完全关闭
                        import time
                        time.sleep(0.5)
                        
                except Exception as cleanup_error:
                    log_warning(f"Word清理时出错: {cleanup_error}", "pywin32_processor")
                
                # 清理临时文件
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        temp_dir = os.path.dirname(temp_file)
                        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                            os.rmdir(temp_dir)
                    except Exception as file_cleanup_error:
                        log_warning(f"清理临时文件时出错: {file_cleanup_error}", "pywin32_processor")
                
                # 最后清理COM
                try:
                    pythoncom.CoUninitialize()
                    log_debug("线程中COM已清理", "pywin32_processor")
                except Exception as com_cleanup_error:
                    log_warning(f"COM清理时出错: {com_cleanup_error}", "pywin32_processor")
        
        # 在线程池中执行标准化
        with ThreadPoolExecutor(max_workers=1) as executor:
            standardized_path = await asyncio.get_event_loop().run_in_executor(
                executor, _standardize_in_thread
            )
        
        # 保存标准化状态
        status_file = session_dir / "standardization_status.json"
        
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump({
                "status": "completed",
                "standardized_path": standardized_path,
                "completion_time": time.time()
            }, f, ensure_ascii=False, indent=2)
        
        log_info(f"会话 {session_id} 的文档标准化完成: {standardized_path}", "pywin32_processor")
        
    except Exception as e:
        log_error(f"后台标准化失败: {e}", "pywin32_processor")
        
        # 保存错误状态
        status_file = session_dir / "standardization_status.json"
        
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump({
                "status": "failed", 
                "error": str(e),
                "completion_time": time.time(),
                "note": "PyWin32标准化失败，无回退方法"
            }, f, ensure_ascii=False, indent=2)


# 检测PyWin32可用性
def check_pywin32_availability() -> bool:
    """检测PyWin32是否可用"""
    return PYWIN32_AVAILABLE


# 模块初始化
if PYWIN32_AVAILABLE:
    log_info("PyWin32可用，将使用增强的文档处理功能", "pywin32_processor")
else:
    log_warning("PyWin32不可用，将使用原有的spire_doc方法", "pywin32_processor") 