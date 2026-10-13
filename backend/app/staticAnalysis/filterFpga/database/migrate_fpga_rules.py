"""
从FPGA规则.md文件导入FPGA规则数据到PostgreSQL

功能：
1. 解析FPGA规则.md文件中的Verilog和VHDL规则
2. 将规则数据插入到fpga_rules表
"""
import sys
import re
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
current_file = Path(__file__).resolve()
db_dir = current_file.parent
filter_dir = db_dir.parent
static_analysis_dir = filter_dir.parent
app_dir = static_analysis_dir.parent
backend_dir = app_dir.parent
project_root = backend_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
from backend.app.staticAnalysis.filterFpga.database.postgresql_models import FPGARule

# FPGA规则文件路径
RULES_DIR = db_dir / "rules"
VERILOG_MANDATORY_PATH = RULES_DIR / "Verilog_强制准则.txt"
VERILOG_ADVISORY_PATH = RULES_DIR / "Verilog_建议准则.txt"
VHDL_MANDATORY_PATH = RULES_DIR / "VHDL_强制准则.txt"
VHDL_ADVISORY_PATH = RULES_DIR / "VHDL_建议准则.txt"


def parse_fpga_rules():
    """解析FPGA规则文件，从4个独立的txt文件提取所有规则"""
    rules = []
    
    try:
        # 1. 解析Verilog强制准则
        if VERILOG_MANDATORY_PATH.exists():
            with open(VERILOG_MANDATORY_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:  # 跳过表头
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        seq = parts[0].strip()
                        rule_code = parts[1].strip()
                        rule_content = parts[2].strip()
                        rules.append({
                            'sequence': int(seq),
                            'rule_code': rule_code,
                            'rule_content': rule_content,
                            'language': 'Verilog',
                            'rule_type': 'mandatory',
                            'category': 'Verilog强制准则',
                            'chapter': None
                        })
        
        # 2. 解析Verilog建议准则
        if VERILOG_ADVISORY_PATH.exists():
            with open(VERILOG_ADVISORY_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:  # 跳过表头
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        seq = parts[0].strip()
                        rule_code = parts[1].strip()
                        rule_content = parts[2].strip()
                        rules.append({
                            'sequence': int(seq),
                            'rule_code': rule_code,
                            'rule_content': rule_content,
                            'language': 'Verilog',
                            'rule_type': 'advisory',
                            'category': 'Verilog建议准则',
                            'chapter': None
                        })
        
        # 3. 解析VHDL强制准则
        if VHDL_MANDATORY_PATH.exists():
            with open(VHDL_MANDATORY_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:  # 跳过表头
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        seq = parts[0].strip()
                        chapter = parts[1].strip()
                        rule_content = parts[2].strip()
                        rules.append({
                            'sequence': int(seq),
                            'rule_code': chapter,
                            'rule_content': rule_content,
                            'language': 'VHDL',
                            'rule_type': 'mandatory',
                            'category': 'VHDL强制准则',
                            'chapter': chapter
                        })
        
        # 4. 解析VHDL建议准则
        if VHDL_ADVISORY_PATH.exists():
            with open(VHDL_ADVISORY_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:  # 跳过表头
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        seq = parts[0].strip()
                        chapter = parts[1].strip()
                        rule_content = parts[2].strip()
                        rules.append({
                            'sequence': int(seq),
                            'rule_code': chapter,
                            'rule_content': rule_content,
                            'language': 'VHDL',
                            'rule_type': 'advisory',
                            'category': 'VHDL建议准则',
                            'chapter': chapter
                        })
        
        return rules
        
    except Exception as e:
        print(f"    ERROR: 解析FPGA规则文件失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def determine_accuracy(rule_code: str, rule_content: str, language: str, rule_type: str) -> str:
    """根据规则编号/内容/语言/类型，判定 accuracy_type: accurate 或 uncertain

    规则：
    - 需要结合上下文、跨模块/跨时钟域分析、动态行为才能确认的问题 -> uncertain
    - 纯语法/结构/命名/单点静态可判定的问题 -> accurate
    具体实现：
    - Verilog: R-14-* (状态机行为)、R-15-* (跨时钟/时钟域) 归为 uncertain
    - VHDL: 5.9.* (时钟域/门控时钟/跨域)、5.11.* (状态机) 归为 uncertain
    - 对于建议准则(A-前缀)中涉及时钟域/状态机/复位时序等语义性的，也归为 uncertain
    - 关键字命中："死锁"、"不可达"、"跨时钟"、"门控时钟"、"同步释放"、"三段式状态机"、"状态数量及编码" -> uncertain
    其他默认 accurate
    """
    text = (rule_content or "")
    lc = (rule_code or "")

    # 规则编号模式
    if language == 'Verilog':
        if lc.startswith('R-14-') or lc.startswith('R-15-'):
            return 'uncertain'
        if lc.startswith('A-') and (lc.startswith('A-14-') or lc.startswith('A-5-')):
            # 建议中与状态机/复位域相关的，容易依赖上下文
            keywords = ['状态机', '跨时钟', '门控时钟', '复位域', '复位时序']
            if any(k in text for k in keywords):
                return 'uncertain'
    elif language == 'VHDL':
        if lc.startswith('5.9.') or lc.startswith('5.11.'):
            return 'uncertain'

    # 关键词命中
    uncertain_keywords = ['死锁', '不可达', '跨时钟', '门控时钟', '同步释放', '三段式状态机', '状态数量', '编码方式要求']
    if any(k in text for k in uncertain_keywords):
        return 'uncertain'

    return 'accurate'


def clean_issue_title(title: str, rule_code: str) -> str:
    """Remove rule code annotations from generated issue titles."""
    if not title:
        return title

    if rule_code:
        patterns = [
            f"（{rule_code}）",
            f"({rule_code})",
            f"[{rule_code}]",
        ]
        for pattern in patterns:
            title = title.replace(pattern, '')

    return re.sub(r'\s+', ' ', title).strip()


def build_issue_title(rule_code: str, rule_content: str, language: str, rule_type: str) -> str:
    """根据规则生成问题名称（四段式标题字段）。优先按具体 rule_code 定义，未命中时使用兜底生成。"""
    core = (rule_content or '').strip()
    def _clean(text: str) -> str:
        return clean_issue_title(text, rule_code)
    # 1) 精确映射（逐条规则定制）
    rule_map = {
        # Verilog 强制 R-2-* 命名类
        'R-2-1': f"标识符命名必须以字母开头（{rule_code}）",
        'R-2-2': f"禁止连续下划线与尾部下划线的命名（{rule_code}）",
        'R-2-3': f"命名禁止与语言关键字同名（{rule_code}）",
        'R-2-4': f"禁止使用电源/地保留名作为标识符（{rule_code}）",
        'R-2-5': f"每个文件仅允许一个 module 定义（{rule_code}）",
        'R-2-6': f"禁止仅用大小写差异区分命名（{rule_code}）",
        'R-2-7': f"文件引用必须使用相对路径（{rule_code}）",
        'R-2-8': f"禁止使用不在允许集合内的数据类型（{rule_code}）",
        'R-2-9': f"模块例化必须使用端口名映射，禁止位置映射（{rule_code}）",
        'R-2-10': f"禁止顶层输入管脚悬空（{rule_code}）",
        'R-2-11': f"禁止在多个文件中重复 define 定义（{rule_code}）",
        # Verilog 强制 R-3-*
        'R-3-1': f"端口例化禁止使用表达式（{rule_code}）",
        'R-3-2': f"顶层端口类型必须使用 reg / wire（{rule_code}）",
        'R-3-3': f"禁止多个嵌套控制语句（{rule_code}）",
        # Verilog 强制 R-4-*
        'R-4-1': f"寄存器输出禁止直连至其他寄存器时钟管脚（{rule_code}）",
        'R-4-2': f"时钟信号禁止连接至非时钟管脚（{rule_code}）",
        'R-4-3': f"组合逻辑输出禁止作为时钟信号（{rule_code}）",
        # Verilog 强制 R-5-* 复位类
        'R-5-1': f"异步置位/复位禁止连接到非置位/复位端（{rule_code}）",
        'R-5-2': f"同一复位链路禁止混用异步复位与同步复位（{rule_code}）",
        'R-5-3': f"禁止使用有竞争冒险的组合输出作为复位信号（{rule_code}）",
        'R-5-4': f"专用时钟单元必须用于驱动内部时钟/高扇出控制/复位信号（{rule_code}）",
        'R-5-5': f"非SRAM型FPGA寄存器必须进行上电初始化（{rule_code}）",
        # Verilog 强制 R-6-* 触发器
        'R-6-1': f"禁止在同一always中混合有复位和无复位触发器（{rule_code}）",
        'R-6-2': f"复位或初始化时必须对触发器赋初值（{rule_code}）",
        'R-6-3': f"复位信号触发条件与进入条件必须一致（{rule_code}）",
        'R-6-4': f"禁止将触发器作为时钟信号（{rule_code}）",
        # Verilog 强制 R-7-* 锁存器
        'R-7-1': f"禁止含锁存器的组合逻辑环路（{rule_code}）",
        'R-7-2': f"禁止使用基本逻辑门描述锁存器（{rule_code}）",
        # Verilog 强制 R-8-* 三态
        'R-8-1': f"禁止组合逻辑输出作为三态缓冲器使能端（{rule_code}）",
        'R-8-2': f"禁止使用内部三态（{rule_code}）",
        # Verilog 强制 R-9-* 运算符
        'R-9-1': f"关系操作符左右数据位宽必须一致（{rule_code}）",
        'R-9-2': f"位操作符左右数据位宽必须一致（{rule_code}）",
        'R-9-3': f"禁止算术表达式中无符号数与有符号数混用（{rule_code}）",
        'R-9-4': f"禁止关系表达式中使用包含X或Z的值（{rule_code}）",
        'R-9-5': f"禁止算术操作中使用包含X或Z的值（{rule_code}）",
        'R-9-6': f"数值位宽必须与实际位宽一致（{rule_code}）",
        'R-9-7': f"禁止算术运算结果位宽溢出（{rule_code}）",
        # Verilog 强制 R-10-* 赋值
        'R-10-1': f"模块端口位宽与实例化信号位宽必须一致（{rule_code}）",
        'R-10-2': f"赋值表达式左值与右值位宽必须一致（{rule_code}）",
        'R-10-3': f"组合电路必须使用阻塞赋值（{rule_code}）",
        'R-10-4': f"时序电路必须使用非阻塞赋值（{rule_code}）",
        'R-10-5': f"禁止同一条件下对同一信号重复赋值（{rule_code}）",
        'R-10-6': f"禁止使用延时语句（{rule_code}）",
        # Verilog 强制 R-11-* 条件语句
        'R-11-1': f"case语句必须使用default分支（{rule_code}）",
        'R-11-2': f"禁止case语句控制表达式使用固定值（{rule_code}）",
        'R-11-3': f"case分支表达式必须在控制范围内且位宽一致（{rule_code}）",
        'R-11-4': f"if/case条件表达式禁止出现x或z（{rule_code}）",
        'R-11-5': f"禁止使用|和||连接敏感信号（{rule_code}）",
        'R-11-6': f"case分支必须使用常量而非变量或逻辑运算（{rule_code}）",
        'R-11-7': f"禁止case选择分支存在遗失赋值（{rule_code}）",
        'R-11-8': f"禁止敏感列表与if条件不匹配（{rule_code}）",
        'R-11-9': f"异步always中if/else分支应包含所有信号赋值（{rule_code}）",
        # Verilog 强制 R-12-* 循环
        'R-12-1': f"for语句初值和条件必须为常数且禁止改变循环变量（{rule_code}）",
        'R-12-2': f"禁止for语句中对循环变量外的变量运算（{rule_code}）",
        'R-12-3': f"复位部分和逻辑部分禁止在同一for循环（{rule_code}）",
        'R-12-4': f"循环语句必须至少满足一次循环条件（{rule_code}）",
        'R-12-5': f"禁止调用递归函数（{rule_code}）",
        # Verilog 强制 R-13-* 函数与其他
        'R-13-1': f"禁止task语句中使用时序控制（{rule_code}）",
        'R-13-2': f"禁止使用initial语句（{rule_code}）",
        'R-13-3': f"function中使用阻塞赋值（=），避免非阻塞赋值（<=）。",
        'R-13-4': f"避免在function/task中对全局信号赋值，仅操作局部变量和输出参数。",
        'R-13-5': f"确保function返回值位宽与输入信号位宽一致，避免位宽转换错误。",
        'R-13-6': f"确保task输入输出信号位宽匹配，必要时进行显式转换。",
        'R-13-7': f"检查并消除组合逻辑中的反馈路径，重构为时序逻辑或状态机。",
        'R-13-8': f"检查所有数组访问，确保索引在合法范围内，必要时添加边界检查。",
        'R-13-9': f"完善敏感信号列表，包含always块中使用的所有输入信号，或使用always @(*)。",
        'R-14-1': f"检查状态机，消除死锁状态和不可达状态，确保所有状态可正常转换。",
        'R-14-2': f"在状态机default分支中将所有寄存器重置为确定的初始状态。",
        'R-14-3': f"在复位分支中为状态机设置明确的初始状态（如IDLE）。",
        'R-15-1': f"在异步时钟域边界处移除组合逻辑，使用寄存器进行同步。",
        'R-15-2': f"在跨时钟域同步器的两级寄存器间避免插入任何组合逻辑。",
        'R-15-3': f"检查并消除第一级同步寄存器后的反馈环路，避免亚稳态传播。",
        'R-16-1': f"在综合约束中明确指定复位属性（如async_reg），禁止工具自动更改。",
        'R-16-2': f"在综合脚本中设置状态机编译模式为safe模式，确保非法状态可恢复。",
        # Verilog 强制 R-14-* 状态机
        'R-14-1': f"状态机禁止死锁状态和不可达状态（{rule_code}）",
        'R-14-2': f"状态机default时必须将寄存器重置为确定状态（{rule_code}）",
        'R-14-3': f"状态机必须设置初始状态（{rule_code}）",
        # Verilog 强制 R-15-* 跨时钟域
        'R-15-1': f"禁止异步时钟区域内放置组合逻辑（{rule_code}）",
        'R-15-2': f"禁止第一级与第二级同步寄存器间插入组合逻辑（{rule_code}）",
        'R-15-3': f"异步时钟第一级同步寄存器后禁止反馈环路（{rule_code}）",
        # Verilog 强制 R-16-* 综合
        'R-16-1': f"禁止综合工具改变代码复位属性（{rule_code}）",
        'R-16-2': f"状态机编译模式必须选择safe模式（{rule_code}）",
    }
    if rule_code in rule_map:
        return _clean(rule_map[rule_code])
    # 2) VHDL规则映射
    if language == 'VHDL':
        # VHDL强制准则
        if rule_code.startswith('5.'):
            if rule_code == '5.1.1': return _clean(f"端口例化应采用名称映射而非位置映射（{rule_code}）")
            elif rule_code == '5.1.2': return _clean(f"例化时禁止输入端口悬空（{rule_code}）")
            elif rule_code == '5.2.1': return _clean(f"每个模块/单元应至少包含1个输入/输出端口（{rule_code}）")
            elif rule_code == '5.2.2': return _clean(f"除双向端口外输出信号禁止驱动同模块内部逻辑（{rule_code}）")
            elif rule_code == '5.2.3': return _clean(f"内部信号应避免使用三态逻辑（{rule_code}）")
            elif rule_code == '5.3.1': return _clean(f"进程敏感列表信号应完整正确（{rule_code}）")
            elif rule_code == '5.4.1': return _clean(f"多位信号变量定义时必须设置位宽（{rule_code}）")
            elif rule_code == '5.4.3': return _clean(f"条件判断表达式避免使用?/X/Z等状态（{rule_code}）")
            elif rule_code == '5.4.4': return _clean(f"不应在进程中使用多个event control段（{rule_code}）")
            elif rule_code == '5.5.1': return _clean(f"自定义标识符命名禁止与关键字重复（{rule_code}）")
            elif rule_code == '5.5.2': return _clean(f"不同类型标识符禁止采用相同名称（{rule_code}）")
            elif rule_code == '5.5.3': return _clean(f"自定义标识符命名要求规范（{rule_code}）")
            elif rule_code == '5.5.4': return _clean(f"禁止使用大小写字母区分不同命名（{rule_code}）")
            elif rule_code == '5.6.1': return _clean(f"信号应在赋值后使用（{rule_code}）")
            elif rule_code == '5.6.2': return _clean(f"运算符两端信号或参数位宽应相等（{rule_code}）")
            elif rule_code == '5.6.3': return _clean(f"常量赋值表达式右边应为固定整型值（{rule_code}）")
            elif rule_code == '5.6.4': return _clean(f"不应在整数实数无符号整数间使用隐式转换（{rule_code}）")
            elif rule_code == '5.6.5': return _clean(f"避免有符号数和无符号数混用于同一运算（{rule_code}）")
            elif rule_code == '5.6.6': return _clean(f"同一模块中单向信号不应有多重驱动（{rule_code}）")
            elif rule_code == '5.6.7': return _clean(f"相同信号源应避免驱动寄存器多个异步端（{rule_code}）")
            elif rule_code == '5.6.8': return _clean(f"信号赋值中不能存在波形（{rule_code}）")
            elif rule_code == '5.7.1': return _clean(f"控制循环终止条件的参数必须为常量（{rule_code}）")
            elif rule_code == '5.7.2': return _clean(f"禁止在for循环体内修改循环变量（{rule_code}）")
            elif rule_code == '5.7.3': return _clean(f"while语句条件表达式不应为常量（{rule_code}）")
            elif rule_code == '5.8.1': return _clean(f"case语句表达式不应为固定常量（{rule_code}）")
            elif rule_code == '5.8.2': return _clean(f"case分支不应使用变量或变量表达式（{rule_code}）")
            elif rule_code == '5.8.3': return _clean(f"case语句必须包含when others分支（{rule_code}）")
            elif rule_code == '5.8.4': return _clean(f"组合逻辑if语句应包含else分支（{rule_code}）")
            elif rule_code == '5.8.5': return _clean(f"组合逻辑case分支下应对所有信号赋值（{rule_code}）")
            elif rule_code == '5.9.1': return _clean(f"禁止时钟信号再汇聚（{rule_code}）")
            elif rule_code == '5.9.2': return _clean(f"禁止时钟信号连接到多路选择器控制端（{rule_code}）")
            elif rule_code == '5.9.3': return _clean(f"避免使用门控时钟（{rule_code}）")
            elif rule_code == '5.9.4': return _clean(f"同一进程中应只使用一个时钟（{rule_code}）")
            elif rule_code == '5.9.5': return _clean(f"跨时钟域信号应采取同步处理措施（{rule_code}）")
            elif rule_code == '5.9.6': return _clean(f"禁止将时钟作为输入数据使用（{rule_code}）")
            elif rule_code == '5.10.1': return _clean(f"禁止寄存器输出反馈到异步复位/置位端（{rule_code}）")
            elif rule_code == '5.10.2': return _clean(f"复位与置位信号不应来自同一信号（{rule_code}）")
            elif rule_code == '5.10.3': return _clean(f"异步复位释放时应采用同步释放方式（{rule_code}）")
            elif rule_code == '5.10.4': return _clean(f"寄存器复位端口禁止悬空（{rule_code}）")
            elif rule_code == '5.11.1': return _clean(f"对状态机无效状态应进行合理处理（{rule_code}）")
            elif rule_code == '5.11.2': return _clean(f"状态机综合属性应适当设置确保有效（{rule_code}）")
            elif rule_code == '5.11.3': return _clean(f"状态机应初始化为合法状态（{rule_code}）")
            elif rule_code == '5.11.4': return _clean(f"状态机不能出现不可达状态（{rule_code}）")
            elif rule_code == '5.12.1': return _clean(f"综合代码中避免使用不可综合的代码（{rule_code}）")
            elif rule_code == '5.12.2': return _clean(f"约束设置时应避免不同约束间矛盾（{rule_code}）")
            elif rule_code == '5.12.3': return _clean(f"避免使用buffer类型的端口（{rule_code}）")
        # VHDL建议准则
        elif rule_code == '5.1.3': return _clean(f"例化时未使用输出端口宜采用open说明（{rule_code}）")
        elif rule_code == '5.2.4': return _clean(f"顶层宜只进行模块例化（{rule_code}）")
        elif rule_code == '5.2.5': return _clean(f"设计中不宜存在多余代码或不可达分支（{rule_code}）")
        elif rule_code == '5.2.6': return _clean(f"设计中不宜产生非预期锁存器（{rule_code}）")
        elif rule_code == '5.2.7': return _clean(f"一个文件宜对应一个设计模块（{rule_code}）")
        elif rule_code == '5.2.8': return _clean(f"建议按不同设计目标进行模块划分（{rule_code}）")
        elif rule_code == '5.2.9': return _clean(f"宜将相关组合逻辑和可复用逻辑划分在同一模块（{rule_code}）")
        elif rule_code == '5.2.10': return _clean(f"每个文件最多一个实体（{rule_code}）")
        elif rule_code == '5.2.11': return _clean(f"VHDL文件应包含std_logic_1164标准包（{rule_code}）")
        elif rule_code == '5.2.12': return _clean(f"避免双向端口连接到单向端口（{rule_code}）")
        elif rule_code == '5.2.13': return _clean(f"组合逻辑内避免反馈电路（{rule_code}）")
        elif rule_code == '5.4.2': return _clean(f"避免出现多余信号（{rule_code}）")
        elif rule_code == '5.4.5': return _clean(f"一维对象声明为降序方式（{rule_code}）")
        elif rule_code == '5.4.6': return _clean(f"避免固定值指定总线范围（{rule_code}）")
        elif rule_code == '5.4.7': return _clean(f"宜按IN/OUT/INOUT顺序定义端口（{rule_code}）")
        elif rule_code == '5.4.8': return _clean(f"不使用bit/bit_vector数据类型（{rule_code}）")
        elif rule_code == '5.4.9': return _clean(f"设计中不包含枚举的enum_encoding属性（{rule_code}）")
        elif rule_code == '5.4.10': return _clean(f"STD_LOGIC_VECTOR数据类型的每个对象（{rule_code}）")
        elif rule_code == '5.4.11': return _clean(f"一维信号有从0索引开始的范围（{rule_code}）")
        elif rule_code == '5.4.12': return _clean(f"整数数据类型对象应有范围限制（{rule_code}）")
        elif rule_code == '5.5.5': return _clean(f"时钟命名宜与一般端口名相区别（{rule_code}）")
        elif rule_code == '5.5.6': return _clean(f"命名准则（{rule_code}）")
        elif rule_code == '5.5.7': return _clean(f"跨模块层次信号应使用同样命名（{rule_code}）")
        elif rule_code == '5.5.8': return _clean(f"避免使用verilog关键字（{rule_code}）")
        elif rule_code == '5.6.9': return _clean(f"三态节点使能端和输入端不宜被同一信号源驱动（{rule_code}）")
        elif rule_code == '5.6.10': return _clean(f"不宜使用组合逻辑输出控制三态门（{rule_code}）")
        elif rule_code == '5.6.11': return _clean(f"避免未寄存的实体输出（{rule_code}）")
        elif rule_code == '5.6.12': return _clean(f"不能使用Z进行赋值（{rule_code}）")
        elif rule_code == '5.6.13': return _clean(f"不允许延迟赋值（{rule_code}）")
        elif rule_code == '5.6.14': return _clean(f"同一线型信号没有多个三态门（{rule_code}）")
        elif rule_code == '5.6.15': return _clean(f"不能与Z/U/H/L/-/W/X进行比较（{rule_code}）")
        elif rule_code == '5.8.6': return _clean(f"避免进程中出现空语句（{rule_code}）")
        elif rule_code == '5.8.7': return _clean(f"多级if else应重视优先级顺序对性能的影响（{rule_code}）")
        elif rule_code == '5.9.7': return _clean(f"不宜使用组合逻辑产生的时钟（{rule_code}）")
        elif rule_code == '5.9.8': return _clean(f"全局时钟宜使用全局时钟布线资源（{rule_code}）")
        elif rule_code == '5.9.9': return _clean(f"不宜使用行波时钟（{rule_code}）")
        elif rule_code == '5.9.10': return _clean(f"应尽量减少时钟域最好只使用一个（{rule_code}）")
        elif rule_code == '5.9.11': return _clean(f"时钟信号源不宜驱动不同时钟沿触发的寄存器（{rule_code}）")
        elif rule_code == '5.9.12': return _clean(f"避免在时钟路径上插入反相器或缓冲器（{rule_code}）")
        elif rule_code == '5.9.13': return _clean(f"避免将触发器输出作为时钟资源（{rule_code}）")
        elif rule_code == '5.9.14': return _clean(f"避免将时钟作为输入数据使用（{rule_code}）")
        elif rule_code == '5.10.5': return _clean(f"应使用复位操作对寄存器初始化（{rule_code}）")
        elif rule_code == '5.10.6': return _clean(f"同一时刻宜使用同一复位域对所有模块复位（{rule_code}）")
        elif rule_code == '5.10.7': return _clean(f"宜将系统复位信号设置为全局网络（{rule_code}）")
        elif rule_code == '5.10.8': return _clean(f"不宜用时钟信号做复位置位操作（{rule_code}）")
        elif rule_code == '5.10.9': return _clean(f"同步复位时外部复位信号宜使用两级寄存器同步（{rule_code}）")
        elif rule_code == '5.10.10': return _clean(f"同一复位信号宜使用唯一的有效电平（{rule_code}）")
        elif rule_code == '5.10.11': return _clean(f"组合逻辑作为复位信号应该被同步（{rule_code}）")
        elif rule_code == '5.10.12': return _clean(f"避免异步复位置位被组合逻辑驱动（{rule_code}）")
        elif rule_code == '5.10.13': return _clean(f"单时钟process不能使用多个异步复位（{rule_code}）")
        elif rule_code == '5.10.14': return _clean(f"异步复位置位仅连接到触发器模块异步复位置位端口（{rule_code}）")
        elif rule_code == '5.11.5': return _clean(f"建议使用三段式状态机（{rule_code}）")
        elif rule_code == '5.11.6': return _clean(f"建议使用枚举类型声明状态机（{rule_code}）")
        elif rule_code == '5.11.7': return _clean(f"状态机中状态数量及编码方式要求（{rule_code}）")
        elif rule_code == '5.12.4': return _clean(f"应在约束文件中对每个时钟定义并添加周期约束（{rule_code}）")
        elif rule_code == '5.13.1': return _clean(f"文件开头应添加注释（{rule_code}）")
        elif rule_code == '5.13.2': return _clean(f"端口定义的输入输出信号应添加注释说明（{rule_code}）")
        elif rule_code == '5.13.3': return _clean(f"内部信号变量应添加注释说明（{rule_code}）")
        elif rule_code == '5.13.4': return _clean(f"避免未注释的结束语句避免未注释的分隔信号声明（{rule_code}）")
        elif rule_code == '5.14.1': return _clean(f"应使用空行进行适当分隔（{rule_code}）")
        elif rule_code == '5.14.2': return _clean(f"程序编写时应注意对齐和缩进（{rule_code}）")
        elif rule_code == '5.14.3': return _clean(f"应使用空格进行适当分隔（{rule_code}）")
        elif rule_code == '5.14.4': return _clean(f"其他编码格式要求（{rule_code}）")
    
    # 3) Verilog建议准则
    if language == 'Verilog' and rule_code.startswith('A-'):
        verilog_advisory_map = {
            'A-1-1': f"未采用标准文件头（{rule_code}）",
            'A-1-2': f"同层次语句未左端对齐或嵌套缩进不规范（{rule_code}）",
            'A-1-3': f"端口信号变量定义未左端对齐（{rule_code}）",
            'A-1-4': f"代码行字符数超过80个（{rule_code}）",
            'A-1-5': f"端口顺序未按时钟复位输入输出双向排列（{rule_code}）",
            'A-1-6': f"同一行描述了多个赋值语句（{rule_code}）",
            'A-1-7': f"一行中对多个I/O端口进行了说明（{rule_code}）",
            'A-1-8': f"代码注释率低于20%（{rule_code}）",
            'A-1-9': f"使用了Tabs符（{rule_code}）",
            'A-1-10': f"输入输出端口声明混杂未分组（{rule_code}）",
            'A-2-1': f"文件名与module名不一致（{rule_code}）",
            'A-2-2': f"标识符命名长度不在2到32个字符之间（{rule_code}）",
            'A-2-3': f"时钟信号命名未采用clk_x或Clk_X格式（{rule_code}）",
            'A-2-4': f"复位信号命名未采用Rst_X/rst_x格式（{rule_code}）",
            'A-2-5': f"常量变量命名风格不符合规范（{rule_code}）",
            'A-2-6': f"使用了defparam语句（{rule_code}）",
            'A-2-7': f"不同module使用了相同参数名（{rule_code}）",
            'A-2-8': f"存在冗余的端口或内部信号（{rule_code}）",
            'A-2-9': f"一维对象范围定义未按降序定义（{rule_code}）",
            'A-2-10': f"使用硬值指定总线范围未使用参数（{rule_code}）",
            'A-3-1': f"顶层模块包含胶合逻辑（{rule_code}）",
            'A-3-2': f"上层模块包含了逻辑而非仅例化（{rule_code}）",
            'A-3-3': f"模块未使用组合逻辑输入寄存器输出（{rule_code}）",
            'A-4-1': f"同时使用了时钟上升沿和下降沿（{rule_code}）",
            'A-4-2': f"时钟产生电路未创建独立模块（{rule_code}）",
            'A-4-3': f"使用了门控时钟（{rule_code}）",
            'A-4-4': f"使用了多个时钟域（{rule_code}）",
            'A-5-1': f"复位产生电路未创建独立模块（{rule_code}）",
            'A-5-2': f"异步复位线路中插入了逻辑运算（{rule_code}）",
            'A-5-3': f"使用内部信号作为异步复位信号（{rule_code}）",
            'A-5-4': f"同时使用了异步置位和异步复位信号（{rule_code}）",
            'A-5-5': f"同一always中使用了多个复位信号（{rule_code}）",
            'A-5-6': f"使用了多个异步复位信号触发（{rule_code}）",
            'A-7-1': f"锁存器与组合逻辑未分开描述（{rule_code}）",
            'A-8-1': f"双向端口直接连接了输入或输出端口（{rule_code}）",
            'A-8-2': f"同一线网有多个三态缓冲区（{rule_code}）",
            'A-9-1': f"向量运算中使用了逻辑运算符（{rule_code}）",
            'A-9-2': f"parameter或常数未指定进制和位宽（{rule_code}）",
            'A-10-1': f"赋值为'Z'（{rule_code}）",
            'A-10-2': f"存在空语句块（{rule_code}）",
            'A-11-1': f"case分支语句存在重叠（{rule_code}）",
            'A-11-2': f"使用了casex或casez语句（{rule_code}）",
            'A-11-3': f"default分支出现了包含x的值（{rule_code}）",
            'A-11-4': f"if或条件运算符的条件表达式为向量（{rule_code}）",
            'A-11-5': f"组合逻辑if语句未以else结尾（{rule_code}）",
            'A-12-1': f"repeat表达式中使用了变量（{rule_code}）",
            'A-13-1': f"数组索引使用了表达式而非简单信号（{rule_code}）",
            'A-14-1': f"单个状态机状态数超过40个（{rule_code}）",
            'A-14-2': f"状态转换时改变位数过多（{rule_code}）",
            'A-16-1': f"使用了full_case属性（{rule_code}）",
        }
        if rule_code in verilog_advisory_map:
            return _clean(verilog_advisory_map[rule_code])
    
    # 4) 兜底：以规则内容为核心
    if len(core) > 80:
        core = core[:80] + '...'
    return _clean(f"{core}（{rule_code}）")


def build_impact_analysis(rule_code: str, rule_content: str, language: str, rule_type: str) -> str:
    """根据规则内容与类型生成影响分析。优先按具体 rule_code 定制。"""
    text = rule_content or ''
    mandatory = (rule_type == 'mandatory') or rule_code.startswith('R-')
    # 1) 精确映射
    impact_map = {
        'R-2-1': '不合规命名会降低可读性并增加命名冲突概率，影响团队协作与自动化检查。',
        'R-2-2': '连续或尾随下划线易引发解析与工具链误判，影响可读性和一致性。',
        'R-2-3': '与关键字同名会导致语义歧义或编译失败，风险较高。',
        'R-2-4': '使用电源/地保留名可能与版图/电气设计混淆，带来工程沟通与实现风险。',
        'R-2-5': '单文件多 module 破坏层次清晰度，影响综合、仿真与维护。',
        'R-2-6': '仅靠大小写区分易造成代码评审与集成时的误用。',
        'R-2-7': '绝对路径造成项目迁移与CI环境不可移植问题。',
        'R-2-8': '非常规类型使用可能与工具链不兼容，带来综合/仿真不一致风险。',
        'R-2-9': '位置映射可读性差且易错，影响模块复用与检查。',
        'R-2-10': '顶层输入悬空会引发不确定输入，导致不稳定行为。',
        'R-2-11': '多处 define 导致宏定义不一致与难以追踪的问题。',
        'R-3-1': '端口表达式使接口语义不清，增加综合/仿真差异风险。',
        'R-3-2': '不规范端口类型影响接口清晰与工具识别。',
        'R-3-3': '深度嵌套控制降低可读性并易产生时序与覆盖率问题。',
        'R-4-1': '时钟管脚驱动不规范，可能引入毛刺与计时违例。',
        'R-4-2': '时钟误连导致时序不可控，严重影响系统稳定性。',
        'R-4-3': '组合输出作为时钟会引入毛刺与不可预期抖动。',
        'R-5-1': '异步置位/复位误连可能导致不可预期复位行为。',
        'R-5-2': '混用异步/同步复位造成复位时序难以保证，增大失效风险。',
        'R-5-3': '竞争冒险的复位来源可能在边沿处产生隐患，导致偶发故障。',
        'R-5-4': '不使用专用时钟单元可能导致高扇出信号延迟不一致，影响FPGA稳定性。',
        'R-5-5': '非SRAM型FPGA未初始化导致上电状态不确定，系统可能异常。',
        'R-6-1': '混合有/无复位触发器导致综合结果不可预测，影响电路一致性。',
        'R-6-2': '触发器未赋初值可能导致复位后状态不确定，影响系统可靠性。',
        'R-6-3': '复位条件不一致可能导致复位逻辑错误，造成系统失效。',
        'R-6-4': '触发器作为时钟会产生毛刺与时序问题，严重影响系统稳定性。',
        'R-7-1': '锁存器环路导致不可预测的振荡与亚稳定状态，影响系统可靠性。',
        'R-7-2': '使用逻辑门描述锁存器导致综合不一致，产生不可预测问题。',
        'R-8-1': '组合逻辑作为三态使能端可能引入毛刺，导致总线冲突。',
        'R-8-2': '内部三态在FPGA中难以实现且可能导致综合失败或总线冲突。',
        'R-9-1': '关系操作符位宽不一致可能导致比较结果错误，影响逻辑正确性。',
        'R-9-2': '位操作符位宽不一致可能导致数据丢失或错误，影响系统功能。',
        'R-9-3': '有/无符号数混用导致运算结果不确定，可能产生意外的符号扩展。',
        'R-9-4': '使用X/Z值进行关系比较导致仿真与综合结果不一致，影响系统可靠性。',
        'R-9-5': '算术操作中包含X/Z值导致结果不确定，产生仿真与综合差异。',
        'R-9-6': '位宽不一致可能导致数据截断或补齿错误，影响数据准确性。',
        'R-9-7': '运算溢出可能导致数据丢失与逻辑错误，严重影响系统正确性。',
        'R-10-1': '端口位宽不匹配导致数据丢失或错误，影响模块间通信。',
        'R-10-2': '赋值位宽不一致可能导致数据截断或错误扩展，影响逻辑正确性。',
        'R-10-3': '组合逻辑使用非阻塞赋值可能导致竞争冒险，产生仿真与综合不一致。',
        'R-10-4': '时序逻辑使用阻塞赋值可能导致时序错误，产生意外的组合逻辑。',
        'R-10-5': '重复赋值导致逻辑冲突与不确定性，综合结果不可预测。',
        'R-10-6': '延时语句不可综合，导致仿真与综合结果完全不同，严重影响系统。',
        'R-11-1': '缺少default分支可能产生锁存器，导致综合与仿真不一致。',
        'R-11-2': '控制表达式为固定值使case语句无意义，可能存在逻辑错误。',
        'R-11-3': '分支表达式超出范围或位宽不一致导致匹配错误，影响逻辑正确性。',
        'R-11-4': '使用x/z值导致仿真与综合行为不一致，产生不可预测的结果。',
        'R-11-5': '使用|或||连接敏感信号可能产生毛刺，影响时序稳定性。',
        'R-11-6': '使用变量或逻辑运算作case分支可能产生锁存器，影响综合结果。',
        'R-11-7': '遗失赋值导致锁存器产生，造成仿真与综合不一致。',
        'R-11-8': '敏感列表与if条件不匹配可能产生锁存器或竞争冒险。',
        'R-11-9': '异步always中遗漏赋值可能导致复位不完全，影响系统初始化。',
        'R-12-1': '循环变量不为常数或被修改导致综合失败或产生意外的大量逻辑。',
        'R-12-2': '对其他变量运算可能导致综合失败或产生不可预测的结果。',
        'R-12-3': '复位与逻辑混在同一循环影响可读性，可能导致综合错误。',
        'R-12-4': '循环不满足条件导致代码无法执行，可能存在逻辑错误。',
        'R-12-5': '递归函数不可综合，导致综合失败。',
        'R-13-1': 'task中使用时序控制不可综合，导致综合失败。',
        'R-13-2': 'initial语句不可综合，仅用于仿真，在硬件中无法实现。',
        'R-13-3': 'function中使用非阻塞赋值可能导致综合错误或产生意外的时序逻辑。',
        'R-13-4': '对全局信号赋值导致多驱动冲突，影响系统稳定性。',
        'R-13-5': '位宽不一致可能导致数据丢失或错误，影响函数正确性。',
        'R-13-6': '位宽不一致可能导致数据丢失或错误，影响task正确性。',
        'R-13-7': '组合逻辑反馈可能导致振荡或亚稳定状态，严重影响系统可靠性。',
        'R-13-8': '数组越界可能导致访问错误数据或综合失败，严重影响系统。',
        'R-13-9': '敏感信号不完整可能产生锁存器或竞争冒险，影响综合结果。',
        'R-14-1': '死锁或不可达状态导致状态机功能异常，可能造成系统卡死。',
        'R-14-2': 'default未重置寄存器导致非法状态下行为不确定，影响系统可靠性。',
        'R-14-3': '未设置初始状态导致上电后状态机状态不确定，影响系统启动。',
        'R-15-1': '异步时钟区域中组合逻辑可能导致亚稳态，产生数据错误。',
        'R-15-2': '同步寄存器间组合逻辑可能导致亚稳态传播，影响跨时钟域可靠性。',
        'R-15-3': '反馈环路可能导致振荡或亚稳态问题，影响跨时钟域稳定性。',
        'R-16-1': '综合工具改变复位属性导致代码与综合结果不一致，影响可预测性。',
        'R-16-2': '非safe模式可能导致状态机出现非法状态，影响系统稳定性。',
        # Verilog建议准则影响分析
        'A-1-1': '缺少标准文件头降低代码可追溯性，不利于版本管理和团队协作。',
        'A-1-2': '代码对齐不规范降低可读性，增加代码审查和维护难度。',
        'A-1-3': '端口信号定义不对齐影响代码整洁度，降低可读性。',
        'A-1-4': '行字符数过多影响代码阅读，在某些编辑器中需要横向滚动。',
        'A-1-5': '端口顺序不规范降低接口清晰度，不利于快速理解模块功能。',
        'A-1-6': '同一行多个赋值语句降低可读性，增加调试难度。',
        'A-1-7': '一行多个端口说明降低接口清晰度，容易遗漏端口含义。',
        'A-1-8': '注释率低降低代码可维护性，增加后续理解和修改成本。',
        'A-1-9': 'Tabs符导致不同编辑器显示不一致，影响代码格式统一性。',
        'A-1-10': '端口声明混乱降低接口清晰度，不利于理解信号方向。',
        'A-2-1': '文件名与模块名不一致增加项目管理难度，不利于文件查找。',
        'A-2-2': '命名长度不合理影响代码可读性，过短难懂过长冗余。',
        'A-2-3': '时钟命名不规范降低信号识别度，不利于时序分析。',
        'A-2-4': '复位命名不规范容易混淆复位极性，增加设计错误风险。',
        'A-2-5': '常量变量命名风格不统一降低代码一致性和可读性。',
        'A-2-6': 'defparam语句破坏参数封装性，影响模块复用和维护。',
        'A-2-7': '不同模块使用相同参数名容易混淆，影响参数管理。',
        'A-2-8': '冗余端口或信号增加代码复杂度，影响综合效率。',
        'A-2-9': '范围定义顺序不统一降低代码一致性，容易产生混淆。',
        'A-2-10': '使用硬值指定范围降低代码灵活性，不利于参数化设计。',
        'A-3-1': '顶层模块包含胶合逻辑降低层次清晰度，影响模块复用。',
        'A-3-2': '上层模块包含逻辑降低层次结构清晰度，不利于维护。',
        'A-3-3': '输入输出不规范影响流水线设计，可能产生时序问题。',
        'A-4-1': '同时使用双沿可能产生时序问题，增加设计复杂度。',
        'A-4-2': '时钟电路未独立降低模块清晰度，不利于时钟管理。',
        'A-4-3': '门控时钟可能引入毛刺，增加时序分析和验证难度。',
        'A-4-4': '多时钟域增加CDC设计复杂度，提高亚稳态风险。',
        'A-5-1': '复位电路未独立降低模块清晰度，不利于复位管理。',
        'A-5-2': '异步复位线路中插入逻辑可能引入毛刺，影响复位可靠性。',
        'A-5-3': '内部信号作为异步复位可能不稳定，影响复位可靠性。',
        'A-5-4': '同时使用置位复位信号增加设计复杂度，容易产生冲突。',
        'A-5-5': '多个复位信号增加复位逻辑复杂度，降低可维护性。',
        'A-5-6': '多个异步复位触发增加复位时序复杂度，影响可靠性。',
        'A-7-1': '锁存器与组合逻辑混合降低代码清晰度，影响综合优化。',
        'A-8-1': '双向端口直连可能导致信号冲突，影响电路功能。',
        'A-8-2': '多个三态缓冲区可能导致总线冲突，影响信号完整性。',
        'A-9-1': '向量运算使用逻辑运算符可能产生意外结果，影响功能正确性。',
        'A-9-2': '未指定进制和位宽降低代码可读性，可能产生位宽误解。',
        'A-10-1': '赋值为Z降低代码可读性，在非三态场景可能产生混淆。',
        'A-10-2': '空语句块降低代码质量，可能是未完成的逻辑或遗留代码。',
        'A-11-1': 'case分支重叠导致优先级不明确，影响综合结果可预测性。',
        'A-11-2': 'casex/casez语句可能产生意外匹配，降低代码安全性。',
        'A-11-3': 'default分支包含x值降低代码可读性，影响调试。',
        'A-11-4': '条件表达式为向量降低代码清晰度，可能产生意外行为。',
        'A-11-5': '组合逻辑if缺少else可能产生锁存器，影响综合结果。',
        'A-12-1': 'repeat使用变量可能导致综合失败或产生意外逻辑。',
        'A-13-1': '数组索引使用表达式降低代码可读性，增加综合复杂度。',
        'A-14-1': '状态机状态数过多增加设计复杂度，影响综合和时序。',
        'A-14-2': '状态转换改变位数多增加功耗，可能影响时序性能。',
        'A-16-1': 'full_case属性可能导致仿真与综合不一致，影响验证准确性。',
        # VHDL强制准则影响分析
        '5.1.1': '未使用名称映射例化易在端口增删后错连，导致接口功能异常与调试困难。',
        '5.1.2': '输入端口悬空会引入高阻或X态，导致仿真与硬件行为不可预测。',
        '5.2.1': '模块缺少必要端口限制外部交互，可能无法接入系统总线或测试平台。',
        '5.2.2': '输出信号回驱内部逻辑会造成双驱动，易触发竞争并破坏信号完整性。',
        '5.2.3': '内部三态逻辑难以综合，在FPGA结构中会引起资源浪费及不确定状态。',
        '5.3.1': '敏感列表缺失信号会生成隐式锁存器，使进程对输入变化响应异常。',
        '5.4.1': '未声明位宽导致默认范围出错，影响硬件资源映射与仿真一致性。',
        '5.4.3': '条件表达式含X或Z会被工具误判，使逻辑覆盖不到所有情况。',
        '5.4.4': '多个事件控制段破坏同步假设，可能导致工艺映射失败或仿真差异。',
        '5.5.1': '标识符与关键字冲突导致编译器解析混乱，可能直接拒绝综合。',
        '5.5.2': '不同对象同名削弱层次隔离，容易误连信号或覆盖变量。',
        '5.5.3': '命名不规范阻碍代码审计和自动化工具识别，增加维护成本。',
        '5.5.4': '仅靠大小写区分名称在大小写不敏感工具中会失效，触发严重混淆。',
        '5.6.1': '信号赋值后未被使用意味着逻辑漂浮，浪费资源并隐藏缺陷。',
        '5.6.2': '运算两端位宽不等会产生隐式扩展，造成数值精度或符号错误。',
        '5.6.3': '常量右侧非固定整型会让推导失败，导致合成结果不确定。',
        '5.6.4': '混合整数、实数与无符号类型会生成复杂转换，难以保证语义一致。',
        '5.6.5': '有符号与无符号混用改变算术比较结果，直接破坏算法正确性。',
        '5.6.6': '单向信号多驱动产生冲突，最终输出不确定或被工具强制裁剪。',
        '5.6.7': '同源信号驱动多个异步端会生成不受控的复位或置位路径。',
        '5.6.8': '信号赋值包含波形将被推迟执行，导致仿真与硬件行为严重偏差。',
        '5.7.1': '循环终止条件可变会阻碍综合优化，可能产生不可控的迭代次数。',
        '5.7.2': '循环内修改变量使迭代边界动态变化，工具难以静态展开。',
        '5.7.3': 'while条件固定意味着循环永远执行或完全跳过，暗示逻辑缺陷。',
        '5.8.1': 'case表达式固定常量导致分支永不可达，掩盖逻辑错误。',
        '5.8.2': '分支使用变量或表达式会触发隐式优先级，增加锁存器风险。',
        '5.8.3': '缺少when others使非法输入无出口，容易产生锁存器或X态。',
        '5.8.4': '组合if缺else导致信号保持旧值，综合器自动插入锁存器。',
        '5.8.5': 'case分支未覆盖所有赋值会产生不完全指定，生成隐式寄存器。',
        '5.9.1': '时钟汇聚引入竞争路径，破坏全局时钟树平衡，触发时序违例。',
        '5.9.2': '时钟驱动多路选择器控制端会产生毛刺，危及数据路径稳定。',
        '5.9.3': '门控时钟在FPGA中引发不受控脉冲，导致不可恢复的亚稳态。',
        '5.9.4': '单进程多时钟破坏同步原则，使仿真与硬件行为无法匹配。',
        '5.9.5': '跨时钟域未同步会直接把亚稳态传入逻辑，威胁系统可靠性。',
        '5.9.6': '把时钟当数据使用会生成不可预测的组合电路，极易违反时序。',
        '5.10.1': '寄存器输出反馈复位端会形成环路，导致复位期间出现异常脉冲。',
        '5.10.2': '复位与置位来自同源使寄存器状态不确定，难以验证稳定性。',
        '5.10.3': '异步复位不同步释放将产生局部偏差，引发跨模块时序问题。',
        '5.10.4': '复位端口悬空导致寄存器初始状态随机，系统上电行为不可控。',
        '5.11.1': '无效状态未处理会使状态机陷入死循环，导致系统挂起。',
        '5.11.2': '综合属性设置不当会让状态机编码混乱，降低面积与时序性能。',
        '5.11.3': '状态机未初始化导致上电后进入非法状态，影响启动可靠性。',
        '5.11.4': '不可达状态占用资源且掩盖设计缺陷，影响代码质量与可测性。',
        '5.12.1': '不可综合代码会导致综合失败或被忽略，造成仿真与硬件不一致。',
        '5.12.2': '约束冲突使工具无法收敛时序，导致布局布线失败或性能下降。',
        '5.12.3': 'buffer端口在FPGA中映射困难，可能导致综合警告或连接错误。',
        # VHDL建议准则影响分析
        '5.1.3': '未使用输出端口未标记open会降低接口清晰度，影响代码可读性。',
        '5.2.4': '顶层包含逻辑降低层次清晰度，不利于模块复用与团队协作。',
        '5.2.5': '多余代码或不可达分支浪费资源，增加维护负担并掩盖潜在错误。',
        '5.2.6': '非预期锁存器会引入时序问题，增加调试难度并影响综合质量。',
        '5.2.7': '多模块共享文件降低可维护性，不利于版本控制与并行开发。',
        '5.2.8': '模块划分不合理会导致接口复杂，增加集成难度与测试成本。',
        '5.2.9': '逻辑划分不当影响复用性，降低设计效率与代码质量。',
        '5.2.10': '多实体共存降低文件清晰度，容易混淆模块边界与职责。',
        '5.2.11': '缺少标准包会导致类型不兼容，影响工具链移植性。',
        '5.2.12': '双向与单向端口直连可能产生驱动冲突，影响信号完整性。',
        '5.2.13': '组合逻辑反馈会产生振荡或亚稳态，严重影响电路可靠性。',
        '5.4.2': '多余信号增加资源消耗，降低代码清晰度与综合效率。',
        '5.4.5': '范围定义不统一降低代码一致性，容易在位操作时产生混淆。',
        '5.4.6': '硬编码范围降低参数化能力，不利于设计复用与扩展。',
        '5.4.7': '端口顺序不规范降低接口可读性，增加理解与集成成本。',
        '5.4.8': 'bit类型功能受限且不兼容std_logic，影响工具链互操作性。',
        '5.4.9': 'enum_encoding属性可能与综合工具冲突，影响状态机编码控制。',
        '5.4.10': 'STD_LOGIC_VECTOR对象定义不规范影响位操作一致性与可读性。',
        '5.4.11': '索引起始不统一降低代码一致性，容易在数组操作时产生错误。',
        '5.4.12': '整数类型无范围限制会占用过多位宽，浪费资源并影响时序。',
        '5.5.5': '时钟命名不明确降低信号识别度，不利于时序分析与约束设置。',
        '5.5.6': '命名不规范降低代码可读性，增加团队协作与代码审查成本。',
        '5.5.7': '跨层次信号命名不一致增加追踪难度，影响调试效率。',
        '5.5.8': '使用Verilog关键字会在混合语言项目中产生冲突，影响互操作性。',
        '5.6.9': '三态节点同源驱动可能产生竞争，影响总线稳定性。',
        '5.6.10': '组合逻辑控制三态门可能引入毛刺，导致总线冲突。',
        '5.6.11': '未寄存输出会增加组合路径延迟，影响时序收敛与接口稳定性。',
        '5.6.12': '使用Z赋值在非三态场景会产生混淆，降低代码清晰度。',
        '5.6.13': '延迟赋值不可综合，导致仿真与硬件行为完全不同。',
        '5.6.14': '多三态驱动同一线网会产生总线冲突，影响信号完整性。',
        '5.6.15': '与不确定值比较会导致仿真与综合不一致，影响验证准确性。',
        '5.8.6': '空语句降低代码质量，可能是未完成逻辑或遗留代码。',
        '5.8.7': 'if优先级不当会影响时序性能，增加关键路径延迟。',
        '5.9.7': '组合逻辑产生时钟会引入毛刺，严重影响时序稳定性。',
        '5.9.8': '未使用全局时钟资源会增加时钟偏斜，影响时序裕量。',
        '5.9.9': '行波时钟会产生严重偏斜，导致时序违例与功能错误。',
        '5.9.10': '多时钟域增加CDC复杂度，提高亚稳态风险与验证难度。',
        '5.9.11': '混用时钟沿会产生时序问题，增加约束复杂度。',
        '5.9.12': '时钟路径插入逻辑会引入延迟与毛刺，影响时钟质量。',
        '5.9.13': '触发器输出作时钟会产生毛刺，严重影响下游逻辑稳定性。',
        '5.9.14': '时钟作数据使用会产生不可预测的组合路径，违反时序约束。',
        '5.10.5': '未使用复位初始化会导致上电状态不确定，影响系统可靠性。',
        '5.10.6': '复位域不统一会产生时序偏差，影响模块间同步。',
        '5.10.7': '复位信号未使用全局网络会增加偏斜，影响复位可靠性。',
        '5.10.8': '时钟信号做复位会产生窄脉冲，可能导致复位不完全。',
        '5.10.9': '外部复位未同步会引入亚稳态，影响复位可靠性。',
        '5.10.10': '复位电平不统一增加设计复杂度，容易产生逻辑错误。',
        '5.10.11': '组合逻辑复位未同步会引入毛刺，影响复位稳定性。',
        '5.10.12': '组合逻辑驱动异步复位会引入毛刺，导致误复位。',
        '5.10.13': '多异步复位会产生竞争，影响复位时序可预测性。',
        '5.10.14': '异步复位误连会导致非预期复位行为，影响系统稳定性。',
        '5.11.5': '非三段式状态机降低代码清晰度，不利于维护与优化。',
        '5.11.6': '非枚举类型状态机降低可读性，增加状态管理难度。',
        '5.11.7': '状态编码不当会影响面积与时序性能，降低综合质量。',
        '5.12.4': '缺少时钟约束会导致时序分析不准确，影响设计可靠性。',
        '5.13.1': '缺少文件头降低代码可追溯性，不利于版本管理。',
        '5.13.2': '端口缺少注释降低接口清晰度，增加理解成本。',
        '5.13.3': '信号缺少注释降低代码可维护性，增加调试难度。',
        '5.13.4': '缺少注释降低代码可读性，影响团队协作效率。',
        '5.14.1': '缺少空行分隔降低代码可读性，影响代码结构清晰度。',
        '5.14.2': '对齐缩进不规范降低代码可读性，增加代码审查难度。',
        '5.14.3': '缺少空格分隔降低代码可读性，影响代码美观度。',
        '5.14.4': '编码格式不规范降低代码一致性，影响团队协作效率。',
    }
    if rule_code in impact_map:
        return impact_map[rule_code]
    # 兜底：未匹配规则返回通用描述
    return f"违反{language} {rule_type}编码规范，可能影响代码质量、可维护性或系统可靠性。"


def build_fix_suggestion(rule_code: str, rule_content: str, language: str, rule_type: str) -> str:
    """根据规则生成修改意见。优先按具体 rule_code 定制。"""
    text = rule_content or ''
    # 1) 精确映射
    fix_map = {
        'R-2-1': '将所有标识符调整为以字母开头，后续才可接数字/下划线，避免工具链警告/错误。',
        'R-2-2': '统一命名风格，移除连续下划线与尾部下划线，使用清晰的下划线分隔。',
        'R-2-3': '检查并重命名与语言关键字冲突的标识符，避免语义冲突。',
        'R-2-4': '避免使用电源/地等保留名，采用具备业务含义的中性命名。',
        'R-2-5': '拆分文件：保证每个源文件只定义一个 module，提升可维护性。',
        'R-2-6': '统一大小写规范，避免仅以大小写区分不同标识符。',
        'R-2-7': '将 include/引用路径改为相对路径，便于CI/CD与跨环境构建。',
        'R-2-8': '限定在允许类型集合内使用（reg/wire/integer/tri/genvar/localparam/parameter）。',
        'R-2-9': '将位置映射改为端口名映射（.port(signal)）以提升可读性与可靠性。',
        'R-2-10': '为顶层输入增加上拉/下拉或驱动源，避免悬空导致不确定行为。',
        'R-2-11': '收敛宏定义位置，集中在单一入口文件，删除重复/分散的 define。',
        'R-3-1': '将端口表达式提至模块内部信号，保持端口连接为纯信号。',
        'R-3-2': '调整顶层端口类型为 reg 或 wire，与工具与规范一致。',
        'R-3-3': '重构深层嵌套控制为平坦结构（如提前返回/拆函数/拆模块）。',
        'R-4-1': '使用专用时钟资源或时钟树，不要用寄存器输出驱动其他寄存器的时钟。',
        'R-4-2': '仅将时钟连接至时钟管脚；其他用途使用使能或同步逻辑。',
        'R-4-3': '禁止用组合输出作为时钟，必要时引入PLL/BUFG等合规时钟资源。',
        'R-5-1': '确保异步置位/复位仅连接至合法复位端口。',
        'R-5-2': '统一复位方案为异步或同步之一，并在全局保持一致。',
        'R-5-3': '移除具有竞争冒险的组合复位路径，引入同步与去抖措施。',
        'R-5-4': '使用BUFG/BUFGCE等专用时钟资源驱动高扇出信号，确保时钟质量。',
        'R-5-5': '在非SRAM型FPGA中为所有寄存器添加初始值（如通过initial或默认值）。',
        'R-6-1': '在同一always块中统一使用有复位或无复位触发器，不要混用。',
        'R-6-2': '在复位分支中为所有触发器提供明确的初始值，避免X态。',
        'R-6-3': '确保复位信号的触发条件（如posedge/negedge）与进入条件完全一致。',
        'R-6-4': '避免将触发器输出作为时钟使用，必要时引入时钟管理模块。',
        'R-7-1': '检查并消除锁存器反馈环路，重构为寄存器或纯组合逻辑。',
        'R-7-2': '使用always块规范描述锁存器，避免使用门级描述。',
        'R-8-1': '将三态使能端改为寄存器输出，避免组合逻辑直接驱动。',
        'R-8-2': '将内部三态改为多路选择器或寄存器实现，避免使用inout类型。',
        'R-9-1': '统一关系操作符两端信号位宽，必要时进行显式扩展或截断。',
        'R-9-2': '统一位操作符两端信号位宽，确保数据完整性。',
        'R-9-3': '避免有/无符号数混用，使用$signed/$unsigned显式转换或统一类型。',
        'R-9-4': '将X/Z值替换为明确的0/1值，避免在关系表达式中使用不确定态。',
        'R-9-5': '将X/Z值替换为明确的0/1值，避免在算术运算中使用不确定态。',
        'R-9-6': '确保数值声明的位宽与实际位宽一致，如8\'d255而非4\'d255。',
        'R-9-7': '增加位宽或使用饱和运算，避免算术运算结果溢出。',
        'R-10-1': '调整模块端口位宽或信号位宽，确保例化时位宽完全匹配。',
        'R-10-2': '调整赋值表达式左右值位宽，必要时进行显式扩展或截断。',
        'R-10-3': '在组合逻辑always块中使用阻塞赋值（=），避免非阻塞赋值（<=）。',
        'R-10-4': '在时序逻辑always块中使用非阻塞赋值（<=），避免阻塞赋值（=）。',
        'R-10-5': '检查并消除同一条件下的重复赋值，保证每个信号只被赋值一次。',
        'R-10-6': '移除所有#延时语句，改用时序逻辑或状态机实现延时功能。',
        'R-11-1': '为case语句添加default分支，并在其中对所有信号赋值。',
        'R-11-2': '将case控制表达式改为变量或信号，避免使用常量。',
        'R-11-3': '确保case分支表达式在控制表达式范围内，且位宽一致。',
        'R-11-4': '避免在if/case条件中使用x/z值，改用明确的0/1逻辑。',
        'R-11-5': '使用逗号(,)代替|或||连接敏感信号，如always @(a, b)。',
        'R-11-6': '将case分支改为常量表达式，避免使用变量或运算结果。',
        'R-11-7': '在case每个分支中对所有信号完整赋值，避免遗漏。',
        'R-11-8': '确保敏感列表包含if条件中使用的所有信号，保持一致性。',
        'R-11-9': '在异步always的if/else分支中为所有信号提供赋值，确保复位完整。',
        'R-12-1': '将for循环初值和终止条件设为常数，禁止在循环体内修改循环变量。',
        'R-12-2': '仅在for循环中对循环变量本身进行操作，避免对其他变量运算。',
        'R-12-3': '将复位逻辑与功能逻辑分离到不同的for循环或代码块。',
        'R-12-4': '检查循环条件，确保至少执行一次，避免空循环。',
        'R-12-5': '将递归函数改为迭代实现，避免使用递归调用。',
        'R-13-1': '移除task中的时序控制（如#、@、wait），改为纯组合或时序逻辑。',
        'R-13-2': '移除initial语句，改用复位逻辑或参数初始化。',
        'R-13-3': '在function中使用阻塞赋值（=），避免非阻塞赋值（<=）。',
        'R-13-4': '避免在function/task中对全局信号赋值，仅操作局部变量和输出参数。',
        'R-13-5': '确保function返回值位宽与输入信号位宽一致，避免位宽转换错误。',
        'R-13-6': '确保task输入输出信号位宽匹配，必要时进行显式转换。',
        'R-13-7': '检查并消除组合逻辑中的反馈路径，重构为时序逻辑或状态机。',
        'R-13-8': '检查所有数组访问，确保索引在合法范围内，必要时添加边界检查。',
        'R-13-9': '完善敏感信号列表，包含always块中使用的所有输入信号，或使用always @(*)。',
        'R-14-1': '检查状态机，消除死锁状态和不可达状态，确保所有状态可正常转换。',
        'R-14-2': '在状态机default分支中将所有寄存器重置为确定的初始状态。',
        'R-14-3': '在复位分支中为状态机设置明确的初始状态（如IDLE）。',
        'R-15-1': '在异步时钟域边界处移除组合逻辑，使用寄存器进行同步。',
        'R-15-2': '在跨时钟域同步器的两级寄存器间避免插入任何组合逻辑。',
        'R-15-3': '检查并消除第一级同步寄存器后的反馈环路，避免亚稳态传播。',
        'R-16-1': '在综合约束中明确指定复位属性（如async_reg），禁止工具自动更改。',
        'R-16-2': '在综合脚本中设置状态机编译模式为safe模式，确保非法状态可恢复。',
        # Verilog建议准则修改意见
        'A-1-1': '在每个源文件开头添加标准文件头，包含文件名、作者、日期、版本、功能描述等信息。',
        'A-1-2': '使用统一的缩进格式（建议4个空格），确保同层次语句左端对齐，嵌套语句逐层缩进。',
        'A-1-3': '调整端口、信号和变量定义格式，使类型和名称左端对齐，提升代码整洁度。',
        'A-1-4': '重构过长代码行，建议每行不超过80字符，必要时分多行书写。',
        'A-1-5': '调整端口声明顺序为：时钟、复位、输入、输出、双向端口，便于快速理解接口。',
        'A-1-6': '将同一行的多个赋值语句拆分为多行，每行一个赋值语句。',
        'A-1-7': '将端口说明分行书写，每行仅说明一个I/O端口，并添加注释。',
        'A-1-8': '增加代码注释，确保注释率不低于20%，重点注释复杂逻辑和接口信号。',
        'A-1-9': '将所有Tab符替换为空格（建议4个空格），保证不同编辑器显示一致。',
        'A-1-10': '重新组织端口声明，将输入、输出、双向端口分组声明，避免混杂。',
        'A-2-1': '确保源文件名与其中定义的module名称一致，便于项目管理和查找。',
        'A-2-2': '检查并调整标识符命名长度，确保在2-32个字符之间，平衡可读性和简洁性。',
        'A-2-3': '统一时钟信号命名为clk_xxx或Clk_XXX格式，xxx表示具体功能或频率。',
        'A-2-4': '统一复位信号命名为rst_p/rst_n或Rst_P/Rst_N格式，明确复位极性。',
        'A-2-5': '统一命名风格：常量全大写，变量全小写或首字母大写，保持代码一致性。',
        'A-2-6': '使用parameter或localparam替代defparam，在模块例化时传递参数值。',
        'A-2-7': '为不同模块的参数使用有区分度的命名，避免参数名重复导致混淆。',
        'A-2-8': '检查并删除未使用的端口和信号，清理冗余定义，简化代码。',
        'A-2-9': '统一一维对象范围定义为降序格式，如[7:0]而非[0:7]，保持一致性。',
        'A-2-10': '使用parameter或localparam定义总线宽度，如parameter WIDTH=8; wire [WIDTH-1:0] data;',
        'A-3-1': '重构顶层模块，将胶合逻辑移到单独的子模块中，顶层仅保留例化和连接。',
        'A-3-2': '重构上层模块，将具体逻辑移到叶子节点模块，上层仅负责例化和连接。',
        'A-3-3': '调整模块接口设计，使用组合逻辑输入和寄存器输出，便于流水线设计。',
        'A-4-1': '统一使用时钟单沿触发（posedge或negedge），避免在同一设计中混用双沿。',
        'A-4-2': '将时钟产生逻辑（如分频、倍频）封装到独立模块中，便于管理和复用。',
        'A-4-3': '使用时钟使能信号替代门控时钟，或使用FPGA厂商提供的专用门控时钟资源。',
        'A-4-4': '尽量使用单时钟域设计，必须跨时钟域时使用标准CDC同步器。',
        'A-5-1': '将复位产生逻辑封装到独立模块中，统一管理复位信号生成和分发。',
        'A-5-2': '避免在异步复位路径中插入逻辑门，如需处理使用同步复位方案。',
        'A-5-3': '使用外部或专用复位信号，避免用内部组合逻辑产生的信号作为异步复位。',
        'A-5-4': '简化复位逻辑，避免同时使用置位和复位信号，统一使用复位信号。',
        'A-5-5': '在每个always块中仅使用一个复位信号，避免多复位信号混用。',
        'A-5-6': '统一使用单个异步复位信号，避免多个异步复位同时触发。',
        'A-7-1': '将锁存器逻辑与组合逻辑分离到不同的always块，便于识别和综合优化。',
        'A-8-1': '在双向端口和单向端口间添加缓冲逻辑，避免直接连接导致冲突。',
        'A-8-2': '检查并确保每个线网只有一个三态驱动源，必要时使用总线仲裁逻辑。',
        'A-9-1': '在向量运算中使用位运算符（&、|、^）而非逻辑运算符（&&、||）。',
        'A-9-2': '为所有parameter和常数明确指定进制和位宽，如8\'d100、4\'hF等。',
        'A-10-1': '避免在非三态场景赋值为Z，改用明确的0/1值或高阻抗控制逻辑。',
        'A-10-2': '删除空语句块或补充完整逻辑，确保每个语句块都有实际功能。',
        'A-11-1': '检查并修正case分支，确保各分支条件互不重叠，逻辑清晰。',
        'A-11-2': '使用标准case语句替代casex/casez，通过明确条件判断提高代码安全性。',
        'A-11-3': '在default分支中使用明确的0/1值，避免使用包含x的不确定值。',
        'A-11-4': '将向量条件表达式改为单位宽信号，如if(|vector)改为if(vector_valid)。',
        'A-11-5': '在组合逻辑的if语句中添加else分支，为所有信号提供完整赋值避免锁存器。',
        'A-12-1': '将repeat表达式改为常量，避免使用变量可能导致的综合问题。',
        'A-13-1': '将数组索引简化为单个信号，避免使用复杂表达式作为索引。',
        'A-14-1': '优化状态机设计，将复杂状态机拆分或合并，控制状态数在40以内。',
        'A-14-2': '优化状态编码方式，减少状态转换时的位变化数，降低功耗和时序压力。',
        'A-16-1': '删除full_case综合属性，通过添加default分支确保case语句完整性。',
        # VHDL强制准则修改意见
        '5.1.1': '将所有模块例化改为名称映射方式，使用port map(port_name => signal_name)格式。',
        '5.1.2': '为所有输入端口提供明确驱动源，避免悬空；未使用端口应显式连接到默认值。',
        '5.2.1': '为模块添加至少一个输入或输出端口，确保模块可与外部交互。',
        '5.2.2': '移除输出信号对内部逻辑的驱动，改用内部信号中转；双向端口除外。',
        '5.2.3': '将内部三态逻辑改为多路选择器或寄存器实现，避免使用inout类型。',
        '5.3.1': '完善进程敏感列表，包含所有读取的信号；或使用process(all)自动推导。',
        '5.4.1': '为所有多位信号显式声明位宽，如signal data: std_logic_vector(7 downto 0)。',
        '5.4.3': '将条件表达式中的X/Z/U等不确定值替换为明确的\'0\'或\'1\'。',
        '5.4.4': '重构进程，确保每个进程只包含一个wait或敏感列表，避免多事件控制。',
        '5.5.1': '检查并重命名与VHDL关键字冲突的标识符，避免编译错误。',
        '5.5.2': '为不同类型对象使用有区分度的命名，避免信号、变量、常量等同名。',
        '5.5.3': '统一标识符命名规范：使用有意义的名称，遵循驼峰或下划线分隔风格。',
        '5.5.4': '统一大小写规范，避免仅以大小写区分不同标识符，如Data与data。',
        '5.6.1': '删除未使用的信号赋值语句，或确保赋值后的信号在后续逻辑中被读取。',
        '5.6.2': '统一运算符两端信号位宽，必要时使用resize或显式类型转换。',
        '5.6.3': '确保常量赋值右侧为固定整型字面量，避免使用变量或表达式。',
        '5.6.4': '避免整数、实数与无符号类型间隐式转换，使用to_integer/to_unsigned等显式转换。',
        '5.6.5': '统一运算中的符号类型，使用signed/unsigned显式声明或转换函数。',
        '5.6.6': '检查并消除单向信号的多驱动源，确保每个信号只有一个驱动进程。',
        '5.6.7': '避免同一信号源驱动寄存器的多个异步端口，分离复位与置位信号源。',
        '5.6.8': '移除信号赋值中的after延迟波形，改用纯组合或时序逻辑。',
        '5.7.1': '将循环终止条件改为常量或静态表达式，避免使用变量控制循环。',
        '5.7.2': '禁止在for循环体内修改循环变量，保持循环迭代可预测。',
        '5.7.3': '检查while循环条件，确保条件为变量而非常量，避免死循环或空循环。',
        '5.8.1': '将case表达式改为变量或信号，避免使用固定常量作为控制表达式。',
        '5.8.2': '将case分支改为常量字面量，避免使用变量或表达式作为分支条件。',
        '5.8.3': '为case语句添加when others分支，并在其中对所有信号赋值。',
        '5.8.4': '在组合逻辑的if语句中添加else分支，为所有信号提供完整赋值。',
        '5.8.5': '确保case每个分支中对所有信号完整赋值，避免部分信号遗漏。',
        '5.9.1': '避免时钟信号汇聚，使用单一时钟源或时钟管理单元分发时钟。',
        '5.9.2': '禁止时钟信号连接到多路选择器控制端，改用时钟使能或门控时钟单元。',
        '5.9.3': '使用时钟使能信号替代门控时钟，或使用FPGA厂商提供的专用门控资源。',
        '5.9.4': '重构进程，确保每个时序进程只使用一个时钟信号。',
        '5.9.5': '在跨时钟域边界添加双触发器同步器或FIFO，避免亚稳态传播。',
        '5.9.6': '禁止将时钟信号作为数据使用，改用时钟使能或边沿检测逻辑。',
        '5.10.1': '避免寄存器输出反馈到异步复位/置位端，使用独立的复位信号源。',
        '5.10.2': '分离复位与置位信号源，避免来自同一信号，确保状态确定性。',
        '5.10.3': '为异步复位添加同步释放电路，使用两级寄存器同步复位撤销。',
        '5.10.4': '为所有寄存器的复位端口提供明确连接，避免悬空导致不确定状态。',
        '5.11.1': '在状态机中添加default或when others分支，处理所有非法状态。',
        '5.11.2': '在综合脚本中设置状态机编码属性，如safe模式或one-hot编码。',
        '5.11.3': '在复位分支中为状态机设置明确的初始状态，如IDLE或RESET状态。',
        '5.11.4': '检查状态机转换逻辑，确保所有状态可达，删除不可达状态定义。',
        '5.12.1': '移除不可综合的代码（如after延迟、wait for、文件操作等），改用可综合结构。',
        '5.12.2': '检查并解决约束冲突，确保时钟周期、输入输出延迟等约束相互兼容。',
        '5.12.3': '将buffer类型端口改为out类型，必要时使用内部信号反馈。',
        # VHDL建议准则修改意见
        '5.1.3': '为未使用的输出端口显式标记为open，如port map(unused_out => open)。',
        '5.2.4': '重构顶层模块，将所有逻辑移到子模块，顶层仅保留例化和连接。',
        '5.2.5': '删除多余代码和不可达分支，使用代码覆盖率工具识别死代码。',
        '5.2.6': '检查并消除非预期锁存器，在组合逻辑中为所有信号提供完整赋值。',
        '5.2.7': '将每个设计模块拆分到独立文件，文件名与实体名保持一致。',
        '5.2.8': '按功能、时钟域或复用性重新划分模块，优化模块接口与层次结构。',
        '5.2.9': '将相关组合逻辑和可复用逻辑封装到独立模块，提升复用性。',
        '5.2.10': '确保每个VHDL文件只包含一个entity定义，便于管理和复用。',
        '5.2.11': '在每个VHDL文件开头添加library ieee; use ieee.std_logic_1164.all;',
        '5.2.12': '在双向与单向端口间添加缓冲逻辑或方向控制，避免直接连接。',
        '5.2.13': '检查并消除组合逻辑反馈路径，重构为时序逻辑或状态机。',
        '5.4.2': '删除未使用的信号定义，使用静态分析工具识别冗余信号。',
        '5.4.5': '统一一维对象范围定义为降序格式，如(7 downto 0)而非(0 to 7)。',
        '5.4.6': '使用generic或constant定义总线宽度，如generic(WIDTH: integer := 8)。',
        '5.4.7': '调整端口声明顺序为：输入(in)、输出(out)、双向(inout)，便于理解。',
        '5.4.8': '将bit/bit_vector类型改为std_logic/std_logic_vector，提升兼容性。',
        '5.4.9': '删除枚举类型的enum_encoding属性，让综合工具自动选择编码。',
        '5.4.10': '规范STD_LOGIC_VECTOR对象定义，统一使用downto方向和明确位宽。',
        '5.4.11': '统一一维信号索引起始为0，使用(WIDTH-1 downto 0)格式。',
        '5.4.12': '为整数类型添加范围限制，如signal count: integer range 0 to 255。',
        '5.5.5': '统一时钟信号命名为clk_xxx或xxx_clk格式，明确时钟功能或频率。',
        '5.5.6': '制定并遵循统一的命名准则，如信号用小写、常量用大写等。',
        '5.5.7': '确保跨模块层次的同一信号使用相同命名，便于信号追踪。',
        '5.5.8': '避免使用Verilog关键字作为VHDL标识符，如reg、wire等。',
        '5.6.9': '分离三态节点的使能端和输入端驱动源，避免同源驱动产生竞争。',
        '5.6.10': '将三态门使能端改为寄存器输出，避免组合逻辑直接驱动。',
        '5.6.11': '在实体输出端添加寄存器，避免组合逻辑直接输出到端口。',
        '5.6.12': '避免在非三态场景赋值为\'Z\'，改用明确的\'0\'或\'1\'值。',
        '5.6.13': '移除所有after延迟赋值，改用纯组合或时序逻辑实现延时。',
        '5.6.14': '检查并确保每个线型信号只有一个三态驱动源，必要时使用总线仲裁。',
        '5.6.15': '避免与\'Z\'/\'U\'/\'X\'等不确定值比较，改用明确的逻辑判断。',
        '5.8.6': '删除空语句或补充完整逻辑，确保每个语句块都有实际功能。',
        '5.8.7': '优化多级if-else结构，将高频条件放在前面，降低关键路径延迟。',
        '5.9.7': '禁止使用组合逻辑产生时钟，改用PLL/MMCM等专用时钟资源。',
        '5.9.8': '使用BUFG等全局时钟缓冲资源驱动全局时钟，降低时钟偏斜。',
        '5.9.9': '避免行波时钟，使用时钟树或全局时钟网络分发时钟。',
        '5.9.10': '尽量使用单时钟域设计，必须跨时钟域时使用标准CDC同步器。',
        '5.9.11': '统一使用时钟单沿触发（上升沿或下降沿），避免混用双沿。',
        '5.9.12': '避免在时钟路径上插入反相器或缓冲器，使用专用时钟资源。',
        '5.9.13': '禁止将触发器输出作为时钟使用，改用时钟管理单元生成时钟。',
        '5.9.14': '禁止将时钟信号作为数据使用，改用时钟使能或边沿检测。',
        '5.10.5': '为所有寄存器添加复位逻辑，在复位分支中提供初始值。',
        '5.10.6': '统一使用同一复位域对所有模块复位，确保复位同步性。',
        '5.10.7': '使用BUFG等全局网络资源驱动系统复位信号，降低复位偏斜。',
        '5.10.8': '避免使用时钟信号做复位，改用专用复位信号或复位管理单元。',
        '5.10.9': '为外部复位信号添加两级寄存器同步，避免亚稳态传入系统。',
        '5.10.10': '统一复位信号有效电平为高电平或低电平，避免混用。',
        '5.10.11': '为组合逻辑产生的复位信号添加同步电路，避免毛刺。',
        '5.10.12': '避免组合逻辑驱动异步复位，改用寄存器输出或专用复位源。',
        '5.10.13': '在单时钟进程中仅使用一个异步复位信号，避免多复位竞争。',
        '5.10.14': '确保异步复位/置位信号仅连接到触发器的异步端口，避免误连。',
        '5.11.5': '重构状态机为三段式：状态转移、状态寄存、输出逻辑分离。',
        '5.11.6': '使用枚举类型定义状态机状态，如type state_type is (IDLE, RUN, DONE)。',
        '5.11.7': '根据需求选择合适的状态编码方式（binary/one-hot/gray），并在综合中指定。',
        '5.12.4': '在约束文件中为每个时钟添加周期约束，如create_clock -period 10。',
        '5.13.1': '在文件开头添加标准注释头，包含文件名、作者、日期、功能描述等。',
        '5.13.2': '为每个端口添加注释说明，描述端口功能、位宽、有效电平等信息。',
        '5.13.3': '为关键内部信号和变量添加注释，说明其功能和用途。',
        '5.13.4': '为结束语句添加注释标签，如end process proc_name; end architecture rtl;',
        '5.14.1': '使用空行分隔不同功能模块，如端口声明、信号定义、进程等。',
        '5.14.2': '使用统一的缩进格式（建议2或4个空格），确保代码层次清晰。',
        '5.14.3': '在运算符、赋值符号等两侧添加空格，提升代码可读性。',
        '5.14.4': '遵循统一的编码格式要求，如关键字小写、标识符命名风格等。',
    }
    if rule_code in fix_map:
        return f"修改意见：{fix_map[rule_code]}"
    # 兜底：未匹配规则返回通用建议
    return f"修改意见：请依据{language} {rule_type}规则要求，对相关代码进行规范化修改，确保符合编码标准。"


def migrate_fpga_rules():
    """迁移FPGA规则数据"""
    try:
        # 获取PostgreSQL会话
        pg_session = get_db_session()
        
        # 检查是否已有数据
        existing_count = pg_session.query(FPGARule).count()
        if existing_count > 0:
            print(f"    INFO: PostgreSQL中已有 {existing_count} 条FPGA规则，执行字段回填...")
            updated_acc = 0
            updated_text = 0
            try:
                for rule in pg_session.query(FPGARule).all():
                    new_acc = determine_accuracy(rule.rule_code, rule.rule_content, rule.language, rule.rule_type)
                    if rule.accuracy_type != new_acc:
                        rule.accuracy_type = new_acc
                        updated_acc += 1
                    # 回填三列文本字段（若为空）
                    if not getattr(rule, 'issue_title', None):
                        rule.issue_title = build_issue_title(rule.rule_code, rule.rule_content, rule.language, rule.rule_type)
                        updated_text += 1
                    if not getattr(rule, 'impact_analysis', None):
                        rule.impact_analysis = build_impact_analysis(rule.rule_code, rule.rule_content, rule.language, rule.rule_type)
                        updated_text += 1
                    if not getattr(rule, 'fix_suggestion', None):
                        rule.fix_suggestion = build_fix_suggestion(rule.rule_code, rule.rule_content, rule.language, rule.rule_type)
                        updated_text += 1
                pg_session.commit()
                print(f"       回填完成：accuracy_type更新 {updated_acc} 条，文本字段更新 {updated_text} 次")
            except Exception as e:
                print(f"       回填失败：{e}")
                pg_session.rollback()
            finally:
                pg_session.close()
            return existing_count
        
        # 解析规则文件
        rules = parse_fpga_rules()
        
        if not rules:
            print(f"    WARNING: 未能从FPGA规则文件中解析到任何规则")
            pg_session.close()
            return 0
        
        # 插入规则
        rule_count = 0
        for rule_data in rules:
            accuracy = determine_accuracy(
                rule_data['rule_code'],
                rule_data['rule_content'],
                rule_data['language'],
                rule_data['rule_type'],
            )
            rule = FPGARule(
                rule_code=rule_data['rule_code'],
                rule_content=rule_data['rule_content'],
                language=rule_data['language'],
                rule_type=rule_data['rule_type'],
                category=rule_data['category'],
                chapter=rule_data['chapter'],
                sequence=rule_data['sequence'],
                accuracy_type=accuracy,
                issue_title=build_issue_title(rule_data['rule_code'], rule_data['rule_content'], rule_data['language'], rule_data['rule_type']),
                impact_analysis=build_impact_analysis(rule_data['rule_code'], rule_data['rule_content'], rule_data['language'], rule_data['rule_type']),
                fix_suggestion=build_fix_suggestion(rule_data['rule_code'], rule_data['rule_content'], rule_data['language'], rule_data['rule_type']),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            pg_session.add(rule)
            rule_count += 1
        
        # 提交
        pg_session.commit()
        pg_session.close()
        
        # 统计信息
        print(f"       - Verilog强制准则: {len([r for r in rules if r['language']=='Verilog' and r['rule_type']=='mandatory'])} 条")
        print(f"       - Verilog建议准则: {len([r for r in rules if r['language']=='Verilog' and r['rule_type']=='advisory'])} 条")
        print(f"       - VHDL强制准则: {len([r for r in rules if r['language']=='VHDL' and r['rule_type']=='mandatory'])} 条")
        print(f"       - VHDL建议准则: {len([r for r in rules if r['language']=='VHDL' and r['rule_type']=='advisory'])} 条")
        
        return rule_count
        
    except Exception as e:
        print(f"    ERROR: FPGA规则导入失败: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """主函数"""
    print("="*70)
    print("FPGA规则数据导入工具")
    print("从FPGA规则.md导入到PostgreSQL")
    print("="*70)
    print()
    
    print("[1/1] 导入FPGA规则...")
    fpga_count = migrate_fpga_rules()
    print(f"    OK 完成，共导入 {fpga_count} 条规则")
    print()
    
    print("="*70)
    print("导入完成！")
    print("="*70)


if __name__ == "__main__":
    main()
