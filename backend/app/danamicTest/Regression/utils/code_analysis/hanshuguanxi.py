
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 该模块的主要内容是根据输入文件得到某一文件夹下c或者c+加程序的语法树
import copy

from tree_sitter import Language, Parser
from collections import defaultdict
import sys
import os  # 导入操作系统模块，用于处理文件路径和文件夹遍历
# 变量设置
call_function = None                  # 初始化为一个默认值或根据你的需求设置初始值
function_calls = defaultdict(list)    # 这一行代码创建了一个名为 function_calls   的字典，并指定了一个默认值的类型为列表。
count = -1                            #用于函数声明计数
function_place=[]                     #用于记录函数的起始位置。
place_start=0                         #用于记录函数起始位置的临时变量
place_end=0                           #用于记录函数结束位置的临时变量

# 1、分析各个函数的起始位置
def analyze_function_place(node):
    # 全局变量声明
    global count
    global place_start
    global place_end
    global function_place
    function_place.clear()
    flag_definition=0                    #是否发现函数声明
    # 使用栈来模拟递归
    stack = [node]
    while stack:
        current_node = stack.pop()
        if current_node.type == 'function_definition':
            count += 1
            place_start = current_node.start_point[0]
            place_end = current_node.end_point[0]
            flag_definition=1            #发现函数声明,标志位设置为1
        if current_node.type == 'function_declarator' and flag_definition==1:
            if (current_node.child_by_field_name('declarator').type == 'identifier') or (current_node.child_by_field_name('declarator').type == 'qualified_identifier'):
                call_function_temp = current_node.child_by_field_name('declarator').text
                call_function_tp = call_function_temp.decode('utf-8')
                function_place.append([call_function_tp, place_start, place_end])
                flag_definition=0
        # 将子节点压入栈中，以便迭代处理
        stack.extend(reversed(current_node.children))
    # （2） 通过递归调用遍历所有子节点

# 2、分析语法树，构建函数调用关系（函数与函数调用的子函数的关系）（仅分析上下级的，不进行多层分析）
def analyze_function_calls(nodee):
    # 全局变量声明
    global function_place
    # 使用栈来模拟递归
    stack = [nodee]
    while stack:
        current_node = stack.pop()
        if current_node.type == 'function_declarator':                       # 如果当天决定是函数声明
            caller = current_node.child_by_field_name('declarator').text     # 得到函数名
            caller = caller.decode('utf-8')                                  # 转码
            start_temp = current_node.start_point[0]
            end_temp = current_node.end_point[0]
            for func in reversed(function_place):
                if start_temp > func[1] and end_temp < func[2]:
                    function_calls[func[0]].append(caller)
                    #log_info(f"父函数：{func[0]}, 起始位置：{func[1]}, 结束位置：{func[2]}, 调用函数：{caller}", Path(__file__).stem)
                    break
        if current_node.type == 'call_expression':
            if (current_node.child_by_field_name('function').type == 'identifier') or (
                    current_node.child_by_field_name('function').type == 'field_expression'):
                caller = current_node.child_by_field_name('function').text
                caller = caller.decode('utf-8')
                start_temp = current_node.start_point[0]
                end_temp = current_node.end_point[0]
                for func in reversed(function_place):
                    if start_temp > func[1] and end_temp < func[2]:
                        function_calls[func[0]].append(caller)
                        #log_info(f"父函数：{func[0]}, 起始位置：{func[1]}, 结束位置：{func[2]}, 调用函数：{caller}", Path(__file__).stem)
                        break
        # 将子节点压入栈中，以便迭代处理
        stack.extend(reversed(current_node.children))

