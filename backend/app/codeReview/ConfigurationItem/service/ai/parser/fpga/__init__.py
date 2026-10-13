"""
FPGA代码解析器模块

提供Verilog HDL和VHDL代码的解析功能
"""

from .fpga_parser import extract_fpga_files_from_code

__all__ = ['extract_fpga_files_from_code'] 