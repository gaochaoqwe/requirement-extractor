"""
回归测试函数配对模型

用于保存旧版本函数与新版本函数的配对关系，以及变更类型和相似度。
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.orm import relationship

from ..database import Base


class RegressionFunctionPair(Base):
    __tablename__ = 'regression_test_function_pairs'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('regression_test_tasks.id', ondelete='CASCADE'), nullable=False)

    old_function_id = Column(Integer, ForeignKey('regression_test_functions.id', ondelete='SET NULL'), nullable=True)
    new_function_id = Column(Integer, ForeignKey('regression_test_functions.id', ondelete='SET NULL'), nullable=True)

    change_type = Column(String(20), nullable=False)
    similarity_score = Column(Float, nullable=True)
    should_review = Column(Boolean, default=True, nullable=False)

    diff_summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    task = relationship('AnalysisTask', foreign_keys=[task_id])
    old_function = relationship('AnalysisFunction', foreign_keys=[old_function_id])
    new_function = relationship('AnalysisFunction', foreign_keys=[new_function_id])

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'old_function_id': self.old_function_id,
            'new_function_id': self.new_function_id,
            'change_type': self.change_type,
            'similarity_score': self.similarity_score,
            'should_review': self.should_review,
            'diff_summary': self.diff_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
