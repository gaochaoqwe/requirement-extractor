"""
FPGA 规则查询 API
"""
from fastapi import APIRouter, Query
from typing import List, Optional, Literal, Dict, Any

from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
from app.staticAnalysis.filterFpga.database.postgresql_models import FPGARule

router = APIRouter(tags=["staticAnalysis-fpga"])


@router.get("/rules")
def list_rules(
    accuracy: Literal["accurate", "uncertain", "all"] = Query("all"),
    language: Optional[Literal["Verilog", "VHDL"]] = Query(None),
    rule_type: Optional[Literal["mandatory", "advisory"]] = Query(None),
) -> Dict[str, Any]:
    """按条件返回 FPGA 规则列表"""
    session = get_db_session()
    try:
        q = session.query(FPGARule)
        if accuracy != "all":
            q = q.filter(FPGARule.accuracy_type == accuracy)
        if language:
            q = q.filter(FPGARule.language == language)
        if rule_type:
            q = q.filter(FPGARule.rule_type == rule_type)
        q = q.order_by(FPGARule.language, FPGARule.rule_type, FPGARule.sequence)
        rows: List[FPGARule] = q.all()
        data = [
            {
                "rule_code": r.rule_code,
                "rule_name": r.rule_content,
                "rule_content": r.rule_content,
                "language": r.language,
                "rule_type": r.rule_type,
                "category": r.category,
                "chapter": r.chapter,
                "sequence": r.sequence,
                "accuracy_type": r.accuracy_type,
                "is_selected": r.is_selected if r.is_selected is not None else True,
            }
            for r in rows
        ]
        return {"items": data, "count": len(data)}
    finally:
        session.close()


@router.get("/stats")
def stats() -> Dict[str, Any]:
    """返回 FPGA 规则统计信息"""
    session = get_db_session()
    try:
        total = session.query(FPGARule).count()
        accurate = session.query(FPGARule).filter(FPGARule.accuracy_type == "accurate").count()
        uncertain = session.query(FPGARule).filter(FPGARule.accuracy_type == "uncertain").count()

        def c(lang: str, acc: Optional[str] = None, rtype: Optional[str] = None) -> int:
            q = session.query(FPGARule).filter(FPGARule.language == lang)
            if acc:
                q = q.filter(FPGARule.accuracy_type == acc)
            if rtype:
                q = q.filter(FPGARule.rule_type == rtype)
            return q.count()

        return {
            "total": total,
            "accurate": accurate,
            "uncertain": uncertain,
            "verilog": {
                "total": c("Verilog"),
                "accurate": c("Verilog", "accurate"),
                "uncertain": c("Verilog", "uncertain"),
                "mandatory": c("Verilog", rtype="mandatory"),
                "advisory": c("Verilog", rtype="advisory"),
            },
            "vhdl": {
                "total": c("VHDL"),
                "accurate": c("VHDL", "accurate"),
                "uncertain": c("VHDL", "uncertain"),
                "mandatory": c("VHDL", rtype="mandatory"),
                "advisory": c("VHDL", rtype="advisory"),
            },
        }
    finally:
        session.close()
