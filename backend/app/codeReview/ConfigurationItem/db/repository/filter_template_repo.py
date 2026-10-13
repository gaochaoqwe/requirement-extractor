"""
全局过滤规则模板仓库
负责模板的CRUD操作
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.filter_template import FilterRuleTemplate
from datetime import datetime

# 导入统一的日志系统
from ...utils.logger import log_debug, log_info, log_error


class FilterTemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self,
        template_name: str,
        keywords: List[str],
        logic_type: str = 'AND',
        description: Optional[str] = None,
        is_system: bool = False,
        sort_order: int = 0
    ) -> FilterRuleTemplate:
        """创建过滤规则模板"""
        try:
            log_debug(f"创建过滤规则模板: name={template_name}, keywords={keywords}", "filter_template_repo")
            
            template = FilterRuleTemplate(
                template_name=template_name,
                keywords=keywords,
                logic_type=logic_type,
                description=description,
                is_system=is_system,
                sort_order=sort_order
            )
            
            self.db.add(template)
            self.db.flush()
            log_debug(f"过滤规则模板创建成功，ID: {template.id}", "filter_template_repo")
            return template
        except Exception as e:
            log_error(f"创建过滤规则模板时出错", "filter_template_repo", e)
            raise

    def get_template_by_id(self, template_id: int) -> Optional[FilterRuleTemplate]:
        """根据ID获取模板"""
        return self.db.query(FilterRuleTemplate).filter(FilterRuleTemplate.id == template_id).first()

    def get_all_templates(self, include_system: bool = True) -> List[FilterRuleTemplate]:
        """获取所有模板"""
        query = self.db.query(FilterRuleTemplate)
        if not include_system:
            query = query.filter(FilterRuleTemplate.is_system == False)
        return query.order_by(FilterRuleTemplate.sort_order, FilterRuleTemplate.id).all()

    def get_system_templates(self) -> List[FilterRuleTemplate]:
        """获取系统预设模板"""
        return self.db.query(FilterRuleTemplate).filter(
            FilterRuleTemplate.is_system == True
        ).order_by(FilterRuleTemplate.sort_order, FilterRuleTemplate.id).all()

    def update_template(self, template_id: int, update_data: Dict[str, Any]) -> Optional[FilterRuleTemplate]:
        """更新模板"""
        template = self.get_template_by_id(template_id)
        if template:
            # 系统模板不允许修改某些字段
            if template.is_system:
                # 只允许修改 sort_order
                if 'sort_order' in update_data:
                    template.sort_order = update_data['sort_order']
            else:
                for key, value in update_data.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
            template.updated_at = datetime.utcnow()
            self.db.flush()
        return template

    def delete_template(self, template_id: int) -> bool:
        """删除模板（系统模板不允许删除）"""
        template = self.get_template_by_id(template_id)
        if template:
            if template.is_system:
                raise ValueError("系统预设模板不能删除")
            self.db.delete(template)
            self.db.flush()
            return True
        return False

    def copy_template_to_task(
        self,
        template_id: int,
        task_id: int
    ) -> 'ProblemFilterRule':
        """
        将模板复制为任务的过滤规则
        
        Args:
            template_id: 模板ID
            task_id: 任务ID
        
        Returns:
            创建的过滤规则
        """
        from .problem_filter_repo import ProblemFilterRepository
        from ..models.problem_filter import ProblemFilterRule
        
        template = self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        # 创建过滤规则
        filter_repo = ProblemFilterRepository(self.db)
        filter_rule = filter_repo.create_filter(
            task_id=task_id,
            filter_name=template.template_name,
            keywords=template.keywords,
            logic_type=template.logic_type,
            template_id=template_id,
            is_enabled=True
        )
        
        return filter_rule

    def copy_all_templates_to_task(self, task_id: int) -> List['ProblemFilterRule']:
        """
        将所有系统模板复制到任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            创建的过滤规则列表
        """
        templates = self.get_system_templates()
        rules = []
        
        for template in templates:
            try:
                rule = self.copy_template_to_task(template.id, task_id)
                rules.append(rule)
            except Exception as e:
                log_error(f"复制模板 {template.id} 到任务 {task_id} 失败", "filter_template_repo", e)
        
        return rules
