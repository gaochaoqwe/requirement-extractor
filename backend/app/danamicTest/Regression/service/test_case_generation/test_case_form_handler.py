"""
回归测试用例表单处理模块
从forms/formFilter/test_case_form_filler.py重构而来的测试用例生成逻辑
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from openpyxl.styles import PatternFill

try:
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from .test_case_generator import generate_test_yongli, generate_test_yonglisheji


def generate_test_cases_for_form(test_name: str, requirement_description: str, 
                                AI_flag: int, jianceyi_flag: str, 
                                test_type: str) -> Dict[str, str]:
    """
    为回归测试表单生成测试用例
    
    Args:
        test_name: 测试项名称
        requirement_description: 需求描述
        AI_flag: AI分析标志
        jianceyi_flag: 检测仪标志
        test_type: 测试类型
        
    Returns:
        Dict[str, str]: 包含description, steps, expected的字典
    """
    try:
        if AI_flag == 1 and requirement_description and len(requirement_description.strip()) > 5:
            # 使用AI生成测试用例
            return generate_ai_test_case(test_name, requirement_description, test_type, jianceyi_flag)
        else:
            # 使用默认测试用例
            return generate_default_test_case(test_name, jianceyi_flag)
    except Exception as e:
        log_error(f"生成测试用例失败: {e}", Path(__file__).stem)
        return generate_default_test_case(test_name, jianceyi_flag)


def generate_ai_test_case(test_name: str, requirement_description: str, 
                         test_type: str, jianceyi_flag: str) -> Dict[str, str]:
    """
    使用AI生成测试用例
    
    Args:
        test_name: 测试项名称
        requirement_description: 需求描述
        test_type: 测试类型
        jianceyi_flag: 检测仪标志
        
    Returns:
        Dict[str, str]: 测试用例内容
    """
    try:
        # 尝试生成AI测试用例
        success, test_cases = generate_test_yongli(
            test_name, requirement_description, '', test_type, jianceyi_flag
        )
        
        if success and test_cases:
            # 取第一个测试用例
            test_case = test_cases[0]
            return {
                'description': test_case[1] if len(test_case) > 1 else f'测试{test_name}功能',
                'steps': test_case[2] if len(test_case) > 2 else f'1. 启动软件\n2. 执行{test_name}操作\n3. 验证结果',
                'expected': test_case[3] if len(test_case) > 3 else f'{test_name}功能正常'
            }
        else:
            log_warning(f"AI生成测试用例失败，使用默认内容", Path(__file__).stem)
            return generate_default_test_case(test_name, jianceyi_flag)
            
    except Exception as e:
        log_error(f"AI生成测试用例异常: {e}", Path(__file__).stem)
        return generate_default_test_case(test_name, jianceyi_flag)


def generate_default_test_case(test_name: str, jianceyi_flag: str) -> Dict[str, str]:
    """
    生成默认测试用例
    
    Args:
        test_name: 测试项名称
        jianceyi_flag: 检测仪标志
        
    Returns:
        Dict[str, str]: 默认测试用例内容
    """
    if jianceyi_flag == '有检测仪':
        if '故障' in test_name or '报警检测' in test_name:
            return {
                'description': f'验证{test_name}功能在故障条件下的处理能力',
                'steps': f'1. 通过代码插桩设置软件故障\n2. 通过检测仪发送自检指令\n3. 通过检测仪状态监控界面查看{test_name}功能实现',
                'expected': f'软件{test_name}功能在故障条件下正常处理并上报状态'
            }
        else:
            return {
                'description': f'验证{test_name}功能实现是否符合需求',
                'steps': f'1. 通过检测仪发送测试指令\n2. 通过检测仪状态监控界面查看{test_name}功能实现\n3. 验证功能响应正确性',
                'expected': f'软件{test_name}功能实现正常，响应符合预期'
            }
    else:
        return {
            'description': f'验证{test_name}功能实现是否符合需求',
            'steps': f'1. 启动被测软件\n2. 执行{test_name}相关操作\n3. 观察软件运行状态和输出结果',
            'expected': f'软件{test_name}功能实现正常，输出结果符合预期'
        }


def set_default_test_cases(test_name: str, jianceyi_flag: str) -> Dict[str, str]:
    """
    设置默认的测试用例（为保持兼容性）
    
    Args:
        test_name: 测试项名称
        jianceyi_flag: 检测仪标志
        
    Returns:
        Dict[str, str]: 默认测试用例内容
    """
    return generate_default_test_case(test_name, jianceyi_flag)


# 保留旧版本函数以兼容
def write_simple_test_cases_to_excel(sheet, row_xuhao: int, test_case_name: str, 
                             test_content: Dict[str, str], is_ai_generated: bool = False):
    """
    将测试用例写入Excel表格（回归测试格式 - 简化版本）
    
    Args:
        sheet: Excel工作表对象
        row_xuhao: 行号
        test_case_name: 测试用例名称
        test_content: 测试用例内容字典
        is_ai_generated: 是否为AI生成
    """
    sheet.cell(row=row_xuhao, column=9, value=test_case_name)  # 8、测试用例名称
    sheet.cell(row=row_xuhao, column=12, value=test_content.get('description', ''))  # 11、测试描述
    sheet.cell(row=row_xuhao, column=16, value=test_content.get('steps', ''))  # 15、输入条件
    sheet.cell(row=row_xuhao, column=17, value=test_content.get('expected', ''))  # 16、预期结果
    sheet.cell(row=row_xuhao, column=24, value='通过')  # 23、测试结果
    sheet.cell(row=row_xuhao, column=25, value='无')  # 24、备注
    
    # 应用格式
    apply_test_case_formatting(sheet, row_xuhao, is_ai_generated)


def get_test_time_info():
    """获取测试时间信息"""
    from datetime import datetime, timedelta
    
    current_time = datetime.now()
    yonglisheji_time = current_time.strftime('%Y-%m-%d')
    
    # 测试时间设为当前时间+7天
    test_time = current_time + timedelta(days=7)
    ceshi_time = test_time.strftime('%Y-%m-%d')
    ceshi_nianyue = test_time.strftime('%Y年%m月')
    
    return yonglisheji_time, ceshi_time, ceshi_nianyue


def write_test_cases_to_excel(sheet, row_xuhao: int, index: int, allkeys: list, 
                             ruanjian_name: str, ruanjian_version: str, 
                             zhangjiehao: list, ceshi_xuqiu_biaoshi: str, 
                             ruanjian_xuqiu_biaoshi: list, leixing_biaoshi: str,
                             ceshileixing_temp: str, ceshixiang_miaoshu: str, 
                             ceshixiang_fangfa: str, ceshi_yongli: str, 
                             ceshi_yonglisheji: str, ceshiren_name: str = '测试人员',
                             zhuguan_name: str = '主管', temp_temp_count: int = 1):
    """
    将测试用例写入Excel表格 - 完整版本（适配真实的测试用例单工作表）
    
    🚨 重要：此函数适配真实的"测试用例单"工作表，有91列
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
        ceshixiang_fangfa: 测试项方法
        ceshi_yongli: 测试用例（输入条件）
        ceshi_yonglisheji: 测试用例设计（预期结果）
        ceshiren_name: 测试人员姓名
        zhuguan_name: 主管姓名
        temp_temp_count: 用例计数
    """
    
    yonglisheji_time, ceshi_time, ceshi_nianyue = get_test_time_info()
    
    if index < len(ruanjian_xuqiu_biaoshi) and ruanjian_xuqiu_biaoshi[index]:
        test_item_id = ceshi_xuqiu_biaoshi + ruanjian_xuqiu_biaoshi[index] + leixing_biaoshi
    else:
        test_item_id = ceshi_xuqiu_biaoshi + 'name' + str(index) + leixing_biaoshi
    
    test_case_id = test_item_id + '-01'
    ceshiyongliname = f"{allkeys[index]}测试用例{temp_temp_count}"
    ceshixiang_miaoshu = f"验证{allkeys[index]}功能实现是否正常"
    ceshixiang_fangfa = f"通过检测仪测试{allkeys[index]}功能"
    ceshi_yongli = f"1、启动测试环境；2、通过检测仪发送{allkeys[index]}测试指令；3、观察软件响应；4、验证功能正确性"
    ceshi_yonglisheji = f"1、测试环境正常启动；2、{allkeys[index]}指令发送成功；3、软件响应正常；4、功能验证通过"
    
    # 根据真实的"测试用例单"工作表表头进行填充
    try:
        # 核心信息列（1-12）
        sheet.cell(row=row_xuhao, column=1, value=f"TC{index+1:03d}")  # A: ID
        sheet.cell(row=row_xuhao, column=2, value=index + 1)  # B: 序号
        sheet.cell(row=row_xuhao, column=3, value=ruanjian_name)  # C: 软件配置项名称
        sheet.cell(row=row_xuhao, column=4, value=ruanjian_version)  # D: 被测软件版本
        sheet.cell(row=row_xuhao, column=5, value='第一轮')  # E: 测试轮次
        sheet.cell(row=row_xuhao, column=6, value=zhangjiehao[index] if index < len(zhangjiehao) else '无')  # F: 需求追溯
        sheet.cell(row=row_xuhao, column=7, value=allkeys[index])  # G: 测试项名称
        sheet.cell(row=row_xuhao, column=8, value=test_item_id)  # H: 测试项标识
        sheet.cell(row=row_xuhao, column=9, value=ceshiyongliname)  # I: 测试用例名称
        sheet.cell(row=row_xuhao, column=10, value=test_case_id)  # J: 测试用例编号
        sheet.cell(row=row_xuhao, column=11, value=ceshileixing_temp)  # K: 测试类型
        sheet.cell(row=row_xuhao, column=12, value=ceshixiang_miaoshu)  # L: 测试描述
        
        # 测试条件和方法（13-18）
        sheet.cell(row=row_xuhao, column=13, value="被测软件正常加载，检测仪、调试计算机上电、测试环境连接正常")  # M: 预置条件
        sheet.cell(row=row_xuhao, column=14, value='无')  # N: 前提与约束
        sheet.cell(row=row_xuhao, column=15, 
                  value="正常终止条件:按正常测试步骤完成测试过程.\n异常终止条件:被测软件功能实现错误、测试用例设计错误、操作错误、测试环境出现异常情况。")  # O: 终止条件
        sheet.cell(row=row_xuhao, column=16, value=ceshi_yongli)  # P: 输入条件
        sheet.cell(row=row_xuhao, column=17, value=ceshi_yonglisheji)  # Q: 预期结果
        sheet.cell(row=row_xuhao, column=18, value='实测结果与预期结果一致表明测试通过，否则测试不通过')  # R: 通过准则
        
        # 人员和时间信息（19-25）
        sheet.cell(row=row_xuhao, column=19, value=ceshiren_name)  # S: 用例设计人
        sheet.cell(row=row_xuhao, column=20, value=zhuguan_name)  # T: 校对人
        sheet.cell(row=row_xuhao, column=21, value=yonglisheji_time)  # U: 设计时间
        sheet.cell(row=row_xuhao, column=22, value=yonglisheji_time)  # V: 校对时间
        sheet.cell(row=row_xuhao, column=23, value=ceshiren_name)  # W: 测试人员
        sheet.cell(row=row_xuhao, column=24, value=zhuguan_name)  # X: 监督人员
        sheet.cell(row=row_xuhao, column=25, value=ceshi_time)  # Y: 测试时间
        
        # 测试结果信息（26-30）
        sheet.cell(row=row_xuhao, column=26, value='')  # Z: 测试结果（待填写）
        sheet.cell(row=row_xuhao, column=27, value='通过')  # AA: 测试结论
        sheet.cell(row=row_xuhao, column=28, value='')  # AB: 问题报告单编号
        sheet.cell(row=row_xuhao, column=29, value=ceshi_nianyue)  # AC: 执行年月
        sheet.cell(row=row_xuhao, column=30, value=0)  # AD: 用例发现问题数
        
    except Exception as e:
        log_error(f"⚠️  填充第{index+1}个测试项时出错: {e}", "test_case_form_handler")
        if "column" in str(e).lower():
            log_error(f"💡 提示：可能需要确保使用的是'测试用例单'工作表而不是其他工作表", "test_case_form_handler")


def apply_test_case_formatting(sheet, row_xuhao: int, is_ai_generated: bool = False):
    """
    应用测试用例格式
    
    Args:
        sheet: Excel工作表对象
        row_xuhao: 行号
        is_ai_generated: 是否为AI生成
    """
    light_yellow_fill = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")  # 浅黄色
    light_green_fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
    light_blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")  # 浅蓝色
    light_red_fill = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")

    for col in range(2, 26):  # 遍历列
        sheet.cell(row=row_xuhao, column=col).fill = light_blue_fill  # 将2到25列设置为浅蓝色
    sheet.cell(row=row_xuhao, column=11).fill = light_green_fill

    # 如果使用了AI生成，标记为红色
    if is_ai_generated:
        sheet.cell(row=row_xuhao, column=12).fill = light_red_fill  # 测试描述
        sheet.cell(row=row_xuhao, column=16).fill = light_red_fill  # 测试步骤
        sheet.cell(row=row_xuhao, column=17).fill = light_red_fill  # 预期结果


def generate_multiple_test_cases(sheet, base_row: int, test_name: str, 
                               requirement_description: str, case_count: int,
                               ai_flag: int, jianceyi_flag: str, test_type: str,
                               basic_info: Dict[str, Any]) -> int:
    """
    生成多个测试用例
    
    Args:
        sheet: Excel工作表对象
        base_row: 起始行号
        test_name: 测试项名称
        requirement_description: 需求描述
        case_count: 用例数量
        ai_flag: AI标志
        jianceyi_flag: 检测仪标志
        test_type: 测试类型
        basic_info: 基本信息字典
        
    Returns:
        int: 下一行行号
    """
    log_info(f"   🤖 生成{case_count}个测试用例: {test_name}", Path(__file__).stem)
    
    current_row = base_row
    
    for item in range(1, case_count + 1):
        log_info(f"     生成第 {item} 个用例...", Path(__file__).stem)
        
        # 生成测试用例内容
        test_content = generate_test_cases_for_form(
            test_name, requirement_description, ai_flag, jianceyi_flag, test_type
        )
        
        # 测试用例名称
        test_case_name = f"{test_name}_测试用例{item}"
        
        # 写入Excel
        write_test_cases_to_excel(
            sheet, current_row, test_case_name, test_content, 
            ai_flag == 1 and len(requirement_description.strip()) > 5
        )
        
        current_row += 1
    
    log_info(f"   ✅ 测试用例生成完成，共 {case_count} 个", Path(__file__).stem)
    return current_row 