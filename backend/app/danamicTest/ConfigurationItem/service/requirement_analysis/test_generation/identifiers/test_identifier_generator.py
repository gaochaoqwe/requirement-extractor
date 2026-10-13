import os
import openpyxl
from openpyxl.styles import PatternFill, Alignment
import numpy as np
import glob
import re

from ..ai_services.ai_content_optimizer import translate_chinese_to_english
from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
# from ....service.project_plan import translate_texts, start_libretranslate_server, stop_libretranslate_server  # 已删除
from .....utils.excel_processing.excel_reader import read_excel_with_sheet
from docx import Document


def check_word_document_xuqiushuoming1(folder_path):
    """
    判断文件夹下是否存在docx文件,如果是就返回对应的路径,如果不是就返回0
    
    Args:
        folder_path: 文件夹路径
        
    Returns:
        str or int: 文件路径或0
    """
    try:
        # 1、docx文档识别
        # 构建文件路径的通配符
        pattern = os.path.join(folder_path, "*需求规格说明*.docx")
        # 使用glob模块获取匹配的文件列表
        matching_files = glob.glob(pattern)
        if matching_files:
            return matching_files[0]
        else:
            return 0  # 或者返回一个空列表 []
    except Exception as e:
        print(f"发生异常: {e}")
        return 0


def extract_software_name1(file_path):
    """
    从文件路径中提取软件名称
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 软件名称
    """
    # 使用正则表达式匹配软件名称部分
    match = re.search(r'[^\\/:*?"<>|\r\n]+软件', file_path)
    if match:
        return match.group(0)
    return 'No_name'

# 函数功能：读取Excel表中第一列和第二列的内容分别形成两个数组
def read_excel_columns(excel_file_path):
    try:
        # 读取Excel文件
        df = read_excel_with_sheet(excel_file_path)
        # 提取第一列和第二列的数据
        column1 = df.iloc[:, 0].tolist()  # 第一列
        column2 = df.iloc[:, 1].tolist()  # 第二列
        return column1, column2
    except Exception as e:
        log_error("读取Excel时发生错误", "file_reader", e)
        return '0', '0'

# 函数功能：读取Excel表中第一列、第二列和第二列的内容分别形成两个数组
# column1：软件名称
# column2：测试项名称
# column3：测试用例名称
def read_excel_columns_three(excel_file_path):
    try:
        # 读取Excel文件
        df = read_excel_with_sheet(excel_file_path)
        # 提取第一列和第二列的数据
        column1 = df.iloc[:, 0].tolist()  # 第一列
        column2 = df.iloc[:, 1].tolist()  # 第二列
        column3 = df.iloc[:, 2].tolist()  # 第二列
        return column1, column2, column3
    except Exception as e:
        log_error("读取Excel时发生错误", "file_reader", e)
        return '0', '0', '0'

