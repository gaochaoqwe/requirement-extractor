from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

from ..services.test_case_service.test_case_design.case_design_service import CaseDesignService

router = APIRouter()


class CaseDesignInitRow(BaseModel):
    row_index: int = Field(..., description="前端表格行号（用于回填）")
    test_item_name: str = Field(..., description="G列 测试项名称")

    template_case_name: str = Field('', description="I列 模板/当前测试用例名称")
    template_test_desc: str = Field('', description="L列 模板/当前测试描述")
    template_input_condition: str = Field('', description="P列 模板/当前输入条件")
    template_expected_result: str = Field('', description="Q列 模板/当前预期结果")


class CaseDesignInitRequest(BaseModel):
    task_id: str = Field(..., description="任务ID，用于绑定代码库")
    entry_code_snippet: str = Field(..., description="入口函数初始化相关代码片段")
    rows: List[CaseDesignInitRow]
    session_id: Optional[str] = Field(None, description="可选，会话ID用于日志归档")


class CaseDesignInitRowResult(BaseModel):
    row_index: int
    case_name: str
    test_desc: str
    input_condition: str
    expected_result: str


class CaseDesignInitResponse(BaseModel):
    success: bool
    session_id: str
    results: List[CaseDesignInitRowResult]
    errors: List[Dict[str, Any]]


class CaseDesignCommonVariable(BaseModel):
    key: str = Field(..., description='变量占位符（双引号内原文），例如 xx（随动/自动扫描等）')
    values: List[str] = Field(default_factory=list, description='用户输入的值列表')
    fissile: bool = Field(True, description='是否裂变变量（默认 true）')


class CaseDesignCommonRequest(BaseModel):
    case_name: str = Field('', description='I列 当前测试用例名称')
    test_desc: str = Field('', description='L列 当前测试描述')
    input_condition: str = Field('', description='P列 当前输入条件')
    expected_result: str = Field('', description='Q列 当前预期结果')
    variables: List[CaseDesignCommonVariable] = Field(default_factory=list)
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseDesignCommonCase(BaseModel):
    case_name: str
    test_desc: str
    input_condition: str
    expected_result: str


class CaseDesignCommonResponse(BaseModel):
    success: bool
    session_id: str
    cases: List[CaseDesignCommonCase]


class CaseDesignSelfCheckNormalizeRequest(BaseModel):
    raw_text: str = Field(..., description='用户输入的故障类别原始文本')
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseDesignSelfCheckNormalizeResponse(BaseModel):
    success: bool
    session_id: str
    normalized: str


class CaseDesignSelfCheckWriteRequest(BaseModel):
    task_id: str = Field(..., description='任务ID，用于绑定代码库')
    entry_code_snippet: str = Field(..., description='入口函数初始化相关代码片段')
    rows: List[CaseDesignInitRow]
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseDesignSelfCheckWriteResponse(BaseModel):
    success: bool
    session_id: str
    results: List[CaseDesignInitRowResult]
    errors: List[Dict[str, Any]]


class CaseDesignSelfCheckFissionRequest(BaseModel):
    case_name: str = Field('', description='I列 当前测试用例名称')
    test_desc: str = Field('', description='L列 当前测试描述')
    input_condition: str = Field('', description='P列 当前输入条件')
    expected_result: str = Field('', description='Q列 当前预期结果')
    xx_values: List[str] = Field(default_factory=list, description='故障类别裂变值列表，仅用于替换xx')
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseDesignSelfCheckFissionResponse(BaseModel):
    success: bool
    session_id: str
    cases: List[CaseDesignCommonCase]


class CaseDesignApiExceptionRequest(BaseModel):
    task_id: str = Field(..., description='任务ID，用于绑定代码库')
    test_item_name: str = Field('', description='G列 测试项名称')
    template_case_name: str = Field('', description='I列 当前/模板测试用例名称')
    template_test_desc: str = Field('', description='L列 当前/模板测试描述')
    template_input_condition: str = Field('', description='P列 当前/模板输入条件')
    template_expected_result: str = Field('', description='Q列 当前/模板预期结果')
    user_code_snippet: str = Field(..., description='用户粘贴的代码片段（用于定位文件/函数/行号并生成插桩代码）')
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseDesignApiExceptionCase(BaseModel):
    case_name: str
    test_desc: str
    input_condition: str
    expected_result: str


class CaseDesignApiExceptionResponse(BaseModel):
    success: bool
    session_id: str
    cases: List[CaseDesignApiExceptionCase]


class CaseDesignApiPeriodRequest(BaseModel):
    task_id: str = Field(..., description='任务ID，用于绑定代码库')
    test_item_name: str = Field('', description='G列 测试项名称')
    template_case_name: str = Field('', description='I列 当前/模板测试用例名称')
    template_test_desc: str = Field('', description='L列 当前/模板测试描述')
    template_input_condition: str = Field('', description='P列 当前/模板输入条件')
    template_expected_result: str = Field('', description='Q列 当前/模板预期结果')
    user_code_snippet: str = Field(..., description='用户粘贴的代码片段（用于定位文件/函数/行号并生成插桩代码）')
    session_id: Optional[str] = Field(None, description='可选，会话ID用于日志归档')


