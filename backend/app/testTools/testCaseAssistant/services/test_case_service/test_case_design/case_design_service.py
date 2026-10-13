from __future__ import annotations

from typing import Any, Dict, List, Tuple

import re

from ....utils.logger import setup_session_logger
from ....database.database import get_db_session
from ....models.models import CaseDesignRepo
from .case_design_ai_client import CaseDesignAIClient
from ...tool.code_locator import (
    locate_snippet_in_repo,
    guess_function_name_from_snippet,
    extract_call_line_for_test_item,
    find_enclosing_function_in_file,
    find_instrumentation_anchor_in_function,
)


class CaseDesignService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = setup_session_logger(session_id)
        self.ai_client = CaseDesignAIClient(session_id)

    def _extract_xx(self, test_item_name: str) -> str:
        name = (test_item_name or '').strip()
        if not name:
            return ''
        if '初始化' in name:
            return name.split('初始化')[0].strip()
        return name

    def _apply_placeholders(self, template: str, xx: str, yy: str, zz: str, mm: str) -> str:
        s = template or ''
        # 优先替换带说明的占位文本
        for pat in [
            'xx（变量/硬件/中断等）',
            'xx(变量/硬件/中断等)',
            'xx（SRIO/CAN等）',
            'xx(SRIO/CAN等)',
        ]:
            if xx:
                s = s.replace(pat, xx)

        # 兜底替换裸占位符
        if xx:
            s = re.sub(r'\bxx\b', xx, s)
        if yy:
            s = re.sub(r'\byy\b', yy, s)
        if zz:
            s = re.sub(r'\bzz\b', zz, s)
        if mm:
            s = re.sub(r'\bmm\b', mm, s)
        return s

    def _apply_xx_only(self, template: str, xx: str) -> str:
        s = template or ''
        if xx:
            # 支持 xx（任意说明）/xx(任意说明) 的整体替换（去掉括号示例说明）
            s = re.sub(r'xx（[^）]*）', xx, s)
            s = re.sub(r'xx\([^)]*\)', xx, s)

        for pat in [
            'xx（变量/硬件/中断等）',
            'xx(变量/硬件/中断等)',
            'xx（SRIO/CAN等）',
            'xx(SRIO/CAN等)',
        ]:
            if xx:
                s = s.replace(pat, xx)
        if xx:
            s = re.sub(r'\bxx\b', xx, s)
        return s

    def _need_fallback_xx_only(self, original: str, ai_text: str, keep_tokens: List[str]) -> bool:
        src = str(original or '')
        out = str(ai_text or '')

        # 如果模板包含步骤结构，AI 不得删改
        if '步骤1' in src and '步骤1' not in out:
            return True
        if '步骤2' in src and '步骤2' not in out:
            return True

        # 如果模板中存在其它占位符（yy/zz/mm/nn/kk），AI 必须原样保留
        for tok in keep_tokens:
            if re.search(rf'\b{re.escape(tok)}\b', src) and not re.search(rf'\b{re.escape(tok)}\b', out):
                return True

        # 自检测裂变场景：固定关键短语不能被删除（否则表示AI改写了模板结构）
        for phrase in ['代码插桩设置', '插装代码为', '故障，在']:
            if phrase in src and phrase not in out:
                return True

        return False

    def _truncate_for_log(self, text: str, limit: int = 800) -> str:
        s = str(text or '')
        if len(s) <= limit:
            return s
        return s[:limit] + '...<truncated>'

    def _default_templates(self) -> Dict[str, str]:
        return {
            'case_name': '"xx（变量/硬件/中断等）"正常初始化',
            'test_desc': '测试软件能否对"xx（变量/硬件/中断等）"正常初始化',
            'input_condition': (
                '步骤1：在"xx（变量/硬件/中断等）"初始化对应的"yy"文件"zz"函数中的\n'
                '"mm（此处是"xx（变量/硬件/中断等）"初始化函数被调用执行那句代码）"\n'
                '代码下方打断点\n'
                '步骤2：软件正常运行，通过调试计算机观察软件是否运行到断点处，判断"xx（变量/硬件/中断等）"初始化函数可以被正常执行完成'
            ),
            'expected_result': '完成步骤2：软件可以运行到断点处，说明"xx（变量/硬件/中断等）"初始化函数可以被正常执行完成',
        }

    def _default_api_exception_templates(self) -> Dict[str, str]:
        return {
            'case_name': '"xx（SRIO/CAN等）"总线接收-"qq（校验位错误/数据长度错误）"',
            'test_desc': '2、测试软件是否对接收的"xx（SRIO/CAN等）"异常数据做正确处理',
            'input_condition': (
                '"步骤1：代码插桩设置""xx（SRIO/CAN等）""总线接收到异常数据，在""yy""文件""zz""函数第""mm""行进行插桩，插桩代码为：\n'
                '""nn""（此处是模拟""qq（校验位错误/数据长度错误）""的插桩代码）\n'
                '设置接收到的数据为异常数据""qq（校验位错误/数据长度错误）""，并打印其对数据的处理结果\n'
                '步骤2：软件正常运行，通过串口查看软件是否识别到了异常数据并且没有使用数据包内的数据段内容"'
            ),
            'expected_result': '完成步骤2：软件识别到了异常数据并且没有使用数据包内数据段内容',
        }

    def _default_api_period_templates(self) -> Dict[str, str]:
        return {
            'case_name': '"xx（SRIO/CAN等）"总线"kk（接收/发送）"-周期',
            'test_desc': '2、测试软件是否对"xx（SRIO/CAN等）"总线"kk（接收/发送）"数据处理周期做正确处理',
            'input_condition': (
                '步骤1：代码插桩计算"xx（SRIO/CAN等）"计算总线数据处理周期，在"yy"文件"zz"函数第"mm"行进行插桩，插桩代码为：\n'
                '"nn"（此处是"xx（SRIO/CAN等）"总线接收/发送的数据处理周期中打印时间戳的代码）\n'
                '打印"xx（SRIO/CAN等）"总线"kk（接收/发送）"数据信息的时间戳\n'
                '步骤2：软件正常运行，通过串口查看软件"kk（接收/发送）"数据的时间戳信息并计算其数据收发周期是否符合接口协议要求'
            ),
            'expected_result': '完成步骤2：通过串口查看软件"kk（接收/发送）"数据的时间戳信息为"cc"，计算其数据收发周期为"dd"，符合接口协议要求',
        }

    def _replace_qq(self, text: str, qq_value: str) -> str:
        s = str(text or '')
        if not qq_value:
            return s
        # 替换 "qq(....)" / "qq（....）" 的引号内整体内容
        s = re.sub(r'qq（[^）]*）', qq_value, s)
        s = re.sub(r'qq\([^)]*\)', qq_value, s)
        s = re.sub(r'\bqq\b', qq_value, s)
        return s

    def _replace_kk(self, text: str, kk_value: str) -> str:
        s = str(text or '')
        if not kk_value:
            return s

        for pat in [
            'kk（接收/发送）',
            'kk(接收/发送)',
        ]:
            s = s.replace(pat, kk_value)

        s = re.sub(r'\bkk\b', kk_value, s)
        return s

    def _get_latest_repo_extract_path(self, task_id: str) -> str:
        with get_db_session() as db:
            repo = (
                db.query(CaseDesignRepo)
                .filter(CaseDesignRepo.task_id == task_id)
                .order_by(CaseDesignRepo.id.desc())
                .first()
            )
            if not repo:
                raise ValueError('当前任务未绑定代码库，请先上传zip代码库')
            return repo.extract_path

    async def case_design_init(self, task_id: str, entry_code_snippet: str, rows) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        extract_path = self._get_latest_repo_extract_path(task_id)

        snippet_text = (entry_code_snippet or '').replace('\r\n', '\n').replace('\r', '\n')
        snippet_lines = [ln for ln in snippet_text.split('\n') if ln.strip()]
        self.logger.info(
            '用例设计-初始化：开始定位入口片段 task_id=%s, extract_path=%s, snippet_non_empty_lines=%d',
            task_id,
            extract_path,
            len(snippet_lines),
        )
        if snippet_lines:
            self.logger.info('用例设计-初始化：snippet_first_line=%s', snippet_lines[0].strip())
            self.logger.info('用例设计-初始化：snippet_last_line=%s', snippet_lines[-1].strip())

        loc = locate_snippet_in_repo(extract_path, entry_code_snippet, logger=self.logger)
        if not loc:
            self.logger.error('用例设计-初始化：入口片段定位失败')
            raise ValueError('未能在代码库中定位入口函数代码片段，请确认上传的代码库与粘贴的代码一致')

        func_name = guess_function_name_from_snippet(entry_code_snippet)

        # 从定位到的文件/行号中解析真实函数名（更可靠）
        parsed_func, parsed_start, parsed_end, parsed_ctx = find_enclosing_function_in_file(loc.file_path, loc.start_line)
        if parsed_func:
            func_name = parsed_func

        parsed_ctx_numbered = ''
        if parsed_ctx and parsed_start:
            ctx_lines = (parsed_ctx or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
            numbered = []
            for i, ln in enumerate(ctx_lines):
                numbered.append(f'{parsed_start + i}: {ln}')
            parsed_ctx_numbered = '\n'.join(numbered)

        instrument_line, instrument_anchor = (0, '')
        if parsed_start and parsed_end:
            instrument_line, instrument_anchor = find_instrumentation_anchor_in_function(
                loc.file_path,
                parsed_start,
                parsed_end,
            )

        self.logger.info(
            f'用例设计-初始化：定位入口片段成功 file={loc.file_path}, lines={loc.start_line}~{loc.end_line}, func={func_name}'
        )

        if instrument_line:
            self.logger.info('用例设计-初始化：instrument_line=%d anchor=%s', instrument_line, instrument_anchor)

        for row in rows:
            try:
                call_line = extract_call_line_for_test_item(row.test_item_name, entry_code_snippet)
                payload = {
                    'test_item_name': row.test_item_name,
                    'template_case_name': row.template_case_name,
                    'template_test_desc': row.template_test_desc,
                    'template_input_condition': row.template_input_condition,
                    'template_expected_result': row.template_expected_result,
                    'code_file': loc.file_path.split('\\')[-1],
                    'func_name': func_name,
                    'line_start': loc.start_line,
                    'line_end': loc.end_line,
                    'call_line': call_line,
                    'enclosing_func_start': parsed_start,
                    'enclosing_func_end': parsed_end,
                    'enclosing_func_context': parsed_ctx,
                    'enclosing_func_context_numbered': parsed_ctx_numbered,
                    'instrument_line': instrument_line,
                    'instrument_anchor': instrument_anchor,
                }

                self.logger.info(f"用例设计-初始化：开始处理 row_index={row.row_index}, 测试项名称={row.test_item_name}")
                ai_res = await self.ai_client.generate_init(payload)
                if not ai_res.get('success'):
                    raise ValueError(ai_res.get('error') or 'AI调用失败')

                data = ai_res['data']

                # 强制模板：只允许替换变量，不允许改写固定句式/步骤
                xx = self._extract_xx(row.test_item_name)
                yy = payload['code_file']
                zz = payload.get('func_name') or func_name
                mm = call_line
                defaults = self._default_templates()

                t_case_name = row.template_case_name or defaults['case_name']
                t_test_desc = row.template_test_desc or defaults['test_desc']
                t_input = row.template_input_condition or defaults['input_condition']
                t_expected = row.template_expected_result or defaults['expected_result']

                filled_case_name = self._apply_placeholders(t_case_name, xx=xx, yy=yy, zz=zz, mm=mm)
                filled_test_desc = self._apply_placeholders(t_test_desc, xx=xx, yy=yy, zz=zz, mm=mm)
                filled_input = self._apply_placeholders(t_input, xx=xx, yy=yy, zz=zz, mm=mm)
                filled_expected = self._apply_placeholders(t_expected, xx=xx, yy=yy, zz=zz, mm=mm)

                # 若 AI 返回不包含模板关键字（例如“步骤1/步骤2”），直接回退到模板填充
                ai_input = str(data.get('input_condition', '') or '').strip()
                ai_expected = str(data.get('expected_result', '') or '').strip()
                if '步骤1' not in ai_input or '步骤2' not in ai_input:
                    data['input_condition'] = filled_input
                if '完成步骤2' not in ai_expected and '步骤2' not in ai_expected:
                    data['expected_result'] = filled_expected

                # 测试用例名称/测试描述也优先走模板填充（避免 AI 改模板）
                data['case_name'] = filled_case_name
                data['test_desc'] = filled_test_desc
                results.append(
                    {
                        'row_index': row.row_index,
                        'case_name': data['case_name'],
                        'test_desc': data['test_desc'],
                        'input_condition': data['input_condition'],
                        'expected_result': data['expected_result'],
                    }
                )
                self.logger.info(f"用例设计-初始化：完成 row_index={row.row_index}")
            except Exception as e:
                err = {'row_index': getattr(row, 'row_index', None), 'error': str(e)}
                errors.append(err)
                self.logger.error(f"用例设计-初始化：失败 row_index={err['row_index']}, error={err['error']}")

        return results, errors

    async def case_design_common(
        self,
        case_name: str,
        test_desc: str,
        input_condition: str,
        expected_result: str,
        variables: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        payload = {
            'case_name': case_name or '',
            'test_desc': test_desc or '',
            'input_condition': input_condition or '',
            'expected_result': expected_result or '',
            'variables': variables or [],
        }

        self.logger.info('用例设计-通用功能：开始处理')
        ai_res = await self.ai_client.generate_common(payload)
        if not ai_res.get('success'):
            raise ValueError(ai_res.get('error') or 'AI调用失败')

        data = ai_res['data']
        cases = data.get('cases')
        if not isinstance(cases, list) or not cases:
            raise ValueError('AI返回 cases 为空')

        out: List[Dict[str, Any]] = []
        for it in cases:
            if not isinstance(it, dict):
                continue
            out.append(
                {
                    'case_name': str(it.get('case_name') or ''),
                    'test_desc': str(it.get('test_desc') or ''),
                    'input_condition': str(it.get('input_condition') or ''),
                    'expected_result': str(it.get('expected_result') or ''),
                }
            )

        if not out:
            raise ValueError('AI返回 cases 无有效数据')

        self.logger.info('用例设计-通用功能：完成 cases=%d', len(out))
        return out

    async def case_design_api_period(
        self,
        task_id: str,
        test_item_name: str,
        template_case_name: str,
        template_test_desc: str,
        template_input_condition: str,
        template_expected_result: str,
        user_code_snippet: str,
    ) -> List[Dict[str, Any]]:
        extract_path = self._get_latest_repo_extract_path(task_id)
        snippet_text = (user_code_snippet or '').replace('\r\n', '\n').replace('\r', '\n')
        snippet_lines = [ln for ln in snippet_text.split('\n') if ln.strip()]
        if not snippet_lines:
            raise ValueError('代码片段不能为空')

        self.logger.info(
            '用例设计-接口周期：开始定位片段 task_id=%s, extract_path=%s, snippet_non_empty_lines=%d',
            task_id,
            extract_path,
            len(snippet_lines),
        )

        loc = locate_snippet_in_repo(extract_path, user_code_snippet, logger=self.logger)
        if not loc:
            self.logger.error('用例设计-接口周期：代码片段定位失败')
            raise ValueError('未能在代码库中定位代码片段，请确认上传的代码库与粘贴的代码一致')

        func_name = guess_function_name_from_snippet(user_code_snippet)
        parsed_func, parsed_start, parsed_end, parsed_ctx = find_enclosing_function_in_file(loc.file_path, loc.start_line)
        if parsed_func:
            func_name = parsed_func

        parsed_ctx_numbered = ''
        if parsed_ctx and parsed_start:
            ctx_lines = (parsed_ctx or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
            numbered = []
            for i, ln in enumerate(ctx_lines):
                numbered.append(f'{parsed_start + i}: {ln}')
            parsed_ctx_numbered = '\n'.join(numbered)

        instrument_line, instrument_anchor = (0, '')
        if parsed_start and parsed_end:
            instrument_line, instrument_anchor = find_instrumentation_anchor_in_function(
                loc.file_path,
                parsed_start,
                parsed_end,
            )

        defaults = self._default_api_period_templates()
        t_case_name = (template_case_name or '').strip() or defaults['case_name']
        t_test_desc = (template_test_desc or '').strip() or defaults.get('test_desc', '')
        t_input = (template_input_condition or '').strip() or defaults['input_condition']
        t_expected = (template_expected_result or '').strip() or defaults['expected_result']

        # 两条用例：kk 固定为 接收/发送
        kk_values = ['接收', '发送']

        xx = self._extract_xx(test_item_name)
        yy = loc.file_path.split('\\')[-1]
        zz = func_name or ''
        mm = str(instrument_line or loc.start_line or '')

        base_case_name = self._apply_placeholders(t_case_name, xx=xx, yy=yy, zz=zz, mm=mm)
        base_test_desc = self._apply_placeholders(t_test_desc, xx=xx, yy=yy, zz=zz, mm=mm)
        base_input = self._apply_placeholders(t_input, xx=xx, yy=yy, zz=zz, mm=mm)
        base_expected = self._apply_placeholders(t_expected, xx=xx, yy=yy, zz=zz, mm=mm)

        payload = {
            'test_item_name': test_item_name or '',
            'code_file': yy,
            'func_name': zz,
            'line_start': loc.start_line,
            'line_end': loc.end_line,
            'enclosing_func_context_numbered': parsed_ctx_numbered,
            'instrument_line': instrument_line,
            'instrument_anchor': instrument_anchor,
            'user_code_snippet': snippet_text,
            'templates': {
                'case_name': base_case_name,
                'test_desc': base_test_desc,
                'input_condition': base_input,
                'expected_result': base_expected,
            },
        }

        self.logger.info('用例设计-接口周期：开始调用AI test_item_name=%s file=%s func=%s', test_item_name, yy, zz)
        ai_res = await self.ai_client.generate_api_period(payload)
        if not ai_res.get('success'):
            raise ValueError(ai_res.get('error') or 'AI调用失败')

        data = ai_res.get('data') or {}
        cases = data.get('cases')
        if not isinstance(cases, list) or len(cases) < 2:
            raise ValueError('AI返回cases数量不足(需要2条)')

        out: List[Dict[str, Any]] = []
        for i in range(2):
            it = cases[i] if i < len(cases) else {}
            if not isinstance(it, dict):
                it = {}

            kkv = kk_values[i]
            case_name_out = str(it.get('case_name') or '')
            test_desc_out = str(it.get('test_desc') or '')
            input_out = str(it.get('input_condition') or '')
            expected_out = str(it.get('expected_result') or '')

            case_name_out = self._replace_kk(case_name_out or base_case_name, kkv)
            test_desc_out = self._replace_kk(test_desc_out or base_test_desc, kkv)
            input_out = self._replace_kk(input_out or base_input, kkv)
            expected_out = expected_out or base_expected
            expected_out = self._replace_kk(expected_out, kkv)

            out.append(
                {
                    'case_name': case_name_out,
                    'test_desc': test_desc_out,
                    'input_condition': input_out,
                    'expected_result': expected_out,
                }
            )

        return out

    async def case_design_self_check_fission(
        self,
        case_name: str,
        test_desc: str,
        input_condition: str,
        expected_result: str,
        xx_values: List[str],
    ) -> List[Dict[str, Any]]:
        values = [str(v or '').strip() for v in (xx_values or []) if str(v or '').strip()]
        if not values:
            raise ValueError('xx_values 为空')

        self.logger.info('用例设计-自检测：fission 入参 case_name=%s', self._truncate_for_log(case_name))
        self.logger.info('用例设计-自检测：fission 入参 test_desc=%s', self._truncate_for_log(test_desc))
        self.logger.info('用例设计-自检测：fission 入参 input_condition=%s', self._truncate_for_log(input_condition))
        self.logger.info('用例设计-自检测：fission 入参 expected_result=%s', self._truncate_for_log(expected_result))
        self.logger.info('用例设计-自检测：fission 入参 xx_values=%s', self._truncate_for_log(values, limit=1200))

        payload = {
            'case_name': case_name or '',
            'test_desc': test_desc or '',
            'input_condition': input_condition or '',
            'expected_result': expected_result or '',
            'xx_values': values,
        }

        self.logger.info('用例设计-自检测：用例裂变开始 xx_values=%d', len(values))
        ai_res = await self.ai_client.generate_self_check_fission(payload)
        if not ai_res.get('success'):
            raise ValueError(ai_res.get('error') or 'AI调用失败')

        data = ai_res['data']
        cases = data.get('cases')
        if not isinstance(cases, list) or not cases:
            raise ValueError('AI返回 cases 为空')

        # 数量不匹配时按最小长度截断，避免前端越界
        n = min(len(values), len(cases))
        keep_tokens = ['yy', 'zz', 'mm', 'nn', 'kk']
        out: List[Dict[str, Any]] = []
        for i in range(n):
            it = cases[i]
            if not isinstance(it, dict):
                continue
            xx_val = values[i]

            case_name_out = str(it.get('case_name') or '')
            test_desc_out = str(it.get('test_desc') or '')
            input_out = str(it.get('input_condition') or '')
            expected_out = str(it.get('expected_result') or '')

            # 若 AI 跑偏（删步骤/删其它变量），回退到“仅替换xx”的安全结果
            fb_case = self._need_fallback_xx_only(case_name or '', case_name_out, keep_tokens)
            fb_desc = self._need_fallback_xx_only(test_desc or '', test_desc_out, keep_tokens)
            fb_input = self._need_fallback_xx_only(input_condition or '', input_out, keep_tokens)
            fb_exp = self._need_fallback_xx_only(expected_result or '', expected_out, keep_tokens)

            self.logger.info(
                '用例设计-自检测：fission fallback i=%d xx=%s case=%s desc=%s input=%s expected=%s',
                i,
                xx_val,
                fb_case,
                fb_desc,
                fb_input,
                fb_exp,
            )

            if fb_case:
                case_name_out = self._apply_xx_only(case_name or '', xx_val)
            if fb_desc:
                test_desc_out = self._apply_xx_only(test_desc or '', xx_val)
            if fb_input:
                input_out = self._apply_xx_only(input_condition or '', xx_val)
            if fb_exp:
                expected_out = self._apply_xx_only(expected_result or '', xx_val)

            out.append(
                {
                    'case_name': case_name_out,
                    'test_desc': test_desc_out,
                    'input_condition': input_out,
                    'expected_result': expected_out,
                }
            )

        if not out:
            raise ValueError('AI返回 cases 无有效数据')

        self.logger.info('用例设计-自检测：用例裂变完成 cases=%d', len(out))
        return out

    async def case_design_self_check_normalize_fault_categories(self, raw_text: str) -> str:
        payload = {
            'raw_text': raw_text or '',
        }

        self.logger.info('用例设计-自检测：故障类别格式转换开始')
        ai_res = await self.ai_client.generate_self_check_normalize(payload)
        if not ai_res.get('success'):
            raise ValueError(ai_res.get('error') or 'AI调用失败')

        data = ai_res['data']
        normalized = data.get('normalized')
        if not isinstance(normalized, str):
            raise ValueError('AI返回normalized类型错误')

        self.logger.info('用例设计-自检测：故障类别格式转换完成')
        return normalized

    async def case_design_self_check_write(
        self,
        task_id: str,
        entry_code_snippet: str,
        rows,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        # 目前“用例编写”逻辑与初始化一致：定位入口片段后，按模板生成 I/L/P/Q
        self.logger.info('用例设计-自检测：用例编写开始 rows=%d', len(rows) if rows else 0)
        return await self.case_design_init(task_id=task_id, entry_code_snippet=entry_code_snippet, rows=rows)

    async def case_design_api_exception(
        self,
        task_id: str,
        test_item_name: str,
        template_case_name: str,
        template_test_desc: str,
        template_input_condition: str,
        template_expected_result: str,
        user_code_snippet: str,
    ) -> List[Dict[str, Any]]:
        extract_path = self._get_latest_repo_extract_path(task_id)
        snippet_text = (user_code_snippet or '').replace('\r\n', '\n').replace('\r', '\n')
        snippet_lines = [ln for ln in snippet_text.split('\n') if ln.strip()]
        if not snippet_lines:
            raise ValueError('代码片段不能为空')

        self.logger.info(
            '用例设计-接口异常测试：开始定位片段 task_id=%s, extract_path=%s, snippet_non_empty_lines=%d',
            task_id,
            extract_path,
            len(snippet_lines),
        )

        loc = locate_snippet_in_repo(extract_path, user_code_snippet, logger=self.logger)
        if not loc:
            self.logger.error('用例设计-接口异常测试：代码片段定位失败')
            raise ValueError('未能在代码库中定位代码片段，请确认上传的代码库与粘贴的代码一致')

        func_name = guess_function_name_from_snippet(user_code_snippet)
        parsed_func, parsed_start, parsed_end, parsed_ctx = find_enclosing_function_in_file(loc.file_path, loc.start_line)
        if parsed_func:
            func_name = parsed_func

        parsed_ctx_numbered = ''
        if parsed_ctx and parsed_start:
            ctx_lines = (parsed_ctx or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
            numbered = []
            for i, ln in enumerate(ctx_lines):
                numbered.append(f'{parsed_start + i}: {ln}')
            parsed_ctx_numbered = '\n'.join(numbered)

        instrument_line, instrument_anchor = (0, '')
        if parsed_start and parsed_end:
            instrument_line, instrument_anchor = find_instrumentation_anchor_in_function(
                loc.file_path,
                parsed_start,
                parsed_end,
            )

        # 模板：若用户单元格为空则用默认模板
        defaults = self._default_api_exception_templates()
        t_case_name = (template_case_name or '').strip() or defaults['case_name']
        t_test_desc = (template_test_desc or '').strip() or defaults.get('test_desc', '')
        t_input = (template_input_condition or '').strip() or defaults['input_condition']
        t_expected = (template_expected_result or '').strip() or defaults['expected_result']

        # 两条用例：qq 固定为两种错误类型
        qq_values = ['校验位错误', '数据长度错误']

        # xx 从测试项名称中抽取
        xx = self._extract_xx(test_item_name)
        yy = loc.file_path.split('\\')[-1]
        zz = func_name or ''
        mm = str(instrument_line or loc.start_line or '')

        # 先做一次安全模板填充（只填 xx/yy/zz/mm/qq），避免 AI 跑偏把变量删掉
        base_case_name = self._apply_placeholders(t_case_name, xx=xx, yy=yy, zz=zz, mm=mm)
        base_test_desc = self._apply_placeholders(t_test_desc, xx=xx, yy=yy, zz=zz, mm=mm)
        base_input = self._apply_placeholders(t_input, xx=xx, yy=yy, zz=zz, mm=mm)
        base_expected = self._apply_placeholders(t_expected, xx=xx, yy=yy, zz=zz, mm=mm)

        payload = {
            'test_item_name': test_item_name or '',
            'code_file': yy,
            'func_name': zz,
            'line_start': loc.start_line,
            'line_end': loc.end_line,
            'enclosing_func_start': parsed_start,
            'enclosing_func_end': parsed_end,
            'enclosing_func_context_numbered': parsed_ctx_numbered,
            'instrument_line': instrument_line,
            'instrument_anchor': instrument_anchor,
            'user_code_snippet': snippet_text,
            'templates': {
                'case_name': base_case_name,
                'test_desc': base_test_desc,
                'input_condition': base_input,
                'expected_result': base_expected,
            },
        }

        self.logger.info('用例设计-接口异常测试：开始调用AI test_item_name=%s file=%s func=%s', test_item_name, yy, zz)
        ai_res = await self.ai_client.generate_api_exception(payload)
        if not ai_res.get('success'):
            raise ValueError(ai_res.get('error') or 'AI调用失败')

        data = ai_res.get('data') or {}
        cases = data.get('cases')
        if not isinstance(cases, list) or len(cases) < 2:
            raise ValueError('AI返回cases数量不足(需要2条)')

        out: List[Dict[str, Any]] = []
        for i in range(2):
            it = cases[i] if i < len(cases) else {}
            if not isinstance(it, dict):
                it = {}

            qqv = qq_values[i]
            case_name_out = str(it.get('case_name') or '')
            test_desc_out = str(it.get('test_desc') or '')
            input_out = str(it.get('input_condition') or '')
            expected_out = str(it.get('expected_result') or '')

            # 兜底：若AI没填 qq，至少强制替换为固定值（保持模板里双引号结构）
            case_name_out = self._replace_qq(case_name_out or base_case_name, qqv)
            test_desc_out = self._replace_qq(test_desc_out or base_test_desc, qqv)
            input_out = self._replace_qq(input_out or base_input, qqv)
            expected_out = expected_out or base_expected

            out.append(
                {
                    'case_name': case_name_out,
                    'test_desc': test_desc_out,
                    'input_condition': input_out,
                    'expected_result': expected_out,
                }
            )

        return out
