
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 该模块的主要功能是进行软件信息统计，主要包括软件的行数、软件空白行数、软件注释行数等。

import os
import re

# 函数功能：统计代码文件中的总行数、注释行数、空白行数和有效代码行数。
# 输入：代码文件的文本内容，以列表形式表示，每个元素为文件的一行文本。
# 输出：一个包含四个整数的元组，分别表示总行数、注释行数、空白行数和有效代码行数。
from .func_Affected import unique_elements


def count_lines(lines):
    total_lines = len(lines)
    comment_lines = 0                     # 注释行数（纯注释不含代码）  /**/  //dfdfdf
    false_comment_lines = 0               # 无效代码行数（有些注释是为了屏蔽代码对这部分不统计在内）
    coment_lines_com=0                    # 代码与注释在同一行中      int a=10;  //变量赋值
    blank_lines = 0                       # 空白行数
    in_comment_block = False
    for line in lines:
        stripped_line = line.strip()              #去除空白行。
        if stripped_line.startswith("/*") and stripped_line.endswith("*/"):
            comment_lines += 1
            if all(ord(char) < 128 for char in line):            # 判断该行注释是不是全英文的，如果是全英文的就认为是无效注释
                false_comment_lines=false_comment_lines+1
        elif stripped_line.startswith("/*"):
            in_comment_block = True
            comment_lines += 1
            if all(ord(char) < 128 for char in line):            # 判断该行注释是不是全英文的，如果是全英文的就认为是无效注释
                false_comment_lines=false_comment_lines+1
        elif stripped_line.endswith("*/") and in_comment_block:
            in_comment_block = False
            comment_lines += 1
            if all(ord(char) < 128 for char in line):            # 判断该行注释是不是全英文的，如果是全英文的就认为是无效注释
                false_comment_lines=false_comment_lines+1
        elif in_comment_block or stripped_line.startswith("//"):
            comment_lines += 1
            if all(ord(char) < 128 for char in line):            # 判断该行注释是不是全英文的，如果是全英文的就认为是无效注释
                false_comment_lines=false_comment_lines+1
        elif "//" in stripped_line:  # 检查行内是否包含 //
            coment_lines_com += 1
            if all(ord(char) < 128 for char in line):            # 判断该行注释是不是全英文的，如果是全英文的就认为是无效注释
                false_comment_lines=false_comment_lines+1
        elif not stripped_line:
            blank_lines += 1
    effective_lines = total_lines - blank_lines-comment_lines            # 有效代码行数（注释行和空白行不计算在内）
    comment_lines=comment_lines+coment_lines_com                         # 注释行数（包含代码注释与函数前注释）
    youxiao_comment_lines=comment_lines-false_comment_lines
    return total_lines, comment_lines,youxiao_comment_lines ,blank_lines, effective_lines
# 函数功能：统计指定文件夹下的C/C++代码文件的总行数、注释行数、空白行数和有效代码行数。
# 输入：文件夹路径folder_path，包含C/C++代码文件的文件夹路径。
# 输出：一个包含五个整数的元组，分别表示总行数、注释行数、有效注释行数、空白行数和有效代码行数。
def ruanjianxixin_tongji(folder_path):
    if not os.path.isdir(folder_path):  # 如果提供的路径不是文件夹
        return 0, 0, 0, 0, 0  # 返回(0, 0, 0, 0, 0)，表示无效路径
    # 使用列表推导式获取所有符合条件的C/C++文件
    # 这些路径应该从调用者传入，这里使用默认值
    target_folder_left = folder_path  # 使用传入的路径
    target_folder_right = folder_path  # 使用传入的路径
    c_cpp_files_left  = [file for file in  os.listdir(target_folder_left)  if file.endswith(".c") or file.endswith(".cpp") or file.endswith(".h") or file.endswith(".H")]  # 读取左侧文件夹里面C或者C++文件的名字:['calculator.cpp', 'calculator.h', 'dayin.cpp', 'dayin.h', 'shuzhijisuan.cpp']
    c_cpp_files_right = [file for file in  os.listdir(target_folder_right) if file.endswith(".c") or file.endswith(".cpp") or file.endswith(".h") or file.endswith(".H")]  # 读取右侧文件夹里面C或者C++文件的名字
    cpp_h_left, cpp_h_right = unique_elements(c_cpp_files_left, c_cpp_files_right)                                            # 获取左侧和右侧文件夹中各自独有的文件名 :cpp_h_left=['haha.cpp'],cpp_h_right=['peizhi.cpp']
    c_cpp_files_left_    = [os.path.join(root, file) for root, dirs, files in os.walk(target_folder_left)  for file in files if file.endswith(".c") or file.endswith(".cpp") or file.endswith(".h")]
    c_cpp_files_right_du_= [os.path.join(root, file) for root, dirs, files in os.walk(target_folder_right) for file in files if file in cpp_h_right]
    c_cpp_files_final=c_cpp_files_left_+c_cpp_files_right_du_
    all_lines = []                 # 存储所有文件的行
    total_lines = 0                # 总行数
    comment_lines = 0              # 注释行数
    youxiao_comment_lines=0
    blank_lines = 0                # 空行数
    effective_lines = 0            # 有效代码行数
    for file_path in c_cpp_files_final:      # 遍历所有C/C++文件
        with open(file_path, "r", errors='ignore') as file:  # 打开文件，忽略编码错误
            file_lines = file.readlines()    # 读取文件的所有行
            all_lines.extend(file_lines)      # 将文件行添加到所有行列表
            file_total, file_comment,file_true_comment, file_blank, file_effective = count_lines(file_lines)  # 统计文件行数
            total_lines += file_total         # 更新总行数
            comment_lines += file_comment      # 更新注释行数
            youxiao_comment_lines=youxiao_comment_lines+file_true_comment
            blank_lines += file_blank  # 更新空行数
            effective_lines += file_effective  # 更新有效代码行数
    return total_lines, comment_lines,youxiao_comment_lines, blank_lines, effective_lines  # 返回统计结果
