from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base


class OptoelectronicRequirement(Base):
    """光电需求分析表模型"""
    __tablename__ = "optoelectronic_requirements"

    id = Column(Integer, primary_key=True, index=True)
    software_category = Column(String(100), nullable=False, comment="软件类别")
    test_item_name = Column(String(200), nullable=False, comment="测试项名称")
    test_item_description = Column(Text, nullable=True, comment="测试项描述")
    test_method = Column(Text, nullable=True, comment="测试方法")
    category_order = Column(Integer, nullable=False, default=0, comment="软件类别排序")
    item_order = Column(Integer, nullable=False, default=0, comment="测试项排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ================= 多Sheet普通导入用的四张业务表 =================

class TurretRequirement(Base):
    """转塔 - 需求数据表"""
    __tablename__ = "turret_requirements"

    id = Column(Integer, primary_key=True, index=True)
    software_category = Column(String(100), nullable=False, comment="软件类别")
    test_item_name = Column(String(200), nullable=False, comment="测试项名称")
    test_content = Column(Text, nullable=True, comment="测试内容")
    test_method = Column(Text, nullable=True, comment="测试方法")
    case_template_name = Column(String(200), nullable=True, comment="用例模板（用例名称）")
    case_template_input = Column(Text, nullable=True, comment="用例模板（输入条件）")
    case_template_expected = Column(Text, nullable=True, comment="用例模板（预期结果）")
    submitter = Column(String(100), nullable=True, comment="提交人")
    # 排序（按类别顺序 + 行内顺序）
    category_order = Column(Integer, nullable=False, default=0, comment="软件类别排序")
    item_order = Column(Integer, nullable=False, default=0, comment="条目排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ExportTask(Base):
    """异步智能导出任务表（用于跨进程/多实例共享进度）"""

    __tablename__ = "export_tasks"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), nullable=False, default="processing")
    progress = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    filename = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CountermeasureAlarmRequirement(Base):
    """对抗告警 - 需求数据表"""
    __tablename__ = "countermeasure_alarm_requirements"

    id = Column(Integer, primary_key=True, index=True)
    software_category = Column(String(100), nullable=False, comment="软件类别")
    test_item_name = Column(String(200), nullable=False, comment="测试项名称")
    test_content = Column(Text, nullable=True, comment="测试内容")
    test_method = Column(Text, nullable=True, comment="测试方法")
    case_template_name = Column(String(200), nullable=True, comment="用例模板（用例名称）")
    case_template_input = Column(Text, nullable=True, comment="用例模板（输入条件）")
    case_template_expected = Column(Text, nullable=True, comment="用例模板（预期结果）")
    submitter = Column(String(100), nullable=True, comment="提交人")
    category_order = Column(Integer, nullable=False, default=0, comment="软件类别排序")
    item_order = Column(Integer, nullable=False, default=0, comment="条目排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OptoRadarRequirement(Base):
    """光雷 - 需求数据表"""
    __tablename__ = "opto_radar_requirements"

    id = Column(Integer, primary_key=True, index=True)
    software_category = Column(String(100), nullable=False, comment="软件类别")
    test_item_name = Column(String(200), nullable=False, comment="测试项名称")
    test_content = Column(Text, nullable=True, comment="测试内容")
    test_method = Column(Text, nullable=True, comment="测试方法")
    case_template_name = Column(String(200), nullable=True, comment="用例模板（用例名称）")
    case_template_input = Column(Text, nullable=True, comment="用例模板（输入条件）")
    case_template_expected = Column(Text, nullable=True, comment="用例模板（预期结果）")
    submitter = Column(String(100), nullable=True, comment="提交人")
    category_order = Column(Integer, nullable=False, default=0, comment="软件类别排序")
    item_order = Column(Integer, nullable=False, default=0, comment="条目排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PodRequirement(Base):
    """吊舱 - 需求数据表"""
    __tablename__ = "pod_requirements"

    id = Column(Integer, primary_key=True, index=True)
    software_category = Column(String(100), nullable=False, comment="软件类别")
    test_item_name = Column(String(200), nullable=False, comment="测试项名称")
    test_content = Column(Text, nullable=True, comment="测试内容")
    test_method = Column(Text, nullable=True, comment="测试方法")
    case_template_name = Column(String(200), nullable=True, comment="用例模板（用例名称）")
    case_template_input = Column(Text, nullable=True, comment="用例模板（输入条件）")
    case_template_expected = Column(Text, nullable=True, comment="用例模板（预期结果）")
    submitter = Column(String(100), nullable=True, comment="提交人")
    category_order = Column(Integer, nullable=False, default=0, comment="软件类别排序")
    item_order = Column(Integer, nullable=False, default=0, comment="条目排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())