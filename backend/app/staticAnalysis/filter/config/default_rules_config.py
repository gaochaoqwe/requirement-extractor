"""
默认规则配置管理
用于保存和加载用户选择的默认规则配置
"""
import json
from pathlib import Path
from typing import Dict, Any, List
import hashlib

# 配置文件路径
CONFIG_DIR = Path(__file__).parent
DEFAULT_RULES_CONFIG_FILE = CONFIG_DIR / "default_selected_rules.json"

# 管理员密码的MD5哈希（默认密码：159357）
ADMIN_PASSWORD_HASH = "36e1a5072c78359066ed7715f5ff3da8"  # MD5("159357")

def verify_admin_password(password: str) -> bool:
    """验证管理员密码"""
    password_hash = hashlib.md5(password.encode()).hexdigest()
    return password_hash == ADMIN_PASSWORD_HASH

def save_default_rules_config(gjb_rules: List[str], cwe_rules: List[str], rule_overrides: Dict[str, Dict[str, str]] = None, custom_filters: Dict[str, List[str]] = None, max_issues_per_rule: int = None) -> bool:
    """
    保存默认规则配置
    
    Args:
        gjb_rules: 选中的GJB8114规则列表
        cwe_rules: 选中的CWE规则列表
        rule_overrides: 规则分类覆盖配置，格式：
            {
                "gjb": {"GJB_R_01_07_11": "uncertain"},
                "cwe": {"S_01_01": "accurate"}
            }
        custom_filters: 自定义关键词过滤配置，格式：
            {
                "GJB_R_01_01_01": ["关键词1", "关键词2"],
                "S_01_01": ["keyword_A", "keyword_B"]
            }
        max_issues_per_rule: 每个规则最多保留的问题数量（0表示不限制）
    
    Returns:
        bool: 保存是否成功
    """
    try:
        config = {
            "gjb_rules": gjb_rules,
            "cwe_rules": cwe_rules,
            "rule_overrides": rule_overrides or {"gjb": {}, "cwe": {}},
            "custom_filters": custom_filters or {},
            "max_issues_per_rule": max_issues_per_rule if max_issues_per_rule is not None else 0,
            "version": "1.0"
        }
        
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(DEFAULT_RULES_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"[ERROR] 保存默认规则配置失败: {str(e)}")
        return False

