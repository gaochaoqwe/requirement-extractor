import requests
import json
import re
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
def generate_test_cases(ceshi_neirong,ceshi_leixing,jianceyi_flag):
    # 构建请求参数
    #  'system':系统预设提示，指导模型生成符合要求的 JSON 数据
    #  'prompt': 提取测试项的提示，指导模型生成符合要求的 JSON 数据
    #  'model': 模型名称
    #  'stream': 是否流式生成
    if jianceyi_flag == '有检测仪':
        # 1、功能测试
        if ceshi_leixing == '功能测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出正常功能以及异常功能的测试项任务。你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：测试内容描述、测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法,注意测试激励的输入和被测软件状态的监控都是通过检测仪实现的，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试项任务。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}。请确保生成的测试项任务覆盖所有关键功能点以及异常情况下的处理测试，并提供详细的测试内容和测试方法。输出结果必须为结构化数据，且符合上述JSON格式。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
        # 性能测试
        elif ceshi_leixing == '性能测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准识别性能指标并生成量化测试方案。每个测试项必须包含：测试内容描述、测试方法描述。输出格式严格遵循JSON字符串格式：'
                          '[{"context": "测试内容描述（需明确性能指标）", "method": "详细描述该测试项的性能测试的测试方法,注意测试激励的输入和被测软件状态的监控都是通过检测仪实现的。示例：使用检测仪模拟100并发用户持续请求登录接口，监测平均响应时间是否≤500ms。"}]',
                'prompt': f'请根据性能测试要求，分析以下软件需求：{ceshi_neirong}。建议覆盖以下性能维度：'
                          '1.系统吞吐量（TPS/QPS）测试'
                          '2.关键事务响应时间（平均/峰值）或者运行周期'
                          '3.长时间运行的性能衰减'
                          '生成不少于1个性能测试项'
                          '输出符合要求的JSON数组。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
        # 边界测试
        elif ceshi_leixing == '边界测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准识别边界条件并生成针对性测试用例。你的任务是根据用户提供的软件需求描述，深入分析并生成包含以下要素的测试项：1)数据范围极值 2)循环/次数限制 3)容量临界点 4)状态转换边界。每个测试项必须包含：测试内容描述、测试方法描述。输出格式严格遵循JSON字符串格式：'
                          '[{"context": "测试内容描述（需明确边界类型）", "method": "测试方法需包含：边界值输入步骤、越界处理验证等，测试激励的输入和被测软件状态的监控都是通过检测仪实现的。示例：系统初始化后，发送含最大允许字符数的配置指令，验证配置存储功能是否正常。"}]',
                'prompt': f'请根据边界测试要求，分析以下软件需求：{ceshi_neirong}。需覆盖以下边界类型：'
                          '1.数值型参数的上下限值（含等于、略小于、略大于边界值的情况）'
                          '2.字符串/数据长度的最大最小值'
                          '3.集合元素的空集/满集状态'
                          '4.状态转换的前置/后置条件'
                          '5.时间相关参数的起始/终止临界点'
                          '生成不少于1个边界测试项，每个测试项的method字段必须包含：'
                          'a)边界值设置方法 b)预期行为验证方式 c)异常处理检查步骤'
                          '输出符合要求的JSON数组。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
        # 其他类型的测试
        else:
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出测试项任务。你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：测试内容描述、测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，测试激励的输入和被测软件状态的监控都是通过检测仪实现的，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试项任务。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}。请确保生成的测试项任务覆盖所有关键功能点，并提供详细的测试内容和测试方法。输出结果必须为结构化数据，且符合上述JSON格式。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
    else:
        # 1、功能测试
        if ceshi_leixing == '功能测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出正常功能以及异常功能的测试项任务。你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：测试内容描述、测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试项任务。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}。请确保生成的测试项任务覆盖所有关键功能点以及异常情况下的处理测试，并提供详细的测试内容和测试方法。输出结果必须为结构化数据，且符合上述JSON格式。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }

        # 性能测试
        elif ceshi_leixing == '性能测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准识别性能指标并生成量化测试方案。每个测试项必须包含：测试内容描述、测试方法描述。输出格式严格遵循JSON字符串格式：'
                          '[{"context": "测试内容描述（需明确性能指标）", "method": "测试方法需包含：负载模拟方式、指标采集工具、性能判定标准。示例：使用跳绳计算机模拟100并发用户持续请求登录接口，监测平均响应时间是否≤500ms。"}]',
                'prompt': f'请根据性能测试要求，分析以下软件需求：{ceshi_neirong}。建议覆盖以下性能维度：'
                          '1.系统吞吐量（TPS/QPS）测试'
                          '2.关键事务响应时间（平均/峰值）或者运行周期'
                          '3.长时间运行的性能衰减'
                          '生成不少于1个性能测试项'
                          '输出符合要求的JSON数组。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }

        # 边界测试
        elif ceshi_leixing == '边界测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准识别边界条件并生成针对性测试用例。你的任务是根据用户提供的软件需求描述，深入分析并生成包含以下要素的测试项：1)数据范围极值 2)循环/次数限制 3)容量临界点 4)状态转换边界。每个测试项必须包含：测试内容描述、测试方法描述。输出格式严格遵循JSON字符串格式：'
                          '[{"context": "测试内容描述（需明确边界类型）", "method": "测试方法需包含：边界值输入步骤、越界处理验证方法。示例：系统初始化后，发送含最大允许字符数的配置指令，验证配置存储功能是否正常。"}]',
                'prompt': f'请根据边界测试要求，分析以下软件需求：{ceshi_neirong}。需覆盖以下边界类型：'
                          '1.数值型参数的上下限值（含等于、略小于、略大于边界值的情况）'
                          '2.字符串/数据长度的最大最小值'
                          '3.集合元素的空集/满集状态'
                          '4.状态转换的前置/后置条件'
                          '5.时间相关参数的起始/终止临界点'
                          '生成不少于1个边界测试项，每个测试项的method字段必须包含：'
                          'a)边界值设置方法 b)预期行为验证方式 c)异常处理检查步骤'
                          '输出符合要求的JSON数组。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
        # 其他类型的测试
        else:
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出测试项任务。你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：测试内容描述、测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析以下软件需求描述，并根据要求生成测试项任务。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}。请确保生成的测试项任务覆盖所有关键功能点，并提供详细的测试内容和测试方法。输出结果必须为结构化数据，且符合上述JSON格式。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
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
            max_loop = max_loop - 1  # 当发生异常时，减少重试次数
            print(e)
            print(' Api分析函数错误(没有数据库情况下的需求分析)!!!!!!')
    return data  # 返回解析后的 JSON 数据


