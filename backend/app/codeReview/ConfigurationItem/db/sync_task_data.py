"""
任务数据同步工具

用于在链路/功能审查启动时，将任务和文件信息从主数据库同步到对应的审查数据库
"""
from sqlalchemy.orm import Session
from ..config_database import get_db  # 函数审查数据库切换模块
from ..config_database_chain import get_chain_db, engine as chain_engine  # 链路审查数据库切换模块
from ..config_database_feature import get_feature_db, engine as feature_engine  # 功能审查数据库切换模块
from .models.task import AnalysisTask
from .models.file import AnalysisFile
from .models_chain import ChainAnalysisTask, ChainAnalysisFile
from .models_feature import FeatureAnalysisTask, FeatureAnalysisFile
from ..utils.logger import log_info, log_debug, log_error


def sync_task_to_chain_db(task_id: int) -> bool:
    """
    将任务数据从主库同步到链路审查库
    
    Args:
        task_id: 任务ID
        
    Returns:
        是否同步成功
    """
    try:
        # 从主库读取任务和文件数据
        main_db = next(get_db())
        try:
            main_task = main_db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not main_task:
                log_error(f"主库中找不到任务: task_id={task_id}", "sync_to_chain")
                return False
            
            main_file = main_db.query(AnalysisFile).filter(AnalysisFile.id == main_task.code_file_id).first()
            
            log_debug(f"从主库读取任务: {main_task.task_name}", "sync_to_chain")
            
        finally:
            main_db.close()
        
        # 写入链路审查库
        chain_db = next(get_chain_db())
        try:
            # 检查是否已存在
            existing_task = chain_db.query(ChainAnalysisTask).filter(ChainAnalysisTask.id == task_id).first()
            
            if existing_task:
                # 更新已有记录
                existing_task.task_name = main_task.task_name
                existing_task.task_description = main_task.task_description
                existing_task.status = main_task.status
                existing_task.progress = main_task.progress
                existing_task.code_file_id = main_task.code_file_id
                log_debug(f"更新链路审查库任务: task_id={task_id}", "sync_to_chain")
            else:
                # 创建新记录
                chain_task = ChainAnalysisTask(
                    id=main_task.id,
                    task_name=main_task.task_name,
                    task_description=main_task.task_description,
                    status=main_task.status,
                    progress=main_task.progress,
                    code_file_id=main_task.code_file_id,
                    analysis_type='chain_review'
                )
                chain_db.add(chain_task)
                log_debug(f"创建链路审查库任务: task_id={task_id}", "sync_to_chain")
            
            # 同步文件信息
            if main_file:
                existing_file = chain_db.query(ChainAnalysisFile).filter(ChainAnalysisFile.id == main_file.id).first()
                
                if existing_file:
                    existing_file.file_name = main_file.file_name
                    existing_file.file_path = main_file.file_path
                    existing_file.extract_path = main_file.extract_path
                    existing_file.file_size = main_file.file_size
                    existing_file.status = main_file.status
                    existing_file.task_id = task_id  # 确保task_id正确
                else:
                    chain_file = ChainAnalysisFile(
                        id=main_file.id,
                        task_id=task_id,  # 使用传入的task_id，而不是main_file.task_id
                        file_name=main_file.file_name,
                        file_path=main_file.file_path,
                        extract_path=main_file.extract_path,
                        file_size=main_file.file_size,
                        status=main_file.status
                    )
                    chain_db.add(chain_file)
                    log_debug(f"同步文件到链路审查库: file_id={main_file.id}", "sync_to_chain")
            
            chain_db.commit()
            log_info(f"✅ 任务数据已同步到链路审查库: task_id={task_id}", "sync_to_chain")
            return True
            
        except Exception as e:
            chain_db.rollback()
            log_error(f"同步到链路审查库失败: task_id={task_id}", "sync_to_chain", e)
            return False
        finally:
            chain_db.close()
            
    except Exception as e:
        log_error(f"同步任务到链路审查库异常: task_id={task_id}", "sync_to_chain", e)
        return False


def sync_task_to_feature_db(task_id: int) -> bool:
    """
    将任务数据从主库同步到功能审查库
    
    Args:
        task_id: 任务ID
        
    Returns:
        是否同步成功
    """
    try:
        # 从主库读取任务和文件数据
        main_db = next(get_db())
        try:
            main_task = main_db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not main_task:
                log_error(f"主库中找不到任务: task_id={task_id}", "sync_to_feature")
                return False
            
            main_file = main_db.query(AnalysisFile).filter(AnalysisFile.id == main_task.code_file_id).first()
            
            log_debug(f"从主库读取任务: {main_task.task_name}", "sync_to_feature")
            
        finally:
            main_db.close()
        
        # 写入功能审查库
        feature_db = next(get_feature_db())
        try:
            # 检查是否已存在
            existing_task = feature_db.query(FeatureAnalysisTask).filter(FeatureAnalysisTask.id == task_id).first()
            
            if existing_task:
                # 更新已有记录
                existing_task.task_name = main_task.task_name
                existing_task.task_description = main_task.task_description
                existing_task.status = main_task.status
                existing_task.progress = main_task.progress
                existing_task.code_file_id = main_task.code_file_id
                log_debug(f"更新功能审查库任务: task_id={task_id}", "sync_to_feature")
            else:
                # 创建新记录
                feature_task = FeatureAnalysisTask(
                    id=main_task.id,
                    task_name=main_task.task_name,
                    task_description=main_task.task_description,
                    status=main_task.status,
                    progress=main_task.progress,
                    code_file_id=main_task.code_file_id,
                    analysis_type='feature_review'
                )
                feature_db.add(feature_task)
                log_debug(f"创建功能审查库任务: task_id={task_id}", "sync_to_feature")
            
            # 同步文件信息
            if main_file:
                existing_file = feature_db.query(FeatureAnalysisFile).filter(FeatureAnalysisFile.id == main_file.id).first()
                
                if existing_file:
                    existing_file.file_name = main_file.file_name
                    existing_file.file_path = main_file.file_path
                    existing_file.extract_path = main_file.extract_path
                    existing_file.file_size = main_file.file_size
                    existing_file.status = main_file.status
                    existing_file.task_id = task_id  # 确保task_id正确
                else:
                    feature_file = FeatureAnalysisFile(
                        id=main_file.id,
                        task_id=task_id,  # 使用传入的task_id，而不是main_file.task_id
                        file_name=main_file.file_name,
                        file_path=main_file.file_path,
                        extract_path=main_file.extract_path,
                        file_size=main_file.file_size,
                        status=main_file.status
                    )
                    feature_db.add(feature_file)
                    log_debug(f"同步文件到功能审查库: file_id={main_file.id}", "sync_to_feature")
            
            feature_db.commit()
            log_info(f"✅ 任务数据已同步到功能审查库: task_id={task_id}", "sync_to_feature")
            return True
            
        except Exception as e:
            feature_db.rollback()
            log_error(f"同步到功能审查库失败: task_id={task_id}", "sync_to_feature", e)
            return False
        finally:
            feature_db.close()
            
    except Exception as e:
        log_error(f"同步任务到功能审查库异常: task_id={task_id}", "sync_to_feature", e)
        return False

