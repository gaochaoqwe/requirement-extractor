from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.databaseManage.dynamicDatabaseManage.db.database import SessionLocal as DynamicSessionLocal
from backend.app.databaseManage.dynamicDatabaseManage.services.intelligent_export_service import (
    IntelligentExportService,
)

from ..database.database import get_db_session, init_database
from ..models.models import CaseDesignTask

router = APIRouter()


class SelectedTestItem(BaseModel):
    row_index: int = Field(..., description="选中的行索引（0-based）")
    test_item_name: str = Field('', description="O列测试项名称")


class AssetReuseSelectedRequest(BaseModel):
    task_id: Optional[str] = Field(None, description="用例编辑任务ID（case_design_tasks.task_id）")
    selected_type: str = Field(..., description="产品类别，如 转塔/对抗告警/光雷/吊舱")
    selected_software_type: str = Field(..., description="软件类型")
    items: List[SelectedTestItem] = Field(default_factory=list, description="选中行的测试项")


class AssetReuseSelectedItemResult(BaseModel):
    row_index: int
    test_item_name: str
    matched: bool
    test_content: str = ''
    test_method: str = ''


class AssetReuseSelectedCaseMatch(BaseModel):
    case_name: str = ''
    test_desc: str = ''
    input_condition: str = ''
    expected_result: str = ''


class AssetReuseSelectedCaseItemResult(BaseModel):
    row_index: int
    test_item_name: str
    matched: bool
    matches: List[AssetReuseSelectedCaseMatch] = Field(default_factory=list)


class AssetReuseSelectedResponse(BaseModel):
    success: bool
    results: List[AssetReuseSelectedItemResult]


class AssetReuseSelectedCaseResponse(BaseModel):
    success: bool
    results: List[AssetReuseSelectedCaseItemResult]


def _case_db() -> Session:
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.post('/asset-reuse-selected/match', response_model=AssetReuseSelectedResponse)
def asset_reuse_selected_match(payload: AssetReuseSelectedRequest, case_db: Session = Depends(_case_db)):
    try:
        init_database()

        if payload.task_id:
            task = case_db.query(CaseDesignTask).filter(CaseDesignTask.task_id == payload.task_id).first()
            if task:
                task.product_type = payload.selected_type
                task.software_type = payload.selected_software_type
                case_db.commit()

        model = IntelligentExportService.MODEL_MAP.get(payload.selected_type)
        if not model:
            raise HTTPException(status_code=400, detail=f"Unsupported type: {payload.selected_type}")

        dyn_db = DynamicSessionLocal()
        try:
            asset_data = IntelligentExportService._get_asset_data(dyn_db, model)
        finally:
            dyn_db.close()

        results: List[AssetReuseSelectedItemResult] = []

        for it in payload.items or []:
            name = str(it.test_item_name or '').strip()
            if not name:
                results.append(
                    AssetReuseSelectedItemResult(
                        row_index=it.row_index,
                        test_item_name=name,
                        matched=False,
                        test_content='',
                        test_method='',
                    )
                )
                continue

            matched_records = IntelligentExportService._match_test_items(
                test_item_name=name,
                asset_data=asset_data,
                selected_software_type=payload.selected_software_type,
            )

            if matched_records:
                merged_test_content = IntelligentExportService._merge_field_content(
                    [r.get('test_content') for r in matched_records]
                )
                merged_test_method = IntelligentExportService._merge_field_content(
                    [r.get('test_method') for r in matched_records]
                )
                results.append(
                    AssetReuseSelectedItemResult(
                        row_index=it.row_index,
                        test_item_name=name,
                        matched=True,
                        test_content=merged_test_content,
                        test_method=merged_test_method,
                    )
                )
            else:
                results.append(
                    AssetReuseSelectedItemResult(
                        row_index=it.row_index,
                        test_item_name=name,
                        matched=False,
                        test_content='',
                        test_method='',
                    )
                )

        return {'success': True, 'results': results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/asset-reuse-selected/case-sheet/match', response_model=AssetReuseSelectedCaseResponse)
def asset_reuse_selected_case_sheet_match(payload: AssetReuseSelectedRequest, case_db: Session = Depends(_case_db)):
    try:
        init_database()

        if payload.task_id:
            task = case_db.query(CaseDesignTask).filter(CaseDesignTask.task_id == payload.task_id).first()
            if task:
                task.product_type = payload.selected_type
                task.software_type = payload.selected_software_type
                case_db.commit()

        model = IntelligentExportService.MODEL_MAP.get(payload.selected_type)
        if not model:
            raise HTTPException(status_code=400, detail=f"Unsupported type: {payload.selected_type}")

        dyn_db = DynamicSessionLocal()
        try:
            asset_data = IntelligentExportService._get_asset_data(dyn_db, model)
        finally:
            dyn_db.close()

        results: List[AssetReuseSelectedCaseItemResult] = []

        for it in payload.items or []:
            name = str(it.test_item_name or '').strip()
            if not name:
                results.append(
                    AssetReuseSelectedCaseItemResult(
                        row_index=it.row_index,
                        test_item_name=name,
                        matched=False,
                        matches=[],
                    )
                )
                continue

            matched_records = IntelligentExportService._match_test_items(
                test_item_name=name,
                asset_data=asset_data,
                selected_software_type=payload.selected_software_type,
            )

            if matched_records:
                matches: List[AssetReuseSelectedCaseMatch] = []
                for r in matched_records:
                    matches.append(
                        AssetReuseSelectedCaseMatch(
                            case_name=str(r.get('case_template_name') or ''),
                            test_desc=str(r.get('test_content') or ''),
                            input_condition=str(r.get('case_template_input') or ''),
                            expected_result=str(r.get('case_template_expected') or ''),
                        )
                    )
                results.append(
                    AssetReuseSelectedCaseItemResult(
                        row_index=it.row_index,
                        test_item_name=name,
                        matched=True,
                        matches=matches,
                    )
                )
            else:
                results.append(
                    AssetReuseSelectedCaseItemResult(
                        row_index=it.row_index,
                        test_item_name=name,
                        matched=False,
                        matches=[],
                    )
                )

        return {'success': True, 'results': results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
