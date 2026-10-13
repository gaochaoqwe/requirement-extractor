#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表格填充服务

用于处理需求分析相关的Excel表格填充任务
重新设计版本，结构清晰，语法正确
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

# 核心工具导入
from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 服务导入
from ..requirement_analysis import ConfigurationItemRequirementAnalysisService as RequirementAnalysisService
from ..software_config import SoftwareConfigService
from ..project_info import ProjectInfoService
from ..project_plan import ConfigurationItemProjectPlanService

# 导入现有的优化数据库模型
from ...db.optimized_models import OptimizedDynamicTestDatabase
from ...db.database_service import get_database_service

# 导入工具模块
from .form_utils import (
    extract_requirements_from_catalog,
    read_first_two_rows_as_dict,
    update_software_info_with_user_data,
    extract_software_name,
    validate_word_document
)

# 导入表格填充器
from .table_fillers.test_case_table_filler import TestCaseTableFiller
from .table_fillers.issue_report_table_filler import IssueReportTableFiller
from .table_fillers.software_config_table_filler import SoftwareConfigTableFiller
from .table_fillers.project_info_table_filler import ProjectInfoTableFiller
from .table_fillers.project_plan_table_filler import ProjectPlanTableFiller

# 导入测试用例服务（回退方案使用）
from ..test_case_generation.test_case_service import TestCaseService
# 导入实时测试用例生成服务
from ..test_case_generation.realtime_test_case_service import RealtimeTestCaseService


