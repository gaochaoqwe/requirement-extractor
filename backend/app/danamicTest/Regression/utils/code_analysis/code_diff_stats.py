
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 该模块代码的主要主要功能是统计两个文件夹下所有代码的差异行数
# 如果存在删除代码，则全部进入代码差异
# 如果有新增代码也全部进入代码差异
# 如果某行存在代码变更，则只记一行代码差异。
import os
import difflib

#函数功能：返回两个文件下代码的差异信息。
from .func_Affected import unique_elements, read_files


def compare_files(file1_path, file2_path):
    with open(file1_path, "r", encoding="utf-8", errors='ignore') as file1, open(file2_path, "r", encoding="utf-8",errors='ignore') as file2:
        lines1 = [line.strip() for line in file1 if line.strip() != '']
        lines2 = [line.strip() for line in file2 if line.strip() != '']
    diff = difflib.unified_diff(lines1, lines2)
    return diff
#函数功能: 计算两本代码发生了多少行代码的变异
#函数输入：代码差异信息
#函数输出：代码差异行数

def count_special_lines(diff_lines):
    plus_count =  0
    minus_count = 0
    flag=0                                                                      #用来表示是否不相同的代码了(0表示未出现，1表示出现)
    line_temp=[]
    flag_exist=0
    for line in diff_lines:
        if line.startswith('++') or line.startswith('--'):
            pass  # 跳过以--或++开头的行
        elif line.startswith('-'):
            if '//'not in line:                                                #如果该行的是注释就跳过，不进行统计。
                line_temp.append(line[1:])
                minus_count += 1
                flag = 1
        elif line.startswith('+'):
            if '//' not in line:                                               #如果该行的是注释就跳过，不进行统计。
                if flag == 1:
                    len_temp = len(line)              # 当前行数据的长度
                    str = line[1:int(len_temp / 2)]
                    for item in line_temp:            # 判断该行差异是新差异还是已有差异
                        if str in item:
                            flag_exist = 1
                    if flag_exist == 1:
                        flag_exist = 0
                    else:
                        plus_count += 1
                else:
                    plus_count += 1
                flag = 1
        else:
            flag = 0
    return plus_count, minus_count

# target_folder_left =  "D:/baxiang_ceshi/CODE_Copy/left"
# target_folder_right = "D:/baxiang_ceshi/CODE_Copy/right"
# 函数功能：统计两个文件夹下所有代码的差异行数
# 函数输入：两个文件夹的路径
# 函数输出：两个文件夹下代码的差异行数，具体包括：（1）同名文件的代码差异行数    （2）左侧文件独有的代码差异行数    （3）右侧文件独有代码差异行数
def special_lines(folder1, folder2):
    if  '/' not in folder1 or '/' not in folder2:
        return 0
    # （1）文件名的读取
    c_cpp_files_left =  [file for file in os.listdir(folder1) if file.endswith(".c") or file.endswith(".cpp") or file.endswith(".h")]  # 读取左侧文件夹里面C或者C++文件的名字:['calculator.cpp', 'calculator.h', 'dayin.cpp', 'dayin.h', 'shuzhijisuan.cpp']
    c_cpp_files_right = [file for file in os.listdir(folder2) if file.endswith(".c") or file.endswith(".cpp") or file.endswith(".h")]  # 读取右侧文件夹里面C或者C++文件的名字
    cpp_h_left, cpp_h_right = unique_elements(c_cpp_files_left,c_cpp_files_right)     # 获取左侧和右侧文件夹中各自独有的文件名 :cpp_h_left=['haha.cpp'],cpp_h_right=['peizhi.cpp']
    c_cpp_files_left = [item for item in c_cpp_files_left if item not in cpp_h_left]  # 获取左右文件中同名文件的路径
    # （2）统计变量初始化
    total_plus = 0
    total_minus = 0                                           #同名文件变更行数
    left_du_hang=0
    right_du_hang=0
    # （3）开始统计
    # 3.1 同名文件统计
    for file_name in c_cpp_files_left:
        file1_path = os.path.join(folder1, file_name)
        file2_path = os.path.join(folder2, file_name)
        if os.path.exists(file2_path):
            diff_lines = compare_files(file1_path, file2_path)
            plus, minus= count_special_lines(diff_lines)             #统计两个文件中代码差异的行数。
            total_plus += plus
            total_minus += minus
    tongming_hangshu=total_plus+total_minus                          # 统计两个文件夹中代码差异的行数(文件名相同的代码)
    # 3.2 左侧独有文件统计
    for cpp_h_left_item in cpp_h_left:                               # cpp_h_left_item：左侧代码独有的文件名： 例：'haha.cpp'
        file1_path_left_du = os.path.join(folder1, cpp_h_left_item)  # 左侧独有代码的路径
        diff_left_du = read_files(file1_path_left_du)                # 读取左侧独有文件中的内容（读取的同时对空格和注释进行剔除）
        left_du_hang=left_du_hang+len(diff_left_du)
    # 3.3 右侧独有文件统计
    for cpp_h_right_item in cpp_h_right:
        file2_path_right_du = os.path.join(folder2, cpp_h_right_item)
        diff_right_du = read_files(file2_path_right_du)
        right_du_hang=right_du_hang+len(diff_right_du)
    # 3.4 统计结果
    total_special_lines_final = tongming_hangshu+left_du_hang+right_du_hang
    return total_special_lines_final