#  函数功能： 读取需求文档中的标识号，返回一个数组
#   函数输出：软件标识号对应的数组
#{'SRC-tgfd','No_Find'}
def read_xuqiu_wendang_biaoshihao(file_path, array_list):
    # 1、加载Word文档
    doc = Document(file_path)
    # 2、将段落列表连接成一个字符串
    text_list = []
    for para in doc.paragraphs:
        text_list.append(para.text.strip())
    len_temp=len(text_list)
    ceshibiaoshi_dict=[]
    # 3、寻找段落中需要的内容
    for item in array_list:  # 需要查找的测试项
        log_debug(f"item={item}", "debug")
        find_flag=0          # 判断是否找到标识号
        if not isinstance(item,str):
            break
        item=item.replace(' ','')                    # 去除空格的影响
        for index, item1 in enumerate(text_list):                #  文档的每一行和其在text_list中的索引
            if index>len_temp-10:                                #  如果搜寻的长度大于文档长度减去2，就提前结束
                break
            if item in item1 or item == item1:
                # 如果找到了需要的测试项，检查下一个段落是否有'标识号'
                #****************************************************************************************************************************************
                # 1、寻找测试项对应的测试说明
                if '标识' in text_list[index + 1]:
                    if ':' in text_list[index + 1]:
                        biaoshihao_temp=text_list[index + 1].split(':')[1]
                        biaoshihao_temp=biaoshihao_temp.strip()
                        biaoshihao_temp=biaoshihao_temp.replace('。','')     # 最终需要的软件的测试标项标识号
                        if len(biaoshihao_temp)>0:
                            ceshibiaoshi_dict.append(biaoshihao_temp)
                            find_flag=1
                        else:
                            biaoshihao_temp = text_list[index + 2]
                            biaoshihao_temp = biaoshihao_temp.strip()
                            biaoshihao_temp = biaoshihao_temp.replace('。', '')  # 最终需要的软件的测试标项标识号
                            biaoshihao_temp = biaoshihao_temp.replace(';', '')  # 最终需要的软件的测试标项标识号
                            biaoshihao_temp = biaoshihao_temp.replace('；', '')  # 最终需要的软件的测试标项标识号
                            if len(biaoshihao_temp) > 0:
                                ceshibiaoshi_dict.append(biaoshihao_temp)
                                find_flag = 1
                        break
                    elif '：' in text_list[index + 1]:
                        biaoshihao_temp=text_list[index + 1].split('：')[1]
                        biaoshihao_temp=biaoshihao_temp.strip()
                        biaoshihao_temp=biaoshihao_temp.replace('。','')     # 最终需要的软件的测试标项标识号
                        if len(biaoshihao_temp) > 0:
                            ceshibiaoshi_dict.append(biaoshihao_temp)
                            find_flag = 1
                        else:
                            biaoshihao_temp = text_list[index + 2]
                            biaoshihao_temp = biaoshihao_temp.strip()
                            biaoshihao_temp = biaoshihao_temp.replace('。', '')  # 最终需要的软件的测试标项标识号
                            biaoshihao_temp = biaoshihao_temp.replace(';', '')  # 最终需要的软件的测试标项标识号
                            biaoshihao_temp = biaoshihao_temp.replace('；', '')  # 最终需要的软件的测试标项标识号
                            if len(biaoshihao_temp) > 0:
                                ceshibiaoshi_dict.append(biaoshihao_temp)
                                find_flag = 1
                        break
        if find_flag==0:
            ceshibiaoshi_dict.append('No_Find')
    return ceshibiaoshi_dict


