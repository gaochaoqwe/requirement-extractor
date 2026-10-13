"""
测试用例生成API端点

提供基于需求分析表的测试用例生成功能，确保每个测试方法都有对应的测试用例。
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
import json
from pathlib import Path

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..service.test_case_generation.test_case_service import TestCaseService
from ..service.test_case_generation.realtime_test_case_service import RealtimeTestCaseService

router = APIRouter(tags=["测试用例生成"])

@router.post("/generate-from-requirement-analysis")
async def generate_test_cases_from_requirement_analysis(
    requirement_analysis_path: str = Form(...),
    requirement_sheet_name: str = Form("需求分析表"),
    output_path: Optional[str] = Form(None),
    output_sheet_name: str = Form("测试用例单"),
    test_type: str = Form("功能测试"),
    detector_flag: str = Form("无检测仪"),
    task_id: Optional[str] = Form(None)
):
    # 接口下线：增强生成已移除，仅保留 TestCaseService
    raise HTTPException(status_code=410, detail="接口已下线：增强生成功能已移除，改用 /extract-from-test-case-excel 进行入库")

@router.post("/validate-method-case-mapping")
async def validate_method_case_mapping(
    requirement_analysis_path: str = Form(..., description="需求分析表Excel文件路径"),
    test_case_path: str = Form(..., description="测试用例表Excel文件路径"),
    requirement_sheet_name: str = Form("需求分析表", description="需求分析表工作表名称"),
    test_case_sheet_name: str = Form("测试用例单", description="测试用例表工作表名称")
):
    """
    验证测试方法与测试用例的映射关系
    
    检查每个需求分析表中的测试方法是否都有对应的测试用例。
    """
    try:
        log_info(f"开始验证测试方法与测试用例的映射关系", "test_case_generation_api")
        
        # 验证输入文件是否存在
        for file_path in [requirement_analysis_path, test_case_path]:
            if not Path(file_path).exists():
                raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 接口下线：增强校验已移除
        raise HTTPException(status_code=410, detail="接口已下线：增强校验功能已移除")
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"验证映射关系失败: {str(e)}", "test_case_generation_api")
        raise HTTPException(status_code=500, detail=f"验证映射关系失败: {str(e)}")

@router.get("/get-method-summary")
async def get_method_summary(
    requirement_analysis_path: str,
    requirement_sheet_name: str = "需求分析表"
):
    """
    获取需求分析表中测试方法的汇总信息
    
    显示每个测试项的测试方法情况，便于用户了解当前状态。
    """
    try:
        log_info(f"获取测试方法汇总信息: {requirement_analysis_path}", "test_case_generation_api")
        
        # 验证输入文件是否存在
        if not Path(requirement_analysis_path).exists():
            raise HTTPException(status_code=404, detail=f"需求分析表文件不存在: {requirement_analysis_path}")
        
        # 接口下线：增强汇总已移除
        raise HTTPException(status_code=410, detail="接口已下线：增强汇总功能已移除")
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"获取汇总信息失败: {str(e)}", "test_case_generation_api")
        raise HTTPException(status_code=500, detail=f"获取汇总信息失败: {str(e)}")

@router.post("/generate-method-based-cases")
async def generate_method_based_cases(
    requirement_analysis_data: str = Form(..., description="需求分析表数据（JSON格式）"),
    test_type: str = Form("功能测试", description="测试类型"),
    detector_flag: str = Form("无检测仪", description="检测仪标志")
):
    """
    直接基于需求分析数据生成基于测试方法的测试用例
    
    返回key-value格式的测试用例，其中key为测试方法，value为测试用例列表。
    """
    try:
        log_info("开始生成基于测试方法的测试用例", "test_case_generation_api")
        
        # 接口下线：方法级生成已移除
        raise HTTPException(status_code=410, detail="接口已下线：方法级用例生成功能已移除")
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"生成基于方法的测试用例失败: {str(e)}", "test_case_generation_api")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@router.post("/batch-generate")
async def batch_generate_test_cases(
    files: List[UploadFile] = File(..., description="需求分析表Excel文件列表"),
    test_type: str = Form("功能测试", description="测试类型"),
    detector_flag: str = Form("无检测仪", description="检测仪标志"),
    output_dir: Optional[str] = Form(None, description="输出目录（可选）")
):
    """
    批量生成测试用例
    
    支持同时处理多个需求分析表文件，为每个文件生成对应的测试用例。
    """
    try:
        log_info(f"开始批量生成测试用例，文件数量: {len(files)}", "test_case_generation_api")
        
        if not files:
            raise HTTPException(status_code=400, detail="没有提供文件")
        
        # 创建临时目录保存上传的文件
        import tempfile
        import uuid
        
        temp_dir = Path(tempfile.gettempdir()) / f"batch_test_case_generation_{uuid.uuid4()}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            results = []
            
            for i, file in enumerate(files):
                try:
                    # 保存上传的文件
                    file_path = temp_dir / f"requirement_{i}_{file.filename}"
                    with open(file_path, "wb") as buffer:
                        content = await file.read()
                        buffer.write(content)
                    
                    log_info(f"处理文件 {i+1}/{len(files)}: {file.filename}", "test_case_generation_api")
                    
                    # 批量接口下线：仅做回执
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "message": "接口已下线：增强批量生成功能已移除",
                        "statistics": {},
                        "output_path": None
                    })
                    
                except Exception as file_error:
                    log_error(f"处理文件 {file.filename} 失败: {str(file_error)}", "test_case_generation_api")
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "message": f"处理失败: {str(file_error)}",
                        "statistics": {},
                        "output_path": None
                    })
            
            # 统计总体结果
            successful_count = sum(1 for r in results if r["success"])
            failed_count = len(results) - successful_count
            
            log_info(f"批量生成完成: 成功 {successful_count} 个，失败 {failed_count} 个", "test_case_generation_api")
            
            return {
                "status": "success",
                "message": "接口已下线：增强批量生成功能已移除",
                "results": results,
                "summary": {
                    "total_files": len(files),
                    "successful_count": 0,
                    "failed_count": len(files),
                    "success_rate": 0.0
                }
            }
            
        finally:
            # 清理临时文件
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                log_warning(f"清理临时文件失败: {str(cleanup_error)}", "test_case_generation_api")
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"批量生成测试用例失败: {str(e)}", "test_case_generation_api")
        raise HTTPException(status_code=500, detail=f"批量生成失败: {str(e)}")

# 新增：使用 TestCaseService 从测试用例Excel抽取并入库
@router.post("/extract-from-test-case-excel")
async def extract_from_test_case_excel(
    test_case_excel_path: str = Form(..., description="测试用例Excel文件路径"),
    sheet_name: str = Form("测试用例单", description="测试用例表工作表名称"),
    task_id: Optional[str] = Form(None, description="任务ID（可选）")
):
    try:
        log_info(f"开始从测试用例Excel抽取入库: {test_case_excel_path}", "test_case_generation_api")
        if not Path(test_case_excel_path).exists():
            raise HTTPException(status_code=404, detail=f"测试用例Excel文件不存在: {test_case_excel_path}")

        service = TestCaseService()
        ok = service.extract_and_store_excel_data_to_db(
            excel_file_path=test_case_excel_path,
            sheet_name=sheet_name,
            task_id=task_id
        )
        if not ok:
            raise HTTPException(status_code=500, detail="抽取入库失败")
        return {"status": "success", "message": "抽取入库成功", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"抽取入库失败: {str(e)}", "test_case_generation_api")
        raise HTTPException(status_code=500, detail=f"抽取入库失败: {str(e)}")


# 新增：实时AI生成并入库
@router.post("/test-cases/generate-realtime")
async def generate_realtime_test_cases(
    task_id: str = Form(..., description="任务ID"),
    requirement_name: str = Form(..., description="测试项/需求名称"),
    requirement_desc: str = Form("", description="需求描述"),
    test_method: str = Form(..., description="测试方法"),
    test_description: str = Form("", description="测试描述"),
    test_type: str = Form("功能测试", description="测试类型"),
    detector_flag: str = Form("无检测仪", description="检测仪标志"),
    software_item_name: str = Form("", description="软件配置项名称"),
    software_version: str = Form("", description="被测软件版本"),
    test_item_identifier: str = Form("", description="测试项标识"),
    requirement_traceability: str = Form("", description="需求追溯"),
    start_sequence: int = Form(1, description="起始序号"),
    product_type: str = Form("", description="组件类型（转塔、对抗告警、光电雷达、吊舱、火控、外挂、显示）")
):
    try:
        log_info(f"实时生成用例: {requirement_name}", "test_case_generation_api")
        
        # 🔧 新增：组织资产库匹配逻辑
        database_template_name = None
        database_template_input = None
        database_template_expected = None
        is_database_matched = False
        
        if product_type and test_description:
            try:
                from ..service.requirement_analysis.test_generation.content_generators.asset_database_enhancer import AssetDatabaseEnhancer
                enhancer = AssetDatabaseEnhancer()
                
                # 基于测试描述匹配组织资产库模板
                database_template_name, database_template_input, database_template_expected, is_database_matched = enhancer.get_matched_templates_for_test_case(
                    test_description=test_description,
                    product_type=product_type
                )
                
                if is_database_matched:
                    log_info(f"[DATABASE_MATCH] ✅ 测试描述匹配到组织资产库模板: {database_template_name}", "test_case_generation_api")
                else:
                    log_info(f"[DATABASE_MATCH] ❌ 测试描述未匹配到组织资产库模板", "test_case_generation_api")
                    
            except Exception as e:
                log_error(f"[DATABASE_MATCH] 组织资产库匹配失败: {e}", "test_case_generation_api")
        
        service = RealtimeTestCaseService()
        result = service.generate_and_save_cases(
            task_id=task_id,
            requirement_name=requirement_name,
            requirement_desc=requirement_desc,
            test_method=test_method,
            test_description=test_description,
            test_type=test_type,
            detector_flag=detector_flag,
            software_item_name=software_item_name or None,
            software_version=software_version or None,
            test_item_identifier=test_item_identifier or None,
            requirement_traceability=requirement_traceability or None,
            start_sequence=int(start_sequence) if start_sequence else 1,
            database_template_name=database_template_name,
            database_template_input=database_template_input,
            database_template_expected=database_template_expected,
            is_database_matched=is_database_matched
        )
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="AI未返回有效用例或保存失败")
        return {"status": "success", "saved_count": result.get("saved_count", 0), "cases": result.get("cases", [])}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"实时生成用例失败: {str(e)}", "test_case_generation_api")
        raise HTTPException(status_code=500, detail=f"实时生成失败: {str(e)}")


# 新增：JSON 批量实时生成（一次请求覆盖一个测试项的所有"测试项描述条目"）
class BatchRealtimeRequest(BaseModel):
    task_id: str
    requirement_name: str
    requirement_desc: str = ""
    requirement_sub_desc: str = ""
    description_items: List[str]
    method_items: List[str]
    test_type: str = "功能测试"
    detector_flag: str = "无检测仪"
    software_item_name: Optional[str] = None
    software_version: Optional[str] = None
    test_item_identifier: Optional[str] = None
    requirement_traceability: Optional[str] = None
    start_sequence: int = 1
    product_type: Optional[str] = None  # 🔧 新增：产品类型参数


@router.post("/test-cases/generate-realtime-batch")
async def generate_realtime_test_cases_batch(payload: BatchRealtimeRequest):
    try:
        log_info(
            f"批量实时生成用例: {payload.requirement_name}, 条目数={len(payload.description_items)}",
            "test_case_generation_api",
        )
        
        # 🔧 新增：为每个描述条目进行组织资产库匹配
        enhanced_description_items = []
        enhanced_method_items = []
        
        if payload.product_type and payload.description_items:
            try:
                from ..service.requirement_analysis.test_generation.content_generators.asset_database_enhancer import AssetDatabaseEnhancer
                enhancer = AssetDatabaseEnhancer()
                
                for i, desc_item in enumerate(payload.description_items):
                    # 为每个测试描述条目尝试匹配组织资产库
                    template_name, template_input, template_expected, is_matched = enhancer.get_matched_templates_for_test_case(
                        test_description=desc_item,
                        product_type=payload.product_type
                    )
                    
                    if is_matched:
                        log_info(f"[DATABASE_MATCH] ✅ 条目{i+1} 匹配到组织资产库模板: {template_name}", "test_case_generation_api")
                        # 使用数据库模板内容
                        enhanced_description_items.append(f"[DB_SOURCE]{desc_item}")
                    else:
                        log_info(f"[DATABASE_MATCH] ❌ 条目{i+1} 未匹配到组织资产库模板", "test_case_generation_api")
                        enhanced_description_items.append(desc_item)
                
                # 方法条目保持原样
                enhanced_method_items = list(payload.method_items or [])
                        
            except Exception as e:
                log_error(f"[DATABASE_MATCH] 批量组织资产库匹配失败: {e}", "test_case_generation_api")
                enhanced_description_items = list(payload.description_items or [])
                enhanced_method_items = list(payload.method_items or [])
        else:
            enhanced_description_items = list(payload.description_items or [])
            enhanced_method_items = list(payload.method_items or [])
        
        service = RealtimeTestCaseService()
        result = service.generate_and_save_cases_by_descriptions(
            task_id=payload.task_id,
            requirement_name=payload.requirement_name,
            requirement_desc=payload.requirement_desc,
            requirement_sub_desc=payload.requirement_sub_desc,
            description_items=enhanced_description_items,
            method_items=enhanced_method_items,
            test_type=payload.test_type,
            detector_flag=payload.detector_flag,
            software_item_name=payload.software_item_name,
            software_version=payload.software_version,
            test_item_identifier=payload.test_item_identifier,
            requirement_traceability=payload.requirement_traceability,
            start_sequence=int(payload.start_sequence) if payload.start_sequence else 1,
        )
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="AI未返回有效用例或保存失败")
        return {"status": "success", "saved_count": result.get("saved_count", 0), "cases": result.get("cases", [])}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"批量实时生成用例失败: {str(e)}", "test_case_generation_api")
        raise HTTPException(status_code=500, detail=f"批量实时生成失败: {str(e)}")