class CaseDesignApiPeriodCase(BaseModel):
    case_name: str
    test_desc: str
    input_condition: str
    expected_result: str


class CaseDesignApiPeriodResponse(BaseModel):
    success: bool
    session_id: str
    cases: List[CaseDesignApiPeriodCase]


@router.post('/case-design/init', response_model=CaseDesignInitResponse)
async def case_design_init(payload: CaseDesignInitRequest):
    """用例设计-初始化：基于G/I/L/P/Q与入口函数代码片段定位信息，逐条调用AI生成I/L/P/Q"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseDesignService(session_id=sid)
        results, errors = await service.case_design_init(
            task_id=payload.task_id,
            entry_code_snippet=payload.entry_code_snippet,
            rows=payload.rows,
        )
        return {
            'success': True,
            'session_id': sid,
            'results': results,
            'errors': errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/case-design/api-period', response_model=CaseDesignApiPeriodResponse)
async def case_design_api_period(payload: CaseDesignApiPeriodRequest):
    """用例设计-接口测试-接口周期：定位代码片段并生成两条周期用例（接收/发送）的 I/L/P/Q"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseDesignService(session_id=sid)
        cases = await service.case_design_api_period(
            task_id=payload.task_id,
            test_item_name=payload.test_item_name,
            template_case_name=payload.template_case_name,
            template_test_desc=payload.template_test_desc,
            template_input_condition=payload.template_input_condition,
            template_expected_result=payload.template_expected_result,
            user_code_snippet=payload.user_code_snippet,
        )
        return {
            'success': True,
            'session_id': sid,
            'cases': cases,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/case-design/api-exception', response_model=CaseDesignApiExceptionResponse)
async def case_design_api_exception(payload: CaseDesignApiExceptionRequest):
    """用例设计-接口测试-接口异常测试：定位代码片段并生成两条异常用例（校验位错误/数据长度错误）的 I/P/Q"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseDesignService(session_id=sid)
        cases = await service.case_design_api_exception(
            task_id=payload.task_id,
            test_item_name=payload.test_item_name,
            template_case_name=payload.template_case_name,
            template_test_desc=payload.template_test_desc,
            template_input_condition=payload.template_input_condition,
            template_expected_result=payload.template_expected_result,
            user_code_snippet=payload.user_code_snippet,
        )
        return {
            'success': True,
            'session_id': sid,
            'cases': cases,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/case-design/common', response_model=CaseDesignCommonResponse)
async def case_design_common(payload: CaseDesignCommonRequest):
    """用例设计-通用功能：变量替换 + 裂变变量排列组合，生成多条用例的 I/L/P/Q"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseDesignService(session_id=sid)
        cases = await service.case_design_common(
            case_name=payload.case_name,
            test_desc=payload.test_desc,
            input_condition=payload.input_condition,
            expected_result=payload.expected_result,
            variables=[v.model_dump() for v in payload.variables],
        )
        return {
            'success': True,
            'session_id': sid,
            'cases': cases,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/case-design/self-check/normalize', response_model=CaseDesignSelfCheckNormalizeResponse)
async def case_design_self_check_normalize(payload: CaseDesignSelfCheckNormalizeRequest):
    """用例设计-自检测：将用户输入的故障类别文本转换为规范的 / 分隔格式"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseDesignService(session_id=sid)
        normalized = await service.case_design_self_check_normalize_fault_categories(payload.raw_text)
        return {
            'success': True,
            'session_id': sid,
            'normalized': normalized,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/case-design/self-check/write', response_model=CaseDesignSelfCheckWriteResponse)
async def case_design_self_check_write(payload: CaseDesignSelfCheckWriteRequest):
    """用例设计-自检测：用例编写（逻辑与初始化类似），基于入口代码片段定位信息生成 I/L/P/Q"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseDesignService(session_id=sid)
        results, errors = await service.case_design_self_check_write(
            task_id=payload.task_id,
            entry_code_snippet=payload.entry_code_snippet,
            rows=payload.rows,
        )
        return {
            'success': True,
            'session_id': sid,
            'results': results,
            'errors': errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/case-design/self-check/fission', response_model=CaseDesignSelfCheckFissionResponse)
async def case_design_self_check_fission(payload: CaseDesignSelfCheckFissionRequest):
    """用例设计-自检测：用例裂变（仅替换xx，其他变量与步骤结构保持原样）"""
    try:
        sid = payload.session_id or str(uuid.uuid4())
        service = CaseDesignService(session_id=sid)
        cases = await service.case_design_self_check_fission(
            case_name=payload.case_name,
            test_desc=payload.test_desc,
            input_condition=payload.input_condition,
            expected_result=payload.expected_result,
            xx_values=payload.xx_values,
        )
        return {
            'success': True,
            'session_id': sid,
            'cases': cases,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
