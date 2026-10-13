import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

KB_ROOT = Path(__file__).parent
BUSINESS_DIR = KB_ROOT / "business"
DEFECT_DIR = KB_ROOT / "defect"  # 通用缺陷（保持向下兼容）
TYPICAL_DEFECTS_DIR = KB_ROOT / "typical_defects"  # 特定软件类型的典型缺陷


def _read_text(path: Path) -> str:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def _split_software_type(software_type: str) -> Tuple[str, str]:
    """解析输入，支持：
    - "领域/软件类型"（优先）
    - 仅 "软件类型"（回退到在所有领域下匹配同名 .md 文件，取首个匹配）
    """
    st = (software_type or "").strip()
    if "/" in st:
        domain, name = st.split("/", 1)
        return domain.strip(), name.strip()

    # 回退匹配：在所有领域下搜索
    for domain_dir in BUSINESS_DIR.iterdir():
        if not domain_dir.is_dir():
            continue
        cand = domain_dir / f"{st}.md"
        if cand.exists():
            return domain_dir.name, st
    return "", st


def load_kb(software_type: str) -> Dict[str, Any]:
    """加载业务与缺陷知识库（Markdown）。
    返回统一结构：{"type","domain","name","kb_text","defect_text","typical_defects_text"}
    若未找到则返回空文本。"""
    domain, name = _split_software_type(software_type)

    # 业务知识 Markdown
    kb_path = BUSINESS_DIR / domain / f"{name}.md" if domain else None
    kb_text = _read_text(kb_path) if kb_path else ""

    # 通用缺陷知识 Markdown（按领域）
    defect_path = DEFECT_DIR / f"{domain}.md" if domain else None
    defect_text = _read_text(defect_path) if defect_path else ""
    
    # 特定软件典型缺陷 Markdown（按具体软件类型）
    typical_defects_path = TYPICAL_DEFECTS_DIR / domain / f"{name}.md" if domain else None
    typical_defects_text = _read_text(typical_defects_path) if typical_defects_path else ""

    return {
        "type": software_type,
        "domain": domain,
        "name": name,
        "kb_text": kb_text,
        "defect_text": defect_text,
        "typical_defects_text": typical_defects_text,
    }


def list_domains() -> List[str]:
    """列出可用的领域。"""
    domains: List[str] = []
    if not BUSINESS_DIR.exists():
        return domains
    for domain_dir in BUSINESS_DIR.iterdir():
        if domain_dir.is_dir():
            domains.append(domain_dir.name)
    return sorted(domains)


def list_software_types_by_domain(domain: str) -> List[str]:
    """列出指定领域下的软件类型。"""
    software_types: List[str] = []
    domain_dir = BUSINESS_DIR / domain
    if not domain_dir.exists() or not domain_dir.is_dir():
        return software_types
    for md_file in domain_dir.glob("*.md"):
        software_types.append(md_file.stem)
    return sorted(software_types)


def list_kb_types() -> List[str]:
    """列出可用的知识库类型，返回格式为 "领域/软件类型"。"""
    results: List[str] = []
    if not BUSINESS_DIR.exists():
        return results
    for domain_dir in BUSINESS_DIR.iterdir():
        if not domain_dir.is_dir():
            continue
        for md_file in domain_dir.glob("*.md"):
            results.append(f"{domain_dir.name}/{md_file.stem}")
    return sorted(results)


def get_domain_software_structure() -> Dict[str, List[str]]:
    """获取完整的领域-软件类型结构。"""
    structure: Dict[str, List[str]] = {}
    if not BUSINESS_DIR.exists():
        return structure
    
    for domain_dir in BUSINESS_DIR.iterdir():
        if not domain_dir.is_dir():
            continue
        domain_name = domain_dir.name
        software_types = []
        for md_file in domain_dir.glob("*.md"):
            software_types.append(md_file.stem)
        structure[domain_name] = sorted(software_types)
    
    return structure 