import requests
import json
# 配置相关参数
try:
    from ...utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
except ImportError:
    try:
        from ....utils.config_utils.config import OLLAMA_HOST, OLLAMA_MODEL
    except ImportError:
        # 如果没有配置文件，使用默认值
        OLLAMA_HOST = "http://localhost:11434"
        OLLAMA_MODEL = "llama2"

def _clean_json_string(json_str):
    """
    清理JSON字符串，处理常见的格式问题
    """
    if not json_str:
        return ""
    
    try:
        # 1. Handle <think>...</think> or leading </think>
        last_think_end_tag_index = json_str.rfind("</think>")
        if last_think_end_tag_index != -1:
            json_str = json_str[last_think_end_tag_index + len("</think>"):]
            json_str = json_str.lstrip()
        
        # 2. 移除 BOM 标记
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
        
        # 3. 处理 Markdown 代码块标记
        json_str = ''.join(
            char for char in json_str 
            if char == '\n' or char == '\t' or not (0 <= ord(char) < 32 or ord(char) == 127)
        )
        
        # 4. 提取JSON内容 - 改进版本，处理完整的JSON对象
        if "```json" in json_str:
            start_marker = "```json"
            end_marker = "```"
            start_pos = json_str.find(start_marker) + len(start_marker)
            end_pos = json_str.find(end_marker, start_pos)
            if end_pos > start_pos:
                json_str = json_str[start_pos:end_pos].strip()
        elif "```" in json_str:
            # 处理没有json标记的代码块
            lines = json_str.split('\n')
            in_code_block = False
            extracted_lines = []
            for line in lines:
                if line.strip() == "```":
                    if in_code_block:
                        break
                    else:
                        in_code_block = True
                        continue
                if in_code_block:
                    extracted_lines.append(line)
            if extracted_lines:
                json_str = '\n'.join(extracted_lines)
        
        # 5. 查找JSON对象的开始和结束
        start_brace = json_str.find('[')
        if start_brace == -1:
            start_brace = json_str.find('{')
        
        if start_brace != -1:
            # 从找到的开始位置提取
            json_str = json_str[start_brace:]
            
            # 寻找匹配的结束位置
            brace_count = 0
            bracket_count = 0
            for i, char in enumerate(json_str):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                
                if (brace_count == 0 and json_str[0] == '{') or (bracket_count == 0 and json_str[0] == '['):
                    json_str = json_str[:i+1]
                    break
        
        # 6. 常见的格式修复
        json_str = json_str.strip()
        json_str = json_str.replace('\n', ' ')
        json_str = json_str.replace('\t', ' ')
        
        # 7. 移除多余的逗号
        json_str = json_str.replace(',}', '}')
        json_str = json_str.replace(',]', ']')
        
        return json_str
        
    except Exception as e:
        print(f"JSON清理过程中发生错误: {e}")
        return json_str

