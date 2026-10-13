"""
需求管理业务逻辑服务
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Dict, Any
import logging
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.app.databaseManage.dynamicDatabaseManage.db import crud, SessionLocal
    from backend.app.databaseManage.dynamicDatabaseManage.schemas import schemas
    from backend.app.databaseManage.dynamicDatabaseManage.utils import excel_utils
except ImportError:
    try:
        from ..db import crud, SessionLocal
        from ..schemas import schemas
        from ..utils import excel_utils
    except ImportError:
        # 如果都失败了，尝试直接导入
        try:
            import crud
            import schemas
            import excel_utils
            SessionLocal = None
        except ImportError:
            print("警告: 无法导入必要的模块")
            crud = None
            schemas = None
            excel_utils = None
            SessionLocal = None

logger = logging.getLogger(__name__)


class RequirementService:
    """需求管理服务类"""
    
    @staticmethod
    def get_requirements_with_pagination(
        db: Session,
        page: int = 1,
        page_size: int = 50,
        software_category: Optional[str] = None
    ) -> Tuple[List[schemas.OptoelectronicRequirement], int]:
        """
        分页获取需求记录
        
        Args:
            db: 数据库会话
            page: 页码（从1开始）
            page_size: 每页数量
            software_category: 软件类别筛选
            
        Returns:
            (需求记录列表, 总数)
        """
        skip = (page - 1) * page_size
        requirements = crud.get_requirements(
            db=db,
            skip=skip,
            limit=page_size,
            software_category=software_category
        )
        total = crud.get_requirements_count(db=db, software_category=software_category)
        return requirements, total
    
    @staticmethod
    def create_requirement(
        db: Session,
        requirement_data: schemas.OptoelectronicRequirementCreate
    ) -> schemas.OptoelectronicRequirement:
        """
        创建需求记录
        
        Args:
            db: 数据库会话
            requirement_data: 需求数据
            
        Returns:
            创建的需求记录
        """
        return crud.create_requirement(db=db, requirement=requirement_data)
    
    @staticmethod
    def update_requirement(
        db: Session,
        requirement_id: int,
        update_data: schemas.OptoelectronicRequirementUpdate
    ) -> Optional[schemas.OptoelectronicRequirement]:
        """
        更新需求记录
        
        Args:
            db: 数据库会话
            requirement_id: 需求ID
            update_data: 更新数据
            
        Returns:
            更新后的需求记录，如果不存在返回None
        """
        return crud.update_requirement(
            db=db,
            requirement_id=requirement_id,
            requirement_update=update_data
        )
    
    @staticmethod
    def delete_requirement(db: Session, requirement_id: int) -> bool:
        """
        删除需求记录
        
        Args:
            db: 数据库会话
            requirement_id: 需求ID
            
        Returns:
            是否删除成功
        """
        return crud.delete_requirement(db=db, requirement_id=requirement_id)
    
    @staticmethod
    def import_from_excel(
        db: Session,
        file_content: bytes,
        clear_existing: bool = False
    ) -> Tuple[List[schemas.OptoelectronicRequirement], str]:
        """
        从Excel文件导入需求记录（智能导入）
        
        Args:
            db: 数据库会话
            file_content: Excel文件内容
            clear_existing: 是否清除现有数据
            
        Returns:
            (导入的需求记录列表, 状态消息)
            
        Raises:
            ValueError: 文件格式错误或导入失败
        """
        try:
            # 解析Excel文件，使用第一个工作表
            requirements_data = excel_utils.parse_excel_file(file_content, sheet_name=None)
            
            # 如果需要，清除现有数据
            if clear_existing:
                deleted_count = crud.delete_all_requirements(db)
                logger.info(f"清除了 {deleted_count} 条现有记录")
            
            # 批量导入
            imported_requirements = crud.create_requirements_batch(
                db=db,
                requirements=requirements_data
            )
            
            message = f"成功导入 {len(imported_requirements)} 条记录"
            if clear_existing:
                message += f"（已清除 {deleted_count} 条原有记录）"
            
            logger.info(message)
            return imported_requirements, message
            
        except Exception as e:
            logger.error(f"Excel导入失败: {str(e)}")
            raise ValueError(f"Excel导入失败: {str(e)}")
    
    @staticmethod
    def normal_import_from_excel(
        db: Session,
        file_content: bytes
    ) -> Tuple[Dict[str, Any], str]:
        """
        普通导入Excel文件，支持模糊匹配和追加功能
        
        Args:
            db: 数据库会话
            file_content: Excel文件内容
            
        Returns:
            (导入结果统计, 状态消息)
        """
        try:
            # 解析Excel文件，使用第一个工作表
            excel_data = excel_utils.parse_excel_for_normal_import(file_content, sheet_name=None)
            
            # 统计信息
            stats = {
                "total_rows": len(excel_data),
                "matched_count": 0,
                "appended_count": 0,
                "created_count": 0,
                "errors": []
            }
            
            for row_data in excel_data:
                try:
                    test_item_name = row_data["test_item_name"]
                    software_category = row_data["software_category"]
                    test_content = row_data["test_item_description"]
                    test_method = row_data["test_method"]
                    
                    # 查找匹配的测试项
                    matched_requirement = crud.find_matching_requirement(db, test_item_name)
                    
                    if matched_requirement:
                        # 找到匹配项，追加测试内容和测试方法
                        if test_content and test_method:
                            crud.append_test_content_and_method(
                                db, 
                                matched_requirement.id, 
                                test_content, 
                                test_method
                            )
                            stats["appended_count"] += 1
                        stats["matched_count"] += 1
                    else:
                        # 未找到匹配项，创建新记录
                        new_requirement_data = {
                            "software_category": software_category,
                            "test_item_name": test_item_name,
                            "test_item_description": test_content,
                            "test_method": test_method
                        }
                        crud.create_requirement(db, new_requirement_data)
                        stats["created_count"] += 1
                            
                except Exception as e:
                    error_msg = f"第{row_data['row_number']}行处理失败: {str(e)}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # 生成状态消息
            message = f"普通导入完成：共处理 {stats['total_rows']} 行数据，"
            message += f"匹配并追加 {stats['appended_count']} 项，"
            message += f"新建 {stats['created_count']} 项"
            
            if stats["errors"]:
                message += f"，{len(stats['errors'])} 行处理失败"
            
            logger.info(message)
            return stats, message
            
        except Exception as e:
            logger.error(f"普通导入失败: {str(e)}")
            raise ValueError(f"普通导入失败: {str(e)}")
    
    @staticmethod
    def export_to_excel(
        db: Session,
        software_category: Optional[str] = None
    ) -> bytes:
        """
        导出需求记录为Excel文件
        
        Args:
            db: 数据库会话
            software_category: 软件类别筛选
            
        Returns:
            Excel文件字节内容
        """
        requirements = crud.get_requirements(
            db=db,
            skip=0,
            limit=10000,  # 导出时获取所有数据
            software_category=software_category
        )
        
        if not requirements:
            raise ValueError("没有找到需求记录")
        
        return excel_utils.export_to_excel(requirements)
    
    @staticmethod
    def validate_excel_file(file_content: bytes) -> dict:
        """
        验证Excel文件结构
        
        Args:
            file_content: Excel文件内容
            
        Returns:
            验证结果字典
        """
        return excel_utils.validate_excel_structure(file_content, sheet_name=None)
    
    @staticmethod
    def get_statistics(db: Session) -> dict:
        """
        获取需求记录统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            统计信息字典
        """
        total_count = crud.get_requirements_count(db)
        
        # 按软件类别统计
        all_requirements = crud.get_requirements(db, skip=0, limit=10000)
        category_stats = {}
        for req in all_requirements:
            category = req.software_category
            if category in category_stats:
                category_stats[category] += 1
            else:
                category_stats[category] = 1
        
        return {
            "total_count": total_count,
            "category_stats": category_stats,
            "categories": list(category_stats.keys())
        }
    
    @staticmethod
    def get_requirements_sorted_by_category(db: Session) -> List[schemas.OptoelectronicRequirement]:
        """
        获取按软件类别排序的需求记录
        
        Args:
            db: 数据库会话
            
        Returns:
            排序后的需求记录列表
        """
        return crud.get_requirements_by_category_sorted(db) 
    
    @staticmethod
    def import_multisheet_7cols(
        db: Session,
        file_content: bytes,
        mode: str = "full"
    ) -> Dict[str, Any]:
        """
        导入多Sheet（7列结构）：按Sheet名称映射至对应表。
        mode: "full" -> 清空对应表后全量导入；"incremental" -> 仅新增不存在的测试项（以测试项名称+内容+方法判重）。
        返回每个Sheet的统计：created/skipped/deleted。
        """
        if mode not in ("full", "incremental"):
            raise ValueError("mode 仅支持 'full' 或 'incremental'")

        # 解析Excel
        parsed = excel_utils.parse_multisheet_requirements(file_content)
        stats: Dict[str, Any] = {}

        for sheet_name, rows in parsed.items():
            model = getattr(crud, "MODEL_MAP", {}).get(sheet_name)
            if model is None:
                logger.warning(f"未找到Sheet到模型的映射，跳过: {sheet_name}")
                continue

            # 🚀 优化: 添加详细日志，便于调试排序问题
            logger.info(f"开始处理Sheet: {sheet_name}, 共{len(rows)}条记录")
            for i, row in enumerate(rows[:3]):  # 只记录前3条用于调试
                logger.debug(f"  第{i+1}条: [{row.get('software_category')}] {row.get('test_item_name')} (Excel行{row.get('_excel_row_number')})")

            sheet_stat = {"created": 0, "skipped": 0, "deleted": 0}

            if mode == "full":
                # 清空表
                deleted = crud.delete_all_by_model(db, model)
                sheet_stat["deleted"] = deleted
                logger.info(f"清空{sheet_name}表: 删除{deleted}条记录")
                
                # 全量创建
                created = crud.create_batch_by_model(db, model, rows)
                sheet_stat["created"] = created
                logger.info(f"批量创建{sheet_name}表: 创建{created}条记录")
            else:
                # 增量模式：逐条判重
                created_count = 0
                skipped_count = 0
                for r in rows:
                    exists = crud.exists_row(
                        db,
                        model,
                        test_item_name=r.get("test_item_name"),
                        test_content=r.get("test_content"),
                        test_method=r.get("test_method"),
                    )
                    if exists:
                        skipped_count += 1
                        continue
                    obj = crud.create_row_with_order(db, model, r)
                    created_count += 1
                db.commit()
                sheet_stat["created"] = created_count
                sheet_stat["skipped"] = skipped_count

            stats[sheet_name] = sheet_stat

        if not stats:
            raise ValueError("导入结果为空：未匹配到任何目标Sheet/表")

        return {"mode": mode, "sheets": stats}

    # ===================== 七列表：分页列表与导出 =====================
    @staticmethod
    def get_sevencols_with_pagination(
        db: Session,
        table: str,
        page: int = 1,
        page_size: int = 50,
        software_category: Optional[str] = None,
        test_item_name: Optional[str] = None,
    ) -> Tuple[List[Any], int]:
        """按表名（中文：转塔/对抗告警/光雷/吊舱）分页查询七列表数据。"""
        import time
        start_time = time.time()
        
        try:
            model = getattr(crud, "MODEL_MAP", {}).get(table)
            if model is None:
                raise ValueError(f"未知的表/Sheet名称: {table}")
            
            # 🚀 优化1: 限制查询范围，避免超大分页
            if page > 1000:  # 限制最大页数
                raise ValueError(f"页数过大: {page}，最大支持1000页")
            
            skip = (page - 1) * page_size
            
            # 🚀 优化2: 并行查询数据和总数（如果数据库支持）
            logger.info(f"开始数据库查询: model={model.__name__}, skip={skip}, limit={page_size}")
            
            items = crud.query_by_model(
                db,
                model,
                skip=skip,
                limit=page_size,
                software_category=software_category,
                test_item_name=test_item_name,
            )
            
            # 🚀 优化3: 如果是第一页且返回数据少于页面大小，可以直接计算总数
            if page == 1 and len(items) < page_size:
                total = len(items)
                logger.info(f"第一页数据不足，直接计算总数: {total}")
            else:
                total = crud.count_by_model(db, model, software_category=software_category, test_item_name=test_item_name)
            
            elapsed = time.time() - start_time
            logger.info(f"数据库查询完成: 耗时{elapsed:.2f}s, 返回{len(items)}条记录")
            
            return items, total
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"数据库查询失败 (耗时{elapsed:.2f}s): {e}")
            raise

    @staticmethod
    def export_sevencols_by_table(
        db: Session,
        table: str,
        software_category: Optional[str] = None,
        test_item_name: Optional[str] = None,
    ) -> bytes:
        """导出指定七列表为Excel二进制。"""
        model = getattr(crud, "MODEL_MAP", {}).get(table)
        if model is None:
            raise ValueError(f"未知的表/Sheet名称: {table}")
        # 取全量（做一个较大上限）
        records = crud.query_by_model(
            db,
            model,
            skip=0,
            limit=100000,
            software_category=software_category,
            test_item_name=test_item_name,
        )
        if not records:
            raise ValueError("无可导出的记录")
        title = table or "七列需求表"
        return excel_utils.export_sevencols_to_excel(records, sheet_title=title)