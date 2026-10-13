"""
CWE规则数据库访问类
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class CWERulesDatabase:
    """CWE规则数据库管理类"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent / "cwe_rules.db"
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"CWE规则数据库不存在: {self.db_path}")
        
        logger.info(f"CWE规则数据库路径: {self.db_path}")
    
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(str(self.db_path))
    
    def get_all_rules(self) -> List[Dict]:
        """获取所有规则"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rule_code, rule_name, accuracy_type, category, description
            FROM cwe_rules
            ORDER BY rule_code
        """)
        
        rules = []
        for row in cursor.fetchall():
            rules.append({
                "rule_code": row[0],
                "rule_name": row[1],
                "accuracy_type": row[2],
                "category": row[3] or "",
                "description": row[4] or ""
            })
        
        conn.close()
        return rules
    
    def get_rules_by_type(self, accuracy_type: str) -> List[Dict]:
        """
        获取指定类型的规则
        
        Args:
            accuracy_type: 'accurate' 或 'uncertain'
        
        Returns:
            规则列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rule_code, rule_name, accuracy_type, category, description
            FROM cwe_rules
            WHERE accuracy_type = ?
            ORDER BY rule_code
        """, (accuracy_type,))
        
        rules = []
        for row in cursor.fetchall():
            rules.append({
                "rule_code": row[0],
                "rule_name": row[1],
                "accuracy_type": row[2],
                "category": row[3] or "",
                "description": row[4] or ""
            })
        
        conn.close()
        logger.info(f"获取{accuracy_type}类型的CWE规则: {len(rules)}个")
        return rules
    
    def get_rule_by_code(self, rule_code: str) -> Optional[Dict]:
        """根据规则代码获取规则"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rule_code, rule_name, accuracy_type, category, description
            FROM cwe_rules
            WHERE rule_code = ?
        """, (rule_code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "rule_code": row[0],
                "rule_name": row[1],
                "accuracy_type": row[2],
                "category": row[3] or "",
                "description": row[4] or ""
            }
        return None
    
    def classify_issue_by_rule_name(self, issue_name: str) -> Tuple[str, Optional[Dict]]:
        """
        根据问题名称分类 - 优先使用规则编号进行精确匹配
        
        Args:
            issue_name: 问题名称，例如 "S_02_01 未初始化的指针" 或 "C/ C++检测指针越界"
        
        Returns:
            (accuracy_type, rule_info) 元组
            accuracy_type: 'accurate' 或 'uncertain'
            rule_info: 规则信息字典或None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 特殊情况：处理没有编号的规则 "C/ C++检测指针越界"
        if issue_name.strip() == "C/ C++检测指针越界":
            logger.info(f"CWE特殊规则匹配: {issue_name}")
            # 这个规则被认为是不确定的（因为需要复杂的数据流分析）
            return "uncertain", {
                "rule_code": "SPECIAL_PTR_BOUND",
                "rule_name": issue_name,
                "accuracy_type": "uncertain",
                "category": "指针越界",
                "description": "检测C/C++代码中的指针越界问题"
            }
        
        # 1. 优先从问题名称开头提取CWE规则编号（最准确的匹配方式）
        # 匹配格式：S_XX_XX 或 S_XX_XX_XX（两位或三位数字段）
        import re
        cwe_pattern = r'^(S_\d{2}_\d{2}(?:_\d{2})?)'
        cwe_match = re.match(cwe_pattern, issue_name)
        
        if cwe_match:
            rule_code = cwe_match.group(1)
            logger.info(f"提取到CWE规则编号: {rule_code}")
            
            cursor.execute("""
                SELECT rule_code, rule_name, accuracy_type, category, description
                FROM cwe_rules
                WHERE rule_code = ?
            """, (rule_code,))
            
            row = cursor.fetchone()
            if row:
                conn.close()
                logger.info(f"CWE规则精确匹配: {rule_code} -> {row[2]}")
                return row[2], {
                    "rule_code": row[0],
                    "rule_name": row[1],
                    "accuracy_type": row[2],
                    "category": row[3] or "",
                    "description": row[4] or ""
                }
            else:
                logger.warning(f"数据库中未找到CWE规则: {rule_code}")
        
        # 2. 如果编号匹配失败，尝试完全匹配规则名称
        cursor.execute("""
            SELECT rule_code, rule_name, accuracy_type, category, description
            FROM cwe_rules
            WHERE rule_name = ?
        """, (issue_name,))
        
        row = cursor.fetchone()
        if row:
            conn.close()
            logger.info(f"CWE规则完全匹配: {issue_name} -> {row[2]}")
            return row[2], {
                "rule_code": row[0],
                "rule_name": row[1],
                "accuracy_type": row[2],
                "category": row[3] or "",
                "description": row[4] or ""
            }
        
        # 3. 尝试模糊匹配（包含关键字）- 作为最后的备用方案
        # 提取描述部分
        description = issue_name
        if " " in issue_name:
            description = issue_name.split(" ", 1)[1]
        
        cursor.execute("""
            SELECT rule_code, rule_name, accuracy_type, category, description
            FROM cwe_rules
            WHERE rule_name LIKE ?
            ORDER BY LENGTH(rule_name) ASC
            LIMIT 1
        """, (f"%{description}%",))
        
        row = cursor.fetchone()
        if row:
            conn.close()
            logger.info(f"CWE规则模糊匹配: {issue_name} -> {row[2]}")
            return row[2], {
                "rule_code": row[0],
                "rule_name": row[1],
                "accuracy_type": row[2],
                "category": row[3] or "",
                "description": row[4] or ""
            }
        
        conn.close()
        logger.warning(f"CWE规则未匹配: {issue_name}，默认为uncertain")
        return "uncertain", None
    
    def get_statistics(self) -> Dict:
        """获取规则统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 总数
        cursor.execute("SELECT COUNT(*) FROM cwe_rules")
        total = cursor.fetchone()[0]
        
        # 确定规则数
        cursor.execute("SELECT COUNT(*) FROM cwe_rules WHERE accuracy_type = 'accurate'")
        accurate = cursor.fetchone()[0]
        
        # 不确定规则数
        cursor.execute("SELECT COUNT(*) FROM cwe_rules WHERE accuracy_type = 'uncertain'")
        uncertain = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "accurate": accurate,
            "uncertain": uncertain
        }