# 根据测试相对应的需求描述，从知识库提取的测试内容和测试方法，生成真正的测试内容和测试方法。
def generate_test_cases_have_zhishi(ceshi_neirong,ceshixiang_miaoshu, ceshixiang_fangfa,ceshi_leixing,jianceyi_flag):
    # 构建请求参数
    #  'system':系统预设提示，指导模型生成符合要求的 JSON 数据
    #  'prompt': 提取测试项的提示，指导模型生成符合要求的 JSON 数据
    #  'model': 模型名称
    #  'stream': 是否流式生成
    if jianceyi_flag == '有检测仪':
        if ceshi_leixing == '功能测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出正常功能以及异常功能的测试项任务。你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：测试内容描述、测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析软件需求描述，对测试内容以及测试方法进行细化，输出结构化数据。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}，测试内容为：{ceshixiang_miaoshu}，测试方法为{ceshixiang_fangfa}。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }

        # 性能测试
        elif ceshi_leixing == '性能测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准识别性能指标并生成量化测试方案。每个测试项必须包含：测试内容描述、测试方法描述。输出格式严格遵循JSON字符串格式：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析软件需求描述，对测试内容以及测试方法进行细化，输出结构化数据。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}，测试内容为：{ceshixiang_miaoshu}，测试方法为{ceshixiang_fangfa}。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
        # 边界测试
        elif ceshi_leixing == '边界测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准识别边界条件并生成针对性测试用例。你的任务是根据用户提供的软件需求描述，深入分析并生成包含以下要素的测试项：1)数据范围极值 2)循环/次数限制 3)容量临界点 4)状态转换边界。每个测试项必须包含：测试内容描述、测试方法描述。输出格式严格遵循JSON字符串格式：'
                          '[{"context": "测试内容描述（需明确边界类型）", "method": "测试方法需包含：边界值输入步骤、越界处理验证方法。示例：系统初始化后，发送含最大允许字符数的配置指令，验证配置存储功能是否正常。"}]',
                'prompt': f'请根据边界测试要求，分析以下软件需求：{ceshi_neirong}。建议覆盖以下边界类型：'
                          '1.数值型参数的上下限值（含等于、略小于、略大于边界值的情况）'
                          '2.字符串/数据长度的最大最小值'
                          '3.集合元素的空集/满集状态'
                          '4.状态转换的前置/后置条件'
                          '5.时间相关参数的起始/终止临界点'
                          '生成不少于1个边界测试项，每个测试项的method字段必须包含：'
                          'a)边界值设置方法 b)预期行为验证方式 c)异常处理检查步骤'
                          '输出符合要求的JSON数组。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
            # 其他类型的测试
        else:
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出测试项任务。你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：测试内容描述、测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析软件需求描述，对测试内容以及测试方法进行细化，输出结构化数据。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}，测试内容为：{ceshixiang_miaoshu}，测试方法为{ceshixiang_fangfa}。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
    else:
        if ceshi_leixing == '功能测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出正常功能以及异常功能的测试项任务。你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：测试内容描述、测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析软件需求描述，对测试内容以及测试方法进行细化，输出结构化数据。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}，测试内容为：{ceshixiang_miaoshu}，测试方法为{ceshixiang_fangfa}。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }

        # 性能测试
        elif ceshi_leixing == '性能测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准识别性能指标并生成量化测试方案。每个测试项必须包含：测试内容描述、测试方法描述。输出格式严格遵循JSON字符串格式：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析软件需求描述，对测试内容以及测试方法进行细化，输出结构化数据。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}，测试内容为：{ceshixiang_miaoshu}，测试方法为{ceshixiang_fangfa}。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
        # 边界测试
        elif ceshi_leixing == '边界测试':
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准识别边界条件并生成针对性测试用例。你的任务是根据用户提供的软件需求描述，深入分析并生成包含以下要素的测试项：1)数据范围极值 2)循环/次数限制 3)容量临界点 4)状态转换边界。每个测试项必须包含：测试内容描述、测试方法描述。输出格式严格遵循JSON字符串格式：'
                          '[{"context": "测试内容描述（需明确边界类型）", "method": "测试方法需包含：边界值输入步骤、越界处理验证方法。示例：系统初始化后，发送含最大允许字符数的配置指令，验证配置存储功能是否正常。"}]',
                'prompt': f'请根据边界测试要求，分析以下软件需求：{ceshi_neirong}。建议覆盖以下边界类型：'
                          '1.数值型参数的上下限值（含等于、略小于、略大于边界值的情况）'
                          '2.字符串/数据长度的最大最小值'
                          '3.集合元素的空集/满集状态'
                          '4.状态转换的前置/后置条件'
                          '5.时间相关参数的起始/终止临界点'
                          '生成不少于1个边界测试项，每个测试项的method字段必须包含：'
                          'a)边界值设置方法 b)预期行为验证方式 c)异常处理检查步骤'
                          '输出符合要求的JSON数组。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }
            # 其他类型的测试
        else:
            params = {
                'system': '你是一个经验丰富的软件测试专家，专注于从软件需求中精准提炼出测试项任务。你的任务是根据用户提供的软件需求描述，深入分析并生成对应的测试项任务，每个测试项都必须包含以下两个关键部分：测试内容描述、测试方法描述。输出格式必须严格遵循JSON字符串数据格式，具体格式如下：'
                          '[{"context": "详细描述测试项的测试内容",  "method": "详细描述该测试项的测试方法和测试步骤，例如：系统正常上电，通过检测仪发送维护自检指令，测试维护自检功能是否正常。"}]',
                'prompt': f'请根据测试类型，分析软件需求描述，对测试内容以及测试方法进行细化，输出结构化数据。测试类型为：{ceshi_leixing}，软件需求描述为：{ceshi_neirong}，测试内容为：{ceshixiang_miaoshu}，测试方法为{ceshixiang_fangfa}。',
                'model': OLLAMA_MODEL,
                'stream': False,
            }

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
            max_loop = max_loop - 1  # 当发生异常时，减少重试次数
            print(e)
            print('Api分析函数错误(基于检索增强的测试需求分析)!!!!!!')
    return data  # 返回解析后的 JSON 数据

