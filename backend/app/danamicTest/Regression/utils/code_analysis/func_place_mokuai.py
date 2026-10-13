
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 该模块的主要内容是得到所有函数的起始位置,包括正式的函数,以及被调用的函数的奇数位置
#
from tree_sitter import Language, Parser
from collections import defaultdict
import os

# 变量设置
call_function = None                  # 初始化为一个默认值或根据你的需求设置初始值
function_calls = defaultdict(list)    # 这一行代码创建了一个名为 function_calls   的字典，并指定了一个默认值的类型为列表。
count = -1                            #用于函数声明计数
function_place=[]                     #用于记录函数的起始位置。
place_start=0                         #用于记录函数起始位置的临时变量
place_end=0                           #用于记录函数结束位置的临时变量

#函数功能：分析函数的位置
#函数输入：node:语法树节点
#函数输出：函数位置信息
def analyze_function_place_total(node):
    # 全局变量声明
    global count
    global place_start
    global place_end
    global function_place
    function_place.clear()
    # 使用栈来模拟递归
    stack = [node]
    flag_definition=0
    while stack:
        current_node = stack.pop()
        # 1、对正式函数的起始位置以及减数位置进行提取
        if current_node.type == 'function_definition':                                                  #正式函数声明
            place_start = current_node.start_point[0]
            place_end = current_node.end_point[0]
            flag_definition=1
        if current_node.type == 'function_declarator' and flag_definition==1:
            if (current_node.child_by_field_name('declarator').type == 'identifier') or (current_node.child_by_field_name('declarator').type == 'qualified_identifier'):
                call_function_temp = current_node.child_by_field_name('declarator').text
                call_function_tp = call_function_temp.decode('utf-8')
                function_place.append([call_function_tp, place_start, place_end])
                # 用完后对函数的起始位置与结束位置进行清空
                place_start=0
                place_end  =0
                flag_definition =  0
        # 对  int main(){int ad = calc.add(3, 3); dauin();}，提取 dauin的起始及结束位置
        if current_node.type == 'call_expression':
            if current_node.child_by_field_name('function').type == 'identifier':
                call_function_temp = current_node.child_by_field_name('function').text
                call_function_tp = call_function_temp.decode('utf-8')
                place_start = current_node.start_point[0]
                place_end = current_node.end_point[0]
                function_place.append([call_function_tp, place_start, place_end])
        # 对  int main(){int ad = calc.add(3, 3); dauin();}，提取 calc.add的起始及结束位置
        if current_node.type == 'call_expression':
            if current_node.child_by_field_name('function').type == 'field_expression':
                call_function_temp = current_node.child_by_field_name('function').text
                call_function_tp = call_function_temp.decode('utf-8')
                place_start = current_node.start_point[0]
                place_end = current_node.end_point[0]
                function_place.append([call_function_tp, place_start, place_end])
        # 将子节点压入栈中，以便迭代处理
        stack.extend(reversed(current_node.children))
    # （2） 通过递归调用遍历所有子节点
# 3、构建函数的语法数，并进行函数调用关系分析
def Function_call_relationship(CODE):
    # 1、建立分析规则（https://github.com/tree-sitter/py-tree-sitter）
    Language.build_library(
        os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'ts_build', 'languages.dll'),
        [
            r'D:\baxiang_ceshi\tree_sitter_wenjian\tree_sitter_langue\tree-sitter-c-master',  # C语言分析包
            r'D:\baxiang_ceshi\tree_sitter_wenjian\tree_sitter_langue\tree-sitter-cpp-master',  # C++语言分析包
            r'D:\baxiang_ceshi\tree_sitter_wenjian\tree_sitter_langue\tree-sitter-python-master',  # python语言分析包
        ]
    )
    # 2、为 C、C++ 和 Python 分别创建了对应的 Language 对象，以便在后续的解析中使用。
    try:
        # 使用项目中实际存在的DLL文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        dll_path = os.path.join(project_root, 'backend', 'ts_build', 'languages.dll')
        
        # 检查DLL文件是否存在
        if os.path.exists(dll_path):
            #C_LANGUAGE = Language(dll_path, 'c')
            CPP_LANGUAGE = Language(dll_path, 'cpp')
        else:
            log_info(f"警告：Tree-sitter语言库文件不存在: {dll_path}", Path(__file__).stem)
            CPP_LANGUAGE = None
        
    except Exception as e:
        log_info(f"警告：无法加载Tree-sitter语言库: {e}", Path(__file__).stem)
        CPP_LANGUAGE = None
    # 3、创建了一个 Parser 对象，并设置其使用的语言为 C++ 语言。
    parser = Parser()
    parser.set_language(CPP_LANGUAGE)
    # 4、解析代码获取语法树
    tree = parser.parse(bytes(CODE, 'utf-8'))
    root_node = tree.root_node
    # 5、分析函数位置
    analyze_function_place_total(root_node)



# 函数功能：将列表里面元素的的'：：'替换为'.'
def replace_double_colon(input_list):
    result = []
    for item in input_list:
        if isinstance(item, list):
            updated_item = [sub_item.replace('::', '.') if isinstance(sub_item, str) else sub_item for sub_item in item]
            result.append(updated_item)
        else:
            result.append(item)
    return result

#函数功能：该函数的主要功能为分析某个项目的函数调用关系
#函数输入：文件路径，
#函数输出：函数的名称及位置以及函数的调用关系
def Function_place_jubu(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        CODE = file.read()                                                      #读取所有代码
    Function_call_relationship(CODE)
    function_place_final = []
    reversed_list=[]
    function_place_final.clear()
    for item in function_place:
        if isinstance(item, list):
            updated_item = [sub_item.replace('::', '.') if isinstance(sub_item, str) else sub_item for sub_item in item]
            if updated_item[1] != updated_item[2]:                              #单行函数认为是空函数，不进行统计
                function_place_final.append(updated_item)
            else:                                                               # 对于单单双函数也进行吸取主要用于函数注释的提取   例子:int  func();//自检测
                pass
        else:
            if item[1] != item[2]:                                              #单行函数认为是空函数，不统计位置信息
                function_place_final.append(item)
            else:
                pass
        reversed_list = function_place_final[::-1]
    return reversed_list