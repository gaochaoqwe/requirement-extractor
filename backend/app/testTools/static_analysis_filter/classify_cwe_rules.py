"""
分类CWE规则为确定规则和不确定规则
"""
from pathlib import Path

# 读取CWE规则
cwe_rules_file = Path(__file__).parent / "database" / "CWE规则.md"

with open(cwe_rules_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 解析规则
rules = []
for line in lines:
    line = line.strip()
    if not line or not line[0].isalpha() and not line[0] == 'S' and not line[0] == 'C':
        continue
    rules.append(line)

print(f"总共 {len(rules)} 个CWE规则\n")

# 分类标准：
# 确定规则（accurate）- 可以通过静态分析准确判断的规则
# 不确定规则（uncertain）- 需要上下文分析或可能产生误报的规则

# 确定规则关键词
accurate_keywords = [
    "未使用", "未定义", "未初始化", "未释放", "未关闭",  # 明确的未做某事
    "禁止使用不安全", "不建议使用不安全", "不建议使用",  # 明确禁止的API
    "类型不兼容", "参数数量不匹配", "参数类型不兼容",  # 明确的类型错误
    "函数返回局部变量", "空函数有返回值", "非空函数无返回值",  # 明确的返回值错误
    "重复释放", "多次释放", "释放非堆内存",  # 明确的内存管理错误
    "固定地址赋给指针", "非法强转", "强制类型转换",  # 明确的类型转换问题
    "无效语句", "代码不可达", "无效跳转",  # 明确的语法问题
    "明文存储", "明文传输",  # 明确的安全问题
]

# 不确定规则关键词
uncertain_keywords = [
    "可疑", "可能", "污染数据", "外部输入", "外部控制",  # 需要数据流分析
    "数组越界", "缓冲区溢出", "指针越界", "整数溢出",  # 需要上下文判断
    "内存泄漏", "资源泄漏", "未释放",  # 需要追踪资源生命周期
    "空指针解引用", "指针解引用前未判空",  # 需要空指针分析
    "竞争条件", "死锁", "线程",  # 并发问题
    "注入", "遍历", "路径",  # 需要输入验证分析
    "使用释放后的内存", "返回释放后的内存",  # Use-after-free
]

# 分类
accurate_rules = []
uncertain_rules = []

for rule in rules:
    # 先检查是否匹配确定规则关键词
    is_accurate = False
    for keyword in accurate_keywords:
        if keyword in rule:
            is_accurate = True
            break
    
    # 如果不是确定规则，检查是否匹配不确定规则关键词
    if not is_accurate:
        for keyword in uncertain_keywords:
            if keyword in rule:
                uncertain_rules.append(rule)
                break
        else:
            # 默认归类到确定规则（简单的语法/类型问题）
            accurate_rules.append(rule)
    else:
        accurate_rules.append(rule)

# 特殊处理：某些规则虽然有"未"字但仍需要上下文分析
special_uncertain = [
    "未控制的递归",
    "未验证的密码改变",
    "未清除敏感信息",
]

# 移动特殊规则
for rule in special_uncertain:
    for r in rules:
        if rule in r and r in accurate_rules:
            accurate_rules.remove(r)
            uncertain_rules.append(r)
            break

print(f"="*100)
print(f"确定规则（accurate）: {len(accurate_rules)} 个")
print(f"="*100)
for idx, rule in enumerate(accurate_rules, 1):
    print(f"{idx:3d}. {rule}")

print(f"\n{'='*100}")
print(f"不确定规则（uncertain）: {len(uncertain_rules)} 个")
print(f"="*100)
for idx, rule in enumerate(uncertain_rules, 1):
    print(f"{idx:3d}. {rule}")

# 保存到文件
output_file = Path(__file__).parent / "database" / "CWE规则分类.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"CWE规则分类结果\n")
    f.write(f"总计: {len(rules)} 个规则\n")
    f.write(f"确定规则: {len(accurate_rules)} 个\n")
    f.write(f"不确定规则: {len(uncertain_rules)} 个\n\n")
    
    f.write("="*100 + "\n")
    f.write("确定规则（accurate）\n")
    f.write("="*100 + "\n")
    for idx, rule in enumerate(accurate_rules, 1):
        f.write(f"{idx:3d}. {rule}\n")
    
    f.write("\n" + "="*100 + "\n")
    f.write("不确定规则（uncertain）\n")
    f.write("="*100 + "\n")
    for idx, rule in enumerate(uncertain_rules, 1):
        f.write(f"{idx:3d}. {rule}\n")

print(f"\n\n✅ 分类结果已保存到: {output_file}")