class FormBuilderService:
    """表格构建服务"""
    
    def __init__(self):
        """初始化服务"""
        # log_info("初始化FormBuilderService", "form_builder_service")
        
        # 初始化各个服务
        self.requirement_service = RequirementAnalysisService()
        self.software_config_service = SoftwareConfigService()
        self.project_info_service = ProjectInfoService()
        self.project_plan_service = ConfigurationItemProjectPlanService()
        
        # 初始化表格填充器
        self.test_case_filler = TestCaseTableFiller()
        
        # 初始化测试用例服务（回退方案）
        self.test_case_service = TestCaseService()
        # 初始化实时测试用例生成服务
        self.realtime_service = RealtimeTestCaseService()
        
        # 初始化 issue_service
        from ..issue_report import ConfigurationItemIssueReportService
        issue_service = ConfigurationItemIssueReportService()
        self.issue_report_filler = IssueReportTableFiller(issue_service=issue_service)
        
        self.software_config_filler = SoftwareConfigTableFiller(software_config_service=self.software_config_service)
        self.project_info_filler = ProjectInfoTableFiller(project_info_service=self.project_info_service)
        self.project_plan_filler = ProjectPlanTableFiller(project_plan_service=self.project_plan_service)
        
        # 数据库集成服务
        self.db_service = get_database_service() if get_database_service else None
        
        # 使用现有的优化数据库
        self.optimized_db = None
        try:
            self.optimized_db = OptimizedDynamicTestDatabase()
            # log_info("优化数据库服务初始化成功", "form_builder_service")
        except Exception as e:
            # log_warning(f"优化数据库服务初始化失败: {e}", "form_builder_service")
            pass
    
    def ceshibiaodan_tianchong(self, file_path_xuqiu_word: str, file_path_mulu_word: str, zhuguan_name: str, 
                              ceshiren_name: str, kaifarenxinxi: List[str], ceshileixing: str,
                              AI_fenx_flag_Anniu: bool, AI_deep_fenx_flag_Anniu: bool, 
                              suoshulingyu: str, jianceyi_flag: str, resource_manager,
                              user_software_info: Dict[str, str] = None, code_lines: int = None,
                              session_id: str = None, task_id: str = None, progress_callback: callable = None) -> int:
        """
        主要的表单填充方法
        
        Args:
            file_path_xuqiu_word: 需求文档路径
            file_path_mulu_word: 目录文档路径
            zhuguan_name: 主管姓名
            ceshiren_name: 测试人员姓名
            kaifarenxinxi: 开发人员信息列表
            ceshileixing: 测试类型
            AI_fenx_flag_Anniu: AI分析开关
            AI_deep_fenx_flag_Anniu: AI深度分析开关
            suoshulingyu: 所属领域
            jianceyi_flag: 检测仪标志
            resource_manager: 资源管理器
            user_software_info: 用户软件信息
            code_lines: 代码行数
            session_id: 会话ID
            task_id: 任务ID
            progress_callback: 进度回调函数
            
        Returns:
            int: 成功填充的表格数量
        """
        try:
            # log_info("开始表单填充流程", "form_builder_service")
            
            if progress_callback:
                progress_callback(5, "正在初始化任务...")
            
            # 1. 初始化任务 - 如果传入了task_id就直接使用，否则创建新的
            # 🔧 修复：无论是否有外部task_id，都需要初始化AI开关控制器
            if task_id:
                # log_info(f"[DB] 使用外部传入的task_id: {task_id}", "form_builder_service")
                # 🔧 修复：使用外部task_id用于数据库存储，而不是设置为None
                db_task_id = task_id  # 使用外部task_id进行数据库存储
                
                # 🔧 新增：为外部task_id在数据库中创建任务记录
                if self.db_service:
                    final_session_id = (session_id or 
                                      (user_software_info.get('session_id') if user_software_info else None) or
                                      getattr(resource_manager, 'session_id', None) or
                                      'default_session')
                    # log_info(f"[DB] 为外部task_id注册任务记录，session_id: {final_session_id}", "form_builder_service")
                    self.db_service.register_existing_task(task_id, final_session_id, 'form_generation')
                
                # 但仍需要初始化AI开关控制器
                try:
                    from ...utils.ai_switch_controller.ai_switch_controller import init_ai_controller
                    ai_controller = init_ai_controller(global_ai_enabled=AI_fenx_flag_Anniu)
                    # log_info(f"AI开关控制器已初始化 - 全局AI状态: {AI_fenx_flag_Anniu}", "form_builder_service")
                except Exception as e:
                    # log_warning(f"AI开关控制器初始化失败: {e}", "form_builder_service")
                    pass
            else:
                db_task_id = self._initialize_task(AI_fenx_flag_Anniu, user_software_info, resource_manager, session_id)
            
            if progress_callback:
                progress_callback(10, "正在验证输入文档...")
            
            # 2. 验证输入文档
            if not self._validate_input_documents(file_path_xuqiu_word, file_path_mulu_word):
                return 0
            
            if progress_callback:
                progress_callback(20, "正在提取和准备数据...")
            
            # 3. 提取和准备数据
            data = self._extract_and_prepare_data(
                file_path_xuqiu_word, file_path_mulu_word, user_software_info,
                code_lines, session_id
            )
            if not data:
                return 0
            
            if progress_callback:
                progress_callback(35, "正在准备Excel模板...")
            
            # 4. 准备Excel模板
            excel_file_path = self._prepare_excel_template(file_path_xuqiu_word, resource_manager)
            if not excel_file_path:
                return 0
            
            if progress_callback:
                progress_callback(45, "正在填充表格...")
            
            # 5. 填充各个表格
            success_count = self._fill_all_tables(
                excel_file_path, data, zhuguan_name, ceshiren_name,
                kaifarenxinxi, suoshulingyu, AI_fenx_flag_Anniu,
                AI_deep_fenx_flag_Anniu, jianceyi_flag, user_software_info,
                db_task_id, progress_callback
            )
            
            if progress_callback:
                progress_callback(95, "正在完成任务...")
            
            # 6. 完成任务
            if self.db_service and db_task_id:
                self.db_service.complete_task(db_task_id)
            
            # log_info(f"表单生成完成，成功填充 {success_count}/6 个表格", "form_builder_service")
            
            if progress_callback:
                progress_callback(100, "表单生成完成！")
            
            # 返回成功（如果至少填充了主要表格）
            return 1 if success_count >= 2 else 0
            
        except Exception as e:
            # log_error(f"表单生成过程中发生错误", "form_builder_service", e)
            if self.db_service and 'db_task_id' in locals() and db_task_id:
                self.db_service.fail_task(db_task_id, str(e))
            return 0
    
    def _initialize_task(self, AI_fenx_flag_Anniu: bool, user_software_info: Dict, 
                        resource_manager, session_id: str) -> Optional[str]:
        """初始化任务"""
        try:
            # 初始化AI开关控制器
            from ...utils.ai_switch_controller.ai_switch_controller import init_ai_controller
            ai_controller = init_ai_controller(global_ai_enabled=AI_fenx_flag_Anniu)
            # log_info(f"AI开关控制器已初始化 - 全局AI状态: {AI_fenx_flag_Anniu}", "form_builder_service")
        except Exception as e:
            # log_warning(f"AI开关控制器初始化失败: {e}", "form_builder_service")
        
            pass
        # 创建数据库任务
        task_id = None
        if self.db_service:
            # 优先使用传入的session_id，然后从user_software_info或resource_manager获取
            final_session_id = (session_id or 
                               (user_software_info.get('session_id') if user_software_info else None) or
                               getattr(resource_manager, 'session_id', None) or
                               'default_session')
            # log_info(f"[DB] 使用session_id: {final_session_id}", "form_builder_service")
            task_id = self.db_service.start_task(final_session_id, 'form_generation')
            # log_info(f"[DB] 创建数据库任务: {task_id}", "form_builder_service")
            
        return task_id
    
    def _validate_input_documents(self, file_path_xuqiu_word: str, file_path_mulu_word: str) -> bool:
        """验证输入文档"""
        # 验证需求文档
        is_valid, message = validate_word_document(file_path_xuqiu_word)
        if not is_valid:
            # log_error(f"需求文档验证失败: {message}", "form_builder_service")
            return False
        
        # 验证目录文档
        is_valid, message = validate_word_document(file_path_mulu_word)
        if not is_valid:
            # log_error(f"目录文档验证失败: {message}", "form_builder_service")
            return False
        
        return True
    
    def _extract_and_prepare_data(self, file_path_xuqiu_word: str, file_path_mulu_word: str,
                                 user_software_info: Dict, code_lines: int, session_id: str) -> Optional[Dict]:
        """提取和准备数据"""
        # 1. 从需求目录文档中提取需求条目
        # log_info("开始从需求目录文档中提取需求条目...", "form_builder_service")
        requirements_dict = extract_requirements_from_catalog(file_path_mulu_word, file_path_xuqiu_word, session_id)
        
        if not requirements_dict:
            # log_error("未能提取到任何需求条目", "form_builder_service")
            return None
        
        # 2. 从需求规格说明文档中提取软件信息
        # log_info("从需求规格说明文档中提取软件信息...", "form_builder_service")
        ruanjian_xinxi_duqu_temp = read_first_two_rows_as_dict(file_path_xuqiu_word)
        
        # 使用用户提供的软件信息覆盖文档中的信息
        if user_software_info:
            update_software_info_with_user_data(ruanjian_xinxi_duqu_temp, user_software_info)
        
        # 3. 准备最终数据
        ruanjian_name = extract_software_name(ruanjian_xinxi_duqu_temp, user_software_info)
        
        # 4. 生成最终需求描述
        final_xuqiu_mioashu = {key: {'name': key, 'description': value} 
                              for key, value in requirements_dict.items()}
        
        total_lines = code_lines if code_lines else 1000
        
        return {
            'requirements_dict': requirements_dict,
            'ruanjian_xinxi_duqu_temp': ruanjian_xinxi_duqu_temp,
            'ruanjian_name': ruanjian_name,
            'final_xuqiu_mioashu': final_xuqiu_mioashu,
            'total_lines': total_lines,
            'file_path_mulu_word': file_path_mulu_word
        }
    
    def _generate_default_xinghao_list(self, data: Dict, user_software_info: Dict) -> List[Dict]:
        """生成默认的软件型号信息列表"""
        try:
            return [{
                'software_name': data.get('ruanjian_name', ''),
                'software_version': user_software_info.get('software_version', '1.0.0'),
                'software_id': user_software_info.get('software_id', ''),
                'description': f"{data.get('ruanjian_name', '')}软件配置项"
            }]
        except Exception as e:
            # log_warning(f"生成默认型号列表失败: {e}", "form_builder_service")
            return []
    
    def _extract_requirement_analysis_data_from_excel(self, excel_file_path: str, sheet_name: str) -> Optional[Dict]:
        """从Excel文件中提取需求分析数据"""
        try:
            # log_info(f"从Excel提取需求分析数据: {excel_file_path}, 工作表: {sheet_name}", "form_builder_service")
            
            # 使用需求分析服务读取数据
            data, status = self.requirement_service.read_requirement_analysis_data(excel_file_path, sheet_name)
            
            if data:
                # log_info(f"成功提取需求分析数据，包含 {len(data.get('test_items', []))} 个测试项", "form_builder_service")
                return data
            else:
                # log_warning(f"提取需求分析数据失败: {status}", "form_builder_service")
                return None
                
        except Exception as e:
            # log_error(f"从Excel提取需求分析数据时发生错误: {str(e)}", "form_builder_service")
            return None
    
    def _prepare_excel_template(self, file_path_xuqiu_word: str, resource_manager) -> Optional[str]:
        """准备Excel模板（增强版，包含文件完整性检查）"""
        try:
            template_file = resource_manager.get_template_path('需求分析表(精准测试工具生成).xlsx')
            output_dir = Path(file_path_xuqiu_word).parent / 'output'
            output_dir.mkdir(exist_ok=True)
            
            excel_file_path = output_dir / '需求分析表(精准测试工具生成).xlsx'
            
            # 🔧 增强：检查模板文件是否存在和完整
            if not os.path.exists(template_file):
                # log_error(f"模板文件不存在: {template_file}", "form_builder_service")
                return None
            
            template_size = os.path.getsize(template_file)
            if template_size < 1024:  # 模板文件太小，可能损坏
                # log_error(f"模板文件可能损坏，大小异常: {template_size} bytes", "form_builder_service")
                return None
            
            # 复制模板文件
            shutil.copy2(template_file, excel_file_path)
            
            # 🔧 增强：验证复制后的文件完整性
            if os.path.exists(excel_file_path):
                copied_size = os.path.getsize(excel_file_path)
                if copied_size == template_size:
                    # 尝试用openpyxl打开验证文件格式
                    try:
                        import openpyxl
                        test_wb = openpyxl.load_workbook(excel_file_path)
                        test_wb.close()
                        # log_info(f"Excel模板准备成功并验证完整: {excel_file_path}", "form_builder_service")
                        return str(excel_file_path)
                    except Exception as validation_error:
                        # log_error(f"Excel文件格式验证失败: {validation_error}", "form_builder_service")
                        return None
                else:
                    # log_error(f"文件复制不完整: 原文件{template_size}字节, 目标文件{copied_size}字节", "form_builder_service")
                    return None
            else:
                # log_error(f"文件复制失败，目标文件不存在: {excel_file_path}", "form_builder_service")
                return None
                
        except Exception as e:
            # log_error(f"准备Excel模板失败: {e}", "form_builder_service")
            return None
    
    def _fill_all_tables(self, excel_file_path: str, data: Dict, zhuguan_name: str, ceshiren_name: str,
                        kaifarenxinxi: List[str], suoshulingyu: str, AI_fenx_flag_Anniu: bool,
                        AI_deep_fenx_flag_Anniu: bool, jianceyi_flag: str,
                        user_software_info: Dict, db_task_id: str = None, 
                        progress_callback: callable = None) -> int:
        """填充所有表格"""
        sheet_names = {
            'requirement_analysis': '需求分析表',
            'test_case': '测试用例单', 
            'issue_report': '问题报告单',
            'software_config': '软件配置项信息',
            'project_info': '项目基本信息',
            'project_plan': '项目策划表'
        }
        
        success_count = 0
        xinghao_xinxi_list = None
        
        # 1. 填充需求分析表
        # log_info("开始填充需求分析表...", "form_builder_service")
        if progress_callback:
            progress_callback(50, "正在填充需求分析表...")
        if self.requirement_service.fill_requirement_analysis_table_for_form_builder(
            excel_file_path, sheet_names['requirement_analysis'],
            data['final_xuqiu_mioashu'], data['ruanjian_name'], data['total_lines'],
            AI_fenx_flag_Anniu, AI_deep_fenx_flag_Anniu, data['file_path_mulu_word'],
            user_software_info,
            task_id=db_task_id,  # 🔧 新增：传递task_id用于数据库存储
            product_type=user_software_info.get('product_type') if user_software_info else None  # 🔧 新增：传递产品类型
        ):
            success_count += 1
            # log_info("需求分析表填充成功", "form_builder_service")
        else:
            # log_error("需求分析表填充失败", "form_builder_service")
            
            # 存储需求分析核心数据到数据库
            # log_info(f"检查数据库存储条件: optimized_db={bool(self.optimized_db)}, db_task_id={db_task_id}", "form_builder_service")
            if self.optimized_db and db_task_id:
                # log_info("开始存储需求分析数据到数据库", "form_builder_service")
                # 🔧 新方法：直接从已生成的Excel文件中提取完整数据存储到数据库
                try:
                    from ..requirement_analysis import ConfigurationItemRequirementAnalysisService
                    requirement_analysis_service = ConfigurationItemRequirementAnalysisService()
                    
                    # 使用新的Excel数据提取方法
                    success = requirement_analysis_service.extract_and_store_excel_data_to_db(
                        excel_file_path=excel_file_path,
                        sheet_name=sheet_names['requirement_analysis'],
                        task_id=db_task_id
                    )
                    if success:
                        # log_info("成功从Excel提取并存储需求分析数据到数据库", "form_builder_service")
                        pass
                    else:
                        # log_warning("从Excel提取需求分析数据失败，使用备用方法", "form_builder_service")
                        # 备用方法：使用原有逻辑
                        self._store_requirement_analysis_to_db_legacy(db_task_id, data['final_xuqiu_mioashu'], data['ruanjian_name'], user_software_info)
                except Exception as e:
                    # log_warning(f"新的Excel数据提取方法失败: {e}，使用备用方法", "form_builder_service")
                    # 备用方法：使用原有逻辑
                    self._store_requirement_analysis_to_db_legacy(db_task_id, data['final_xuqiu_mioashu'], data['ruanjian_name'], user_software_info)
            else:
                # log_warning(f"跳过数据库存储: optimized_db={bool(self.optimized_db)}, db_task_id={db_task_id}", "form_builder_service")
                # 读取需求分析表数据，用于后续表格填充
                pass
        # 🔧 修复：从数据库获取需求分析数据，包含测试项信息
        requirement_analysis_excel_data = None
        if db_task_id:
            log_info(f"🔍 尝试从数据库获取需求分析数据，task_id: {db_task_id}", "form_builder_service")
            requirement_analysis_excel_data = self._get_requirement_analysis_from_db(db_task_id)
            if requirement_analysis_excel_data:
                test_items_count = len(requirement_analysis_excel_data.get('test_items', []))
                log_info(f"✅ 成功从数据库获取需求分析数据，包含 {test_items_count} 个测试项", "form_builder_service")
                if test_items_count > 0:
                    first_item = requirement_analysis_excel_data['test_items'][0]
                    log_info(f"📋 第一个测试项示例: {first_item.get('name', 'N/A')}", "form_builder_service")
                else:
                    log_error("❌ 数据库中的需求分析数据为空！", "form_builder_service")
                # 2. 实时生成测试用例并直接入库（替代旧的Excel填充与抽取流程）
                if progress_callback:
                    progress_callback(65, "正在实时生成测试用例并入库...")

                total_saved_cases = 0
                try:
                    test_items = requirement_analysis_excel_data.get('test_items', [])
                    for idx, item in enumerate(test_items, start=1):
                        requirement_name = item.get('name') or item.get('test_item_name') or ''
                        requirement_desc = item.get('requirement_description', '')
                        requirement_sub_desc = item.get('requirement_sub_description', requirement_desc)
                        description_items_raw = item.get('test_description', '')
                        method_items_raw = item.get('test_method', '')
                        test_type_val = item.get('test_type', '功能测试')
                        test_item_identifier = item.get('test_item_identifier', '')
                        requirement_trace = item.get('software_requirement_trace', '')

                        if not description_items_raw:
                            log_warning(f"跳过无测试描述的测试项: {requirement_name}", "form_builder_service")
                            continue

                        # 🔧 修复：正确解析测试描述中的多个条目
                        # 将测试描述按行分割，每行是一个测试条目
                        description_lines = [line.strip() for line in description_items_raw.split('\n') if line.strip()]
                        method_lines = [line.strip() for line in method_items_raw.split('\n') if line.strip()]
                        
                        log_info(f"[ITEM_PARSE] 测试项 '{requirement_name}' 解析到 {len(description_lines)} 条测试描述", "form_builder_service")
                        log_info(f"[ITEM_PARSE] 测试项 '{requirement_name}' 解析到 {len(method_lines)} 条测试方法", "form_builder_service")

                        # 🔧 修复：为每个测试条目单独匹配数据库并生成用例
                        product_type = user_software_info.get('product_type') if user_software_info else None
                        
                        # 🔧 新增：为当前测试项维护累计的用例编号计数器
                        current_case_sequence = 1
                        
                        # 为每个测试条目生成用例
                        for i, desc_line in enumerate(description_lines):
                            log_info(f"[SEQUENCE_DEBUG] 处理第{i+1}条测试内容: '{desc_line[:50]}...', current_case_sequence={current_case_sequence}", "form_builder_service")
                            method_line = method_lines[i] if i < len(method_lines) else (method_lines[-1] if method_lines else '')
                            
                            # 尝试为当前条目匹配数据库模板
                            db_template_input = None
                            db_template_expected = None
                            is_db_matched = False
                            
                            if product_type:
                                try:
                                    from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.content_generators.asset_database_enhancer import AssetDatabaseEnhancer
                                    enhancer = AssetDatabaseEnhancer()
                                    
                                    # 为当前条目查找匹配的数据库模板
                                    db_template_name, db_template_input, db_template_expected, is_db_matched = enhancer.get_matched_templates_for_test_case(
                                        test_description=desc_line,  # 使用具体的测试条目内容进行匹配
                                        product_type=product_type
                                    )
                                    
                                    if is_db_matched:
                                        log_info(f"[DATABASE_MATCH] ✅ 条目 '{desc_line[:50]}...' 匹配到数据库模板", "form_builder_service")
                                    else:
                                        log_info(f"[DATABASE_MATCH] ❌ 条目 '{desc_line[:50]}...' 未匹配到数据库模板", "form_builder_service")
                                        
                                except Exception as e:
                                    log_error(f"[DATABASE_MATCH] 条目数据库匹配失败: {e}", "form_builder_service")
                            
                            # 生成测试用例
                            # 🔧 修复：使用累计的用例编号，确保每个测试项内的用例编号连续
                            log_info(f"[SEQUENCE_DEBUG] 即将调用generate_and_save_cases: start_sequence={current_case_sequence}", "form_builder_service")
                            
                            res = self.realtime_service.generate_and_save_cases(
                                task_id=db_task_id,
                                requirement_name=requirement_name,  # 🔧 修复：使用原始测试项名称
                                requirement_desc=requirement_desc,
                                test_method=method_line,
                                test_description=desc_line,
                                test_type=test_type_val,
                                detector_flag=jianceyi_flag,
                                software_item_name=data.get('ruanjian_name', ''),
                                software_version=(user_software_info.get('software_version') if user_software_info else None),
                                test_item_identifier=test_item_identifier,
                                requirement_traceability=requirement_trace,
                                start_sequence=current_case_sequence,  # 🔧 修复：使用累计编号
                                ceshiren_name=ceshiren_name,
                                zhuguan_name=zhuguan_name,
                                database_template_name=db_template_name,
                                database_template_input=db_template_input,
                                database_template_expected=db_template_expected,
                                is_database_matched=is_db_matched
                            )
                            
                            log_info(f"[SEQUENCE_DEBUG] generate_and_save_cases返回结果: success={res.get('success') if res else False}, actual_case_count={res.get('actual_case_count', 'N/A') if res else 'N/A'}", "form_builder_service")
                            
                            if res and res.get('success'):
                                total_saved_cases += int(res.get('saved_count') or 0)
                                # 🔧 新增：更新累计编号，加上实际生成的用例数量
                                actual_case_count = res.get('actual_case_count', 1)
                                log_info(f"[SEQUENCE_DEBUG] 更新前: current_case_sequence={current_case_sequence}, actual_case_count={actual_case_count}", "form_builder_service")
                                current_case_sequence += actual_case_count
                                log_info(f"[SEQUENCE_DEBUG] 更新后: current_case_sequence={current_case_sequence}", "form_builder_service")
                                
                                template_type = "数据库模板" if is_db_matched else "AI生成"
                                log_info(f"[CASE_GEN] ✅ {template_type}用例生成成功: {requirement_name}, 生成{actual_case_count}个用例, 下次起始编号: {current_case_sequence}", "form_builder_service")
                            else:
                                log_warning(f"[CASE_GEN] ❌ 用例生成失败: {requirement_name}", "form_builder_service")
                                # 🔧 修复：即使失败也要更新编号，避免编号冲突
                                current_case_sequence += 1
                                log_info(f"[SEQUENCE_DEBUG] 失败情况下更新编号: current_case_sequence={current_case_sequence}", "form_builder_service")

                    if total_saved_cases > 0:
                        success_count += 1
                        log_info(f"✅ 实时生成并入库测试用例完成，共保存 {total_saved_cases} 条", "form_builder_service")
                        
                        # 🔧 新增：将数据库中的测试用例数据填充到Excel测试用例单
                        if progress_callback:
                            progress_callback(70, "正在将测试用例数据填充到Excel...")
                        
                        try:
                            log_info(f"📝 开始将数据库中的测试用例数据填充到Excel测试用例单", "form_builder_service")
                            
                            # 从数据库获取测试用例数据
                            from ...db.optimized_models import OptimizedDynamicTestDatabase
                            db = OptimizedDynamicTestDatabase()
                            test_cases_from_db = db.get_test_cases_by_task(db_task_id)
                            
                            log_info(f"📊 从数据库获取到 {len(test_cases_from_db)} 条测试用例数据", "form_builder_service")
                            
                            if test_cases_from_db:
                                # 使用excel_io.writer模块将测试用例写入Excel
                                from ..test_case_generation.excel_io.writer import write_realtime_cases_to_excel
                                
                                log_info(f"📝 开始写入测试用例到Excel文件: {excel_file_path}", "form_builder_service")
                                log_info(f"📝 目标工作表: {sheet_names['test_case']}", "form_builder_service")
                                log_info(f"📝 测试用例数据示例: {test_cases_from_db[0] if test_cases_from_db else 'None'}", "form_builder_service")
                                
                                write_success = write_realtime_cases_to_excel(
                                    test_cases=test_cases_from_db,
                                    excel_path=excel_file_path,
                                    sheet_name=sheet_names['test_case']
                                )
                                
                                if write_success:
                                    log_info(f"✅ 成功将 {len(test_cases_from_db)} 条测试用例写入Excel测试用例单", "form_builder_service")
                                else:
                                    log_error(f"❌ 写入测试用例到Excel失败", "form_builder_service")
                            else:
                                log_warning(f"⚠️ 数据库中没有找到测试用例数据 (task_id: {db_task_id})", "form_builder_service")
                                
                        except Exception as excel_write_error:
                            log_error(f"❌ 填充测试用例到Excel时发生异常: {excel_write_error}", "form_builder_service")
                            import traceback
                            log_error(f"❌ 异常详情: {traceback.format_exc()}", "form_builder_service")
                    else:
                        log_warning("⚠️ 实时生成阶段未保存任何测试用例", "form_builder_service")
                except Exception as e:
                    log_error(f"实时生成测试用例阶段异常: {e}", "form_builder_service")
            else:
                log_error("❌ 从数据库获取需求分析数据失败！", "form_builder_service")
        else:
            log_error("❌ 没有提供 db_task_id，无法从数据库获取数据", "form_builder_service")
        
            pass
        
        
        # 填充问题报告单
        if progress_callback:
            progress_callback(75, "正在填充问题报告单...")
        if self.issue_report_filler.fill_issue_report_table(
            excel_file_path,
            sheet_names['issue_report'],
            data['ruanjian_xinxi_duqu_temp'],
            data['ruanjian_name'],
            zhuguan_name,
            ceshiren_name,
            kaifarenxinxi,
            user_software_info
        ):
            success_count += 1
            # log_info("问题报告单填充成功", "form_builder_service")
        
        # log_info("开始填充软件配置项信息表...", "form_builder_service")
        if progress_callback:
            progress_callback(80, "正在填充软件配置项信息表...")
        # 生成软件型号信息列表（创建默认列表）
        xinghao_xinxi_list = self._generate_default_xinghao_list(data, user_software_info)
        
        if self.software_config_filler.fill_software_config_table(
            excel_file_path, 
            sheet_names['software_config'], 
            data['ruanjian_xinxi_duqu_temp'], 
            data['ruanjian_name'], 
            kaifarenxinxi,
            suoshulingyu, 
            xinghao_xinxi_list,
            zhuguan_name,
            ceshiren_name,
            user_software_info
        ):
            success_count += 1
            # log_info("软件配置项信息表填充成功", "form_builder_service")
            
            # 🔧 新增：存储软件配置数据到数据库
            if self.optimized_db and db_task_id:
                # log_info("开始存储软件配置数据到数据库", "form_builder_service")
                try:
                    # 准备软件配置数据
                    config_data = {
                        'software_name': data['ruanjian_name'],
                        'software_version': user_software_info.get('software_version', '1.0.0') if user_software_info else '1.0.0',
                        'software_identifier': user_software_info.get('software_id', '') if user_software_info else '',
                        'development_department': kaifarenxinxi[1] if len(kaifarenxinxi) > 1 else '',
                        'programming_language': user_software_info.get('programming_language', 'C/C++') if user_software_info else 'C/C++',
                        'development_environment': user_software_info.get('development_environment', 'Visual Studio') if user_software_info else 'Visual Studio',
                        'runtime_environment': user_software_info.get('runtime_environment', 'Windows') if user_software_info else 'Windows',
                        'software_level': user_software_info.get('software_level', 'C级') if user_software_info else 'C级'
                    }
                    
                    # 使用数据库服务存储
                    self.db_service.store_software_config_data(db_task_id, config_data)
                    # log_info(f"[DB] 软件配置数据成功存储到数据库，task_id: {db_task_id}", "form_builder_service")
                    
                except Exception as db_e:
                    # log_error(f"[DB] 存储软件配置数据到数据库时发生错误: {str(db_e)}", "form_builder_service")
                    pass
            else:
                # log_info("[DB] 跳过软件配置数据库存储（未提供task_id或数据库服务）", "form_builder_service")
        
                pass
        # log_info("开始填充项目基本信息表...", "form_builder_service")
        if progress_callback:
            progress_callback(85, "正在填充项目基本信息表...")
        if self.project_info_filler.fill_project_info_table(
            excel_file_path, 
            sheet_names['project_info'], 
            data['ruanjian_xinxi_duqu_temp'], 
            data['ruanjian_name'],
            zhuguan_name, 
            ceshiren_name,
            kaifarenxinxi, 
            xinghao_xinxi_list,
            user_software_info
        ):
            success_count += 1
            # log_info("项目基本信息表填充成功", "form_builder_service")
            
            # 🔧 新增：存储项目信息数据到数据库
            if self.optimized_db and db_task_id:
                # log_info("开始存储项目信息数据到数据库", "form_builder_service")
                try:
                    # 准备基本信息，合并所有数据源
                    basic_info = {
                        'software_name': data['ruanjian_name'],
                        'software_version': user_software_info.get('software_version', '1.0.0') if user_software_info else '1.0.0',
                        'software_id': user_software_info.get('software_id', '') if user_software_info else '',
                        'domain': user_software_info.get('domain', suoshulingyu) if user_software_info else suoshulingyu,
                        'aircraft_model': user_software_info.get('aircraft_model', '') if user_software_info else '',
                        'project_director': user_software_info.get('project_director', '') if user_software_info else '',
                        'development_department': user_software_info.get('development_department', kaifarenxinxi[1] if len(kaifarenxinxi) > 1 else '') if user_software_info else (kaifarenxinxi[1] if len(kaifarenxinxi) > 1 else ''),
                        'chief_designer': user_software_info.get('chief_designer', '') if user_software_info else '',
                        'programming_language': user_software_info.get('programming_language', 'C/C++') if user_software_info else 'C/C++',
                        'development_environment': user_software_info.get('development_environment', 'Visual Studio') if user_software_info else 'Visual Studio',
                        'runtime_environment': user_software_info.get('runtime_environment', 'Windows') if user_software_info else 'Windows',
                        'software_level': user_software_info.get('software_level', 'C级') if user_software_info else 'C级',
                        'test_manager': zhuguan_name,
                        'test_personnel': ceshiren_name,
                        'developer': kaifarenxinxi[0] if kaifarenxinxi else ''
                    }
                    
                    # 使用数据库服务存储
                    self.db_service.store_project_info_data(db_task_id, basic_info, user_software_info)
                    # log_info(f"[DB] 项目信息数据成功存储到数据库，task_id: {db_task_id}", "form_builder_service")
                    
                except Exception as db_e:
                    # log_error(f"[DB] 存储项目信息数据到数据库时发生错误: {str(db_e)}", "form_builder_service")
                    pass
            else:
                # log_info("[DB] 跳过项目信息数据库存储（未提供task_id或数据库服务）", "form_builder_service")
        
                pass
        # log_info("开始填充项目策划表...", "form_builder_service")
        if progress_callback:
            progress_callback(90, "正在填充项目策划表...")
        if self.project_plan_filler.fill_project_plan_table(
            excel_file_path, 
            sheet_names['project_plan'], 
            data['ruanjian_name'], 
            xinghao_xinxi_list,
            data['total_lines'],
            zhuguan_name,
            ceshiren_name,
            list(data['requirements_dict'].keys()),
            data['requirements_dict']  # 🔧 修复：传递完整需求字典以保留编号信息
        ):
            success_count += 1
            # log_info("项目策划表填充成功", "form_builder_service")
            
            # 存储项目策划核心数据到数据库
            if self.optimized_db and db_task_id:
                # 🔧 新方法：直接从已生成的Excel文件中提取完整数据存储到数据库
                try:
                    from ..project_plan.project_plan_service import ProjectPlanService
                    project_plan_service = ProjectPlanService()
                    
                    # 使用新的Excel数据提取方法
                    success = project_plan_service.extract_and_store_excel_data_to_db(
                        excel_file_path=excel_file_path,
                        sheet_name=sheet_names['project_plan'],
                        task_id=db_task_id
                    )
                    if success:
                        # log_info("成功从Excel提取并存储项目策划数据到数据库", "form_builder_service")
                        pass
                    else:
                        # log_warning("从Excel提取项目策划数据失败，使用备用方法", "form_builder_service")
                        # 备用方法：使用原有逻辑
                        self._store_project_plan_to_db_legacy(db_task_id, data['requirements_dict'], zhuguan_name, ceshiren_name)
                except Exception as e:
                    # log_warning(f"新的Excel数据提取方法失败: {e}，使用备用方法", "form_builder_service")
                    # 备用方法：使用原有逻辑
                    self._store_project_plan_to_db_legacy(db_task_id, data['requirements_dict'], zhuguan_name, ceshiren_name)
        
        return success_count
    
    def _get_requirement_analysis_from_db(self, task_id: str) -> Optional[Dict]:
        """从数据库获取需求分析数据（包含测试方法）"""
        try:
            # log_info(f"从数据库获取需求分析数据，task_id: {task_id}", "form_builder_service")
            
            # 使用正确的方法名
            requirement_analysis_list = self.optimized_db.get_requirement_analysis_by_task(task_id)
            
            if requirement_analysis_list:
                # log_info(f"成功从数据库获取 {len(requirement_analysis_list)} 条需求分析数据", "form_builder_service")
                
                # 转换为新模块需要的格式
                test_items = []
                skipped_count = 0
                
                for item in requirement_analysis_list:
                    test_method = item.get('test_method', '').strip()
                    test_item_name = item.get('test_item_name', '').strip()
                    
                    # 只包含有测试方法的项目
                    if test_method:
                        test_item = {
                            'name': test_item_name,
                            'pure_name': test_item_name,
                            'requirement_description': item.get('requirement_description', ''),
                            'test_description': item.get('test_description', ''),
                            'test_method': test_method,
                            'test_item_identifier': item.get('test_item_identifier', ''),
                            'pass_criteria': item.get('pass_criteria', ''),
                            'adequacy_requirement': item.get('adequacy_requirement', ''),
                            'test_type': item.get('test_type', '功能测试'),
                            'software_requirement_trace': item.get('software_requirement_trace', '')
                        }
                        test_items.append(test_item)
                        # log_info(f"添加测试项: {test_item_name} -> 测试方法: {test_method[:50]}...", "form_builder_service")
                    else:
                        skipped_count += 1
                        # log_warning(f"跳过无测试方法的项目: {test_item_name}", "form_builder_service")
                
                # log_info(f"有效测试项: {len(test_items)}, 跳过: {skipped_count}", "form_builder_service")
                return {'test_items': test_items}
            else:
                # log_warning(f"从数据库获取需求分析数据为空，task_id: {task_id}", "form_builder_service")
                return None
        except Exception as e:
            # log_error(f"从数据库获取需求分析数据时发生错误: {str(e)}", "form_builder_service")
            return None

    def _store_requirement_analysis_to_db(self, session_id: str, final_xuqiu_mioashu: Dict,
                                          ruanjian_name: str, user_software_info: Dict):
        """存储需求分析核心数据到现有数据库"""
        try:
            requirements_data = []
            software_id = user_software_info.get('software_id', 'UNKNOWN') if user_software_info else 'UNKNOWN'
            software_version = user_software_info.get('software_version', '1.0.0') if user_software_info else '1.0.0'

            for req_id, req_data in final_xuqiu_mioashu.items():
                if isinstance(req_data, dict):
                    req_name = req_data.get('name', req_id)
                    req_desc = req_data.get('description', '')
                    chapter = req_data.get('chapter', '')

                    # 生成测试项标识  
                    # 🔧 使用简单的英文标识符生成规则，不再依赖AI翻译
                    english_id = f'Function{len(requirements_data)+1:03d}'
                    test_item_identifier = f"CT-{software_id}-{software_version}-{english_id}-FN01"

                    requirement_data = {
                        'requirement_id': req_id,
                        'index_number': len(requirements_data) + 1,
                        'software_name': ruanjian_name,
                        'software_version': software_version,
                        'round_info': '',
                        'standard_sub_requirement_name': '',
                        'standard_sub_requirement_identifier': '',
                        'standard_sub_requirement_unit': '',
                        'task_requirement_trace': f"《{ruanjian_name}软件需求规格说明》",
                        'software_requirement_trace': req_id,
                        'software_requirement_name': req_name,
                        'software_requirement_identifier': req_id,
                        'requirement_description': req_desc,
                        'test_type': '功能测试',
                        'test_item_name': req_name,
                        'test_item_identifier': test_item_identifier,
                        'process_identifier': test_item_identifier,
                        'requirement_sub_description': req_desc,
                        'test_description': f'验证{req_name}的功能实现',
                        'test_method': f'通过检测仪发送测试指令,查看{req_name}功能实现是否正常',
                        'adequacy_requirement': f'完成{req_name}相关的所有测试用例',
                        'pass_criteria': f'{req_name}功能正常'
                    }
                    requirements_data.append(requirement_data)

            self.optimized_db.save_requirement_analysis(session_id, requirements_data)
            # log_info(f"已存储 {len(requirements_data)} 条需求分析数据到数据库", "form_builder_service")
            
        except Exception as e:
            # log_warning(f"存储需求分析数据失败: {e}", "form_builder_service")

            pass
    def _store_requirement_analysis_to_db_legacy(self, session_id: str, final_xuqiu_mioashu: Dict,
                                          ruanjian_name: str, user_software_info: Dict):
        """存储需求分析核心数据到现有数据库（备用方法）"""
        try:
            requirements_data = []
            software_id = user_software_info.get('software_id', 'UNKNOWN') if user_software_info else 'UNKNOWN'
            software_version = user_software_info.get('software_version', '1.0.0') if user_software_info else '1.0.0'

            for req_id, req_data in final_xuqiu_mioashu.items():
                if isinstance(req_data, dict):
                    req_name = req_data.get('name', req_id)
                    req_desc = req_data.get('description', '')
                    chapter = req_data.get('chapter', '')

                    # 生成测试项标识
                    # 🔧 使用简单的英文标识符生成规则，不再依赖AI翻译
                    english_id = f'Function{len(requirements_data)+1:03d}'
                    test_item_identifier = f"CT-{software_id}-{software_version}-{english_id}-FN01"

                    requirement_data = {
                        'requirement_id': req_id,
                        'index_number': len(requirements_data) + 1,
                        'software_name': ruanjian_name,
                        'software_version': software_version,
                        'round_info': '',
                        'standard_sub_requirement_name': '',
                        'standard_sub_requirement_identifier': '',
                        'standard_sub_requirement_unit': '',
                        'task_requirement_trace': f"《{ruanjian_name}软件需求规格说明》",
                        'software_requirement_trace': req_id,
                        'software_requirement_name': req_name,
                        'software_requirement_identifier': req_id,
                        'requirement_description': req_desc,
                        'test_type': '功能测试',
                        'test_item_name': req_name,
                        'test_item_identifier': test_item_identifier,
                        'process_identifier': test_item_identifier,
                        'requirement_sub_description': req_desc,
                        'test_description': f'验证{req_name}的功能实现',
                        'test_method': f'通过检测仪发送测试指令,查看{req_name}功能实现是否正常',
                        'adequacy_requirement': f'完成{req_name}相关的所有测试用例',
                        'pass_criteria': f'{req_name}功能正常'
                    }
                    requirements_data.append(requirement_data)

            self.optimized_db.save_requirement_analysis(session_id, requirements_data)
            # log_info(f"已存储 {len(requirements_data)} 条需求分析数据到数据库", "form_builder_service")
            
        except Exception as e:
            # log_warning(f"存储需求分析数据失败: {e}", "form_builder_service")

            pass
    def _store_test_cases_to_db_legacy(self, session_id: str, final_xuqiu_mioashu: Dict, ai_enabled: bool):
        """存储测试用例核心数据到现有数据库（备用方法）"""
        try:
            test_cases_data = []
            case_counter = 1

            for req_id, req_data in final_xuqiu_mioashu.items():
                if isinstance(req_data, dict):
                    req_name = req_data.get('name', req_id)
                    req_desc = req_data.get('description', '')
                    
                    test_case_data = {
                        'task_id': session_id,
                        'requirement_id': req_id,
                        'test_case_id': f'TC{case_counter:03d}',
                        'test_case_name': f'验证{req_name}功能',
                        'test_case_description': f'验证{req_name}功能是否正常工作',
                        'test_type': 'functional',
                        'preconditions': '系统正常运行，相关模块已初始化',
                        'test_steps': f'[{{"step":1,"action":"准备{req_name}相关的测试数据"}},{{"step":2,"action":"执行{req_name}功能"}},{{"step":3,"action":"验证功能执行结果"}}]',
                        'expected_results': f'{req_name}功能按照需求规格说明正常工作',
                        'test_data_input': f'{req_name}相关的测试数据'
                    }
                    test_cases_data.append(test_case_data)
                    case_counter += 1

            self.optimized_db.save_test_cases(session_id, test_cases_data)
            # log_info(f"已存储 {len(test_cases_data)} 条测试用例数据到数据库", "form_builder_service")
            
        except Exception as e:
            # log_warning(f"存储测试用例数据失败: {e}", "form_builder_service")

            pass
    def _store_project_plan_to_db_legacy(self, session_id: str, requirements_dict: Dict, zhuguan_name: str, ceshiren_name: str):
        """存储项目策划核心数据到现有数据库（备用方法）"""
        try:
            project_plan_data = []
            software_id = 'UNKNOWN' # 项目策划不直接关联软件ID，但可以包含
            software_version = '1.0.0'

            for req_id, req_data in requirements_dict.items():
                if isinstance(req_data, dict):
                    req_name = req_data.get('name', req_id)
                    req_desc = req_data.get('description', '')
                    chapter = req_data.get('chapter', '')

                    # 生成项目策划标识
                    project_plan_identifier = f"PP-{software_id}-{software_version}-{req_id}-FN01"

                    project_plan_item = {
                        'task_id': session_id,
                        'requirement_id': req_id,
                        'project_plan_id': project_plan_identifier,
                        'project_plan_name': f'项目策划: {req_name}',
                        'project_plan_description': f'项目策划: {req_desc}',
                        'project_plan_type': 'project_planning',
                        'project_plan_status': 'pending',
                        'project_plan_priority': 'normal',
                        'project_plan_assignee': zhuguan_name,
                        'project_plan_reporter': ceshiren_name,
                        'project_plan_start_date': '2023-01-01', # 示例日期
                        'project_plan_end_date': '2023-12-31', # 示例日期
                        'project_plan_estimated_hours': 10, # 示例工时
                        'project_plan_actual_hours': 0, # 示例工时
                        'project_plan_dependencies': [], # 示例依赖
                        'project_plan_notes': f'项目策划: {req_desc}',
                        'tracking_info': f"《{zhuguan_name}项目策划》 {req_name}"
                    }
                    project_plan_data.append(project_plan_item)

            self.optimized_db.save_project_plan(session_id, project_plan_data)
            # log_info(f"已存储 {len(project_plan_data)} 条项目策划数据到数据库", "form_builder_service")
            
        except Exception as e:
            # log_warning(f"存储项目策划数据失败: {e}", "form_builder_service")


            pass
# 为了保持兼容性，创建别名
ConfigurationItemFormBuilderService = FormBuilderService 