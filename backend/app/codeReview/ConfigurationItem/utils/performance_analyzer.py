"""
性能分析器
用于统计代码审查流程中每个步骤的耗时，帮助识别性能瓶颈
"""
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager
from .logger import log_info, log_debug, log_warning, log_error

class PerformanceStep:
    """性能步骤记录"""
    def __init__(self, step_name: str, parent_step: str = None):
        self.step_name = step_name
        self.parent_step = parent_step
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.sub_steps: List['PerformanceStep'] = []
        self.metadata: Dict[str, Any] = {}
        
    def start(self):
        """开始计时"""
        self.start_time = time.perf_counter()
        
    def end(self):
        """结束计时"""
        if self.start_time is None:
            raise ValueError(f"Step {self.step_name} was not started")
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        
    def add_metadata(self, key: str, value: Any):
        """添加元数据"""
        self.metadata[key] = value
        
    def get_duration_ms(self) -> float:
        """获取持续时间（毫秒）"""
        return self.duration * 1000 if self.duration else 0
        
    def get_duration_str(self) -> str:
        """获取格式化的持续时间字符串"""
        if self.duration is None:
            return "未完成"
        
        if self.duration < 1:
            return f"{self.duration * 1000:.2f}ms"
        elif self.duration < 60:
            return f"{self.duration:.2f}s"
        else:
            minutes = int(self.duration // 60)
            seconds = self.duration % 60
            return f"{minutes}m{seconds:.2f}s"

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self._thread_local = threading.local()
        
    def _get_current_session(self) -> Dict[str, Any]:
        """获取当前线程的会话数据"""
        if not hasattr(self._thread_local, 'session'):
            self._thread_local.session = {
                'steps': [],
                'step_stack': [],
                'task_id': None,
                'file_id': None,
                'session_start_time': time.perf_counter()
            }
        return self._thread_local.session
    
    def start_session(self, task_id: int, file_id: int):
        """开始一个新的性能分析会话"""
        session = self._get_current_session()
        session['task_id'] = task_id
        session['file_id'] = file_id
        session['session_start_time'] = time.perf_counter()
        session['steps'] = []
        session['step_stack'] = []
        
        log_info(f"开始性能分析会话 - task_id: {task_id}, file_id: {file_id}", "performance_analyzer")
    
    def start_step(self, step_name: str, **metadata) -> PerformanceStep:
        """开始一个新的性能步骤"""
        session = self._get_current_session()
        
        parent_step = session['step_stack'][-1] if session['step_stack'] else None
        step = PerformanceStep(step_name, parent_step.step_name if parent_step else None)
        
        # 添加元数据
        for key, value in metadata.items():
            step.add_metadata(key, value)
            
        step.start()
        session['step_stack'].append(step)
        
        # 如果是顶级步骤，添加到步骤列表
        if parent_step is None:
            session['steps'].append(step)
        else:
            parent_step.sub_steps.append(step)
            
        log_debug(f"开始步骤: {step_name}", "performance_analyzer")
        return step
    
    def end_step(self, step_name: str = None) -> Optional[PerformanceStep]:
        """结束当前步骤"""
        session = self._get_current_session()
        
        if not session['step_stack']:
            log_warning("没有正在进行的步骤可以结束", "performance_analyzer")
            return None
            
        step = session['step_stack'].pop()
        
        if step_name and step.step_name != step_name:
            log_warning(f"步骤名称不匹配: 期望 {step_name}, 实际 {step.step_name}", "performance_analyzer")
            
        step.end()
        
        log_info(f"步骤完成: {step.step_name} - 耗时: {step.get_duration_str()}", "performance_analyzer")
        
        # 记录详细的步骤信息
        metadata_str = ", ".join([f"{k}={v}" for k, v in step.metadata.items()]) if step.metadata else ""
        if metadata_str:
            log_debug(f"步骤元数据: {step.step_name} - {metadata_str}", "performance_analyzer")
            
        return step
    
    @contextmanager
    def measure_step(self, step_name: str, **metadata):
        """上下文管理器，自动测量步骤耗时"""
        step = self.start_step(step_name, **metadata)
        try:
            yield step
        finally:
            self.end_step(step_name)
    
    def add_step_metadata(self, key: str, value: Any):
        """为当前步骤添加元数据"""
        session = self._get_current_session()
        if session['step_stack']:
            session['step_stack'][-1].add_metadata(key, value)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话性能摘要"""
        session = self._get_current_session()
        
        total_duration = time.perf_counter() - session['session_start_time']
        
        summary = {
            'task_id': session.get('task_id'),
            'file_id': session.get('file_id'),
            'total_duration': total_duration,
            'total_duration_str': self._format_duration(total_duration),
            'steps': []
        }
        
        for step in session['steps']:
            summary['steps'].append(self._step_to_dict(step))
            
        return summary
    
    def _step_to_dict(self, step: PerformanceStep) -> Dict[str, Any]:
        """将步骤转换为字典格式"""
        step_dict = {
            'name': step.step_name,
            'duration': step.duration,
            'duration_str': step.get_duration_str(),
            'metadata': step.metadata.copy(),
            'sub_steps': []
        }
        
        for sub_step in step.sub_steps:
            step_dict['sub_steps'].append(self._step_to_dict(sub_step))
            
        return step_dict
    
    def _format_duration(self, duration: float) -> str:
        """格式化持续时间"""
        if duration < 1:
            return f"{duration * 1000:.2f}ms"
        elif duration < 60:
            return f"{duration:.2f}s"
        else:
            minutes = int(duration // 60)
            seconds = duration % 60
            return f"{minutes}m{seconds:.2f}s"
    
    def log_session_summary(self):
        """记录会话性能摘要到日志"""
        summary = self.get_session_summary()
        
        log_info("=" * 60, "performance_summary")
        log_info(f"性能分析摘要 - Task ID: {summary['task_id']}, File ID: {summary['file_id']}", "performance_summary")
        log_info(f"总耗时: {summary['total_duration_str']}", "performance_summary")
        log_info("=" * 60, "performance_summary")
        
        self._log_steps(summary['steps'], indent=0)
        
        # 分析性能瓶颈
        self._analyze_bottlenecks(summary['steps'])
        
        log_info("=" * 60, "performance_summary")
    
    def _log_steps(self, steps: List[Dict[str, Any]], indent: int = 0):
        """递归记录步骤信息"""
        for step in steps:
            indent_str = "  " * indent
            duration_str = step['duration_str']
            
            # 根据耗时添加标记
            if step['duration'] and step['duration'] > 10:  # 超过10秒
                duration_str += " ⚠️"
            elif step['duration'] and step['duration'] > 30:  # 超过30秒
                duration_str += " 🔥"
                
            log_info(f"{indent_str}├─ {step['name']}: {duration_str}", "performance_summary")
            
            # 记录元数据
            if step['metadata']:
                for key, value in step['metadata'].items():
                    log_debug(f"{indent_str}│  └─ {key}: {value}", "performance_summary")
            
            # 递归记录子步骤
            if step['sub_steps']:
                self._log_steps(step['sub_steps'], indent + 1)
    
    def _analyze_bottlenecks(self, steps: List[Dict[str, Any]]):
        """分析性能瓶颈"""
        all_steps = []
        self._flatten_steps(steps, all_steps)
        
        # 按耗时排序
        all_steps.sort(key=lambda x: x['duration'] or 0, reverse=True)
        
        log_info("性能瓶颈分析:", "performance_summary")
        
        # 显示耗时最长的前5个步骤
        top_steps = all_steps[:5]
        for i, step in enumerate(top_steps, 1):
            if step['duration'] and step['duration'] > 1:  # 只显示超过1秒的步骤
                log_info(f"  {i}. {step['name']}: {step['duration_str']}", "performance_summary")
                
                # 显示相关元数据
                if step['metadata']:
                    relevant_metadata = {}
                    for key, value in step['metadata'].items():
                        if key in ['function_count', 'file_count', 'token_count', 'prompt_length']:
                            relevant_metadata[key] = value
                    if relevant_metadata:
                        metadata_str = ", ".join([f"{k}={v}" for k, v in relevant_metadata.items()])
                        log_info(f"     相关数据: {metadata_str}", "performance_summary")
        
        # 提供优化建议
        self._provide_optimization_suggestions(all_steps)
    
    def _flatten_steps(self, steps: List[Dict[str, Any]], result: List[Dict[str, Any]]):
        """将嵌套的步骤扁平化"""
        for step in steps:
            result.append(step)
            if step['sub_steps']:
                self._flatten_steps(step['sub_steps'], result)
    
    def _provide_optimization_suggestions(self, steps: List[Dict[str, Any]]):
        """提供优化建议"""
        suggestions = []
        
        # 检查AI调用耗时
        ai_steps = [s for s in steps if 'ai' in s['name'].lower() and s['duration'] and s['duration'] > 5]
        if ai_steps:
            total_ai_time = sum(s['duration'] for s in ai_steps)
            suggestions.append(f"AI调用耗时较长 ({self._format_duration(total_ai_time)})，考虑：")
            suggestions.append("  - 优化提示词长度")
            suggestions.append("  - 使用更快的模型")
            suggestions.append("  - 实现批量处理")
        
        # 检查文件解析耗时
        parse_steps = [s for s in steps if any(keyword in s['name'].lower() for keyword in ['parse', 'extract', 'analyze']) and s['duration'] and s['duration'] > 3]
        if parse_steps:
            suggestions.append("代码解析耗时较长，考虑：")
            suggestions.append("  - 缓存解析结果")
            suggestions.append("  - 并行处理文件")
            suggestions.append("  - 优化tree-sitter使用")
        
        # 检查数据库操作耗时
        db_steps = [s for s in steps if any(keyword in s['name'].lower() for keyword in ['database', 'save', 'create']) and s['duration'] and s['duration'] > 2]
        if db_steps:
            suggestions.append("数据库操作耗时较长，考虑：")
            suggestions.append("  - 使用批量插入")
            suggestions.append("  - 优化数据库索引")
            suggestions.append("  - 减少事务提交频率")
        
        if suggestions:
            log_info("优化建议:", "performance_summary")
            for suggestion in suggestions:
                log_info(f"  {suggestion}", "performance_summary")
    
    def clear_session(self):
        """清除当前会话数据"""
        if hasattr(self._thread_local, 'session'):
            delattr(self._thread_local, 'session')

# 全局性能分析器实例
performance_analyzer = PerformanceAnalyzer() 