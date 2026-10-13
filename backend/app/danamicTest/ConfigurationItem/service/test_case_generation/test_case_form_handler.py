"""
配置项测试用例表单处理器

提供测试用例表单生成相关功能。
"""

import sys
from pathlib import Path
import datetime

# 添加路径以导入其他模块
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from .test_case_generator import generate_test_yongli, generate_test_yonglisheji, generate_test_cases
except ImportError:
    try:
        from test_case_generator import generate_test_yongli, generate_test_yonglisheji, generate_test_cases
    except ImportError:
        # 如果都导入失败，定义简单的替代函数
        def generate_test_yongli(*args, **kwargs):
            return "通过检测仪发送测试指令，验证功能正确性"
        
        def generate_test_yonglisheji(*args, **kwargs):
            return "预期结果：软件功能实现正常"
            
        def generate_test_cases(*args, **kwargs):
            return (True, [["默认测试用例", "验证功能正确性", "执行测试步骤", "预期结果正常"]])

import requests
import json
# 配置相关参数
try:
    from ...utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 🔧 修复：添加边框样式导入
from openpyxl.styles import PatternFill, Alignment, Border, Side


def generate_test_cases_for_form(cehisixiang_name_temp: str, value_mioashu: str, 
                                AI_fenx_flag_Anniu: int, jianceyi_flag: str, 
                                ceshileixing_remp: str) -> tuple:
    """
    为表单生成测试用例 - 统一调用一次AI生成完整测试用例
    
    Args:
        cehisixiang_name_temp: 测试项名称
        value_mioashu: 需求描述
        AI_fenx_flag_Anniu: AI分析标志
        jianceyi_flag: 检测仪标志
        ceshileixing_remp: 测试类型
        
    Returns:
        tuple: (统一的测试用例结果, 统一的测试用例结果) - 为了向后兼容返回两个相同的结果
    """
    log_debug(f"开始生成测试用例 - 测试项: {cehisixiang_name_temp}, 类型: {ceshileixing_remp}", "test_case_form_handler")
    
    # 如果启用AI分析
    if AI_fenx_flag_Anniu == 1:
        if len(value_mioashu) > 5:
            try:
                for i in range(1, 5):
                    # 🔧 修复：确保value_mioashu是字符串类型
                    if isinstance(value_mioashu, dict):
                        # 如果是字典，尝试获取描述内容
                        value_mioashu_str = value_mioashu.get('description', '') or value_mioashu.get('content', '') or str(value_mioashu)
                        log_debug(f"value_mioashu是字典类型，提取内容: {value_mioashu_str[:100]}...", "test_case_form_handler")
                    else:
                        value_mioashu_str = str(value_mioashu) if value_mioashu is not None else ""
                    
                    value_mioashu_clean = value_mioashu_str.replace('\n', '')
                    
                    log_debug(f"第{i}次尝试AI生成 - 需求描述: {value_mioashu_clean[:50]}...", "test_case_form_handler")
                    
                    # 🔧 统一调用一次AI生成测试用例（支持AI开关）
                    # 获取AI配置
                    from ...utils.ai_switch_controller.ai_switch_controller import get_ai_controller, AIModule
                    ai_controller = get_ai_controller()
                    ai_config = ai_controller.get_ai_config(AIModule.TEST_CASE_GENERATION)
                    
                    unified_result = generate_test_cases(
                        ceshixiang_name=cehisixiang_name_temp, 
                        requirement_description=value_mioashu_clean, 
                        test_content=value_mioashu_clean,
                        ceshileixing=ceshileixing_remp, 
                        jianceyi_flag=jianceyi_flag,
                        ai_config=ai_config  # 传递AI配置
                    )
                    
                    log_debug(f"AI生成结果: {unified_result}", "test_case_form_handler")
                    
                    # 检查是否成功生成
                    if unified_result[0] == False or unified_result == 'error':
                        log_debug(f"第{i}次尝试失败，重试中...", "test_case_form_handler")
                        continue
                    else:
                        log_info(f"第{i}次尝试成功生成测试用例", "test_case_form_handler")
                        # 为了向后兼容，返回两个相同的结果
                        return unified_result, unified_result
                        
                # 所有尝试都失败，使用默认值
                log_info('AI分析出错！！！！，生成的结果为error!!!!', Path(__file__).stem)
                default_result = set_default_test_cases(cehisixiang_name_temp, jianceyi_flag)
                return default_result, default_result
                
            except Exception as e:
                log_info(f'AI分析出错,模型没有被调起来！！！！！！！: {e}', Path(__file__).stem)
                default_result = set_default_test_cases(cehisixiang_name_temp, jianceyi_flag)
                return default_result, default_result
        else:
            log_info('需求描述过短，使用默认测试用例', Path(__file__).stem)
            default_result = set_default_test_cases(cehisixiang_name_temp, jianceyi_flag)
            return default_result, default_result
    else:
        log_info('未启用AI分析，使用默认测试用例', Path(__file__).stem)
        default_result = set_default_test_cases(cehisixiang_name_temp, jianceyi_flag)
        return default_result, default_result


