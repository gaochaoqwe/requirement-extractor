"""
更新GJB8114规则数据库 - 根据标准文档重新生成规则
"""
import sqlite3
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GJB8114RulesUpdater:
    def __init__(self, db_path: str = None):
        """初始化规则更新器"""
        if db_path is None:
            current_dir = Path(__file__).parent
            db_path = current_dir / "database" / "gjb8114_rules.db"
        
        self.db_path = str(db_path)
        self.rules_md_path = Path("D:/code/requirement_extractor/backend/app/staticAnalysis/service/ai/rules/GJB8114规则.md")
    
    def parse_rules_from_md(self) -> List[Tuple[str, str, str, str, str]]:
        """从MD文件解析规则"""
        rules = []
        
        try:
            with open(self.rules_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析规则的正则表达式
            # 匹配格式：5.1.1.1准则R-1-1-1禁止通过宏定义改变关键字和基本类型含义
            # 改进的正则表达式，更准确地匹配完整的规则描述
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 匹配规则行格式
                # 支持多种格式：5.1.1.1准则R-1-1-1... 或 5.1.1.1 准则R-1-1-1...
                rule_match = re.match(r'(\d+\.\d+\.\d+\.\d+)\s*准则\s*(R-\d+-\d+-\d+)\s*(.+)', line)
                
                if rule_match:
                    section_num = rule_match.group(1)  # 如 5.1.1.1
                    rule_code = rule_match.group(2)    # 如 R-1-1-1
                    rule_desc = rule_match.group(3).strip()  # 规则描述
                    
                    # 转换为GJB格式的规则编号
                    # R-1-1-1 -> GJB_R_01_01_01
                    parts = rule_code.replace('R-', '').split('-')
                    if len(parts) == 3:
                        gjb_code = f"GJB_R_{parts[0].zfill(2)}_{parts[1].zfill(2)}_{parts[2].zfill(2)}"
                        
                        # 生成完整的规则名称
                        full_rule_name = f"{gjb_code}{rule_desc}"
                        
                        # 确定分类
                        category = self._determine_category(section_num, rule_desc)
                        accuracy_type = self._determine_accuracy_type(rule_code, rule_desc)
                        
                        rules.append((gjb_code, full_rule_name, rule_desc, category, accuracy_type))
            
            logger.info(f"从MD文件解析到 {len(rules)} 条规则")
            return rules
            
        except Exception as e:
            logger.error(f"解析MD文件失败: {str(e)}")
            return []
    
    def _determine_category(self, section_num: str, rule_desc: str) -> str:
        """根据章节号和描述确定规则分类"""
        section_map = {
            '5.1.1': '强制准则',
            '5.2': '版面书写',
            '5.3': '指针使用',
            '5.4': '分支控制',
            '5.5': '跳转控制',
            '5.6': '运算处理',
            '5.7': '函数调用',
            '5.8': '语句使用',
            '5.9': '循环控制',
            '5.10': '类型转换',
            '5.11': '初始化',
            '5.12': '比较判断',
            '5.13': '变量使用',
            '6.1': '类与对象',
            '6.2': 'C++强制准则',
            '6.3': '析构函数',
            '6.4': '虚拟函数',
            '6.5': 'C++类型转换',
            '6.6': '内存释放'
        }
        
        # 找到最匹配的分类
        for prefix, category in section_map.items():
            if section_num.startswith(prefix):
                return category
        
        return '其他'
    
    def _determine_accuracy_type(self, rule_code: str, rule_desc: str) -> str:
        """确定规则的准确性类型"""
        # 基于规则内容判断是否为确定规则
        accurate_keywords = [
            '禁止', '必须', '不能', '不允许', '强制', '语法', '声明', '定义',
            '类型', '关键字', '宏定义', 'typedef', 'extern', 'void', 'NULL',
            '大括号', '括号', '注释', '头文件', 'include', 'switch', 'case',
            'default', 'break', 'return', 'setjmp', 'longjmp', '浮点常数',
            '整型变量', '赋值语句', '位运算', '++', '--', '移位', '数组下标',
            '逻辑非', '枚举', 'sizeof', '标准函数', '实参', '形参', '返回值',
            '八进制', '大写字母', 'for循环', 'while', '强制转换', '初始化',
            '逻辑量', '无符号', '有符号', '局部变量', '全局变量', '函数名',
            '变量名', '枚举元素', 'volatile', 'const', '字符串', '构造函数',
            'explicit', 'virtual', 'dynamic_cast', 'new', 'delete'
        ]
        
        uncertain_keywords = [
            '越界', '未分配', '已释放', '空指针', '文件指针', '缓存区', '缓冲区',
            '内存', 'malloc', 'calloc', 'free', 'gets', 'fgets', '不可达',
            '未赋值', '未初始化', '递归', '自调用', '顺序相关', '异常',
            '生命周期', '作用域', '数据流', '控制流', '路径', '分析'
        ]
        
        # 检查是否包含不确定关键字
        for keyword in uncertain_keywords:
            if keyword in rule_desc:
                return 'uncertain'
        
        # 检查是否包含确定关键字
        for keyword in accurate_keywords:
            if keyword in rule_desc:
                return 'accurate'
        
        # 默认为不确定
        return 'uncertain'
    
    def recreate_database(self):
        """重新创建数据库"""
        try:
            # 删除旧数据库文件
            db_file = Path(self.db_path)
            if db_file.exists():
                db_file.unlink()
                logger.info("已删除旧数据库文件")
            
            # 确保目录存在
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建新数据库
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建规则表
                cursor.execute('''
                    CREATE TABLE gjb8114_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_code TEXT UNIQUE NOT NULL,
                        rule_name TEXT NOT NULL,
                        rule_description TEXT,
                        category TEXT NOT NULL,
                        accuracy_type TEXT NOT NULL,
                        analysis_complexity TEXT,
                        detection_method TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建规则关键字映射表
                cursor.execute('''
                    CREATE TABLE rule_keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_code TEXT NOT NULL,
                        keyword TEXT NOT NULL,
                        keyword_type TEXT,
                        FOREIGN KEY (rule_code) REFERENCES gjb8114_rules (rule_code)
                    )
                ''')
                
                conn.commit()
                logger.info("数据库表结构创建完成")
                
        except Exception as e:
            logger.error(f"重新创建数据库失败: {str(e)}")
            raise
    
    def populate_rules(self):
        """填充规则数据"""
        try:
            # 解析规则
            rules = self.parse_rules_from_md()
            if not rules:
                logger.error("没有解析到任何规则")
                return
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 插入规则数据
                for rule_code, rule_name, rule_desc, category, accuracy_type in rules:
                    # 设置分析复杂度和检测方法
                    if accuracy_type == 'accurate':
                        analysis_complexity = '语法分析'
                        detection_method = 'AST分析'
                    else:
                        analysis_complexity = '数据流分析'
                        detection_method = 'AI分析'
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO gjb8114_rules 
                        (rule_code, rule_name, rule_description, category, accuracy_type, analysis_complexity, detection_method)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (rule_code, rule_name, rule_desc, category, accuracy_type, analysis_complexity, detection_method))
                
                # 添加关键字映射
                self._populate_keywords(cursor, rules)
                
                conn.commit()
                logger.info(f"成功插入 {len(rules)} 条规则")
                
        except Exception as e:
            logger.error(f"填充规则数据失败: {str(e)}")
            raise
    
    def _populate_keywords(self, cursor, rules: List[Tuple]):
        """填充关键字映射"""
        for rule_code, rule_name, rule_desc, category, accuracy_type in rules:
            # 从规则描述中提取关键字
            keywords = self._extract_keywords(rule_desc)
            
            for keyword, keyword_type in keywords:
                cursor.execute('''
                    INSERT OR IGNORE INTO rule_keywords (rule_code, keyword, keyword_type)
                    VALUES (?, ?, ?)
                ''', (rule_code, keyword, keyword_type))
    
    def _extract_keywords(self, rule_desc: str) -> List[Tuple[str, str]]:
        """从规则描述中提取关键字"""
        keywords = []
        
        # 主要关键字（直接出现在描述中的重要词汇）
        primary_keywords = [
            '宏定义', '关键字', 'typedef', '重定义', '#define', '#undef', 
            '函数', '参数', '变量', '数组', '指针', '结构体', '枚举',
            'extern', 'void', 'NULL', '大括号', '括号', '注释', '头文件',
            'include', 'switch', 'case', 'default', 'break', 'return',
            'if', 'else', 'for', 'while', '循环', '赋值', '类型转换',
            '初始化', '比较', '逻辑', '运算', '表达式', '越界', '内存',
            '释放', '分配', 'malloc', 'free', 'new', 'delete'
        ]
        
        for keyword in primary_keywords:
            if keyword in rule_desc:
                keywords.append((keyword, 'primary'))
        
        # 如果没有找到主要关键字，从描述中提取重要词汇
        if not keywords:
            # 提取中文词汇作为次要关键字
            import re
            chinese_words = re.findall(r'[\u4e00-\u9fff]+', rule_desc)
            for word in chinese_words:
                if len(word) >= 2:  # 只保留长度>=2的词
                    keywords.append((word, 'secondary'))
        
        return keywords[:5]  # 最多保留5个关键字
    
    def update_database(self):
        """更新数据库"""
        try:
            logger.info("开始更新GJB8114规则数据库...")
            
            # 重新创建数据库
            self.recreate_database()
            
            # 填充规则数据
            self.populate_rules()
            
            # 验证数据
            self.verify_database()
            
            logger.info("GJB8114规则数据库更新完成！")
            
        except Exception as e:
            logger.error(f"更新数据库失败: {str(e)}")
            raise
    
    def verify_database(self):
        """验证数据库内容"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 统计规则数量
                cursor.execute("SELECT COUNT(*) FROM gjb8114_rules")
                total_rules = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM gjb8114_rules WHERE accuracy_type = 'accurate'")
                accurate_rules = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM gjb8114_rules WHERE accuracy_type = 'uncertain'")
                uncertain_rules = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM rule_keywords")
                total_keywords = cursor.fetchone()[0]
                
                logger.info(f"数据库验证结果:")
                logger.info(f"  总规则数: {total_rules}")
                logger.info(f"  确定规则: {accurate_rules}")
                logger.info(f"  不确定规则: {uncertain_rules}")
                logger.info(f"  关键字映射: {total_keywords}")
                
                # 显示几个示例规则
                cursor.execute("SELECT rule_code, rule_name FROM gjb8114_rules LIMIT 5")
                examples = cursor.fetchall()
                logger.info("示例规则:")
                for rule_code, rule_name in examples:
                    logger.info(f"  {rule_code}: {rule_name[:50]}...")
                
        except Exception as e:
            logger.error(f"验证数据库失败: {str(e)}")

def main():
    """主函数"""
    try:
        updater = GJB8114RulesUpdater()
        updater.update_database()
        
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()
