from sqlalchemy.orm import Session
from typing import List, Optional
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.app.databaseManage.dynamicDatabaseManage.db import models
except ImportError:
    try:
        from . import models
    except ImportError:
        try:
            import models
        except ImportError:
            print("警告: 无法导入models模块")
            models = None

# 软件类别排序映射
CATEGORY_ORDER_MAP = {
    "通用": 1,
    "主控": 2,
    "随动/主控": 3,
    "图像/主控": 4,
    "红外/主控": 5,
    "激光/主控": 6,
    "手柄": 7,
    "分色滤光": 8,
    "分色虑光": 8,
}

# 七列表模型映射（多Sheet）
MODEL_MAP = {
    "转塔": getattr(models, "TurretRequirement", None),
    "对抗告警": getattr(models, "CountermeasureAlarmRequirement", None),
    "光雷": getattr(models, "OptoRadarRequirement", None),
    "吊舱": getattr(models, "PodRequirement", None),
}

# ======================== 通用工具（针对七列表各模型） ========================
def get_max_item_order_by_category_model(db: Session, model, software_category: str) -> int:
    """获取任意模型在指定软件类别下的最大 item_order 值"""
    try:
        result = db.query(model.item_order).filter(
            model.software_category == software_category
        ).order_by(model.item_order.desc()).first()
        return result[0] if result else 0
    except Exception:
        return 0


def delete_all_by_model(db: Session, model) -> int:
    """删除指定模型下的所有记录，返回删除数量"""
    count = db.query(model).count()
    db.query(model).delete()
    db.commit()
    return count


def create_row_with_order(db: Session, model, data: dict):
    """创建单行记录：增量导入时添加到所有记录的末尾，保持全局顺序"""
    category = data.get("software_category")
    category_order = CATEGORY_ORDER_MAP.get(category, 999)
    
    # 🚀 修复：获取全局最大item_order，确保新记录添加到末尾
    max_existing_order = db.query(model.item_order).order_by(model.item_order.desc()).first()
    item_order = (max_existing_order[0] if max_existing_order and max_existing_order[0] else 0) + 1

    # 🚀 优化: 创建数据副本，移除Excel行号等临时信息
    data_copy = {k: v for k, v in data.items() if not k.startswith("_")}

    obj = model(
        **data_copy,
        category_order=category_order,
        item_order=item_order,
    )
    db.add(obj)
    db.flush()  # 获取自增ID
    return obj


def create_batch_by_model(db: Session, model, rows: List[dict]) -> int:
    """批量创建：严格保持Excel原始顺序，返回创建数量"""
    if not rows:
        return 0

    # 🚀 修复1: 按Excel原始行号排序，保持表单中的顺序
    sorted_rows = sorted(rows, key=lambda x: x.get("_excel_row_number", 0))
    
    # 🚀 修复2: 获取当前数据库中的最大item_order值（用于增量导入）
    # 但对于全量导入，表应该已经被清空，所以从1开始
    max_existing_order = db.query(model.item_order).order_by(model.item_order.desc()).first()
    starting_order = (max_existing_order[0] if max_existing_order and max_existing_order[0] else 0)

    # 🚀 修复3: 按Excel顺序依次分配item_order，不按类别重新分组
    created = 0
    
    for i, r in enumerate(sorted_rows):
        cat = r.get("software_category")
        category_order = CATEGORY_ORDER_MAP.get(cat, 999)
        
        # 🚀 关键修复：按Excel顺序分配item_order，保持原始顺序
        item_order = starting_order + i + 1
        
        # 创建数据副本，移除Excel行号信息
        data_copy = {k: v for k, v in r.items() if not k.startswith("_")}
        
        obj = model(
            **data_copy,
            category_order=category_order,
            item_order=item_order,
        )
        db.add(obj)
        created += 1
        
    db.commit()
    return created


