
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

#模块功能：统计变更的代码影响到了哪些函数
import json
import os
import difflib
#函数功能：返回代码的差异信息
from .func_place_mokuai import Function_place_jubu
from .hanshuguanxi import  Function_relationship, Function_relationship_place, func_called_and_call_ship
# 删除注释及空行后进行比较
from .hanshupanduan import find_functions, replace_elements
from .quanju_bianliang_chuli import find_elements_in_text, extract_variable_name, quanju_chuli_quchu_rongyu

In_zhushi_flag=0                                                                  #用于判断该行是否在注释中
# 函数功能：将注释内容替换为 /**/，以实现注释的移除。
def remove_comments(line):
    line=line.strip()                                                             #去除空白行
    global In_zhushi_flag
    if line.startswith('/*')  and line.endswith('*/'):                            #识别：/*******/
        line = '/**/'
    elif line.startswith('/*'):                                                   #多行注释开始标志:/*
        line = '/**/'
        In_zhushi_flag = 1
    elif line.endswith('*/'):
        line = '/**/'
        In_zhushi_flag = 0
    elif In_zhushi_flag==1:
        line = '/**/'
    elif '//' in line:
        if len(line.split('//'))>1:
            line=line.split('//')[0]
        else:
            line='/**/'
    return line

# 函数功能：比较两个文件的内容
# 函数输入：两个文件路径
# 函数输出：差异信息
def compare_files(file1_path, file2_path):
    with open(file1_path, "r", encoding="utf-8", errors='ignore') as file1, open(file2_path, "r", encoding="utf-8",errors='ignore') as file2:
        lines1 = [remove_comments(line) for line in file1 if len(remove_comments(line))>1]
        lines2 = [remove_comments(line) for line in file2 if len(remove_comments(line))>1]
    differ = difflib.Differ()
    diff = list(differ.compare(lines1, lines2))
    return diff

# 函数功能：判断字符串是否包含字母
# 输入：字符串
# 输出：布尔值
# 例：contains_letter("12345")    # 输出 False
# 例：contains_letter("abc123")   # 输出 True
# 例：contains_letter("!@#$a%")  # 输出 False
def contains_letter(input_string):
    return any(char.isalpha() for char in input_string)

# 函数功能：将字典列表中的值合并成一个数组
# 函数输入：字典列表           :
# 函数输出：合并后的数组        :
def extract_pairs_from_list_of_dicts(list_of_dicts):
    pairs_array = []
    for dictionary in list_of_dicts:
        for key, value in dictionary.items():
            if len(value[0]) > 0:                  # 函数不为空
                if contains_letter(value[0]):      # 去除异常函数名
                    pairs_array.append(value[0])
    return pairs_array

# 去除字典中包含include的减值对
# 函数输入：
#     element_positions: 字典，包含所有元素的位置信息        {”include”: [1, 2, 3]},"case 'a':": [15], 'std::cout << "有点力" << std::endl;': [24]
# 函数输出：
#     clean_elements: 去除include的字典                  {"case 'a':": [15], 'std::cout << "有点力" << std::endl;': [24]
def remove_include_keys(element_positions):
    clean_elements = {key: value for key, value in element_positions.items() if 'include' not in key}
    return clean_elements


#函数功能:查找代码的位置差异代码的位置
#函数输入：
#         file1_path:原始代码路径
#         line_temp :差异代码信息
#函数输出： 返回一个字典，字典的键是差异代码，信息字典的值对应的是代码的位置。
def find_function_diff(file1_path,line_temp):
    with open(file1_path, "r", encoding="utf-8", errors='ignore') as file1:    #打开文件
        lines= [line.strip() for line in file1 ]     # 读取代码信息，逐行读取
    if len(line_temp) == 0:
        return {}
    element_positions = {}                           # 创建一个字典来存储元素和位置信息
    for key, value in line_temp.items():
        if len(key)==0:
            continue
        value= [x for x in value if x != 'None']     # 证明该代码为文件的首位置
        find_flag1 = 0
        find_flag2 = 0
        if len(value)==0:
            for index,element in enumerate(lines):
                if key == element:
                    element_positions[key] = [index]
                    break
        if len(value) == 1:
            for index,element in enumerate(lines):
                if value[0] == element:
                    find_flag1 = 1
                if find_flag1 == 1:
                    if key == element:
                        element_positions[key] = [index]
                        break
        if len(value) == 2:
            for index,element in enumerate(lines):
                if value[0] in element:
                    find_flag1 = 1
                if value[1] in element:
                    find_flag2 = 1
                if find_flag1 == 1 and find_flag2 == 1:
                    if key in element:
                        element_positions[key] = [index]
                        break
    return element_positions

def find_function_diff_du(file1_path,line_temp):
    with open(file1_path, "r", encoding="utf-8", errors='ignore') as file1:    #打开文件
        lines= [line.strip() for line in file1 ]     # 读取代码信息，逐行读取
    element_positions = {}                           # 创建一个字典来存储元素和位置信息
    for element in line_temp:
        element=element.strip()
        if 'include' in element:                     # 不统计由于头文件内容变化所带来的差异
            continue
        if element == '}' or element == '}':
            continue
        found_in_lines1 = []
        for i, line in enumerate(lines):                    # 在 lines1 中查找元素所在的行
            if element == line:
                found_in_lines1.append(i)                   # 记录元素在文件中的行号
        element_positions[element] = found_in_lines1        # 将元素和位置信息添加到字典中
    return element_positions




# 输出参数：
#         plus_elements :['moveRight();','some text']
#         plus_elements :['None', 'None']
#         plus_elements :['moveRight();','None']

def find_elements_with_num(lst, num):
    if len(lst) ==0 or num == 0:
        return ['None', 'None']
    plus_elements = []
    jishu = 0
    for i in range(num, -1, -1):  # 从列表末尾往前数到指定位置
        if lst[i].startswith('+') or lst[i].startswith('-'):    # 正负号开头的元素不计入
            if i == 0:                                          # 如果已经是最后一个元素，则返回None
                if len(plus_elements)==0:
                     plus_elements.append('None')
                     plus_elements.append('None')
                     return plus_elements
                else:
                    plus_elements.append('None')
                    plus_elements = sorted(plus_elements, key=len, reverse=True)
                    return plus_elements
            else:                                               # 如果不是最后一个元素，则继续往前数
                continue
        else:
            plus_elements.append(lst[i].strip())
            jishu = jishu+1
            if jishu == 2:
                plus_elements=sorted(plus_elements, key=len, reverse=True)
                return plus_elements
            elif i == 0:
                plus_elements.append('None')
                plus_elements = sorted(plus_elements, key=len, reverse=True)
                return plus_elements


