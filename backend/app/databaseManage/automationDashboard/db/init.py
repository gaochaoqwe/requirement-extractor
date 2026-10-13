from .database import engine, SessionLocal, Base
from .models import DashboardConfig, PhaseConfig, SubStepConfig
import logging

logger = logging.getLogger(__name__)


def init_db():
    Base.metadata.create_all(bind=engine)
    _seed_default_data()


def _seed_default_data():
    db = SessionLocal()
    try:
        if db.query(DashboardConfig).count() > 0:
            return

        configs = [
            {
                "name": "配置项测试",
                "description": "配置项软件测评自动化配置",
                "phases": [
                    {
                        "name": "文档审查", "order_index": 0, "weight": 5.0,
                        "automation_level": 75.0, "icon": "doc", "color": "#4A90D9",
                        "sub_steps": [
                            {"name": "问题发现", "order_index": 0, "weight": 90.0, "automation_level": 85.0},
                            {"name": "编写问题单", "order_index": 1, "weight": 10.0, "automation_level": 40.0},
                        ]
                    },
                    {
                        "name": "静态分析", "order_index": 1, "weight": 10.0,
                        "automation_level": 60.0, "icon": "analysis", "color": "#7B68EE",
                        "sub_steps": [
                            {"name": "问题分类", "order_index": 0, "weight": 30.0, "automation_level": 70.0},
                            {"name": "问题确认", "order_index": 1, "weight": 40.0, "automation_level": 50.0},
                            {"name": "问题单编写", "order_index": 2, "weight": 30.0, "automation_level": 60.0},
                        ]
                    },
                    {
                        "name": "代码审查", "order_index": 2, "weight": 25.0,
                        "automation_level": 55.0, "icon": "code", "color": "#E87040",
                        "sub_steps": [
                            {"name": "问题发现", "order_index": 0, "weight": 70.0, "automation_level": 65.0},
                            {"name": "问题单编写", "order_index": 1, "weight": 30.0, "automation_level": 30.0},
                        ]
                    },
                    {
                        "name": "动态测试", "order_index": 3, "weight": 50.0,
                        "automation_level": 40.0, "icon": "dynamic", "color": "#2ECC71",
                        "sub_steps": [
                            {"name": "表单生成", "order_index": 0, "weight": 15.0, "automation_level": 80.0},
                            {"name": "测试项划分", "order_index": 1, "weight": 20.0, "automation_level": 30.0},
                            {"name": "测试用例单（步骤和预期结果）", "order_index": 2, "weight": 25.0, "automation_level": 45.0},
                            {"name": "测试项描述和测试方法", "order_index": 3, "weight": 20.0, "automation_level": 50.0},
                            {"name": "测试用例名称编号描述", "order_index": 4, "weight": 20.0, "automation_level": 35.0},
                        ]
                    },
                    {
                        "name": "报告编写", "order_index": 4, "weight": 10.0,
                        "automation_level": 25.0, "icon": "report", "color": "#F39C12",
                        "sub_steps": [
                            {"name": "章节1", "order_index": 0, "weight": 20.0, "automation_level": 30.0},
                            {"name": "章节2", "order_index": 1, "weight": 20.0, "automation_level": 25.0},
                            {"name": "章节3", "order_index": 2, "weight": 20.0, "automation_level": 20.0},
                            {"name": "章节4", "order_index": 3, "weight": 20.0, "automation_level": 25.0},
                            {"name": "章节5", "order_index": 4, "weight": 20.0, "automation_level": 25.0},
                        ]
                    },
                ]
            },
            {
                "name": "鉴定测评",
                "description": "鉴定测评软件测评自动化配置",
                "phases": [
                    {
                        "name": "文档审查", "order_index": 0, "weight": 5.0,
                        "automation_level": 75.0, "icon": "doc", "color": "#4A90D9",
                        "sub_steps": [
                            {"name": "问题发现", "order_index": 0, "weight": 90.0, "automation_level": 85.0},
                            {"name": "编写问题单", "order_index": 1, "weight": 10.0, "automation_level": 40.0},
                        ]
                    },
                    {
                        "name": "静态分析", "order_index": 1, "weight": 10.0,
                        "automation_level": 60.0, "icon": "analysis", "color": "#7B68EE",
                        "sub_steps": [
                            {"name": "问题分类", "order_index": 0, "weight": 30.0, "automation_level": 70.0},
                            {"name": "问题确认", "order_index": 1, "weight": 40.0, "automation_level": 50.0},
                            {"name": "问题单编写", "order_index": 2, "weight": 30.0, "automation_level": 60.0},
                        ]
                    },
                    {
                        "name": "代码审查", "order_index": 2, "weight": 20.0,
                        "automation_level": 55.0, "icon": "code", "color": "#E87040",
                        "sub_steps": [
                            {"name": "问题发现", "order_index": 0, "weight": 70.0, "automation_level": 65.0},
                            {"name": "问题单编写", "order_index": 1, "weight": 30.0, "automation_level": 30.0},
                        ]
                    },
                    {
                        "name": "动态测试", "order_index": 3, "weight": 45.0,
                        "automation_level": 40.0, "icon": "dynamic", "color": "#2ECC71",
                        "sub_steps": [
                            {"name": "表单生成", "order_index": 0, "weight": 15.0, "automation_level": 80.0},
                            {"name": "测试项划分", "order_index": 1, "weight": 20.0, "automation_level": 30.0},
                            {"name": "测试用例单（步骤和预期结果）", "order_index": 2, "weight": 25.0, "automation_level": 45.0},
                            {"name": "测试项描述和测试方法", "order_index": 3, "weight": 20.0, "automation_level": 50.0},
                            {"name": "测试用例名称编号描述", "order_index": 4, "weight": 20.0, "automation_level": 35.0},
                        ]
                    },
                    {
                        "name": "报告编写", "order_index": 4, "weight": 20.0,
                        "automation_level": 25.0, "icon": "report", "color": "#F39C12",
                        "sub_steps": [
                            {"name": "章节1", "order_index": 0, "weight": 20.0, "automation_level": 30.0},
                            {"name": "章节2", "order_index": 1, "weight": 20.0, "automation_level": 25.0},
                            {"name": "章节3", "order_index": 2, "weight": 20.0, "automation_level": 20.0},
                            {"name": "章节4", "order_index": 3, "weight": 20.0, "automation_level": 25.0},
                            {"name": "章节5", "order_index": 4, "weight": 20.0, "automation_level": 25.0},
                        ]
                    },
                ]
            }
        ]

        for cfg_data in configs:
            cfg = DashboardConfig(name=cfg_data["name"], description=cfg_data["description"])
            db.add(cfg)
            db.flush()
            for ph_data in cfg_data["phases"]:
                ph = PhaseConfig(
                    dashboard_id=cfg.id,
                    name=ph_data["name"],
                    order_index=ph_data["order_index"],
                    weight=ph_data["weight"],
                    automation_level=ph_data["automation_level"],
                    icon=ph_data["icon"],
                    color=ph_data["color"],
                )
                db.add(ph)
                db.flush()
                for ss_data in ph_data["sub_steps"]:
                    ss = SubStepConfig(
                        phase_id=ph.id,
                        name=ss_data["name"],
                        order_index=ss_data["order_index"],
                        weight=ss_data["weight"],
                        automation_level=ss_data["automation_level"],
                    )
                    db.add(ss)

        db.commit()
        logger.info("自动化仪表板默认数据已初始化")

    except Exception as e:
        db.rollback()
        logger.error(f"初始化默认数据失败: {e}")
    finally:
        db.close()
