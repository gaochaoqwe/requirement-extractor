"""
智能表单导入服务
1) 对上传表的前两列(软件类别, 测试项名称)进行局部匹配
2) 未强匹配项，调用AI进行批量判重/入库建议
3) 返回前端可确认的建议，前端确认后再提交入库/列追加
"""
from __future__ import annotations

from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
import difflib
import logging
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.app.databaseManage.dynamicDatabaseManage.db import crud
    from backend.app.databaseManage.dynamicDatabaseManage.schemas import schemas
    from backend.app.databaseManage.dynamicDatabaseManage.services.openai.client import AIClient
    from backend.app.databaseManage.dynamicDatabaseManage.utils import excel_utils
except ImportError:
    try:
        from ..db import crud
        from ..schemas import schemas
        from .openai.client import AIClient
        from ..utils import excel_utils
    except ImportError:
        try:
            import crud
            import schemas
            import excel_utils
            AIClient = None
        except ImportError:
            print("警告: 无法导入必要的模块")
            crud = None
            schemas = None
            excel_utils = None
            AIClient = None

logger = logging.getLogger(__name__)


def _similar(a: str, b: str) -> float:
    """简单相似度(0~1)。"""
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _best_match(target: str, candidates: List[str]) -> Tuple[int, float]:
    """返回最佳匹配下标与相似度。若无候选，(-1,0)。"""
    if not candidates:
        return -1, 0.0
    best_idx, best_score = -1, 0.0
    for idx, c in enumerate(candidates):
        s = _similar(target, c)
        if s > best_score:
            best_idx, best_score = idx, s
    return best_idx, best_score