# 函数功能：查找代码变异代码及其前两行内容
# 函数输入：
#         diff_lines=diff=['#include <iostream>', '  int password = 0;', '  +void printNumbers(int start, int end) {']
# 函数输出：
#         line_temp_left_final={}
#         line_temp_right_final={'void printNumbers(int start, int end) {': ['#include <iostream>', 'int password = 0;']}
def count_special_lines(diff_lines):
    line_temp_left_dict={}
    line_temp_right_dict={}
    diff_lines=[line.strip() for line in diff_lines]
    for index, line in enumerate(diff_lines):
        if line.startswith('++') or line.startswith('--'):
            pass  # 跳过以--或++开头的行
        elif line.startswith('-'):
            if not (line.startswith('-//') or line.startswith('-}') or line.startswith('-{') or line.startswith('/*')):                                             #如果该行的是注释就跳过，不进行统计。
                line_temp_left=line[1:].strip()
                line_temp_left_dict[line_temp_left]=find_elements_with_num(diff_lines, index)
        elif line.startswith('+'):
            if not (line.startswith('+//') or line.startswith('+}') or line.startswith('+{')or line.startswith('/*')):
                line_temp_right=line[1:].strip()
                line_temp_right_dict[line_temp_right]=find_elements_with_num(diff_lines, index)
    return line_temp_left_dict, line_temp_right_dict


# 函数功能：将二维数组合成为一维数组
# 函数输入：
#        arr：一个多维数组 例如： [[1, 2, 3], [4], [5], 6]
# 函数输出：
#        flattened_array：合并后的一位数组  例如：[1, 2, 3, 4, 5, 6]
def flatten_nested_array(arr):
    flattened_array = []
    for element in arr:
        if isinstance(element, list):
            flattened_array.extend(flatten_nested_array(element))
        else:
            flattened_array.append(element)
    return flattened_array
#  C和c加加的常见函数
# 数据扁平处理
def flatten_list(input_list):
    output_list = []
    for element in input_list:
        if isinstance(element, list):
            output_list.extend(flatten_list(element))
        else:
            output_list.append(element)
    return output_list
# 函数功能：判断字符串中是否包含英文字母
# 输入参数：input_string
# 输出参数：True or False  如果包含英文字母则输出为真，否则输出为假。
def has_english_letters(input_string):
    for char in input_string:
        if char.isalpha():
            return True
    return False

#函数功能：根据函数位置查找该变异代码所影响的函数。
#函数输入：
#       fun_place：函数的位置信息{'tongji();': [5], 'dayin.power();': [6], 'plane();': [46, 53]}
#       Dict：函数字典：[['Calculator.add', 2, 7], ['Calculator.subtract', 11, 14], ['Calculator.multiply', 16, 19], ['Calculator.divide', 21, 25]]
#函数输出：
#       bianyi_effect：函数内部变化及其影响到的函数： {"case 'aa':": ['processInput'], 'int aaaa = quanju_flag;': ['main']}
#       quanju_final：发生变异的全局变量的名称
def find_matching_functions(fun_place, Dict):                            #主要用于存储代码差异影响到了哪些函数
    result_temp = []
    quanju_varible=[]                         #主要用于全局变量的统计
    flag_find = 0
    bianyi_effect={}
    # 遍历fun_place中的键值对
    for key, value in fun_place.items():      #
        # 遍历Dict中的元素                           #判断是否找到对应函数
        if len(key) ==0:                          # 如果没有找到对应函数就跳过
            continue
        elif key.startswith('printf') or key.startswith('puts') or key.startswith('std::'):     # 跳过printf和puts函数
            continue
        for value_temp in value:                   # 遍历该函数的位置信息
            for item in Dict:
                if value_temp >= item[1] and value_temp <= item[2]:
                    result_temp.append(item[0])
                    flag_find = 1                                  # 证明该函数为非全局变量
                    break
        if flag_find == 0:                                         # 如果该变量没有对应的函数就判断该变量为全局变量
            if '(' in key  or ')' in key:                          # 防止将函数声明误认为全局变量声明
                pass
            else:
                quanju_varible.append(key)        # 如果没找到对应函数则证明该变量是全局变量单独对其进行统计
        elif len(result_temp) > 0:
            bianyi_effect[key]=result_temp
            result_temp=[]
        flag_find=0                                            # 循环执行完后及时将标志进行清零
    # 使用集合去除重复值，并返回结果
    quanju_varible=flatten_list(quanju_varible)
    quanju_final = list(set(quanju_varible))                       #全局变量
    quanju_final= [item for item in quanju_final if item!= '']
    return bianyi_effect,quanju_final
# 功能同上主要对全局变量进行查找
# 区别在于对于非全局变量只找到一个其对应的函数即可,对于全局变量可能有多个对应的函数
def find_matching_functions_qunju(fun_place, Dict):
    quanju_final = {}                           # 用于存储代码差异影响到的函数
    yichang_varible = []  # 用于全局变量的统计
    for key, value in fun_place.items():
        result = []                             # 用于存储每个键对应的匹配函数列表
        flag_find = 0
        for value_temp in value:
            for item in Dict:
                if value == []:                 # 如果函数的位置信息为空，直接跳过
                    break
                if value_temp >= item[1] and value_temp <= item[2]:
                    result.append(item[0])
                    flag_find = 1
            if flag_find == 0:
                yichang_varible.append(key) #如果没有找到全局变量影响的函数，证明该函数没有被调用。就将其记录到异常变量中
                quanju_final[key] = ['Without Functions!!!!!!']
            else:
                result=list(set(result))
                quanju_final[key] = result  #
    return quanju_final,yichang_varible


# 读取该文件，并在该文件中追加数据
def write_data_and_increment_line(file_path, data):
    try:
        with open(file_path, 'a') as file:
            file.write(data + '\n')
    except Exception as e:
        log_info(str("发生错误:", e), Path(__file__).stem)
        return None
# 函数功能：将字典的内容写入到文件中。
def write_dict_to_file(file_path,data_dict,num):
    try:
        # 以追加模式打开文件并将字典数据以JSON格式写入文件*\
        with open(file_path, 'a') as file:
            for key, value in data_dict.items():
                    value=value[0]
                    entry = f"{num} {value}          {key}"
                    json.dump(entry, file)
                    file.write('\n')  # 写入换行符以分隔不同的字典数据
    except Exception as e:
        log_info(str("发生错误:", e), Path(__file__).stem)

# 函数功能：将数组写入到一个文件中
def write_array_to_file(file_path,data_array):
    try:
        # 以追加模式打开文件并将数组数据写入文件
        with open(file_path, 'a') as file:
            for item in data_array:
                file.write(str(item) + '\n')
    except Exception as e:
        log_info(str("发生错误:", e), Path(__file__).stem)

# 函数功能：将字典中的键合并成一个字符串
# 函数输入：字典
# 函数输出：合并后的字符串
def merge_keys_as_string(dictionary):
    keys = list(dictionary.keys())  # 获取字典中的键并转换为列表
    merged_keys = ', '.join(keys)  # 使用 ', '.join() 方法将键合并成一个字符串，使用逗号和空格分隔
    return merged_keys

