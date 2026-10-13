from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

from ..services.test_item_service.test_item_design.req_design_service import RequirementDesignService

router = APIRouter()


class ReqDesignInitRow(BaseModel):
    row_index: int = Field(..., description="前端表格中的行号（用于回填）")
    test_item_name: str = Field(..., description="测试项名称（N列）")
    requirement_sub_item_desc: str = Field(..., description="需求子项描述（S列）")
    template_test_item_desc: str = Field(..., description="模板/当前测试项描述（T列）")
    template_test_method: str = Field(..., description="模板/当前测试方法（U列）")


class ReqDesignInitRequest(BaseModel):
    rows: List[ReqDesignInitRow]
    session_id: Optional[str] = Field(None, description="可选，会话ID用于日志归档")


class ReqDesignInitRowResult(BaseModel):
    row_index: int
    test_item_desc: str
    test_method: str


class ReqDesignInitResponse(BaseModel):
    success: bool
    session_id: str
    results: List[ReqDesignInitRowResult]
    errors: List[Dict[str, Any]]


class ReqDesignCommonRequest(BaseModel):
    test_item_name: str = Field('', description="测试项名称（N列）")
    requirement_sub_item_desc: str = Field('', description="需求子项描述（S列）")
    test_item_desc: str = Field(..., description="当前测试项描述（T列）")
    test_method: str = Field(..., description="当前测试方法（U列）")
    variables: Dict[str, str] = Field(default_factory=dict, description="变量占位符到用户输入的映射，例如 {\"xx（...）\": \"随动/自动扫描\"}")
    session_id: Optional[str] = Field(None, description="可选，会话ID用于日志归档")


class ReqDesignCommonResponse(BaseModel):
    success: bool
    session_id: str
    test_item_desc: str
    test_method: str


class ReqDesignSelfCheckNormalizeRequest(BaseModel):
    raw_text: str = Field(..., description="用户输入的故障类别原始文本")
    session_id: Optional[str] = Field(None, description="可选，会话ID用于日志归档")


class ReqDesignSelfCheckNormalizeResponse(BaseModel):
    success: bool
    session_id: str
    normalized: str


class ReqDesignSelfCheckRequest(BaseModel):
    test_item_name: str = Field('', description="测试项名称（N列）")
    requirement_sub_item_desc: str = Field('', description="需求子项描述（S列）")
    test_item_desc: str = Field(..., description="当前测试项描述（T列）")
    test_method: str = Field(..., description="当前测试方法（U列）")
    variables: Dict[str, str] = Field(default_factory=dict, description="变量占位符到用户输入的映射")
    fault_categories: str = Field('', description="规范化后的故障类别列表，格式如：主控板故障/随动控制板故障/图像板故障")
    session_id: Optional[str] = Field(None, description="可选，会话ID用于日志归档")


class ReqDesignSelfCheckResponse(BaseModel):
    success: bool
    session_id: str
    test_item_desc: str
    test_method: str


@router.post("/req-design/init", response_model=ReqDesignInitResponse)
async def req_design_init(payload: ReqDesignInitRequest):
    """需求设计 - 初始化：逐条调用AI，返回每行的测试项描述/测试方法"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = RequirementDesignService(session_id=sid)
        results, errors = await service.req_design_init(payload.rows)
        return {
            "success": True,
            "session_id": sid,
            "results": results,
            "errors": errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/req-design/common", response_model=ReqDesignCommonResponse)
async def req_design_common(payload: ReqDesignCommonRequest):
    """需求设计 - 通用功能：根据用户输入的变量取值，对T/U进行替换与整理（由AI完成）"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = RequirementDesignService(session_id=sid)
        res = await service.req_design_common(
            test_item_name=payload.test_item_name,
            requirement_sub_item_desc=payload.requirement_sub_item_desc,
            test_item_desc=payload.test_item_desc,
            test_method=payload.test_method,
            variables=payload.variables,
        )
        return {
            "success": True,
            "session_id": sid,
            "test_item_desc": res["test_item_desc"],
            "test_method": res["test_method"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/req-design/self-check/normalize", response_model=ReqDesignSelfCheckNormalizeResponse)
async def req_design_self_check_normalize(payload: ReqDesignSelfCheckNormalizeRequest):
    """需求设计 - 自检测：将用户输入的故障类别文本转换为规范的 / 分隔格式"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = RequirementDesignService(session_id=sid)
        normalized = await service.req_design_self_check_normalize_fault_categories(payload.raw_text)
        return {
            "success": True,
            "session_id": sid,
            "normalized": normalized,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/req-design/self-check", response_model=ReqDesignSelfCheckResponse)
async def req_design_self_check(payload: ReqDesignSelfCheckRequest):
    """需求设计 - 自检测：基于故障类别（可作为变量默认值）对T/U进行替换与整理（由AI完成）"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = RequirementDesignService(session_id=sid)
        res = await service.req_design_self_check(
            test_item_name=payload.test_item_name,
            requirement_sub_item_desc=payload.requirement_sub_item_desc,
            test_item_desc=payload.test_item_desc,
            test_method=payload.test_method,
            variables=payload.variables,
            fault_categories=payload.fault_categories,
        )
        return {
            "success": True,
            "session_id": sid,
            "test_item_desc": res["test_item_desc"],
            "test_method": res["test_method"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
