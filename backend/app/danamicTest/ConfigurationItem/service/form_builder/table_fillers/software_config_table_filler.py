"""
软件配置表填充器

专门负责填充软件配置项信息表格
"""

from typing import Dict, List, Optional

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


class SoftwareConfigTableFiller:
    """软件配置表填充器"""
    
    def __init__(self, software_config_service):
        self.software_config_service = software_config_service
    
    def fill_software_config_table(self, excel_file_path: str, sheet_name: str, 
                                  ruanjian_xinxi_duqu_temp: Dict, ruanjian_name: str, 
                                  kaifarenxinxi: List[str], suoshulingyu: str, 
                                  xinghao_xinxi_list: list, zhuguan_name: str = "", 
                                  ceshiren_name: str = "", user_software_info: Dict = None,
                                  requirement_doc_path: str = None, code_lines: int = None) -> bool:
        """填充软件配置项信息表"""
        try:
            # 从kaifarenxinxi中提取测试人员信息
            if not ceshiren_name and kaifarenxinxi:
                ceshiren_name = kaifarenxinxi[0] if isinstance(kaifarenxinxi, list) else str(kaifarenxinxi)
            
            log_debug(f"[DEBUG] 软件配置项表参数:", "software_config_table_filler")
            log_debug(f"   user_software_info: {user_software_info}", "software_config_table_filler")
            log_debug(f"   ruanjian_name: '{ruanjian_name}'", "software_config_table_filler")
            
            # 调用软件配置service
            success = self.software_config_service.generate_software_config_table(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                ruanjian_name=ruanjian_name,
                ceshiren_name=ceshiren_name,
                zhuguan_name=zhuguan_name,
                daima_chayi_hangshu=code_lines or 0,
                xinghao_xinxi_list=xinghao_xinxi_list,
                ruanjian_xinxi_duqu_temp=ruanjian_xinxi_duqu_temp,
                ceshileixing="配置项测试",
                user_software_info=user_software_info,
                planning_requirements_count=0,
                analysis_requirements_count=0,
                requirement_doc_path=requirement_doc_path,
                apply_formatting=True
            )
            
            if success:
                log_info(f"配置项软件配置项信息表填充成功: {sheet_name}", "software_config_table_filler")
            else:
                log_error(f"配置项软件配置项信息表填充失败: {sheet_name}", "software_config_table_filler")
                
            return success
            
        except Exception as e:
            log_error(f"填充配置项软件配置项信息表时发生错误", "software_config_table_filler", e)
            return False 