# 函数功能；读取项目策划表中的内容，生成对应的英语标识
# 函数输入：
def ceshibiaoshi_duqu(excel_file_path):
    ceshibiaoshi=[]
    sheet_name = '项目策划表'
    df = read_excel_with_sheet(excel_file_path, sheet_name=sheet_name)
    len_value = df.iloc[6, 4]     # 采集的需求变更个数
    ruanjian_name= df.iloc[0, 4]  # 软件名称
    ruanjian_xuqiu = df.iloc[16:16 + len_value, 2].reset_index(drop=True).tolist()                         # 软件需求转换为列表
    ruanjian_xuqiu= [item for item in ruanjian_xuqiu if isinstance(item, str)]                             # 删除软件需求中不是字符串的元素
    len_value=len(ruanjian_xuqiu)                                                                          # 对提供的测试项数量进行一次校正
    # 对策划表的测试项标识进行填充
    try:
        # 如果软件标识已经写完了,就不再重新填充
        if len(ruanjian_xuqiu) == 0:      # 每点击一次都自动进行测试标识填充
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb['项目策划表']
            # 设置单元格样式，使其支持换行
            sheet.cell(row=16 + len_value + 2, column=3).value = f"文档审查范围：\n1.《{ruanjian_name}需求规格说明》；\n2.《{ruanjian_name}研制任务书》；\n3.《{ruanjian_name}设计说明》；"
            sheet.cell(row=16 + len_value + 3, column=3).value = "静态分析范围:\n全部手写代码；"
            sheet.cell(row=16 + len_value + 4, column=3).value = "代码审查范围:\n全部手写代码；"
            sheet.cell(row=16 + len_value + 5, column=3).value = "环境其他要求:\n本次测试使用产品加检测仪环境；"
            sheet.cell(row=16 + len_value + 6, column=3).value = "其他要求:\n无；"
            wb.save(excel_file_path)
            log_warning("软件需求数为0，无需进行编号", "identifier")
            return 1
        else:
            # 1、分析是否存在软件需求规格说明
            file_path_daima_lujing = "D:/baxiang_ceshi/被测代码路径代码.txt"  # Flash文件的位置
            # 直接读取文件路径
            try:
                with open(file_path_daima_lujing, 'r', encoding='utf-8') as f:
                    xuanze_value = [line.strip() for line in f.readlines()]
            except FileNotFoundError:
                xuanze_value = ["", "", ""]  # 默认值
            
            file_path_xuqiu_word = check_word_document_xuqiushuoming1(xuanze_value[2] if len(xuanze_value) > 2 else "")  # 读取软件需求规格说明内容 :如果失败返回零,如果成功返回路径
            if file_path_xuqiu_word == 0:        # 如果没有找到软件需求规格说明
                find_flag=0
                log_warning("没有找到软件需求规格说明", "file_reader")
            else:
                ruanjian_name = extract_software_name1(file_path_xuqiu_word)
                try:
                    # 1、加载Word文档
                    doc = Document(file_path_xuqiu_word)
                    find_flag = 1
                    log_info("找到软件需求规格说明", "file_reader")
                except Exception as e:
                    find_flag = 0
                    log_warning("没有找到软件需求规格说明", "file_reader")
            # 1、如果没有找到软件需求规格说明，就使用AI翻译读取软件标识
            if find_flag==0:         # 如果没有找到软件需求规格说明
                # 🔧 修复：离线翻译服务已删除，直接使用AI翻译
                log_info("使用AI翻译处理需求标识", "translator")
                temp_count = 0
                for item in ruanjian_xuqiu:  # 软件需求逐一分析
                    # 调用大模型进行翻译
                    fanyijieguo = translate_chinese_to_english(item)
                    if fanyijieguo == None:
                        ceshibiaoshi.append(f'SRC-name{temp_count}')
                        temp_count += 1
                        log_error("AI翻译失败，使用默认标识", "translator")
                    else:
                        # 检查重复
                        if fanyijieguo in ceshibiaoshi:
                            fanyijieguo = f'SRC-name-Dup{temp_count}'
                        ceshibiaoshi.append(fanyijieguo)
                        temp_count += 1
            # 2、如果存在软件需求规格说明，从软件需求规格说明中读取软件标识
            else:
                ceshibiaoshi_duqu=read_xuqiu_wendang_biaoshihao(file_path_xuqiu_word, ruanjian_xuqiu)        #{'SRC-tgfd','No_Find'}
                # 🔧 修复：简化逻辑，优先使用文档提取的标识，否则使用AI翻译
                if len(ceshibiaoshi_duqu) == len(ruanjian_xuqiu):
                    temp_count = 0
                    for item in ruanjian_xuqiu:  # 软件需求逐一分析
                        # 如果已经从需求文档中读到了软件标识，就直接使用
                        if temp_count < len(ceshibiaoshi_duqu) and ceshibiaoshi_duqu[temp_count] != 'No_Find':
                            wenti_xuqiu_miaoshu = ceshibiaoshi_duqu[temp_count]
                            if wenti_xuqiu_miaoshu in ceshibiaoshi:
                                wenti_xuqiu_miaoshu = 'SRC-name-Dup' + str(temp_count)
                            ceshibiaoshi.append(wenti_xuqiu_miaoshu)
                        else:
                            # 否则使用AI翻译
                            fanyijieguo = translate_chinese_to_english(item)
                            if fanyijieguo == None:
                                wenti_xuqiu_miaoshu = 'SRC-Name' + str(temp_count)
                                ceshibiaoshi.append(wenti_xuqiu_miaoshu)
                                log_error("AI翻译失败，使用默认标识", "translator")
                            else:
                                if fanyijieguo in ceshibiaoshi:
                                    fanyijieguo = f'SRC-name-Dup{temp_count}'
                                ceshibiaoshi.append(fanyijieguo)
                        temp_count += 1
                # 3、如果从软件需求规格说明中读取的标识不正确，就使用AI翻译处理
                else:
                    # 🔧 修复：使用AI翻译替代离线翻译服务
                    log_info("使用AI翻译处理需求标识（备用方案）", "translator")
                    temp_count = 0
                    for item in ruanjian_xuqiu:  # 软件需求逐一分析
                        # 调用大模型进行翻译
                        fanyijieguo = translate_chinese_to_english(item)
                        if fanyijieguo == None:
                            ceshibiaoshi.append(f'SRC-name{temp_count}')
                            temp_count += 1
                            log_error("AI翻译失败，使用默认标识", "translator")
                        else:
                            # 检查重复
                            if fanyijieguo in ceshibiaoshi:
                                fanyijieguo = f'SRC-name-Alt{temp_count}'
                            ceshibiaoshi.append(fanyijieguo)
                            temp_count += 1
            # 对策划表的测试项标识进行填充
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb['项目策划表']
            #  设置Excel表格的颜色为红色
            light_red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
            light_blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")  # 与软件配置项信息表保持一致的蓝色
            # 对测试标识的结果进行二次清洗
            for i in range(len(ceshibiaoshi)):
                if '；' in ceshibiaoshi[i]:
                    ceshibiaoshi[i] = ceshibiaoshi[i].replace('；', '')
                if ';' in ceshibiaoshi[i]:
                    ceshibiaoshi[i] = ceshibiaoshi[i].replace(';', '')
                if '。' in ceshibiaoshi[i]:
                    ceshibiaoshi[i] = ceshibiaoshi[i].replace('。', '')
                if '’' in ceshibiaoshi[i]:
                    ceshibiaoshi[i] = ceshibiaoshi[i].replace('‘', '')
            # 设置单元格样式，使其支持换行
            for i in range(len(ceshibiaoshi)):
                if 'SRC-name-Chong' in ceshibiaoshi[i] or 'SRC-Name-fanyicuowu' in ceshibiaoshi[i]:
                    sheet.cell(row=16 + i + 2, column=14).value = ceshibiaoshi[i]
                    sheet.cell(row=16 + i + 2, column=14).fill = light_red_fill       # 将存在重复的列表颜色改为红色
                else:
                    sheet.cell(row=16 + i + 2, column=14).value = ceshibiaoshi[i]
                    sheet.cell(row=16 + i + 2, column=14).fill = light_blue_fill  # 参数row和column分别指定单元格的行号和列号
            sheet.cell(row=16 + len_value + 2,column=3).value = f"文档审查范围：\n1.《{ruanjian_name}需求规格说明》；\n2.《{ruanjian_name}研制任务书》；\n3.《{ruanjian_name}设计说明》；"
            sheet.cell(row=16 + len_value + 3, column=3).value = "静态分析范围:\n全部手写代码；"
            sheet.cell(row=16 + len_value + 4, column=3).value = "代码审查范围:\n全部手写代码；"
            sheet.cell(row=16 + len_value + 5, column=3).value = "环境其他要求:\n本次测试使用产品加检测仪环境；"
            sheet.cell(row=16 + len_value + 6, column=3).value = "其他要求:\n无；"
            # 打开项目策划表对项目策划表中的内容进行填空
            sheet1 = wb['软件配置项信息']
            sheet1.cell(row=31, column=3, value= len_value)       # 软件测试项数目
            sheet1.cell(row=40, column=3, value=len_value)        # 被测软件需求捕获总数
            sheet1.cell(row=41, column=3, value=len_value)        # 被测软件需求测试总数
            sheet1.cell(row=48, column=3, value=len_value*0.2)    # 被测软件需求测试总数
            # 对重新填写后的Excel表进保存
            wb.save(excel_file_path)
            log_info("测试标识编号完成", "identifier")
            return ceshibiaoshi
    except Exception as e:                                        # 如果测试标识读取失败,就自动进行测试表单填充
        log_error("测试标识编写过程中出现故障", "identifier")
        log_error("读取策划表时发生错误", "file_reader", e)


