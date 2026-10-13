"""
状态管理器
管理生成流程的状态文件，跟踪4个步骤的完成情况
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


STATE_FILE_NAME = "generation_state.json"


class GenerationStateManager:
    """生成状态管理器"""
    
    def __init__(self, session_dir: Path):
        """
        初始化状态管理器
        
        Args:
            session_dir: 会话目录路径
        """
        self.session_dir = Path(session_dir)
        self.state_file = self.session_dir / STATE_FILE_NAME
        
    def initialize_state(self, requirement_doc_info: Dict[str, Any], basic_info: Dict[str, Any], 
                        catalog_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        初始化状态文件
        
        Args:
            requirement_doc_info: 需求文档信息 {original_path, standardized_path, upload_time}
            basic_info: 基本信息
            catalog_items: 测试需求项列表
            
        Returns:
            初始化的状态字典
        """
        state = {
            "session_id": self.session_dir.name,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "requirement_document": {
                "original_path": requirement_doc_info.get("original_path", ""),
                "standardized_path": requirement_doc_info.get("standardized_path", ""),
                "upload_time": requirement_doc_info.get("upload_time", datetime.now().isoformat())
            },
            "basic_info": basic_info,
            "catalog_items": catalog_items,
            "completed_steps": {
                "step1_project_info": {
                    "completed": False,
                    "completed_at": None,
                    "output_files": [],
                    "task_id": None,
                    "error": None
                },
                "step2_test_issue": {
                    "completed": False,
                    "completed_at": None,
                    "output_files": [],
                    "task_id": None,
                    "error": None
                },
                "step3_requirement_analysis": {
                    "completed": False,
                    "completed_at": None,
                    "output_files": [],
                    "task_id": None,
                    "error": None
                },
                "step4_test_case": {
                    "completed": False,
                    "completed_at": None,
                    "output_files": [],
                    "task_id": None,
                    "error": None
                }
            }
        }
        
        self._save_state(state)
        log_info(f"初始化状态文件: {self.state_file}", "state_manager")
        return state
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        加载状态文件
        
        Returns:
            状态字典，如果文件不存在返回None
        """
        if not self.state_file.exists():
            log_warning(f"状态文件不存在: {self.state_file}", "state_manager")
            return None
            
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            log_debug(f"加载状态文件成功: {self.state_file}", "state_manager")
            return state
        except Exception as e:
            log_error(f"加载状态文件失败: {str(e)}", "state_manager")
            return None
    
    def update_step_status(self, step_name: str, completed: bool = False, 
                          output_files: List[str] = None, task_id: str = None,
                          error: str = None) -> bool:
        """
        更新步骤状态
        
        Args:
            step_name: 步骤名称 (step1_project_info, step2_test_issue, step3_requirement_analysis, step4_test_case)
            completed: 是否完成
            output_files: 输出文件列表
            task_id: 任务ID
            error: 错误信息
            
        Returns:
            更新是否成功
        """
        state = self.load_state()
        if state is None:
            log_error(f"无法加载状态文件，更新步骤状态失败: {step_name}", "state_manager")
            return False
        
        if step_name not in state["completed_steps"]:
            log_error(f"无效的步骤名称: {step_name}", "state_manager")
            return False
        
        # 更新步骤信息
        step_info = state["completed_steps"][step_name]
        step_info["completed"] = completed
        
        if completed:
            step_info["completed_at"] = datetime.now().isoformat()
        
        if output_files is not None:
            step_info["output_files"] = output_files
            
        if task_id is not None:
            step_info["task_id"] = task_id
            
        if error is not None:
            step_info["error"] = error
        
        # 更新最后修改时间
        state["last_updated"] = datetime.now().isoformat()
        
        self._save_state(state)
        log_info(f"更新步骤状态成功: {step_name}, completed={completed}", "state_manager")
        return True
    
    def get_step_status(self, step_name: str) -> Optional[Dict[str, Any]]:
        """
        获取步骤状态
        
        Args:
            step_name: 步骤名称
            
        Returns:
            步骤状态字典
        """
        state = self.load_state()
        if state is None:
            return None
            
        return state["completed_steps"].get(step_name)
    
    def is_step_completed(self, step_name: str) -> bool:
        """
        检查步骤是否已完成
        
        Args:
            step_name: 步骤名称
            
        Returns:
            是否已完成
        """
        step_status = self.get_step_status(step_name)
        if step_status is None:
            return False
        return step_status.get("completed", False)
    
    def can_start_step(self, step_name: str) -> Tuple[bool, str]:
        """
        检查是否可以开始某个步骤（验证依赖关系）
        
        Args:
            step_name: 步骤名称
            
        Returns:
            (是否可以开始, 原因说明)
        """
        state = self.load_state()
        if state is None:
            return False, "状态文件不存在，请先上传需求文档"
        
        # 检查各步骤的依赖关系
        if step_name == "step1_project_info":
            # Step1只需要基本信息和需求文档
            if not state.get("requirement_document", {}).get("original_path"):
                return False, "需求文档未上传"
            if not state.get("basic_info"):
                return False, "基本信息未填写"
            return True, "可以开始"
            
        elif step_name == "step2_test_issue":
            # Step2需要Step1完成
            if not self.is_step_completed("step1_project_info"):
                return False, "请先完成步骤1：生成项目信息表"
            # 检查是否有标准化文档
            if not state.get("requirement_document", {}).get("standardized_path"):
                return False, "需求文档未标准化"
            return True, "可以开始"
            
        elif step_name == "step3_requirement_analysis":
            # Step3需要Step2完成，并且需要有项目策划表
            if not self.is_step_completed("step2_test_issue"):
                return False, "请先完成步骤2：生成测试表与问题单"
            # 检查Step2是否生成了项目策划表
            step2_files = self.get_step_status("step2_test_issue").get("output_files", [])
            has_planning = any("策划" in f or "planning" in f.lower() for f in step2_files)
            if not has_planning:
                return False, "未找到项目策划表"
            return True, "可以开始"
            
        elif step_name == "step4_test_case":
            # Step4需要Step3完成，并且需要有需求分析表
            if not self.is_step_completed("step3_requirement_analysis"):
                return False, "请先完成步骤3：生成需求分析表"
            # 检查Step3是否生成了需求分析表
            step3_files = self.get_step_status("step3_requirement_analysis").get("output_files", [])
            has_analysis = any("需求分析" in f or "requirement" in f.lower() for f in step3_files)
            if not has_analysis:
                return False, "未找到需求分析表"
            return True, "可以开始"
            
        else:
            return False, f"未知的步骤名称: {step_name}"
    
    def update_basic_info(self, basic_info: Dict[str, Any]) -> bool:
        """
        更新基本信息
        
        Args:
            basic_info: 基本信息字典
            
        Returns:
            是否更新成功
        """
        state = self.load_state()
        if state is None:
            log_error("无法加载状态文件，更新基本信息失败", "state_manager")
            return False
        
        state["basic_info"] = basic_info
        state["last_updated"] = datetime.now().isoformat()
        
        self._save_state(state)
        log_info("更新基本信息成功", "state_manager")
        return True
    
    def get_basic_info(self) -> Optional[Dict[str, Any]]:
        """
        获取基本信息
        
        Returns:
            基本信息字典
        """
        state = self.load_state()
        if state is None:
            return None
        return state.get("basic_info")
    
    def get_requirement_document_info(self) -> Optional[Dict[str, Any]]:
        """
        获取需求文档信息
        
        Returns:
            需求文档信息字典
        """
        state = self.load_state()
        if state is None:
            return None
        return state.get("requirement_document")
    
    def get_catalog_items(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取测试需求项
        
        Returns:
            测试需求项列表
        """
        state = self.load_state()
        if state is None:
            return None
        return state.get("catalog_items", [])
    
    def get_all_generated_files(self) -> List[str]:
        """
        获取所有已生成的文件列表
        
        Returns:
            文件名列表
        """
        state = self.load_state()
        if state is None:
            return []
        
        all_files = []
        for step_name, step_info in state["completed_steps"].items():
            if step_info["completed"]:
                all_files.extend(step_info.get("output_files", []))
        
        return all_files
    
    def _save_state(self, state: Dict[str, Any]) -> bool:
        """
        保存状态文件
        
        Args:
            state: 状态字典
            
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            self.session_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            log_debug(f"保存状态文件成功: {self.state_file}", "state_manager")
            return True
        except Exception as e:
            log_error(f"保存状态文件失败: {str(e)}", "state_manager")
            return False

    def save_state(self, state: Dict[str, Any]) -> bool:
        """
        保存状态文件（对外公开方法，供API层调用）
        """
        return self._save_state(state)
    
    def reset_state(self) -> bool:
        """
        重置状态（删除状态文件）
        
        Returns:
            是否重置成功
        """
        try:
            if self.state_file.exists():
                self.state_file.unlink()
                log_info(f"重置状态文件成功: {self.state_file}", "state_manager")
            return True
        except Exception as e:
            log_error(f"重置状态文件失败: {str(e)}", "state_manager")
            return False

