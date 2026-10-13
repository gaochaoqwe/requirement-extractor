import json
import re
import asyncio
import os
import httpx
from pathlib import Path
from typing import Any, Dict, Optional

from ....utils.logger import get_session_logger


class CaseDesignAIClient:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logger = get_session_logger(session_id)
        self.config = self._load_config()
        self._init_client()

        self.request_timeout = 180.0
        self.max_retries = 3
        self.retry_delay = 1.5
        self.max_log_chars = 2000

    def _truncate_for_log(self, text: str) -> str:
        s = str(text or '')
        return s

    def _load_config(self) -> Dict[str, Any]:
        try:
            app_dir = next((p for p in Path(__file__).resolve().parents if p.name == 'app'), None)
            config_path = (app_dir / 'config.json') if app_dir else (Path(__file__).resolve().parents[6] / 'config.json')
            if not config_path.exists():
                self.logger.error(f'配置文件不存在: {config_path}')
                return {}
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f'加载配置文件失败: {e}')
            return {}

    def _init_client(self):
        openai_config = self.config.get('openai', {})
        self.api_key = openai_config.get('api_key')
        self.base_url = openai_config.get('base_url', 'https://api.openai.com/v1')
        self.model_name = openai_config.get('model_name', 'gpt-3.5-turbo')
        self.model_params = self.config.get('model_params', {})
        self._setup_no_proxy_for_domestic_ai(self.base_url)

    def _setup_no_proxy_for_domestic_ai(self, base_url: str):
        try:
            if not isinstance(base_url, str) or not base_url:
                return

            bypass_proxy_domains = [
                'aliyuncs.com',
                'dashscope.aliyuncs.com',
                'qianfan.baidubce.com',
                'baidubce.com',
                'volces.com',
                'volcengine.com',
                'tencentcloudapi.com',
                'deepseek.com',
                'moonshot.cn',
                'bigmodel.cn',
                'minimax.chat',
                'lingyiwanwu.com',
                'siliconflow.cn',
                'siliconflow.com',
                'hyperbolic.xyz',
            ]

            if not any(d in base_url for d in bypass_proxy_domains):
                return

            no_proxy_list = ','.join(bypass_proxy_domains)
            os.environ['NO_PROXY'] = no_proxy_list
            os.environ['no_proxy'] = no_proxy_list
        except Exception as e:
            self.logger.warning(f'设置NO_PROXY失败: {e}')

    def _sanitize_output_text(self, text: str) -> str:
        if not isinstance(text, str):
            return ''

        out = text
        # 去掉示例说明
        out = re.sub(r"[（(]\s*变量\s*/\s*硬件\s*/\s*中断\s*等\s*[）)]", "", out)
        out = re.sub(r"[（(][^）)]*(变量|硬件|中断)[^）)]*[）)]", "", out)

        # 将安全引用符号转为英文双引号
        out = re.sub(r"《\s*([^》]+?)\s*》", r'"\1"', out)
        out = re.sub(r"【\s*([^】]+?)\s*】", r'"\1"', out)
        out = out.replace('“', '"').replace('”', '"')

        out = re.sub(r"\s{2,}", " ", out).strip()
        return out

    def _parse_json_strict(self, content: str) -> Optional[Dict[str, Any]]:
        if not isinstance(content, str) or not content.strip():
            return None

        raw = content.strip()

        try:
            fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, flags=re.IGNORECASE)
            if fence:
                raw = fence.group(1).strip()
        except Exception:
            pass

        try:
            return json.loads(raw)
        except Exception:
            pass

        try:
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return None
            return json.loads(m.group(0))
        except Exception:
            return None

    def _build_prompt(
        self,
        test_item_name: str,
        template_case_name: str,
        template_test_desc: str,
        template_input_condition: str,
        template_expected_result: str,
        code_file: str,
        func_name: str,
        line_start: int,
        line_end: int,
        call_line: str,
        enclosing_func_start: int = 0,
        enclosing_func_end: int = 0,
        enclosing_func_context: str = '',
        enclosing_func_context_numbered: str = '',
        instrument_line: int = 0,
        instrument_anchor: str = '',
    ) -> str:
        return (
            '你是测试工程师助手。\n'
            '任务：根据【测试项名称】与【代码定位信息】在不改变模板步骤结构的前提下，生成测试用例内容。\n'
            '你需要：\n'
            '1) 替换模板中的变量 xx/yy/zz/mm 为真实信息（故障名称/文件名/函数名/行号）。\n'
            '2) 对“插装代码为：”后的占位说明，必须给出具体的 C 风格插桩示例代码：通过【强行设置某个变量的值】使某个 if 条件成立，从而让函数返回故障码(IR_FAULT_xxx)。\n'
            '3) 你必须从我提供的“带真实行号的源码上下文”中选择一个行号 N，作为插桩点：在第N行代码下方插入插桩代码，使得后续某个 if 条件成立并返回故障。\n'
            '4) 插桩行号 N 必须是源码上下文里出现过的行号，不能编造。\n'
            '5) 你输出的步骤1中必须明确出现“第N行”字样；并且“插装代码为：”后必须直接给出插桩代码（不要输出“插桩行号：...”）。\n'
            '6) 保持“步骤1/步骤2...”结构与固定句式，不能改写成一句话。\n'
            '你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n'
            '输出 JSON 格式如下：\n'
            '{"case_name": "...", "test_desc": "...", "input_condition": "...", "expected_result": "..."}\n\n'
            '约束：\n'
            '1) 必须填充文件名/函数名/行号；函数名不得为空。\n'
            '2) 模板中的示例说明（如："（变量/硬件/中断等）"）只是举例：输出时必须去掉这些示例说明，不能原样带出。\n'
            '3) 为了保证JSON合法：输出的 value 字符串中禁止出现英文双引号(\")。需要引用对象请使用《》或【】包裹，例如《RS422》。\n'
            '4) 输出必须是合法 JSON，值必须是字符串。\n\n'
            f'测试项名称：{test_item_name}\n\n'
            f'代码定位信息：文件={code_file}，函数={func_name}，行号={line_start}~{line_end}，调用语句={call_line}\n\n'
            f'所在函数范围(参考)：{enclosing_func_start}~{enclosing_func_end}\n\n'
            f'插桩参考(可选)：instrument_line_hint={instrument_line}\n'
            f'插桩锚点行(可选参考)：{instrument_anchor}\n\n'
            f'所在函数源码上下文(带真实行号，必须从这里选插桩行号)：\n{enclosing_func_context_numbered}\n\n'
            f'测试用例名称模板：{template_case_name}\n\n'
            f'测试描述模板：{template_test_desc}\n\n'
            f'输入条件模板：{template_input_condition}\n\n'
            f'预期结果模板：{template_expected_result}\n'
        )

    def _build_common_prompt(
        self,
        case_name: str,
        test_desc: str,
        input_condition: str,
        expected_result: str,
        variables: Any,
    ) -> str:
        vars_json = '[]'
        try:
            vars_json = json.dumps(variables or [], ensure_ascii=False)
        except Exception:
            vars_json = '[]'

        return (
            '你是测试工程师助手。\n'
            '任务：对用例设计的 4 列文本进行变量替换，并根据“裂变变量”做排列组合生成多条用例。\n'
            '输入中变量占位符通常位于英文双引号内，内容包含 xx/yy/zz/mm/nn/kk 之一，例如 "xx（随动/自动扫描等）"。\n'
            '你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n'
            '输出 JSON 格式如下：\n'
            '{"cases": [{"case_name":"...","test_desc":"...","input_condition":"...","expected_result":"..."}]}\n\n'
            '规则：\n'
            '1) 变量列表是一个数组，每项包含 key/values/fissile/one_to_one。key 是变量代号，只能是：xx/yy/zz/mm/nn/kk。values 为用户输入拆分后的值列表。\n'
            '2) 替换方式：当文本中出现类似 "xx..." / "yy..."（双引号内内容以 key 开头，且包含该 key）时，将双引号内整段内容替换为本次组合里该 key 选择的 value。\n'
            '3) 裂变规则：\n'
            '   a) fissile=true 的变量：参与排列组合（笛卡尔积）\n'
            '   b) one_to_one=true 的变量：不参与排列组合，而是按索引顺序一一对应配对。\n'
            '      - 所有 one_to_one=true 的变量必须有相同数量的 values\n'
            '      - 这些变量的值按索引位置配对使用：第0个值配第0个值，第1个值配第1个值，依此类推\n'
            '      - 重要：在生成用例时，one_to_one 变量的索引必须同步变化，不能固定使用某一个索引\n'
            '   c) fissile=false 且 one_to_one=false 的变量：若 values 有多个，只取第一个值。\n'
            '4) 用例生成逻辑（重要）：\n'
            '   - 第一步：对所有 fissile=true 的变量做笛卡尔积，得到 N 种裂变组合\n'
            '   - 第二步：对每一种裂变组合，遍历 one_to_one 变量的索引（0到M-1），生成 M 条用例\n'
            '   - 总用例数 = N × M（N=裂变组合数，M=one_to_one变量的值个数）\n'
            '   - 具体示例：\n'
            '     假设 zz 是裂变变量，values=[电视, 红外]（2个值）\n'
            '     假设 xx 是一对一变量，values=[随动, 自动扫描]（2个值）\n'
            '     假设 yy 是一对一变量，values=[手柄, 检测仪软件指令界面]（2个值）\n'
            '     则生成4条用例：\n'
            '     用例1: zz=电视, xx=随动（索引0）, yy=手柄（索引0）\n'
            '     用例2: zz=电视, xx=自动扫描（索引1）, yy=检测仪软件指令界面（索引1）\n'
            '     用例3: zz=红外, xx=随动（索引0）, yy=手柄（索引0）\n'
            '     用例4: zz=红外, xx=自动扫描（索引1）, yy=检测仪软件指令界面（索引1）\n'
            '     注意：每条用例中，所有 one_to_one 变量使用相同的索引！\n'
            '5) 你只能做变量替换与必要的文字清理，不要扩写、不要新增测试点/步骤/阈值。\n'
            '6) 为保证 JSON 合法：输出字符串中禁止出现英文双引号(\")，如需引用对象请用《》或【】包裹。\n\n'
            f'变量配置(JSON)：{vars_json}\n\n'
            f'I列(测试用例名称)：\n{case_name}\n\n'
            f'L列(测试描述)：\n{test_desc}\n\n'
            f'P列(输入条件)：\n{input_condition}\n\n'
            f'Q列(预期结果)：\n{expected_result}\n'
        )

    def _build_self_check_fission_prompt(
        self,
        case_name: str,
        test_desc: str,
        input_condition: str,
        expected_result: str,
        xx_values: Any,
    ) -> str:
        values_json = '[]'
        try:
            values_json = json.dumps(xx_values or [], ensure_ascii=False)
        except Exception:
            values_json = '[]'

        return (
            '你是测试工程师助手。\n'
            '任务：对用例设计的 4 列文本进行“故障类型裂变”。\n'
            '你只允许替换变量 xx（故障类型），并根据给定的 xx_values 生成多条用例。\n'
            '严禁改变模板的固定文字、严禁删除或合并步骤结构、严禁替换或删除其它变量占位符（yy/zz/mm/nn/kk 必须原样保留）。\n'
            '特别规则(必须遵守)：\n'
            '1) 当出现 "xx（...）" 或 "xx(...)" 这种带示例说明的写法时，必须将引号内整段替换为纯故障名（即 xx_values 中的值），括号及括号内内容必须去掉，不能保留。\n'
            '2) 例如："xx（主控板/随动控制板/图像处理板/手柄控制板等）" 替换为 "红外探测器故障"。\n'
            '你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n'
            '输出 JSON 格式如下：\n'
            '{"cases": [{"case_name":"...","test_desc":"...","input_condition":"...","expected_result":"..."}]}\n\n'
            '示例(输入 -> 输出)：\n'
            '输入P列(模板)：\n'
            '步骤1：代码插桩设置"xx（主控板/随动控制板/图像处理板/手柄控制板等）"故障，在"yy"文件"zz"函数"mm"行进行插桩，插装代码为：\n'
            '（此处为设置故障的插桩代码，比如说你将一个自检故障状态置为1）\n'
            '步骤2：软件正常运行，通过检测仪软件的状态监控界面观察软件上报"xx（主控板/随动控制板/图像处理板/手柄控制板等）"上电自检故障状态是否正确\n'
            '当 xx_values 中某条为 红外探测器故障 时，输出P列必须为：\n'
            '步骤1：代码插桩设置"红外探测器故障"故障，在"yy"文件"zz"函数"mm"行进行插桩，插装代码为：\n'
            '（此处为设置故障的插桩代码，比如说你将一个自检故障状态置为1）\n'
            '步骤2：软件正常运行，通过检测仪软件的状态监控界面观察软件上报"红外探测器故障"上电自检故障状态是否正确\n\n'
            '规则：\n'
            '1) 仅替换 xx：当文本中出现类似 "xx..."（双引号内内容以 xx 开头，且包含 xx）时，将双引号内整段内容替换为本次用例的故障类型值。\n'
            '2) 若存在裸的 xx（不在引号内），也要替换为故障类型值；但不要改动 yy/zz/mm/nn/kk。\n'
            '3) 输出 cases 条数必须等于 xx_values 的条数，顺序与 xx_values 一致。\n'
            '4) 如果输入包含“步骤1/步骤2/步骤3...”等结构，输出必须保留这些步骤标题与段落结构。\n'
            '5) 为保证 JSON 合法：输出字符串中禁止出现英文双引号(\")，如需引用对象请用《》或【】包裹。\n\n'
            f'xx_values(JSON)：{values_json}\n\n'
            f'I列(测试用例名称)：\n{case_name}\n\n'
            f'L列(测试描述)：\n{test_desc}\n\n'
            f'P列(输入条件)：\n{input_condition}\n\n'
            f'Q列(预期结果)：\n{expected_result}\n'
        )

    def _build_self_check_normalize_prompt(self, raw_text: str) -> str:
        return (
            '你是测试工程师助手。\n'
            '任务：将用户输入的故障类别原始文本，转换成规范的、用英文斜杠/分隔的列表格式。\n'
            '要求：\n'
            '1) 输出必须严格为 JSON，不能输出任何多余文字、不能使用 Markdown。\n'
            '2) JSON 格式：{"normalized": "..."}\n'
            '3) normalized 的内容必须是：多个故障类别用 / 分隔，例如：主控板故障/随动控制板故障/图像板故障\n'
            '4) 只输出故障类别本身，不要输出编号、解释、换行。\n'
            '5) 为保证 JSON 合法：输出 value 字符串中禁止出现英文双引号(\")，如需引用请用《》或【】包裹。\n\n'
            f'用户输入原文：\n{raw_text}\n'
        )

    def _build_api_exception_prompt(self, payload: Dict[str, Any]) -> str:
        test_item_name = str(payload.get('test_item_name') or '')
        code_file = str(payload.get('code_file') or '')
        func_name = str(payload.get('func_name') or '')
        line_start = int(payload.get('line_start') or 0)
        line_end = int(payload.get('line_end') or 0)
        ctx_numbered = str(payload.get('enclosing_func_context_numbered') or '')
        instrument_line = int(payload.get('instrument_line') or 0)
        instrument_anchor = str(payload.get('instrument_anchor') or '')
        user_code_snippet = str(payload.get('user_code_snippet') or '')
        templates = payload.get('templates') if isinstance(payload.get('templates'), dict) else {}
        t_case_name = str(templates.get('case_name') or '')
        t_test_desc = str(templates.get('test_desc') or '')
        t_input = str(templates.get('input_condition') or '')
        t_expected = str(templates.get('expected_result') or '')

        return (
            '你是测试工程师助手。\n'
            '任务：这是用例设计-接口测试-接口异常测试。你必须基于【模板】只做变量填充与插桩代码补全，不要扩写，不要新增步骤。\n'
            '本功能必须输出两条用例：\n'
            '用例1的 qq 固定为 校验位错误；用例2的 qq 固定为 数据长度错误。\n'
            '你需要根据我给你的【代码片段+定位信息】来确定 yy/zz/mm/nn 的内容：\n'
            'yy=文件名；zz=函数名；mm=插桩行号（必须是上下文里真实出现的行号）；nn=插桩代码（C风格）。\n'
            '要求：\n'
            '1) 必须保持模板中所有双引号结构存在（模板里有连续双引号时也要保留表达结构）。\n'
            '2) 为保证 JSON 合法：你输出的 value 字符串中禁止出现英文双引号(\")。\n'
            '   当需要输出带引号的变量（例如 "CAN"），请用《CAN》表示；后端会自动转换为英文双引号。\n'
            '你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n'
            '输出 JSON 格式如下：\n'
            '{"cases": [{"case_name": "...", "test_desc": "...", "input_condition": "...", "expected_result": "..."}, {"case_name": "...", "test_desc": "...", "input_condition": "...", "expected_result": "..."}]}\n\n'
            f'测试项名称：{test_item_name}\n\n'
            f'代码定位信息：文件={code_file}，函数={func_name}，行号={line_start}~{line_end}\n\n'
            f'插桩参考(可选)：instrument_line_hint={instrument_line}\n'
            f'插桩锚点行(可选参考)：{instrument_anchor}\n\n'
            f'用户粘贴代码片段：\n{user_code_snippet}\n\n'
            f'所在函数源码上下文(带真实行号，mm必须从这里选)：\n{ctx_numbered}\n\n'
            f'模板-测试用例名称(I列)：\n{t_case_name}\n\n'
            f'模板-测试描述(L列)：\n{t_test_desc}\n\n'
            f'模板-输入条件(P列)：\n{t_input}\n\n'
            f'模板-预期结果(Q列)：\n{t_expected}\n'
        )

    def _build_api_period_prompt(self, payload: Dict[str, Any]) -> str:
        test_item_name = str(payload.get('test_item_name') or '')
        code_file = str(payload.get('code_file') or '')
        func_name = str(payload.get('func_name') or '')
        line_start = int(payload.get('line_start') or 0)
        line_end = int(payload.get('line_end') or 0)
        ctx_numbered = str(payload.get('enclosing_func_context_numbered') or '')
        instrument_line = int(payload.get('instrument_line') or 0)
        instrument_anchor = str(payload.get('instrument_anchor') or '')
        user_code_snippet = str(payload.get('user_code_snippet') or '')
        templates = payload.get('templates') if isinstance(payload.get('templates'), dict) else {}
        t_case_name = str(templates.get('case_name') or '')
        t_test_desc = str(templates.get('test_desc') or '')
        t_input = str(templates.get('input_condition') or '')
        t_expected = str(templates.get('expected_result') or '')

        return (
            '你是测试工程师助手。\n'
            '任务：这是用例设计-接口测试-接口周期。你必须基于【模板】只做变量填充与插桩代码补全，不要扩写，不要新增步骤。\n'
            '本功能必须输出两条用例：用例1的 kk 固定为 接收；用例2的 kk 固定为 发送。\n'
            '你需要根据我给你的【代码片段+定位信息】来确定 xx/kk/yy/zz/mm/nn 的内容：\n'
            'xx/kk 需要根据测试项名称判断；yy=文件名；zz=函数名；mm=插桩行号（必须是上下文里真实出现的行号）；nn=插桩代码（C风格，用于打印时间戳）。\n'
            '特别要求：预期结果中的 cc/dd 是测试后填写的值，cc/dd 必须原样保留，不允许你填充或改写。\n'
            '要求：\n'
            '1) 必须保持模板中所有双引号结构存在（模板里有连续双引号时也要保留表达结构）。\n'
            '2) 为保证 JSON 合法：你输出的 value 字符串中禁止出现英文双引号(")。当需要输出带引号的变量，请用《》表示；后端会自动转换为英文双引号。\n'
            '3) 你必须严格输出 JSON，不能输出任何多余文字、不能使用 Markdown。\n'
            '输出 JSON 格式如下：\n'
            '{"cases": [{"case_name": "...", "test_desc": "...", "input_condition": "...", "expected_result": "..."}, {"case_name": "...", "test_desc": "...", "input_condition": "...", "expected_result": "..."}]}\n\n'
            f'测试项名称：{test_item_name}\n\n'
            f'代码定位信息：文件={code_file}，函数={func_name}，行号={line_start}~{line_end}\n\n'
            f'插桩参考(可选)：instrument_line_hint={instrument_line}\n'
            f'插桩锚点行(可选参考)：{instrument_anchor}\n\n'
            f'用户粘贴代码片段：\n{user_code_snippet}\n\n'
            f'所在函数源码上下文(带真实行号，mm必须从这里选)：\n{ctx_numbered}\n\n'
            f'模板-测试用例名称(I列)：\n{t_case_name}\n\n'
            f'模板-测试描述(L列)：\n{t_test_desc}\n\n'
            f'模板-输入条件(P列)：\n{t_input}\n\n'
            f'模板-预期结果(Q列)：\n{t_expected}\n'
        )

    async def generate_init(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(
            payload.get('test_item_name', ''),
            payload.get('template_case_name', ''),
            payload.get('template_test_desc', ''),
            payload.get('template_input_condition', ''),
            payload.get('template_expected_result', ''),
            payload.get('code_file', ''),
            payload.get('func_name', ''),
            int(payload.get('line_start') or 0),
            int(payload.get('line_end') or 0),
            payload.get('call_line', ''),
            int(payload.get('enclosing_func_start') or 0),
            int(payload.get('enclosing_func_end') or 0),
            payload.get('enclosing_func_context', '') or '',
            payload.get('enclosing_func_context_numbered', '') or '',
            int(payload.get('instrument_line') or 0),
            payload.get('instrument_anchor', '') or '',
        )
        return await self._call_ai_with_retry(prompt)

    async def generate_common(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_common_prompt(
            payload.get('case_name', ''),
            payload.get('test_desc', ''),
            payload.get('input_condition', ''),
            payload.get('expected_result', ''),
            payload.get('variables', []) or [],
        )
        return await self._call_ai_with_retry(prompt)

    async def generate_self_check_fission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_self_check_fission_prompt(
            payload.get('case_name', ''),
            payload.get('test_desc', ''),
            payload.get('input_condition', ''),
            payload.get('expected_result', ''),
            payload.get('xx_values', []) or [],
        )
        self.logger.info('用例设计-自检测：用例裂变 prompt=\n%s', self._truncate_for_log(prompt))
        res = await self._call_ai_with_retry(prompt)
        try:
            raw = res.get('raw') if isinstance(res, dict) else None
            if raw:
                self.logger.info('用例设计-自检测：用例裂变 raw_response=\n%s', self._truncate_for_log(raw))
        except Exception:
            pass
        return res

    async def generate_api_period(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_api_period_prompt(payload)
        self.logger.info('用例设计-接口周期 prompt=\n%s', self._truncate_for_log(prompt))
        res = await self._call_ai_with_retry(
            prompt,
            case_item_keys=['case_name', 'test_desc', 'input_condition', 'expected_result'],
        )
        try:
            raw = res.get('raw') if isinstance(res, dict) else None
            if raw:
                self.logger.info('用例设计-接口周期 raw_response=\n%s', self._truncate_for_log(raw))
        except Exception:
            pass
        return res

    async def generate_self_check_normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_self_check_normalize_prompt(payload.get('raw_text', ''))
        return await self._call_ai_with_retry_generic(prompt, required_keys=['normalized'])

    async def generate_api_exception(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_api_exception_prompt(payload)
        self.logger.info('用例设计-接口异常测试 prompt=\n%s', self._truncate_for_log(prompt))
        res = await self._call_ai_with_retry(
            prompt,
            case_item_keys=['case_name', 'test_desc', 'input_condition', 'expected_result'],
        )
        try:
            raw = res.get('raw') if isinstance(res, dict) else None
            if raw:
                self.logger.info('用例设计-接口异常测试 raw_response=\n%s', self._truncate_for_log(raw))
        except Exception:
            pass
        return res

    async def _call_ai_with_retry_generic(self, prompt: str, required_keys: Optional[list] = None) -> Dict[str, Any]:
        last_error: Optional[str] = None
        required_keys = required_keys or []

        for attempt in range(self.max_retries):
            try:
                content = await self._call_ai(prompt)
                self.logger.info('AI原始返回 raw_response=\n%s', self._truncate_for_log(content))
                parsed = self._parse_json_strict(content)
                if not parsed:
                    snippet = (content or '')
                    self.logger.warning(f'AI原始返回内容(解析失败): {snippet}')
                    raise ValueError('AI返回不是合法JSON')

                for k in required_keys:
                    if k not in parsed:
                        raise ValueError(f'AI返回JSON缺少字段: {k}')

                data: Dict[str, Any] = {}
                for k in required_keys:
                    v = parsed.get(k)
                    if isinstance(v, str):
                        data[k] = self._sanitize_output_text(v)
                    elif isinstance(v, (dict, list)):
                        data[k] = v
                    else:
                        raise ValueError(f'AI返回JSON字段类型错误: {k}')

                return {'success': True, 'data': data, 'raw': content}
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f'AI调用失败 attempt={attempt + 1}/{self.max_retries}: {last_error}')
                await asyncio.sleep(self.retry_delay)

        return {'success': False, 'error': last_error or 'AI调用失败'}

    async def _call_ai_with_retry(self, prompt: str, case_item_keys: Optional[list] = None) -> Dict[str, Any]:
        last_error: Optional[str] = None

        # init/common/self_check_fission 默认需要 4 字段；接口异常测试会传入 3 字段
        item_keys = case_item_keys or ['case_name', 'test_desc', 'input_condition', 'expected_result']

        for attempt in range(self.max_retries):
            try:
                content = await self._call_ai(prompt)
                self.logger.info('AI原始返回 raw_response=\n%s', self._truncate_for_log(content))
                parsed = self._parse_json_strict(content)
                if not parsed:
                    snippet = (content or '')
                    if len(snippet) > self.max_log_chars:
                        snippet = snippet[: self.max_log_chars] + '...<truncated>'
                    self.logger.warning(f'AI原始返回内容(解析失败，已截断): {snippet}')
                    raise ValueError('AI返回不是合法JSON')

                # init: 直接四字段
                keys = ['case_name', 'test_desc', 'input_condition', 'expected_result']
                if all(isinstance(parsed.get(k), (str, dict, list)) for k in keys):
                    data: Dict[str, Any] = {}
                    for k in keys:
                        v = parsed.get(k, '')
                        if isinstance(v, str):
                            data[k] = self._sanitize_output_text(v)
                        else:
                            data[k] = v
                    return {'success': True, 'data': data, 'raw': content}

                # common: cases 数组
                cases = parsed.get('cases')
                if isinstance(cases, list) and cases:
                    out_cases = []
                    for it in cases:
                        if not isinstance(it, dict):
                            continue
                        if not all(isinstance(it.get(k), str) for k in item_keys):
                            continue
                        out_cases.append({k: self._sanitize_output_text(it.get(k, '')) for k in item_keys})
                    if not out_cases:
                        self.logger.warning('AI原始返回内容(cases结构不合法): %s', self._truncate_for_log(content))
                        raise ValueError('AI返回cases结构不合法')
                    return {'success': True, 'data': {'cases': out_cases}, 'raw': content}

                self.logger.warning('AI原始返回内容(字段/类型错误，已截断): %s', self._truncate_for_log(content))
                raise ValueError('AI返回JSON缺少字段或类型错误')
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f'AI调用失败 attempt={attempt + 1}/{self.max_retries}: {last_error}')
                await asyncio.sleep(self.retry_delay)

        return {'success': False, 'error': last_error or 'AI调用失败'}

    async def _call_ai(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError('缺少 openai.api_key 配置')

        url = self.base_url.rstrip('/') + '/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        body = {
            'model': self.model_name,
            'messages': [
                {'role': 'system', 'content': '你是一个严谨的测试工程师助手。'},
                {'role': 'user', 'content': prompt},
            ],
        }
        body.update(self.model_params or {})

        timeout = httpx.Timeout(self.request_timeout)
        async with httpx.AsyncClient(timeout=timeout, trust_env=True) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            return data['choices'][0]['message']['content']