def set_default_test_cases(cehisixiang_name_temp: str, jianceyi_flag: str) -> tuple:
    """
    设置默认的测试用例
    
    Args:
        cehisixiang_name_temp: 测试项名称
        jianceyi_flag: 检测仪标志
        
    Returns:
        tuple: (测试用例, 测试用例设计)
    """
    if jianceyi_flag == '有检测仪':
        if '故障' in cehisixiang_name_temp or '报警检测' in cehisixiang_name_temp:
            ceshi_yongli = f'1、通过代码插桩设置软件故障；2、通过检测仪发送自检指令；3、通过检测仪状态监控界面查看测试软件{cehisixiang_name_temp}功能实现是否正常'
            ceshi_yonglisheji = f'1、预期结果：软件{cehisixiang_name_temp}功能实现正常；2、测试步骤：通过代码插桩设置软件故障，通过检测仪发送自检指令，通过检测仪状态监控界面查看测试软件{cehisixiang_name_temp}功能实现是否正常'
        else:
            ceshi_yongli = f'1、通过检测仪发送测试指令；2、通过检测仪状态监控界面查看测试软件{cehisixiang_name_temp}功能实现是否正常'
            ceshi_yonglisheji = f'1、预期结果：软件{cehisixiang_name_temp}功能实现正常；2、测试步骤：通过检测仪发送测试指令，通过检测仪状态监控界面查看测试软件{cehisixiang_name_temp}功能实现是否正常'
    else:
        ceshi_yongli = f'1、启动被测软件；2、执行{cehisixiang_name_temp}相关操作；3、观察软件运行状态和输出结果'
        ceshi_yonglisheji = f'1、预期结果：软件{cehisixiang_name_temp}功能实现正常；2、测试步骤：启动被测软件，执行{cehisixiang_name_temp}相关操作，观察软件运行状态和输出结果'
    
    return ceshi_yongli, ceshi_yonglisheji


def get_test_time_info():
    """
    获取测试时间相关信息
    
    Returns:
        tuple: (用例设计时间, 测试执行时间, 年月格式)
    """
    current_date = datetime.date.today()
    yonglisheji_time = current_date.strftime('%Y/%m/%d')  # 当前日期
    # 测试执行时间设置为第二天
    ceshi_time = (current_date + datetime.timedelta(days=1)).strftime('%Y/%m/%d')
    # 年月格式
    ceshi_year_month = current_date.strftime('%Y-%m')
    return yonglisheji_time, ceshi_time, ceshi_year_month


