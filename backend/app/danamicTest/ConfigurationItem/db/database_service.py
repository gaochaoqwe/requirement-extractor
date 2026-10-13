"""
数据库集成服务
用于在动态测试表单生成过程中存储各种数据到数据库
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .optimized_models import OptimizedDynamicTestDatabase

class DatabaseIntegrationService:
    """数据库集成服务"""
    
    def __init__(self, db_path: str = None):
        self.db = OptimizedDynamicTestDatabase(db_path)
        self.logger = logging.getLogger(__name__)
    
    def start_task(self, session_id: str, task_type: str = 'form_generation') -> str:
        """开始一个新的任务"""
        task_id = self.db.create_task(session_id, task_type)
        self.db.update_task_status(task_id, 'running')
        self.logger.info(f"开始任务 {task_id} (会话: {session_id})")
        return task_id
    
    def register_existing_task(self, task_id: str, session_id: str, task_type: str = 'form_generation'):
        """为已存在的task_id注册任务记录"""
        try:
            # 检查任务是否已存在
            existing_task = self.db.get_task_status(task_id)
            if existing_task:
                self.logger.info(f"任务 {task_id} 已存在，仅更新状态为running")
                self.db.update_task_status(task_id, 'running')
            else:
                # 创建新的任务记录
                self.db.create_task_with_id(task_id, session_id, task_type)
                self.db.update_task_status(task_id, 'running')
                self.logger.info(f"为外部task_id {task_id} 创建任务记录 (会话: {session_id})")
        except Exception as e:
            self.logger.error(f"注册任务 {task_id} 失败: {e}")
            # 🔧 修复：移除备用任务创建逻辑，避免重复创建
            # 如果注册失败，不再尝试备用创建，避免产生重复记录
            pass
    
    def complete_task(self, task_id: str):
        """完成任务"""
        self.db.update_task_status(task_id, 'completed')
        self.logger.info(f"任务 {task_id} 已完成")
    
    def fail_task(self, task_id: str, error_message: str):
        """任务失败"""
        self.db.update_task_status(task_id, 'failed', error_message)
        self.logger.error(f"任务 {task_id} 失败: {error_message}")
    
    def store_project_info_data(self, task_id: str, basic_info: Dict[str, Any], user_software_info: Optional[Dict[str, Any]] = None):
        """存储项目信息数据"""
        try:
            # 🔧 修复：改进字段映射逻辑，优先使用user_software_info，但如果字段不存在则回退到basic_info
            def get_field_value(field_name, alt_field_name=None):
                """获取字段值，优先从user_software_info，然后从basic_info"""
                if user_software_info and user_software_info.get(field_name):
                    return user_software_info.get(field_name)
                elif alt_field_name and basic_info.get(alt_field_name):
                    return basic_info.get(alt_field_name)
                else:
                    return basic_info.get(field_name)
            
            # 合并基本信息和用户软件信息
            project_info_data = {
                'software_name': get_field_value('software_name'),
                'software_version': get_field_value('software_version'),
                'software_id': get_field_value('software_id', 'software_identifier'),
                'domain': get_field_value('domain'),
                'aircraft_model': get_field_value('aircraft_model'),
                'project_director': get_field_value('project_director'),
                'development_department': get_field_value('development_department'),
                'chief_designer': get_field_value('chief_designer'),
                'programming_language': get_field_value('programming_language'),
                'development_environment': get_field_value('development_environment'),
                'runtime_environment': get_field_value('runtime_environment'),
                'software_level': get_field_value('software_level'),
                'additional_info': {
                    'test_type': basic_info.get('test_type'),
                    'test_requirement_identifier_prefix': basic_info.get('test_requirement_identifier_prefix'),
                    'test_manager': basic_info.get('test_manager'),
                    'test_personnel': basic_info.get('test_personnel'),
                    'developer': basic_info.get('developer'),
                    'basic_info_raw': basic_info,
                    'user_software_info_raw': user_software_info
                }
            }
            
            # 🔧 新增：调试日志，记录映射的字段值
            self.logger.debug(f"项目信息数据映射结果: software_name={project_info_data['software_name']}, software_version={project_info_data['software_version']}")
            
            self.db.save_project_info(task_id, project_info_data)
            self.logger.info(f"已存储项目信息数据到任务 {task_id}")
            
        except Exception as e:
            self.logger.error(f"存储项目信息数据失败 (任务 {task_id}): {e}")
            raise
    
    def store_software_config_data(self, task_id: str, config_data: Dict[str, Any]):
        """存储软件配置数据"""
        try:
            # 转换软件配置数据格式
            software_config_data = {
                'config_item_name': config_data.get('software_name'),
                'config_item_version': config_data.get('software_version'),
                'config_item_id': config_data.get('software_identifier'),
                'config_status': 'active',  # 默认状态
                'config_type': 'software_configuration',
                'file_path': config_data.get('file_path'),
                'checksum': config_data.get('checksum'),
                'size_info': config_data.get('size_info'),
                'modification_time': config_data.get('modification_time'),
                'responsible_person': config_data.get('development_department'),
                'additional_config': {
                    'programming_language': config_data.get('programming_language'),
                    'development_environment': config_data.get('development_environment'),
                    'runtime_environment': config_data.get('runtime_environment'),
                    'software_level': config_data.get('software_level'),
                    'config_data_raw': config_data
                }
            }
            
            self.db.save_software_config(task_id, software_config_data)
            self.logger.info(f"已存储软件配置数据到任务 {task_id}")
            
        except Exception as e:
            self.logger.error(f"存储软件配置数据失败 (任务 {task_id}): {e}")
            raise
    
    def store_project_plan_data(self, task_id: str, plan_items: List[Dict[str, Any]]):
        """存储项目策划数据"""
        try:
            plan_data_list = []
            
            for i, item in enumerate(plan_items):
                plan_data = {
                    'plan_item_id': f"PLAN_{task_id}_{i+1:03d}",
                    'plan_item_name': item.get('name', f'策划项{i+1}'),
                    'plan_description': item.get('description', ''),
                    'plan_type': item.get('type', 'general'),
                    'priority_level': item.get('priority', 3),  # 默认中等优先级
                    'estimated_effort': item.get('effort', ''),
                    'start_date': item.get('start_date', ''),
                    'end_date': item.get('end_date', ''),
                    'assigned_personnel': item.get('assigned_personnel', ''),
                    'status': item.get('status', 'planned'),
                    'dependencies': item.get('dependencies', []),
                    'deliverables': item.get('deliverables', []),
                    'additional_plan_info': {
                        'original_data': item
                    }
                }
                plan_data_list.append(plan_data)
            
            self.db.save_project_plan(task_id, plan_data_list)
            self.logger.info(f"已存储项目策划数据到任务 {task_id} ({len(plan_data_list)} 个项目)")
            
        except Exception as e:
            self.logger.error(f"存储项目策划数据失败 (任务 {task_id}): {e}")
            raise
    
    def store_requirement_analysis_data(self, task_id: str, analysis_data: Dict[str, Any]):
        """存储需求分析数据"""
        try:
            analysis_data_list = []
            
            if 'test_items' in analysis_data:
                for i, item in enumerate(analysis_data['test_items']):
                    requirement_data = {
                        'requirement_id': item.get('name', f'REQ_{task_id}_{i+1:03d}'),
                        'requirement_name': item.get('pure_name', item.get('name')),
                        'requirement_description': item.get('requirement_description', ''),
                        'requirement_type': 'functional',  # 默认功能需求
                        'priority': 'medium',  # 默认中等优先级
                        'complexity': 'medium',  # 默认中等复杂度
                        'test_item_identifier': item.get('test_item_identifier', ''),
                        'test_item_name': item.get('pure_name', ''),
                        'test_description': item.get('test_description', ''),
                        'test_method': item.get('test_method', ''),
                        'chapter_number': item.get('chapter_number', ''),
                        'tracking_info': item.get('software_requirement_trace', ''),
                        'acceptance_criteria': item.get('pass_criteria', ''),
                        'test_data': {
                            'english_identifier': item.get('english_identifier', ''),
                            'adequacy_requirement': item.get('adequacy_requirement', ''),
                            'test_type': item.get('test_type', 'functional')
                        },
                        'additional_analysis_info': {
                            'index': item.get('index'),
                            'standard_sub_requirement_name': item.get('standard_sub_requirement_name'),
                            'standard_sub_requirement_unit': item.get('standard_sub_requirement_unit'),
                            'task_requirement_trace': item.get('task_requirement_trace'),
                            'software_requirement_name': item.get('software_requirement_name'),
                            'requirement_sub_description': item.get('requirement_sub_description'),
                            'original_item': item
                        }
                    }
                    analysis_data_list.append(requirement_data)
            
            self.db.save_requirement_analysis(task_id, analysis_data_list)
            self.logger.info(f"已存储需求分析数据到任务 {task_id} ({len(analysis_data_list)} 个需求)")
            
        except Exception as e:
            self.logger.error(f"存储需求分析数据失败 (任务 {task_id}): {e}")
            raise
    
    def store_test_cases_data(self, task_id: str, test_cases_data: List[Dict[str, Any]], requirement_mapping: Optional[Dict[str, str]] = None):
        """存储测试用例数据"""
        try:
            test_cases_list = []
            
            for i, test_case in enumerate(test_cases_data):
                # 从测试用例数据中提取信息
                case_data = {
                    'requirement_id': requirement_mapping.get(str(i)) if requirement_mapping else f'REQ_{task_id}_{i+1:03d}',
                    'test_case_id': test_case.get('test_case_id', f'TC_{task_id}_{i+1:03d}'),
                    'test_case_name': test_case.get('test_case_name', test_case.get('case_name')),
                    'test_case_description': test_case.get('test_case_description', test_case.get('case_description')),
                    'test_type': test_case.get('test_type', 'functional'),
                    'test_priority': test_case.get('test_priority', 'medium'),
                    'preconditions': test_case.get('preconditions', '被测软件正常加载'),
                    'test_steps': test_case.get('test_steps', test_case.get('case_steps', [])),
                    'expected_results': test_case.get('expected_results', test_case.get('case_expect')),
                    'actual_results': test_case.get('actual_results', ''),
                    'test_status': test_case.get('test_status', 'created'),
                    'test_environment': test_case.get('test_environment', '标准测试环境'),
                    'test_data_input': test_case.get('test_data_input', ''),
                    'test_personnel': test_case.get('test_personnel', '测试人员'),
                    'execution_time': test_case.get('execution_time'),
                    'execution_duration': test_case.get('execution_duration'),
                    'defect_info': test_case.get('defect_info', {}),
                    'additional_case_info': {
                        'test_item_identifier': test_case.get('test_item_identifier'),
                        'test_item_name': test_case.get('test_item_name'),
                        'requirement_tracking': test_case.get('requirement_tracking'),
                        'original_case': test_case
                    }
                }
                test_cases_list.append(case_data)
            
            self.db.save_test_cases(task_id, test_cases_list)
            self.logger.info(f"已存储测试用例数据到任务 {task_id} ({len(test_cases_list)} 个用例)")
            
        except Exception as e:
            self.logger.error(f"存储测试用例数据失败 (任务 {task_id}): {e}")
            raise
    
    def get_task_summary(self, task_id: str) -> Dict[str, Any]:
        """获取任务摘要信息"""
        try:
            task_info = self.db.get_task_info(task_id)
            if not task_info:
                return {}
            
            # 可以在这里添加更多的统计信息查询
            # 例如：需求数量、测试用例数量等
            
            return {
                'task_info': task_info,
                'summary': {
                    'has_project_info': True,  # 可以通过查询数据库确定
                    'has_software_config': True,
                    'has_project_plan': True,
                    'has_requirement_analysis': True,
                    'has_test_cases': True
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取任务摘要失败 (任务 {task_id}): {e}")
            return {}
    
    def get_base_data_for_frontend(self) -> Dict[str, List[Dict[str, str]]]:
        """获取前端需要的基础数据"""
        try:
            return {
                'domains': self.db.get_domains(),
                'test_managers': self.db.get_test_managers(),
                'test_personnel': self.db.get_test_personnel(),
                'developers': self.db.get_developers(),
                'aircraft_models': self.db.get_aircraft_models(),
                'project_directors': self.db.get_project_directors(),
                'development_departments': self.db.get_development_departments(),
                'chief_designers': self.db.get_chief_designers(),
                'components': self.db.get_components()
            }
        except Exception as e:
            self.logger.error(f"获取基础数据失败: {e}")
            return {}


# 单例实例
_database_service_instance = None

def get_database_service() -> DatabaseIntegrationService:
    """获取数据库集成服务单例"""
    global _database_service_instance
    if _database_service_instance is None:
        _database_service_instance = DatabaseIntegrationService()
    return _database_service_instance 