# 函数功能：取两个列表的交集
# 例：输入：list_a = [1, 2, 3, 4, 5]
#         list_b = [3, 4, 5, 6, 7]
#      输出：[3, 4, 5]
def find_unique_elements(list1, list2):
    unique_elements = []
    for item in list1:
        if item not in list2 and item not in unique_elements:
            unique_elements.append(item)
    for item in list2:
        if item not in list1 and item not in unique_elements:
            unique_elements.append(item)
    return unique_elements

# 函数功能：各自返回两个列表中独有的元素
# 输入：两个列表
# 输出：两个列表 中独有的元
# 例： list1 = ['calculator.cpp', 'calculator.h', 'dayin.cpp', 'dayin.h','shuzhijisuan.cpp']
#     list2 = ['calculator.cpp', 'calculator.h', 'dayin.cpp', 'dayin.h','shuzhijisuan.cpp', 'fdfsdsds']
#     unique_list1: []
#     unique_list2: ['fdfsdsds']
def unique_elements(list1, list2):
    unique_list1 = [item for item in list1 if item not in list2]
    unique_list2 = [item for item in list2 if item not in list1]
    return unique_list1, unique_list2

# 函数功能：读取文件中的内容形成一个列表
def read_files(file1_path):
    with open(file1_path, "r", encoding="utf-8", errors='ignore') as file1:
        lines = [remove_comments(line) for line in file1 if line.strip() != '']   #读取文件的内容同时将注释替换为:'/**/'
        lines = [element for element in lines if element != '/**/']
    return lines


# 函数功能：将字典转换为字符串
# 输入：字典     例： {'key1': 'value1', 'key2': 'value2'}
# 输出：字符串   例： key1: value1\n key2: value2\n
def dict_to_string(dictionary):
    result = ""
    length = len(dictionary)
    if length == 0:
        return result
    else:
        num = 1
        max_key_length = max(len(key) for key in dictionary)  # 找到最长的键的长度
        for i, (key, value) in enumerate(dictionary.items()):
            # 使用字符串的rjust方法对齐影响函数的输出
            if i == length - 1:  # Check if it's the last element
                result += '        ' + f"（{num:1d}） 代码变更: {key.ljust(max_key_length)} 影响到的函数为: {value}"
            else:
                result += '        ' + f"（{num:1d}） 代码变更: {key.ljust(max_key_length)} 影响到的函数为: {value}\n"
            num += 1
        max_key_length = 0
        return result

# 函数功能：合并两个字典
# 输入：dict_a = {'a': 1, 'b': 2}，dict_b = {'b': 3, 'c': 4}
# 输出：{'a': 1, 'b': 3, 'c': 4}
def merge_dicts_two(dict1, dict2):
    merged_dict = dict1.copy()
    merged_dict.update(dict2)
    return merged_dict

# 去除字典中的空值
def remove_empty_keys(dictionary):
    return {key: value for key, value in dictionary.items() if len(key)>1}

# 函数功能：过滤列表中的特殊字符 ['?', '\n']
# 输入：['  #include <iostream>', '  int password = 0;','?                 --\n']
# 输出：['  #include <iostream>',' int password = 0;']
def filter_list(diff_list):
    chars_to_remove = ['?', '\n','/**/']
    return [line for line in diff_list if not any(char in line for char in chars_to_remove)]
#函数功能：根据函数位置查找该变异代码所影响的函数。
#函数输入：文件位置
#函数输出：
#    list_left_final=[{'if (start > end) {': ['printNumbersRecursive'], 'return 10;': ['printNumbersRecursive'], 'return 0;': ['plane']}, {'int a= aaaaa;': ['shangdian'], "case 'a':": ['processInput'], 'int a = 1000;': ['main'], 'int dayinx = aaaaa1[0];': ['main']}]
#    list_right_final=[{'if (start > end)': ['printNumbersRecursive'], 'return 0;': ['printNumbersRecursive'], 'return 100;': ['plane']}, {"case 'aa':": ['processInput'], 'int aaaa = quanju_flag;': ['main'], 'int ddd=H / (sin(-Ceta-a));': ['main'], 'int a = 1000, bb = 200,cc=500;': ['main']}, {'void printNumbers() {': ['printNumbers'], 'for (int i = 1; i <= 10; ++i) {': ['printNumbers']}]
#    quanju_left={'aaaaa1': ['main'], '<iostream>': ['Without Functions!!!!!!'], 'ccbbb': ['shangdian', 'main'], 'aaaaa': ['shangdian', 'main'], 'pppp': ['Without Functions!!!!!!']}
#    quanju_right={'<iostream>': ['Without Functions!!!!!!'], 'ccbbb': ['shangdian'], 'aaaaa': ['shangdian'], 'pppp': ['Without Functions!!!!!!']}

