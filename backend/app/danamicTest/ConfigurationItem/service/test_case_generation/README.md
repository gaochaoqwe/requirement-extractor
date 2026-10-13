# 测试用例生成模块（重构版）

本目录提供“基于测试方法”的测试用例生成与写入能力，已按职责解耦为多个子模块，便于复用与测试。

## 模块结构

- ai/
  - prompts.py：构建系统/用户/批量生成 Prompt 的纯函数
  - client.py：统一的 AI 客户端封装（重试、响应清理、最小校验）
- parsing/
  - response_parser.py：解析批量 AI 响应为方法-用例映射
  - fallback.py：兜底用例生成（逐方法生成），以回调注入拆分与单方法生成
- rendering/
  - formatters.py：将“方法-用例”数据格式化为 Excel 行数据（纯函数+回调）
- excel_io/
  - writer.py：Excel 写入封装。
    - write_formatted_cases_to_excel：增强服务路径（复用表单写入逻辑）
    - write_realtime_cases_to_excel：实时服务路径（简单表头写入）
- services（位于同目录的类文件）：
  - enhanced_test_case_service.py：增强服务（推荐对外入口）
  - realtime_test_case_service.py：实时服务
  - method_based_test_case_generator.py：核心生成器（建议通过服务层使用）

## 使用示例

- 推荐入口（增强服务）：
```python
from backend.app.danamicTest.ConfigurationItem.service.test_case_generation import EnhancedTestCaseService

svc = EnhancedTestCaseService()
# requirement_analysis_data: 从“需求分析”服务读取得到
success = svc.generate_and_fill_test_cases(
    requirement_analysis_data=requirement_analysis_data,
    excel_path="output.xlsx",
    sheet_name="测试用例单",
    software_info={"software_name": "Demo", "software_version": "1.0.0"},
    test_type="功能测试",
    detector_flag="无检测仪",
    zhuguan_name="主管",
    ceshiren_name="测试人员",
    task_id="task-001",
)
```

- 实时服务：
```python
from backend.app.danamicTest.ConfigurationItem.service.test_case_generation import RealtimeTestCaseService

rt = RealtimeTestCaseService()
ok = rt.generate_realtime_test_cases(
    requirement_analysis_data=some_data,
    excel_path="realtime.xlsx",
    sheet_name="测试用例单",
    software_info={"software_name": "Demo", "software_version": "1.0.0"},
)
```

- 如果仅需生成“方法-用例”映射（不直接写 Excel）：
```python
from backend.app.danamicTest.ConfigurationItem.service.test_case_generation import MethodBasedTestCaseGenerator

gen = MethodBasedTestCaseGenerator()
method_based_cases = gen.generate_test_cases_from_requirement_analysis(test_items, "功能测试", "无检测仪")
formatted_rows = gen.format_test_cases_for_excel(method_based_cases, {"software_name": "Demo", "software_version": "1.0.0"}, task_id=None)
```

## 兼容性
- 公有方法签名保持不变；原私有方法保留，外层已改为委托到新模块，便于回滚。
- 建议外部仅通过服务类调用，避免直接依赖底层 openpyxl 或网络调用实现。

## 开发建议
- 新增功能优先放入对应子模块（ai/parsing/rendering/excel_io）。
- 服务类仅做编排与日志，避免堆积业务细节。
