# CWE规则支持实施计划

## 概述
添加对CWE规则（C/C++缺陷检测项）的支持，与现有GJB8114规则并行处理。

---

## 任务分解

### ✅ 阶段1: 数据库层（2-3小时）

#### 1.1 创建CWE规则数据库表
文件: `backend/app/testTools/static_analysis_filter/database/cwe_rules_database.py`

```python
class CWERulesDatabase:
    """CWE规则数据库管理"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化CWE规则表"""
        # 创建表: cwe_rules
        # 字段: rule_code, rule_name, accuracy_type, category, description
        pass
    
    def get_rules_by_type(self, accuracy_type: str) -> List[Dict]:
        """获取指定类型的规则"""
        pass
    
    def classify_issue_by_rule_name(self, issue_name: str) -> Tuple[str, Dict]:
        """根据问题名称分类"""
        pass
```

#### 1.2 CWE规则分类
- **确定规则（accurate）**: ~120个
  - 类型错误、未使用、明确禁止的API等
- **不确定规则（uncertain）**: ~77个
  - 数组越界、指针问题、内存泄漏、并发问题等

---

### 📝 阶段2: 服务层（3-4小时）

#### 2.1 修改EnhancedService支持双规则处理
文件: `backend/app/testTools/static_analysis_filter/services/enhanced_service.py`

**关键修改**:
```python
class EnhancedStaticAnalysisService:
    def __init__(self, session_id: str):
        self.gjb_db = RulesDatabase(gjb_db_path)  # GJB8114
        self.cwe_db = CWERulesDatabase(cwe_db_path)  # CWE
        
        # 双轨道处理
        self.gjb_issues = []
        self.cwe_issues = []
        
        # 双日志
        self.gjb_logger = get_session_logger(session_id, prefix="GJB")
        self.cwe_logger = get_session_logger(session_id, prefix="CWE")
    
    async def process_uploaded_files(self, excel_path, ...):
        """处理上传文件，解析两个sheet"""
        # 读取 GJB_8114 sheet
        self.gjb_issues = self._parse_gjb_sheet(excel_path)
        
        # 读取 C_CPP缺陷检测项（CWE通用缺陷） sheet
        self.cwe_issues = self._parse_cwe_sheet(excel_path)
        
        return {
            "gjb_count": len(self.gjb_issues),
            "cwe_count": len(self.cwe_issues)
        }
    
    async def process_session_enhanced(self):
        """并行处理两种规则"""
        # 创建两个并发任务
        gjb_task = asyncio.create_task(self._process_gjb_issues())
        cwe_task = asyncio.create_task(self._process_cwe_issues())
        
        # 等待两个任务完成
        await asyncio.gather(gjb_task, cwe_task)
```

#### 2.2 修改日志系统
文件: `backend/app/testTools/static_analysis_filter/utils/logger.py`

```python
def get_session_logger(session_id: str, rule_type: str = "GJB"):
    """
    获取会话日志器
    rule_type: "GJB" 或 "CWE"
    """
    log_dir = Path(...) / session_id
    log_file = log_dir / f"static_analysis_{rule_type}_{session_id}_{timestamp}.log"
    ...
```

---

### 🎨 阶段3: API层（2小时）

#### 3.1 修改API支持双规则
文件: `backend/app/testTools/static_analysis_filter/api/api.py`

**新增端点**:
```python
@router.get("/rules/cwe/{accuracy_type}")
async def get_cwe_rules(accuracy_type: str):
    """获取CWE规则列表"""
    pass

@router.get("/status/{session_id}/detailed")
async def get_detailed_status(session_id: str):
    """获取详细状态（包含GJB和CWE两部分）"""
    return {
        "gjb": {
            "total_issues": ...,
            "processed_issues": ...,
            "current_analyzing": ...
        },
        "cwe": {
            "total_issues": ...,
            "processed_issues": ...,
            "current_analyzing": ...
        }
    }
```