def getImpactedFunctions(folder1, folder2):
    Code_difference_path = "D:/baxiang_ceshi/代码差异信息.txt"
    #清空文档中代码差异信息
    with open(Code_difference_path, 'w') as file:
        pass  # 不写入任何内容，仅清空文件
    c_cpp_files_left =  [file for file in os.listdir(folder1) if file.endswith(".c") or file.endswith(".cpp")or file.endswith(".h")]       # 读取左侧文件夹里面C或者C++文件的名字:['calculator.cpp', 'calculator.h', 'dayin.cpp', 'dayin.h', 'shuzhijisuan.cpp']
    c_cpp_files_right = [file for file in os.listdir(folder2) if file.endswith(".c") or file.endswith(".cpp")or file.endswith(".h")]      # 读取右侧文件夹里面C或者C++文件的名字
    cpp_h_left, cpp_h_right = unique_elements(c_cpp_files_left, c_cpp_files_right)      # 获取左侧和右侧文件夹中各自独有的文件名 :cpp_h_left=['haha.cpp'],cpp_h_right=['peizhi.cpp']
    c_cpp_files_left=[item for item in c_cpp_files_left if item not in cpp_h_left]      # 获取左右文件中同名文件的路径
    list_left_final  = []
    list_right_final = []
    quanju_list_left_final  = {}
    quanju_list_right_final = {}
    # 获取整个函数文档的函数位置
    output_file_left_comb  = "D:/baxiang_ceshi/CODE_Copy/left_comb/Combine_left.txt"    # 将所有代码合并后形成的txt文件
    output_file_right_comb = "D:/baxiang_ceshi/CODE_Copy/right_comb/Combine_right.txt"  # 将所有代码合并后形成的txt文件
    func_place1_combine = Function_place_jubu(output_file_left_comb)               # func_place1：包含了函数信息以及函数的起始位置。例：[['Calculator.add', 2, 7], ['Calculator.subtract', 11, 14], ['Calculator.multiply', 16, 19], ['Calculator.divide', 21, 25]]
    func_place2_combine = Function_place_jubu(output_file_right_comb)              # func_place2：包含了函数信息以及函数的起始位置。
    # 是否对左右侧独有的代码进行处理的标志
    flag_left_du=0                   # 0:表示未开始处理  1:表示有数据   2:表示无数据
    flag_right_du=0                  # 0:表示未开始处理  1:表示有数据   2:表示无数据
    flag_biaoqian_du=0               # 同名文件表头写入标志。    0：表示未写入   1：表示已经写入    （-----（1）独有文件代码差异信息及对应位置-------）
    flag_biaoqian=0                  # 同名文件表头写入标志。    0：表示未写入   1：表示已经写入    （-----（2）共有文件代码差异信息及对应位置----）
    flag_tongming=0                  #
    flag_left_du_write =0            # 0：开始写入，1：已经写入，不再进行二次写入
    flag_right_du_write=0            # 0：开始写入，1：已经写入，不再进行二次写入
    # 异常数据的初始化
    yichang_right_du =[]
    yichang_left_du=[]
    yichang_right = []
    yichang_left = []
    # 在地址为Code_difference_path的文档中写入内容
    # 1、对文件差异进行处理
    for file_name in c_cpp_files_left:                                                         # 左文件夹中的文件名
        file1_path = os.path.join(folder1, file_name)
        file2_path = os.path.join(folder2, file_name)
        # 1、对左侧独有的c或c++文件进行处理
        if flag_left_du == 0:
            if cpp_h_left == []:
                flag_left_du = 2                                                 #flag_left_du:0:表示未开始处理  1:表示有数据   2:表示无数据
            else:
                flag_left_du = 1
                for cpp_h_left_item in cpp_h_left:                               # cpp_h_left_item：左侧代码独有的文件名： 例：'haha.cpp'
                    file1_path_left_du = os.path.join(folder1, cpp_h_left_item)  # 左侧独有代码的路径
                    # (1) 查找当前路径下C或C++代码中的所有函数名称及对应的位置：例：['login', 24, 40]
                    func_dict_left_du = Function_place_jubu(file1_path_left_du)  # func_place1：包含了函数信息以及函数的起始位置。例：[['Calculator.add', 2, 7], ['Calculator.subtract', 11, 14], ['Calculator.multiply', 16, 19], ['Calculator.divide', 21, 25]]
                    # (2) 读取左侧独有文件中的所有内容，视为代码差异
                    diff_left_du = read_files(file1_path_left_du)                # 读取左侧独有文件中的内容（读取的同时对空格和注释进行剔除）
                    # (3) 返回差异代码在当前C或C++代码中对应的位置信息,并对其影响到的函数进行分析
                    fun_place_left_du = find_function_diff_du(file1_path_left_du,diff_left_du)                      # 获取位置信息： fun_place_left_du 例：{'tongji();': [5], 'dayin.power();': [6]}
                    fun_place_left_du = {key: value for key, value in fun_place_left_du.items() if value != []}     # 去掉空值
                    # (4) 分析发生变异的哪些是全局变量哪些是局部变量
                    # 例：list_left_du={'int kaka()': ['kaka'], '{': ['kaka'], 'int aa = 10;': ['kaka'], 'int cccc = 20;': ['kaka'], 'return 0;': ['kaka'], '}': ['kaka']}
                    # 例：quanju_bianliang_left_du=['int sdsdjkfnslk = 20;', 'int guka,sigama;', 'int sdsdjk = 200;']
                    list_left_du, quanju_bianliang_left_du = find_matching_functions(fun_place_left_du,func_dict_left_du)
                    # (5)对全局变量进行提取
                    qj_bianliang_left_du = []
                    for item in quanju_bianliang_left_du:                                                        # ['int sdsdjk = 200;', 'int sdsdjkfnslk = 20;', 'int guka,sigama;']
                        quanju_left_du = extract_variable_name(item)                                             # 从字符串中提取变量名
                        qj_bianliang_left_du = qj_bianliang_left_du + quanju_left_du                             # ['sdsdjk', 'sdsdjkfnslk', 'guka', 'sigama']
                    # (6)得到全局变量的位置
                    quanuju_left_place_du = find_elements_in_text(output_file_left_comb,qj_bianliang_left_du)    # 返回了全局变量所包含的位置信息:例：{'hanshutiqu': [8]}
                    # (7)判断全局变量的改变影响到了哪些函数
                    # 例：quanuju_left_place_du={'sdsdjk': [114, 115], 'sdsdjkfnslk': [114], 'guka': [117], 'sigama': [117]}
                    # 例：quanju_list_left_du={'sdsdjk': ['Without Functions!!!!!!'], 'sdsdjkfnslk': ['Without Functions!!!!!!'], 'guka': ['Without Functions!!!!!!'], 'sigama': ['Without Functions!!!!!!']}
                    quanju_list_left_du, yichang_left_du = find_matching_functions_qunju(quanuju_left_place_du,func_place1_combine)   # 变异代码所影响的函数形成了一个数组(去重后)
                    #yichang_left_du = ['aa17', 'aa42', 'aa54', 'aa71', 'aa29', 'aa58', 'aa22', 'aa24', 'aa85', 'aa97']               # 代码不被任何函数引用(可能是结构体)
                    # (8)对由代码直接变更的内容进行处理
        # 2、对右侧独有的c或c++文件进行处理
        if flag_right_du == 0:
            if cpp_h_right == []:
                flag_right_du = 2                                                          # 0:表示未开始处理  1:表示有数据   2:表示无数据
            else:
                flag_right_du = 1
                for cpp_h_right_item in cpp_h_right:
                    file2_path_right_du = os.path.join(folder2, cpp_h_right_item)          # 右侧独有代码的路径
                    # (1) 查找当前路径下C或C++代码中的所有函数名称及对应的位置：例：
                    func_dict_right_du = Function_place_jubu(file2_path_right_du)
                    # (2) 读取右侧独有文件中的所有内容，视为代码差异
                    diff_right_du = read_files(file2_path_right_du)                        # 读取右侧代码内容,同时删除注释
                    # log_info(f"diff_right_du={diff_right_du}", Path(__file__).stem)
                    # (3) 返回差异代码在当前C或C++代码中对应的位置信息,并对其影响到的函数进行分析
                    fun_place_right_du = find_function_diff_du(file2_path_right_du, diff_right_du)
                    fun_place_right_du = {key: value for key, value in fun_place_right_du.items() if value != []}
                    # log_info(f"fun_place_right_du={fun_place_right_du}", Path(__file__).stem)
                    # (4) 分析发生变异的哪些是全局变量哪些是局部变量
                    # 参数说明：list_right_du              :非全局变量变化影响到的函数
                    # #       quanju_bianliang_right_du  :包含全局变量的那一行的内容
                    list_right_du, quanju_bianliang_right_du = find_matching_functions(fun_place_right_du,func_dict_right_du)
                    # log_info(f"list_right_du={list_right_du}", Path(__file__).stem)
                    # log_info(f"quanju_bianliang_right_du={quanju_bianliang_right_du}", Path(__file__).stem)
                    # (5)对全局变量进行提取
                    qj_bianliang_right_du = []
                    for item in quanju_bianliang_right_du:
                        quanju_right_du = extract_variable_name(item)
                        qj_bianliang_right_du = qj_bianliang_right_du + quanju_right_du
                        # log_info(f"qj_bianliang_right_du={qj_bianliang_right_du}", Path(__file__).stem)
                    # (6)得到全局变量的位置
                    quanuju_right_place_du = find_elements_in_text(output_file_right_comb, qj_bianliang_right_du)
                    # log_info(f"quanuju_right_place_du={quanuju_right_place_du}", Path(__file__).stem)
                    # (7)判断全局变量的改变影响到了哪些函数
                    quanju_list_right_du, yichang_right_du = find_matching_functions_qunju(quanuju_right_place_du,func_place2_combine)   #quanju_right_left_du={'sdsdjk': ['Without Functions!!!!!!'], 'guka': ['Without Functions!!!!!!'], 'sigama': ['Without Functions!!!!!!'], 'sdsdjkfnslk': ['Without Functions!!!!!!']}
        # 3、对共有的文件进行处理
        if os.path.exists(file2_path):                                                    # 如果左侧文件夹的文件在右侧文件夹也有
            flag_tongming=1                                                               # 在本次循环中存在同名文件
            # (1) 查找当前路径下C或C++代码中的所有函数名称及对应的位置：例：['login', 24, 40]
            func_place1=  Function_place_jubu(file1_path)                                 # func_place1：包含了函数信息以及函数的起始位置。例：[['Calculator.add', 2, 7], ['Calculator.subtract', 11, 14], ['Calculator.multiply', 16, 19], ['Calculator.divide', 21, 25]]
            func_place2 = Function_place_jubu(file2_path)                                 # func_place2：包含了函数信息以及函数的起始位置。
            # (2) 输出两个同名文件的文件差异信息
            diff= compare_files(file1_path, file2_path)                                   # 代码差异对比信息
            diff = filter_list(diff)
            # 去除列表中的特殊元素:['?', '\n']
            line_temp_left, line_temp_right = count_special_lines(diff)                   # 函数输出:字典：键为变异的代码，键值为变异代码的前两行代码。
            if len(line_temp_left) == 0 and len(line_temp_right) == 0:
                continue
            # line_temp_left = {'if (start > end) {': ['void printNumbersRecursive(int start, int end) {', 'std::cout << i << " ";'],'return 10;': ['void printNumbersRecursive(int start, int end) {', 'std::cout << i << " ";']}
            # (2) 返回差异代码在当前C或C++代码中对应的位置信息,并对其影响到的函数进行分析
            fun_place_left =  find_function_diff(file1_path,line_temp_left)                                                  #fun_place_left 例：{'tongji();': [5], 'dayin.power();': [6]}
            fun_place_right = find_function_diff(file2_path,line_temp_right)                                                # fun_place_right例：{'if (start > end)': [10], 'int xianxisngjisuan=10;': [12], 'int a = 10000;': [37], 'plane();': [46, 53]}
            if len(fun_place_left) == 0 and len(fun_place_right) == 0:
                continue
            fun_place_left =  {key: value for key, value in fun_place_left.items()  if value != []}  # fun_place_left={'if (start > end) {': [10], 'return 10;': [12], 'return 0;': [41]}
            fun_place_right = {key: value for key, value in fun_place_right.items() if value != []}  #fun_place_right={'if (start > end)': [10], 'return 0;': [12], 'return 100;': [42]}
            # 参数说明：list_left:非全局变量变化影响到的函数
            # #       quanju_bianliang_left:包含全局变量的那一行的内容
            list_left,  quanju_bianliang_left  =  find_matching_functions(fun_place_left,  func_place1)                      # 变异代码所影响的函数形成了一个数组(去重后):list_left:{'return 0;': ['plane', 'feijikongzhi']},quanju_bianliang_left=['int aaaaa1[10] = { 0 }, bbbbbb = 200, ccbbb = 5000;']
            list_right, quanju_bianliang_right =  find_matching_functions(fun_place_right, func_place2)                      # list_right:变异代码所影响的函数形成了一个数组(去重后),quanju_bianliang_right:包含全局变量的那一行的内容

            # （3）对全局变量影响到的函数进行统计
            #  <1>对全局变量进行合并确定是哪些发生了变化
            left_quanju_fianl,right_quanju_fianl = quanju_chuli_quchu_rongyu(quanju_bianliang_left,quanju_bianliang_right)  #左侧和右侧全局变量的增删修改内容合并
            quanuju_left  = find_elements_in_text(output_file_left_comb , left_quanju_fianl)                                #返回了全局变量所包含的位置信息:例：{'hanshutiqu': [8]}
            quanuju_right = find_elements_in_text(output_file_right_comb, right_quanju_fianl)                               #返回了全局变量所包含的位置信息:例：{'hanshutiqu': [8]}
            #  查找全局变量影响到了哪些函数：['Calculator.add']
            quanju_list_left,  yichang_left  = find_matching_functions_qunju(quanuju_left,  func_place1_combine)            # 变异代码所影响的函数形成了一个数组(去重后):quanju_list_left:{'aaaaa': ['main'], 'aaaaa1': ['main'], 'ccbbb': ['main']}
            quanju_list_right, yichang_right = find_matching_functions_qunju(quanuju_right, func_place2_combine)            #quanju_list_right={'aaaaa': ['main'], 'pppp': ['shangdian'], 'ccccbbb': ['main'], 'ceshi_flag': ['Without Functions!!!!!!'], 'ccbbb': ['main']}
            # (4)将差异函数进行合并
            list_left_final.append(list_left)                                               # 代码差异影响到了哪些函数 : list_left={'return 0;': ['plane', 'feijikongzhi']}
            list_right_final.append(list_right)                                             # 代码差异影响到了哪些函数
            quanju_list_left_final=merge_dicts_two(quanju_list_left_final,quanju_list_left)     #
            quanju_list_right_final=merge_dicts_two(quanju_list_right_final,quanju_list_right)  # quanju_list_right={'aaaaa': ['main'], 'pppp': ['shangdian'], 'ccccbbb': ['main'], 'ceshi_flag': ['Without Functions!!!!!!'], 'ccbbb': ['main']}

        # (6)将代码差异写入到代码差异文件中-独有文件处理
        if flag_left_du ==1 or flag_right_du ==1:
            if flag_biaoqian_du ==0 :                 # 表头的写入标志
                write_data_and_increment_line(Code_difference_path,'-----------------------------------------（1）独有文件代码差异信息及对应位置-----------------------------------------')
            flag_biaoqian_du=1                    # 表头的写入标志
        if flag_left_du ==1:
            if flag_left_du_write == 0:               # 左边有左右文件并且还没有写入
                flag_left_du_write=1
                write_data_and_increment_line(Code_difference_path, file1_path_left_du)  #
                # (6.1)将代码差异写入到代码差异文件中
                write_dict_to_file(Code_difference_path, file1_path_left_du, 'L')  # 写入代码差异位置信息
                if list_left or quanju_list_left:
                    write_data_and_increment_line(Code_difference_path,     '局部代码变更列表：' + merge_keys_as_string(list_left_du))
                    list_left_du_string = dict_to_string(list_left_du)
                    if len(list_left_du_string) > 0:
                        write_data_and_increment_line(Code_difference_path, list_left_du_string)
                    else:
                        write_data_and_increment_line(Code_difference_path, list_left_du_string)
                    write_data_and_increment_line(Code_difference_path,'全局变量列表' + str(qj_bianliang_left_du))  # qj_bianliang_left_du
                    quanju_string_left = dict_to_string(quanju_list_left_du)
                    if len(quanju_string_left) > 0:
                        write_data_and_increment_line(Code_difference_path,quanju_string_left)
                write_data_and_increment_line(Code_difference_path, '              ')
                write_data_and_increment_line(Code_difference_path, '              ')
                write_data_and_increment_line(Code_difference_path, '              ')
        if flag_right_du == 1:
            if flag_right_du_write == 0:
                flag_right_du_write=1
                write_data_and_increment_line(Code_difference_path, file2_path_right_du)
                # (6.2)将代码差异写入到代码差异文件中。
                write_dict_to_file(Code_difference_path, file2_path_right_du, 'R')  # 写入代码差异位置信息
                if list_right or quanju_list_right:
                    write_data_and_increment_line(Code_difference_path, '局部代码变更列表：' + merge_keys_as_string(list_right_du))
                    list_right_du_string = dict_to_string(list_right_du)
                    if len(list_right_du_string) > 0:
                        write_data_and_increment_line(Code_difference_path,list_right_du_string)
                    else:
                        write_data_and_increment_line(Code_difference_path, 'Null')
                    write_data_and_increment_line(Code_difference_path, '全局变量列表：' + str(qj_bianliang_right_du))
                    quanju_string_right = dict_to_string(quanju_list_right_du)
                    if len(quanju_string_right) > 0:
                        write_data_and_increment_line(Code_difference_path, quanju_string_right)
                    else:
                        write_data_and_increment_line(Code_difference_path, 'Null')
                write_data_and_increment_line(Code_difference_path, '              ')
                write_data_and_increment_line(Code_difference_path, '              ')
                write_data_and_increment_line(Code_difference_path, '              ')

        # (7)将代码差异写入到代码差异文件中-共有文件处理
        if flag_biaoqian ==0:
            if flag_biaoqian_du ==1:
                write_data_and_increment_line(Code_difference_path,'-----------------------------------------（2）共有文件代码差异信息及对应位置-----------------------------------------')
            else:
                write_data_and_increment_line(Code_difference_path,'-----------------------------------------（1）共有文件代码差异信息及对应位置-----------------------------------------')
            flag_biaoqian=1
        if flag_tongming == 1:
            flag_tongming = 0
            write_data_and_increment_line(Code_difference_path, file1_path)  #
            # (7.1)将代码差异写入到代码差异文件中
            write_dict_to_file(Code_difference_path, fun_place_left, 'L')  # 写入代码差异位置信息
            if list_left or quanju_list_left:
                write_data_and_increment_line(Code_difference_path, '局部代码变更列表：' + merge_keys_as_string(list_left))
                list_left_string = dict_to_string(list_left)
                if len(list_left_string) > 0:
                    write_data_and_increment_line(Code_difference_path, list_left_string)
                else:
                    write_data_and_increment_line(Code_difference_path, 'Null')
                write_data_and_increment_line(Code_difference_path, '全局变量列表：' + str(left_quanju_fianl))
                quanju_list_left_string = dict_to_string(quanju_list_left)
                if len(quanju_list_left_string) > 0:
                    write_data_and_increment_line(Code_difference_path, quanju_list_left_string)
                else:
                    write_data_and_increment_line(Code_difference_path, '' + 'Null')
            # (7.2)将代码差异写入到代码差异文件中。
            write_data_and_increment_line(Code_difference_path, file2_path)
            write_dict_to_file(Code_difference_path, fun_place_right, 'R')  # 写入代码差异位置信息
            if list_right or quanju_list_right:
                write_data_and_increment_line(Code_difference_path, '局部代码变更列表：' + merge_keys_as_string(list_right))
                list_right_string = dict_to_string(list_right)
                if len(list_right_string) > 0:
                    write_data_and_increment_line(Code_difference_path, list_right_string)
                else:
                    write_data_and_increment_line(Code_difference_path, 'Null')
                write_data_and_increment_line(Code_difference_path, '全局变量列表：' + str(right_quanju_fianl))
                quanju_list_right_string = dict_to_string(quanju_list_right)
                if len(quanju_list_right_string) > 0:
                    write_data_and_increment_line(Code_difference_path, quanju_list_right_string)
                else:
                    write_data_and_increment_line(Code_difference_path, 'Null')
            write_data_and_increment_line(Code_difference_path, '              ')
            write_data_and_increment_line(Code_difference_path, '              ')
            write_data_and_increment_line(Code_difference_path, '              ')
        # (8）清空变量的信息
        fun_place_left.clear()
        fun_place_right.clear()
        line_temp_left.clear()
        line_temp_right.clear()
    # 将独自变量影响的内容添加到统计结果中
    if flag_left_du==1:
        list_left_final.append(list_left_du)
        quanju_list_left_final=merge_dicts_two(quanju_list_left_final,quanju_list_left_du)                        # quanju_list_left_du={'sdsdjk': ['Without Functions!!!!!!'], 'sdsdjkfnslk': ['Without Functions!!!!!!'], 'guka': ['Without Functions!!!!!!'], 'sigama': ['Without Functions!!!!!!']}
    if flag_right_du==1:
        list_right_final.append(list_right_du)
        quanju_list_right_final=merge_dicts_two(quanju_list_right_final,quanju_list_right_du)
    # 去除空元素
    list_left_final=[item for item in list_left_final if item]                                                    # [{'if (start > end) {': ['printNumbersRecursive'], 'fadongji();': ['plane']}, {'int a = 100;': ['main'], 'int b = 5;': ['main']}]
    list_right_final=[item for item in list_right_final if item]
    yichang_genggai = yichang_right_du + yichang_left_du+yichang_right+yichang_left                               # 这里面的变更内容不被任何函数引用
    yichang_genggai =[item for item in yichang_genggai if len(item)>0]
    yichang_genggai=list(set(yichang_genggai))                                                                    # 去除重复元素
    quanju_list_left_final  = {key: value for key, value in quanju_list_left_final.items()  if len(key) > 1}      # 去除空元素
    quanju_list_right_final = {key: value for key, value in quanju_list_right_final.items() if len(key) > 1}      # 去除空元素
    return list_left_final,list_right_final,quanju_list_left_final,quanju_list_right_final, yichang_genggai       # 代码差异最后影响到的函数：# list_left_final  :[{'int flag_daji = mubiaodaji(10);': ['main'], "processInput('a');": ['main']}]

