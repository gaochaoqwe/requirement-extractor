from __future__ import annotations

from typing import Any, Dict, List, Tuple

from pathlib import Path

from ....utils.logger import setup_session_logger
from ..test_case_design.case_design_ai_client import CaseDesignAIClient


class CaseFillService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = setup_session_logger(session_id)
        self.ai_client = CaseDesignAIClient(session_id)

    def _build_case_name_prompt(self, payload: Dict[str, Any]) -> str:
        test_item_name = str(payload.get('test_item_name') or '')
        test_desc = str(payload.get('test_desc') or '')
        input_condition = str(payload.get('input_condition') or '')
        expected_result = str(payload.get('expected_result') or '')
        neighbor_case_names = payload.get('neighbor_case_names')

        if not isinstance(neighbor_case_names, list):
            neighbor_case_names = []

        neighbor_text = '\n'.join([f'- {str(x)}' for x in neighbor_case_names if str(x).strip()])
        if not neighbor_text:
            neighbor_text = '(无)'

        return (
            '你是测试工程师助手。\n'
            '任务：根据测试项名称、测试描述、输入条件、预期结果，为测试用例表生成【测试用例名称】。\n'
            '你必须只输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n'
            '要求：\n'
            '1) 输出格式固定为：{"case_name": "..."}\n'
            '2) case_name 必须简洁、可读，并尽量使用短横线“-”拆分不同差异维度。\n'
            '3) 不要把多个差异维度合并成一个长短语；应优先提取对象、模式、状态变化、触发条件、预期现象等维度。\n'
            '4) 同一测试项下多个用例名称要明显区分侧重点，避免重复或过于相近。\n'
            '5) 参考“同一测试项附近的其他用例名称”，尽量保持风格一致但不要重复。\n'
            '6) case_name 的格式建议为：{test_item_name}-维度1-维度2-结果验证。\n'
            '7) 为保证 JSON 合法：你输出的 case_name 字符串中禁止出现英文双引号(")。当需要输出带引号的变量，请用《》表示；后端会自动转换为英文双引号。\n\n'
            f'测试项名称(G列)：{test_item_name}\n\n'
            f'测试描述(L列)：\n{test_desc}\n\n'
            f'输入条件(P列)：\n{input_condition}\n\n'
            f'测试结果/预期结果(Q列)：\n{expected_result}\n\n'
            '同测试项附近(最多5条)其他用例名称(I列，仅供参考)：\n'
            f'{neighbor_text}\n'
        )

    def _build_test_desc_prompt(self, payload: Dict[str, Any]) -> str:
        test_item_name = str(payload.get('test_item_name') or '')
        case_name = str(payload.get('case_name') or '')
        input_condition = str(payload.get('input_condition') or '')
        expected_result = str(payload.get('expected_result') or '')

        return (
            '你是测试工程师助手。\n'
            '任务：为测试用例表生成【测试描述（L列）】。\n'
            '你必须只输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n'
            '要求：\n'
            '1) 输出格式固定为：{"test_desc": "..."}\n'
            '2) test_desc 必须简洁，优先使用“测试XXX功能实现是否正确”或“测试XXX性能是否符合指标要求”的形式。\n'
            '3) XXX 需要根据输入条件和预期结果提炼出具体测试目标，不要写成泛泛而谈。\n'
            '4) 为保证 JSON 合法：你输出的 test_desc 字符串中禁止出现英文双引号(")。当需要输出带引号的变量，请用《》表示；后端会自动转换为英文双引号。\n\n'
            f'测试项名称(G列)：{test_item_name}\n\n'
            f'测试用例名称(I列)：{case_name}\n\n'
            f'输入条件(P列)：\n{input_condition}\n\n'
            f'测试结果/预期结果(Q列)：\n{expected_result}\n'
        )

    def _load_normal_mode_prompt(self) -> str:
        prompt_path = Path(__file__).resolve().parents[3] / 'prompts' / 'normal_mode_prompt.md'
        try:
            return prompt_path.read_text(encoding='utf-8')
        except Exception as e:
            self.logger.error('加载普通模式提示词失败: %s', e)
            return ''

    def _build_test_item_desc_method_prompt(self, payload: Dict[str, Any]) -> str:
        test_item_name = str(payload.get('test_item_name') or '')
        rows = payload.get('rows') if isinstance(payload.get('rows'), list) else []

        test_cases_parts = []
        for i, row in enumerate(rows, 1):
            input_condition = str(row.get('input_condition') or '')
            expected_result = str(row.get('expected_result') or '')
            test_desc = str(row.get('test_desc') or '')
            case_name = str(row.get('case_name') or '')
            test_cases_parts.append(
                f'用例{i}: 输入条件: {input_condition or "无"}, 预期结果: {expected_result or "无"}, 测试描述: {test_desc or "无"}, 用例名称: {case_name or "无"}'
            )
        test_cases = '\n'.join(test_cases_parts) if test_cases_parts else '(无)'

        template = self._load_normal_mode_prompt()
        if not template:
            return ''
        return template.format(test_item_name=test_item_name, test_cases=test_cases)

    async def smart_fill_case_name(self, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        total = len(rows)
        for idx, row in enumerate(rows, 1):
            try:
                row_index = int(row.get('row_index') or 0)
                prompt = self._build_case_name_prompt(row)
                self.logger.info('表单智能填充-用例名称 progress=%s/%s row=%s=\n%s', idx, total, row_index, prompt)

                ai_res = await self.ai_client._call_ai_with_retry_generic(prompt, required_keys=['case_name'])
                if not isinstance(ai_res, dict) or not ai_res.get('success'):
                    raise ValueError(str(ai_res.get('error') or 'AI返回失败'))

                data = ai_res.get('data') if isinstance(ai_res.get('data'), dict) else {}
                case_name = str(data.get('case_name') or '').strip()
                if not case_name:
                    raise ValueError('AI未返回case_name')

                results.append({'row_index': row_index, 'case_name': case_name, 'progress_current': idx, 'progress_total': total})
            except Exception as e:
                self.logger.exception('表单智能填充-用例名称 失败 row=%s', row.get('row_index'))
                errors.append({'row_index': row.get('row_index'), 'error': str(e), 'progress_current': idx, 'progress_total': total})

        return results, errors

    def _format_ai_field(self, value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            parts = []
            for key in sorted(value.keys(), key=lambda x: int(x) if str(x).isdigit() else 10**9):
                item = str(value.get(key) or '').strip()
                if item:
                    parts.append(item)
            return '\n'.join(parts).strip()
        if isinstance(value, list):
            parts = []
            for item in value:
                text = str(item or '').strip()
                if text:
                    parts.append(text)
            return '\n'.join(parts).strip()
        return str(value or '').strip()

    async def smart_fill_test_desc(self, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        total = len(rows)
        for idx, row in enumerate(rows, 1):
            try:
                row_index = int(row.get('row_index') or 0)
                prompt = self._build_test_desc_prompt(row)
                self.logger.info('表单智能填充-测试描述 progress=%s/%s row=%s=\n%s', idx, total, row_index, prompt)

                ai_res = await self.ai_client._call_ai_with_retry_generic(prompt, required_keys=['test_desc'])
                if not isinstance(ai_res, dict) or not ai_res.get('success'):
                    raise ValueError(str(ai_res.get('error') or 'AI返回失败'))

                data = ai_res.get('data') if isinstance(ai_res.get('data'), dict) else {}
                test_desc = str(data.get('test_desc') or '').strip()
                if not test_desc:
                    raise ValueError('AI未返回test_desc')

                results.append({'row_index': row_index, 'test_desc': test_desc, 'progress_current': idx, 'progress_total': total})
            except Exception as e:
                self.logger.exception('表单智能填充-测试描述 失败 row=%s', row.get('row_index'))
                errors.append({'row_index': row.get('row_index'), 'error': str(e), 'progress_current': idx, 'progress_total': total})

        return results, errors

    async def smart_fill_test_item_desc_method(self, rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        total = len(rows)
        if total == 0:
            return results, errors

        test_item_name = str(rows[0].get('test_item_name') or '').strip()
        prompt = self._build_test_item_desc_method_prompt({
            'test_item_name': test_item_name,
            'rows': rows,
        })
        self.logger.info('表单智能填充-测试项描述和测试方法 progress=1/%s test_item=%s=\n%s', total, test_item_name, prompt)

        try:
            ai_res = await self.ai_client._call_ai_with_retry_generic(prompt, required_keys=['test_item_desc', 'test_method'])
            self.logger.info('表单智能填充-测试项描述和测试方法 AI原始返回 test_item=%s => %s', test_item_name, ai_res)
            if not isinstance(ai_res, dict) or not ai_res.get('success'):
                raise ValueError(str(ai_res.get('error') or 'AI返回失败'))

            data = ai_res.get('data') if isinstance(ai_res.get('data'), dict) else {}
            self.logger.info('表单智能填充-测试项描述和测试方法 AI解析后data test_item=%s => %s', test_item_name, data)
            test_item_desc = self._format_ai_field(data.get('test_item_desc'))
            test_method = self._format_ai_field(data.get('test_method'))
            self.logger.info('表单智能填充-测试项描述和测试方法 准备回填 test_item=%s desc=%s method=%s', test_item_name, test_item_desc, test_method)
            if not test_item_desc or not test_method:
                raise ValueError('AI未返回test_item_desc或test_method')

            target_row = int(rows[0].get('row_index') or 0)
            results.append({
                'row_index': target_row,
                'test_item_desc': test_item_desc,
                'test_method': test_method,
                'progress_current': 1,
                'progress_total': 1,
            })
        except Exception as e:
            self.logger.exception('表单智能填充-测试项描述和测试方法 失败 test_item=%s', test_item_name)
            errors.append({'row_index': rows[0].get('row_index'), 'error': str(e), 'progress_current': 1, 'progress_total': 1})

        return results, errors
