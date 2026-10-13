"""普通模式 FPGA 默认规则配置管理（JSON 文件存储，管理员密码保护）。"""
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

CONFIG_DIR = Path(__file__).parent
DEFAULT_RULES_CONFIG_FILE = CONFIG_DIR / "default_selected_rules.json"

# MD5("159357")
ADMIN_PASSWORD_HASH = "36e1a5072c78359066ed7715f5ff3da8"


def verify_admin_password(password: str) -> bool:
    return hashlib.md5(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH


def save_default_rules_config(selected_rules: List[str]) -> bool:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = {"selected_rules": selected_rules, "version": "1.0"}
        with open(DEFAULT_RULES_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] 保存普通模式FPGA默认规则配置失败: {e}")
        return False


def load_default_rules_config() -> Dict[str, Any]:
    try:
        if not DEFAULT_RULES_CONFIG_FILE.exists():
            return {"selected_rules": [], "has_config": False}
        with open(DEFAULT_RULES_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return {"selected_rules": config.get("selected_rules", []), "has_config": True}
    except Exception as e:
        print(f"[ERROR] 加载普通模式FPGA默认规则配置失败: {e}")
        return {"selected_rules": [], "has_config": False}


def has_default_config() -> bool:
    return DEFAULT_RULES_CONFIG_FILE.exists()