---

### 🖼️ 阶段4: 前端UI（4-5小时）

#### 4.1 添加规则切换Tab
文件: `frontend_vue/src/views/testTools/staticAnalysisFilter/StaticAnalysisFilter.vue`

```vue
<template>
  <div class="static-analysis-filter">
    <!-- 规则选择区域 -->
    <el-card class="rule-selection-card">
      <el-tabs v-model="activeRuleType" @tab-change="handleRuleTypeChange">
        <el-tab-pane label="GJB8114规则" name="gjb">
          <!-- GJB规则列表 -->
          <div class="rules-container">
            <div class="rules-column">
              <h4>确定规则</h4>
              <el-checkbox-group v-model="selectedGjbAccurateRules">
                <el-checkbox v-for="rule in gjbAccurateRules" :key="rule.rule_code" :value="rule.rule_code">
                  {{ rule.rule_name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
            <div class="rules-column">
              <h4>不确定规则</h4>
              <el-checkbox-group v-model="selectedGjbUncertainRules">
                <el-checkbox v-for="rule in gjbUncertainRules" :key="rule.rule_code" :value="rule.rule_code">
                  {{ rule.rule_name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="CWE规则" name="cwe">
          <!-- CWE规则列表 -->
          <div class="rules-container">
            <div class="rules-column">
              <h4>确定规则</h4>
              <el-checkbox-group v-model="selectedCweAccurateRules">
                <el-checkbox v-for="rule in cweAccurateRules" :key="rule.rule_code" :value="rule.rule_code">
                  {{ rule.rule_name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
            <div class="rules-column">
              <h4>不确定规则</h4>
              <el-checkbox-group v-model="selectedCweUncertainRules">
                <el-checkbox v-for="rule in cweUncertainRules" :key="rule.rule_code" :value="rule.rule_code">
                  {{ rule.rule_name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 处理进度显示区域 - 上下两部分 -->
    <div class="progress-container" v-if="isProcessing">
      <!-- GJB进度（上半部分） -->
      <el-card class="progress-card gjb-progress">
        <template #header>
          <div class="card-header">
            <span>🔍 GJB8114 规则审查进度</span>
          </div>
        </template>
        <div class="progress-content">
          <el-progress 
            :percentage="gjbProgress" 
            :stroke-width="12"
            :status="gjbStatus"
          />
          <div class="progress-details">
            <p>总问题数: {{ gjbTotalIssues }}</p>
            <p>已处理: {{ gjbProcessedIssues }}</p>
            <p>当前分析: {{ gjbCurrentAnalyzing }}</p>
            <p>工具调用次数: {{ gjbToolCallsCount }}</p>
          </div>
        </div>
      </el-card>

      <!-- CWE进度（下半部分） -->
      <el-card class="progress-card cwe-progress">
        <template #header>
          <div class="card-header">
            <span>🛡️ CWE规则审查进度</span>
          </div>
        </template>
        <div class="progress-content">
          <el-progress 
            :percentage="cweProgress" 
            :stroke-width="12"
            :status="cweStatus"
          />
          <div class="progress-details">
            <p>总问题数: {{ cweTotalIssues }}</p>
            <p>已处理: {{ cweProcessedIssues }}</p>
            <p>当前分析: {{ cweCurrentAnalyzing }}</p>
            <p>工具调用次数: {{ cweToolCallsCount }}</p>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      activeRuleType: 'gjb',  // 当前选中的规则类型tab
      
      // GJB规则
      gjbAccurateRules: [],
      gjbUncertainRules: [],
      selectedGjbAccurateRules: [],
      selectedGjbUncertainRules: [],
      
      // CWE规则
      cweAccurateRules: [],
      cweUncertainRules: [],
      selectedCweAccurateRules: [],
      selectedCweUncertainRules: [],
      
      // GJB进度
      gjbTotalIssues: 0,
      gjbProcessedIssues: 0,
      gjbCurrentAnalyzing: '',
      gjbToolCallsCount: 0,
      gjbProgress: 0,
      gjbStatus: '',
      
      // CWE进度
      cweTotalIssues: 0,
      cweProcessedIssues: 0,
      cweCurrentAnalyzing: '',
      cweToolCallsCount: 0,
      cweProgress: 0,
      cweStatus: '',
    }
  },
  
  methods: {
    async loadGjbRules() {
      // 加载GJB规则
    },
    
    async loadCweRules() {
      // 加载CWE规则
    },
    
    async checkDetailedStatus() {
      // 轮询获取双进度
      const response = await staticAnalysisFilterAPI.getDetailedStatus(this.sessionId)
      
      // 更新GJB进度
      this.gjbTotalIssues = response.gjb.total_issues
      this.gjbProcessedIssues = response.gjb.processed_issues
      ...
      
      // 更新CWE进度
      this.cweTotalIssues = response.cwe.total_issues
      this.cweProcessedIssues = response.cwe.processed_issues
      ...
    }
  }
}
</script>

<style scoped>
.progress-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.progress-card {
  flex: 1;
}

.gjb-progress {
  border-left: 4px solid #409EFF;
}

.cwe-progress {
  border-left: 4px solid #67C23A;
}
</style>
```