def load_default_rules_config() -> Dict[str, Any]:
    """
    加载默认规则配置
    
    Returns:
        dict: 包含 gjb_rules, cwe_rules, rule_overrides, custom_filters 和 max_issues_per_rule 的字典
    """
    try:
        if not DEFAULT_RULES_CONFIG_FILE.exists():
            return {
                "gjb_rules": [],
                "cwe_rules": [],
                "rule_overrides": {"gjb": {}, "cwe": {}},
                "custom_filters": {},
                "max_issues_per_rule": 0
            }
        
        with open(DEFAULT_RULES_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return {
            "gjb_rules": config.get("gjb_rules", []),
            "cwe_rules": config.get("cwe_rules", []),
            "rule_overrides": config.get("rule_overrides", {"gjb": {}, "cwe": {}}),
            "custom_filters": config.get("custom_filters", {}),
            "max_issues_per_rule": config.get("max_issues_per_rule", 0)
        }
    except Exception as e:
        print(f"[ERROR] 加载默认规则配置失败: {str(e)}")
        return {
            "gjb_rules": [],
            "cwe_rules": [],
            "rule_overrides": {"gjb": {}, "cwe": {}},
            "custom_filters": {},
            "max_issues_per_rule": 0
        }

def has_default_config() -> bool:
    """检查是否存在默认配置"""
    return DEFAULT_RULES_CONFIG_FILE.exists()

def apply_rule_overrides_to_database(rule_overrides: Dict[str, Dict[str, str]]) -> bool:
    """
    应用规则覆盖到数据库（永久修改）- PostgreSQL版本
    
    Args:
        rule_overrides: 规则分类覆盖配置
            {
                "gjb": {"GJB_R_01_07_11": "uncertain", ...},
                "cwe": {"S_01_01": "accurate", ...}
            }
    
    Returns:
        bool: 是否成功
    """
    try:
        from app.staticAnalysis.filter.database.postgresql_database import get_db_session
        from app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, CWERule
        from app.staticAnalysis.filter.database.postgresql_rules_database import PostgreSQLRulesDatabase
        
        # 更新GJB规则数据库（批量获取+统一提交）
        gjb_overrides = rule_overrides.get("gjb", {})
        if gjb_overrides:
            session = get_db_session()
            try:
                # 统一转换为数据库存储格式
                converted_map = {
                    PostgreSQLRulesDatabase.convert_gjb_format(code): acc
                    for code, acc in gjb_overrides.items()
                }
                target_codes = list(converted_map.keys())
                if target_codes:
                    rules = session.query(GJB8114Rule).filter(GJB8114Rule.rule_code.in_(target_codes)).all()
                    updated_count = 0
                    existing_codes = set()
                    for rule in rules:
                        existing_codes.add(rule.rule_code)
                        new_acc = converted_map.get(rule.rule_code)
                        if new_acc and rule.accuracy_type != new_acc:
                            rule.accuracy_type = new_acc
                            updated_count += 1
                            print(f"[INFO] 更新GJB规则: {rule.rule_code} -> {new_acc}")
                    # 提示未找到的
                    missing = set(target_codes) - existing_codes
                    for code in missing:
                        print(f"[WARNING] 未找到GJB规则: {code}")
                    session.commit()
                    print(f"[INFO] GJB规则数据库更新成功，共更新{updated_count}条规则")
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        
        # 更新CWE规则数据库（批量获取+统一提交）
        cwe_overrides = rule_overrides.get("cwe", {})
        if cwe_overrides:
            session = get_db_session()
            try:
                target_codes = list(cwe_overrides.keys())
                if target_codes:
                    rules = session.query(CWERule).filter(CWERule.rule_code.in_(target_codes)).all()
                    updated_count = 0
                    existing_codes = set()
                    for rule in rules:
                        existing_codes.add(rule.rule_code)
                        new_acc = cwe_overrides.get(rule.rule_code)
                        if new_acc and rule.accuracy_type != new_acc:
                            rule.accuracy_type = new_acc
                            updated_count += 1
                            print(f"[INFO] 更新CWE规则: {rule.rule_code} -> {new_acc}")
                    # 提示未找到的
                    missing = set(target_codes) - existing_codes
                    for code in missing:
                        print(f"[WARNING] 未找到CWE规则: {code}")
                    session.commit()
                    print(f"[INFO] CWE规则数据库更新成功，共更新{updated_count}条规则")
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 应用规则覆盖到数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def save_selected_rules_to_database(gjb_rules: List[str], cwe_rules: List[str]) -> bool:
    """
    保存勾选状态到数据库 - C/C++版本
    将所有规则的 is_selected 设为 False，然后将选中的规则设为 True
    
    Args:
        gjb_rules: 选中的GJB规则列表
        cwe_rules: 选中的CWE规则列表
    
    Returns:
        bool: 是否成功
    """
    try:
        from app.staticAnalysis.filter.database.postgresql_database import get_db_session
        from app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, CWERule
        
        # 更新GJB规则勾选状态
        session = get_db_session()
        try:
            # 1. 先将所有GJB规则的 is_selected 设为 False
            all_gjb_rules = session.query(GJB8114Rule).all()
            for rule in all_gjb_rules:
                rule.is_selected = False
            print(f"[INFO] 已将 {len(all_gjb_rules)} 条GJB规则的 is_selected 重置为 False")
            
            # 2. 将选中的GJB规则设为 True
            selected_count = 0
            for rule_code in gjb_rules:
                # 转换规则代码格式
                from app.staticAnalysis.filter.database.postgresql_rules_database import PostgreSQLRulesDatabase
                converted_code = PostgreSQLRulesDatabase.convert_gjb_format(rule_code)
                rule = session.query(GJB8114Rule).filter(GJB8114Rule.rule_code == converted_code).first()
                if rule:
                    rule.is_selected = True
                    selected_count += 1
                    print(f"[INFO] 设置GJB规则为已选中: {converted_code}")
                else:
                    print(f"[WARNING] 未找到GJB规则: {converted_code} (原始: {rule_code})")
            
            session.commit()
            print(f"[INFO] GJB规则勾选状态保存成功，共选中 {selected_count} 条规则")
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
        
        # 更新CWE规则勾选状态
        session = get_db_session()
        try:
            # 1. 先将所有CWE规则的 is_selected 设为 False
            all_cwe_rules = session.query(CWERule).all()
            for rule in all_cwe_rules:
                rule.is_selected = False
            print(f"[INFO] 已将 {len(all_cwe_rules)} 条CWE规则的 is_selected 重置为 False")
            
            # 2. 将选中的CWE规则设为 True
            selected_count = 0
            for rule_code in cwe_rules:
                rule = session.query(CWERule).filter(CWERule.rule_code == rule_code).first()
                if rule:
                    rule.is_selected = True
                    selected_count += 1
                    print(f"[INFO] 设置CWE规则为已选中: {rule_code}")
                else:
                    print(f"[WARNING] 未找到CWE规则: {rule_code}")
            
            session.commit()
            print(f"[INFO] CWE规则勾选状态保存成功，共选中 {selected_count} 条规则")
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        print(f"[ERROR] 保存勾选状态到数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def load_selected_rules_from_database() -> Dict[str, List[str]]:
    """
    从数据库加载勾选的规则列表 - C/C++版本
    
    Returns:
        Dict[str, List[str]]: 包含 gjb_rules 和 cwe_rules 的字典
    """
    try:
        from app.staticAnalysis.filter.database.postgresql_database import get_db_session
        from app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, CWERule
        
        session = get_db_session()
        try:
            # 查询所有 is_selected = True 的GJB规则
            gjb_selected = session.query(GJB8114Rule).filter(GJB8114Rule.is_selected == True).all()
            # 转换回原始格式（如 A-1-2）
            gjb_rules = []
            for rule in gjb_selected:
                # 将 GJB_R_01_01_01 转换回 A-1-1 格式
                parts = rule.rule_code.split('_')
                if len(parts) == 5 and parts[0] == 'GJB' and parts[1] == 'R':
                    original_code = f"{parts[2]}-{parts[3]}-{parts[4]}"
                    gjb_rules.append(original_code)
                else:
                    gjb_rules.append(rule.rule_code)
            
            # 查询所有 is_selected = True 的CWE规则
            cwe_selected = session.query(CWERule).filter(CWERule.is_selected == True).all()
            cwe_rules = [rule.rule_code for rule in cwe_selected]
            
            print(f"[INFO] 从数据库加载勾选规则: GJB={len(gjb_rules)}条, CWE={len(cwe_rules)}条")
            return {
                "gjb_rules": gjb_rules,
                "cwe_rules": cwe_rules
            }
        finally:
            session.close()
            
    except Exception as e:
        print(f"[ERROR] 从数据库加载勾选规则失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"gjb_rules": [], "cwe_rules": []}