# 3、构建函数的语法数，并进行函数调用关系分析
def Function_call_relationship(CODE):
    # 1、建立分析规则（https://github.com/tree-sitter/py-tree-sitter）
    try:
        # 使用项目中实际存在的DLL文件
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        dll_path = os.path.join(project_root, 'backend', 'ts_build', 'languages.dll')
        
        # 检查DLL文件是否存在
        if not os.path.exists(dll_path):
            log_info(f"警告：Tree-sitter语言库文件不存在: {dll_path}", Path(__file__).stem)
            return
        
        # 不需要构建，直接使用已编译的DLL
        # Language.build_library(dll_path, [...])  # 注释掉构建步骤
        
        # 2、为 C、C++ 和 Python 分别创建了对应的 Language 对象，以便在后续的解析中使用。
        C_LANGUAGE = Language(dll_path, 'c')
        CPP_LANGUAGE = Language(dll_path, 'cpp')
        PY_LANGUAGE = Language(dll_path, 'python')
        
        # 3、创建了一个 Parser 对象，并设置其使用的语言为 C++ 语言。
        parser = Parser()
        parser.set_language(CPP_LANGUAGE)
        # 4、解析代码获取语法树
        tree = parser.parse(bytes(CODE, 'utf-8'))
        root_node = tree.root_node
        # 5、分析函数位置
        analyze_function_place(root_node)
        # 6、存储函数调用关系创建
        analyze_function_calls(root_node)
        
    except Exception as e:
        log_info(f"警告：无法加载Tree-sitter语言库: {e}", Path(__file__).stem)
        log_info("跳过代码分析步骤...", Path(__file__).stem)
        return

# 4、读取文件夹路径下所有的c或者c加加文件
def read_cpp_files(folder_path):
    cpp_code = ''
    # 遍历文件夹中的所有文件和子文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.c') or file.endswith('.cpp') or file.endswith('.h'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                    cpp_code+= code
    return cpp_code

# 函数功能：将里面的：：替换为.
def replace_double_colon(input_list):
    result = []
    for item in input_list:
        if isinstance(item, list):
            updated_item = [sub_item.replace('::', '.') if isinstance(sub_item, str) else sub_item for sub_item in item]
            result.append(updated_item)
        else:
            result.append(item)
    return result


# 函数功能：遍历输入字典中的每个键值对，如果键和键值相等，则会将它们存储到 extracted_dict 中，并将原始字典中的这些数据标记为删除。
# 函数输入：
#         input_dict函数调用关系字典
# 函数输出：
#         input_dict函数调用关系字典
#         extracted_dict:递归函数的输字典
# 例：输入：input_dict={'Calculator.add': ['tongji', 'dayin.power'],'printNumbersRecursive': ['printNumbersRecursive']}   输出：input_dict={'Calculator.add': ['tongji', 'dayin.power']}   extracted_dict={'printNumbersRecursive': ['printNumbersRecursive']}

def extract_and_remove_equal_key_value_pairs(input_dict):
    extracted_dict = {}
    keys_to_remove = []
    for key, values in input_dict.items():
        for value in values:
            if key == value:
                if key not in extracted_dict:
                    extracted_dict[key] = []
                extracted_dict[key].append(value)
                keys_to_remove.append(key)
    extracted_keys = list(extracted_dict.keys())
    for key in keys_to_remove:
        if key in input_dict:
            del input_dict[key]
    return input_dict, extracted_keys

# 函数功能:去除字典中间值的重复元素
# 例：输入：{'addition': ['dayin'], 'subtraction': ['dayin', 'dayin', 'dayin'], 'multiplication': ['dayin', 'dayin', 'dayin'], 'division': ['dayin']}
# 输出：{'addition': ['dayin'], 'subtraction': ['dayin'], 'multiplication': ['dayin'], 'division': ['dayin']}
def remove_duplicates_from_dict(input_dict):
    for key, value in input_dict.items():
        input_dict[key] = list(set(value))
    return input_dict