class IntelligentImportService:
    """智能导入核心逻辑。"""

    @staticmethod
    def parse_excel(file_content: bytes) -> List[schemas.OptoelectronicRequirementCreate]:
        """使用已有工具解析Excel(四列)。"""
        return excel_utils.parse_excel_file(file_content, sheet_name=None)

    @staticmethod
    def build_preview(
        db: Session,
        items: List[schemas.OptoelectronicRequirementCreate],
        strong_threshold: float = 0.86,
        weak_threshold: float = 0.72,
    ) -> List[schemas.IntelligentImportSuggestion]:
        """对每一行给出建议: 追加后两列 或 需要AI判定/新建。"""
        # 拉取现有库记录
        existing = crud.get_requirements(db=db, skip=0, limit=10000)
        names = [e.test_item_name or "" for e in existing]
        categories = [e.software_category or "" for e in existing]

        suggestions: List[schemas.IntelligentImportSuggestion] = []
        pending_ai: List[Tuple[int, schemas.OptoelectronicRequirementCreate]] = []

        for idx, it in enumerate(items):
            # 先按(类别+名称)做联合评分
            best_idx_name, score_name = _best_match(it.test_item_name, names)
            best_idx_cat, score_cat = _best_match(it.software_category, categories)

            # 若名称与类别指向同一条，提升可信度
            if best_idx_name == best_idx_cat and best_idx_name != -1:
                score = 0.6 * score_name + 0.4 * score_cat + 0.05
                matched = existing[best_idx_name]
            else:
                # 退化为名称优先
                score = score_name
                matched = existing[best_idx_name] if best_idx_name != -1 else None

            if matched and score >= strong_threshold:
                # 建议：只追加后两列
                suggestions.append(
                    schemas.IntelligentImportSuggestion(
                        index=idx,
                        incoming=it,
                        suggestion_type="append_columns",
                        matched_id=matched.id,
                        matched_name=matched.test_item_name,
                        matched_category=matched.software_category,
                        confidence=round(score, 3),
                        rationale="基于(类别+名称)的强匹配，建议仅追加测试项描述与测试方法"
                    )
                )
            else:
                # 置信度不足，交给AI二判
                pending_ai.append((idx, it))

        if pending_ai:
            suggestions.extend(IntelligentImportService._ai_batch_judgement(db, pending_ai, existing))

        # 维持原始顺序
        suggestions.sort(key=lambda s: s.index)
        return suggestions

    @staticmethod
    def _ai_batch_judgement(
        db: Session,
        pending: List[Tuple[int, schemas.OptoelectronicRequirementCreate]],
        existing: List[schemas.OptoelectronicRequirement],
        batch_size: int = 15,
    ) -> List[schemas.IntelligentImportSuggestion]:
        """将待判定条目分批送给AI，返回建议。"""
        client = AIClient()

        def build_prompt(batch: List[Tuple[int, schemas.OptoelectronicRequirementCreate]]) -> str:
            preview_existing = [
                {
                    "id": e.id,
                    "software_category": e.software_category,
                    "test_item_name": e.test_item_name,
                    "test_item_description": e.test_item_description or "",
                }
                for e in existing[:120]
            ]
            incoming = [
                {
                    "index": idx,
                    "software_category": it.software_category,
                    "test_item_name": it.test_item_name,
                    "test_item_description": it.test_item_description or "",
                    "test_method": it.test_method or "",
                }
                for idx, it in batch
            ]
            instructions = (
                "你是需求库判重助手。对每个incoming与existing进行对比，判断是否应入库(create_new)或映射到已有matched_id(append_columns)。"
                "要求输出JSON: {\\n  \\\"results\\\": [\\n    {\\n      \\\"index\\\": <int>,\\n      \\\"decision\\\": \\\"append_columns\\\"|\\\"create_new\\\",\\n      \\\"matched_id\\\": <int|null>,\\n      \\\"confidence\\\": <0~1>,\\n      \\\"rationale\\\": \\\"简要理由\\\"\\n    }\\n  ]\\n}。\\n"
                "规则: 若现有库有同名或高度相似且同类别的测试项，则prefer append_columns，仅追加描述与方法；否则create_new。"
            )
            return (
                instructions
                + "\nexisting="
                + json_dumps(preview_existing)
                + "\nincoming="
                + json_dumps(incoming)
            )

        results: List[schemas.IntelligentImportSuggestion] = []
        for i in range(0, len(pending), batch_size):
            batch = pending[i : i + batch_size]
            prompt = build_prompt(batch)
            parsed, _raw = client.call_ai_stream(prompt)
            rows = (parsed or {}).get("results", []) if isinstance(parsed, dict) else []
            for row in rows:
                try:
                    decision = row.get("decision", "create_new")
                    matched_id = row.get("matched_id")
                    idx = row.get("index")
                    confidence = float(row.get("confidence", 0.5))
                    rationale = row.get("rationale", "")
                    incoming_item = dict(batch)[idx]
                    matched = None
                    matched_name = None
                    matched_category = None
                    if matched_id:
                        matched = next((e for e in existing if e.id == matched_id), None)
                        if matched:
                            matched_name = matched.test_item_name
                            matched_category = matched.software_category

                    results.append(
                        schemas.IntelligentImportSuggestion(
                            index=idx,
                            incoming=incoming_item,
                            suggestion_type="append_columns" if decision == "append_columns" else "create_new",
                            matched_id=matched_id,
                            matched_name=matched_name,
                            matched_category=matched_category,
                            confidence=round(confidence, 3),
                            rationale=rationale or ("AI判定")
                        )
                    )
                except Exception as e:
                    logger.warning(f"解析AI结果失败: {e}")
                    continue
        return results

    @staticmethod
    def preview_from_excel(
        db: Session,
        file_content: bytes,
    ) -> List[schemas.IntelligentImportSuggestion]:
        items = IntelligentImportService.parse_excel(file_content)
        return IntelligentImportService.build_preview(db, items)

    @staticmethod
    def commit(
        db: Session,
        decisions: List[schemas.IntelligentImportDecision]
    ) -> Dict[str, Any]:
        """根据前端确认结果入库。"""
        created = 0
        updated = 0
        errors: List[str] = []
        for d in decisions:
            try:
                if d.suggestion_type == "append_columns" and d.matched_id:
                    update_model = schemas.OptoelectronicRequirementUpdate(
                        test_item_description=d.incoming.test_item_description,
                        test_method=d.incoming.test_method,
                    )
                    ok = crud.update_requirement(db=db, requirement_id=d.matched_id, requirement_update=update_model)
                    if ok:
                        updated += 1
                    else:
                        errors.append(f"未找到ID={d.matched_id}")
                elif d.suggestion_type == "create_new":
                    created_obj = crud.create_requirement(db=db, requirement=d.incoming)
                    if created_obj:
                        created += 1
                    else:
                        errors.append("创建失败")
            except Exception as e:
                errors.append(str(e))

        return {"created": created, "updated": updated, "errors": errors}


# 小工具：安全dumps
def json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)