# 函数功能：    将一个二维数组进行扁平化，去除空元素
def flatten_and_remove_empty(input_list):
    flattened_list = [item for sublist in input_list for item in sublist if sublist]
    return flattened_list

# 全局变量的定义
total_leng=0
flag_ceshiguimo=False
func_place_tongji_left=[]
func_place_tongji_right=[]
name_find_flag = 0
# 函数功能：    函数数组的测试规模统计,统计函数的上下级以及函数本身的总行数
# 函数输入：
#            func_name：函数数组，包含所有进需要进行测试规模统计的函数    :['printNumbers', 'main', 'processInput', 'plane']
#            folder_path：代码位置
# 函数输出：    测试规模
# 中间变量说明：
    # func_place_tongji = [['Calculator.subtract', 16, 18], ['Calculator.divide', 25, 29], ['printNumbers', 42, 46],
    #                      ['printNumbersRecursive', 49, 57], ['moveUp', 59, 61], ['moveDown', 63, 65],
    #                      ['moveLeft', 67, 69], ['moveRight', 71, 73], ['plane', 75, 83], ['feijikongzhi', 84, 88],
    #                      ['login', 89, 105], ['printNumbers', 112, 117], ['shangdian', 123, 126],
    #                      ['mubiaodaji', 129, 133], ['processInput', 135, 151], ['main', 153, 169]]
    # func_calls_guimo = {'moveUp': ['printf'], 'moveDown': ['printf'], 'moveLeft': ['printf'], 'moveRight': ['printf'],
    #                     'plane': ['fadongji', 'moveUp', 'moveRight', 'moveDown', 'moveLeft'], 'feijikongzhi': ['plane'],
    #                     'login': ['feijikongzhi', 'printNumbersRecursive'], 'mubiaodaji': ['plane'],
