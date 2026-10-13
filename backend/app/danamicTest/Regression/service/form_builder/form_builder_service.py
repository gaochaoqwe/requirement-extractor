"""
回归测试表单构建服务
整合了无策划表和有策划表的表单生成功能
从core/form_builder.py和core/form_builder_with_planning.py重构而来
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

try:
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ....utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..requirement_analysis import RegressionRequirementAnalysisService
from ..test_case_generation import generate_test_cases_for_form
from ..test_case_generation.test_case_form_handler import write_test_cases_to_excel, get_test_time_info
from ..issue_report import RegressionIssueReportService
from ..software_config import RegressionSoftwareConfigService
from ..project_info import RegressionProjectInfoService
from ..project_plan import RegressionProjectPlanService


class RegressionFormBuilderService:
    """回归测试表单构建服务（无策划表版本）"""
    
    def __init__(self):
        self.requirement_service = RegressionRequirementAnalysisService()
        self.issue_service = RegressionIssueReportService()
        self.software_config_service = RegressionSoftwareConfigService()
        self.project_info_service = RegressionProjectInfoService()
        self.project_plan_service = RegressionProjectPlanService()
    
    def ceshibiaodan_tianchong(self, file_path_wenjianjia: str, zhuguan_name: str, 
                              ceshiren_name: str, kaifarenxinxi: List[str], ceshileixing: str,
                              AI_fenx_flag_Anniu: bool, AI_deep_fenx_flag_Anniu: bool, 
                              suoshulingyu: str, jianceyi_flag: str, resource_manager=None,
                              user_software_info: Dict[str, str] = None, catalog_path: str = None,
                              code_lines: int = None, code_file_path: str = None) -> int:
        """
        回归测试表单填充函数（无策划表版本）
        
        Args:
            file_path_wenjianjia: 文件夹路径
            zhuguan_name: 主管姓名
            ceshiren_name: 测试人员
            kaifarenxinxi: 开发人员信息
            ceshileixing: 测试类型
            AI_fenx_flag_Anniu: AI分析标志
            AI_deep_fenx_flag_Anniu: 深度分析标志
            suoshulingyu: 所属领域
            jianceyi_flag: 检测仪标志
            resource_manager: 资源管理器
            user_software_info: 用户软件信息
            catalog_path: 目录路径
            code_lines: 代码行数
            code_file_path: 代码文件路径
            
        Returns:
            int: 生成结果 (1表示成功，0表示失败)
        """
        try:
            if ceshileixing == '回归测试':
                return self._handle_regression_test(
                    file_path_wenjianjia, zhuguan_name, ceshiren_name, 
                    kaifarenxinxi, AI_fenx_flag_Anniu, AI_deep_fenx_flag_Anniu,
                    suoshulingyu, jianceyi_flag, resource_manager, 
                    user_software_info, code_lines
                )
            else:
                log_warning(f"不支持的测试类型: {ceshileixing}", "regression_form_builder")
                return 0
                
        except Exception as e:
            log_error(f"填充回归测试表单时发生错误", "regression_form_builder", e)
            return 0
    
    def check_word_document_huigui(self, file_path: str) -> str:
        """
        检查回归测试相关文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            str: 文档路径或'0'表示失败
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return '0'
            
            # 检查是否为目录
            if os.path.isdir(file_path):
                # 在目录中查找软件变更与影响域分析报告
                for file in os.listdir(file_path):
                    if file.endswith('.docx') and ('变更' in file or '影响' in file or '分析' in file):
                        full_path = os.path.join(file_path, file)
                        return full_path
                return '0'
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.docx'):
                return '0'
            
            return file_path
            
        except Exception as e:
            log_error(f"检查回归测试文档失败", "regression_form_builder", e)
            return '0'
    
    def read_word_tables(self, file_path: str) -> List[List[str]]:
        """
        读取Word文档中的表格数据
        
        Args:
            file_path: Word文档路径
            
        Returns:
            List[List[str]]: 表格数据列表
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            tables_data = []
            
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        row_data.append(cell.text.strip())
                    table_data.append(row_data)
                tables_data.append(table_data)
            
            log_info(f"成功读取 {len(tables_data)} 个表格", "regression_form_builder")
            return tables_data
            
        except Exception as e:
            log_error(f"读取Word表格失败", "regression_form_builder", e)
            return []
    
    def _handle_regression_test(self, file_path_wenjianjia: str, zhuguan_name: str,
                               ceshiren_name: str, kaifarenxinxi: List[str],
                               AI_fenx_flag_Anniu: bool, AI_deep_fenx_flag_Anniu: bool,
                               suoshulingyu: str, jianceyi_flag: str, resource_manager,
                               user_software_info: Dict[str, str], code_lines: int) -> int:
        """处理回归测试流程"""
        try:
            # 1. 读取软件变更与影响域分析报告
            file_path_biangeng_word = self.check_word_document_huigui(file_path_wenjianjia)
            if file_path_biangeng_word == '0':
                log_error("被测文档路径中未包含软件变更与影响域分析报告", "regression_form_builder")
                return 0
            
            # 2. 准备测试表单模板
            excel_file_path = self._prepare_test_templates(resource_manager)
            if not excel_file_path:
                log_error("测试表单模板准备失败", "regression_form_builder")
                return 0
            
            # 3. 设置代码差异行数
            daima_chayi_lines = code_lines if code_lines is not None else 0
            log_info("跳过代码差异分析，使用默认值", "regression_form_builder")
            
            # 4. 读取软件信息和需求变更
            ruanjian_xinxi_duqu_temp, ceshixiang_neirong_dict = self._read_software_and_requirements(
                file_path_biangeng_word, user_software_info
            )
            
            if not ruanjian_xinxi_duqu_temp:
                log_error("软件信息读取失败", "regression_form_builder")
                return 0
            
            # 5. 填充各个表格
            success = self._fill_all_tables(
                excel_file_path, ruanjian_xinxi_duqu_temp, ceshixiang_neirong_dict,
                zhuguan_name, ceshiren_name, kaifarenxinxi, suoshulingyu,
                AI_fenx_flag_Anniu, AI_deep_fenx_flag_Anniu, jianceyi_flag,
                daima_chayi_lines
            )
            
            if success:
                log_info(f"回归测试表单填充完成: {excel_file_path}", "regression_form_builder")
                return 1
            else:
                return 0
                
        except Exception as e:
            log_error(f"处理回归测试时发生错误", "regression_form_builder", e)
            return 0
    
    def _prepare_test_templates(self, resource_manager) -> Optional[str]:
        """准备测试表单模板"""
        try:
            if resource_manager:
                beifen_excel = resource_manager.get_templates_dir()
                ceshidan_folder_path = tempfile.mkdtemp(prefix='regression_test_')
                log_info(f"使用临时工作目录: {ceshidan_folder_path}", "regression_form_builder")
            else:
                current_dir = Path(__file__).parent.parent.parent
                beifen_excel = str(current_dir / "resources" / "templates")
                ceshidan_folder_path = str(current_dir / "temp" / "CeshiDan")
                os.makedirs(ceshidan_folder_path, exist_ok=True)
                log_info(f"使用相对路径: templates={beifen_excel}, work_dir={ceshidan_folder_path}", "regression_form_builder")
            
            # 复制模板文件
            self._copy_excel_files(beifen_excel, ceshidan_folder_path)
            excel_file_path = os.path.join(ceshidan_folder_path, '需求分析表(精准测试工具生成).xlsx')
            
            return excel_file_path
            
        except Exception as e:
            log_error(f"准备测试模板失败", "regression_form_builder", e)
            return None
    
    def _copy_excel_files(self, source_dir: str, dest_dir: str):
        """复制Excel模板文件"""
        try:
            if not os.path.exists(source_dir):
                log_warning(f"模板目录不存在: {source_dir}", "regression_form_builder")
                return
            
            for file in os.listdir(source_dir):
                if file.endswith('.xlsx'):
                    source_file = os.path.join(source_dir, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(source_file, dest_file)
                    
        except Exception as e:
            log_error(f"复制Excel文件失败", "regression_form_builder", e)
    
    def _read_software_and_requirements(self, file_path: str, user_software_info: Dict) -> Tuple[Dict, Dict]:
        """读取软件信息和需求变更"""
        try:
            # 读取软件信息 - 这里应该调用requirement_reader中的功能
            # 暂时返回默认值
            ruanjian_xinxi = {
                '软件名称': user_software_info.get('software_name', '回归测试软件') if user_software_info else '回归测试软件',
                '软件版本': user_software_info.get('software_version', '1.0.0') if user_software_info else '1.0.0',
                '被测软件版本': [user_software_info.get('software_version', '1.0.0')] if user_software_info else ['1.0.0']
            }
            
            # 读取测试项内容
            ceshixiang_neirong = {
                "回归功能测试1": "验证修改后的功能是否正常",
                "回归接口测试": "验证接口修改后的兼容性",
                "回归性能测试": "验证性能是否受到影响",
                "回归安全测试": "验证安全功能是否正常"
            }
            
            return ruanjian_xinxi, ceshixiang_neirong
            
        except Exception as e:
            log_error(f"读取软件信息和需求失败", "regression_form_builder", e)
            return {}, {}
    
    def _fill_all_tables(self, excel_file_path: str, ruanjian_xinxi: Dict, 
                        ceshixiang_neirong: Dict, zhuguan_name: str, ceshiren_name: str,
                        kaifarenxinxi: List[str], suoshulingyu: str, AI_fenx_flag_Anniu: bool,
                        AI_deep_fenx_flag_Anniu: bool, jianceyi_flag: str, 
                        daima_chayi_lines: int) -> bool:
        """填充所有表格"""
        try:
            sheet_names = {
                'requirement_analysis': '需求分析表',
                'test_case': '测试用例单',
                'issue_report': '问题报告单',
                'software_config': '软件配置项信息',
                'project_info': '项目基本信息',
                'project_plan': '项目策划表'
            }
            
            log_info("开始填充回归测试表单...", "regression_form_builder")
            
            # 填充项目基本信息表
            log_info("开始填充项目基本信息表...", "regression_form_builder")
            project_info_success = self._fill_project_info_table(
                excel_file_path, sheet_names['project_info'],
                ruanjian_xinxi, zhuguan_name, ceshiren_name, 
                kaifarenxinxi, suoshulingyu
            )
            
            if not project_info_success:
                log_error("项目基本信息表填充失败", "regression_form_builder")
                return False
            
            # 填充软件配置项信息表
            log_info("开始填充软件配置项信息表...", "regression_form_builder")
            software_config_success = self._fill_software_config_table(
                excel_file_path, sheet_names['software_config'],
                ruanjian_xinxi, zhuguan_name, ceshiren_name,
                kaifarenxinxi, suoshulingyu, daima_chayi_lines, user_software_info
            )
            
            if not software_config_success:
                log_error("软件配置项信息表填充失败", "regression_form_builder")
                return False
            
            # 填充需求分析表
            log_info("开始填充需求分析表...", "regression_form_builder")
            requirement_analysis_success = self._fill_requirement_analysis_table(
                excel_file_path, sheet_names['requirement_analysis'],
                ruanjian_xinxi, ceshixiang_neirong, AI_fenx_flag_Anniu
            )
            
            if not requirement_analysis_success:
                log_error("需求分析表填充失败", "regression_form_builder")
                return False
            
            # TODO: 后续实现其他表格的填充逻辑
            # - 测试用例单  
            # - 问题报告单
            # - 项目策划表
            
            log_info("回归测试表单填充完成", "regression_form_builder")
            return True
            
        except Exception as e:
            log_error(f"填充表格失败", "regression_form_builder", e)
            return False
    
    def _fill_requirement_analysis_table(self, excel_file_path: str, sheet_name: str,
                                        ruanjian_xinxi: Dict, ceshixiang_neirong: Dict, 
                                        AI_fenx_flag_Anniu: bool) -> bool:
        """填充需求分析表"""
        try:
            log_info(f"开始填充回归测试需求分析表: {sheet_name}", "regression_form_builder")
            
            # 构建与配置项模块兼容的数据结构
            ruanjian_name = ruanjian_xinxi.get('软件名称', ['回归测试软件'])[0]
            
            # 构建需求数据结构（类似配置项模块的final_xuqiu_mioashu）
            diama_biangeng_xuqiu = {}
            for req_id, req_desc in ceshixiang_neirong.items():
                # 如果req_desc是字符串，构建完整的需求数据结构
                if isinstance(req_desc, str):
                    diama_biangeng_xuqiu[req_id] = {
                        'name': req_id,  # 这里可能是REQ-001格式，会在excel_filler中进一步处理
                        'description': req_desc,
                        'software_name': ruanjian_name
                    }
                else:
                    diama_biangeng_xuqiu[req_id] = req_desc
            
            # 🚨 关键修复：提取实际的需求名称而不是REQ标识符
            # 构建实际需求名称列表用于传递给Excel填充器
            actual_requirement_names = []
            for req_id, req_data in diama_biangeng_xuqiu.items():
                if isinstance(req_data, dict) and 'name' in req_data:
                    # 如果有name字段，使用它（可能包含章节号，excel_filler会进一步处理）
                    actual_requirement_names.append(req_data['name'])
                else:
                    # 向下兼容：直接使用req_id
                    actual_requirement_names.append(req_id)
            
            neirong_dict = []
            for req_data in diama_biangeng_xuqiu.values():
                if isinstance(req_data, dict):
                    neirong_dict.append(req_data.get('description', ''))
                else:
                    neirong_dict.append(str(req_data))
            
            # 调用需求分析service
            success = self.requirement_service.generate_requirement_analysis_table(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                ruanjian_xinxi=ruanjian_xinxi,
                ruanjian_name=ruanjian_name,
                diama_biangeng_xuqiu=diama_biangeng_xuqiu,
                file_path="",
                ceshileixing="回归测试",
                neirong_dict=neirong_dict,
                biaoshihao_ceshixianng=actual_requirement_names,  # 🚨 传递实际需求名称
                AI_fenx_flag_Anniu=1 if AI_fenx_flag_Anniu else 0,
                jianceyi_flag=0
            )
            
            if success:
                log_info(f"回归测试需求分析表填充成功: {sheet_name}", "regression_form_builder")
            else:
                log_error(f"回归测试需求分析表填充失败: {sheet_name}", "regression_form_builder")
            
            return success
            
        except Exception as e:
            log_error(f"填充回归测试需求分析表时发生错误: {e}", "regression_form_builder", e)
            return False
    
    def _fill_project_info_table(self, excel_file_path: str, sheet_name: str,
                                ruanjian_xinxi: Dict, zhuguan_name: str, ceshiren_name: str,
                                kaifarenxinxi: List[str], suoshulingyu: str) -> bool:
        """填充项目基本信息表"""
        try:
            # 准备基本信息，从ruanjian_xinxi中提取
            basic_info = {
                'software_name': ruanjian_xinxi.get('软件名称', ''),
                'software_version': ruanjian_xinxi.get('软件版本', ''),
                'domain': suoshulingyu,
                'aircraft_model': '',  # 回归测试可能没有飞机型号
                'software_id': '',     # 可以从ruanjian_xinxi中提取
                'project_director': '',
                'development_department': '',
                'chief_designer': ''
            }
            
            # 调用项目信息service
            success = self.project_info_service.generate_project_info_table(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                basic_info=basic_info,
                zhuguan_name=zhuguan_name,
                kaifarenxinxi=kaifarenxinxi,
                xinghao_xinxi_list=None,
                suoshulingyu=suoshulingyu,
                apply_formatting=True
            )
            
            if success:
                log_info(f"回归测试项目基本信息表填充成功: {sheet_name}", "regression_form_builder")
            else:
                log_error(f"回归测试项目基本信息表填充失败: {sheet_name}", "regression_form_builder")
                
            return success
            
        except Exception as e:
            log_error(f"填充回归测试项目基本信息表时发生错误", "regression_form_builder", e)
            return False
    
    def _fill_software_config_table(self, excel_file_path: str, sheet_name: str,
                                   ruanjian_xinxi: Dict, zhuguan_name: str, ceshiren_name: str,
                                   kaifarenxinxi: List[str], suoshulingyu: str, 
                                   daima_chayi_lines: int, user_software_info: Dict = None) -> bool:
        """填充软件配置项信息表"""
        try:
            # 准备软件名称
            ruanjian_name = ruanjian_xinxi.get('软件名称', '回归测试软件')
            
            log_debug(f"[DEBUG] 回归测试软件配置项表参数:", "regression_form_builder")
            log_debug(f"   user_software_info: {user_software_info}", "regression_form_builder")
            log_debug(f"   ruanjian_name: '{ruanjian_name}'", "regression_form_builder")
            
            # 调用软件配置项信息service
            success = self.software_config_service.generate_software_config_table(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                ruanjian_name=ruanjian_name,
                ceshiren_name=ceshiren_name,
                zhuguan_name=zhuguan_name,
                daima_chayi_hangshu=daima_chayi_lines,
                xinghao_xinxi_list=None,
                ruanjian_xinxi_duqu_temp=ruanjian_xinxi,
                ceshileixing="回归测试",
                user_software_info=user_software_info,  # 修复：传递用户软件信息
                planning_requirements_count=0,
                analysis_requirements_count=0,
                code_path=None,
                impact_analysis_doc_path=None,
                apply_formatting=True
            )
            
            if success:
                log_info(f"回归测试软件配置项信息表填充成功: {sheet_name}", "regression_form_builder")
            else:
                log_error(f"回归测试软件配置项信息表填充失败: {sheet_name}", "regression_form_builder")
                
            return success
            
        except Exception as e:
            log_error(f"填充回归测试软件配置项信息表时发生错误", "regression_form_builder", e)
            return False


class RegressionFormBuilderWithPlanningService:
    """有策划表的回归测试表单构建服务"""
    
    def __init__(self):
        self.requirement_service = RegressionRequirementAnalysisService()
        self.issue_service = RegressionIssueReportService()
        self.software_config_service = RegressionSoftwareConfigService()
        self.project_info_service = RegressionProjectInfoService()
        self.project_plan_service = RegressionProjectPlanService()
    
    def ceshibiaodan_tianchong_have_cehua(self, file_path_wenjianjia: str, file_path_cehua: str, 
                                         zhuguan_name: str, ceshiren_name: str, kaifaren: str,
                                         ceshileixing: str, AI_fenx_flag_Anniu: int, 
                                         AI_deep_fenx_flag_Anniu: int, jianceyi_flag: str) -> int:
        """
        基于策划表的回归测试表单填充函数
        
        Args:
            file_path_wenjianjia: 文件夹路径
            file_path_cehua: 策划表路径
            zhuguan_name: 主管姓名
            ceshiren_name: 测试人员
            kaifaren: 开发人员
            ceshileixing: 测试类型
            AI_fenx_flag_Anniu: AI分析标志
            AI_deep_fenx_flag_Anniu: 深度分析标志
            jianceyi_flag: 检测仪标志
            
        Returns:
            int: 生成结果 (1表示成功，0表示失败)
        """
        try:
            log_info("开始基于策划表生成回归测试表单", "regression_form_builder_with_planning")
            
            # 1. 读取策划表内容获取关键信息
            log_info("读取策划表内容...", "regression_form_builder_with_planning")
            cehuabiao_data = self._read_planning_document(file_path_cehua)
            
            if not cehuabiao_data:
                log_error("策划表读取失败", "regression_form_builder_with_planning")
                return 0
            
            # 2. 从软件变更与影响分析报告中读取信息
            log_info("读取软件变更与影响分析报告...", "regression_form_builder_with_planning")
            software_info, document_info, requirement_changes, function_set = self._read_impact_analysis_report(
                file_path_wenjianjia
            )
            
            # 3. 验证数据完整性
            if not self._validate_required_data(software_info):
                log_error("软件信息不完整", "regression_form_builder_with_planning")
                return 0
            
            # 4. 生成各个表单
            sheet_names = {
                'requirement_analysis': '需求分析表',
                'test_case': '测试用例单',
                'issue_report': '问题报告单'
            }
            
            # 4.1 填充需求分析表
            log_info("填充需求分析表...", "regression_form_builder_with_planning")
            requirement_analysis_success = self._fill_requirement_analysis_with_planning(
                file_path_cehua, sheet_names['requirement_analysis'],
                software_info, cehuabiao_data, ceshiren_name, kaifaren, ceshileixing
            )
            
            if not requirement_analysis_success:
                log_error("需求分析表填充失败", "regression_form_builder_with_planning")
                return 0
            
            # 4.2 填充测试用例单
            log_info("填充测试用例单...", "regression_form_builder_with_planning")
            self._fill_test_case_with_planning(
                file_path_cehua, sheet_names['test_case'],
                software_info, cehuabiao_data, zhuguan_name, ceshiren_name, ceshileixing,
                requirement_changes, AI_deep_fenx_flag_Anniu, jianceyi_flag
            )
            
            # 4.3 填充问题报告单
            log_info("填充问题报告单...", "regression_form_builder_with_planning")
            self._fill_issue_report_with_planning(
                file_path_cehua, sheet_names['issue_report'],
                software_info, ceshiren_name, kaifaren, ceshileixing
            )
            
            log_info("基于策划表的回归测试表单生成完成", "regression_form_builder_with_planning")
            return 1
            
        except Exception as e:
            log_error(f"基于策划表的回归测试表单生成失败", "regression_form_builder_with_planning", e)
            return 0
    
    def _read_planning_document(self, file_path: str) -> Optional[Dict]:
        """读取策划表文档"""
        try:
            # 这里应该包含策划表读取逻辑
            # 回归测试的策划表可能包含特定的回归测试项
            return {
                'test_items': ['回归功能测试1', '回归功能测试2', '回归接口测试1', '回归性能测试'],
                'test_scope': '回归测试范围',
                'test_schedule': '回归测试计划',
                'test_resources': ['回归测试环境', '回归测试数据'],
                'change_points': ['变更点1', '变更点2', '变更点3']  # 回归测试特有的变更点
            }
        except Exception as e:
            log_error(f"读取策划表失败: {e}", "regression_form_builder_with_planning")
            return None
    
    def _read_impact_analysis_report(self, file_path: str) -> Tuple[Dict, Dict, Dict, List]:
        """读取软件变更与影响分析报告"""
        try:
            # 这里应该包含影响分析报告读取逻辑
            # 回归测试特别关注变更影响
            software_info = {
                '软件名称': '回归测试软件',
                '软件标识': 'REG-TEST-001',
                '被测软件版本': '1.1.0',  # 回归测试通常是新版本
                '基线版本': '1.0.0'      # 回归测试特有的基线版本
            }
            
            document_info = {
                '文档版本': '1.1',
                '文档日期': '2024-01-01',
                '变更记录': '版本变更记录'
            }
            
            requirement_changes = {
                '回归功能测试1': '功能A的修改验证',
                '回归功能测试2': '功能B的新增验证',
                '回归接口测试1': '接口C的变更验证',
                '回归性能测试': '性能影响验证'
            }
            
            function_set = ['changed_function1', 'changed_function2', 'new_function1']
            
            return software_info, document_info, requirement_changes, function_set
            
        except Exception as e:
            log_error(f"读取影响分析报告失败: {e}", "regression_form_builder_with_planning")
            return {}, {}, {}, []
    
    def _validate_required_data(self, software_info: Dict) -> bool:
        """验证必需的数据完整性"""
        required_fields = ['软件名称', '软件标识', '被测软件版本']
        
        for field in required_fields:
            if not software_info.get(field):
                log_warning(f"缺少必需字段: {field}", "regression_form_builder_with_planning")
                return False
        
        return True
    
    def _fill_requirement_analysis_with_planning(self, excel_file_path: str, sheet_name: str,
                                                software_info: Dict, cehuabiao_data: Dict, 
                                                ceshiren_name: str, kaifaren: str, ceshileixing: str):
        """基于策划表填充需求分析表"""
        try:
            log_info("填充回归测试需求分析表", "regression_form_builder_with_planning")
            
            # 构建需求数据结构
            ruanjian_name = software_info.get('软件名称', '回归测试软件')
            ruanjian_xinxi = {
                '软件名称': [ruanjian_name],
                '软件标识': [software_info.get('软件标识', 'REG')]
            }
            
            # 从策划表数据中提取需求信息
            requirement_changes = cehuabiao_data.get('requirement_changes', {})
            
            # 构建需求数据结构
            diama_biangeng_xuqiu = {}
            for req_id, req_info in requirement_changes.items():
                if isinstance(req_info, dict):
                    diama_biangeng_xuqiu[req_id] = req_info
                else:
                    diama_biangeng_xuqiu[req_id] = {
                        'name': req_id,
                        'description': str(req_info),
                        'software_name': ruanjian_name
                    }
            
            # 🚨 关键修复：提取实际的需求名称而不是REQ标识符
            actual_requirement_names = []
            for req_id, req_data in diama_biangeng_xuqiu.items():
                if isinstance(req_data, dict) and 'name' in req_data:
                    actual_requirement_names.append(req_data['name'])
                else:
                    actual_requirement_names.append(req_id)
            
            neirong_dict = []
            for req_data in diama_biangeng_xuqiu.values():
                if isinstance(req_data, dict):
                    neirong_dict.append(req_data.get('description', ''))
                else:
                    neirong_dict.append(str(req_data))
            
            # 调用需求分析service
            success = self.requirement_service.generate_requirement_analysis_table(
                excel_file_path=excel_file_path,
                sheet_name=sheet_name,
                ruanjian_xinxi=ruanjian_xinxi,
                ruanjian_name=ruanjian_name,
                diama_biangeng_xuqiu=diama_biangeng_xuqiu,
                file_path="",
                ceshileixing=ceshileixing,
                neirong_dict=neirong_dict,
                biaoshihao_ceshixianng=actual_requirement_names,  # 🚨 传递实际需求名称
                AI_fenx_flag_Anniu=1,
                jianceyi_flag=0
            )
            
            if success:
                log_info(f"回归测试需求分析表(策划表版本)填充成功: {sheet_name}", "regression_form_builder_with_planning")
            else:
                log_error(f"回归测试需求分析表(策划表版本)填充失败: {sheet_name}", "regression_form_builder_with_planning")
            
            return success
            
        except Exception as e:
            log_error(f"基于策划表填充回归测试需求分析表时发生错误: {e}", "regression_form_builder_with_planning", e)
            return False
    
    def _fill_test_case_with_planning(self, excel_file_path: str, sheet_name: str, 
                                     software_info: Dict, cehuabiao_data: Dict, 
                                     zhuguan_name: str, ceshiren_name: str, ceshileixing: str,
                                     requirement_changes: Dict, AI_deep_fenx_flag_Anniu: bool, jianceyi_flag: str):
        """基于策划表填充测试用例单 - 修正版本（使用完整的91列映射）"""
        try:
            log_debug(f"🔧 开始回归测试用例单填充", "regression_form_builder_with_planning")
            log_debug(f"文件路径: {excel_file_path}", "regression_form_builder_with_planning")
            log_debug(f"目标工作表: {sheet_name}", "regression_form_builder_with_planning")
            log_debug(f"需求变更数量: {len(requirement_changes)}", "regression_form_builder_with_planning")
            log_debug(f"AI深度分析标志: {AI_deep_fenx_flag_Anniu}", "regression_form_builder_with_planning")
            
            from openpyxl import load_workbook
            
            log_debug(f"正在加载Excel文件: {excel_file_path}", "regression_form_builder_with_planning")
            workbook = load_workbook(excel_file_path)
            
            log_debug(f"Excel文件包含的工作表: {workbook.sheetnames}", "regression_form_builder_with_planning")
            
            if sheet_name not in workbook.sheetnames:
                log_error(f"工作表 '{sheet_name}' 不存在，可用工作表: {workbook.sheetnames}", "regression_form_builder_with_planning")
                return False
                
            worksheet = workbook[sheet_name]
            log_debug(f"✅ 成功选择工作表: {sheet_name} ({worksheet.max_row}行, {worksheet.max_column}列)", "regression_form_builder_with_planning")
            
            # 🚨 检查工作表表头（调试用）
            log_debug("检查工作表表头（前30列）:", "regression_form_builder_with_planning")
            for col in range(1, min(31, worksheet.max_column + 1)):
                try:
                    header_value = worksheet.cell(row=1, column=col).value
                    if header_value:
                        col_letter = ""
                        if col <= 26:
                            col_letter = chr(64 + col)
                        else:
                            col_letter = "A" + chr(64 + col - 26)
                        log_debug(f"  {col_letter}({col}): {header_value}", "regression_form_builder_with_planning")
                except Exception as e:
                    log_debug(f"  列{col}: 读取失败 - {e}", "regression_form_builder_with_planning")
            
            # 准备测试数据
            ruanjian_name = software_info.get('software_name', '回归测试软件')
            ruanjian_version = software_info.get('software_version', 'V2.00')
            
            # 从需求变更中提取测试项
            allkeys = list(requirement_changes.keys())
            zhangjiehao = []
            ceshi_xuqiu_biaoshi = "RT-"  # 回归测试标识
            ruanjian_xuqiu_biaoshi = []
            leixing_biaoshi = "REG01"
            ceshileixing_temp = ceshileixing or "回归测试"
            
            # 从需求变更数据中提取更多信息
            for i, (req_id, req_data) in enumerate(requirement_changes.items()):
                if isinstance(req_data, dict):
                    # 提取章节号（如果存在）
                    chapter = req_data.get('chapter', f'R.{i+1}.{i+1}')
                    zhangjiehao.append(chapter)
                    ruanjian_xuqiu_biaoshi.append(f'REG{i+1:03d}')
            
            log_debug(f"准备的测试数据:", "regression_form_builder_with_planning")
            log_debug(f"  测试项列表: {allkeys}", "regression_form_builder_with_planning")
            log_debug(f"  软件名称: {ruanjian_name}", "regression_form_builder_with_planning")
            log_debug(f"  软件版本: {ruanjian_version}", "regression_form_builder_with_planning")
            log_debug(f"  章节号: {zhangjiehao}", "regression_form_builder_with_planning")
            
            # 🚨 修正版：正确处理AI返回的多个测试用例
            current_row = 2  # 从第2行开始（第1行是表头）
            total_test_cases_filled = 0
            
            for req_index, (req_id, req_data) in enumerate(requirement_changes.items()):
                log_debug(f"处理第{req_index+1}个需求变更: {req_id}", "regression_form_builder_with_planning")
                
                if isinstance(req_data, dict):
                    # 生成测试用例描述和方法
                    req_name = req_data.get('name', req_id)
                    req_desc = req_data.get('description', '')
                    
                    log_debug(f"  需求名称: {req_name}", "regression_form_builder_with_planning")
                    log_debug(f"  需求描述长度: {len(req_desc)}", "regression_form_builder_with_planning")
                    
                    # 🚨 关键修正：调用AI生成多个测试用例 (回归测试参数格式)
                    from ..test_case_generation.test_case_generator import generate_test_yongli
                    
                    test_result = generate_test_yongli(
                        ceshixiang_name=req_name,
                        requirement_description=req_desc,
                        test_content=req_desc,
                        ceshileixing=ceshileixing_temp,
                        jianceyi_flag=jianceyi_flag
                    )
                    
                    log_debug(f"  AI生成结果类型: {type(test_result)}", "regression_form_builder_with_planning")
                    
                    # 解析AI返回的测试用例数据
                    test_cases_list = []
                    if isinstance(test_result, tuple) and len(test_result) == 2:
                        success_flag, test_cases_data = test_result
                        log_debug(f"  生成成功标志: {success_flag}", "regression_form_builder_with_planning")
                        log_debug(f"  测试用例数据类型: {type(test_cases_data)}", "regression_form_builder_with_planning")
                        
                        if success_flag and isinstance(test_cases_data, list):
                            test_cases_list = test_cases_data
                            log_debug(f"  ✅ 获取到 {len(test_cases_list)} 个测试用例", "regression_form_builder_with_planning")
                        else:
                            log_debug(f"  ⚠️ AI生成失败或数据格式不正确，使用默认测试用例", "regression_form_builder_with_planning")
                            # 创建默认测试用例
                            test_cases_list = [[
                                f"{req_name}回归测试用例",
                                f"验证{req_name}回归功能实现是否正常", 
                                f"步骤1：启动测试环境；步骤2：回归测试{req_name}功能；步骤3：验证结果",
                                f"完成步骤1：测试环境正常；完成步骤2：{req_name}回归功能正常；完成步骤3：验证通过"
                            ]]
                    else:
                        log_debug(f"  ⚠️ 测试结果格式异常，使用默认测试用例", "regression_form_builder_with_planning")
                        # 创建默认测试用例
                        test_cases_list = [[
                            f"{req_name}回归测试用例",
                            f"验证{req_name}回归功能实现是否正常", 
                            f"步骤1：启动测试环境；步骤2：回归测试{req_name}功能；步骤3：验证结果",
                            f"完成步骤1：测试环境正常；完成步骤2：{req_name}回归功能正常；完成步骤3：验证通过"
                        ]]
                    
                    # 🚨 关键修正：为每个测试用例创建一行Excel数据
                    for case_index, test_case in enumerate(test_cases_list):
                        log_debug(f"    填充测试用例{case_index+1}: 行{current_row}", "regression_form_builder_with_planning")
                        
                        # 解析测试用例数据 [case_name, case_description, case_steps, case_expect]
                        if len(test_case) >= 4:
                            case_name = test_case[0] if test_case[0] else f"{req_name}回归测试用例{case_index+1}"
                            case_description = test_case[1] if test_case[1] else f"验证{req_name}回归功能"
                            case_steps = test_case[2] if test_case[2] else f"回归测试{req_name}的基本功能"
                            case_expect = test_case[3] if test_case[3] else f"{req_name}回归功能正常工作"
                        else:
                            log_debug(f"    ⚠️ 测试用例数据不完整: {test_case}", "regression_form_builder_with_planning")
                            case_name = f"{req_name}回归测试用例{case_index+1}"
                            case_description = f"验证{req_name}回归功能"
                            case_steps = f"回归测试{req_name}的基本功能"
                            case_expect = f"{req_name}回归功能正常工作"
                        
                        log_debug(f"    测试用例名称: {case_name}", "regression_form_builder_with_planning")
                        log_debug(f"    测试描述: {case_description[:50]}...", "regression_form_builder_with_planning")
                        log_debug(f"    输入条件长度: {len(case_steps)}", "regression_form_builder_with_planning")
                        log_debug(f"    预期结果长度: {len(case_expect)}", "regression_form_builder_with_planning")
                        
                        # 使用完整的91列填充函数
                        try:
                            # 🚨 修复：为了让每个测试用例都有正确的序号，扩展数组以避免索引越界
                            write_test_cases_to_excel(
                                sheet=worksheet,
                                row_xuhao=current_row,
                                index=total_test_cases_filled,  # 使用全局测试用例计数作为序号
                                allkeys=[case_name] * (total_test_cases_filled + 1),  # 🚨 扩展数组以避免索引越界
                                ruanjian_name=ruanjian_name,
                                ruanjian_version=ruanjian_version,
                                zhangjiehao=[zhangjiehao[req_index] if req_index < len(zhangjiehao) else f'R.{req_index+1}.{case_index+1}'] * (total_test_cases_filled + 1),
                                ceshi_xuqiu_biaoshi=ceshi_xuqiu_biaoshi,
                                ruanjian_xuqiu_biaoshi=[f'REG{req_index+1:03d}-{case_index+1:02d}'] * (total_test_cases_filled + 1),
                                leixing_biaoshi=leixing_biaoshi,
                                ceshileixing_temp=ceshileixing_temp,
                                ceshixiang_miaoshu=case_description,  # 使用AI生成的描述
                                ceshixiang_fangfa=f"通过检测仪进行{req_name}回归测试",
                                ceshi_yongli=case_steps,  # 使用AI生成的测试步骤
                                ceshi_yonglisheji=case_expect,  # 使用AI生成的预期结果
                                ceshiren_name=ceshiren_name,
                                zhuguan_name=zhuguan_name,
                                temp_temp_count=case_index + 1  # 用例编号
                            )
                            log_debug(f"    ✅ 成功填充行{current_row}的完整数据（91列）", "regression_form_builder_with_planning")
                            current_row += 1
                            total_test_cases_filled += 1
                        except Exception as fill_error:
                            log_error(f"    ❌ 填充行{current_row}时出错: {fill_error}", "regression_form_builder_with_planning")
                            log_debug(f"    错误详情: {str(fill_error)}", "regression_form_builder_with_planning")
                            current_row += 1  # 即使失败也要移动到下一行
                else:
                    log_debug(f"  跳过非字典类型的需求数据: {type(req_data)}", "regression_form_builder_with_planning")
            
            log_debug(f"保存修正版Excel文件", "regression_form_builder_with_planning")
            workbook.save(excel_file_path)
            
            log_info(f"修正版回归测试用例单填充成功: {sheet_name}", "regression_form_builder_with_planning")
            log_debug(f"📊 修正版填充总结:", "regression_form_builder_with_planning")
            log_debug(f"  - 原始需求变更数量: {len(requirement_changes)}", "regression_form_builder_with_planning")
            log_debug(f"  - 实际填充的测试用例数量: {total_test_cases_filled}", "regression_form_builder_with_planning")
            log_debug(f"  - 最后填充的行号: {current_row - 1}", "regression_form_builder_with_planning")
            log_debug(f"  - 使用的工作表: {sheet_name}", "regression_form_builder_with_planning")
            log_debug(f"  - 填充方式: 完整91列映射", "regression_form_builder_with_planning")
            log_debug(f"  - 使用函数: write_test_cases_to_excel", "regression_form_builder_with_planning")
            log_debug(f"  - AI生成模式: 每个需求变更可生成多个测试用例", "regression_form_builder_with_planning")
            
            return True
            
        except Exception as e:
            log_error(f"修正版回归测试用例单填充失败", "regression_form_builder_with_planning", e)
            log_debug(f"错误详情: {str(e)}", "regression_form_builder_with_planning")
            import traceback
            log_debug(f"错误堆栈: {traceback.format_exc()}", "regression_form_builder_with_planning")
            return False
    
    def _fill_issue_report_with_planning(self, excel_file_path: str, sheet_name: str, *args):
        """基于策划表填充问题报告单"""
        # 调用问题报告service的策划表版本
        log_info("填充回归测试问题报告单", "regression_form_builder_with_planning")
        # 这里会调用具体的填充逻辑
        pass 