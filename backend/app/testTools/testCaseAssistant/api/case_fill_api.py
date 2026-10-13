from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

from ..services.test_case_service.test_case_fill.case_fill_service import CaseFillService

router = APIRouter()


class CaseFillCaseNameRow(BaseModel):
    row_index: int = Field(..., description='前端表格行号（用于回填）')
    test_item_name: str = Field('', description='G列 测试项名称')
    test_desc: str = Field('', description='L列 测试描述')
    input_condition: str = Field('', description='P列 输入条件')
    expected_result: str = Field('', description='Q列 测试结果/预期结果')
    neighbor_case_names: List[str] = Field(default_factory=list, description='附近同测试项用例名称（I列）')


class CaseFillCaseNameRequest(BaseModel):
    task_id: str = Field(..., description='任务ID（用于日志归档/未来扩展）')
    rows: List[CaseFillCaseNameRow] = Field(default_factory=list)
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseFillCaseNameRowResult(BaseModel):
    row_index: int
    case_name: str


class CaseFillCaseNameResponse(BaseModel):
    success: bool
    session_id: str
    results: List[CaseFillCaseNameRowResult]
    errors: List[Dict[str, Any]]


class CaseFillTestDescRow(BaseModel):
    row_index: int = Field(..., description='前端表格行号（用于回填）')
    test_item_name: str = Field('', description='G列 测试项名称')
    case_name: str = Field('', description='I列 测试用例名称')
    input_condition: str = Field('', description='P列 输入条件')
    expected_result: str = Field('', description='Q列 测试结果/预期结果')


class CaseFillTestItemDescMethodRow(BaseModel):
    row_index: int = Field(..., description='前端表格行号（用于回填）')
    test_item_name: str = Field('', description='G列 测试项名称')
    case_name: str = Field('', description='I列 测试用例名称')
    test_desc: str = Field('', description='L列 测试描述')
    input_condition: str = Field('', description='P列 输入条件')
    expected_result: str = Field('', description='Q列 测试结果/预期结果')


class CaseFillTestItemDescMethodRequest(BaseModel):
    task_id: str = Field(..., description='任务ID（用于日志归档/未来扩展）')
    test_item_name: str = Field('', description='测试项名称（用于分组匹配）')
    rows: List[CaseFillTestItemDescMethodRow] = Field(default_factory=list)
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseFillTestItemDescMethodRowResult(BaseModel):
    row_index: int
    test_item_desc: str
    test_method: str


class CaseFillTestItemDescMethodResponse(BaseModel):
    success: bool
    session_id: str
    results: List[CaseFillTestItemDescMethodRowResult]
    errors: List[Dict[str, Any]]


class CaseFillTestDescRequest(BaseModel):
    task_id: str = Field(..., description='任务ID（用于日志归档/未来扩展）')
    rows: List[CaseFillTestDescRow] = Field(default_factory=list)
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseFillTestDescRowResult(BaseModel):
    row_index: int
    test_desc: str


class CaseFillTestDescResponse(BaseModel):
    success: bool
    session_id: str
    results: List[CaseFillTestDescRowResult]
    errors: List[Dict[str, Any]]


@router.post('/case-fill/case-name', response_model=CaseFillCaseNameResponse)
async def case_fill_case_name(payload: CaseFillCaseNameRequest):
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseFillService(session_id=sid)
        results, errors = await service.smart_fill_case_name([r.model_dump() for r in payload.rows])
        return {
            'success': True,
            'session_id': sid,
            'results': results,
            'errors': errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/case-fill/test-desc', response_model=CaseFillTestDescResponse)
async def case_fill_test_desc(payload: CaseFillTestDescRequest):
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseFillService(session_id=sid)
        results, errors = await service.smart_fill_test_desc([r.model_dump() for r in payload.rows])
        return {
            'success': True,
            'session_id': sid,
            'results': results,
            'errors': errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/case-fill/test-item-desc-method', response_model=CaseFillTestItemDescMethodResponse)
async def case_fill_test_item_desc_method(payload: CaseFillTestItemDescMethodRequest):
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseFillService(session_id=sid)
        results, errors = await service.smart_fill_test_item_desc_method([r.model_dump() for r in payload.rows])
        return {
            'success': True,
            'session_id': sid,
            'results': results,
            'errors': errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