#                         'processInput': ['mubiaodaji'],'main': ['sin', 'mubiaodaji', 'shangdian', 'calc.add', 'calc.subtract', 'login','processInput']}
def ceshi_guimo_tongji(func_name ,folder_left , folder_right):
    global total_leng,flag_ceshiguimo, func_place_tongji_left, func_place_tongji_right,name_find_flag
    total_leng = 0
    func_jihe=[]
    func_place_tongji_left, func_calls_guimo_left, digui_function_guimo_left =    Function_relationship(folder_left)
    func_place_tongji_right, func_calls_guimo_right, digui_function_guimo_right = Function_relationship(folder_right)
    for name in func_name:
        func_called_left,func_calls_left=func_called_and_call_ship(name,func_calls_guimo_left)                        # func_calls_guimo:函数调用关系包括函数本身以及函数的上一级和下一级函数
        if len(func_called_left) > 0 or len(func_calls_left) > 0:                                                     # 如果找到了该函数的调用关系(左侧)
            func_jihe.append([name])
            func_jihe.append(func_called_left)
            func_jihe.append(func_calls_left)
        else:                                                                                                         # 如果没有找到就从右侧继续找
            func_called_right, func_calls_right = func_called_and_call_ship(name,func_calls_guimo_right)
            func_jihe.append([name])
            func_jihe.append(func_called_right)
            func_jihe.append(func_calls_right)
    #  将函数的调用关系添加到列表中，同时去除重复的元素
    func_jihe=flatten_and_remove_empty(func_jihe)
    unique_set =  set(func_jihe)                                #去重
    func_affect = list(unique_set)                              #重新转化为列表
    # 计算函数的测试规模
    for item in func_affect:
        name_find_flag = 0
        if not '.' in item:
            for items in func_place_tongji_left:
                if item == items[0]:
                    name_find_flag=1
                    total_leng = total_leng + items[2] - items[1] + 1
                    break
            if name_find_flag==0:
                for items in func_place_tongji_right:
                    if item == items[0]:
                        total_leng = total_leng + items[2] - items[1] + 1
                        break
        else:
            item_temp= item.split('.')  # 要查找的函数名的拆分。
            for items in func_place_tongji_left:
                if '.' in items[0]:
                    items_temp=items[0].split('.')
                    if item_temp[1]==items_temp[1]:
                        name_find_flag=1
                        total_leng = total_leng + items[2] - items[1] + 1
                        break
                if name_find_flag==0:
                    for items in func_place_tongji_right:
                        if '.' in items[0]:
                            items_temp=items[0].split('.')
                            if item_temp[1]==items_temp[1]:
                                total_leng = total_leng + items[2] - items[1] + 1
                                break
    return total_leng,func_affect   #ceshi_guimo=94    func_affect=['fadongji', 'moveLeft', 'moveUp', 'printNumbers', 'calc.add', 'moveDown', 'feijikongzhi', 'main', 'sin', 'moveRight', 'calc.subtract', 'plane', 'processInput', 'mubiaodaji', 'login', 'shangdian']