# 根据软件需求描述，生成测试相对应的测试内容和测试方法。
# 函数输入：
#     1）xuqiumiaoshu：软件需求描述。
#     2）test_content: 测试内容。
#     3）ceshileixing: 测试类型。
# 函数输出：
#     1）xuqiumiaoshu：测试相对应的技术描述。
#     2）test_content: 测试内容。
def AI_generate_yongli(xuqiumiaoshu,test_content,ceshileixing,jianceyi_flag):
    # 构建请求参数
    #  'system':系统预设提示，指导模型生成符合要求的 JSON 数据
    #  'prompt': 提取测试项的提示，指导模型生成符合要求的 JSON 数据
    #  'model': 模型名称
    #  'stream': 是否流式生成
    # 有检测仪提示词设计*********************************************************************************************
    # ************************************************************************************************1、边界测试提示词模板*****************************************************************************************************************
    if jianceyi_flag=='有检测仪':
        yongli_tishici_bianjie="详细列出测试用例的具体步骤。例如：步骤1：软件正常运行，通过检测仪发送登陆指令。\n步骤2：通过检测仪状态监控观察软件是否跳转到登陆界面。\n步骤3：通过检测仪输入长度为20的登陆密码。\n步骤4：通过检测仪状态监控观察软件是否实现密码登录。"
        yonglibuzhou_tishici_bianjie="对应每个步骤的预期结果，例如：完成步骤2：检测仪状态监控显示软件跳转到登陆界面\n完成步骤4：检测仪状态监控显示软件实现密码登录。"
        # 1） 专门针对边界测试的提示词模板
        if '边界' in ceshileixing:
            if len(test_content) > 3:  # 如果测试内容大于3，则进行提示词的筛选
                system_prompt = (
                    "你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取边界测试用例。你的任务是根据用户提供的软件需求描述，生成详细的边界测试用例，每个测试用例必须包含以下四个部分："
                    "测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果，注意测试用例中测试激励的输入和被测软件状态的监控都是通过检测仪实现的。输出格式必须严格遵循JSON字符串数据格式，具体格式如下："
                    f'[{{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", 'f'"method": "{yongli_tishici_bianjie}", 'f'"expect": "{yonglibuzhou_tishici_bianjie}"}}]')
                params = {
                    'system': system_prompt,
                    'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试用例。测试类型为：{ceshileixing}，软件需求描述为：{xuqiumiaoshu}。请确保生成的测试用例覆盖所有边界条件，包括正常边界值、异常边界值和特殊边界值。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
            # 2、进行提示词的筛选： 结合测试内容。采用检索增强的方式进行测试用例生成。
            else:
                system_prompt = (
                    "你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取边界测试用例。你的任务是根据用户提供的软件需求描述，生成详细的边界测试用例，每个测试用例必须包含以下四个部分："
                    "测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果，注意测试用例中测试激励的输入和被测软件状态的监控都是通过检测仪实现的。输出格式必须严格遵循JSON字符串数据格式，具体格式如下："
                    f'[{{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", 'f'"method": "{yongli_tishici_bianjie}", 'f'"expect": "{yonglibuzhou_tishici_bianjie}"}}]')
                params = {
                    'system': system_prompt,
                    'prompt': f'请根据边界测试的要求，分析以下测试需求，并根据要求生成边界测试用例。测试类型为：{ceshileixing}，测试内容为：{test_content}，软件需求描述为：{xuqiumiaoshu}。请确保生成的测试用例覆盖所有边界条件，包括正常边界值、异常边界值和特殊边界值。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
            # ***********************************************************************************************2、性能测试提示词模板******************************************************************************************************************
            # 2） 专门针对功能测试的提示词模板
        elif '性能' in ceshileixing:
            yongli_tishici_xingneng= "详细列出测试用例的具体步骤。例如：步骤1：软件正常启动，通过检测仪发送登陆指令。\n步骤2：观察检测仪的状态显示界面,通过计时器记录软件跳转到登录界面的时间。"
            yonglibuzhou_tishici_xingneng="对应每个步骤的预期结果，例如：完成步骤2：计时器显示检测仪状态监控界面跳转到登录界面时间为10秒。\n"
            if len(test_content) > 3:  # 如果测试内容大于3，则进行提示词的筛选
                system_prompt = (
                    "你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取边界测试用例。你的任务是根据用户提供的软件需求描述，生成详细的边界测试用例，每个测试用例必须包含以下四个部分："
                    "测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果，注意测试用例中测试激励的输入和被测软件状态的监控都是通过检测仪实现的。输出格式必须严格遵循JSON字符串数据格式，具体格式如下："
                    f'[{{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", 'f'"method": "{yongli_tishici_xingneng}", 'f'"expect": "{yonglibuzhou_tishici_xingneng}"}}]')
                params = {
                    'system': system_prompt,
                    'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成性能测试用例。测试类型为：{ceshileixing}，软件需求描述为：{xuqiumiaoshu}。请确保生成的测试用例覆盖所有性能场景，包括正常负载、高负载和边界负载。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
            # 2、进行提示词的筛选： 结合测试内容。采用检索增强的方式进行测试用例生成。
            else:
                system_prompt = (
                    "你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取边界测试用例。你的任务是根据用户提供的软件需求描述，生成详细的边界测试用例，每个测试用例必须包含以下四个部分："
                    "测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果，注意测试用例中测试激励的输入和被测软件状态的监控都是通过检测仪实现的。输出格式必须严格遵循JSON字符串数据格式，具体格式如下："
                    f'[{{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", 'f'"method": "{yongli_tishici_xingneng}", 'f'"expect": "{yonglibuzhou_tishici_xingneng}"}}]')
                params = {
                    'system': system_prompt,
                    'prompt': f'请根据测试类型，分析以下测试需求，并根据要求生成性能测试用例。测试类型为：{ceshileixing}，测试内容为：{test_content}，软件需求描述为：{xuqiumiaoshu}。请确保生成的测试用例覆盖所有性能场景，包括正常负载、高负载和边界负载。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
        # 无检测仪提示词设计*********************************************************************************************************************************************
        # ***********************************************************************************************3、功能测试提示词模板******************************************************************************************************************
        # 3） 专门针对功能测试的提示词模板
        else:
            yongli_tishici_gongneng= "详细列出测试用例的具体步骤。例如：步骤1：软件正常运行，通过检测仪发送登陆指令。\n步骤2：通过检测仪状态监控观察软件是否跳转到登陆界面。\n步骤3：通过检测仪输入长度为20的登陆密码。\n步骤4：通过检测仪状态监控观察软件是否实现密码登录。"
            yonglibuzhou_tishici_gongneng = "对应每个步骤的预期结果，例如：完成步骤2：检测仪状态监控显示软件跳转到登陆界面\n完成步骤4：检测仪状态监控显示软件实现密码登录。"
            if len(test_content) > 3:  # 如果测试内容大于3，则进行提示词的筛选
                system_prompt = (
                    "你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取边界测试用例。你的任务是根据用户提供的软件需求描述，生成详细的边界测试用例，每个测试用例必须包含以下四个部分："
                    "测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果，注意测试用例中测试激励的输入和被测软件状态的监控都是通过检测仪实现的。输出格式必须严格遵循JSON字符串数据格式，具体格式如下："
                    f'[{{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", 'f'"method": "{yongli_tishici_gongneng}", 'f'"expect": "{yonglibuzhou_tishici_gongneng}"}}]')
                params = {
                    'system': system_prompt,
                    'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试用例，要求至少包含一个异常测试用例，对异常场景下的软件功能进行测试。测试类型为：{ceshileixing}，软件需求描述为：{xuqiumiaoshu}。生成的测试用例应覆盖所有关键功能点，确保每个测试用例都包含详细的步骤和预期结果。输出结果必须为结构化数据，且符合上述JSON格式。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
            # 2、进行提示词的筛选： 结合测试内容。采用检索增强的方式进行测试用例生成。
            else:
                system_prompt = (
                    "你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取边界测试用例。你的任务是根据用户提供的软件需求描述，生成详细的边界测试用例，每个测试用例必须包含以下四个部分："
                    "测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果，注意测试用例中测试激励的输入和被测软件状态的监控都是通过检测仪实现的。输出格式必须严格遵循JSON字符串数据格式，具体格式如下："
                    f'[{{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", 'f'"method": "{yongli_tishici_gongneng}", 'f'"expect": "{yonglibuzhou_tishici_gongneng}"}}]')
                params = {
                    'system': system_prompt,
                    'prompt': f'请根据测试类型以及测试内容，分析以下测试需求，并根据要求生成测试用例。测试类型为：{ceshileixing}，测试内容为：{test_content}，软件需求描述为：{xuqiumiaoshu}。生成的测试用例应覆盖所有关键功能点，确保每个测试用例都包含详细的步骤和预期结果。输出结果必须为结构化数据，且符合上述JSON格式。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
    #**************************************************************************************************************无检测仪*************************************************************************************************
    else:
        # 1） 专门针对边界测试的提示词模板
        if '边界' in ceshileixing:
            if len(test_content) > 3:  # 如果测试内容大于3，则进行提示词的筛选
                params = {
                    'system': '你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取边界测试用例。你的任务是根据用户提供的软件需求描述，生成详细的边界测试用例，每个测试用例必须包含以下四个部分：测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                              '[{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", '
                              '"method": "详细列出测试用例的具体步骤，例如：步骤1：打开应用。\n步骤2：输入用户名和密码。\n步骤3：点击登录按钮。", '
                              '"expect": "对应每个步骤的预期结果，例如：完成步骤1：应用成功打开。\n完成步骤2：用户名和密码输入框显示正常。\n步骤3：成功登录并跳转到主页。"}]',
                    'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试用例。测试类型为：{ceshileixing}，软件需求描述为：{xuqiumiaoshu}。请确保生成的测试用例覆盖所有边界条件，包括正常边界值、异常边界值和特殊边界值。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
            # 2、进行提示词的筛选： 结合测试内容。采用检索增强的方式进行测试用例生成。
            else:
                params = {
                    'system': '你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取边界测试用例。你的任务是根据用户提供的软件需求描述，生成详细的边界测试用例，每个测试用例必须包含以下四个部分：测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                              '[{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", '
                              '"method": "详细列出测试用例的具体步骤，例如：步骤1：打开应用。\n步骤2：输入用户名和密码。\n步骤3：点击登录按钮。", '
                              '"expect": "对应每个步骤的预期结果，例如：完成步骤1：应用成功打开。\n完成步骤2：用户名和密码输入框显示正常。\n完成步骤3：成功登录并跳转到主页。"}]',
                    'prompt': f'请根据边界测试的要求，分析以下测试需求，并根据要求生成边界测试用例。测试类型为：{ceshileixing}，测试内容为：{test_content}，软件需求描述为：{xuqiumiaoshu}。请确保生成的测试用例覆盖所有边界条件，包括正常边界值、异常边界值和特殊边界值。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
            # ***********************************************************************************************2、性能测试提示词模板******************************************************************************************************************
            # 2） 专门针对功能测试的提示词模板
        elif '性能' in ceshileixing:
            if len(test_content) > 3:  # 如果测试内容大于3，则进行提示词的筛选
                params = {
                    'system': '你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取性能测试用例。你的任务是根据用户提供的软件需求描述，生成详细的性能测试用例，每个测试用例必须包含以下四个部分：测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                              '[{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", '
                              '"method": "详细列出测试用例的具体步骤，例如：步骤1：启动性能测试工具。\n步骤2：设置并发用户数为100。\n步骤3：发送请求并记录响应时间。", '
                              '"expect": "对应每个步骤的预期结果，例如：完成步骤1：性能测试工具成功启动。\n完成步骤2：并发用户数设置为100。\n完成步骤3：响应时间小于1秒。"}]',
                    'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成性能测试用例。测试类型为：{ceshileixing}，软件需求描述为：{xuqiumiaoshu}。请确保生成的测试用例覆盖所有性能场景，包括正常负载、高负载和边界负载。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
            # 2、进行提示词的筛选： 结合测试内容。采用检索增强的方式进行测试用例生成。
            else:
                params = {
                    'system': '你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取性能测试用例。你的任务是根据用户提供的软件需求描述，生成详细的性能测试用例，每个测试用例必须包含以下四个部分：测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                              '[{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", '
                              '"method": "详细列出测试用例的具体步骤，例如：步骤1：启动性能测试工具。\n步骤2：设置并发用户数为100。\n步骤3：发送请求并记录响应时间。", '
                              '"expect": "对应每个步骤的预期结果，例如：完成步骤1：性能测试工具成功启动。\n完成步骤2：并发用户数设置为100。\n完成步骤3：响应时间小于1秒。"}]',
                    'prompt': f'请根据测试类型，分析以下测试需求，并根据要求生成性能测试用例。测试类型为：{ceshileixing}，测试内容为：{test_content}，软件需求描述为：{xuqiumiaoshu}。请确保生成的测试用例覆盖所有性能场景，包括正常负载、高负载和边界负载。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }

        # ***********************************************************************************************3、功能测试提示词模板******************************************************************************************************************
        # 3） 专门针对功能测试的提示词模板
        else:
            if len(test_content) > 3:  # 如果测试内容大于3，则进行提示词的筛选
                params = {
                    'system': '你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取测试用例。你的任务是根据用户提供的软件需求描述，生成详细的测试用例，每个测试用例必须包含以下四个部分：测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                              '[{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", '
                              '"method": "详细列出测试用例的具体步骤，例如：步骤1：打开应用。\n步骤2：输入用户名和密码。\n步骤3：点击登录按钮。", '
                              '"expect": "对应每个步骤的预期结果，例如：完成步骤1：应用成功打开。\n完成步骤2：用户名和密码输入框显示正常。\n步骤3：成功登录并跳转到主页。"}]',
                    'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试用例，要求至少包含一个异常测试用例，对异常场景下的软件功能进行测试。测试类型为：{ceshileixing}，软件需求描述为：{xuqiumiaoshu}。生成的测试用例应覆盖所有关键功能点，确保每个测试用例都包含详细的步骤和预期结果。输出结果必须为结构化数据，且符合上述JSON格式。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
            # 2、进行提示词的筛选： 结合测试内容。采用检索增强的方式进行测试用例生成。
            else:
                params = {
                    'system': '你是一个经验丰富的软件测试工程师，专注于从软件需求中精准提取测试用例。你的任务是根据用户提供的软件需求描述，生成详细的测试用例，每个测试用例必须包含以下四个部分：测试用例名称、测试用例描述、测试用例具体的步骤、测试用例每个步骤对应的预期结果。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                              '[{"item": "测试用例名称", "context": "详细描述测试用例的目的和背景", '
                              '"method": "详细列出测试用例的具体步骤，例如：步骤1：打开应用。\n步骤2：输入用户名和密码。\n步骤3：点击登录按钮。", '
                              '"expect": "对应每个步骤的预期结果，例如：完成步骤1：应用成功打开。\n完成步骤2：用户名和密码输入框显示正常。\n完成步骤3：成功登录并跳转到主页。"}]',
                    'prompt': f'请根据测试类型以及测试内容，分析以下测试需求，并根据要求生成测试用例。测试类型为：{ceshileixing}，测试内容为：{test_content}，软件需求描述为：{xuqiumiaoshu}。生成的测试用例应覆盖所有关键功能点，确保每个测试用例都包含详细的步骤和预期结果。输出结果必须为结构化数据，且符合上述JSON格式。/nothink',
                    'model': OLLAMA_MODEL,
                    'stream': False,
                }
   # ***********************************************************************************************************基于提示词的测试用例生成*************************************************************************************************
    # 开始进行测试用例构建。
    max_loop = 5  # 设置最大重试次数为 5 次
    data = None  # 初始化返回数据为 None
    while max_loop > 0 and not data:  # 当重试次数大于 0 且未获取到数据时，循环继续
        try:
            res = requests.post(url=f'{OLLAMA_HOST}/api/generate', json=params,verify=False)
            # 发送 POST 请求到指定的 URL，参数为 `params`
            # 注意：`unl` 应改为 `url`，否则会报错
            response = res.json()["response"]
            # 从响应中提取 "response" 字段的值
            
            # 使用改进的JSON清理方法
            cleaned_response = _clean_json_string(response)
            data = json.loads(cleaned_response)
            print(data)
            # 将提取的 JSON 字符串解析为 Python 对象
        except Exception as e:
            max_loop = max_loop - 1        # 当发生异常时，减少重试次数
            print(e)
            print(' Api分析函数错误（测试用例生成）!!!!!!')
    return data                            # 返回解析后的 JSON 数据

# 函数功能：该函数的主要功能是根据软件的需求描述、对应的测试内容和测试方法，调用AI模型,生成软件的测试用例
# 函数输入：
    #测试项名称：ceshixiang_name
    #需求描述:  requirement_description
    #测试内容:  test_content
    #测试类型： ceshileixing
# 函数输出：
    # yingli_fenxi_flag:  用于判断AI分析是否成功。
    # ceshiyongli:       [['测试用例名称',‘测试用例描述',具体的测试步骤','合着盈利对应的预期结果']]
# 输出具体要求 ：
#     1）测试用例名称：名字要简短易懂的。
#     2）测试用例描述：主要用于描述该用例用来测试什么内容。
#     3）具体的测试步骤：需要给出详细的执行步骤。例：步骤1：。步骤2：。步骤3：。
#     4）预期结果：需要给出测试步骤对应的测试结果。例：例：完成步骤1：。完成步骤2：。完成步骤3：。
def generate_test_yongli(ceshixiang_name,requirement_description,test_content,ceshileixing,jianceyi_flag):
    yingli_fenxi_flag = False
    ceshiyongli = []             # 用于存储测试用例,主要包括： 测试用例名称、测试用例描述、测试步骤、预期结果
    try:
        # 调用 AI_generate_yongli 函数生成测试用例
        ai_data = AI_generate_yongli(requirement_description,test_content,ceshileixing,jianceyi_flag)
        if ai_data:
            # 解析 AI 返回的数据
            for item in ai_data:
                # 1）测试用例名称：简短易懂
                case_name = ceshixiang_name+'-'+item['item'].strip() if 'item' in item else ''
                # 2）测试用例描述：描述测试内容
                case_description = item['context'] if 'context' in item else ''
                # 3）测试步骤：详细执行步骤
                case_steps = item['method'].strip() if 'method' in item else ''
                # 4）预期结果：测试结果
                case_expect = item['expect'].strip() if 'expect' in item else ''
                # 进行分行
                # 将测试用例添加到列表中
                ceshiyongli.append([case_name, case_description, case_steps, case_expect])
            yingli_fenxi_flag = True  # AI 分析成功
        else:
            print("AI 未返回有效数据（测试用例设计）")
    except Exception as e:
        print(f"生成测试用例时发生错误：{e}")
    return yingli_fenxi_flag, ceshiyongli



def generate_test_yonglisheji(requirement_description,test_content,ceshileixing,jianceyi_flag):
    yingli_fenxi_flag = False
    ceshiyongli = []             # 用于存储测试用例,主要包括： 测试用例名称、测试用例描述、测试步骤、预期结果
    try:
        # 调用 AI_generate_yongli 函数生成测试用例
        ai_data = AI_generate_yongli(requirement_description,test_content,ceshileixing,jianceyi_flag)
        if ai_data:
            # 解析 AI 返回的数据
            for item in ai_data:
                # 1）测试用例名称：简短易懂
                case_name = item['item'].strip() if 'item' in item else ''
                # 2）测试用例描述：描述测试内容
                case_description = item['context'] if 'context' in item else ''
                # 3）测试步骤：详细执行步骤
                case_steps = item['method'].strip() if 'method' in item else ''
                # 4）预期结果：测试结果
                case_expect = item['expect'].strip() if 'expect' in item else ''
                # 进行分行
                # 将测试用例添加到列表中
                ceshiyongli.append([case_name, case_description, case_steps, case_expect])
            yingli_fenxi_flag = True  # AI 分析成功
        else:
            print("AI 未返回有效数据（测试用例设计）")
    except Exception as e:
        print(f"生成测试用例时发生错误：{e}")
    return yingli_fenxi_flag, ceshiyongli