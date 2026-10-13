"""
回归测试下拉数据管理API端点
处理各种下拉列表数据的获取和添加
"""

from fastapi import APIRouter, HTTPException, Form

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

from ..utils.logging_utils.log_utils import setup_logger
from ..db.models import regression_db_instance

router = APIRouter(tags=["下拉数据管理"])
logger = setup_logger(__name__)


# ================= 基本信息相关接口 =================

@router.get("/dropdown-data/domains")
async def get_domains():
    """
    获取所属领域列表
    """
    try:
        domains = regression_db_instance.get_domains()
        return {
            "status": "success",
            "data": domains
        }
    except Exception as e:
        logger.error(f"获取领域数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取领域数据失败: {str(e)}")


@router.get("/dropdown-data/test-managers")
async def get_test_managers():
    """
    获取测试主管列表
    """
    try:
        managers = regression_db_instance.get_test_managers()
        return {
            "status": "success",
            "data": managers
        }
    except Exception as e:
        logger.error(f"获取测试主管数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取测试主管数据失败: {str(e)}")


@router.get("/dropdown-data/test-personnel")
async def get_test_personnel():
    """
    获取测试人员列表
    """
    try:
        personnel = regression_db_instance.get_test_personnel()
        return {
            "status": "success",
            "data": personnel
        }
    except Exception as e:
        logger.error(f"获取测试人员数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取测试人员数据失败: {str(e)}")


@router.get("/dropdown-data/developers")
async def get_developers():
    """
    获取开发人员列表
    """
    try:
        developers = regression_db_instance.get_developers()
        return {
            "status": "success",
            "data": developers
        }
    except Exception as e:
        logger.error(f"获取开发人员数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取开发人员数据失败: {str(e)}")


@router.post("/dropdown-data/domains")
async def add_domain(name: str = Form(...)):
    """
    添加新的领域
    """
    try:
        success = regression_db_instance.add_domain(name)
        if success:
            return {
                "status": "success",
                "message": "领域添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="领域已存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加领域失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加领域失败: {str(e)}")


@router.post("/dropdown-data/test-managers")
async def add_test_manager(name: str = Form(...)):
    """
    添加新的测试主管
    """
    try:
        success = regression_db_instance.add_test_manager(name)
        if success:
            return {
                "status": "success",
                "message": "测试主管添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="测试主管已存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加测试主管失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加测试主管失败: {str(e)}")


@router.post("/dropdown-data/test-personnel")
async def add_test_personnel(name: str = Form(...)):
    """
    添加新的测试人员
    """
    try:
        success = regression_db_instance.add_test_personnel(name)
        if success:
            return {
                "status": "success",
                "message": "测试人员添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="测试人员已存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加测试人员失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加测试人员失败: {str(e)}")


@router.post("/dropdown-data/developers")
async def add_developer(name: str = Form(...)):
    """
    添加新的开发人员
    """
    try:
        success = regression_db_instance.add_developer(name)
        if success:
            return {
                "status": "success",
                "message": "开发人员添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="开发人员已存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加开发人员失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加开发人员失败: {str(e)}")


# ================= 可选信息相关接口 =================

@router.get("/dropdown-data/aircraft-models")
async def get_aircraft_models():
    """
    获取飞机型号列表
    """
    try:
        models = regression_db_instance.get_aircraft_models()
        return {
            "status": "success",
            "data": models
        }
    except Exception as e:
        logger.error(f"获取飞机型号数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取飞机型号数据失败: {str(e)}")


@router.get("/dropdown-data/project-directors")
async def get_project_directors():
    """
    获取项目总师列表
    """
    try:
        directors = regression_db_instance.get_project_directors()
        return {
            "status": "success",
            "data": directors
        }
    except Exception as e:
        logger.error(f"获取项目总师数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目总师数据失败: {str(e)}")


@router.get("/dropdown-data/development-departments")
async def get_development_departments():
    """
    获取研制部门列表
    """
    try:
        departments = regression_db_instance.get_development_departments()
        return {
            "status": "success",
            "data": departments
        }
    except Exception as e:
        logger.error(f"获取研制部门数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取研制部门数据失败: {str(e)}")


@router.get("/dropdown-data/chief-designers")
async def get_chief_designers():
    """
    获取主任设计师列表
    """
    try:
        designers = regression_db_instance.get_chief_designers()
        return {
            "status": "success",
            "data": designers
        }
    except Exception as e:
        logger.error(f"获取主任设计师数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取主任设计师数据失败: {str(e)}")


@router.post("/dropdown-data/aircraft-models")
async def add_aircraft_model(name: str = Form(...)):
    """
    添加新的飞机型号
    """
    try:
        success = regression_db_instance.add_aircraft_model(name)
        if success:
            return {
                "status": "success",
                "message": "飞机型号添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="飞机型号已存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加飞机型号失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加飞机型号失败: {str(e)}")


@router.post("/dropdown-data/project-directors")
async def add_project_director(name: str = Form(...)):
    """
    添加新的项目总师
    """
    try:
        success = regression_db_instance.add_project_director(name)
        if success:
            return {
                "status": "success",
                "message": "项目总师添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="项目总师已存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加项目总师失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加项目总师失败: {str(e)}")


@router.post("/dropdown-data/development-departments")
async def add_development_department(name: str = Form(...)):
    """
    添加新的研制部门
    """
    try:
        success = regression_db_instance.add_development_department(name)
        if success:
            return {
                "status": "success",
                "message": "研制部门添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="研制部门已存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加研制部门失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加研制部门失败: {str(e)}")


@router.post("/dropdown-data/chief-designers")
async def add_chief_designer(name: str = Form(...)):
    """
    添加新的主任设计师
    """
    try:
        success = regression_db_instance.add_chief_designer(name)
        if success:
            return {
                "status": "success",
                "message": "主任设计师添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="主任设计师已存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加主任设计师失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加主任设计师失败: {str(e)}")