# 函数功能：返回字典的所有键值并且去重
#函数输入：
#        input_data：     comb_quanju=[{'aaaaa1': ['main'], 'ccbbb': ['main'], 'aaaaa': ['main'], 'aaaaaaaaaaaa': ['Without Functions!!!!!!'], 'ceshi_flag': ['Without Functions!!!!!!'], 'ccccbbb': ['main'], 'pppp': ['shangdian']}]
#函数输出：
#        result    :     ['shangdian', 'main', 'Without Functions!!!!!!']
def combine_keys_and_values(input_data):
    result = []
    for data_dict in input_data:
        for key, values in data_dict.items():
            result.extend(values)
    result=list(set(result))
    if 'Without Functions!!!!!!' in result:         # 去除空元素
        result.remove('Without Functions!!!!!!')
    return result


# 备份代码
# 函数功能：    最终的测试规模统计
# 函数输入：
# target_folder_left =  "D:/baxiang_ceshi/CODE_Copy/left"
# target_folder_right = "D:/baxiang_ceshi/CODE_Copy/right"
def final_ceshi_guimo_zuizao(folder1, folder2):
    global quanju_Flag_flag
    if '/' in folder1 and '/' in folder2:
        list_left_final, list_right_final, quanju_left__, quanju_right__, yichang_genggai = getImpactedFunctions(folder1, folder2)  # 统计两个文件夹中代码差异影响到了哪些函数  例子：['plane', 'main']
        # 对非全局变量的代码变更的测试规模进行统计
        list_left_func = extract_pairs_from_list_of_dicts(list_left_final)    # list_left_func=['plane', 'processInput', 'main', 'main']
        list_right_func = extract_pairs_from_list_of_dicts(list_right_final)  # list_right_func=['plane', 'processInput', 'main', 'main', 'main', 'printNumbers', 'printNumbers']
        # 绘制差异代码的影响范围,并将所有的图片存放在一个文件夹中。
        list_comb = list_left_func + list_right_func
        list_comb = list(set(list_comb))  # list_comb=['printNumbers', 'main', 'processInput', 'plane']
        ceshi_guimo, func_tongji_jihe = ceshi_guimo_tongji(list_comb, folder1,folder2)  # ceshi_guimo=94    func_tongji_jihe(测试规模统计到的函数)=['fadongji','moveLeft','moveUp', 'printNumbers', 'calc.add','moveDown', 'feijikongzhi','main','sin','moveRight', 'calc.subtract', 'plane', 'processInput','mubiaodaji', '                 #
        # 对全局变量导致的代码的测试规模进行统计
        comb_quanju = [merge_dicts_two(quanju_left__,quanju_right__)]  # 统计全全局变量变化所影响的所有函数  例：comb_quanju=[{'aaaaa1': ['main'], 'ccbbb': ['main'], 'aaaaa': ['main'], 'aaaaaaaaaaaa': ['Without Functions!!!!!!'], 'ceshi_flag': ['Without Functions!!!!!!'], 'ccccbbb': ['main'], 'pppp': ['shangdian']}]
        quanju_effcet_func = combine_keys_and_values(comb_quanju)  # 统计全局变量影响到了哪些函数       例：['shangdian', 'main']
        quanju_effcet_func = [item for item in quanju_effcet_func if item not in func_tongji_jihe]
        quanju_guimo = 0
        for item in quanju_effcet_func:
            quanju_Flag_flag = 0
            if item not in list_comb:  # 如果全局变量影响的函数与局部变量影响的函数不重合的话
                for temp in func_place_tongji_left:
                    if item == temp[0]:
                        quanju_Flag_flag = 1
                        quanju_guimo = quanju_guimo + temp[2] - temp[1]
                        break
                if quanju_Flag_flag == 0:
                    for temp in func_place_tongji_right:
                        if item == temp[0]:
                            quanju_guimo = quanju_guimo + temp[2] - temp[1]
                            break
    else:
        return -1
    return ceshi_guimo + quanju_guimo + len(yichang_genggai)