#函数功能：该函数的主要功能为分析某个项目的函数调用关系
#函数输入：文件夹的路径。
#函数输出：函数的名称及位置以及函数的调用关系
#    function_place_final:函数字典的起始位置
#    function_calls_final:函数字典的调用关系
#    digui_func:          函数字典的递归函数为
def Function_relationship(folder_path):
    try:
        CODE = read_cpp_files(folder_path)
        Function_call_relationship(CODE)         # 分析函数调用关系
        function_place_final = []
        for item in function_place:
            if isinstance(item, list):
                updated_item = [sub_item.replace('::', '.') if isinstance(sub_item, str) else sub_item for sub_item in item]
                function_place_final.append(updated_item)
            else:
                function_place_final.append(item)
        function_calls_final = {}
        function_place.clear()
        for key, value in function_calls.items():
            updated_key = key.replace('::', '.')
            updated_value = [v.replace('::', '.') for v in value]
            function_calls_final[updated_key] = updated_value       #可能存在键值内多个元素重复.function_={'addition': ['dayin'], 'subtraction': ['dayin', 'dayin', 'dayin'], 'multiplication': ['dayin', 'dayin', 'dayin'], 'division': ['dayin']}
            #去除重复元素
        function_calls_final=remove_duplicates_from_dict(function_calls_final)
        function_calls.clear()
        function_calls_final,digui_func=extract_and_remove_equal_key_value_pairs(function_calls_final)   # 查找哪些是递归函数以及非递归函数
        # log_info(f"函数字典的起始位置为：{function_place_final}", Path(__file__).stem)
        # log_info(f"函数字典的调用关系为：{function_calls_final}", Path(__file__).stem)
        # log_info(f"函数字典的递归函数为：{digui_func}", Path(__file__).stem)
        return function_place_final,function_calls_final,digui_func
    except Exception as e:
        log_info(f"警告：函数关系分析失败: {e}", Path(__file__).stem)
        log_info("返回空的分析结果...", Path(__file__).stem)
        return [], {}, []

# 函数功能：函数用于处理C++文件，读取指定文件夹中的C++文件内容，建立函数调用关系，并将函数调用关系和函数位置信息整合在一起。最后返回整合后的函数位置信息列表。
def Function_relationship_place(folder_path):
    try:
        CODE = read_cpp_files(folder_path)
        Function_call_relationship(CODE)
        function_place_final = []
        for item in function_place:
            if isinstance(item, list):
                updated_item = [sub_item.replace('::', '.') if isinstance(sub_item, str) else sub_item for sub_item in item]
                function_place_final.append(updated_item)
            else:
                function_place_final.append(item)
        function_place.clear()
        return function_place_final
    except Exception as e:
        log_info(f"警告：函数位置分析失败: {e}", Path(__file__).stem)
        log_info("返回空的分析结果...", Path(__file__).stem)
        return []


#函数功能：查看：某函数的代码行数,如果是一个数组，则将数组中所有函数的函数相加返回。
#特殊处理：对于类函数处理如下，假设有一个类Animal 里边有一个函数Animal.sub，用类实例化了一个对象 Animal ani    ，在统计代码行数时认为ani.sub=Animal.sub
#函数输入：函数名称（不需要带参数）、func_place
#函数输出：函数的名称及位置以及函数的量关系
def Function_long(fun_name, func_place):
    if isinstance(fun_name, list):
        total_length = 0
        for single_name in fun_name:
            single_name_temp = single_name.split('.')
            found = False
            # 遍历 func_place 中的每个函数信息
            for func in func_place:
                if len(single_name_temp) == 1:
                    # 处理单个函数名的情况
                    if len(func) >= 3 and func[0] == single_name_temp[0]:
                        # 如果找到匹配的函数名，计算其长度并累加到总长度中
                        total_length += (func[2] - func[1] + 1)
                        found = True
                        break
                else:
                    # 处理多个函数名的情况
                    if len(func) >= 3:
                        func_parts = func[0].split('.')
                        if len(func_parts) >= 2 and func_parts[1] == single_name_temp[1]:
                            # 如果找到匹配的函数名，计算其长度并累加到总长度中
                            total_length += (func[2] - func[1] + 1)
                            found = True
                            break
            if not found:
                # 如果未找到匹配的函数名，返回0
                return 0
        # 返回所有匹配函数的总长度
        return total_length
    else:
        # 处理单个函数名的情况（非列表）
        for func in func_place:
            fun_name_split = fun_name.split('.')
            if len(fun_name_split) == 1:
                # 处理单个函数名的情况
                if len(func) >= 3 and func[0] == fun_name_split[0]:
                    # 如果找到匹配的函数名，返回其长度
                    return func[2] - func[1] + 1
            else:
                # 处理多个函数名的情况
                if len(func) >= 3:
                    func_parts = func[0].split('.')
                    if len(func_parts) >= 2 and func_parts[1] == fun_name_split[1]:
                        # 如果找到匹配的函数名，返回其长度
                        return func[2] - func[1] + 1
        # 如果未找到匹配的函数名，返回0
        return 0


