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
        print(f"[DEBUG][FPGA][CONFIG] 保存默认配置到: {DEFAULT_RULES_CONFIG_FILE}")
        fpga_overrides_count = len(config['rule_overrides'].get('fpga', {}))
        gjb_overrides_count = len(config['rule_overrides'].get('gjb', {}))
        print(f"[DEBUG][FPGA][CONFIG] gjb_rules={len(config['gjb_rules'])}, cwe_rules={len(config['cwe_rules'])}, overrides(fpga)={fpga_overrides_count}, overrides(gjb)={gjb_overrides_count}, custom_filters={len(config['custom_filters'])}, max_issues_per_rule={config['max_issues_per_rule']}")

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
        
        print(f"[DEBUG][FPGA][CONFIG] 加载默认配置自: {DEFAULT_RULES_CONFIG_FILE}")
        with open(DEFAULT_RULES_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        result = {
            "gjb_rules": config.get("gjb_rules", []),
            "cwe_rules": config.get("cwe_rules", []),
            "rule_overrides": config.get("rule_overrides", {"gjb": {}, "cwe": {}}),
            "custom_filters": config.get("custom_filters", {}),
            "max_issues_per_rule": config.get("max_issues_per_rule", 0)
        }
        try:
            ro = result.get("rule_overrides", {})
            fpga_overrides_count = len(ro.get('fpga', {}))
            gjb_overrides_count = len(ro.get('gjb', {}))
            print(f"[DEBUG][FPGA][CONFIG] 加载成功: gjb_rules={len(result['gjb_rules'])}, cwe_rules={len(result['cwe_rules'])}, overrides(fpga)={fpga_overrides_count}, overrides(gjb)={gjb_overrides_count}, custom_filters={len(result['custom_filters'])}, max_issues_per_rule={result['max_issues_per_rule']}")
        except Exception:
            pass
        return result
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
    应用规则覆盖到数据库（永久修改）- FPGA 版本
    
    Args:
        rule_overrides: 规则分类覆盖配置
            {
                "gjb": {"A-2-1": "uncertain", "R-4-3": "accurate", ...},
                "cwe": {"S_01_01": "accurate", ...}  # 如未使用可忽略
            }
    
    Returns:
        bool: 是否成功
    """
    try:
        # 使用 FPGA 专用数据库与模型
        from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
        from app.staticAnalysis.filterFpga.database.postgresql_models import FPGARule
        
        # 更新 FPGA 规则（支持 'fpga' 键，映射到 gjb 处理逻辑）
        fpga_overrides = rule_overrides.get("fpga", {})
        gjb_overrides = rule_overrides.get("gjb", {})
        # 合并 fpga 和 gjb 键的覆盖（fpga 优先）
        all_overrides = {**gjb_overrides, **fpga_overrides}
        if all_overrides:
            session = get_db_session()
            try:
                updated_count = 0
                for rule_code, new_accuracy_type in all_overrides.items():
                    # FPGA 规则库中即以 rule_code 存储（如 A-2-1 / R-4-3 / 5.1.1）
                    rule = session.query(FPGARule).filter(FPGARule.rule_code == rule_code).first()
                    if rule:
                        rule.accuracy_type = new_accuracy_type
                        updated_count += 1
                        print(f"[INFO][FPGA] 更新规则: {rule_code} -> {new_accuracy_type}")
                    else:
                        print(f"[WARNING][FPGA] 未找到规则: {rule_code}")
                session.commit()
                print(f"[INFO][FPGA] 规则数据库更新成功，共更新{updated_count}条规则")
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

        # 若存在 cwe 覆盖，这里暂不处理（FPGA 页面一般不动 CWE）。
        # 如需处理，可在此处追加 CWE 相关表结构及更新逻辑。

        return True
        
    except Exception as e:
        print(f"[ERROR][FPGA] 应用规则覆盖到数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def save_selected_rules_to_database(selected_rules: List[str]) -> bool:
    """
    保存勾选状态到数据库 - FPGA版本
    将所有规则的 is_selected 设为 False，然后将选中的规则设为 True
    
    Args:
        selected_rules: 选中的规则列表 (如 ["A-1-5", "R-2-1", ...])
    
    Returns:
        bool: 是否成功
    """
    try:
        # 使用 FPGA 专用数据库与模型
        from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
        from app.staticAnalysis.filterFpga.database.postgresql_models import FPGARule
        
        session = get_db_session()
        try:
            # 1. 先将所有规则的 is_selected 设为 False
            all_rules = session.query(FPGARule).all()
            for rule in all_rules:
                rule.is_selected = False
            print(f"[INFO][FPGA] 已将 {len(all_rules)} 条规则的 is_selected 重置为 False")
            
            # 2. 将选中的规则设为 True
            selected_count = 0
            for rule_code in selected_rules:
                rule = session.query(FPGARule).filter(FPGARule.rule_code == rule_code).first()
                if rule:
                    rule.is_selected = True
                    selected_count += 1
                    print(f"[INFO][FPGA] 设置规则为已选中: {rule_code}")
                else:
                    print(f"[WARNING][FPGA] 未找到规则: {rule_code}")
            
            session.commit()
            print(f"[INFO][FPGA] 勾选状态保存成功，共选中 {selected_count} 条规则")
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        print(f"[ERROR][FPGA] 保存勾选状态到数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def load_selected_rules_from_database() -> List[str]:
    """
    从数据库加载勾选的规则列表 - FPGA版本
    
    Returns:
        List[str]: 选中的规则代码列表
    """
    try:
        # 使用 FPGA 专用数据库与模型
        from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
        from app.staticAnalysis.filterFpga.database.postgresql_models import FPGARule
        
        session = get_db_session()
        try:
            # 查询所有 is_selected = True 的规则
            selected_rules = session.query(FPGARule).filter(FPGARule.is_selected == True).all()
            rule_codes = [rule.rule_code for rule in selected_rules]
            print(f"[INFO][FPGA] 从数据库加载勾选规则: {len(rule_codes)} 条")
            return rule_codes
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"[ERROR][FPGA] 从数据库加载勾选规则失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

