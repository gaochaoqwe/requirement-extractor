"""
实时测试用例生成服务

输入单个测试项信息 -> 调用AI生成 -> 解析与字段映射 -> 保存至数据库
"""
from typing import List, Dict, Any, Optional

try:
    from .ai.prompts import build_system_prompt, build_user_prompt, build_batch_test_case_prompt
    from .ai.client import call_ai_for_simple_generation, call_ai_for_batch_generation
    from .test_case_form_handler import get_test_time_info
    from ...db.optimized_models import OptimizedDynamicTestDatabase
    from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    from .parsing.response_parser import parse_batch_ai_response
except ImportError:
    try:
        from app.danamicTest.ConfigurationItem.service.test_case_generation.ai.prompts import build_system_prompt, build_user_prompt, build_batch_test_case_prompt
        from app.danamicTest.ConfigurationItem.service.test_case_generation.ai.client import call_ai_for_simple_generation, call_ai_for_batch_generation
        from app.danamicTest.ConfigurationItem.service.test_case_generation.test_case_form_handler import get_test_time_info
        from app.danamicTest.ConfigurationItem.db.optimized_models import OptimizedDynamicTestDatabase
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
        from app.danamicTest.ConfigurationItem.service.test_case_generation.parsing.response_parser import parse_batch_ai_response
    except Exception:  # 兜底，避免导入失败导致崩溃
        def log_info(msg: str, module: str = None):
            print(f"[INFO] {module or 'realtime_service'}: {msg}")
        def log_error(msg: str, module: str = None):
            print(f"[ERROR] {module or 'realtime_service'}: {msg}")
        def log_warning(msg: str, module: str = None):
            print(f"[WARN] {module or 'realtime_service'}: {msg}")
        def log_debug(msg: str, module: str = None):
            print(f"[DEBUG] {module or 'realtime_service'}: {msg}")
        # 简易占位符，运行期若触发此分支请修正导入路径
        def build_system_prompt(requirement_name: str, ceshileixing: str, jianceyi_flag: str) -> str:
            return "请输出 {\"test_cases\": [] }"
        def build_user_prompt(test_method: str, test_description: str, requirement_name: str, requirement_desc: str, ceshileixing: str, method_index: int = 1) -> str:
            return ""
        def call_ai_for_simple_generation(system_prompt: str, user_prompt: str, max_retry: int = 3) -> str:
            return "{\"test_cases\": []}"
        def get_test_time_info():
            return ("2025/01/01", "2025/01/02", "2025-01")
        class OptimizedDynamicTestDatabase:
            def save_test_cases(self, task_id: str, rows: List[Dict[str, Any]]):
                pass