# 函数功能：对软件的测试项进行分析，输出测试内容和测试方法。
# 输入:    软件需求
# 输出软件：测试内容、测试方法
# ceshi_leixing: 测试类型
def moxingfenxi(str_temp,ceshi_leixing,jianceyi_flag):
    try:
        # 1、直接调用梁恒瑞提供的api接口的方法。
        # url = "https://hpc.613.com/ais/chain/api/test"  # "prompt":"进行目标攻击前需要判断激光状态是否正常
        # data = {"prompt": str_temp}
        # response = requests.post(url,json=data,verify=False)
        # fenxijieguo=response.json()
        # 判定用例的设计内容(功能测试，性能测试，边界测试)
        # 2、自行封装的ai模型调用的方法？
        fenxijieguo=generate_test_cases(str(str_temp),ceshi_leixing,jianceyi_flag)
        ceshineirong_jishu_temp=1    # 变量初始化
        ceshifangfa_jishu_temp=1
        ceshineirong_final=''
        ceshifangfa_final=''
        # 遍历列表中的每个字典
        for item in fenxijieguo:
            # 对测试内容进行分析。
            ceshineirong=item['context']
            ceshineirong = str(ceshineirong_jishu_temp) + '、' + ceshineirong + '\n'
            ceshineirong_jishu_temp=ceshineirong_jishu_temp+1   
            # 对测试方法进行分析。
            ceshifangfa= item['method']
            ceshifangfa=ceshifangfa.replace('\n','')  #避免大模型生成的编号中的中英文符号产生干扰。
            ceshifangfa = ceshifangfa.replace('1. ', '').replace('2. ', '').replace('3. ', '').replace('4. ','').replace('5. ', '').replace('6. ', '').replace('7. ', '').replace('8. ', '').replace('9. ', '')
            ceshifangfa = ceshifangfa.replace('步骤1：', '').replace('步骤2：', '').replace('步骤3：', '').replace('步骤4：', '').replace('步骤5：', '').replace('步骤6：', '').replace('步骤7：', '').replace('步骤8：', '')
            ceshifangfa = ceshifangfa.replace('步骤1:', '').replace('步骤2:', '').replace('步骤3:', '').replace('步骤4:', '').replace('步骤5:', '').replace('步骤6:', '').replace('步骤7:', '').replace('步骤8:', '')
            ceshifangfa = ceshifangfa.replace('；', '，')
            ceshifangfa = ceshifangfa.replace('。', '，')
            ceshifangfa = ceshifangfa + '，'
            ceshifangfa = ceshifangfa.replace('，，', '。')
            # 如果生成的结果只包含一个测试方法,则直接将测试方法编号加上。
            ceshifangfa = str(ceshifangfa_jishu_temp) + '、' + ceshifangfa
            ceshifangfa_jishu_temp = ceshifangfa_jishu_temp + 1
            # 将结果拼接
            ceshineirong_final= ceshineirong_final+ceshineirong    # 测试内容描述
            ceshifangfa_final= ceshifangfa_final+ceshifangfa       # 测试方法描述
        #对生成的结果进行进一步的拆分
        ceshifangfa_final = re.sub(r'(\d+、)', r'\n\g<0>', ceshifangfa_final)  # 加换行符
        ceshifangfa_final = ceshifangfa_final.replace('\n\n', '\n')  # 避免出现断行
        # 返回测试内容、测试方法
        return ceshineirong_final,ceshifangfa_final
    except:
        print("API分析结果错误(不进行检索增强)！！！！！！")
        return 'error','error'


