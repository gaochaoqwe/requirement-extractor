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

def save_default_rules_config(gjb_rules: List[str], cwe_rules: List[str]) -> bool:
    """
    保存默认规则配置
    
    Args:
        gjb_rules: 选中的GJB8114规则列表
        cwe_rules: 选中的CWE规则列表
    
    Returns:
        bool: 保存是否成功
    """
    try:
        config = {
            "gjb_rules": gjb_rules,
            "cwe_rules": cwe_rules,
            "version": "1.0"
        }
        
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(DEFAULT_RULES_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"[ERROR] 保存默认规则配置失败: {str(e)}")
        return False

def load_default_rules_config() -> Dict[str, List[str]]:
    """
    加载默认规则配置
    
    Returns:
        dict: 包含 gjb_rules 和 cwe_rules 的字典，如果文件不存在则返回空列表
    """
    try:
        if not DEFAULT_RULES_CONFIG_FILE.exists():
            return {
                "gjb_rules": [],
                "cwe_rules": []
            }
        
        with open(DEFAULT_RULES_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return {
            "gjb_rules": config.get("gjb_rules", []),
            "cwe_rules": config.get("cwe_rules", [])
        }
    except Exception as e:
        print(f"[ERROR] 加载默认规则配置失败: {str(e)}")
        return {
            "gjb_rules": [],
            "cwe_rules": []
        }

def has_default_config() -> bool:
    """检查是否存在默认配置"""
    return DEFAULT_RULES_CONFIG_FILE.exists()

