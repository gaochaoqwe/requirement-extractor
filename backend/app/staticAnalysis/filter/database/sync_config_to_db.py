#!/usr/bin/env python3
"""
同步配置文件中的勾选状态到数据库（C/C++版本）
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
POSTGRES_HOST = os.getenv("STATIC_POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("STATIC_POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("STATIC_POSTGRES_DB", "static_analysis_filter")
POSTGRES_USER = os.getenv("STATIC_POSTGRES_USER", "static_analysis")
POSTGRES_PASSWORD = os.getenv("STATIC_POSTGRES_PASSWORD", "123456")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

print(f"[INFO] 数据库: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

# 使用 SQLAlchemy 直接操作
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class GJB8114Rule(Base):
    """GJB8114规则表映射"""
    __tablename__ = "gjb8114_rules"
    
    id = Column(Integer, primary_key=True)
    rule_code = Column(String(50), unique=True, nullable=False)
    rule_name = Column(Text, nullable=False)
    rule_description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    accuracy_type = Column(String(20), nullable=False, default='accurate')
    is_selected = Column(Boolean, default=True)  # 这是我们要同步的字段
    analysis_complexity = Column(Text, nullable=True)
    detection_method = Column(Text, nullable=True)
    problem_name = Column(Text, nullable=False, default="")
    requirement_description = Column(Text, nullable=False, default="")
    impact_analysis = Column(Text, nullable=False, default="")
    improvement_suggestion = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CWERule(Base):
    """CWE规则表映射"""
    __tablename__ = "cwe_rules"
    
    id = Column(Integer, primary_key=True)
    rule_code = Column(String(50), unique=True, nullable=False)
    rule_name = Column(Text, nullable=False)
    accuracy_type = Column(String(20), nullable=False, default='accurate')
    is_selected = Column(Boolean, default=True)  # 这是我们要同步的字段
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    problem_name = Column(Text, nullable=False, default="")
    requirement_description = Column(Text, nullable=False, default="")
    impact_analysis = Column(Text, nullable=False, default="")
    improvement_suggestion = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def convert_gjb_format(rule_code: str) -> str:
    """将 A-1-2 格式转换为 GJB_R_01_01_02 格式"""
    try:
        parts = rule_code.split('-')
        if len(parts) == 3:
            section, chapter, rule = parts
            return f"GJB_R_{section.zfill(2)}_{chapter.zfill(2)}_{rule.zfill(2)}"
    except Exception:
        pass
    return rule_code

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
        
        gjb_rules = config.get("gjb_rules", [])
        cwe_rules = config.get("cwe_rules", [])
        
        print(f"[INFO] 从配置文件读取到 GJB规则: {len(gjb_rules)} 条")
        print(f"[INFO] 从配置文件读取到 CWE规则: {len(cwe_rules)} 条")
        
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # 1. 同步GJB规则勾选状态
            all_gjb_rules = session.query(GJB8114Rule).all()
            for rule in all_gjb_rules:
                rule.is_selected = False
            print(f"[INFO] 已将 {len(all_gjb_rules)} 条GJB规则的 is_selected 重置为 False")
            
            selected_count = 0
            not_found_rules = []
            for rule_code in gjb_rules:
                converted_code = convert_gjb_format(rule_code)
                rule = session.query(GJB8114Rule).filter(GJB8114Rule.rule_code == converted_code).first()
                if rule:
                    rule.is_selected = True
                    selected_count += 1
                    print(f"[INFO] 设置GJB规则为已选中: {converted_code}")
                else:
                    not_found_rules.append(f"{rule_code} ({converted_code})")
            
            print(f"[INFO] GJB规则同步完成，共设置 {selected_count} 条规则为已勾选")
            if not_found_rules:
                print(f"[WARNING] 以下GJB规则在数据库中未找到: {not_found_rules}")
            
            # 2. 同步CWE规则勾选状态
            all_cwe_rules = session.query(CWERule).all()
            for rule in all_cwe_rules:
                rule.is_selected = False
            print(f"[INFO] 已将 {len(all_cwe_rules)} 条CWE规则的 is_selected 重置为 False")
            
            selected_count = 0
            not_found_rules = []
            for rule_code in cwe_rules:
                rule = session.query(CWERule).filter(CWERule.rule_code == rule_code).first()
                if rule:
                    rule.is_selected = True
                    selected_count += 1
                    print(f"[INFO] 设置CWE规则为已选中: {rule_code}")
                else:
                    not_found_rules.append(rule_code)
            
            print(f"[INFO] CWE规则同步完成，共设置 {selected_count} 条规则为已勾选")
            if not_found_rules:
                print(f"[WARNING] 以下CWE规则在数据库中未找到: {not_found_rules}")
            
            session.commit()
            print(f"[SUCCESS] 同步完成！")
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
