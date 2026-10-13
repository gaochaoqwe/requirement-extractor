"""
数据库管理模块的数据库初始化
"""
import logging
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.join(current_dir, '..', '..', '..', '..')
# 添加到Python路径
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

# 软件类别排序映射
CATEGORY_ORDER_MAP = {
    "通用": 1,
    "随动": 2,
    "图像": 3,
    "红外": 4,
    "激光": 5,
    "分色滤光": 6,
    "手柄": 7
}

# 默认数据
DEFAULT_DATA = [
    # 通用类别
    {
        "software_category": "通用",
        "test_item_name": "CAN初始化",
        "test_item_description": "1、测试软件是否完成对所有变量的初始化。",
        "test_method": "1、使用科代扫描工具对软件进行扫描。检测及变量是否完成初始化。2、在软件进行初始化的地方打断点,通过动态测试验证。",
        "category_order": 1,
        "item_order": 1
    },
    {
        "software_category": "通用",
        "test_item_name": "上电自检",
        "test_item_description": "1、测试软件上电自检功能是否正常,是否能对故障过载进行检测。",
        "test_method": "1、测试软件能否正常通过上电自检。2、通过代码插桩设置上电自检故障,软件正常运行,通过检测仪的状态监控界面查看。",
        "category_order": 1,
        "item_order": 2
    },
    # 随动类别
    {
        "software_category": "随动",
        "test_item_name": "余量",
        "test_item_description": "1、测试软件运行余量是否满足需求大于30%的要求。",
        "test_method": "1、通过调试计算机中软件编译环境的内存监控功能查看软件的内存余量是否大于30%。2、通过调试计算机中软件编译环境的内存监控功能查看软件的内存余量是否大于30%。",
        "category_order": 2,
        "item_order": 1
    },
    {
        "software_category": "随动",
        "test_item_name": "其他",
        "test_item_description": "1、测试2、测试3、测试",
        "test_method": "1、看门狗功能测试:在软件的关键代码路径中插入看门狗代码,例如 while(1){},运行软件,观察看门狗代码是否被触发。",
        "category_order": 2,
        "item_order": 2
    },
    # 图像类别
    {
        "software_category": "图像",
        "test_item_name": "安全",
        "test_item_description": "1、测试软件安全功能是否正常。",
        "test_method": "1、通过检测仪指令发送界面发送str1指令,通过检测仪的图像显示界面及状态监控界面观察测试软件对str1指令的响应。",
        "category_order": 3,
        "item_order": 1
    },
    {
        "software_category": "图像",
        "test_item_name": "可靠性",
        "test_item_description": "1、测试软件可靠性功能是否正常。",
        "test_method": "1、通过检测仪指令发送界面发送str1指令,通过检测仪的图像显示界面及状态监控界面观察测试软件对str1指令的响应。",
        "category_order": 3,
        "item_order": 2
    },
    # 红外类别
    {
        "software_category": "红外",
        "test_item_name": "修改控制器满偏故障检",
        "test_item_description": "1、测试2、测试3、测试",
        "test_method": "1、通过检测仪指令发送界面发送str1指令,通过检测仪的图像显示界面及状态监控界面观察测试软件对str1指令的响应。",
        "category_order": 4,
        "item_order": 1
    },
    # 激光类别
    {
        "software_category": "激光",
        "test_item_name": "用户身份验证功能",
        "test_item_description": "验证用户登录系统时的身份验证机制,包括用户名密码验证、权限控制等。",
        "test_method": "1、测试用户登录功能。2、测试权限控制功能。3、测试密码加密功能。",
        "category_order": 5,
        "item_order": 1
    },
    # 分色滤光类别
    {
        "software_category": "分色滤光",
        "test_item_name": "性能",
        "test_item_description": "1、测试软件性能是否满足要求。",
        "test_method": "1、性能测试方法1。2、性能测试方法2。3、性能测试方法3。",
        "category_order": 6,
        "item_order": 1
    },
    # 手柄类别
    {
        "software_category": "手柄",
        "test_item_name": "实时通知推送功能",
        "test_item_description": "1、测试软件实时通知推送功能是否正常。",
        "test_method": "1、测试通知推送功能。2、测试实时性要求。3、测试推送失败处理。",
        "category_order": 7,
        "item_order": 1
    }
]


def init_db():
    """初始化数据库管理模块的数据库表"""
    try:
        # 尝试导入数据库模块
        from .database import engine, Base, SessionLocal
        # 导入models模块以确保所有模型类被注册到Base
        from . import models  # noqa: F401
        from .models import OptoelectronicRequirement
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库管理模块数据库表创建成功")
        
        # 插入默认数据
        insert_default_data(SessionLocal, OptoelectronicRequirement)
        
        return True
    except ImportError as e:
        logger.error(f"数据库模块导入失败: {e}")
        print(f"警告: 数据库模块导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"数据库管理模块数据库表创建失败: {e}")
        print(f"错误: 数据库管理模块数据库表创建失败: {e}")
        return False


def insert_default_data(SessionLocal, OptoelectronicRequirement):
    """插入默认数据"""
    try:
        db = SessionLocal()
        
        # 检查是否已有数据
        existing_count = db.query(OptoelectronicRequirement).count()
        if existing_count > 0:
            logger.info(f"数据库中已有 {existing_count} 条记录，跳过默认数据插入")
            return
        
        # 插入默认数据
        for data_item in DEFAULT_DATA:
            requirement = OptoelectronicRequirement(**data_item)
            db.add(requirement)
        
        db.commit()
        logger.info(f"成功插入 {len(DEFAULT_DATA)} 条默认数据")
        
    except Exception as e:
        logger.error(f"插入默认数据失败: {e}")
        db.rollback()
    finally:
        db.close()


def clear_db():
    """清空数据库中的所有数据（保留表结构）。"""
    try:
        from .database import SessionLocal
        from . import models
        
        db = SessionLocal()
        try:
            # 清空四个业务表的数据
            tables_to_clear = [
                models.TurretRequirement,
                models.CountermeasureAlarmRequirement, 
                models.OptoRadarRequirement,
                models.PodRequirement,
                models.OptoelectronicRequirement  # 原有的光电需求表
            ]
            
            total_deleted = 0
            for table_model in tables_to_clear:
                if hasattr(table_model, '__tablename__'):
                    count = db.query(table_model).count()
                    if count > 0:
                        db.query(table_model).delete()
                        logger.info(f"已清空表 {table_model.__tablename__}: {count} 条记录")
                        total_deleted += count
                    else:
                        logger.info(f"表 {table_model.__tablename__} 已经为空")
            
            db.commit()
            logger.info(f"数据库清空完成，共删除 {total_deleted} 条记录")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"清空数据库失败: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"清空数据库失败: {e}")
        return False

def reset_db():
    """重置数据库（兼容旧接口，实际调用清空数据库）。"""
    try:
        logger.info("调用重置数据库接口，实际执行清空数据库操作")
        return clear_db()
    except Exception as e:
        logger.error(f"重置数据库失败: {e}")
        return False


if __name__ == "__main__":
    init_db()