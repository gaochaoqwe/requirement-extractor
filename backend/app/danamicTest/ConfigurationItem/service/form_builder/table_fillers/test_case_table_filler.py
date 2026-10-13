"""
测试用例表填充器

专门负责填充测试用例单的复杂91列Excel映射逻辑
保留原始 _fill_test_case_table_corrected 方法中的所有调试代码和功能
"""

from typing import Dict, List, Optional
from openpyxl import load_workbook

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ...test_case_generation import generate_test_cases_for_form

# 🔧 修复：导入完整的91列填充函数
try:
    from ...test_case_generation.test_case_form_handler import write_test_cases_to_excel, get_test_time_info
except ImportError:
    try:
        from ....test_case_generation.test_case_form_handler import write_test_cases_to_excel, get_test_time_info
    except ImportError:
        from app.danamicTest.ConfigurationItem.service.test_case_generation.test_case_form_handler import write_test_cases_to_excel, get_test_time_info


class TestCaseTableFiller:
    """测试用例表填充器"""
    
    def __init__(self):
        pass
    
    def fill_test_case_table_corrected(self, excel_file_path: str, sheet_name: str, 
                                      final_xuqiu_mioashu: Dict, ruanjian_name: str, 
                                      requirements_dict: Dict, AI_fenx_flag_Anniu: bool,
                                      user_software_info: Optional[Dict[str, str]] = None,
                                      requirement_analysis_data: Optional[Dict] = None,
                                      zhuguan_name: str = "", ceshiren_name: str = "") -> bool:
        """
        填充测试用例单 - 修正版本（使用完整的91列映射）
        
        完整保留原始 form_builder_service.py 中的复杂逻辑
        """
        try:
            log_debug(f"[FIX] 开始修正版测试用例单填充", "test_case_table_filler")
            log_debug(f"文件路径: {excel_file_path}", "test_case_table_filler")
            log_debug(f"[FIX] 人员信息 - 测试人员: '{ceshiren_name}', 主管: '{zhuguan_name}'", "test_case_table_filler")
            log_debug(f"需求数量: {len(final_xuqiu_mioashu)}", "test_case_table_filler")
            
            workbook = load_workbook(excel_file_path)
            log_debug(f"可用工作表: {workbook.sheetnames}", "test_case_table_filler")
            
            if sheet_name not in workbook.sheetnames:
                log_error(f"工作表 '{sheet_name}' 不存在，可用: {workbook.sheetnames}", "test_case_table_filler")
                return False
                
            worksheet = workbook[sheet_name]
            log_debug(f"[SUCCESS] 成功选择工作表: {sheet_name} ({worksheet.max_row}行, {worksheet.max_column}列)", "test_case_table_filler")
            
            # 准备测试数据
            allkeys = list(final_xuqiu_mioashu.keys())
            
            # [FIX] 修复：从前端传递的软件信息中获取版本号，不带V前缀
            ruanjian_version = user_software_info.get('software_version', '2.00') if user_software_info else '2.00'
            log_debug(f"  使用前端版本号: {ruanjian_version} (不带V)", "test_case_table_filler")
            
            # 准备测试数据结构
            zhangjiehao = []
            ceshi_xuqiu_biaoshi = "CT-"
            ruanjian_xuqiu_biaoshi = []
            leixing_biaoshi = "FN01"
            ceshileixing_temp = "功能测试"
            
            # [FIX] 修复：从需求分析表数据中提取相关信息
            requirement_tracking_list = []  # 软件需求规格说明条目追踪关系
            test_item_names = []  # 测试项名称
            test_item_identifiers = []  # 测试项标识
            
            if requirement_analysis_data and 'test_items' in requirement_analysis_data:
                test_items = requirement_analysis_data['test_items']
                log_debug(f"  从需求分析表获取到 {len(test_items)} 个测试项", "test_case_table_filler")
                
                for i, test_item in enumerate(test_items):
                    # [FIX] 获取软件需求规格说明条目追踪关系（与需求分析表第17列相同）
                    if 'software_requirement_trace' in test_item:
                        tracking_info = test_item['software_requirement_trace']
                    else:
                        # 否则重新构造（确保包含章节号）
                        chapter_number = test_item.get('chapter_number', '')
                        pure_name = test_item.get('pure_name', '')
                        if chapter_number and pure_name:
                            tracking_info = f"《{ruanjian_name}软件需求规格说明》 {chapter_number} {pure_name}"
                        else:
                            tracking_info = f"《{ruanjian_name}软件需求规格说明》 {pure_name}"
                    requirement_tracking_list.append(tracking_info.strip())
                    
                    # 获取测试项名称（纯名称，不是REQ-001格式）
                    test_item_names.append(test_item.get('pure_name', test_item.get('name', f'需求{i+1}')))
                    
                    # 🔧 修复：优先从需求分析表中获取已生成的测试项标识
                    if 'test_item_identifier' in test_item and test_item['test_item_identifier'].strip():
                        test_identifier = test_item['test_item_identifier'].strip()
                        log_debug(f"    测试项{i+1}: 从需求分析表获取标识 '{test_identifier}'", "test_case_table_filler")
                    else:
                        # 否则重新生成（使用正确的英文标识符）
                        software_id = user_software_info.get('software_id', 'UNKNOWN') if user_software_info else 'UNKNOWN'
                        english_id = test_item.get('english_identifier', f'Function{i+1}')
                        test_identifier = f"CT-{software_id}-{ruanjian_version}-{english_id}-FN01"
                        log_debug(f"    测试项{i+1}: 重新生成标识 '{test_identifier}'", "test_case_table_filler")
                    
                    test_item_identifiers.append(test_identifier)
                    
                    log_debug(f"    测试项{i+1}: 名称='{test_item.get('pure_name', 'N/A')}', 标识='{test_identifier}'", "test_case_table_filler")
            else:
                log_error("❌ 未能从需求分析数据中获取测试项信息！", "test_case_table_filler")
                log_error(f"❌ requirement_analysis_data 类型: {type(requirement_analysis_data)}", "test_case_table_filler")
                log_error(f"❌ requirement_analysis_data 内容: {requirement_analysis_data}", "test_case_table_filler")
                log_error(f"❌ requirement_analysis_data 是否有 test_items: {'test_items' in requirement_analysis_data if requirement_analysis_data else 'N/A'}", "test_case_table_filler")
                
                # 🚫 移除默认数据生成，强制要求正确的数据
                log_error("❌ 拒绝使用默认数据，必须提供正确的需求分析数据！", "test_case_table_filler")
                return False
            
            log_debug(f"准备的测试数据:", "test_case_table_filler")
            log_debug(f"  测试项列表: {allkeys}", "test_case_table_filler")
            log_debug(f"  软件名称: {ruanjian_name}", "test_case_table_filler")
            log_debug(f"  软件版本: {ruanjian_version}", "test_case_table_filler")
            
            # 🔧 补充：生成章节号和需求标识列表
            if requirement_analysis_data and 'test_items' in requirement_analysis_data:
                test_items = requirement_analysis_data['test_items']
                for i, test_item in enumerate(test_items):
                    zhangjiehao.append(test_item.get('chapter_number', f'3.{i+1}.{i+1}'))
                    ruanjian_xuqiu_biaoshi.append(f'REQ{i+1:03d}')
            else:
                # 默认生成章节号和需求标识
                for i in range(len(allkeys)):
                    zhangjiehao.append(f'3.{i+1}.{i+1}')
                    ruanjian_xuqiu_biaoshi.append(f'REQ{i+1:03d}')
            
            log_debug(f"  章节号: {zhangjiehao}", "test_case_table_filler")
            log_debug(f"  测试项标识列表: {test_item_identifiers}", "test_case_table_filler")
            
            # [ALERT] 修正版：正确处理AI返回的多个测试用例
            current_row = 2  # 从第2行开始（第1行是表头）
            total_test_cases_filled = 0
            
            for req_index, (req_id, req_data) in enumerate(final_xuqiu_mioashu.items()):
                log_debug(f"处理第{req_index+1}个需求: {req_id}", "test_case_table_filler")
                
                if isinstance(req_data, dict):
                    # 生成测试用例描述和方法
                    req_name = req_data.get('name', req_id)
                    req_desc = req_data.get('description', '')
                    
                    log_debug(f"  需求名称: {req_name}", "test_case_table_filler")
                    log_debug(f"  需求描述长度: {len(req_desc)}", "test_case_table_filler")
                    
                    # [ALERT] 关键修正：调用AI生成多个测试用例
                    test_result = generate_test_cases_for_form(
                        cehisixiang_name_temp=req_name,
                        value_mioashu=req_desc,
                        AI_fenx_flag_Anniu=1 if AI_fenx_flag_Anniu else 0,
                        jianceyi_flag='是',
                        ceshileixing_remp='配置项测试'
                    )
                    
                    log_debug(f"  AI生成结果类型: {type(test_result)}", "test_case_table_filler")
                    log_debug(f"  AI生成结果内容: {test_result}", "test_case_table_filler")
                    
                    # 🔧 修复：正确解析generate_test_cases_for_form返回的数据格式
                    test_cases_list = []
                    if isinstance(test_result, tuple) and len(test_result) == 2:
                        # 现在两个结果是相同的，只需要取第一个
                        unified_result = test_result[0]
                        if isinstance(unified_result, tuple) and len(unified_result) == 2:
                            success_flag, test_cases = unified_result
                            
                            if success_flag and isinstance(test_cases, list) and test_cases:
                                # 🔧 修复：正确处理AI返回的测试用例数据格式
                                for idx, case_data in enumerate(test_cases):
                                    
                                    if isinstance(case_data, list) and len(case_data) >= 4:
                                        # 新格式：[测试用例名称, 测试用例描述, 输入条件, 预期结果]
                                        test_case = {
                                            'test_case_description': case_data[1],  # 测试用例描述
                                            'test_steps': case_data[2],             # 输入条件（测试步骤）
                                            'expected_result': case_data[3],        # 预期结果
                                            'test_data': f'{req_name}相关测试数据'
                                        }
                                        test_cases_list.append(test_case)
                                        log_debug(f"    成功解析列表格式测试用例: {case_data[0]}", "test_case_table_filler")
                                    elif isinstance(case_data, dict):
                                        # 字典格式：直接使用
                                        test_cases_list.append(case_data)
                                        log_debug(f"    成功解析字典格式测试用例", "test_case_table_filler")
                                    else:
                                        log_warning(f"    未知的测试用例格式: {type(case_data)} - {case_data}", "test_case_table_filler")
                                
                                log_debug(f"  [SUCCESS] 成功获取AI生成的测试用例，共 {len(test_cases_list)} 个", "test_case_table_filler")
                            else:
                                log_warning(f"  [WARNING] AI生成失败或返回空结果 - success: {success_flag}, cases: {test_cases}", "test_case_table_filler")
                        else:
                            log_warning(f"  [WARNING] 统一结果格式异常: {unified_result}", "test_case_table_filler")
                    else:
                        log_warning(f"  [WARNING] AI返回结果格式异常: {test_result}", "test_case_table_filler")
                    
                    # 如果AI生成失败，提供默认测试用例
                    if not test_cases_list:
                        log_info(f"  [FALLBACK] 为需求 '{req_name}' 提供默认测试用例", "test_case_table_filler")
                        test_cases_list = [{
                            'test_case_description': f'验证{req_name}功能是否正常工作',
                            'test_steps': f'1. 准备{req_name}相关的测试数据\n2. 执行{req_name}功能\n3. 验证功能执行结果',
                            'expected_result': f'{req_name}功能按照需求规格说明正常工作',
                            'test_data': f'{req_name}相关的测试数据'
                        }]
                    
                    # [ALERT] 核心修正：使用正确的write_test_cases_to_excel函数填充91列
                    for case_index, test_case in enumerate(test_cases_list):
                        if current_row > 1000:  # 防止行数过多
                            log_warning(f"达到最大行数限制 1000，停止填充", "test_case_table_filler")
                            break
                        
                        # 获取当前需求的相关信息
                        current_req_tracking = requirement_tracking_list[req_index] if req_index < len(requirement_tracking_list) else f"《{ruanjian_name}软件需求规格说明》 {req_name}"
                        current_test_item_name = test_item_names[req_index] if req_index < len(test_item_names) else req_name
                        current_test_identifier = test_item_identifiers[req_index] if req_index < len(test_item_identifiers) else f"CT-UNKNOWN-{ruanjian_version}-Function{req_index+1}-FN01"
                        current_chapter = zhangjiehao[req_index] if req_index < len(zhangjiehao) else f'3.{req_index+1}.{case_index+1}'
                        current_req_identifier = ruanjian_xuqiu_biaoshi[req_index] if req_index < len(ruanjian_xuqiu_biaoshi) else f'REQ{req_index+1:03d}-{case_index+1:02d}'
                        
                        # 提取测试用例数据
                        case_name = test_case.get('test_case_description', f'{current_test_item_name}测试用例{case_index+1}')
                        case_description = test_case.get('test_case_description', f'验证{current_test_item_name}功能')
                        case_steps = test_case.get('test_steps', f'1. 执行{current_test_item_name}功能\n2. 检查执行结果')
                        case_expect = test_case.get('expected_result', f'{current_test_item_name}功能正常执行')
                        
                        log_debug(f"    填充第{case_index+1}个测试用例:", "test_case_table_filler")
                        log_debug(f"      - case_name: '{case_name}'", "test_case_table_filler")
                        log_debug(f"      - case_steps: '{case_steps}'", "test_case_table_filler")
                        log_debug(f"      - case_expect: '{case_expect}'", "test_case_table_filler")
                        
                        # 🔧 修复：使用完整的91列填充函数（与重构前保持一致）
                        try:
                            write_test_cases_to_excel(
                                sheet=worksheet,
                                row_xuhao=current_row,
                                index=total_test_cases_filled,  # 使用全局测试用例计数作为序号
                                allkeys=[case_name] * (total_test_cases_filled + 1),  # 扩展数组以避免索引越界
                                ruanjian_name=ruanjian_name,
                                ruanjian_version=ruanjian_version,
                                zhangjiehao=[current_chapter] * (total_test_cases_filled + 1),
                                ceshi_xuqiu_biaoshi=ceshi_xuqiu_biaoshi,
                                ruanjian_xuqiu_biaoshi=[current_req_identifier] * (total_test_cases_filled + 1),
                                leixing_biaoshi=leixing_biaoshi,
                                ceshileixing_temp=ceshileixing_temp,
                                ceshixiang_miaoshu=case_description,  # 使用AI生成的描述
                                ceshixiang_fangfa=f"通过检测仪测试{current_test_item_name}功能",
                                ceshi_yongli=case_steps,  # 使用AI生成的测试步骤
                                ceshi_yonglisheji=case_expect,  # 使用AI生成的预期结果
                                ceshiren_name=ceshiren_name,
                                zhuguan_name=zhuguan_name,
                                temp_temp_count=case_index + 1,  # 用例编号
                                # 传递需求分析表中的信息
                                requirement_tracking=current_req_tracking,
                                test_item_name=current_test_item_name,
                                test_item_identifier=current_test_identifier,
                                # 传递AI生成的测试用例名称
                                ai_test_case_name=case_name
                            )
                            log_debug(f"    [SUCCESS] 成功填充行{current_row}的完整数据（91列）", "test_case_table_filler")
                            current_row += 1
                            total_test_cases_filled += 1
                        except Exception as fill_error:
                            log_error(f"    [ERROR] 填充行{current_row}时出错: {fill_error}", "test_case_table_filler")
                            log_debug(f"    错误详情: {str(fill_error)}", "test_case_table_filler")
                            current_row += 1  # 即使失败也要移动到下一行
            
            # 保存工作簿
            workbook.save(excel_file_path)
            log_info(f"[SUCCESS] 测试用例单填充完成，共填充 {total_test_cases_filled} 个测试用例", "test_case_table_filler")
            
            return True
            
        except Exception as e:
            log_error(f"填充测试用例单时发生错误: {e}", "test_case_table_filler")
            return False 