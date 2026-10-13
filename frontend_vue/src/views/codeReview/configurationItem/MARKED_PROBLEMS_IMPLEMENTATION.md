# 标记问题功能实现说明

## 功能概述

已为代码审查模块的三种审查类型（函数审查、链路审查、功能审查）添加了标记问题功能，支持：
- 将标记的问题存储到后端数据库
- 多人协作：任何人打开同一任务都能看到已标记的问题
- 查看标记问题位置
- 导出已标记的问题为Excel

## 后端实现

### 1. 数据库表

表名：`code_review_marked_problems`

字段：
- `id`: 主键
- `task_id`: 任务ID（外键）
- `analysis_type`: 分析类型（function/chain/feature）
- `problem_key`: 问题唯一标识
- `problem_data`: 完整问题数据（JSONB）
- `marked_by`: 标记人
- `marked_at`: 标记时间

### 2. API端点

所有端点路径前缀：`/api/codeReview/{task_id}/marked_problems`

- `POST /` - 保存标记问题
- `DELETE /` - 删除标记问题  
- `GET /` - 获取标记问题列表
- `GET /locations` - 获取标记位置（用于高亮）
- `GET /count` - 获取标记数量

### 3. 初始化数据库

运行以下命令创建表：
```bash
cd backend
python app/codeReview/ConfigurationItem/db/init_marked_problems_simple.py
```

## 前端实现

### 已完成模块

#### 1. 函数审查 (✅ 已完成)
- 文件：`functionCodemap/CodeMapSidebar.vue`
- 功能：
  - 标记/取消标记问题
  - 查看标记问题（显示标记的文件和函数）
  - 导出已标记问题
  - 从localStorage迁移到后端API

#### 2. 功能审查 (✅ 已完成)
- 文件：`featureReview/FeatureReviewPage.vue`
- 功能：
  - 标记/取消标记问题
  - 导出已标记问题
  - 从localStorage迁移到后端API

### 待完成模块

#### 3. 链路审查 (⏳ 待实现)
- 文件：`chainCodemap/CodeMapSidebar.vue`或相关组件
- 需要添加的功能同函数审查

## 链路审查实现步骤

### 方案1：修改现有ChainMapSidebar.vue组件

该组件目前只有导出功能，需要：

1. 将localStorage调用改为API调用
2. 参考函数审查的实现：

```javascript
// 从
import { saveMarkedProblem, removeMarkedProblem } from '../shared/problemMarking';

// 改为
import { buildProblemKey } from '../shared/problemMarking';

// 添加标记功能
async function toggleProblemMark(problem) {
  const problemKey = buildProblemKey(problem);
  const isMarked = markedProblems.value.has(problemKey);
  
  try {
    if (isMarked) {
      await axios.delete(`/api/codeReview/${props.taskId}/marked_problems`, {
        data: {
          analysis_type: 'chain',
          problem_key: problemKey
        }
      });
      markedProblems.value.delete(problemKey);
      ElMessage.success('已取消标记');
    } else {
      await axios.post(`/api/codeReview/${props.taskId}/marked_problems`, {
        analysis_type: 'chain',
        problem_key: problemKey,
        problem_data: problem
      });
      markedProblems.value.add(problemKey);
      ElMessage.success('标记成功');
    }
  } catch (error) {
    ElMessage.error('标记操作失败');
  }
}

// 加载标记状态
async function loadMarkedProblems() {
  if (!props.taskId) return;
  try {
    const response = await axios.get(`/api/codeReview/${props.taskId}/marked_problems`, {
      params: { analysis_type: 'chain' }
    });
    if (response.data.success) {
      const keys = response.data.data.map(item => item.problem_key);
      markedProblems.value = new Set(keys);
    }
  } catch (error) {
    console.error('加载标记问题失败:', error);
  }
}

// 导出修改
async function exportMarkedProblems() {
  try {
    // 从后端获取所有已标记的问题
    const response = await axios.get(`/api/codeReview/${props.taskId}/marked_problems`, {
      params: { analysis_type: 'chain' }
    });
    const markedProblemsArray = response.data.data.map(item => item.problem_data);
    
    // ...调用导出API
  } catch (error) {
    ElMessage.error('导出失败');
  }
}
```

### 方案2：如果链路审查使用完整的CodeMapSidebar.vue组件

参考函数审查的完整实现，需要：

1. 在问题列表中添加标记按钮
2. 在header添加"查看标记问题"和"导出已标记"按钮
3. 实现标记、查看、导出功能

## 测试步骤

1. 在函数审查页面标记一些问题
2. 切换到另一个浏览器/用户，打开同一任务
3. 确认能看到已标记的问题
4. 测试导出功能
5. 验证问题不会跨任务显示

## 注意事项

- 所有标记数据现在存储在后端，不再使用localStorage
- 问题唯一标识（problem_key）基于问题内容生成
- 同一问题在同一任务下不能重复标记（数据库有唯一约束）
- 删除任务时会级联删除该任务的所有标记问题

## 文件清单

### 后端
- `db/models/marked_problem.py` - 数据库模型
- `db/repository/marked_problem_repo.py` - 仓储层
- `api/endpoints/marked_problems.py` - API端点
- `db/init_marked_problems_simple.py` - 数据库初始化脚本

### 前端
- `functionCodemap/CodeMapSidebar.vue` - 函数审查组件（已完成）
- `featureReview/FeatureReviewPage.vue` - 功能审查组件（已完成）
- `chainCodemap/ChainMapSidebar.vue` - 链路审查组件（待完成）
- `shared/problemMarking.ts` - 共享工具函数（只保留buildProblemKey）

