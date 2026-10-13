try:
    from ..logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

#  该模块主要用于对全局变量进行处理


# 函数功能：寻找数组中的某个元素在文本中的位置
# 函数输入：
#        file_path：       文本位置
#        elements_to_find：数组
#函数输出：
#        输出一个字典包含元素的名称，以及元素在文本中的位置
def find_elements_in_text(file_path, elements_to_find):
    try:
        with open(file_path, 'r', errors='ignore') as file:
            lines = file.readlines()
        found_lines = {}  # 用于存储找到的元素及其行号
        for element in elements_to_find:
            if '(' in element or ')' in element:
                continue
            if element.isdigit():
                continue
            for line_num, line in enumerate(lines, start=1):
                if element in line:
                    if element in found_lines:
                        found_lines[element].append(line_num)
                    else:
                        found_lines[element] = [line_num]
        return found_lines
    except FileNotFoundError:
        from pathlib import Path
        log_info(f"File '{file_path}' not found.", Path(__file__).stem)


# 找出两个列表中不同的元素
# 输入：两个列表
# 例子：
# list1 = ['int aaaaa = 1000','bbbbbb = 200','ccbbb = 5000','ddddd=20;']
# list2 = ['int aaaaa = 1000','bbbbbb = 200','ccbbb = 15000;']
# 输出：['ccbbb = 5000', 'ddddd=20;']
def find_different_elements(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    # 使用对称差集（symmetric difference）找到不同的元素
    different_elements = list(set1.symmetric_difference(set2))
    return different_elements


# 函数功能：查找变量的变化
# 输入：
#old_list = ['int aaaaa = 1000, bbbbbb = 200, ccbbb = 5000, ddddd=20;']
#new_list = ['int aaaaa = 1000, bbbbbb = 200, ccccbbb = 15000;']
# 输出：发生变化的变量： ['ccbbb', 'ddddd', 'ccccbbb']
#
def find_variable_changes(old_list, new_list):
    bianliang_fenxi_fianl=[]
    old_list = old_list[0].split(',')
    new_list = new_list[0].split(',')
    bianliang_flag=find_different_elements(old_list, new_list)     #找出两个列表中不同的元素  :['ccbbb = 5000', 'ddddd=20;']
    for item in bianliang_flag:
        if '=' in item:
            item= item.split('=')[0]
            item=item.strip()
            item= item.split(' ')[-1]
            bianliang_fenxi_fianl.append(item)
        else:
            bianliang_fenxi_fianl.append(item)
    bianliang_fenxi_fianl=list(set(bianliang_fenxi_fianl))
    return bianliang_fenxi_fianl

# 函数功能：将两个列表中相同的元素和不同的元素分别存储在两个数组中
# unique_elements： list1中不在list2中的元素以及list2中不在list1中的元素
# common_elements： list1和list2中都存在的元素
def diff_and_common_elements(list1, list2):
    unique_elements = []
    common_elements = []
    # 寻找不同和相同的元素
    for item in list1:
        if item not in list2 and item not in unique_elements:
            unique_elements.append(item)
        elif item in list2 and item not in common_elements:
            common_elements.append(item)
    for item in list2:
        if item not in list1 and item not in unique_elements:
            unique_elements.append(item)
        elif item in list1 and item not in common_elements:
            common_elements.append(item)

    return unique_elements, common_elements

#函数功能：从表达式中查找变量名称
#输入：表达式:definition           'sdf int localVar =10, bbb = 20,ddfdfdfd=20'
#输出：变量名:                       ['localVar', 'bbb', 'ddfdfdfd']
def extract_variable_name(definition_string):
    if len(definition_string)==0:                             # 如果定义为空
        return []
    # 1、在提取变量名之前先去掉注释
    if '//' in definition_string:
        delimiter = '//'
        definition_1 = definition_string.split(delimiter)[0]
    elif '/*' in definition_string:
        delimiter = '/*'
        definition_1 = definition_string.split(delimiter)[0]
    else:
        definition_1 = definition_string
    # 2、判断是全局变量还是宏
    if definition_1.startswith('#define'):  # 如果该行是宏定义
        parts = definition_1.split()
        # 找到第一个非空的部分，这应该是标识符
        for part in parts:
            if part != "#define":
                identifier = part
                return [identifier]
    else:  # 如果该行是全局变量
        # 如果同一行出现多个变量
        variable_name_final_final = []
        if ',' in definition_1:
            variable_names = definition_1.split(',')
            for var in variable_names:
                var = var.strip()
                if '=' in var:
                    variable_name = var.split('=')[0]
                else:
                    variable_name = var
                if ';' in variable_name:
                    variable_name = variable_name.split(';')[0]
                if len(variable_name.split()) > 1:
                    variable_name_final = variable_name.split()[-1]
                else:
                    variable_name_final = variable_name
                if '[' in variable_name_final:                                 # 提取数组的数组名
                    variable_name_final = variable_name_final.split('[')[0]
                variable_name_final=variable_name_final.strip()                # 防止变量前后存在空格
                variable_name_final_final.append(variable_name_final)
            variable_name_final_final1 = [s for s in variable_name_final_final if any(char.isalpha() for char in s)]
            return variable_name_final_final1  # 返回一个列表
        else:  # 如果一行只有一个变量
            if '=' in definition_1:
                variable_name = definition_1.split('=')[0]
            else:
                variable_name = definition_1
            variable_name_final = variable_name.split()[-1]
            variable_name_final_final = variable_name_final.replace(';', '')
            return [variable_name_final_final]  # 返回一个列表
# 函数功能:从列表中查询包含固定字符串的元素
# lst: 列表
# query_string: 固定字符串
def find_elements_containing_string(lst, query_string):
    matching_elements = [element for element in lst if query_string in element]
    if len(matching_elements)>1:
        return [matching_elements[0]]
    else:
        return matching_elements

# 函数功能：找出列表1中与列表2相同的元素
# 输入：两个列表
# 输出：相同的元素列表
# 例：输入：['zhang]    ['zhang11]
# 输出：['zhang']
def find_common_elements(list1, list2):
    matching_elements=[]
    for item in list1:
        for item2 in list2:
            if item in item2:
                matching_elements.append(item)
    return matching_elements

# 函数功能:分析哪些全局变量发生了变化(对冗余变量进行删除),当发现某行发生变化时,要精确的确定这一行中的哪个变量发生了变化
# quanju_bianliang_left:  左侧代码变异的全部的全局变量 : ['int* quanju_flag =20', 'int aaaaa, bbbbbb[1] = 200, ccbbb = 5000,ddddd=20;']
# quanju_bianliang_right: 右侧代码变异的全部的全局变量 : ['int* quanju_flag =20', 'int aaaa, bbbbbb[1] = 201, ccccbbb = 15000;']
# 函数输出：
# ['ccccbbb', 'quanju_flag', 'ccbbb', 'ddddd']

def quanju_chuli_quchu_rongyu(quanju_bianliang_left,quanju_bianliang_right):
    left_quanju_chushi  = []                                         # 包含了左侧代码变异的全部的全局变量
    right_quanju_chushi = []                                         # 包含了右侧代码变异的全部的全局变量
    final_jieguo=[]
    for item in quanju_bianliang_left:
        temp_list = extract_variable_name(item)                      #从字符串中提取变量名
        if len(temp_list)==0:
            pass
        else:
            left_quanju_chushi = left_quanju_chushi + temp_list          #包含了左侧代码变异的全部的全局变量: ['quanju_flag', 'aaaaa', 'bbbbbb[1]', 'ccbbb', 'ddddd']
    for item in quanju_bianliang_right:
        temp_list = extract_variable_name(item)                          # 从字符串中提取变量名
        if len(temp_list)==0:
            pass
        else:
            right_quanju_chushi = right_quanju_chushi + temp_list        # 包含了右侧代码变异的全部的全局变量:['quanju_flag', 'aaaa', 'bbbbbb[1]', 'ccccbbb']
        right_quanju_chushi = right_quanju_chushi + temp_list            # 包含了右侧代码变异的全部的全局变量:['quanju_flag', 'aaaa', 'bbbbbb[1]', 'ccccbbb']
        #  log_info(str(unique_elements), Path(__file__).stem):['aaaaa', 'ccbbb', 'ddddd', 'aaaa', 'ccccbbb']
        #  log_info(str(common_elements), Path(__file__).stem):['quanju_flag', 'bbbbbb[1]']
    unique_elements, common_elements = diff_and_common_elements(left_quanju_chushi, right_quanju_chushi)   # 计算两个列表中相同的元素和不同的元素(判断哪些是增加和删除的变量,哪些是变量的值发生的变化)
    # 左右两侧的变量名相同则继续分析是否发生变化:common_elements
    jihe_quanju_comin=[]
    for item in common_elements:
        left_hang_neirong=find_elements_containing_string(quanju_bianliang_left  ,item)                    #找到共同变量所在的行内容：['int aaaaa = 1000, bbbbbb = 200, ccbbb = 5000,ddddd=20;']
        right_hang_neirong=find_elements_containing_string(quanju_bianliang_right,item)                    #找到共同变量所在的行内容：['int aaaaa = 1000, bbbbbb = 200, ccccbbb = 15000;']
        bianhuan_temp=find_variable_changes(left_hang_neirong,right_hang_neirong)                          #最终分析出来的变化的变量名：bianhuan_temp=['ccccbbb', 'ccbbb', 'ddddd']
        jihe_quanju_comin=jihe_quanju_comin+bianhuan_temp
        jihe_quanju_comin=list(set(jihe_quanju_comin))                                                     #列表内容去重
    final_quanju_fenxi=jihe_quanju_comin+unique_elements                                                   #
    final_quanju_fenxi=list(set(final_quanju_fenxi))                                                       #列表内容去重
    for item in final_quanju_fenxi:                                                                        #对数组进行处理提取变量名:aa[3]    提取结果为：aa
        item = item.split(' ')
        if len(item)>1:
            item = item[-1]
        else:
            item = item[0]
        if '[' in item:
            item = item.split('[')[0]
            final_jieguo=final_jieguo+[item]
        else:
            final_jieguo=final_jieguo+[item]
    final_jieguo=list(set(final_jieguo))
    left_quanju_fianl_ =find_common_elements(final_jieguo,left_quanju_chushi)    # 左侧代码变异的全部的全局变量: ['int* quanju_flag =20', 'int aaaaa, bbbbbb[1] = 200, ccbbb = 5000,ddddd=20;']
    right_quanju_fianl_=find_common_elements(final_jieguo,right_quanju_chushi)   # 右侧代码变异的全部的全局变量: ['int* quanju_flag =20', 'int aaaa, bbbbbb[1] = 201, ccccbbb = 15000;']
    return left_quanju_fianl_,right_quanju_fianl_