#函数功能：查找与某函数相邻的下级函数
#函数输入：查找层级   函数名   func_calls（函数调用关系）
#函数输出：某函数调用关系
def get_function_call_value(function_name, function_dict):
    if isinstance(function_name, list):                     #判断输入函数名是不是一个数组
        result = []
        for name in function_name:                          #对数组中的每个名字进行遍历
            for key, value in function_dict.items():        #根据函数名查字典
                if name == key:                             #如果是，返回字典对应的值
                    result.extend([name,value])
        return result if result else None
    else:
        for key, value in function_dict.items():
            if function_name == key:
                return [function_name,value]
        return None  # 如果函数名不在字典中，返回None或其他适当的值

# 函数功能：查找某个函数调用的所有函数
# 函数的输入：
#   Dict：包含函数调用关系的字典。
#   fun_name：要查找调用关系的函数名。
#   visited（可选）：一个集合，用于跟踪已经访问过的函数，以避免死循环。默认值为 None。
# 函数的输出：一个多维数组，涵盖了函数所有调用的函数以及层级关系。
def find_function_call(Dict, fun_name, visited=None):
    if visited is None:
        visited = set()
    if fun_name in visited:
        return [fun_name]
    if isinstance(fun_name, str):
        visited.add(fun_name)
    else:
        log_info("error!!!  您输入的函数有问题，函数名需要为字符串，例如：'main', 'dayin'", Path(__file__).stem)
        sys.exit()
    #如果函数名中不存在小数点，则不进行小数点后的函数的匹配。
    if '.' not in fun_name:
        if fun_name in Dict:
            value = Dict[fun_name]
            new_value = []
            for item in value:
                result = find_function_call(Dict, item, visited)
                if result is not None:
                    new_value.append(result)
            if not new_value:
                return [fun_name]
            return [fun_name, new_value]
        else:
            return [fun_name]
    else:
        parts = fun_name.split('.')
        for key in Dict.keys():
            if '.' in key:
                ker_parts = key.split('.')
                if ker_parts[1] == parts[1]:
                    value = Dict[key]  # 使用 key 而不是 fun_name
                    new_value = []
                    for item in value:
                        result = find_function_call(Dict, item, visited)
                        if result is not None:
                            new_value.append(result)
                    if not new_value:
                        return [fun_name]
                    return [fun_name, new_value]
        return [fun_name]  # 如果没有找到匹配的键，则返回原始的 fun_name

# 函数功能：查找某个函数调用的所有函数的标准输出
def find_function_calls_stand(Dict, fun_name):
    function_call=find_function_call(Dict, fun_name, visited=None)  #查找函数的被调用关系
    if isinstance(function_call, list) and len(function_call) > 1:
        function_call.pop(0)
        function_call=function_call[0]
    else:
        function_call=[]
    # 移除第一个元素 "main"
    return function_call
