"""
任务取消管理器

提供线程安全的任务取消标志管理，允许动态取消正在运行的任务
支持任务暂停和恢复功能
"""
import threading
from typing import Dict, Set
from .logger import log_info, log_warning, log_debug

class TaskCancelManager:
    """任务取消管理器（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        # 存储取消标志 {task_id: threading.Event()}
        self._cancel_flags: Dict[int, threading.Event] = {}
        # 访问锁
        self._flags_lock = threading.Lock()
        
        log_debug("TaskCancelManager 初始化完成", "task_cancel_manager")
        
        # 从数据库恢复暂停的任务
        self._restore_paused_tasks()
    
    def register_task(self, task_id: int):
        """
        注册一个任务（创建取消标志）
        
        Args:
            task_id: 任务ID
        """
        with self._flags_lock:
            if task_id not in self._cancel_flags:
                self._cancel_flags[task_id] = threading.Event()
                log_debug(f"任务 {task_id} 已注册到取消管理器", "task_cancel_manager")
    
    def cancel_task(self, task_id: int) -> bool:
        """
        取消一个任务（设置取消标志）
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功设置取消标志
        """
        with self._flags_lock:
            if task_id in self._cancel_flags:
                self._cancel_flags[task_id].set()
                log_info(f"任务 {task_id} 的取消标志已设置", "task_cancel_manager")
                return True
            else:
                log_warning(f"任务 {task_id} 不存在于取消管理器中", "task_cancel_manager")
                return False
    
    def is_cancelled(self, task_id: int) -> bool:
        """
        检查任务是否被取消
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 任务是否被取消
        """
        with self._flags_lock:
            if task_id in self._cancel_flags:
                return self._cancel_flags[task_id].is_set()
            return False
    
    def unregister_task(self, task_id: int):
        """
        取消注册任务（清理取消标志）
        
        Args:
            task_id: 任务ID
        """
        with self._flags_lock:
            if task_id in self._cancel_flags:
                del self._cancel_flags[task_id]
                log_debug(f"任务 {task_id} 已从取消管理器中移除", "task_cancel_manager")
    
    def get_registered_tasks(self) -> Set[int]:
        """
        获取所有已注册的任务ID
        
        Returns:
            Set[int]: 任务ID集合
        """
        with self._flags_lock:
            return set(self._cancel_flags.keys())
    
    def _restore_paused_tasks(self):
        """
        从数据库恢复暂停的任务
        在系统启动时调用，恢复所有paused状态的任务到取消管理器
        """
        try:
            # 注意：这里必须从 ConfigurationItem 包内导入，而不是上一级 codeReview
            # 使用两级相对导入，指向 app.codeReview.ConfigurationItem.config_database / db.models
            from ..config_database import get_db
            from ..db.models.task import AnalysisTask
            
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # 查询所有暂停的任务
                paused_tasks = db.query(AnalysisTask).filter(
                    AnalysisTask.status == 'paused'
                ).all()
                
                if paused_tasks:
                    log_info(f"发现 {len(paused_tasks)} 个暂停的任务，正在恢复到取消管理器", "task_restore")
                    
                    for task in paused_tasks:
                        # 注册任务并设置取消标志（暂停状态）
                        self.register_task(task.id)
                        self._cancel_flags[task.id].set()
                        log_info(f"恢复暂停任务: ID={task.id}, Name={task.task_name}", "task_restore")
                else:
                    log_debug("没有发现暂停的任务", "task_restore")
                    
            finally:
                db.close()
                
        except Exception as e:
            log_warning(f"恢复暂停任务失败: {e}", "task_restore")
    
    def pause_task(self, task_id: int, db) -> bool:
        """
        暂停任务（持久化到数据库）
        
        Args:
            task_id: 任务ID
            db: 数据库会话
            
        Returns:
            bool: 是否成功暂停
        """
        # 这里同样需要从 ConfigurationItem 包下的 db.repository 导入
        from ..db.repository.task_repo import TaskRepository
        from datetime import datetime
        
        # 设置内存标志
        success = self.cancel_task(task_id)
        
        # 更新数据库状态为 paused
        task_repo = TaskRepository(db)
        task = task_repo.get_task(task_id)
        
        if task:
            task.status = 'paused'
            task.paused_at = datetime.utcnow()
            db.commit()
            log_info(f"任务 {task_id} 已暂停并持久化到数据库", "task_pause")
        
        return success
    
    def resume_task(self, task_id: int) -> bool:
        """
        恢复任务（清除取消标志）
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功恢复
        """
        with self._flags_lock:
            if task_id in self._cancel_flags:
                # 清除取消标志
                self._cancel_flags[task_id].clear()
                log_info(f"任务 {task_id} 的取消标志已清除，可以继续执行", "task_resume")
                return True
            else:
                # 如果不存在，创建一个新的（未设置的）标志
                self._cancel_flags[task_id] = threading.Event()
                log_info(f"任务 {task_id} 已注册到取消管理器", "task_resume")
                return True


# 全局单例实例
task_cancel_manager = TaskCancelManager()

