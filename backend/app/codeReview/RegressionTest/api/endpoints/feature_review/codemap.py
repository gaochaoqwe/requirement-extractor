"""
功能点代码视图API
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import json

from ....db.deps import get_db
from ....db.repository.feature_repo import FeatureRepository, FeatureReviewProblemRepository
from ....db.repository.function_repo import FunctionRepository
from ....db.models.feature_problem import Feature

router = APIRouter()


@router.get("/codemap/{task_id}")
async def get_feature_codemap(task_id: int, db: Session = Depends(get_db)):
    """
    获取功能点代码视图数据
    
    返回:
    {
        "features": [
            {
                "id": 1,
                "feature_name": "用户登录",
                "feature_description": "...",
                "implementation_description": "...",
                "functions": [
                    {
                        "function_name": "login",
                        "file_path": "user/auth.c",
                        "source_code": "...",
                        "start_line": 10,
                        "end_line": 50
                    }
                ],
                "problems": [...]
            }
        ]
    }
    """
    try:
        feature_repo = FeatureRepository(db)
        problem_repo = FeatureReviewProblemRepository(db)
        function_repo = FunctionRepository(db)
        
        # 获取所有功能点
        features = feature_repo.get_features_by_task(task_id)
        
        result = []
        for feature in features:
            # 获取功能点的问题
            problems = problem_repo.get_problems_by_feature(feature.id)
            
            # 解析相关函数（带执行顺序）
            related_functions = []
            call_chain_order = []  # 记录链路顺序
            
            try:
                # 解析call_chain获取执行顺序
                if feature.call_chain:
                    # call_chain格式如: "start_scan → acquire_raw_signal → allocate_signal_buffer"
                    call_chain_order = [func.strip() for func in feature.call_chain.split('→')]
                
                if feature.related_functions:
                    func_names = json.loads(feature.related_functions)
                    
                    # 从数据库中获取函数详情
                    for func_name in func_names:
                        db_funcs = function_repo.search_functions(task_id, func_name)
                        if db_funcs:
                            func = db_funcs[0]
                            
                            # 确定函数在链路中的位置（A、B、C、D...）
                            chain_position = None
                            chain_index = -1
                            if func_name in call_chain_order:
                                chain_index = call_chain_order.index(func_name)
                                # 转换为字母标记：0->A, 1->B, 2->C...
                                if chain_index < 26:
                                    chain_position = chr(65 + chain_index)  # A=65
                                else:
                                    chain_position = f"{chain_index + 1}"  # 超过26个用数字
                            
                            related_functions.append({
                                "function_name": func.function_name,
                                "file_path": func.file_path,
                                "source_code": func.source_code or f"// 源代码不可用",
                                "start_line": func.start_line or 0,
                                "end_line": func.end_line or 0,
                                "chain_position": chain_position,  # A、B、C、D...
                                "chain_index": chain_index if chain_index >= 0 else None  # 0、1、2、3...
                            })
                    
                    # 按链路顺序排序（有顺序的排前面，没有的排后面）
                    related_functions.sort(key=lambda x: (x['chain_index'] if x['chain_index'] is not None else 9999, x['function_name']))
                    
            except Exception as e:
                print(f"解析功能点函数失败: {e}")
            
            result.append({
                "id": feature.id,
                "feature_name": feature.feature_name,
                "feature_description": feature.feature_description,
                "implementation_description": feature.implementation_description or "暂无实现描述",
                "status": feature.status,
                "functions": related_functions,
                "problems": [p.to_dict() for p in problems]
            })
        
        return {
            "task_id": task_id,
            "features": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取功能点代码视图失败: {str(e)}")


@router.get("/codemap/{task_id}/feature/{feature_id}")
async def get_feature_detail(task_id: int, feature_id: int, db: Session = Depends(get_db)):
    """
    获取单个功能点的详细信息
    """
    try:
        feature_repo = FeatureRepository(db)
        problem_repo = FeatureReviewProblemRepository(db)
        
        feature = feature_repo.get_feature(feature_id)
        if not feature or feature.task_id != task_id:
            raise HTTPException(status_code=404, detail="功能点不存在")
        
        problems = problem_repo.get_problems_by_feature(feature_id)
        
        # 解析相关函数（带执行顺序）
        related_functions = []
        call_chain_order = []
        
        try:
            # 解析call_chain获取执行顺序
            if feature.call_chain:
                call_chain_order = [func.strip() for func in feature.call_chain.split('→')]
            
            if feature.related_functions:
                func_names = json.loads(feature.related_functions)
                function_repo = FunctionRepository(db)
                
                for func_name in func_names:
                    db_funcs = function_repo.search_functions(task_id, func_name)
                    if db_funcs:
                        func = db_funcs[0]
                        
                        # 确定函数在链路中的位置
                        chain_position = None
                        chain_index = -1
                        if func_name in call_chain_order:
                            chain_index = call_chain_order.index(func_name)
                            if chain_index < 26:
                                chain_position = chr(65 + chain_index)
                            else:
                                chain_position = f"{chain_index + 1}"
                        
                        related_functions.append({
                            "function_name": func.function_name,
                            "file_path": func.file_path,
                            "source_code": func.source_code or "// 源代码不可用",
                            "start_line": func.start_line or 0,
                            "end_line": func.end_line or 0,
                            "chain_position": chain_position,
                            "chain_index": chain_index if chain_index >= 0 else None
                        })
                
                # 按链路顺序排序
                related_functions.sort(key=lambda x: (x['chain_index'] if x['chain_index'] is not None else 9999, x['function_name']))
                
        except Exception as e:
            print(f"解析功能点函数失败: {e}")
        
        return {
            "feature": feature.to_dict(),
            "functions": related_functions,
            "problems": [p.to_dict() for p in problems]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取功能点详情失败: {str(e)}")