---

## 实施时间估算

| 阶段 | 任务 | 预估时间 |
|------|------|---------|
| 1 | 数据库层 | 2-3小时 |
| 2 | 服务层 | 3-4小时 |
| 3 | API层 | 2小时 |
| 4 | 前端UI | 4-5小时 |
| 5 | 测试调试 | 2-3小时 |
| **总计** | | **13-17小时** |

---

## 关键技术点

### 1. Excel双Sheet解析
```python
import openpyxl

wb = openpyxl.load_workbook(excel_path)

# Sheet 1: GJB_8114
gjb_sheet = wb["GJB_8114(国家军用标准CC++语言可靠性编程规范"]
gjb_issues = parse_sheet(gjb_sheet)

# Sheet 2: CWE
cwe_sheet = wb["C_CPP缺陷检测项（CWE通用缺陷）"]
cwe_issues = parse_sheet(cwe_sheet)
```

### 2. 并发处理
```python
async def process_both_rules():
    gjb_task = process_gjb()
    cwe_task = process_cwe()
    results = await asyncio.gather(gjb_task, cwe_task)
```

### 3. 双日志系统
```
logs/
  └── session_id/
      ├── static_analysis_GJB_session_id_timestamp.log
      └── static_analysis_CWE_session_id_timestamp.log
```

---

## 需要修改的文件清单

### 后端（约15个文件）
1. `database/cwe_rules_database.py` ✨ 新建
2. `database/rules_database.py` 🔧 修改
3. `services/enhanced_service.py` 🔧 重点修改
4. `services/code_analysis_agent_v2.py` 🔧 可能需要修改
5. `api/api.py` 🔧 修改
6. `utils/logger.py` 🔧 修改
7. `utils/excel_parser.py` 🔧 修改
8. `models/models.py` 🔧 可能需要修改

### 前端（约5个文件）
1. `views/testTools/staticAnalysisFilter/StaticAnalysisFilter.vue` 🔧 重点修改
2. `api/staticAnalysisFilter/index.js` 🔧 修改
3. `api/staticAnalysisFilter/staticAnalysisFilterService.js` 🔧 修改

---

## 下一步建议

由于这是一个大型重构任务，建议：

1. **先完成数据库层** - 创建CWE规则表和分类
2. **再完成服务层核心逻辑** - 双轨处理
3. **然后API层** - 提供新接口
4. **最后前端UI** - 展示双进度

每个阶段完成后进行测试，确保功能正常再进行下一阶段。

**现在是否开始实施？需要我先完成哪个阶段？**