def exists_row(db: Session, model, *, test_item_name: str, test_content: Optional[str], test_method: Optional[str]) -> bool:
    """判重：以 测试项名称 + 测试内容 + 测试方法 全等来判断是否存在"""
    q = db.query(model).filter(model.test_item_name == test_item_name)
    # 允许 None 的等值判断
    if test_content is None:
        q = q.filter(model.test_content.is_(None))
    else:
        q = q.filter(model.test_content == test_content)

    if test_method is None:
        q = q.filter(model.test_method.is_(None))
    else:
        q = q.filter(model.test_method == test_method)

    return db.query(q.exists()).scalar()


def query_by_model(
    db: Session,
    model,
    *,
    skip: int = 0,
    limit: int = 50,
    software_category: Optional[str] = None,
    test_item_name: Optional[str] = None,
):
    """按模型查询，支持按 software_category 和 test_item_name 模糊筛选，并按导入顺序(item_order)排序"""
    q = db.query(model)
    if software_category:
        q = q.filter(model.software_category.contains(software_category))
    if test_item_name:
        q = q.filter(model.test_item_name.contains(test_item_name))
    # 🚀 修复：只按item_order排序，保持导入时的Excel原始顺序
    q = q.order_by(model.item_order)
    return q.offset(skip).limit(limit).all()


def count_by_model(db: Session, model, *, software_category: Optional[str] = None, test_item_name: Optional[str] = None) -> int:
    """按模型计数，可选软件类别和测试项名称筛选"""
    q = db.query(model)
    if software_category:
        q = q.filter(model.software_category.contains(software_category))
    if test_item_name:
        q = q.filter(model.test_item_name.contains(test_item_name))
    return q.count()

def get_category_order(category: str) -> int:
    return CATEGORY_ORDER_MAP.get(category, 999)


def get_requirement(db: Session, requirement_id: int) -> Optional[models.OptoelectronicRequirement]:
    """根据ID获取单个需求记录"""
    return db.query(models.OptoelectronicRequirement).filter(
        models.OptoelectronicRequirement.id == requirement_id
    ).first()


def get_requirements(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    software_category: Optional[str] = None
) -> List[models.OptoelectronicRequirement]:
    """获取需求记录列表，支持分页和按软件类别筛选，自动排序"""
    query = db.query(models.OptoelectronicRequirement)
    
    if software_category:
        query = query.filter(models.OptoelectronicRequirement.software_category.contains(software_category))
    
    # 按软件类别和测试项排序
    query = query.order_by(
        models.OptoelectronicRequirement.category_order,
        models.OptoelectronicRequirement.item_order
    )
    
    return query.offset(skip).limit(limit).all()


def get_requirements_count(
    db: Session,
    software_category: Optional[str] = None
) -> int:
    """获取需求记录总数"""
    query = db.query(models.OptoelectronicRequirement)
    
    if software_category:
        query = query.filter(models.OptoelectronicRequirement.software_category.contains(software_category))
    
    return query.count()


def get_max_item_order_by_category(db: Session, software_category: str) -> int:
    """获取指定软件类别下的最大测试项排序值"""
    result = db.query(models.OptoelectronicRequirement.item_order).filter(
        models.OptoelectronicRequirement.software_category == software_category
    ).order_by(models.OptoelectronicRequirement.item_order.desc()).first()
    
    return result[0] if result else 0


def create_requirement(
    db: Session, 
    requirement_data: dict
) -> models.OptoelectronicRequirement:
    """创建新的需求记录，自动设置排序值"""
    # 设置软件类别排序
    category_order = CATEGORY_ORDER_MAP.get(requirement_data.get("software_category"), 999)
    
    # 设置测试项排序
    max_item_order = get_max_item_order_by_category(db, requirement_data.get("software_category"))
    item_order = max_item_order + 1
    
    db_requirement = models.OptoelectronicRequirement(
        **requirement_data,
        category_order=category_order,
        item_order=item_order
    )
    db.add(db_requirement)
    db.commit()
    db.refresh(db_requirement)
    return db_requirement