# 函数功能：去重
# 函数的输入：列表
# 函数的输出：去重后的列表
def remove_duplicates(lst):
    new_list = []
    if len(lst) == 0:
        return lst
    for item in lst:
        if item not in new_list:
            new_list.append(item)
    return new_list
# 函数功能：查找某个函数被调的所有函数
# 函数的输入：
#   Dict：包含函数调用关系的字典：'Calculator.add': ['tongji', 'dayin.power'], 'Aoteman': ['add', 'subtract', 'multiply', 'divide'], 'moveUp': ['printf'], 'moveDown': ['printf'], 'moveLeft': ['printf'], 'moveRight': ['printf'], 'plane': ['moveUp', 'moveDown', 'moveLeft', 'moveRight'], 'feijikongzhi': ['plane'], 'login': ['plane', 'printNumbersRecursive', 'feijikongzhi'], 'main': ['login', 'calc.add', 'calc.subtract', 'shangdian']}
#   fun_name：要查找调用关系的函数名。
#   visited（可选）：一个集合，用于跟踪已经访问过的函数，以避免死循环。默认值为 None。
# 函数的输出：一个多维数组，涵盖了所有调用该函数的层级关系
def find_function_calleds(Dict, fun_name, visited=None):
    if visited is None:
        visited = set()
    results = []
    # 如果函数名中不存在小数点，则按正常的逻辑进行处理
    if '.' not in fun_name:
        for key, value in Dict.items():
            if key not in visited and fun_name in value:                #如果该键尚未被查找。
                visited.add(key)
                sub_results = find_function_calleds(Dict, key, visited)
                if sub_results:
                    results.append(sub_results)  # 使用 extend 方法将子结果扩展到当前结果列表中
        if not results:
            return [fun_name]
        return [fun_name, results]
    else:
        fun_name_parts = fun_name.split('.')     #要查找的函数名的拆分。
        for key, value in Dict.items():
            if key not in visited:               #如果这个键尚未被查找。
                for value_temp in value:
                    if '.' in value_temp:
                        value_temp_parts=value_temp.split('.')
                        if value_temp_parts[1]== fun_name_parts[1]:
                            visited.add(key)
                            sub_results = find_function_calleds(Dict, key, visited)
                            if sub_results:
                                results.append(sub_results)
        if not results:
            return [fun_name]
        return [fun_name, results]


# 函数功能：根据键值的不同将一个字典拆分成多个字典
# 函数输入：
#        Dict: 字典                例：{'feijikongzhi': ['plane']}
#        name: 函数名称             例：'plane'
# 函数输出：
#        dict_list： 拆分后的字典列表 例：[{'feijikongzhi': ['plane']}, {'feijikongzhi': ['plane']}]
def dict_fenzhi_chaifen(Dict,name):
    aa=copy.deepcopy(Dict)
    dict_list = [aa]  # 将初始字典的副本添加到列表中
    updated_dict = Dict  # 创建一个副本，避免直接修改原始字典
    for key, value_list in updated_dict.items():
        if name in value_list:
            value_list.remove(name)
            dict_list.append(updated_dict.copy())  # 将修改后的字典副本添加到列表中
    return dict_list

# 功能：删除字典中指定元素,排列组合后生成新的字典
# 函数输入：字典，要删除的元素名称    例：{'feijikongzhi': ['plane'],'login':['plane','sdsds'],'main':['plane','sdsd']}     plane
# 函数输出：字典列表               例：[{'feijikongzhi': ['plane'], 'login': ['sdsds'], 'main': ['sdsd']}, {'feijikongzhi': [], 'login': ['plane', 'sdsds'], 'main': ['sdsd']}, {'feijikongzhi': [], 'login': ['sdsds'], 'main': ['plane', 'sdsd']}]
def remove_one_yuansu_from_dict(Dict,name):
    dict_list = []  # 创建一个空列表，用于存储每次修改后的字典副本
    visit=[]
    updated_dict = copy.deepcopy(Dict)  # 创建一个深度副本，避免直接修改原始字典
    # 先找到都有哪些元素包含了key
    for key, value_list in updated_dict.items():
        if name in value_list:       # 如果找到了包含plane的键值对
            visit.append(key)
    for key in visit:
        dict_temp= copy.deepcopy(Dict)
        for key_temp,value_list in dict_temp.items():
            if key_temp != key and name in value_list:
                value_list.remove(name)
        dict_list.append(dict_temp)
    return dict_list