# 全局单例
_cwe_db_instance = None


def get_cwe_rules_database() -> CWERulesDatabase:
    """获取CWE规则数据库单例"""
    global _cwe_db_instance
    if _cwe_db_instance is None:
        _cwe_db_instance = CWERulesDatabase()
    return _cwe_db_instance


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    db = CWERulesDatabase()
    
    print("="*80)
    print("CWE规则数据库测试")
    print("="*80)
    
    # 统计信息
    stats = db.get_statistics()
    print(f"\n统计信息:")
    print(f"  总规则数: {stats['total']}")
    print(f"  确定规则: {stats['accurate']}")
    print(f"  不确定规则: {stats['uncertain']}")
    
    # 获取确定规则
    print(f"\n获取前5个确定规则:")
    accurate_rules = db.get_rules_by_type("accurate")
    for rule in accurate_rules[:5]:
        print(f"  {rule['rule_code']}: {rule['rule_name']}")
    
    # 获取不确定规则
    print(f"\n获取前5个不确定规则:")
    uncertain_rules = db.get_rules_by_type("uncertain")
    for rule in uncertain_rules[:5]:
        print(f"  {rule['rule_code']}: {rule['rule_name']}")
    
    # 测试分类
    print(f"\n测试问题分类:")
    test_cases = [
        "S_21_01 一般的数组越界",
        "S_15_01 变量未初始化使用",
        "C/ C++检测指针越界",
        "S_04_08 不建议使用不安全的scanf类函数",
    ]
    
    for test_case in test_cases:
        accuracy_type, rule_info = db.classify_issue_by_rule_name(test_case)
        if rule_info:
            print(f"  {test_case} -> {accuracy_type} ({rule_info['rule_code']})")
        else:
            print(f"  {test_case} -> {accuracy_type} (未匹配)")

