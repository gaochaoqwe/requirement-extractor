#!/usr/bin/env python3
"""
同步配置文件中的勾选状态到数据库
使用方法：python sync_config_to_db.py
"""
import json
import os
import sys
from pathlib import Path

# 设置后端目录
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parents[3]  # 向上4层到 backend
os.chdir(backend_dir)

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(str(env_file))
        print(f"[INFO] 已加载环境变量文件: {env_file}")
except ImportError:
    pass

# 直接配置数据库连接（不依赖复杂导入链）
POSTGRES_HOST = os.getenv("FPGA_POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("FPGA_POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("FPGA_POSTGRES_DB", "fpga_static_analysis_filter")
POSTGRES_USER = os.getenv("FPGA_POSTGRES_USER", "fpga_analysis")
POSTGRES_PASSWORD = os.getenv("FPGA_POSTGRES_PASSWORD", "123456")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

print(f"[INFO] 数据库: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

# 使用 SQLAlchemy 直接操作
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class FPGARule(Base):
    """FPGA规则表映射"""
    __tablename__ = "fpga_rules"
    
    id = Column(Integer, primary_key=True)
    rule_code = Column(String(50), unique=True, nullable=False)
    rule_content = Column(Text, nullable=False)
    language = Column(String(20), nullable=False)
    rule_type = Column(String(20), nullable=False)
    category = Column(String(100), nullable=True)
    chapter = Column(String(50), nullable=True)
    sequence = Column(Integer, nullable=True)
    accuracy_type = Column(String(20), nullable=False, default='accurate')
    is_selected = Column(Boolean, default=True)  # 这是我们要同步的字段
    issue_title = Column(Text, nullable=True)
    impact_analysis = Column(Text, nullable=True)
    fix_suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def sync_config_to_database():
    """将配置文件中的勾选状态同步到数据库"""
    try:
        # 读取配置文件
        config_file = Path(__file__).parent.parent / "config" / "default_selected_rules.json"
        if not config_file.exists():
            print(f"[ERROR] 配置文件不存在: {config_file}")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        selected_rules = config.get("gjb_rules", [])
        print(f"[INFO] 从配置文件读取到 {len(selected_rules)} 条勾选规则")
        
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # 1. 先将所有规则设为未勾选
            all_rules = session.query(FPGARule).all()
            for rule in all_rules:
                rule.is_selected = False
            print(f"[INFO] 已将 {len(all_rules)} 条规则的 is_selected 重置为 False")
            
            # 2. 将选中的规则设为 True
            selected_count = 0
            not_found_rules = []
            for rule_code in selected_rules:
                rule = session.query(FPGARule).filter(FPGARule.rule_code == rule_code).first()
                if rule:
                    rule.is_selected = True
                    selected_count += 1
                else:
                    not_found_rules.append(rule_code)
            
            session.commit()
            print(f"[SUCCESS] 同步完成！共设置 {selected_count} 条规则为已勾选")
            
            if not_found_rules:
                print(f"[WARNING] 以下规则在数据库中未找到: {not_found_rules}")
            
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            engine.dispose()
            
    except Exception as e:
        print(f"[ERROR] 同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = sync_config_to_database()
    sys.exit(0 if success else 1)
