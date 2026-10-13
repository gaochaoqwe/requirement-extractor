from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

from ..services.test_item_service.test_item_design.req_design_api_test_service import ReqDesignApiTestService

router = APIRouter()


class ReqDesignApiTestRow(BaseModel):
    row_index: int = Field(..., description="前端表格中的行号（用于回填）")
    test_item_name: str = Field('', description="测试项名称（O列）")
    template_test_item_desc: str = Field('', description="模板/当前测试项描述（T列）")
    template_test_method: str = Field('', description="模板/当前测试方法（U列）")

    class Config:
        extra = 'ignore'


class ReqDesignApiTestGenerateRequest(BaseModel):
    interface_types: Optional[str] = Field(None, description="兼容旧版本：接口类型列表（已弃用）")
    rows: List[ReqDesignApiTestRow]
    session_id: Optional[str] = Field(None, description="可选，会话ID用于日志归档")

    class Config:
        extra = 'ignore'


class ReqDesignApiTestRowResult(BaseModel):
    row_index: int
    test_item_desc: str
    test_method: str


class ReqDesignApiTestGenerateResponse(BaseModel):
    success: bool
    session_id: str
    results: List[ReqDesignApiTestRowResult]
    errors: List[Dict[str, Any]]


@router.post('/req-design/api-test/generate', response_model=ReqDesignApiTestGenerateResponse)
async def req_design_api_test_generate(payload: ReqDesignApiTestGenerateRequest):
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = ReqDesignApiTestService(session_id=sid)
        results, errors = await service.generate(rows=payload.rows)
        return {
            'success': True,
            'session_id': sid,
            'results': results,
            'errors': errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
