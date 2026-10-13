"""
功能点审查数据访问层
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from ..models.feature_problem import Feature, FeatureReviewProblem

logger = logging.getLogger(__name__)


class FeatureRepository:
    """功能点数据访问类"""
    
    def __init__(self, db: Session):
        self.db = db
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """确保数据库表包含最新的列（兼容旧版本数据库）"""
        try:
            result = self.db.execute(text("PRAGMA table_info(features)")).fetchall()
            column_names = set()
            for row in result:
                # row 结构: (cid, name, type, notnull, dflt_value, pk)
                if isinstance(row, tuple) and len(row) > 1:
                    column_names.add(row[1])
                elif hasattr(row, "_mapping"):
                    column_names.add(row._mapping.get("name"))
            if "call_chain" not in column_names:
                logger.debug("[FeatureRepository] call_chain 列缺失，自动补充...")
                self.db.execute(text("ALTER TABLE features ADD COLUMN call_chain TEXT"))
                self.db.commit()
                logger.info("[FeatureRepository] 已为 features 表添加 call_chain 列")
        except Exception as exc:
            logger.warning("[FeatureRepository] Schema ensure failed: %s", exc)
            self.db.rollback()
    
    def create_feature(self, feature_data: Dict[str, Any]) -> Feature:
        """创建功能点"""
        feature = Feature(**feature_data)
        self.db.add(feature)
        self.db.commit()
        self.db.refresh(feature)
        return feature
    
    def get_feature(self, feature_id: int) -> Optional[Feature]:
        """获取功能点"""
        return self.db.query(Feature).filter(Feature.id == feature_id).first()
    
    def get_features_by_task(self, task_id: int) -> List[Feature]:
        """获取任务的所有功能点"""
        return self.db.query(Feature).filter(
            Feature.task_id == task_id
        ).order_by(Feature.id).all()
    
    def update_feature(self, feature_id: int, feature_data: Dict[str, Any]) -> Optional[Feature]:
        """更新功能点"""
        feature = self.get_feature(feature_id)
        if feature:
            for key, value in feature_data.items():
                if hasattr(feature, key):
                    setattr(feature, key, value)
            self.db.commit()
            self.db.refresh(feature)
        return feature
    
    def delete_feature(self, feature_id: int) -> bool:
        """删除功能点"""
        feature = self.get_feature(feature_id)
        if feature:
            self.db.delete(feature)
            self.db.commit()
            return True
        return False


class FeatureReviewProblemRepository:
    """功能点审查问题数据访问类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _ensure_schema(self):
        """确保表结构存在"""
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.db.bind)
            if not inspector.has_table('feature_review_problems'):
                from ...db.models.feature_problem import Base
                Base.metadata.create_all(bind=self.db.bind, tables=[FeatureReviewProblem.__table__])
        except Exception as e:
            # 表可能已存在或正在创建中，忽略错误
            print(f"[FeatureReviewProblemRepository] _ensure_schema warning: {e}")
            pass
    
    def create_problem(self, problem_data: Dict[str, Any]) -> FeatureReviewProblem:
        """创建功能点审查问题"""
        problem = FeatureReviewProblem(**problem_data)
        self.db.add(problem)
        self.db.commit()
        self.db.refresh(problem)
        return problem
    
    def get_problem(self, problem_id: int) -> Optional[FeatureReviewProblem]:
        """获取问题"""
        return self.db.query(FeatureReviewProblem).filter(
            FeatureReviewProblem.id == problem_id
        ).first()
    
    def get_problems_by_feature(self, feature_id: int) -> List[FeatureReviewProblem]:
        """获取功能点的所有问题"""
        return self.db.query(FeatureReviewProblem).filter(
            FeatureReviewProblem.feature_id == feature_id
        ).order_by(FeatureReviewProblem.id).all()
    
    def get_problems_by_task(self, task_id: int) -> List[FeatureReviewProblem]:
        """获取任务的所有功能点审查问题"""
        return self.db.query(FeatureReviewProblem).filter(
            FeatureReviewProblem.task_id == task_id
        ).order_by(desc(FeatureReviewProblem.issue_level), FeatureReviewProblem.id).all()
    
    def update_problem(self, problem_id: int, problem_data: Dict[str, Any]) -> Optional[FeatureReviewProblem]:
        """更新问题"""
        problem = self.get_problem(problem_id)
        if problem:
            for key, value in problem_data.items():
                if hasattr(problem, key):
                    setattr(problem, key, value)
            self.db.commit()
            self.db.refresh(problem)
        return problem
    
    def delete_problem(self, problem_id: int) -> bool:
        """删除问题"""
        problem = self.get_problem(problem_id)
        if problem:
            self.db.delete(problem)
            self.db.commit()
            return True
        return False
    
    def count_by_task(self, task_id: int) -> int:
        """统计任务的功能点审查问题数量"""
        return self.db.query(FeatureReviewProblem).filter(
            FeatureReviewProblem.task_id == task_id
        ).count()