# 再有知识库的情况下，根据软件的需求描述分析软件的测试内容和测试方法
# 函数输入：
# str_temp：测试项对应的软件需求描述。
# ceshixiang_miaoshu：测试项对应的测试内容。
# ceshixiang_fangfa：测项项对应的测试方法
# ceshixiang_name:测试项名称
def moxingfenxi_have_zhishi(str_temp,ceshixiang_miaoshu, ceshixiang_fangfa,ceshi_leixing,jianceyi_flag):
    # 1、如果检索增强分析成功就用检索增强的结果，如果没有的话直接返回原结果。
    try:
        # 1、直接调用梁恒瑞提供的api接口的方法。
        # url = "https://hpc.613.com/ais/chain/api/test"  # "prompt":"进行目标攻击前需要判断激光状态是否正常
        # data = {"prompt": str_temp}
        # response = requests.post(url,json=data,verify=False)
        # fenxijieguo=response.json()

        # 2、自行封装的ai模型调用的方法？
        fenxijieguo = generate_test_cases_have_zhishi(str(str_temp),ceshixiang_miaoshu, ceshixiang_fangfa,ceshi_leixing,jianceyi_flag)
        ceshineirong_jishu_temp = 1  # 变量初始化
        ceshifangfa_jishu_temp = 1
        ceshineirong_final = ''
        ceshifangfa_final = ''
        # 遍历列表中的每个字典
        for item in fenxijieguo:
            # 对测试内容进行分析。
            ceshineirong = item['context']
            ceshineirong = str(ceshineirong_jishu_temp) + '、' + ceshineirong + '\n'
            ceshineirong_jishu_temp = ceshineirong_jishu_temp + 1
            # 对测试方法进行分析。
            ceshifangfa = item['method']
            ceshifangfa=ceshifangfa.replace('\n','').replace(' ','')                                 #避免大模型生成的编号中的中英文符号产生干扰。
            ceshifangfa = ceshifangfa.replace('1. ', '').replace('2. ', '').replace('3. ', '').replace('4. ', '').replace('5. ', '').replace('6. ', '').replace('7. ', '').replace('8. ', '').replace('9. ', '')
            ceshifangfa = ceshifangfa.replace('步骤1：', '').replace('步骤2：', '').replace('步骤3：', '').replace('步骤4：', '').replace('步骤5：', '').replace('步骤6：', '').replace('步骤7：', '').replace('步骤8：', '')
            ceshifangfa = ceshifangfa.replace('步骤1:', '').replace('步骤2:', '').replace('步骤3:', '').replace('步骤4:', '').replace('步骤5:', '').replace('步骤6:', '').replace('步骤7:', '').replace('步骤8:', '')
            ceshifangfa = ceshifangfa.replace('；', '，')
            ceshifangfa = ceshifangfa.replace('。', '，')
            ceshifangfa = ceshifangfa+'，'
            ceshifangfa = ceshifangfa.replace('，，', '。')
            # 如果生成的结果只包含一个测试方法,则直接将测试方法编号加上。
            ceshifangfa = str(ceshifangfa_jishu_temp) + '、' + ceshifangfa
            ceshifangfa_jishu_temp = ceshifangfa_jishu_temp + 1
            # 将结果拼接
            ceshineirong_final = ceshineirong_final + ceshineirong      # 测试内容描述
            ceshifangfa_final = ceshifangfa_final + ceshifangfa         # 测试方法描述
        # 对生成的结果进行进一步的拆分
        ceshifangfa_final = re.sub(r'(\d+、)', r'\n\g<0>', ceshifangfa_final)   # 加换行符
        ceshifangfa_final = ceshifangfa_final.replace('\n\n', '\n')  # 避免出现断行
        # 返回测试内容、测试方法
        return ceshineirong_final, ceshifangfa_final
    # 2、如果检索增强分析失败就直接返回原结果
    except:
        print("API分析结果错误（进行检索增强）！！！！！！")
        return ceshixiang_miaoshu, ceshixiang_fangfa

# 翻译功能已移动到ai.test_analysis模块中