class RealtimeTestCaseService:
    """AI 实时生成测试用例并入库的服务"""

    def __init__(self):
        pass

    @staticmethod
    def _parse_ai_json(json_str: str) -> List[Dict[str, Any]]:
        """解析AI返回的JSON字符串，提取 test_cases 列表"""
        import json
        try:
            data = json.loads(json_str or "")
            if isinstance(data, dict) and isinstance(data.get("test_cases"), list):
                return data["test_cases"]
            return []
        except Exception:
            return []

    def generate_and_save_cases(
        self,
        task_id: str,
        requirement_name: str,
        requirement_desc: str,
        test_method: str,
        test_description: str,
        test_type: str,
        detector_flag: str,
        software_item_name: Optional[str] = None,
        software_version: Optional[str] = None,
        test_item_identifier: Optional[str] = None,
        requirement_traceability: Optional[str] = None,
        start_sequence: int = 1,
        ceshiren_name: str = "测试人员",
        zhuguan_name: str = "主管",
        database_template_name: Optional[str] = None,
        database_template_input: Optional[str] = None,
        database_template_expected: Optional[str] = None,
        is_database_matched: bool = False
    ) -> Dict[str, Any]:
        """
        调用AI生成用例并入库
        返回: { success: bool, saved_count: int, cases: List[Dict] }
        """
        try:
            log_info(f"[Realtime] 开始生成: {requirement_name}, start_sequence={start_sequence}", "realtime_service")
            system_prompt = build_system_prompt(requirement_name, test_type, detector_flag)
            user_prompt = build_user_prompt(
                test_method=test_method,
                test_description=test_description,
                requirement_name=requirement_name,
                requirement_desc=requirement_desc,
                ceshileixing=test_type,
                method_index=1,
            )

            ai_output = call_ai_for_simple_generation(system_prompt, user_prompt, max_retry=3)
            cases = self._parse_ai_json(ai_output)
            if not cases:
                log_warning("AI未返回有效用例，保存空列表", "realtime_service")
                return {"success": False, "saved_count": 0, "cases": [], "actual_case_count": 0}

            # 时间信息
            design_time, test_time, year_month = get_test_time_info()

            # 映射为DB行
            rows: List[Dict[str, Any]] = []
            
            # 🔧 修复：对于数据库匹配的测试项，只生成一个用例，避免重复
            if is_database_matched:
                # 数据库匹配的情况：只生成一个用例，使用数据库模板
                cases_to_process = [{}]  # 只需要一个空字典作为占位符
                log_info(f"[DATABASE_MATCHED] 数据库匹配用例，只生成1个用例", "realtime_service")
            else:
                # AI生成的情况：使用AI返回的所有用例
                cases_to_process = cases
                log_info(f"[AI_GENERATED] AI生成用例，共{len(cases)}个用例", "realtime_service")
            
            for i, c in enumerate(cases_to_process, start=start_sequence):
                # 🔧 修复：对于数据库匹配的用例，优先使用数据库模板中的用例名称
                if is_database_matched and database_template_name and database_template_name.strip():
                    # 🔧 新增：为数据库模板用例名称添加来源标记
                    case_name = f"[DB_SOURCE]{database_template_name.strip()}"  # 使用数据库中的用例模板名称并添加标记
                    log_info(f"[DATABASE_TEMPLATE] 使用数据库模板用例名称: '{database_template_name.strip()}'", "realtime_service")
                elif is_database_matched:
                    # 🔧 新增：为数据库匹配但无模板名称的用例添加标记
                    case_name = f"[DB_SOURCE]{requirement_name}{start_sequence}"  # 如：操作日志审计功能1
                else:
                    case_name = (c.get("case_name") or f"用例{i}").strip()  # AI生成的用例名称，去掉requirement_name前缀
                
                # 🔧 修复：测试用例的测试描述直接使用需求分析表中的测试项描述，不使用AI生成的case_description
                case_desc = test_description.strip()
                
                # 🔧 新增：对于数据库匹配的测试项，直接使用数据库中的输入条件和预期结果
                if is_database_matched and database_template_input and database_template_expected:
                    # 🔧 新增：为数据库模板内容添加来源标记
                    input_conditions = f"[DB_SOURCE]{database_template_input.strip()}"
                    expected_results = f"[DB_SOURCE]{database_template_expected.strip()}"
                    log_info(f"[DATABASE_TEMPLATE] 使用数据库模板: 输入条件长度={len(database_template_input)}, 预期结果长度={len(database_template_expected)}", "realtime_service")
                else:
                    input_conditions = (c.get("input_conditions") or "").strip()
                    expected_results = (c.get("expected_results") or "").strip()

                # 编号策略：优先使用测试项标识+序号
                if test_item_identifier:
                    test_case_number = f"{test_item_identifier}-{i:02d}"
                else:
                    test_case_number = f"{requirement_name}-{i:02d}"
                
                log_debug(f"[CASE_NUMBER] 生成用例编号: {test_case_number}, i={i}, start_sequence={start_sequence}", "realtime_service")

                # 计算校对时间（设计时间后一天）
                try:
                    import datetime
                    design_date = datetime.datetime.strptime(design_time, '%Y/%m/%d')
                    review_date = design_date + datetime.timedelta(days=1)
                    review_time_str = review_date.strftime('%Y/%m/%d')
                except:
                    review_time_str = design_time  # 如果解析失败，使用原时间
                
                row: Dict[str, Any] = {
                    # 关键关联
                    "requirement_id": requirement_name,
                    # 基础列映射
                    "test_case_id": None,
                    "sequence_number": i,
                    "software_item_name": software_item_name or "",
                    "software_version": (software_version or "").lstrip("Vv"),
                    "test_round": "第一轮",
                    "requirement_traceability": requirement_traceability or "",
                    "test_item_name": requirement_name,
                    "test_item_identifier": test_item_identifier or requirement_name,
                    "test_case_name": case_name,
                    "test_case_number": test_case_number,
                    "test_type": test_type,
                    "test_description": case_desc,
                    "preconditions": "被测软件正常加载，检测仪、调试计算机上电、测试环境连接正常",
                    "prerequisites_constraints": "无",
                    "input_actions": None,
                    "input_conditions": input_conditions,
                    "expected_results": expected_results,
                    "pass_criteria": "实测结果与预期结果一致表明测试通过，否则测试不通过",
                    "case_designer": ceshiren_name,
                    "reviewer": zhuguan_name,
                    "design_time": design_time,
                    "review_time": review_time_str,
                    "test_personnel": ceshiren_name,
                    "supervisor": zhuguan_name,
                    "test_time": test_time,
                    "test_result": "",  # 待执行
                    "test_conclusion": "通过",
                    "issue_report_number": "",
                    "execution_year_month": year_month,
                    "issues_found_count": 0,
                }
                rows.append(row)

            db = OptimizedDynamicTestDatabase()
            try:
                db_path = getattr(db, 'db_path', None)
                if db_path:
                    log_debug(f"DB路径: {db_path}", "realtime_service")
            except Exception:
                pass
            db.save_test_cases(task_id, rows)
            # 写后校验
            try:
                _rows = db.get_test_cases_by_task(task_id)
                log_info(f"[Realtime] 保存用例 {len(rows)} 条，库内现有 {len(_rows)} 条 (task_id={task_id})", "realtime_service")
                if _rows:
                    log_debug(f"首条示例: {_rows[0]}", "realtime_service")
            except Exception as _e_v:
                log_warning(f"写后校验失败: {_e_v}", "realtime_service")
            result = {
                "success": True, 
                "saved_count": len(rows), 
                "cases": rows,
                "actual_case_count": len(cases_to_process)  # 🔧 新增：返回实际生成的用例数量
            }
            log_info(f"[RETURN_DEBUG] 返回结果: actual_case_count={result['actual_case_count']}, saved_count={result['saved_count']}", "realtime_service")
            return result
        except Exception as e:
            log_error(f"实时生成入库失败: {e}", "realtime_service")
            return {"success": False, "saved_count": 0, "cases": [], "actual_case_count": 0}

    def generate_and_save_cases_by_descriptions(
        self,
        task_id: str,
        requirement_name: str,
        requirement_desc: str,
        requirement_sub_desc: str,
        description_items: List[str],
        method_items: List[str],
        test_type: str,
        detector_flag: str,
        software_item_name: Optional[str] = None,
        software_version: Optional[str] = None,
        test_item_identifier: Optional[str] = None,
        requirement_traceability: Optional[str] = None,
        start_sequence: int = 1,
        ceshiren_name: str = "测试人员",
        zhuguan_name: str = "主管",
        database_template_name: Optional[str] = None,
        database_template_input: Optional[str] = None,
        database_template_expected: Optional[str] = None,
        is_database_matched: bool = False
    ) -> Dict[str, Any]:
        """
        单次请求覆盖一个测试项下的“所有测试项描述条目”的全部用例：
        - 构造批量Prompt并调用模型
        - 解析各方法对应的用例
        - 与 description_items 一一对齐：每个条目至少一条用例
        - 映射字段并一次入库
        """
        try:
            # 1) 组装批量提示词并调用AI
            prompt = build_batch_test_case_prompt(
                requirement_name=requirement_name,
                requirement_desc=requirement_desc,
                requirement_sub_desc=requirement_sub_desc,
                description_items=description_items,
                method_items=method_items,
                ceshileixing=test_type,
                jianceyi_flag=detector_flag,
            )
            ai_json = call_ai_for_batch_generation(prompt)
            method_to_cases: Dict[str, List[Dict[str, str]]] = {}
            index_to_cases: Dict[int, List[Dict[str, str]]] = {}
            if ai_json:
                try:
                    method_to_cases = parse_batch_ai_response(ai_json, method_items) or {}
                    # 额外：基于原始JSON构建“按索引”映射，避免方法文本不完全一致导致匹配失败
                    import json as _json
                    try:
                        _data = _json.loads(ai_json)
                        if isinstance(_data, dict) and isinstance(_data.get('test_cases_by_method'), list):
                            for _it in _data['test_cases_by_method']:
                                if not isinstance(_it, dict):
                                    continue
                                _idx = _it.get('method_index')
                                _tcs = _it.get('test_cases')
                                if isinstance(_idx, int) and isinstance(_tcs, list):
                                    # 简单校验：字段必须存在且为非空字符串
                                    _valid = []
                                    for _c in _tcs:
                                        if isinstance(_c, dict) and all(isinstance(_c.get(k, ''), str) and _c.get(k, '').strip() for k in ('case_name','case_description','input_conditions','expected_results')):
                                            _valid.append(_c)
                                    if _valid:
                                        index_to_cases[_idx] = _valid
                    except Exception as _e_json:
                        log_warning(f"按索引构建映射失败: {_e_json}", "method_based_generator")
                except Exception as e:
                    log_warning(f"批量解析失败，将尝试逐方法兜底: {e}", "realtime_generator")

            # 2) 与描述条目对齐：确保每个描述条目至少有1条用例
            aligned_rows: List[Dict[str, Any]] = []
            seq = max(1, int(start_sequence))

            # 时间信息（与表单保持一致） - 兼容 tuple/dict 两种返回
            time_info = get_test_time_info()
            design_time = ''
            test_time = ''
            year_month = ''
            try:
                if isinstance(time_info, tuple) and len(time_info) == 3:
                    design_time, test_time, year_month = time_info
                elif isinstance(time_info, dict):
                    design_time = time_info.get('design_time', '')
                    test_time = time_info.get('test_time', '')
                    year_month = time_info.get('year_month', '')
                else:
                    log_warning(f"get_test_time_info 返回未知类型: {type(time_info)}", "realtime_generator")
            except Exception as _e:
                log_warning(f"解析时间信息失败: {_e}", "realtime_generator")

            # 清洗版本号
            def _clean_version(v: Optional[str]) -> Optional[str]:
                if not v:
                    return v
                return v[1:] if isinstance(v, str) and v.startswith(('V', 'v')) else v

            # 若AI返回多个方法，而输入仅1条描述，则尝试拆分描述/或复制描述以匹配方法数
            try:
                total_methods = 0
                if method_to_cases:
                    total_methods = len(method_to_cases)
                elif index_to_cases:
                    total_methods = len(index_to_cases)
                if total_methods > 1 and len(description_items) == 1:
                    raw_desc = description_items[0] or ""
                    # 常见分隔：换行、中文顿号、编号“1、2、3、4、”等
                    import re as _re
                    # 先按换行切
                    parts = [p.strip() for p in (raw_desc.splitlines() if raw_desc else []) if p.strip()]
                    # 若按行不足，再按编号切
                    if len(parts) < total_methods:
                        tmp = _re.split(r"(?:^|\s)(?:\d+、|\d+\.|（\d+）|\(\d+\))\s*", raw_desc)
                        parts2 = [p.strip() for p in tmp if p and p.strip()]
                        if len(parts2) >= len(parts):
                            parts = parts2
                    # 若仍不足，按中文分号或分隔符切
                    if len(parts) < total_methods:
                        tmp = _re.split(r"[；;]\s*", raw_desc)
                        parts3 = [p.strip() for p in tmp if p and p.strip()]
                        if len(parts3) >= len(parts):
                            parts = parts3
                    # 若仍不足，复制描述
                    if len(parts) < total_methods:
                        parts = [raw_desc.strip() or ""] * total_methods
                    else:
                        # 若超过方法数，截断
                        parts = parts[:total_methods]
                    log_debug(f"描述扩展: methods={total_methods}, 原始1条 -> 扩展为 {len(parts)} 条", "realtime_generator")
                    description_items = parts
            except Exception as _e_split:
                log_warning(f"描述扩展失败，将使用单条描述: {_e_split}", "realtime_generator")

            log_debug(f"对齐阶段: description_items={len(description_items)}, method_items={len(method_items)}", "realtime_generator")
            for idx, desc in enumerate(description_items):
                method_text = method_items[idx] if idx < len(method_items) else (method_items[-1] if method_items else "")
                cases = method_to_cases.get(method_text, [])
                matched_by = "text"
                if not cases:
                    # 按索引（1-based）匹配
                    cases = index_to_cases.get(idx + 1, [])
                    matched_by = "index" if cases else matched_by
                log_debug(f"条目{idx+1}: method_text='{(method_text or '')[:40]}', 匹配方式={matched_by}, 命中用例数={len(cases) if isinstance(cases, list) else 0}", "realtime_generator")

                # 兜底：若该方法没有生成任何用例，调用单项实时生成获取至少一条
                if not cases:
                    try:
                        sys_prompt = build_system_prompt(requirement_name, test_type, detector_flag)
                        usr_prompt = build_user_prompt(
                            test_method=method_text or desc,
                            test_description=desc,
                            requirement_name=requirement_name,
                            requirement_desc=requirement_desc,
                            ceshileixing=test_type,
                            method_index=idx + 1,
                        )
                        single_json = call_ai_for_simple_generation(sys_prompt, usr_prompt)
                        import json as _json
                        if single_json:
                            d = _json.loads(single_json)
                            if isinstance(d, dict) and isinstance(d.get('test_cases'), list):
                                cases = d['test_cases'][:1] or []
                    except Exception as e:
                        log_warning(f"兜底实时生成失败: 条目{idx+1} - {e}", "realtime_generator")

                # 若仍为空，放置一条可跟进的占位用例
                if not cases:
                    cases = [{
                        'case_name': f"{requirement_name}-条目{idx+1}基本验证",
                        'case_description': f"针对测试项描述条目进行基本验证: {desc[:50]}...",
                        'input_conditions': "步骤1：准备环境；步骤2：根据条目执行；步骤3：记录现象",
                        'expected_results': "完成步骤3：系统行为符合条目要求或给出明确反馈",
                    }]
                    log_warning(f"条目{idx+1}: 无法从批量/兜底获取有效用例，已放置占位用例", "realtime_generator")

                # 映射到DB行：测试描述列严格填"对应的测试项描述条目"
                for local_i, case in enumerate(cases, start=1):
                    # 计算校对时间（设计时间后一天）
                    try:
                        import datetime
                        design_date = datetime.datetime.strptime(design_time, '%Y/%m/%d')
                        review_date = design_date + datetime.timedelta(days=1)
                        review_time_str = review_date.strftime('%Y/%m/%d')
                    except:
                        review_time_str = design_time  # 如果解析失败，使用原时间
                    
                    row = {
                        'requirement_id': None,
                        'test_case_id': None,
                        'software_item_name': software_item_name,
                        'software_version': _clean_version(software_version),
                        'test_round': '第一轮',
                        'requirement_traceability': requirement_traceability,
                        'test_item_name': requirement_name,
                        'test_item_identifier': test_item_identifier,
                        # 🔧 修复：对于数据库匹配的用例，优先使用数据库模板中的用例名称
                        'test_case_name': (
                            database_template_name.strip() if (is_database_matched and database_template_name and database_template_name.strip()) 
                            else f"{requirement_name}{idx+1}" if is_database_matched 
                            else (case.get('case_name') or f"条目{idx+1}-用例{local_i}")
                        ),
                        'test_case_number': f"{(test_item_identifier or requirement_name)}-{seq:02d}",
                        'test_type': test_type,
                        'test_description': desc,  # 对齐对应条目
                        'preconditions': '被测软件正常加载，检测仪、调试计算机上电、测试环境连接正常',
                        'prerequisites_constraints': '无',
                        'input_actions': '',
                        # 🔧 新增：对于数据库匹配的测试项，直接使用数据库中的输入条件和预期结果
                        'input_conditions': database_template_input if (is_database_matched and database_template_input) else case.get('input_conditions', ''),
                        'expected_results': database_template_expected if (is_database_matched and database_template_expected) else case.get('expected_results', ''),
                        'pass_criteria': '实测结果与预期结果一致表明测试通过，否则测试不通过',
                        'case_designer': ceshiren_name,
                        'reviewer': zhuguan_name,
                        'design_time': design_time,
                        'review_time': review_time_str,
                        'test_personnel': ceshiren_name,
                        'supervisor': zhuguan_name,
                        'test_time': test_time,
                        'test_result': '',
                        'test_conclusion': '通过',
                        'issue_report_number': '',
                        'execution_year_month': year_month,
                        'issues_found_count': 0,
                    }
                    aligned_rows.append(row)
                    seq += 1

            # 3) 入库（统一一次保存）
            db = OptimizedDynamicTestDatabase()
            try:
                db_path = getattr(db, 'db_path', None)
                if db_path:
                    log_debug(f"DB路径: {db_path}", "realtime_generator")
            except Exception:
                pass
            # 批量保存，避免每次从1开始导致的覆盖问题
            saved_count = 0
            try:
                db.save_test_cases(task_id, aligned_rows)
                saved_count = len(aligned_rows)
            except Exception as e:
                log_warning(f"批量保存用例失败，将逐条尝试: {e}", "realtime_generator")
                for i, row in enumerate(aligned_rows, start=int(start_sequence) or 1):
                    try:
                        db.save_test_case_row(task_id=task_id, sequence_number=i, row=row)
                        saved_count += 1
                    except Exception as e2:
                        log_warning(f"保存第{i}条用例失败: {e2}", "realtime_generator")

            # 写后校验
            try:
                _rows = db.get_test_cases_by_task(task_id)
                log_info(f"批量生成并入库完成：测试项 '{requirement_name}', 条目 {len(description_items)} 个, 共保存 {saved_count} 条；库内现有 {len(_rows)} 条 (task_id={task_id})", "realtime_generator")
                if _rows:
                    log_debug(f"保存明细首条: {_rows[0]}", "realtime_generator")
            except Exception as _e_v:
                log_warning(f"写后校验失败: {_e_v}", "realtime_generator")
            log_debug(f"保存明细: aligned_rows={len(aligned_rows)}, 首条示例={aligned_rows[0] if aligned_rows else {} }", "realtime_generator")
            return {"success": True, "saved_count": saved_count, "cases": aligned_rows, "actual_case_count": len(aligned_rows)}
        except Exception as e:
            log_error(f"批量生成并入库失败: {str(e)}", "realtime_generator")
            return {"success": False, "error": str(e), "actual_case_count": 0}