def write_test_cases_to_excel(sheet, row_xuhao: int, index: int, allkeys: list, 
                            ruanjian_name: str, ruanjian_version: str, 
                            zhangjiehao: list, ceshi_xuqiu_biaoshi: str, 
                            ruanjian_xuqiu_biaoshi: list, leixing_biaoshi: str,
                            ceshileixing_temp: str, ceshixiang_miaoshu: str, 
                            ceshixiang_fangfa: str, ceshi_yongli: str, 
                            ceshi_yonglisheji: str, ceshiren_name: str = '测试人员',
                            zhuguan_name: str = '主管', temp_temp_count: int = 1,
                            requirement_tracking: str = None, test_item_name: str = None,
                            test_item_identifier: str = None, ai_test_case_name: str = None):
    """
    将测试用例写入Excel表格 - 完整版本（适配真实的测试用例单工作表）
    
    [ALERT] 重要：此函数适配真实的"测试用例单"工作表，有91列
    表头结构：ID、序号、软件配置项名称、被测软件版本、测试轮次、需求追溯、测试项名称、
            测试项标识、测试用例名称、测试用例编号、测试类型、测试描述、预置条件、
            前提与约束、终止条件、输入条件、预期结果、通过准则、用例设计人、校对人、
            设计时间、校对时间、测试人员、监督人员、测试时间、测试结果、测试结论、
            问题报告单编号、执行年月、用例发现问题数...
    
    Args:
        sheet: Excel工作表对象（应该是"测试用例单"工作表）
        row_xuhao: 行号
        index: 测试项索引
        allkeys: 测试项名称列表
        ruanjian_name: 软件名称
        ruanjian_version: 软件版本
        zhangjiehao: 章节号列表
        ceshi_xuqiu_biaoshi: 测试需求标识
        ruanjian_xuqiu_biaoshi: 软件需求标识列表
        leixing_biaoshi: 类型标识
        ceshileixing_temp: 测试类型
        ceshixiang_miaoshu: 测试项描述
        ceshixiang_fangfa: 测试方法
        ceshi_yongli: 测试用例
        ceshi_yonglisheji: 测试用例设计
        ceshiren_name: 测试人员名称
        zhuguan_name: 主管名称
        temp_temp_count: 用例计数
        requirement_tracking: 需求追溯信息
        test_item_name: 测试项名称
        test_item_identifier: 测试项标识
        ai_test_case_name: AI生成的测试用例名称
    """
    
    # 获取时间信息
    yonglisheji_time, ceshi_time, ceshi_nianyue = get_test_time_info()
    
    # [FIX] 修复：测试用例名称直接使用AI返回的名称
    if ai_test_case_name:
        ceshiyongliname = ai_test_case_name
    else:
        # 向后兼容：如果没有AI测试用例名称，使用原逻辑
        ceshiyongliname = f"{allkeys[index]}测试用例{temp_temp_count}"
    
    # [FIX] 修复：使用测试项标识生成测试用例编号
    if test_item_identifier:
        # 使用传递的测试项标识
        test_case_id = f"{test_item_identifier}-{temp_temp_count:02d}"
    else:
        # 向后兼容：使用原逻辑
        if index < len(ruanjian_xuqiu_biaoshi) and ruanjian_xuqiu_biaoshi[index]:
            test_item_id = ceshi_xuqiu_biaoshi + ruanjian_xuqiu_biaoshi[index] + leixing_biaoshi
        else:
            test_item_id = ceshi_xuqiu_biaoshi + 'name' + str(index) + leixing_biaoshi
        test_case_id = f"{test_item_id}-{temp_temp_count:02d}"
    
    # 根据真实的"测试用例单"工作表表头进行填充
    try:
        from openpyxl.styles import Alignment, PatternFill
        
        # [FIX] 创建标准蓝色填充样式，与其他表单保持一致
        light_blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")
        
        # 🔧 修复：创建统一的边框样式，确保所有填充的单元格都有边框
        standard_border = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
        
        # 核心信息列（1-12）
        # [FIX] 修复：第一列ID不需要填数据
        # sheet.cell(row=row_xuhao, column=1, value=f"TC{index+1:03d}")  # A: ID - 不填充
        
        # [FIX] 为所有填充的单元格添加蓝色背景
        cell_b = sheet.cell(row=row_xuhao, column=2, value=index + 1)  # B: 序号
        cell_b.fill = light_blue_fill
        cell_b.border = standard_border
        
        cell_c = sheet.cell(row=row_xuhao, column=3, value=ruanjian_name)  # C: 软件配置项名称
        cell_c.fill = light_blue_fill
        cell_c.border = standard_border
        
        # [FIX] 修复：第四列版本不需要带V，直接填前端传过来的版本号
        cell_d = sheet.cell(row=row_xuhao, column=4, value=ruanjian_version)  # D: 被测软件版本（不带V）
        cell_d.fill = light_blue_fill
        cell_d.border = standard_border
        
        # [FIX] 修复：测试轮次默认填"第一轮"，并垂直居中
        test_round_cell = sheet.cell(row=row_xuhao, column=5, value='第一轮')  # E: 测试轮次
        test_round_cell.alignment = Alignment(vertical='center', horizontal='center')
        test_round_cell.fill = light_blue_fill
        test_round_cell.border = standard_border
        
        # [FIX] 修复：需求追溯填"软件需求规格说明条目追踪关系"内容
        requirement_trace_value = requirement_tracking if requirement_tracking else (zhangjiehao[index] if index < len(zhangjiehao) else '无')
        cell_f = sheet.cell(row=row_xuhao, column=6, value=requirement_trace_value)  # F: 需求追溯
        cell_f.fill = light_blue_fill
        cell_f.border = standard_border
        
        # [FIX] 修复：测试项名称和测试项标识填对应的需求分析表内容
        test_item_name_value = test_item_name if test_item_name else allkeys[index]
        test_item_id_value = test_item_identifier if test_item_identifier else test_item_id
        cell_g = sheet.cell(row=row_xuhao, column=7, value=test_item_name_value)  # G: 测试项名称
        cell_g.fill = light_blue_fill
        cell_g.border = standard_border
        
        cell_h = sheet.cell(row=row_xuhao, column=8, value=test_item_id_value)  # H: 测试项标识
        cell_h.fill = light_blue_fill
        cell_h.border = standard_border
        
        cell_i = sheet.cell(row=row_xuhao, column=9, value=ceshiyongliname)  # I: 测试用例名称
        cell_i.fill = light_blue_fill
        cell_i.border = standard_border
        
        cell_j = sheet.cell(row=row_xuhao, column=10, value=test_case_id)  # J: 测试用例编号
        cell_j.fill = light_blue_fill
        cell_j.border = standard_border
        
        cell_k = sheet.cell(row=row_xuhao, column=11, value=ceshileixing_temp)  # K: 测试类型
        cell_k.fill = light_blue_fill
        cell_k.border = standard_border
        
        cell_l = sheet.cell(row=row_xuhao, column=12, value=ceshixiang_miaoshu)  # L: 测试描述
        cell_l.fill = light_blue_fill
        cell_l.border = standard_border
        
        # 测试条件和方法（13-18）
        cell_m = sheet.cell(row=row_xuhao, column=13, value="被测软件正常加载，检测仪、调试计算机上电、测试环境连接正常")  # M: 预置条件
        cell_m.fill = light_blue_fill
        cell_m.border = standard_border
        
        cell_n = sheet.cell(row=row_xuhao, column=14, value='无')  # N: 前提与约束
        cell_n.fill = light_blue_fill
        cell_n.border = standard_border
        
        cell_o = sheet.cell(row=row_xuhao, column=15, 
                  value="正常终止条件:按正常测试步骤完成测试过程.\n异常终止条件:被测软件功能实现错误、测试用例设计错误、操作错误、测试环境出现异常情况。")  # O: 终止条件
        cell_o.fill = light_blue_fill
        cell_o.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        cell_o.border = standard_border
        
        # [FIX] 修复：将输入条件的分号分隔转换为换行符分隔，并左对齐
        formatted_input_conditions = ceshi_yongli.replace('；', '\n').replace(';', '\n') if ceshi_yongli else '无'
        cell_p = sheet.cell(row=row_xuhao, column=16, value=formatted_input_conditions)  # P: 输入条件
        cell_p.fill = light_blue_fill
        cell_p.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        cell_p.border = standard_border
        
        # [FIX] 修复：将预期结果的分号分隔转换为换行符分隔，并左对齐
        formatted_expected_results = ceshi_yonglisheji.replace('；', '\n').replace(';', '\n') if ceshi_yonglisheji else '无'
        cell_q = sheet.cell(row=row_xuhao, column=17, value=formatted_expected_results)  # Q: 预期结果
        cell_q.fill = light_blue_fill
        cell_q.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        cell_q.border = standard_border
        
        cell_r = sheet.cell(row=row_xuhao, column=18, value='实测结果与预期结果一致表明测试通过，否则测试不通过')  # R: 通过准则
        cell_r.fill = light_blue_fill
        cell_r.border = standard_border
        
        # 人员和时间信息（19-25）
        cell_s = sheet.cell(row=row_xuhao, column=19, value=ceshiren_name)  # S: 用例设计人
        cell_s.fill = light_blue_fill
        cell_s.border = standard_border
        
        # 校对时间设置为设计时间后一天
        import datetime
        try:
            design_date = datetime.datetime.strptime(yonglisheji_time, '%Y/%m/%d')
            review_date = design_date + datetime.timedelta(days=1)
            review_time_str = review_date.strftime('%Y/%m/%d')
        except:
            review_time_str = yonglisheji_time  # 如果解析失败，使用原时间
        
        cell_t = sheet.cell(row=row_xuhao, column=20, value=zhuguan_name)  # T: 校对人
        cell_t.fill = light_blue_fill
        cell_t.border = standard_border
        
        cell_u = sheet.cell(row=row_xuhao, column=21, value=yonglisheji_time)  # U: 设计时间
        cell_u.fill = light_blue_fill
        cell_u.border = standard_border
        
        cell_v = sheet.cell(row=row_xuhao, column=22, value=review_time_str)  # V: 校对时间（设计时间后一天）
        cell_v.fill = light_blue_fill
        cell_v.border = standard_border
        
        cell_w = sheet.cell(row=row_xuhao, column=23, value=ceshiren_name)  # W: 测试人员
        cell_w.fill = light_blue_fill
        cell_w.border = standard_border
        
        cell_x = sheet.cell(row=row_xuhao, column=24, value=zhuguan_name)  # X: 监督人员
        cell_x.fill = light_blue_fill
        cell_x.border = standard_border
        
        cell_y = sheet.cell(row=row_xuhao, column=25, value=ceshi_time)  # Y: 测试时间
        cell_y.fill = light_blue_fill
        cell_y.border = standard_border
        
        # 测试结果信息（26-30）
        # 注意：第26列和第28列是空的（待填写），不需要着色
        sheet.cell(row=row_xuhao, column=26, value='')  # Z: 测试结果（待填写）- 不着色
        sheet.cell(row=row_xuhao, column=26).border = standard_border
        
        cell_aa = sheet.cell(row=row_xuhao, column=27, value='通过')  # AA: 测试结论
        cell_aa.fill = light_blue_fill
        cell_aa.border = standard_border
        
        sheet.cell(row=row_xuhao, column=28, value='')  # AB: 问题报告单编号 - 不着色
        sheet.cell(row=row_xuhao, column=28).border = standard_border
        
        cell_ac = sheet.cell(row=row_xuhao, column=29, value=ceshi_nianyue)  # AC: 执行年月
        cell_ac.fill = light_blue_fill
        cell_ac.border = standard_border
        
        cell_ad = sheet.cell(row=row_xuhao, column=30, value=0)  # AD: 用例发现问题数
        cell_ad.fill = light_blue_fill
        cell_ad.border = standard_border
        
        # [FIX] 自动调整行高以适应多行文本内容
        # 计算输入条件和预期结果的行数，选择较大的值来设置行高
        input_lines = len(formatted_input_conditions.split('\n')) if formatted_input_conditions else 1
        expected_lines = len(formatted_expected_results.split('\n')) if formatted_expected_results else 1
        max_lines = max(input_lines, expected_lines, 3)  # 至少3行高度
        
        # 设置行高（每行约15个单位，加上额外的间距）
        sheet.row_dimensions[row_xuhao].height = max_lines * 18
        
    except Exception as e:
        print(f"[WARNING]  填充第{index+1}个测试项时出错: {e}")
        # 如果是列不足的问题，可能是在错误的工作表上操作
        if "column" in str(e).lower():
            print(f"[TIP] 提示：可能需要确保使用的是'测试用例单'工作表而不是其他工作表")


def write_simple_test_cases_to_excel(sheet, row_xuhao: int, ceshi_yongli: str, ceshi_yonglisheji: str):
    """
    将测试用例写入Excel表格 - 简化版本（保持向后兼容）
    
    根据用户反馈，原来的填写位置不对，这里调整为更可能正确的列位置
    
    Args:
        sheet: Excel工作表对象
        row_xuhao: 行号
        ceshi_yongli: 测试用例
        ceshi_yonglisheji: 测试用例设计
    """
    # 根据常见的Excel表格结构，测试用例可能在L、M列或更靠后的列
    sheet.cell(row=row_xuhao, column=12, value=ceshi_yongli)      # L: 测试用例
    sheet.cell(row=row_xuhao, column=13, value=ceshi_yonglisheji)  # M: 测试用例设计
    sheet.cell(row=row_xuhao, column=16, value='通过')             # P: 测试结果
    sheet.cell(row=row_xuhao, column=21, value='无')               # U: 备注 