# 函数功能：查找某个函数被调的所有函数的标准输出
# 函数的输入：
#   Dict：包含函数调用关系的字典。
#   fun_name：要查找调用关系的函数名。
# 函数的输出：一个多维数组，涵盖了所有调用该函数的层级关系
def find_function_calleds_stand(Dict, fun_name):
    # 因为因为递归调用一次只能查着一条线,某个函数被多个函数调用时分析其调用关系需进行二次处理
    function_call_fianl=[]
    Dict_list=remove_one_yuansu_from_dict(Dict, fun_name)
    for dict_temp in Dict_list:
        function_call=find_function_calleds(dict_temp, fun_name, visited=None)
        if isinstance(function_call, list) and len(function_call) > 1:
            function_call.pop(0)
            function_call = function_call[0]
        else:
            function_call = [fun_name]
        function_call_fianl.append(function_call)
    return function_call_fianl

# 函数的功能:提取列表中每个元素的第1个值
# 函数的输入:
#          fun_nampt:函数的名称
#          call_list：函数调用了什么函数的列表
#          called_list：函数被什么函数调用的集合。
#          func_place：函数的位置集合
# 函数输出：列表的第一个值
def extract_first_elements(fun_name, call_list, called_list, func_place):
    result = []
    #
    for item in call_list:
        if isinstance(item, list):
            result.append(item[0])
        else:
            result.append(item)
    length_call = Function_long(result, func_place)  # 调用函数长
    result1 = []
    for item in called_list:
        if isinstance(item, list):
            result1.append(item[0])
        else:
            result1.append(item)
    length_called = Function_long(result1, func_place)  # 被调函数长度
    length_func = Function_long(fun_name, func_place)
    # log_info(str(f"(1), Path(__file__).stem){fun_name}调用的数据长度为：{result}={length_call}", end="      ")
    # log_info(str(f"(2), Path(__file__).stem){fun_name}被调用的数据长度为：{result1}={length_called}", end = "      ")
    # log_info(f"(3){fun_name}自身的数据长度为：{length_func}", Path(__file__).stem)
    return length_func + length_called + length_call

# 函数功能：查找某个函数被调的所有函数的标准输出(上一级)
def func_calld_find(name,dictionary):
    keys_with_plane = [key for key, value in dictionary.items() if name in value]
    if len(keys_with_plane) == 0:
        return []
    return keys_with_plane
# 函数功能：查找某个函数调用的所有函数的标准输出(下一级)
def func_call_find(name,dictionary):
    keys_with_plane = [value for key, value in dictionary.items() if name in key]
    if len(keys_with_plane) == 0:
        return []
    return keys_with_plane[0]

##############################################模块最终提供的入口函数###########################################################
# 函数功能：函数的调用和被调用关系的解析
# 函数的输入:
#           folder_path:函数所在的文件夹的位置。例如：'C:/Users/Administrator/Desktop/c++xuexi/shuzhijisuan2.1'
#           fun_name:函数的名称。                      例如：'plane'
# 函数输出：
#           result_func_called：函数被调用关系的列表。   例： ['feijikongzhi', 'login']
#           result_func_calls： 函数调用关系的列表。     例： ['moveUp', 'moveDown', 'moveLeft', 'moveRight']

def func_called_and_call_ship(fun_name,func_calls_guimo):
    func_calld=func_calld_find(fun_name,func_calls_guimo)
    func_calls=func_call_find (fun_name,func_calls_guimo)
    return  func_calld,func_calls