# 函数功能：将字典中的键值对互换(局部函数)
# 输入 ：字典列表  ：[{'<iostream>': ['Without Functions!!!!!!'], 'ccbbb': ['main', 'shangdian'], 'pppp': ['Without Functions!!!!!!'], 'ccccbbb': ['shangdian']}]
# 输出 ：字典列表  ：{'Without Functions!!!!!!': ['<iostream>', 'pppp'], 'main': ['ccbbb'], 'shangdian': ['ccbbb', 'ccccbbb']}
def merge_dicts_list_(list_of_dicts):
    result_dict = {}
    for item in list_of_dicts:
        for key, value_list in item.items():
            if len(value_list) == 1:
                if  value_list[0] == 'Without Functions!!!!!!':  # 对于未被调用的全局变量不进行统计
                    continue
                if value_list[0] not in result_dict:
                    result_dict[value_list[0]] = [key]
                else:
                    result_dict[value_list[0]].append(key)
            elif len(value_list) > 1:
                for value in value_list:
                    if value == 'Without Functions!!!!!!':       # 对于未被调用的全局变量不进行统计
                        continue
                    if value not in result_dict:
                        result_dict[value] = [key]
                    else:
                        result_dict[value].append(key)
    return result_dict

# 函数功能：    最终的测试规模统计
# 函数输入：
# target_folder_left =  "D:/baxiang_ceshi/CODE_Copy/left"
# target_folder_right = "D:/baxiang_ceshi/CODE_Copy/right"
quanju_Flag_flag = 0

def final_ceshi_guimo(folder1, folder2):
    global quanju_Flag_flag
    if '/' in folder1 and '/' in folder2:
        list_left_final, list_right_final, quanju_left__, quanju_right__, yichang_genggai = getImpactedFunctions(folder1, folder2)  # 统计两个文件夹中代码差异影响到了哪些函数  例子：['plane', 'main']
        # log_info(f"list_left_final={list_left_final}", Path(__file__).stem)                    # list_left_final=[{'return 0;': ['plane']}, {"case 'a':": ['processInput'], 'int a = 1000;': ['main'], 'int dayinx = aaaaa1[0];': ['main']}]
        # log_info(f"list_right_final={list_right_final}", Path(__file__).stem)                  # list_right_final=[{'return 100;': ['plane']}, {"case 'aa':": ['processInput'], 'int aaaa = quanju_flag;': ['main'], 'int ddd=H / (sin(-Ceta-a));': ['main'], 'int a = 1000, bb = 200,cc=500;': ['main']}, {'void printNumbers() {': ['printNumbers'], 'for (int i = 1; i <= 10; ++i) {': ['printNumbers']}]
        # log_info(f"quanju_left__={quanju_left__}", Path(__file__).stem)                        # quanju_left__={'aaaaa1': ['main'], 'ccbbb': ['main'], 'aaaaa': ['main'], 'aaaaaaaaaaaa': ['Without Functions!!!!!!']}
        # log_info(f"quanju_right__={quanju_right__}", Path(__file__).stem)                      # quanju_right__={'ccccbbb': ['main'], 'ccbbb': ['main'], 'aaaaa': ['main', 'shangdian']}, 'ceshi_flag': ['Without Functions!!!!!!'], 'pppp': ['shangdian']}
        # 1、对代码变更及代码变更影响到的函数进行合并处理
        # 1.1 局部变量  （给出函数内部哪些内容发生了变化）
        list_left_final_effect  = merge_dicts_list_(list_left_final)     # {'printNumbersRecursive': ['if (start > end) {', 'return 10;'], 'plane': ['return 0;'], 'shangdian': ['int a= aaaaa;'], 'processInput': ["case 'a':"], 'main': ['int a = 1000;', 'int dayinx = aaaaa1[0];']}
        list_right_final_effect = merge_dicts_list_(list_right_final)    # {'printNumbersRecursive': ['if (start > end)', 'return 0;'], 'plane': ['return 100;'], 'processInput': ["case 'aa':"], 'main': ['int aaaa = quanju_flag;', 'int ddd=H / (sin(-Ceta-a));', 'int a = 1000, bb = 200,cc=500;'], 'printNumbers': ['void printNumbers() {', 'for (int i = 1; i <= 10; ++i) {']}
        # 1.2 全局变量  （给出函数内部哪些内容发生了变化）
        quanju_left__effect  = merge_dicts_list_([quanju_left__])        # {'shangdian': ['ccbbb', 'aaaaa', 'ccccbbb'], 'main': ['ccbbb', 'aaaaa', 'aaaaa1']}
        quanju_right__effect = merge_dicts_list_([quanju_right__])       # {'shangdian': ['ccccbbb', 'aaaaa', 'ccbbb']}
        # 2、利用扩散模型，对软件的测试规模进行评估
        # 2.1对局部变量的处理


        # 2.2 对全局变量的处理


        # 2.3 对指针的处理


        # 2.4 对数组的处理


        # 2.5 对结构体的处理


        # 2.6 对类的处理


    return len(yichang_genggai)


