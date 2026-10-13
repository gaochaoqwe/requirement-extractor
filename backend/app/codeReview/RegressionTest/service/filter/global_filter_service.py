"""
全局过滤规则服务
从JSON配置文件加载规则，自动应用到所有任务的问题
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ...utils.logger import log_info, log_error, log_debug


@dataclass
class FilterRule:
    """过滤规则数据类"""
    id: str
    name: str
    keywords: List[str]
    logic: str  # 'AND' 或 'OR'
    enabled: bool
    description: str


class GlobalFilterService:
    """全局过滤规则服务"""
    
    _instance = None
    _rules: List[FilterRule] = []
    _config_path: Path = None
    _auto_apply: bool = True
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化服务"""
        if not self._config_path:
            # 配置文件路径
            current_dir = Path(__file__).parent.parent.parent
            self._config_path = current_dir / "config" / "global_filter_rules.json"
            # 加载规则
            self.reload_rules()
    
    def reload_rules(self) -> bool:
        """
        重新加载过滤规则
        
        Returns:
            是否加载成功
        """
        try:
            if not self._config_path.exists():
                log_error(f"过滤规则配置文件不存在: {self._config_path}", "global_filter_service")
                return False
            
            with open(self._config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self._auto_apply = config.get('auto_apply', True)
            rules_data = config.get('rules', [])
            
            # 解析规则
            self._rules = []
            for rule_data in rules_data:
                rule = FilterRule(
                    id=rule_data.get('id'),
                    name=rule_data.get('name'),
                    keywords=rule_data.get('keywords', []),
                    logic=rule_data.get('logic', 'AND'),
                    enabled=rule_data.get('enabled', True),
                    description=rule_data.get('description', '')
                )
                self._rules.append(rule)
            
            log_info(f"成功加载 {len(self._rules)} 条全局过滤规则", "global_filter_service")
            return True
            
        except Exception as e:
            log_error("加载全局过滤规则失败", "global_filter_service", e)
            return False
    
    def get_enabled_rules(self) -> List[FilterRule]:
        """
        获取所有启用的规则
        
        Returns:
            启用的规则列表
        """
        return [rule for rule in self._rules if rule.enabled]
    
    def get_all_rules(self) -> List[FilterRule]:
        """
        获取所有规则
        
        Returns:
            所有规则列表
        """
        return self._rules.copy()
    
    def is_auto_apply(self) -> bool:
        """
        是否自动应用过滤规则
        
        Returns:
            是否自动应用
        """
        return self._auto_apply
    
    def should_filter_problem(self, problem_reason: str) -> Tuple[bool, Optional[str]]:
        """
        判断问题是否应该被过滤
        
        Args:
            problem_reason: 问题原因文本
        
        Returns:
            (是否过滤, 匹配的规则名称)
        """
        if not problem_reason:
            return False, None
        
        problem_reason_lower = problem_reason.lower()
        
        for rule in self.get_enabled_rules():
            if not rule.keywords:
                continue
            
            # 根据逻辑类型进行匹配
            if rule.logic == 'OR':
                # OR逻辑：任一关键词存在即匹配
                match = any(
                    keyword.lower() in problem_reason_lower
                    for keyword in rule.keywords
                )
            else:
                # AND逻辑：所有关键词都必须存在
                match = all(
                    keyword.lower() in problem_reason_lower
                    for keyword in rule.keywords
                )
            
            if match:
                log_debug(
                    f"问题被规则'{rule.name}'过滤: {problem_reason[:50]}...",
                    "global_filter_service"
                )
                return True, rule.name
        
        return False, None
    
    def filter_problems(self, problems: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """
        过滤问题列表
        
        Args:
            problems: 问题列表
        
        Returns:
            (保留的问题列表, 被过滤的问题列表)
        """
        if not self._auto_apply:
            return problems, []
        
        kept_problems = []
        filtered_problems = []
        
        for problem in problems:
            problem_reason = problem.get('problem_reason', '')
            should_filter, rule_name = self.should_filter_problem(problem_reason)
            
            if should_filter:
                # 添加过滤信息
                problem['filtered_by_rule'] = rule_name
                filtered_problems.append(problem)
            else:
                kept_problems.append(problem)
        
        log_info(
            f"过滤结果: 保留 {len(kept_problems)} 个问题, 过滤 {len(filtered_problems)} 个问题",
            "global_filter_service"
        )
        
        return kept_problems, filtered_problems
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        获取过滤规则统计信息
        
        Returns:
            统计信息
        """
        enabled_rules = self.get_enabled_rules()
        return {
            'total_rules': len(self._rules),
            'enabled_rules': len(enabled_rules),
            'disabled_rules': len(self._rules) - len(enabled_rules),
            'auto_apply': self._auto_apply,
            'config_path': str(self._config_path),
            'rules': [
                {
                    'id': rule.id,
                    'name': rule.name,
                    'keywords': rule.keywords,
                    'logic': rule.logic,
                    'enabled': rule.enabled
                }
                for rule in self._rules
            ]
        }


# 全局单例实例
_global_filter_service = GlobalFilterService()


def get_global_filter_service() -> GlobalFilterService:
    """
    获取全局过滤服务实例
    
    Returns:
        全局过滤服务实例
    """
    return _global_filter_service
