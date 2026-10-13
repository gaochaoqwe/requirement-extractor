"""
问题报告表填充器

专门负责填充问题报告单表格
"""

from typing import Dict, List, Optional, Any

try:
    from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


class IssueReportTableFiller:
    """问题报告表填充器"""
    
    def __init__(self, issue_service):
        self.issue_service = issue_service
    
    def fill_issue_report_table(self, excel_file_path: str, sheet_name: str, 
                               ruanjian_xinxi_duqu_temp: Dict, ruanjian_name: str, 
                               zhuguan_name: str, ceshiren_name: str,
                               kaifarenxinxi: List[str],
                               user_software_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        填充问题报告单
        
        完整保留原始逻辑
        """
        try:
            # 准备符合现有方法签名的参数，优先使用前端传来的数据
            software_id = ''
            software_version = ''
            
            # 优先使用用户输入的软件信息
            if user_software_info:
                software_id = user_software_info.get('software_id', '')
                software_version = user_software_info.get('software_version', '')
                log_info(f"使用前端传来的软件信息: software_id={software_id}, software_version={software_version}", "issue_report_table_filler")
            
            # 如果用户信息为空，尝试从提取的信息中获取
            if not software_id and ruanjian_xinxi_duqu_temp.get('软件标识'):
                software_id = ruanjian_xinxi_duqu_temp['软件标识']
            if not software_version and ruanjian_xinxi_duqu_temp.get('被测软件版本'):
                software_version = ruanjian_xinxi_duqu_temp['被测软件版本']
            
            # 如果还是为空，使用软件名称作为后备方案（仅软件标识）
            if not software_id:
                software_id = ruanjian_name[:8] if len(ruanjian_name) > 8 else ruanjian_name
                log_warning(f"未找到软件标识，使用软件名称截取: {software_id}", "issue_report_table_filler")
            if not software_version:
                software_version = '1.0.0'  # 默认版本
                log_warning(f"未找到软件版本，使用默认版本: {software_version}", "issue_report_table_filler")
            
            ruanjian_xinxi = {
                '软件名称': [ruanjian_name],
                '软件标识': [software_id],
                '被测软件版本': [software_version]
            }
            diama_biangeng_xuqiu = ['功能测试问题', '接口测试问题', '性能测试问题']  # 默认测试问题类型
            log_debug(f"[FIX] 问题报告单 - 开发人员信息: {kaifarenxinxi}, 测试人员: {ceshiren_name}", "issue_report_table_filler")
            
            # 调用问题报告service
            success = self.issue_service.generate_issue_report_table(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                ruanjian_xinxi=ruanjian_xinxi,
                ruanjian_name=ruanjian_name,
                diama_biangeng_xuqiu=diama_biangeng_xuqiu,
                ceshiren_name=ceshiren_name,
                kaifarenxinxi=kaifarenxinxi,
                ceshileixing="配置项测试",
                issue_count=16,
                apply_formatting=True
            )
            
            if success:
                log_info(f"问题报告单填充成功: {sheet_name}", "issue_report_table_filler")
            else:
                log_error(f"问题报告单填充失败: {sheet_name}", "issue_report_table_filler")
                
            return success
            
        except Exception as e:
            log_error(f"填充问题报告单时发生错误", "issue_report_table_filler", e)
            return False 