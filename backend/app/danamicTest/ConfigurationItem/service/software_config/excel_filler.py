"""
软件配置项信息Excel填充器

负责将软件配置项信息数据填充到Excel工作表中。
"""

import logging
import openpyxl
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# 导入任务日志函数
from ...utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

# 配置日志
logger = logging.getLogger(__name__)

class SoftwareConfigExcelFiller:
    """软件配置项信息Excel填充器"""
    
    def __init__(self):
        """初始化Excel填充器"""
        self.logger = logger
        self.cell_mapping = self._get_cell_mapping()
    
    def fill_software_config_sheet(
        self,
        excel_file_path: str,
        sheet_name: str,
        software_config_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        填充软件配置项信息工作表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            software_config_data: 软件配置数据字典
            session_id: 会话ID，用于访问标准化文档（可选）
            
        Returns:
            bool: 填充是否成功
        """
        try:
            self.logger.info(f"开始填充软件配置项信息表: {sheet_name}")
            
            # 打开Excel工作簿
            wb = openpyxl.load_workbook(excel_file_path)
            
            # 获取工作表
            if sheet_name not in wb.sheetnames:
                self.logger.error(f"工作表 '{sheet_name}' 不存在")
                return False
            
            sheet = wb[sheet_name]
            
            # 填充数据
            self._fill_basic_software_info(sheet, software_config_data)
            self._fill_software_details(sheet, software_config_data)
            self._fill_statistics_info(sheet, software_config_data)
            self._fill_time_info(sheet, software_config_data)
            self._fill_fixed_values(sheet, software_config_data)
            
            # 保存文件
            wb.save(excel_file_path)
            
            self.logger.info("软件配置项信息表填充完成")
            return True
            
        except Exception as e:
            self.logger.error(f"填充软件配置项信息表时发生错误: {str(e)}")
            return False
    
    def _fill_basic_software_info(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充基本软件信息"""
        basic_info = software_config_data.get('basic_info', {})
        software_details = software_config_data.get('software_details', {})
        
        # 1. 软件名称
        software_name = basic_info.get('software_name', '')
        sheet.cell(row=2, column=3, value=software_name)
        
        # 8. 被测软件基础版本（回归测试）
        sheet.cell(row=9, column=3, value='')
        
        # 9. 被测软件版本
        software_version = software_details.get('software_version', '')
        sheet.cell(row=10, column=3, value=software_version)
        
        # 11. 软件规模
        code_lines = basic_info.get('code_lines', 0)
        sheet.cell(row=12, column=3, value=code_lines)
        
        self.logger.debug(f"基本软件信息填充完成: 名称={software_name}, 版本={software_version}, 规模={code_lines}")
    
    def _fill_software_details(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充软件详细信息"""
        software_details = software_config_data.get('software_details', {})
        data_sources = software_config_data.get('data_sources', {})
        
        # 检查是否有型号信息库数据
        if 'model_database' in data_sources:
            self._fill_from_model_database(sheet, software_details)
        else:
            # 使用AI生成或文档提取的信息
            self._fill_from_ai_or_document(sheet, software_details, software_config_data)
        
        # 填充其他详细信息
        self._fill_other_details(sheet, software_details)
    
    def _fill_from_model_database(self, sheet, software_details: Dict[str, Any]) -> None:
        """从型号信息库填充"""
        # 导入拼音工具
        from ...utils.pinyin_utils import get_software_short_name_en
        
        software_short_name = software_details.get('software_short_name', '')
        
        # ✅ 根据软件简称生成英文简称（拼音首字母），而不是使用数据库中的值
        software_short_name_en = get_software_short_name_en(software_short_name) if software_short_name else ''
        
        sheet.cell(row=3, column=3, value=software_short_name)                                  # 2. 软件简称
        sheet.cell(row=4, column=3, value=software_short_name_en)                               # 3. 软件简称（英文）✅ 使用拼音首字母
        sheet.cell(row=5, column=3, value=software_details.get('software_id', ''))             # 4. 软件标识
        sheet.cell(row=6, column=3, value=software_details.get('system_name', ''))             # 5. 系统名称
        sheet.cell(row=7, column=3, value=software_details.get('system_short_name', ''))       # 6. 系统简称
        sheet.cell(row=8, column=3, value=software_details.get('component', ''))               # 7. 组件
        sheet.cell(row=11, column=3, value=software_details.get('software_id', ''))            # 10. 软件代号
        sheet.cell(row=13, column=3, value=software_details.get('programming_language', ''))   # 12. 编程语言
        sheet.cell(row=14, column=3, value=software_details.get('development_environment', '')) # 13. 开发环境
        sheet.cell(row=15, column=3, value=software_details.get('runtime_environment', ''))    # 14. 运行环境
        sheet.cell(row=16, column=3, value=software_details.get('software_level', ''))         # 15. 软件等级
        
        self.logger.info(f"从型号信息库填充: 软件简称='{software_short_name}', 英文简称='{software_short_name_en}'")
    
    def _fill_from_ai_or_document(self, sheet, software_details: Dict[str, Any], software_config_data: Dict[str, Any]) -> None:
        """从AI生成或文档提取填充"""
        try:
            # ✅ 优先使用从需求文档中提取的软件信息
            basic_info = software_config_data.get('basic_info', {})
            software_name = basic_info.get('software_name', '')
            
            # 尝试从需求文档提取软件信息
            doc_info = self._extract_from_requirement_doc(software_config_data)
            
            if doc_info and doc_info.get('software_short_name'):
                # 如果从文档提取到了软件简称，使用文档提取的值并应用系统名称规则
                self.logger.info(f"使用文档提取的软件信息: {doc_info}")
                sheet.cell(row=3, column=3, value=doc_info.get('software_short_name', ''))
                sheet.cell(row=4, column=3, value=doc_info.get('software_short_name_en', ''))
                sheet.cell(row=6, column=3, value=doc_info.get('system_name', ''))
                sheet.cell(row=7, column=3, value=doc_info.get('system_short_name', ''))
                # ✅ 组件从用户输入的software_details获取
                sheet.cell(row=8, column=3, value=software_details.get('component', ''))
                
                self.logger.info("文档提取软件信息填充完成")
            elif software_name:
                # 如果没有从文档提取到，尝试使用AI生成
                ai_info = self._generate_ai_software_info(software_name)
                if ai_info:
                    sheet.cell(row=3, column=3, value=ai_info.get('software_short_name', ''))
                    sheet.cell(row=4, column=3, value=ai_info.get('software_short_name_en', ''))
                    sheet.cell(row=6, column=3, value=ai_info.get('system_name', ''))
                    sheet.cell(row=7, column=3, value=ai_info.get('system_short_name', ''))
                    # ✅ 组件从用户输入的software_details获取，不使用AI生成的值
                    sheet.cell(row=8, column=3, value=software_details.get('component', ''))
                    
                    self.logger.info(f"AI生成软件信息填充完成: {ai_info}")
                else:
                    self._fill_default_software_info(sheet, software_details)
            else:
                self._fill_default_software_info(sheet, software_details)
                
        except Exception as e:
            self.logger.error(f"填充软件信息失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            self._fill_default_software_info(sheet, software_details)
    
    def _extract_from_requirement_doc(self, software_config_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """从需求文档中提取软件信息"""
        try:
            # 获取需求文档路径
            requirement_doc_path = software_config_data.get('requirement_doc_path')
            if not requirement_doc_path or not Path(requirement_doc_path).exists():
                self.logger.info("未提供需求文档路径或文档不存在，跳过文档提取")
                return None
            
            # 导入软件信息提取器和拼音工具
            from .software_info_extract.software_info_extractor import extract_software_info_from_document
            from ...utils.pinyin_utils import get_software_short_name_en
            
            # 从文档中提取软件信息
            self.logger.info(f"从需求文档提取软件信息: {requirement_doc_path}")
            extract_result = extract_software_info_from_document(requirement_doc_path, debug_mode=True)
            
            if not extract_result.get('found'):
                self.logger.info(f"文档提取失败: {extract_result.get('message', '未知原因')}")
                return None
            
            doc_data = extract_result.get('data', {})
            if not doc_data:
                self.logger.info("文档中未提取到软件信息")
                return None
            
            self.logger.info(f"文档提取原始数据: {doc_data}")
            
            # ✅ 提取的数据已经包含system_name和system_short_name（由extractor自动计算）
            software_short_name = doc_data.get('software_short_name', '')
            system_name = doc_data.get('system_name', '')
            system_short_name = doc_data.get('system_short_name', '')
            
            # ✅ 根据软件简称生成英文简称（拼音首字母）
            software_short_name_en = get_software_short_name_en(software_short_name) if software_short_name else ''
            
            result = {
                'software_short_name': software_short_name,
                'software_short_name_en': software_short_name_en,
                'system_name': system_name,
                'system_short_name': system_short_name,
                'component': ''  # 组件从用户输入获取，不从文档提取
            }
            
            self.logger.info(f"文档提取处理后数据: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"从需求文档提取软件信息失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return None
    
    def _generate_ai_software_info(self, software_name: str) -> Optional[Dict[str, str]]:
        """生成AI软件信息（使用OpenAI）"""
        try:
            # ✅ 使用OpenAI生成软件信息
            from .ai_generator.openai_software_info_generator import generate_software_info_by_openai
            
            self.logger.info(f"开始使用OpenAI为软件 '{software_name}' 生成软件信息")
            
            # 调用OpenAI生成软件信息
            ai_result = generate_software_info_by_openai(software_name)
            
            if not ai_result:
                self.logger.warning("OpenAI未返回有效结果")
                return None
            
            # OpenAI已经直接返回了需要的格式，无需额外转换
            result = {
                'software_short_name': ai_result.get('software_short_name', ''),
                'software_short_name_en': ai_result.get('software_short_name_en', ''),
                'system_name': ai_result.get('system_name', ''),
                'system_short_name': ai_result.get('system_short_name', ''),
                'component': ''  # 组件从用户输入获取，不从AI生成
            }
            
            self.logger.info(f"OpenAI生成成功: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"OpenAI生成软件信息失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return None
    
    def _fill_default_software_info(self, sheet, software_details: Dict[str, Any]) -> None:
        """填充默认软件信息"""
        # 导入拼音工具
        from ...utils.pinyin_utils import get_software_short_name_en
        
        software_short_name = software_details.get('software_short_name', '')
        
        # ✅ 根据软件简称生成英文简称（拼音首字母）
        software_short_name_en = get_software_short_name_en(software_short_name) if software_short_name else ''
        
        sheet.cell(row=3, column=3, value=software_short_name)
        sheet.cell(row=4, column=3, value=software_short_name_en)  # ✅ 使用拼音首字母
        sheet.cell(row=6, column=3, value=software_details.get('system_name', ''))
        sheet.cell(row=7, column=3, value=software_details.get('system_short_name', ''))
        # ✅ 组件从用户输入的software_details获取
        sheet.cell(row=8, column=3, value=software_details.get('component', ''))
        
        self.logger.info(f"默认软件信息填充: 软件简称='{software_short_name}', 英文简称='{software_short_name_en}', 组件='{software_details.get('component', '')}'")
    
    def _fill_other_details(self, sheet, software_details: Dict[str, Any]) -> None:
        """填充其他详细信息"""
        # 4. 软件标识
        software_id = software_details.get('software_id', '')
        sheet.cell(row=5, column=3, value=software_id)
        
        # 10. 软件代号
        sheet.cell(row=11, column=3, value=software_id)
        
        # 12. 编程语言
        sheet.cell(row=13, column=3, value=software_details.get('programming_language', 'ANSIC'))
        
        # 13-14. 开发环境和运行环境（智能提取）
        self._fill_environment_info(sheet, software_details)
        
        # 15. 软件等级
        sheet.cell(row=16, column=3, value=software_details.get('software_level', '重要'))
    
    def _fill_environment_info(self, sheet, software_details: Dict[str, Any]) -> None:
        """填充环境信息（智能提取）"""
        try:
            log_info("开始填充环境信息（智能提取）", "software_config_excel_filler")
            
            # 导入环境信息提取器
            from .ai_generator.environment_extractor import EnvironmentExtractor
            
            # 获取默认值
            dev_env = software_details.get('development_environment', 'AcoreIde')
            runtime_env = software_details.get('runtime_environment', '飞腾2000（天脉3）')
            
            log_debug(f"默认环境值 - 开发环境: {dev_env}, 运行环境: {runtime_env}", "software_config_excel_filler")
            
            # 尝试从需求文档中智能提取环境信息
            try:
                # 这里需要获取需求文档路径和内容
                # 可以从software_config_data中获取requirement_doc_path
                requirement_doc_path = getattr(self, '_current_requirement_doc_path', None)
                
                log_debug(f"需求文档路径: {requirement_doc_path}", "software_config_excel_filler")
                
                if requirement_doc_path:
                    log_info("开始智能提取环境信息", "software_config_excel_filler")
                    extractor = EnvironmentExtractor()
                    
                    # 读取需求文档内容
                    log_debug("开始读取需求文档内容", "software_config_excel_filler")
                    requirement_content = self._read_requirement_document(requirement_doc_path)
                    
                    if requirement_content:
                        log_info(f"需求文档读取成功，内容长度: {len(requirement_content)}", "software_config_excel_filler")
                        
                        # 获取AI分析函数（如果可用）
                        ai_function = getattr(self, '_ai_analysis_function', None)
                        log_debug(f"AI分析函数: {'已设置' if ai_function else '未设置'}", "software_config_excel_filler")
                        
                        # 提取环境信息
                        log_info("调用环境提取器", "software_config_excel_filler")
                        extracted_info = extractor.extract_environment_info(
                            requirement_content, ai_function, session_id  # 🔧 传递session_id
                        )
                        
                        log_info(f"环境提取结果: {extracted_info}", "software_config_excel_filler")
                        
                        # 使用提取的信息（如果成功提取）
                        if extracted_info.get('development_environment'):
                            dev_env = extracted_info['development_environment']
                            log_info(f"智能提取开发环境: {dev_env}", "software_config_excel_filler")
                        else:
                            log_warning("未提取到开发环境信息，使用默认值", "software_config_excel_filler")
                        
                        if extracted_info.get('runtime_environment'):
                            runtime_env = extracted_info['runtime_environment']
                            log_info(f"智能提取运行环境: {runtime_env}", "software_config_excel_filler")
                        else:
                            log_warning("未提取到运行环境信息，使用默认值", "software_config_excel_filler")
                    else:
                        log_warning("无法读取需求文档内容，使用默认环境信息", "software_config_excel_filler")
                else:
                    log_warning("未提供需求文档路径，使用默认环境信息", "software_config_excel_filler")
                    
            except Exception as extract_error:
                log_error(f"智能提取环境信息失败，使用默认值: {extract_error}", "software_config_excel_filler")
                import traceback
                log_error(f"环境提取错误详情: {traceback.format_exc()}", "software_config_excel_filler")
            
            # 填充到Excel
            log_debug(f"填充环境信息到Excel - 开发环境(row=14): {dev_env}", "software_config_excel_filler")
            log_debug(f"填充环境信息到Excel - 运行环境(row=15): {runtime_env}", "software_config_excel_filler")
            
            sheet.cell(row=14, column=3, value=dev_env)      # 13. 开发环境
            sheet.cell(row=15, column=3, value=runtime_env)  # 14. 运行环境
            
            log_info(f"环境信息填充完成: 开发环境='{dev_env}', 运行环境='{runtime_env}'", "software_config_excel_filler")
            
        except Exception as e:
            log_error(f"环境信息填充失败: {e}", "software_config_excel_filler")
            import traceback
            log_error(f"环境填充错误详情: {traceback.format_exc()}", "software_config_excel_filler")
            # 使用默认值作为兜底
            sheet.cell(row=14, column=3, value='AcoreIde')
            sheet.cell(row=15, column=3, value='飞腾2000（天脉3）')
            log_warning("使用默认环境信息作为兜底", "software_config_excel_filler")
    
    def _read_requirement_document(self, doc_path: str) -> Optional[str]:
        """读取需求文档内容"""
        try:
            log_debug(f"开始读取需求文档: {doc_path}", "software_config_excel_filler")
            
            from pathlib import Path
            import docx
            
            doc_path = Path(doc_path)
            log_debug(f"文档路径对象: {doc_path}", "software_config_excel_filler")
            
            if not doc_path.exists():
                log_error(f"需求文档不存在: {doc_path}", "software_config_excel_filler")
                return None
            
            log_debug(f"文档文件大小: {doc_path.stat().st_size} 字节", "software_config_excel_filler")
            log_debug(f"文档扩展名: {doc_path.suffix.lower()}", "software_config_excel_filler")
            
            if doc_path.suffix.lower() == '.docx':
                # 读取Word文档
                log_debug("开始读取Word文档", "software_config_excel_filler")
                doc = docx.Document(doc_path)
                paragraphs = [paragraph.text for paragraph in doc.paragraphs]
                content = '\n'.join(paragraphs)
                log_info(f"Word文档读取成功，段落数: {len(paragraphs)}, 内容长度: {len(content)}", "software_config_excel_filler")
                log_debug(f"文档内容前500字符: {content[:500]}...", "software_config_excel_filler")
                return content
            elif doc_path.suffix.lower() == '.txt':
                # 读取文本文档
                log_debug("开始读取文本文档", "software_config_excel_filler")
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                log_info(f"文本文档读取成功，内容长度: {len(content)}", "software_config_excel_filler")
                log_debug(f"文档内容前500字符: {content[:500]}...", "software_config_excel_filler")
                return content
            else:
                log_error(f"不支持的文档格式: {doc_path.suffix}", "software_config_excel_filler")
                return None
                
        except Exception as e:
            log_error(f"读取需求文档时发生错误: {str(e)}", "software_config_excel_filler")
            import traceback
            log_error(f"文档读取错误详情: {traceback.format_exc()}", "software_config_excel_filler")
            return None
    
    def set_requirement_doc_path(self, doc_path: str) -> None:
        """设置需求文档路径"""
        self._current_requirement_doc_path = doc_path
        log_info(f"设置需求文档路径: {doc_path}", "software_config_excel_filler")
        
        # 验证文档是否存在
        from pathlib import Path
        if Path(doc_path).exists():
            log_debug("需求文档路径验证成功", "software_config_excel_filler")
        else:
            log_warning(f"需求文档路径不存在: {doc_path}", "software_config_excel_filler")
    
    def set_ai_analysis_function(self, ai_function: callable) -> None:
        """设置AI分析函数"""
        self._ai_analysis_function = ai_function
        log_info("AI分析函数设置成功", "software_config_excel_filler")
        log_debug(f"AI函数类型: {type(ai_function)}", "software_config_excel_filler")
    
    def _fill_statistics_info(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充统计信息"""
        basic_info = software_config_data.get('basic_info', {})
        statistics_info = software_config_data.get('statistics_info', {})
        
        # 16. 责任人（测试人员）
        if basic_info.get('is_same_person', False):
            sheet.cell(row=17, column=3, value=basic_info.get('manager_name', ''))
        else:
            tester_name = basic_info.get('tester_name', '')
            manager_name = basic_info.get('manager_name', '')
            sheet.cell(row=17, column=3, value=f"{manager_name}、{tester_name}")
        
        # 19-22. 规模相关信息
        sheet.cell(row=20, column=3, value=statistics_info.get('software_change_scale', 0))
        sheet.cell(row=21, column=3, value=statistics_info.get('test_scale', 0))
        sheet.cell(row=22, column=3, value=statistics_info.get('review_document_scale', 60))
        sheet.cell(row=23, column=3, value=statistics_info.get('test_document_scale', 0))
        
        # 27-31. 测试相关统计
        sheet.cell(row=28, column=3, value=statistics_info.get('actual_test_workload', 2))
        sheet.cell(row=29, column=3, value=statistics_info.get('remaining_issues_count', 0))  # ✨ 遗留问题总数默认填0
        sheet.cell(row=30, column=3, value=statistics_info.get('test_depth', '全面测试'))
        sheet.cell(row=31, column=3, value=statistics_info.get('planning_requirements_count', 0))
        
        # 38-41. 需求相关统计
        sheet.cell(row=39, column=3, value=statistics_info.get('effective_test_code_scale', 0))
        sheet.cell(row=40, column=3, value=statistics_info.get('planning_requirements_count', 0))
        sheet.cell(row=41, column=3, value=statistics_info.get('analysis_requirements_count', 0))
        
        # 42-44. 项目成员相关
        self._fill_team_member_info(sheet, basic_info, statistics_info)
        
        # 48. 标准需求数 - 需求：不填任何内容（空着）
        # sheet.cell(row=48, column=3, value=statistics_info.get('planning_requirements_count', 0))  # 已注释，保持空值
    
    def _fill_team_member_info(self, sheet, basic_info: Dict[str, Any], statistics_info: Dict[str, Any]) -> None:
        """填充团队成员信息"""
        if basic_info.get('is_same_person', False):
            sheet.cell(row=43, column=3, value='')  # 项目成员测试规模
            sheet.cell(row=44, column=3, value='')  # 项目成员投入工时
        else:
            test_scale = statistics_info.get('test_scale', 0)
            member_scale_1 = round(test_scale * 0.2)
            member_scale_2 = round(test_scale - member_scale_1)
            member_hours_1 = 1
            member_hours_2 = round(test_scale / 500) + 2
            
            sheet.cell(row=43, column=3, value=f"{member_scale_1}、{member_scale_2}")
            sheet.cell(row=44, column=3, value=f"{member_hours_1}、{member_hours_2}")
    
    def _fill_time_info(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充时间信息"""
        time_info = software_config_data.get('time_info', {})
        
        sheet.cell(row=24, column=3, value=time_info.get('planned_start_time', ''))    # 23. 计划开始时间
        sheet.cell(row=25, column=3, value=time_info.get('planned_end_time', ''))      # 24. 计划结束时间
        sheet.cell(row=26, column=3, value=time_info.get('actual_start_time', ''))     # 25. 启动时间（实际）
        sheet.cell(row=27, column=3, value=time_info.get('actual_end_time', ''))       # 26. 结束时间（实际）
    
    def _fill_fixed_values(self, sheet, software_config_data: Dict[str, Any]) -> None:
        """填充固定值"""
        from openpyxl.styles import PatternFill, Alignment
        fixed_values = software_config_data.get('fixed_values', {})
        
        print("\n" + "="*80)
        print("[SOFTWARE_CONFIG] _fill_fixed_values 开始执行")
        print("="*80)
        
        # 蓝色填充（用于已填写的数据）
        light_blue_fill = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")
        center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        sheet.cell(row=18, column=3, value=fixed_values.get('is_closed', '是'))                    # 17. 是否闭项
        sheet.cell(row=19, column=3, value=fixed_values.get('is_urgent', '是'))                    # 18. 是否紧急
        sheet.cell(row=32, column=3, value=fixed_values.get('remarks', '无'))                      # 31. 备注
        sheet.cell(row=33, column=3, value=fixed_values.get('development_stage', 'S'))             # 32. 研制阶段
        sheet.cell(row=34, column=3, value=fixed_values.get('verification_status', '所内验证'))     # 33. 验证情况
        sheet.cell(row=35, column=3, value=fixed_values.get('config_management_status', '首次入库')) # 34. 配置管理状态
        sheet.cell(row=36, column=3, value=fixed_values.get('purpose', '联试'))                    # 35. 用途
        sheet.cell(row=37, column=3, value=fixed_values.get('related_major_issues', '无'))         # 36. 关联重大事项
        sheet.cell(row=38, column=3, value=fixed_values.get('is_model_generated', '否'))           # 37. 是否模型生成项目
        sheet.cell(row=42, column=3, value=fixed_values.get('is_cooperation_project', '是'))       # 41. 是否合作项目
        
        print("\n[SOFTWARE_CONFIG] 搜索关键行位置:")
        
        # 搜索"是否出差项目"所在的行
        business_trip_row = None
        for row_num in range(45, 52):  # 搜索45-52行
            b_col_value = sheet.cell(row=row_num, column=2).value
            if b_col_value and '出差' in str(b_col_value):
                business_trip_row = row_num
                print(f"  找到'是否出差项目'在第{row_num}行，B列: '{b_col_value}'")
                break
        
        if not business_trip_row:
            print("  未找到'是否出差项目'行，显示45-52行供参考：")
            for row_num in range(45, 52):
                b_val = sheet.cell(row=row_num, column=2).value
                c_val = sheet.cell(row=row_num, column=3).value
                print(f"    第{row_num}行 B列: '{b_val}' | C列: '{c_val}'")
        
        # 45. 软件类型 - 需求：不填任何内容（空着）
        print("\n[SOFTWARE_CONFIG] 处理第45行（软件类型）- 保持空值")
        # sheet.cell(row=45, column=3, value=fixed_values.get('software_type', '应用软件'))  # 已注释，保持空值
        
        # 46. 软件类别 - 需求：不填任何内容（空着）
        print("\n[SOFTWARE_CONFIG] 处理第46行（软件类别）- 保持空值")
        
        # ✨ 47. 开发人员工作量 - 需求：默认填0，蓝色背景
        print("\n[SOFTWARE_CONFIG] 处理第47行（开发人员工作量）")
        cell_b47 = sheet.cell(row=47, column=2)
        cell_c47 = sheet.cell(row=47, column=3)
        print(f"  修改前 - B47: '{cell_b47.value}' | C47: '{cell_c47.value}'")
        
        cell_c47.value = fixed_values.get('developer_workload', 0)
        cell_c47.fill = light_blue_fill
        print(f"  修改后 - B47: '{cell_b47.value}' | C47: '{cell_c47.value}' | 填充色: 蓝色")
        
        # 48. 标准需求数 - 保持空值
        print("\n[SOFTWARE_CONFIG] 处理第48行（标准需求数）- 保持空值")
        
        # ✨ 动态处理"是否出差项目" - 需求：B列居中，C列填"否"并设置蓝色背景
        if business_trip_row:
            print(f"\n[SOFTWARE_CONFIG] 处理第{business_trip_row}行（是否出差项目）")
            cell_b_trip = sheet.cell(row=business_trip_row, column=2)  # B列：标签
            cell_c_trip = sheet.cell(row=business_trip_row, column=3)  # C列：值
            print(f"  修改前 - B列: '{cell_b_trip.value}' | C列: '{cell_c_trip.value}'")
            print(f"  修改前 - B列对齐: {cell_b_trip.alignment.horizontal}/{cell_b_trip.alignment.vertical}")
            
            # B列标签居中
            cell_b_trip.alignment = center_alignment
            
            # C列填"否"并设置蓝色背景
            cell_c_trip.value = fixed_values.get('is_business_trip', '否')
            cell_c_trip.fill = light_blue_fill
            print(f"  修改后 - B列: '{cell_b_trip.value}' | C列: '{cell_c_trip.value}' | 填充色: 蓝色")
            print(f"  修改后 - B列对齐: {cell_b_trip.alignment.horizontal}/{cell_b_trip.alignment.vertical}")
        else:
            print("\n[SOFTWARE_CONFIG] 警告：未找到'是否出差项目'行，跳过处理")
        
        print("\n" + "="*80)
        print("[SOFTWARE_CONFIG] _fill_fixed_values 执行完毕")
        print("="*80 + "\n")
    
    def _get_cell_mapping(self) -> Dict[str, tuple]:
        """获取单元格映射关系"""
        return {
            'software_name': (2, 3),                    # 软件名称
            'software_short_name': (3, 3),              # 软件简称
            'software_short_name_en': (4, 3),           # 软件简称（英文）
            'software_id': (5, 3),                      # 软件标识
            'system_name': (6, 3),                      # 系统名称
            'system_short_name': (7, 3),                # 系统简称
            'component': (8, 3),                        # 组件
            'base_version': (9, 3),                     # 被测软件基础版本
            'software_version': (10, 3),                # 被测软件版本
            'software_code': (11, 3),                   # 软件代号
            'software_scale': (12, 3),                  # 软件规模
            'programming_language': (13, 3),            # 编程语言
            'development_environment': (14, 3),         # 开发环境
            'runtime_environment': (15, 3),             # 运行环境
            'software_level': (16, 3),                  # 软件等级
            'responsible_person': (17, 3),              # 责任人
            'is_closed': (18, 3),                       # 是否闭项
            'is_urgent': (19, 3),                       # 是否紧急
            'software_change_scale': (20, 3),           # 软件更改规模
            'test_code_scale': (21, 3),                 # 测试代码规模
            'review_document_scale': (22, 3),           # 审查文档规模
            'test_document_scale': (23, 3),             # 编写测试文档规模
            'planned_start_time': (24, 3),              # 计划开始时间
            'planned_end_time': (25, 3),                # 计划结束时间
            'actual_start_time': (26, 3),               # 启动时间（实际）
            'actual_end_time': (27, 3),                 # 结束时间（实际）
            'actual_test_workload': (28, 3),            # 实际测试工作量
            'remaining_issues_count': (29, 3),          # 遗留问题总数
            'test_depth': (30, 3),                      # 测试深度
            'test_item_count': (31, 3),                 # 测试项数量
            'remarks': (32, 3),                         # 备注
            'development_stage': (33, 3),               # 研制阶段
            'verification_status': (34, 3),             # 验证情况
            'config_management_status': (35, 3),        # 配置管理状态
            'purpose': (36, 3),                         # 用途
            'related_major_issues': (37, 3),            # 关联重大事项
            'is_model_generated': (38, 3),              # 是否模型生成项目
            'effective_test_code_scale': (39, 3),       # 有效测试代码规模
            'requirement_capture_count': (40, 3),       # 被测软件需求捕获总数
            'requirement_test_count': (41, 3),          # 被测软件需求测试总数
            'is_cooperation_project': (42, 3),          # 是否合作项目
            'member_test_scale': (43, 3),               # 项目成员测试规模
            'member_work_hours': (44, 3),               # 项目成员工时
            'software_type': (45, 3),                   # 软件类型
            'developer_workload': (46, 3),              # ✨ 开发人员工作量
            'is_business_trip': (47, 3),                # 是否出差项目
            'standard_requirement_count': (48, 3)       # 标准需求数
        }
    
    def get_filled_data_summary(self, excel_file_path: str, sheet_name: str) -> Dict[str, str]:
        """获取已填充数据的摘要"""
        try:
            wb = openpyxl.load_workbook(excel_file_path)
            sheet = wb[sheet_name]
            
            summary = {}
            for field, (row, col) in self.cell_mapping.items():
                cell_value = sheet.cell(row=row, column=col).value
                summary[field] = str(cell_value) if cell_value else ""
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取填充数据摘要时发生错误: {str(e)}")
            return {}
