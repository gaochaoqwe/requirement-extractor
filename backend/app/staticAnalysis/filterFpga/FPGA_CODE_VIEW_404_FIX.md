# FPGA代码视图404错误修复

## 问题描述

前端访问FPGA代码视图时报404错误：
```
GET /api/staticAnalysis/fpga/code-view/33
Response: 404 Not Found
```

但C/C++的代码视图正常工作。

## 问题分析

### 1. 端点确实存在

✅ **已确认**：`code-view` 端点存在于 `filterFpga/api/api.py` 第872行

```python
@router.get("/code-view/{task_id}")
def get_code_view_data(
    task_id: str,
    rule_type: str = Query('fpga', description="规则类型: fpga")
) -> Dict[str, Any]:
    """获取代码视图所需的数据"""
    ...
```

### 2. 路由配置正确

✅ **路由挂载**：`staticAnalysis/__init__.py` 第19行

```python
router.include_router(filter_fpga_router, prefix="/fpga", tags=["static-analysis-filter-fpga"])
```

**完整路径**：`/api/staticAnalysis/fpga/code-view/{task_id}`

### 3. 前端调用正确

✅ **前端代码**：`filterFpga/StaticAnalysisCodeView.vue` 第215行

```javascript
const fpgaRes = await axios.get(`/api/staticAnalysis/fpga/code-view/${taskId.value}`)
```

## 可能的原因

### 原因1：后端服务未重启 ⭐

最近的代码修改（编码修复、日志修复等）还没有生效。

**解决方法**：重启后端服务

### 原因2：有语法错误或导入错误

运行测试脚本时发现循环导入错误（虽然不影响filter的code-view）。

### 原因3：代码编辑未保存

最近的修改可能没有保存到文件。

## 解决步骤

### 步骤1：检查文件完整性

确认`filterFpga/api/api.py`包含code-view端点：

```bash
# 在PowerShell中执行
Get-Content "E:\code\requirement_extractor\backend\app\staticAnalysis\filterFpga\api\api.py" | Select-String "code-view"
```

**预期输出**：
```
872:@router.get("/code-view/{task_id}")
```

### 步骤2：重启后端服务

**方法1：使用终端**
1. 停止当前运行的后端服务（Ctrl+C）
2. 重新运行：
```bash
conda activate aiTest_new
python run_fastapi.py
```

**方法2：在VSCode/IDE中**
1. 停止调试/运行
2. 重新启动后端服务

### 步骤3：验证端点注册

启动后端后，在浏览器访问：
```
http://localhost:8000/docs
```

在Swagger UI中搜索 `code-view`，应该能看到：
- ✅ `/api/staticAnalysis/filter/code-view/{task_id}` (C/C++)
- ✅ `/api/staticAnalysis/fpga/code-view/{task_id}` (FPGA)

### 步骤4：测试FPGA代码视图

1. 重启后端后，刷新前端页面
2. 进入FPGA代码视图
3. 检查是否还有404错误

## 快速验证脚本

创建测试文件 `test_fpga_api.py`：

```python
import requests

# 测试FPGA code-view端点（使用实际的task_id）
task_id = "33"  # 替换为实际的任务ID
url = f"http://localhost:8000/api/staticAnalysis/fpga/code-view/{task_id}"

print(f"测试URL: {url}")

try:
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("✅ 端点工作正常")
        print(f"返回数据: {response.json()}")
    elif response.status_code == 404:
        print("❌ 404错误 - 任务不存在或端点未注册")
        print(f"错误详情: {response.json()}")
    else:
        print(f"其他错误: {response.text}")
except Exception as e:
    print(f"❌ 请求失败: {e}")
```

## 常见问题

### Q1: 重启后仍然404

**检查项**：
1. 后端是否真的重启了（检查终端输出时间戳）
2. 端口是否正确（默认8000）
3. 是否有其他错误阻止路由注册

### Q2: Swagger UI中看不到FPGA的code-view端点

**可能原因**：
1. 路由加载失败
2. 有导入错误
3. 端点定义有语法错误

**解决方法**：
1. 检查后端启动日志
2. 查看是否有错误信息
3. 确认所有import都正确

### Q3: C/C++的code-view工作但FPGA的不工作

**原因**：
- FPGA的路由可能没有正确包含到主路由
- filterFpga/api/api.py可能没有被正确导入

**检查**：
```python
# 在 staticAnalysis/__init__.py 中确认：
from .filterFpga.api.api import router as filter_fpga_router
router.include_router(filter_fpga_router, prefix="/fpga", tags=["static-analysis-filter-fpga"])
```

## 验证清单

完成以下检查：

- [ ] ✅ 确认 `filterFpga/api/api.py` 包含 `code-view` 端点（第872行）
- [ ] ✅ 确认 `staticAnalysis/__init__.py` 包含FPGA路由挂载
- [ ] ✅ 重启后端服务
- [ ] ✅ 访问 `/docs` 确认端点已注册
- [ ] ✅ 测试FPGA代码视图，确认无404错误

## 预期结果

重启后端服务后：
1. ✅ `/docs` 中能看到FPGA的code-view端点
2. ✅ 前端访问FPGA代码视图不再报404
3. ✅ 能正常加载FPGA代码和问题列表

## 相关文件

### 后端
- `backend/app/staticAnalysis/filterFpga/api/api.py` - FPGA代码视图API
- `backend/app/staticAnalysis/__init__.py` - 主路由配置
- `backend/run_fastapi.py` - 后端启动文件

### 前端
- `frontend_vue/src/views/staticAnalysis/filterFpga/StaticAnalysisCodeView.vue` - FPGA代码视图组件

### 文档
- `backend/app/staticAnalysis/filterFpga/FPGA_CODE_VIEW_404_FIX.md` - 本文档

## 修改日期

2025年12月3日