def create_requirements_batch(
    db: Session, 
    requirements: List[dict]
) -> List[models.OptoelectronicRequirement]:
    """批量创建需求记录，自动设置排序值"""
    db_requirements = []
    
    # 按软件类别分组，为每个类别设置正确的排序值
    category_items = {}
    for req in requirements:
        category = req.get("software_category")
        if category not in category_items:
            category_items[category] = []
        category_items[category].append(req)
    
    for category, items in category_items.items():
        category_order = CATEGORY_ORDER_MAP.get(category, 999)
        max_item_order = get_max_item_order_by_category(db, category)
        
        for i, req in enumerate(items):
            item_order = max_item_order + i + 1
            db_requirement = models.OptoelectronicRequirement(
                **req,
                category_order=category_order,
                item_order=item_order
            )
            db.add(db_requirement)
            db_requirements.append(db_requirement)
    
    db.commit()
    for db_requirement in db_requirements:
        db.refresh(db_requirement)
    
    return db_requirements


def update_requirement(
    db: Session, 
    requirement_id: int, 
    requirement_update: dict
) -> Optional[models.OptoelectronicRequirement]:
    """更新需求记录"""
    db_requirement = get_requirement(db, requirement_id)
    if not db_requirement:
        return None
    
    # 如果软件类别发生变化，需要重新计算排序值
    if 'software_category' in requirement_update:
        new_category = requirement_update['software_category']
        new_category_order = CATEGORY_ORDER_MAP.get(new_category, 999)
        requirement_update['category_order'] = new_category_order
        
        # 重新计算测试项排序
        max_item_order = get_max_item_order_by_category(db, new_category)
        requirement_update['item_order'] = max_item_order + 1
    
    for field, value in requirement_update.items():
        setattr(db_requirement, field, value)
    
    db.commit()
    db.refresh(db_requirement)
    return db_requirement


def delete_requirement(db: Session, requirement_id: int) -> bool:
    """删除需求记录"""
    db_requirement = get_requirement(db, requirement_id)
    if not db_requirement:
        return False
    
    db.delete(db_requirement)
    db.commit()
    return True


def delete_all_requirements(db: Session) -> int:
    """删除所有需求记录，返回删除的数量"""
    count = db.query(models.OptoelectronicRequirement).count()
    db.query(models.OptoelectronicRequirement).delete()
    db.commit()
    return count


def find_matching_requirement(
    db: Session, 
    test_item_name: str
) -> Optional[models.OptoelectronicRequirement]:
    """根据测试项名称进行模糊匹配"""
    return db.query(models.OptoelectronicRequirement).filter(
        models.OptoelectronicRequirement.test_item_name.contains(test_item_name)
    ).first()


def append_test_content_and_method(
    db: Session,
    requirement_id: int,
    new_test_content: str,
    new_test_method: str
) -> Optional[models.OptoelectronicRequirement]:
    """追加测试内容和测试方法到现有记录"""
    db_requirement = get_requirement(db, requirement_id)
    if not db_requirement:
        return None
    
    # 追加测试内容
    if db_requirement.test_item_description:
        # 计算新的序号
        existing_lines = db_requirement.test_item_description.split('\n')
        max_number = 0
        for line in existing_lines:
            if line.strip() and '、' in line:
                try:
                    num = int(line.split('、')[0])
                    max_number = max(max_number, num)
                except:
                    pass
        
        new_number = max_number + 1
        db_requirement.test_item_description += f"\n{new_number}、{new_test_content}"
    else:
        db_requirement.test_item_description = f"1、{new_test_content}"
    
    # 追加测试方法
    if db_requirement.test_method:
        # 计算新的序号
        existing_lines = db_requirement.test_method.split('\n')
        max_number = 0
        for line in existing_lines:
            if line.strip() and '、' in line:
                try:
                    num = int(line.split('、')[0])
                    max_number = max(max_number, num)
                except:
                    pass
        
        new_number = max_number + 1
        db_requirement.test_method += f"\n{new_number}、{new_test_method}"
    else:
        db_requirement.test_method = f"1、{new_test_method}"
    
    db.commit()
    db.refresh(db_requirement)
    return db_requirement


def get_requirements_by_category_sorted(db: Session) -> List[models.OptoelectronicRequirement]:
    """获取按软件类别排序的所有需求记录"""
    return db.query(models.OptoelectronicRequirement).order_by(
        models.OptoelectronicRequirement.category_order,
        models.OptoelectronicRequirement.item_order
    ).all() 