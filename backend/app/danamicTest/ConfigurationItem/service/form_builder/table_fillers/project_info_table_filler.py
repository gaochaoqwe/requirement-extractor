"""
项目信息表填充器

专门负责填充项目基本信息表格
"""

from typing import Dict, List

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


class ProjectInfoTableFiller:
    """项目信息表填充器"""
    
    def __init__(self, project_info_service):
        self.project_info_service = project_info_service
    
    def fill_project_info_table(self, excel_file_path: str, sheet_name: str, 
                               ruanjian_xinxi_duqu_temp: Dict, ruanjian_name: str, 
                               zhuguan_name: str, ceshiren_name: str, 
                               kaifarenxinxi: List[str], xinghao_xinxi_list: list, 
                               user_software_info: Dict) -> bool:
        """填充项目基本信息表"""
        try:
            # 准备基本信息，优先使用user_software_info
            basic_info = user_software_info if user_software_info else {}
            
            # 确定所属领域
            suoshulingyu = basic_info.get('domain', '通用领域') if basic_info else '通用领域'
            
            # 调用项目信息service
            success = self.project_info_service.generate_project_info_table(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                basic_info=basic_info,
                zhuguan_name=zhuguan_name,
                kaifarenxinxi=kaifarenxinxi,
                xinghao_xinxi_list=xinghao_xinxi_list,
                suoshulingyu=suoshulingyu,
                apply_formatting=True
            )
            
            if success:
                log_info(f"项目基本信息表填充成功: {sheet_name}", "project_info_table_filler")
            else:
                log_error(f"项目基本信息表填充失败: {sheet_name}", "project_info_table_filler")
                
            return success
            
        except Exception as e:
            log_error(f"填充项目基本信息表时发生错误", "project_info_table_filler", e)
            return False 