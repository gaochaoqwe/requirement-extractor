#!/usr/bin/env python3
"""
调试日志工具模块
专门处理需求分析过程中的调试日志记录和分析

功能包括：
- 需求规格内容日志记录
- 原始内容日志记录
- 目录内容日志记录
- 格式化日志输出
"""

from typing import List
from pathlib import Path

# 导入日志工具
try:
    from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_debug, log_warning
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_debug, log_warning


class DebugLogger:
    """调试日志记录器"""
    
    def __init__(self):
        """初始化日志记录器"""
        self.max_log_lines = 50  # 最大日志行数
        self.max_line_length = 100  # 每行最大长度
    
    def log_requirement_spec_content(self, file_path: str, content: str):
        """
        记录需求规格说明文档的内容（调试用）
        
        Args:
            file_path: 文件路径
            content: 文档内容
        """
        # log_info(f"开始记录需求规格说明文档内容: {file_path}", "debug_logger")
        
        if not content.strip():
            # log_warning("文档内容为空", "debug_logger")
            return
        
        # 分行并限制日志数量
        lines = content.split('\n')
        total_lines = len(lines)
        non_empty_lines = [line for line in lines if line.strip()]
        
        # log_info(f"文档统计 - 总行数: {total_lines}, 非空行数: {len(non_empty_lines)}", "debug_logger")
        
        # 记录前几行内容用于调试
        sample_lines = non_empty_lines[:self.max_log_lines]
        # log_debug("=== 需求规格说明文档内容样本 ===", "debug_logger")
        
        for i, line in enumerate(sample_lines, 1):
            truncated_line = self._truncate_line(line)
            # log_debug(f"第{i}行: {truncated_line}", "debug_logger")
        
        if len(non_empty_lines) > self.max_log_lines:
            # log_debug(f"... 省略了 {len(non_empty_lines) - self.max_log_lines} 行内容", "debug_logger")
        
            pass
        # log_debug("=== 需求规格说明文档内容样本结束 ===", "debug_logger")
    
    def log_original_content(self, non_empty_lines: List[str]):
        """
        记录原始内容（用于调试）
        
        Args:
            non_empty_lines: 非空行列表
        """
        # log_info(f"记录原始内容，共 {len(non_empty_lines)} 行", "debug_logger")
        
        if not non_empty_lines:
            # log_warning("没有非空行内容", "debug_logger")
            return
        
        # log_debug("=== 原始文档内容（非空行）===", "debug_logger")
        
        # 记录前几行内容
        sample_lines = non_empty_lines[:self.max_log_lines]
        for i, line in enumerate(sample_lines, 1):
            truncated_line = self._truncate_line(line)
            # log_debug(f"原始第{i}行: {truncated_line}", "debug_logger")
        
        if len(non_empty_lines) > self.max_log_lines:
            # log_debug(f"... 省略了 {len(non_empty_lines) - self.max_log_lines} 行原始内容", "debug_logger")
        
            pass
        # log_debug("=== 原始文档内容结束 ===", "debug_logger")
    
    def log_catalog_content(self, file_path: str, content: str):
        """
        记录目录文档的内容（调试用）
        
        Args:
            file_path: 文件路径
            content: 目录内容
        """
        # log_info(f"开始记录目录文档内容: {file_path}", "debug_logger")
        
        if not content.strip():
            # log_warning("目录内容为空", "debug_logger")
            return
        
        # 分行处理
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # log_info(f"目录统计 - 总行数: {len(lines)}, 非空行数: {len(non_empty_lines)}", "debug_logger")
        
        # 记录目录结构
        # log_debug("=== 目录文档内容样本 ===", "debug_logger")
        
        sample_lines = non_empty_lines[:self.max_log_lines]
        for i, line in enumerate(sample_lines, 1):
            truncated_line = self._truncate_line(line)
            # log_debug(f"目录第{i}行: {truncated_line}", "debug_logger")
        
        if len(non_empty_lines) > self.max_log_lines:
            # log_debug(f"... 省略了 {len(non_empty_lines) - self.max_log_lines} 行目录内容", "debug_logger")
        
            pass
        # log_debug("=== 目录文档内容样本结束 ===", "debug_logger")
    
    def log_processing_summary(self, file_path: str, sections_found: int, requirements_matched: int):
        """
        记录处理摘要信息
        
        Args:
            file_path: 处理的文件路径
            sections_found: 找到的章节数
            requirements_matched: 匹配的需求数
        """
        # log_info("=== 处理摘要 ===", "debug_logger")
        # log_info(f"文件路径: {file_path}", "debug_logger")
        # log_info(f"识别章节数: {sections_found}", "debug_logger")
        # log_info(f"匹配需求数: {requirements_matched}", "debug_logger")
        # log_info("=== 处理摘要结束 ===", "debug_logger")
    
    def log_section_analysis(self, sections: List[dict]):
        """
        记录章节分析结果
        
        Args:
            sections: 章节列表
        """
        if not sections:
            # log_warning("没有找到任何章节", "debug_logger")
            return
        
        # log_info(f"章节分析结果，共找到 {len(sections)} 个章节", "debug_logger")
        # log_debug("=== 章节分析详情 ===", "debug_logger")
        
        for i, section in enumerate(sections[:10], 1):  # 只显示前10个章节
            heading = section.get('heading', '未知标题')
            content_length = len(section.get('content', ''))
            level = section.get('level', 0)
            
            truncated_heading = self._truncate_line(heading)
            # log_debug(f"章节{i}: [{level}级] {truncated_heading} (内容长度: {content_length})", "debug_logger")
        
        if len(sections) > 10:
            # log_debug(f"... 省略了 {len(sections) - 10} 个章节", "debug_logger")
        
            pass
        # log_debug("=== 章节分析详情结束 ===", "debug_logger")
    
    def log_requirement_matching_result(self, req_name: str, found: bool, details: dict = None):
        """
        记录需求匹配结果
        
        Args:
            req_name: 需求名称
            found: 是否找到匹配
            details: 匹配详情（可选）
        """
        status = "✓ 找到" if found else "✗ 未找到"
        # log_info(f"需求匹配: {status} - {req_name}", "debug_logger")
        
        if found and details:
            # 记录匹配详情的摘要
            description = details.get('description', '')[:50]
            if description:
                # log_debug(f"  描述摘要: {description}...", "debug_logger")
                pass
        elif not found:
            # log_warning(f"  未能在文档中找到需求: {req_name}", "debug_logger")
    
            pass
    def _truncate_line(self, line: str) -> str:
        """
        截断过长的行以适应日志显示
        
        Args:
            line: 原始行内容
            
        Returns:
            截断后的行内容
        """
        if not line:
            return ''
        
        line = line.strip()
        if len(line) <= self.max_line_length:
            return line
        
        return line[:self.max_line_length] + "..."
    
    def log_error_with_context(self, error_msg: str, context: dict = None):
        """
        记录带有上下文信息的错误
        
        Args:
            error_msg: 错误消息
            context: 上下文信息（可选）
        """
        # log_error(f"错误: {error_msg}", "debug_logger")
        
        if context:
            # log_error("错误上下文:", "debug_logger")
            for key, value in context.items():
                # log_error(f"  {key}: {value}", "debug_logger")
    
                pass
    def log_performance_info(self, operation: str, duration: float, items_processed: int = None):
        """
        记录性能信息
        
        Args:
            operation: 操作名称
            duration: 持续时间（秒）
            items_processed: 处理的项目数（可选）
        """
        # log_info(f"性能统计 - {operation}: {duration:.2f}秒", "debug_logger")
        
        if items_processed is not None:
            rate = items_processed / duration if duration > 0 else 0
            # log_info(f"  处理项目数: {items_processed}, 处理速率: {rate:.2f}项/秒", "debug_logger")


# 创建全局实例
debug_logger = DebugLogger() 