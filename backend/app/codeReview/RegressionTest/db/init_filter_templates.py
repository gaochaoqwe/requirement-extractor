"""
初始化全局过滤规则模板
从 过滤策略.md 导入系统预设规则
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.codeReview.RegressionTest.db.database import SessionLocal
from backend.app.codeReview.RegressionTest.db.repository.filter_template_repo import FilterTemplateRepository
from backend.app.codeReview.RegressionTest.utils.logger import log_info, log_error


# 系统预设规则（基于 过滤策略.md）
SYSTEM_FILTER_RULES = [
    {
        'template_name': '数组可能问题',
        'keywords': ['数组', '可能'],
        'logic_type': 'AND',
        'description': '过滤掉问题原因中同时包含"数组"和"可能"的问题',
        'sort_order': 1
    },
    {
        'template_name': 'memcpy/memset可能问题',
        'keywords': ['memcpy', 'memset', '可能'],
        'logic_type': 'AND',
        'description': '过滤掉问题原因中包含"memcpy"或"memset"且包含"可能"的问题',
        'sort_order': 2
    },
    {
        'template_name': '指针可能问题',
        'keywords': ['指针', '可能'],
        'logic_type': 'AND',
        'description': '过滤掉问题原因中同时包含"指针"和"可能"的问题',
        'sort_order': 3
    },
    {
        'template_name': '未初始化可能问题',
        'keywords': ['未初始化', '可能'],
        'logic_type': 'AND',
        'description': '过滤掉问题原因中同时包含"未初始化"和"可能"的问题',
        'sort_order': 4
    },
    {
        'template_name': '潜在未定义问题',
        'keywords': ['潜在', '未定义'],
        'logic_type': 'AND',
        'description': '过滤掉问题原因中同时包含"潜在"和"未定义"的问题',
        'sort_order': 5
    },
    {
        'template_name': '硬编码或魔法数字',
        'keywords': ['硬编码', '魔法数字'],
        'logic_type': 'OR',
        'description': '过滤掉问题原因中包含"硬编码"或"魔法数字"的问题',
        'sort_order': 6
    },
    {
        'template_name': '浮点数溢出或精度损失',
        'keywords': ['浮点数溢出', '精度损失'],
        'logic_type': 'OR',
        'description': '过滤掉问题原因中包含"浮点数溢出"或"精度损失"的问题',
        'sort_order': 7
    },
    {
        'template_name': '缺少注释',
        'keywords': ['缺少注释'],
        'logic_type': 'AND',
        'description': '过滤掉问题原因中包含"缺少注释"的问题',
        'sort_order': 8
    }
]


def init_system_filter_templates():
    """初始化系统预设过滤规则模板"""
    db = SessionLocal()
    try:
        template_repo = FilterTemplateRepository(db)
        
        # 检查是否已经初始化过
        existing_templates = template_repo.get_system_templates()
        if existing_templates:
            log_info(f"系统过滤规则模板已存在（共{len(existing_templates)}条），跳过初始化", "init_filter_templates")
            return
        
        # 创建系统模板
        created_count = 0
        for rule_data in SYSTEM_FILTER_RULES:
            try:
                template = template_repo.create_template(
                    template_name=rule_data['template_name'],
                    keywords=rule_data['keywords'],
                    logic_type=rule_data['logic_type'],
                    description=rule_data['description'],
                    is_system=True,
                    sort_order=rule_data['sort_order']
                )
                created_count += 1
                log_info(f"创建系统模板: {template.template_name}", "init_filter_templates")
            except Exception as e:
                log_error(f"创建系统模板失败: {rule_data['template_name']}", "init_filter_templates", e)
        
        db.commit()
        log_info(f"系统过滤规则模板初始化完成，共创建 {created_count} 条规则", "init_filter_templates")
        
    except Exception as e:
        db.rollback()
        log_error("初始化系统过滤规则模板失败", "init_filter_templates", e)
        raise
    finally:
        db.close()


def reset_system_filter_templates():
    """重置系统预设过滤规则模板（慎用）"""
    db = SessionLocal()
    try:
        from backend.app.codeReview.RegressionTest.db.models.filter_template import FilterRuleTemplate
        
        # 删除所有系统模板
        deleted = db.query(FilterRuleTemplate).filter(
            FilterRuleTemplate.is_system == True
        ).delete()
        db.commit()
        
        log_info(f"删除了 {deleted} 条系统模板", "init_filter_templates")
        
        # 重新初始化
        init_system_filter_templates()
        
    except Exception as e:
        db.rollback()
        log_error("重置系统过滤规则模板失败", "init_filter_templates", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("开始初始化系统过滤规则模板...")
    init_system_filter_templates()
    print("初始化完成！")
