
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 函数功能：判断一个字符串是否包含函数，如果包含函数就返回函数名，否则返回：False
# 参数：字符串
# 返回值：布尔值，如果包含函数就返回真辅导返回为假
def has_functions(expression):
    if '=' in  expression:                             # int a=dayin（10）； 变为  int a=dayin（20），主要影响的应该是a
        return False
    if '(' in expression and ')' in expression:        # 判断是否可能存在函数
        expression=expression.split('(')[0]            # 保留括号前的内容 例如：'int main(10);'    变为'int main;'
        expression=expression.split(' ')[-1]           # 用空格的表达式进行分割 'int main;'变为 main
        if '=' in expression:                          # 如果最终提取的包含等号则取等号后面的内容 例：'int gg=loginn();'    只得到loginn
            expression=expression.split('=')[1]
        if expression != 'if' and  expression!= 'for' and expression!= 'while' and expression!= 'do' and expression!='switch' and expression!= 'case' and expression!= 'continue' and expression!='return' and expression!= 'else' and expression!='struct' and expression!= 'union':
            if '(' in expression:
                return False
            else:
                return expression
        else:
            return False
    else:
        return False
# 函数功能:将代码差异区分为 函数区和非函数区
# 函数输入： 代码差异区
# 函数返回值： 函数区和非函数区
# 例： 输入：diff_list：['int flag_daji = mubiaodaji(10);', "processInput('a');",'int a=10']
#     输出：func_jihe：[{'int flag_daji = mubiaodaji(10);': ['mubiaodaji']}, {"processInput('a');": ['processInput']}]
#     输出：no_func_ji：['int a=10']
def find_functions(diff_list):
    func_jihe={}
    for item in diff_list:
        if has_functions(item)!= False:
            func_jihe[item]=[has_functions(item)]
    return func_jihe


# 函数功能：如果字典2中存在与字典1相同的元素,将字典2中的元素替换为字典1中的元素
# 函数输入：
#     dict1 = [{'int flag_daji = mubiaodaji(10);': ['mubiaodaji']}, {"processInput('a');": ['processInput']}]
#     dict2 = [{'int flag_daji = mubiaodaji(10);': ['mubiaodaji']}, {"processInput('a');": ['processInput']}]
# 函数输出：
#     dict2：
def replace_elements(dict1, dict2):
    new_dict = dict2.copy()  # 创建一个副本用于存储结果
    for key1, value1 in dict1.items():
        for key2, value2 in dict2.items():
            if key1 == key2:
                new_dict[key2] = value1  # 替换相同键的值
    return new_dict
