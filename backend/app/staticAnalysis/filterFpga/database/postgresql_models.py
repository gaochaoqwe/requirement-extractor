"""
FPGA静态分析过滤工具PostgreSQL数据库模型

包含的表：
1. static_analysis_filter.db的表（会话、问题、标记问题）
2. fpga_rules表（FPGA Verilog和VHDL编码规则）
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# ==================== 静态分析会话和问题表 ====================

class StaticAnalysisSession(Base):
    """静态分析过滤会话表"""
    __tablename__ = "static_analysis_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    codebase_path = Column(String(500), nullable=True)  # 代码库路径
    operator_name = Column(String(100), nullable=True)  # 操作人员姓名（从登录session获取）
    status = Column(String(20), default="pending")  # pending, processing, ai_analyzing, completed, error
    total_issues = Column(Integer, default=0)
    filtered_issues = Column(Integer, default=0)
    ai_analyzed_issues = Column(Integer, default=0)  # AI分析的问题数
    accurate_issues = Column(Integer, default=0)     # 确定规则问题数
    uncertain_issues = Column(Integer, default=0)    # 不确定规则问题数
    output_filename = Column(String(255), nullable=True)
    filter_keywords = Column(Text, nullable=True)  # JSON格式存储过滤关键字
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # [NEW] 问题单准确率反馈（类比函数审查的注释准确率）
    problem_sheet_accuracy_rate = Column(String(50), nullable=True)  # 问题单准确率：50%以下、50%-70%、70%-85%、85%-95%、95%-100%
    problem_sheet_feedback_at = Column(DateTime, nullable=True)  # 反馈时间

    # [NEW] 标记问题导出记录（类比函数审查的标记问题导出）
    marked_problems_exported = Column(Boolean, default=False)  # 是否导出过标记问题

    # 关联问题项
    issues = relationship("StaticAnalysisIssue", back_populates="session", cascade="all, delete-orphan")

class StaticAnalysisIssue(Base):
    """静态分析问题表"""
    __tablename__ = "static_analysis_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("static_analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)  # 在Excel中的行号
    
    # 原始问题信息
    sheet_name = Column(String(255), nullable=True) # 工作表名称
    issue_name = Column(Text, nullable=True)        # 问题名称
    issue_file = Column(Text, nullable=True)        # 问题文件
    issue_line = Column(Text, nullable=True)        # 问题行数
    issue_description = Column(Text, nullable=True) # 问题描述
    gjb_rule_code = Column(String(50), nullable=True, index=True) # 提取的GJB规则编号
    
    # 规则分类信息
    rule_type = Column(String(20), nullable=True, index=True)   # 'gjb' 或 'cwe'，标识规则类型
    rule_code = Column(String(50), nullable=True, index=True)   # 匹配的规则编号
    rule_accuracy_type = Column(String(20), nullable=True, index=True)  # accurate/uncertain/unknown
    
    # 处理后的信息
    issue_location = Column(Text, nullable=True)    # 格式化的问题位置
    issue_summary = Column(Text, nullable=True)     # 问题总结
    is_filtered = Column(Boolean, default=False, index=True)    # 是否被过滤掉
    filter_reason = Column(String(255), nullable=True)  # 过滤原因
    
    # AI分析结果
    ai_analyzed = Column(Boolean, default=False, index=True)    # 是否经过AI分析
    ai_is_real_issue = Column(Boolean, nullable=True)  # AI判断是否为真实问题
    ai_confidence = Column(Float, nullable=True)    # AI置信度 0.0-1.0
    ai_analysis_result = Column(Text, nullable=True)  # AI分析结果
    ai_evidence = Column(Text, nullable=True)       # AI分析证据 (JSON格式)
    ai_reasoning = Column(Text, nullable=True)      # AI推理过程
    ai_recommendations = Column(Text, nullable=True)  # AI建议
    
    # 问题状态：1=新发现(绿色)，2=已查看(灰色)，3=已过滤(灰色)，4=已标记(蓝色)
    problem_status = Column(Integer, default=1, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联会话
    session = relationship("StaticAnalysisSession", back_populates="issues")
    
    # 组合索引
    __table_args__ = (
        Index('idx_task_rule_type', 'task_id', 'rule_type'),
        Index('idx_task_accuracy', 'task_id', 'rule_accuracy_type'),
        Index('idx_task_status', 'task_id', 'problem_status'),
    )

class StaticAnalysisMarkedProblem(Base):
    """用户标记的问题表"""
    __tablename__ = "static_analysis_marked_problems"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    rule_type = Column(String(20), nullable=False, index=True)  # 'gjb' 或 'cwe'
    
    # 问题唯一标识（根据问题内容生成的key）
    problem_key = Column(String(512), nullable=False, index=True)
    
    # 完整的问题数据（JSON格式存储）
    problem_data = Column(Text, nullable=False)  # JSON字符串
    
    # 标记信息
    marked_by = Column(String(255), nullable=True)  # 标记人（可选）
    marked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 组合索引
    __table_args__ = (
        Index('idx_session_rule_type', 'session_id', 'rule_type'),
        Index('idx_session_problem_key', 'session_id', 'problem_key'),
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'session_id': self.session_id,
            'rule_type': self.rule_type,
            'problem_key': self.problem_key,
            'problem_data': json.loads(self.problem_data) if isinstance(self.problem_data, str) else self.problem_data,
            'marked_by': self.marked_by,
            'marked_at': self.marked_at.isoformat() if self.marked_at else None
        }

# ==================== FPGA规则表 ====================

class FPGARule(Base):
    """FPGA编码规则表（包含Verilog和VHDL规则）"""
    __tablename__ = "fpga_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_code = Column(String(50), unique=True, nullable=False, index=True)  # 如 R-2-1, A-1-1, 5.1.1
    rule_content = Column(Text, nullable=False)  # 规则内容描述
    language = Column(String(20), nullable=False, index=True)  # 'Verilog' 或 'VHDL'
    rule_type = Column(String(20), nullable=False, index=True)  # 'mandatory'(强制) 或 'advisory'(建议)
    category = Column(String(100), nullable=True, index=True)  # 规则分类（可选）
    chapter = Column(String(50), nullable=True)  # 章节号（VHDL使用）
    sequence = Column(Integer, nullable=True)  # 序号
    accuracy_type = Column(String(20), nullable=False, default='accurate', index=True)  # accurate / uncertain
    is_selected = Column(Boolean, default=True, index=True)  # 是否被勾选（默认True）
    # 新增：问题单字段模板
    issue_title = Column(Text, nullable=True)         # 问题名称/四段式标题字段
    impact_analysis = Column(Text, nullable=True)     # 影响分析
    fix_suggestion = Column(Text, nullable=True)      # 修改意见
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_language_type', 'language', 'rule_type'),
    )

