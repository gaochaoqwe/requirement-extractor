"""
函数配对仓库
"""

from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from ..models.function_pair import RegressionFunctionPair


class FunctionPairRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_pair(self, pair_data: Dict[str, Any]) -> RegressionFunctionPair:
        pair = RegressionFunctionPair(**pair_data)
        self.db.add(pair)
        self.db.commit()
        self.db.refresh(pair)
        return pair

    def batch_create_pairs(self, pairs_data: List[Dict[str, Any]]) -> List[RegressionFunctionPair]:
        pairs = [RegressionFunctionPair(**data) for data in pairs_data]
        self.db.bulk_save_objects(pairs)
        self.db.commit()
        return pairs

    def get_pair(self, pair_id: int) -> Optional[RegressionFunctionPair]:
        return self.db.query(RegressionFunctionPair).filter(RegressionFunctionPair.id == pair_id).first()

    def get_pairs_by_task(self, task_id: int) -> List[RegressionFunctionPair]:
        return (
            self.db.query(RegressionFunctionPair)
            .filter(RegressionFunctionPair.task_id == task_id)
            .order_by(RegressionFunctionPair.id)
            .all()
        )
