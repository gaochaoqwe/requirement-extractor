"""
静态分析问题过滤工具数据库模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

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
    
    # [NEW] 标记问题导出记录（类比函数审查的标记问题导出）
    marked_problems_exported = Column(Boolean, default=False)  # 是否导出过标记问题
    
    # 关联问题项
    issues = relationship("StaticAnalysisIssue", back_populates="session")

class StaticAnalysisIssue(Base):
    """静态分析问题表"""
    __tablename__ = "static_analysis_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("static_analysis_sessions.id"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)  # 在Excel中的行号
    
    # 原始问题信息
    sheet_name = Column(String(255), nullable=True) # 工作表名称
    issue_name = Column(Text, nullable=True)        # 问题名称
    issue_file = Column(Text, nullable=True)        # 问题文件
    issue_line = Column(Text, nullable=True)        # 问题行数
    issue_description = Column(Text, nullable=True) # 问题描述
    gjb_rule_code = Column(String(50), nullable=True) # 提取的GJB规则编号
    
    # 规则分类信息
    rule_type = Column(String(20), nullable=True)   # 'gjb' 或 'cwe'，标识规则类型
    rule_code = Column(String(50), nullable=True)   # 匹配的规则编号
    rule_accuracy_type = Column(String(20), nullable=True)  # accurate/uncertain/unknown
    
    # 处理后的信息
    issue_location = Column(Text, nullable=True)    # 格式化的问题位置
    issue_summary = Column(Text, nullable=True)     # 问题总结
    is_filtered = Column(Boolean, default=False)    # 是否被过滤掉
    filter_reason = Column(String(255), nullable=True)  # 过滤原因
    
    # AI分析结果
    ai_analyzed = Column(Boolean, default=False)    # 是否经过AI分析
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


class StaticAnalysisMarkedProblem(Base):
    """用户标记的问题表"""
    __tablename__ = "static_analysis_marked_problems"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    rule_type = Column(String(20), nullable=False, index=True)  # 'gjb' 或 'cwe'
    
    # 问题唯一标识（根据问题内容生成的key）
    problem_key = Column(String(512), nullable=False)
    
    # 完整的问题数据（JSON格式存储）
    problem_data = Column(Text, nullable=False)  # JSON字符串
    
    # 标记信息
    marked_by = Column(String(255), nullable=True)  # 标记人（可选）
    marked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
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