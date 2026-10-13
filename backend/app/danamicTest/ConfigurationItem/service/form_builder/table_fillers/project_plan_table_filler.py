"""
项目策划表填充器

专门负责填充项目策划表格
"""

from typing import List, Optional

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


class ProjectPlanTableFiller:
    """项目策划表填充器"""
    
    def __init__(self, project_plan_service):
        self.project_plan_service = project_plan_service
    
    def fill_project_plan_table(self, excel_file_path: str, sheet_name: str, 
                               ruanjian_name: str, xinghao_xinxi_list: list, total_lines: int,
                               zhuguan_name: str = '', ceshiren_name: str = '', 
                               requirement_names: Optional[List[str]] = None,
                               requirements_dict: Optional[dict] = None) -> bool:
        """填充项目策划表
        
        Args:
            requirement_names: 需求名称列表（可能不包含编号）
            requirements_dict: 完整的需求字典（包含编号信息）
        """
        try:
            log_info(f"[FIX] [form_builder_project_plan] 开始填充项目策划表: {sheet_name}", "project_plan_table_filler")
            
            # [ALERT] 详细监控：输入参数
            log_info(f"📋 [form_builder_project_plan] 输入参数监控:", "project_plan_table_filler")
            log_info(f"   - Excel文件: {excel_file_path}", "project_plan_table_filler")
            log_info(f"   - 工作表名: {sheet_name}", "project_plan_table_filler")
            log_info(f"   - 软件名称: {ruanjian_name}", "project_plan_table_filler")
            log_info(f"   - 测试主管: '{zhuguan_name}'", "project_plan_table_filler")
            log_info(f"   - 测试人员: '{ceshiren_name}'", "project_plan_table_filler")
            log_info(f"   - 需求名称列表: {requirement_names}", "project_plan_table_filler")
            
            # 如果型号信息为空，提供默认值
            if not xinghao_xinxi_list:
                xinghao_xinxi_list = ['默认项目', '光电领域', '项目总师']
                log_warning("型号信息为空，使用默认值", "project_plan_table_filler")
            
            # [ALERT] 关键修复：优先使用包含编号信息的requirements_dict
            if requirements_dict:
                # 🔧 修复：使用完整的需求字典，保留编号信息
                ceshixiang_neirong_dict = {key: f"验证{key}的实现是否符合需求规格说明中的功能要求" 
                                         for key in requirements_dict.keys()}
                log_info(f"[SUCCESS] [form_builder_project_plan] 使用完整需求字典 ({len(requirements_dict)}个，包含编号信息)", "project_plan_table_filler")
                log_debug(f"   需求字典键（含编号）: {list(requirements_dict.keys())}", "project_plan_table_filler")
            elif requirement_names and len(requirement_names) > 0:
                # 回退：使用从需求分析表中提取的实际需求名称
                ceshixiang_neirong_dict = {name: f"验证{name}的实现是否符合需求规格说明中的功能要求" 
                                         for name in requirement_names}
                log_info(f"[SUCCESS] [form_builder_project_plan] 回退使用需求名称列表 ({len(requirement_names)}个)", "project_plan_table_filler")
                log_debug(f"   需求名称列表: {requirement_names}", "project_plan_table_filler")
            else:
                # 备用：使用默认需求（向后兼容）
                ceshixiang_neirong_dict = {
                    "功能测试": "验证软件核心功能是否正常实现",
                    "接口测试": "验证软件接口功能是否正常",
                    "异常处理测试": "验证软件异常处理机制",
                    "性能测试": "验证软件性能指标是否满足要求",
                    "边界值测试": "验证软件在边界条件下的处理能力"
                }
                log_warning("[WARNING] [form_builder_project_plan] 未提供需求数据，使用默认需求", "project_plan_table_filler")
            
            # 调用项目策划service
            excel_filler = self.project_plan_service.excel_filler
            success = excel_filler.write_to_excel_cell_cehuabiao_peizhixing(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name, 
                ruanjian_name=ruanjian_name, 
                xinghao_xinxi_list=xinghao_xinxi_list, 
                daima_chayi_hangshu=total_lines,
                ceshixiang_neirong_dict=ceshixiang_neirong_dict,
                zhuguan_name=zhuguan_name,
                ceshiren_name=ceshiren_name
            )
            
            if success:
                log_info(f"[SUCCESS] [form_builder_project_plan] 项目策划表填充成功: {sheet_name}", "project_plan_table_filler")
            else:
                log_error(f"[ERROR] [form_builder_project_plan] 项目策划表填充失败: {sheet_name}", "project_plan_table_filler")
                
            return success
            
        except Exception as e:
            log_error(f"填充项目策划表时发生错误", "project_plan_table_filler", e)
            return False 