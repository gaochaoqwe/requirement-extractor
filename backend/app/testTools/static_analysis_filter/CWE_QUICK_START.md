# CWE功能快速实施指南

## ✅ 已完成
1. **CWE规则分类** - 197个规则分为107个确定规则和90个不确定规则
2. **CWE数据库创建** - `cwe_rules.db` 已创建并填充数据

## 🚀 下一步骤（按优先级）

由于这是一个大型重构，建议分3个阶段实施：

### 阶段1: 数据库和API层（2-3小时）✨

#### 1.1 创建CWE规则数据库访问类
文件: `backend/app/testTools/static_analysis_filter/database/cwe_rules_database.py`

```python
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class CWERulesDatabase:
    """CWE规则数据库管理类"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "cwe_rules.db"
        self.conn = None
    
    def get_rules_by_type(self, accuracy_type: str) -> List[Dict]:
        """获取指定类型的规则"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rule_code, rule_name, accuracy_type, category 
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
                "category": row[3]
            })
        
        conn.close()
        return rules
    
    def classify_issue_by_rule_name(self, issue_name: str) -> Tuple[str, Optional[Dict]]:
        """
        根据问题名称分类
        返回: (accuracy_type, rule_info)
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 尝试完全匹配
        cursor.execute("""
            SELECT rule_code, rule_name, accuracy_type, category
            FROM cwe_rules
            WHERE rule_name = ?
        """, (issue_name,))
        
        row = cursor.fetchone()
        if row:
            conn.close()
            return row[2], {
                "rule_code": row[0],
                "rule_name": row[1],
                "accuracy_type": row[2],
                "category": row[3]
            }
        
        # 尝试部分匹配（去掉rule_code前缀）
        # 例如: "S_21_01 一般的数组越界" -> "一般的数组越界"
        if " " in issue_name:
            description = issue_name.split(" ", 1)[1]
            cursor.execute("""
                SELECT rule_code, rule_name, accuracy_type, category
                FROM cwe_rules
                WHERE rule_name LIKE ?
            """, (f"%{description}%",))
            
            row = cursor.fetchone()
            if row:
                conn.close()
                return row[2], {
                    "rule_code": row[0],
                    "rule_name": row[1],
                    "accuracy_type": row[2],
                    "category": row[3]
                }
        
        conn.close()
        return "uncertain", None  # 默认为不确定
```

#### 1.2 添加CWE规则API端点
文件: `backend/app/testTools/static_analysis_filter/api/api.py`

在现有文件中添加：

```python
from ..database.cwe_rules_database import CWERulesDatabase

# 全局CWE数据库实例
_cwe_db = CWERulesDatabase()

@router.get("/rules/cwe/{accuracy_type}")
async def get_cwe_rules(accuracy_type: str):
    """
    获取CWE规则列表
    accuracy_type: 'accurate' 或 'uncertain'
    """
    try:
        rules = _cwe_db.get_rules_by_type(accuracy_type)
        return {
            "success": True,
            "rules": rules,
            "count": len(rules)
        }
    except Exception as e:
        logger.error(f"获取CWE规则失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/status/{session_id}/detailed")
async def get_detailed_status(session_id: str):
    """
    获取详细状态（GJB和CWE两部分）
    """
    service = get_enhanced_service(session_id)
    if not service:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    status = service.get_detailed_status()
    return status
```

### 阶段2: 服务层（最复杂，3-4小时）🔥

这部分需要大量修改，建议你参考 `CWE_IMPLEMENTATION_PLAN.md` 中的详细说明。

关键点：
1. `EnhancedStaticAnalysisService` 需要维护两组数据（GJB和CWE）
2. 需要修改Excel解析逻辑，支持读取两个sheet
3. 需要实现并行处理两种规则的逻辑
4. 需要双日志系统

### 阶段3: 前端UI（4-5小时）🎨

前端改动较大，包括：
1. 规则选择Tab切换
2. 双进度显示（上下布局）
3. 双轮询状态更新

---

## 📝 建议实施流程

### 方案A: 完整实施（推荐但耗时）
1. 完成阶段1（API层） - 今天
2. 完成阶段2（服务层） - 明天
3. 完成阶段3（前端） - 后天
4. 测试和调试 - 第4天

### 方案B: 最小可用版本（MVP）
1. 先支持CWE规则查询API - 1小时
2. 修改Excel解析支持双sheet - 2小时
3. 前端添加规则切换Tab - 2小时
4. 串行处理（而非并行） - 简化实现

### 方案C: 渐进式实施
1. 第一周：后端支持，但前端还是单规则
2. 第二周：前端支持切换，但只能处理一种
3. 第三周：完整并行处理

---

## 🔑 关键决策点

1. **是否需要并行处理？**
   - 是：性能好，但实现复杂
   - 否：简单，但处理时间长

2. **日志如何组织？**
   - 两个独立文件：清晰但文件多
   - 一个文件带标签：简单但可能混乱

3. **前端进度显示方式？**
   - 上下两部分：清晰但占用空间
   - Tab切换：节省空间但不能同时看

---

## 💡 当前状态

✅ 数据库已准备好
✅ 规则分类完成  
⏳ 等待后续实施

**建议**：先实施CWE规则查询API和数据库访问类（1小时），测试通过后再决定是否继续完整实施。