# 函数功能：去重
def remove_duplicates(lst):
    new_list = []
    for item in lst:
        if item not in new_list:
            new_list.append(item)
    return new_list

# 函数功能：函数的调用和被调用关系的解析
# 函数的输入:
#           folder_path:函数所在的文件夹的位置。例如：'C:/Users/Administrator/Desktop/c++xuexi/shuzhijisuan2.1'
#           fun_name:函数的名称。例如：'main'
# 函数输出：
#           result_func_called：函数被调用关系的列表。
#           result_func_calls： 函数调用关系的列表。
#           extracted_values：  该函数的测试规模（上下级函数的行数及自身的行数的和）
#           digui_function:     记录递归数组信息的数组(数字内的所有函数都是递归函数)
### 全局变量
flag_Function_relationship=False                            #用于监控Function_relationship是否执行
func_place_huitu=[]
func_calls_huitu={}
digui_function_huitu=[]
def ceshi_huitu(folder_path,fun_name):
    global func_place_huitu, func_calls_huitu,digui_function_huitu,flag_Function_relationship
    if not flag_Function_relationship:
        # 对某个函数的上级函数进行分析，绘制形成字典
        func_place_huitu, func_calls_huitu,digui_function_huitu = Function_relationship(folder_path)    #软件中所有函数的上下级绘制(仅有一级):{'Calculator.add': ['tongji', 'dayin.power'], 'moveUp': ['printf'], 'moveDown': ['printf'], 'moveLeft': ['printf'], 'moveRight': ['printf'], 'plane': ['moveUp', 'moveDown', 'moveLeft', 'moveRight'], 'feijikongzhi': ['plane'], 'login': ['plane', 'printNumbersRecursive', 'feijikongzhi'], 'main': ['login', 'calc.add', 'calc.subtract', 'shangdian']}

        #log_info(f"函数的调用关系为{func_calls_huitu}", Path(__file__).stem)
        flag_Function_relationship=True
    result_func_calls =  find_function_calls_stand  (func_calls_huitu, fun_name)           # 查找某个函数调用的所有函数的标准输出
    result_func_called = find_function_calleds_stand(func_calls_huitu, fun_name)           # 查找某个函数被调的所有函数的标准输出(已完善)

    result_func_calls=remove_duplicates(result_func_calls)                                 # 去重
    result_func_called=remove_duplicates(result_func_called)                               # 去重
    return [result_func_called,result_func_calls]

################################################测试代码#########################################################
# fun_name ='plane'
# folder_path='C:/Users/Administrator/Desktop/c++xuexi/shuzhijisuan2.1'
# result_func_called,result_func_calls,extracted_values=ceshiguimo(folder_path,fun_name)
# log_info(str(result_func_called), Path(__file__).stem)
# log_info(str(result_func_calls), Path(__file__).stem)







#########################知识拓展##################################
'''
#参数解释
# 子节点【节点数、节点列表】
root_node.child_count: int
root_node.children: list[Node]| None

# 该语法树节点对应代码字符串位置【左闭右开】
root_node.start_byte: int
root_node.end_byte: int

# 语法树节点对应代码 (行, 列) 位置元组
root_node.start_point: tuple[int, int]
root_node.end_point: tuple[int, int]

# 语法树命名节点、命名类型 以及 语法树对应的文本
# 因为具体语法树有代码所有的标记，所以一些符号可能没有类型
# 我猜测该属性可以用于区别具体语法树符号节点，构建抽象语法树
root_node.is_named: bool
root_node.type: str # 没有类型时，这里显示代码原始标记
root_node.text: bytes

# 语法树父节点
root_node.parent: Node| None

# 语法树左兄弟、左命名兄弟
root_node.prev_sibling: Node| None
root_node.prev_named_sibling: Node| None


# 语法树右兄弟、右命名兄弟
root_node.next_sibling: Node| None
root_node.next_named_sibling: Node| None
'''