# # 函数功能；读取项目策划表中的内容
# # 函数输入：
# def ceshibiaoshi_duqu(excel_file_path):
#     ceshibiaoshi=[]
#     biaoshishujuku=r'D:\baxiang_ceshi\DataBase\测试用例标准数据库.xlsx'
#     sheet_name = '项目策划表'
#     df = read_excel_with_sheet(excel_file_path, sheet_name=sheet_name)
#     len_value = df.iloc[6, 4]     # 采集的需求变更个数
#     ruanjian_name= df.iloc[0, 4]  # 软件名称
#     ruanjian_xuqiu = df.iloc[16:16 + len_value, 2].reset_index(drop=True).tolist()                         # 软件需求转换为列表
#     ruanjian_xuqiu= [item for item in ruanjian_xuqiu if isinstance(item, str)]                             # 删除软件需求中不是字符串的元素
#     len_value=len(ruanjian_xuqiu)                                                                          # 对提供的测试项数量进行一次校正
#     # 对策划表的测试项标识进行填充
#     try:
#         # 如果软件标识已经写完了,就不再重新填充
#         if len(ruanjian_xuqiu) == 0:      # 每点击一次都自动进行测试标识填充
#             wb = openpyxl.load_workbook(excel_file_path)
#             sheet = wb['项目策划表']
#             # 设置单元格样式，使其支持换行
#             sheet.cell(row=16 + len_value + 2, column=3).value = f"文档审查范围：\n1.《{ruanjian_name}需求规格说明》；\n2.《{ruanjian_name}研制任务书》；\n3.《{ruanjian_name}设计说明》；"
#             sheet.cell(row=16 + len_value + 3, column=3).value = "静态分析范围:\n全部手写代码；"
#             sheet.cell(row=16 + len_value + 4, column=3).value = "代码审查范围:\n全部手写代码；"
#             sheet.cell(row=16 + len_value + 5, column=3).value = "环境其他要求:\n本次测试使用产品加检测仪环境；"
#             sheet.cell(row=16 + len_value + 6, column=3).value = "其他要求:\n无；"
#             wb.save(excel_file_path)
#             print("软件需求数为0，无需进行编号!!!!!!!!!!!!!!!!!!!")
#             return 1
#         else:
#             # 启动离线翻译服务器
#             server_process = start_libretranslate_server()
#             # 数据库数据录取
#             column1, column2 = read_excel_columns(biaoshishujuku)           # 读取数据库中软件标识的内容
#             if column1 =='0':
#                 combined_dict={'error':'null'}
#             else:
#                 combined_dict = dict(zip(column1, column2))                 # 将两个数组合成一个字典
#             temp_count = 0
#             print(f"combined_dict={combined_dict}")
#             # 根据数据库的内容对测试标识进行填充
#             for item in ruanjian_xuqiu:                                 # 软件需求逐一分析
#                 xuqiu_find=0                                            # 是否在字典中找到测试标识(0表示没找到,1表示找到了)
#                 for item1 in combined_dict.keys():                      # 打印对字典中的键值进行逐一列举
#                     if '&' in item1:
#                         item1_fenge = item1.split('&')
#                         if len(item1_fenge) == 2:
#                             if item1_fenge[0] in item and item1_fenge[1] in item:             # 如果测试项名称中存在字典中的关键词   :item1_fenge[0]:字典关键词    item软件需求
#                                 if combined_dict[item1] in ceshibiaoshi:  # 分析该测试样标识是否存在，如果存在就不进行读取
#                                     wenti_xuqiu_miaoshu = 'SRC-name-Chong' + str(temp_count)
#                                     ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                                     xuqiu_find = 1
#                                     temp_count = temp_count + 1
#                                     break
#                                 else:  # 如果不存在就将其读取为正常标识
#                                     ceshibiaoshi.append(combined_dict[item1])
#                                     xuqiu_find = 1
#                                     break
#                         elif len(item1_fenge) == 3:
#                             if item1_fenge[0] in item and item1_fenge[1] in item and item1_fenge[2] in item:
#                                 if combined_dict[item1] in ceshibiaoshi:  # 分析该测试样标识是否存在，如果存在就不进行读取
#                                     wenti_xuqiu_miaoshu = 'SRC-name-Chong' + str(temp_count)
#                                     ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                                     xuqiu_find = 1
#                                     temp_count = temp_count + 1
#                                     break
#                             else:  # 如果不存在就将其读取为正常标识
#                                 ceshibiaoshi.append(combined_dict[item1])
#                                 xuqiu_find = 1
#                                 break
#                         else:
#                             if item1_fenge[0] in item and item1_fenge[1] in item:  # 如果测试项名称中存在字典中的关键词
#                                 if combined_dict[item1] in ceshibiaoshi:  # 分析该测试样标识是否存在，如果存在就不进行读取
#                                     wenti_xuqiu_miaoshu = 'SRC-name-Chong' + str(temp_count)
#                                     ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                                     xuqiu_find = 1
#                                     temp_count = temp_count + 1
#                                     break
#                                 else:  # 如果不存在就将其读取为正常标识
#                                     ceshibiaoshi.append(combined_dict[item1])
#                                     xuqiu_find = 1
#                                     break
#                     elif '||' in item1:
#                         item1_fenge = item1.split('||')
#                         if len(item1_fenge) == 2:
#                             if item1_fenge[0] in item or item1_fenge[1] in item:  # 如果测试项名称中存在字典中的关键词
#                                 if combined_dict[item1] in ceshibiaoshi:  # 分析该测试样标识是否存在，如果存在就不进行读取
#                                     wenti_xuqiu_miaoshu = 'SRC-name-Chong' + str(temp_count)
#                                     ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                                     xuqiu_find = 1
#                                     temp_count = temp_count + 1
#                                     break
#                                 else:  # 如果不存在就将其读取为正常标识
#                                     ceshibiaoshi.append(combined_dict[item1])
#                                     xuqiu_find = 1
#                                     break
#                         elif len(item1_fenge) == 3:
#                             if item1_fenge[0] in item or item1_fenge[1] in item or item1_fenge[2] in item:
#                                 if combined_dict[item1] in ceshibiaoshi:  # 分析该测试样标识是否存在，如果存在就不进行读取
#                                     wenti_xuqiu_miaoshu = 'SRC-name-Chong' + str(temp_count)
#                                     ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                                     xuqiu_find = 1
#                                     temp_count = temp_count + 1
#                                     break
#                             else:  # 如果不存在就将其读取为正常标识
#                                 ceshibiaoshi.append(combined_dict[item1])
#                                 xuqiu_find = 1
#                                 break
#                         else:
#                             if item1_fenge[0] in item or item1_fenge[1] in item:  # 如果测试项名称中存在字典中的关键词
#                                 if combined_dict[item1] in ceshibiaoshi:  # 分析该测试样标识是否存在，如果存在就不进行读取
#                                     wenti_xuqiu_miaoshu = 'SRC-name-Chong' + str(temp_count)
#                                     ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                                     xuqiu_find = 1
#                                     temp_count = temp_count + 1
#                                     break
#                                 else:  # 如果不存在就将其读取为正常标识
#                                     ceshibiaoshi.append(combined_dict[item1])
#                                     xuqiu_find = 1
#                                     break
#                     else:
#                         if item1 in item:  # 如果测试项名称中存在字典中的关键词
#                             if combined_dict[item1] in ceshibiaoshi:  # 分析该测试样标识是否存在，如果存在就不进行读取
#                                 wenti_xuqiu_miaoshu = 'SRC-name-Chong' + str(temp_count)
#                                 ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                                 xuqiu_find = 1
#                                 temp_count = temp_count + 1
#                                 break
#                             else:  # 如果不存在就将其读取为正常标识
#                                 ceshibiaoshi.append(combined_dict[item1])
#                                 xuqiu_find = 1
#                                 break
#                                 # 如果字典中不包含该关键词
#                 if xuqiu_find==0:
#                     # 示例用法
#                     if server_process==-1:
#                         wenti_xuqiu_miaoshu='SRC-Name'+str(temp_count)
#                         ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                         temp_count = temp_count + 1
#                     else:
#                         texts_to_translate = [item]
#                         wenti_xuqiu_miaoshu = translate_texts(texts_to_translate)
#                         wenti_xuqiu_miaoshu=wenti_xuqiu_miaoshu[0]
#                         ceshibiaoshi.append(wenti_xuqiu_miaoshu)
#                         temp_count = temp_count + 1
#             # 关闭服务器
#             stop_libretranslate_server(server_process)
#             # 对策划表的测试项标识进行填充
#             wb = openpyxl.load_workbook(excel_file_path)
#             sheet = wb['项目策划表']
#             #  设置Excel表格的颜色为红色
#             light_red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
#             # 设置单元格样式，使其支持换行
#             for i in range(len(ceshibiaoshi)):
#                 if 'SRC-name-Chong' in ceshibiaoshi[i]:
#                     sheet.cell(row=16 + i + 2, column=14).value = ceshibiaoshi[i]
#                     sheet.cell(row=16 + i + 2, column=14).fill = light_red_fill       # 将存在重复的列表颜色改为红色
#                 else:
#                     sheet.cell(row=16 + i + 2, column=14).value = ceshibiaoshi[i]
#             sheet.cell(row=16 + len_value + 2,column=3).value = f"文档审查范围：\n1.《{ruanjian_name}需求规格说明》；\n2.《{ruanjian_name}研制任务书》；\n3.《{ruanjian_name}设计说明》；"
#             sheet.cell(row=16 + len_value + 3, column=3).value = "静态分析范围:\n全部手写代码；"
#             sheet.cell(row=16 + len_value + 4, column=3).value = "代码审查范围:\n全部手写代码；"
#             sheet.cell(row=16 + len_value + 5, column=3).value = "环境其他要求:\n本次测试使用产品加检测仪环境；"
#             sheet.cell(row=16 + len_value + 6, column=3).value = "其他要求:\n无；"
#             wb.save(excel_file_path)
#             log_info("测试标识编号完成", "identifier")
#             return ceshibiaoshi
#     except Exception as e:                                        # 如果测试标识读取失败,就自动进行测试表单填充
#         log_error("测试标识编写过程中出现故障", "identifier")
#         log_error("读取策划表时发生错误", "file_reader", e)