"""
GJB8114规则分类数据库管理
"""
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class RulesDatabase:
    def __init__(self, db_path: str = None):
        """初始化规则数据库"""
        if db_path is None:
            current_dir = Path(__file__).parent
            db_path = current_dir / "gjb8114_rules.db"
        
        self.db_path = str(db_path)
        self._init_database()
        self._populate_rules()
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建规则表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gjb8114_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_code TEXT UNIQUE NOT NULL,
                        rule_name TEXT NOT NULL,
                        rule_description TEXT,
                        category TEXT NOT NULL,
                        accuracy_type TEXT NOT NULL,  -- 'accurate' 或 'uncertain'
                        analysis_complexity TEXT,     -- 分析复杂度描述
                        detection_method TEXT,        -- 检测方法
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建规则关键字映射表（用于模糊匹配）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rule_keywords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_code TEXT NOT NULL,
                        keyword TEXT NOT NULL,
                        keyword_type TEXT,  -- 'primary', 'secondary', 'alias'
                        FOREIGN KEY (rule_code) REFERENCES gjb8114_rules (rule_code)
                    )
                ''')
                
                conn.commit()
                logger.info(f"规则数据库初始化成功: {self.db_path}")
                
        except Exception as e:
            logger.error(f"初始化规则数据库失败: {str(e)}")
            raise
    
    def _populate_rules(self):
        """填充规则数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查是否已有数据
                cursor.execute("SELECT COUNT(*) FROM gjb8114_rules")
                if cursor.fetchone()[0] > 0:
                    logger.info("规则数据已存在，跳过初始化")
                    return
                
                # 一定准确的规则
                accurate_rules = self._get_accurate_rules()
                for rule in accurate_rules:
                    cursor.execute('''
                        INSERT OR IGNORE INTO gjb8114_rules 
                        (rule_code, rule_name, rule_description, category, accuracy_type, analysis_complexity, detection_method)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', rule)
                
                # 不确定的规则
                uncertain_rules = self._get_uncertain_rules()
                for rule in uncertain_rules:
                    cursor.execute('''
                        INSERT OR IGNORE INTO gjb8114_rules 
                        (rule_code, rule_name, rule_description, category, accuracy_type, analysis_complexity, detection_method)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', rule)
                
                # 添加关键字映射
                self._populate_keywords(cursor)
                
                conn.commit()
                logger.info(f"规则数据填充完成，共{len(accurate_rules) + len(uncertain_rules)}条规则")
                
        except Exception as e:
            logger.error(f"填充规则数据失败: {str(e)}")
            raise
    
    def _get_accurate_rules(self) -> List[Tuple]:
        """获取一定准确的规则列表"""
        return [
            # 宏定义相关
            ("R-1-1-1", "禁止通过宏定义改变关键字和基本类型含义", "宏定义不能改变关键字和基本类型的含义", "宏定义", "accurate", "语法分析", "AST分析"),
            ("R-1-1-2", "禁止将其他标识宏定义为关键字和基本类型", "标识符不能定义为关键字和基本类型", "宏定义", "accurate", "语法分析", "符号表检查"),
            ("R-1-1-3", "禁止用typedef自定义的类型被重新定义", "typedef定义的类型不能重复定义", "类型定义", "accurate", "语法分析", "符号表检查"),
            ("R-1-1-4", "禁止重新定义C或C++的关键字", "不能重新定义语言关键字", "宏定义", "accurate", "语法分析", "关键字检查"),
            ("R-1-1-5", "禁止#define被重复定义", "宏定义不能重复", "宏定义", "accurate", "语法分析", "符号表检查"),
            ("R-1-1-6", "函数中#define和#undef必须配对使用", "函数内宏定义和取消定义必须配对", "宏定义", "accurate", "语法分析", "配对检查"),
            ("R-1-1-7", "以函数形式定义的宏，参数和结果必须使用括号括起来", "函数式宏的参数和结果需要括号", "宏定义", "accurate", "语法分析", "宏展开检查"),
            
            # 结构体和类型定义
            ("R-1-1-8", "结构、联合、枚举的定义中必须定义标识名", "结构体等必须有标识名", "类型定义", "accurate", "语法分析", "AST分析"),
            ("R-1-1-9", "结构体定义中禁止含有无名结构体", "结构体不能包含匿名结构体", "类型定义", "accurate", "语法分析", "结构体分析"),
            ("R-1-1-10", "位定义的有符号整型变量位长必须大于1", "有符号位域长度必须大于1", "类型定义", "accurate", "语法分析", "位域检查"),
            ("R-1-1-11", "位定义的整数型变量必须明确定义是有符号还是无符号的", "位域必须明确符号性", "类型定义", "accurate", "语法分析", "类型检查"),
            ("R-1-1-12", "位定义的变量必须是同长度的类型且定义位禁止跨越类型的长度", "位域不能跨越类型边界", "类型定义", "accurate", "语法分析", "位域分析"),
            
            # 函数声明
            ("R-1-1-13", "函数声明中必须对参数类型进行声明，并带有变量名", "函数声明需要参数类型和名称", "函数声明", "accurate", "语法分析", "函数签名检查"),
            ("R-1-1-14", "函数声明必须与函数原型一致", "函数声明和定义必须一致", "函数声明", "accurate", "语法分析", "签名比较"),
            ("R-1-1-15", "函数中的参数必须使用类型声明", "函数参数必须有类型声明", "函数声明", "accurate", "语法分析", "参数检查"),
            ("R-1-1-16", "外部声明的变量，类型必须与定义一致", "extern声明类型必须一致", "变量声明", "accurate", "语法分析", "类型一致性检查"),
            ("R-1-1-17", "禁止在函数体内使用外部声明", "函数内不能使用extern声明", "变量声明", "accurate", "语法分析", "作用域检查"),
            ("R-1-1-18", "数组定义禁止没有显式的边界限定", "数组必须有明确的大小", "数组定义", "accurate", "语法分析", "数组声明检查"),
            ("R-1-1-19", "禁止使用extern声明对变量初始化", "extern变量不能初始化", "变量声明", "accurate", "语法分析", "初始化检查"),
            ("R-1-1-20", "用于数值计算的字符型变量必须明确定义是有符号还是无符号", "字符型变量必须明确符号性", "类型定义", "accurate", "语法分析", "类型检查"),
            ("R-1-1-23", "函数参数表为空时，必须使用void明确说明", "空参数列表必须用void", "函数声明", "accurate", "语法分析", "参数列表检查"),
            
            # 头文件相关
            ("R-1-1-21", "禁止在#include语句中使用绝对路径", "include不能使用绝对路径", "头文件", "accurate", "语法分析", "路径检查"),
            ("R-1-1-22", "禁止头文件重复包含", "头文件不能重复包含", "头文件", "accurate", "语法分析", "包含检查"),
            
            # 代码格式和书写规范
            ("R-1-2-1", "循环体必须用大括号括起来", "循环体需要大括号", "代码格式", "accurate", "语法分析", "AST结构检查"),
            ("R-1-2-2", "if、else if、else必须用大括号括起来", "条件语句需要大括号", "代码格式", "accurate", "语法分析", "AST结构检查"),
            ("R-1-2-3", "禁止在头文件前有可执行代码", "头文件前不能有可执行代码", "代码格式", "accurate", "语法分析", "预处理检查"),
            ("R-1-2-4", "引起二义性理解的逻辑表达式，必须使用括号显示说明优先级顺序", "复杂表达式需要括号", "代码格式", "accurate", "语法分析", "表达式分析"),
            ("R-1-2-5", "逻辑判别表达式中的运算项必须使用括号", "逻辑表达式需要括号", "代码格式", "accurate", "语法分析", "表达式分析"),
            ("R-1-2-6", "禁止嵌套注释", "不能嵌套注释", "代码格式", "accurate", "语法分析", "注释检查"),
            
            # 指针使用规范
            ("R-1-3-1", "禁止指针的指针超过两级", "指针层级不能超过两级", "指针使用", "accurate", "语法分析", "类型检查"),
            ("R-1-3-2", "C函数指针的使用必须加以&明确说明", "函数指针需要&操作符", "指针使用", "accurate", "语法分析", "表达式检查"),
            ("R-1-3-7", "动态分配的指针变量定义时如未被分配空间，必须初始化为NULL", "未分配的指针必须初始化为NULL", "指针使用", "accurate", "语法分析", "初始化检查"),
            ("R-1-3-9", "空指针必须使用NULL避免使用整型数0", "空指针必须用NULL", "指针使用", "accurate", "语法分析", "常量检查"),
            
            # Switch语句结构
            ("R-1-4-3", "禁止使用空switch语句", "switch语句不能为空", "控制流", "accurate", "语法分析", "AST结构检查"),
            ("R-1-4-4", "禁止对bool量使用switch语句", "bool类型不能用switch", "控制流", "accurate", "语法分析", "类型检查"),
            ("R-1-4-5", "禁止switch语句中只包含default语句", "switch不能只有default", "控制流", "accurate", "语法分析", "AST结构检查"),
            ("R-1-4-6", "除枚举类型列举完全外，switch必须要有default", "switch必须有default", "控制流", "accurate", "语法分析", "分支检查"),
            ("R-1-4-8", "switch语句的所有分支必须具有相同的层次范围", "switch分支层次必须一致", "控制流", "accurate", "语法分析", "作用域检查"),
            
            # 跳转控制
            ("R-1-5-2", "禁止使用setjmp/longjmp", "不能使用setjmp/longjmp", "控制流", "accurate", "语法分析", "函数调用检查"),
            
            # 运算和表达式语法
            ("R-1-6-1", "禁止将浮点常数赋给整型变量", "浮点数不能直接赋给整型", "类型转换", "accurate", "语法分析", "类型检查"),
            ("R-1-6-3", "禁止在逻辑表达式中使用赋值语句", "逻辑表达式中不能赋值", "表达式", "accurate", "语法分析", "表达式分析"),
            ("R-1-6-4", "禁止对逻辑表达式进行位运算", "逻辑表达式不能位运算", "表达式", "accurate", "语法分析", "操作符检查"),
            ("R-1-6-5", "禁止在运算表达式中或函数调用参数中使用++或--操作符", "表达式中不能用++/--", "表达式", "accurate", "语法分析", "操作符检查"),
            ("R-1-6-6", "对变量进行移位运算禁止超出变量长度", "移位不能超出变量长度", "表达式", "accurate", "语法分析", "移位检查"),
            ("R-1-6-7", "禁止移位操作中的移位数为负数", "移位数不能为负", "表达式", "accurate", "语法分析", "常量检查"),
            ("R-1-6-9", "数组下标必须是大于等于零的整型数", "数组下标必须非负整数", "数组访问", "accurate", "语法分析", "类型检查"),
            ("R-1-6-10", "禁止对常数值做逻辑非的运算", "常数不能逻辑非运算", "表达式", "accurate", "语法分析", "常量检查"),
            ("R-1-6-11", "禁止非枚举类型变量使用枚举类型的值", "非枚举变量不能用枚举值", "类型转换", "accurate", "语法分析", "类型检查"),
            ("R-1-6-13", "禁止在sizeof中使用赋值", "sizeof中不能赋值", "表达式", "accurate", "语法分析", "表达式分析"),
            
            # 函数定义和调用语法
            ("R-1-7-1", "禁止覆盖标准函数库的函数", "不能重定义标准库函数", "函数定义", "accurate", "语法分析", "符号表检查"),
            ("R-1-7-2", "禁止函数的实参和形参类型不一致", "实参形参类型必须一致", "函数调用", "accurate", "语法分析", "类型检查"),
            ("R-1-7-3", "禁止实参与形参的个数不一致", "实参形参个数必须一致", "函数调用", "accurate", "语法分析", "参数个数检查"),
            ("R-1-7-4", "禁止使用旧形式的函数参数表定义形式", "不能用旧式函数定义", "函数定义", "accurate", "语法分析", "语法检查"),
            ("R-1-7-5", "函数声明和函数定义中的参数类型必须一致", "声明定义参数类型必须一致", "函数定义", "accurate", "语法分析", "签名比较"),
            ("R-1-7-6", "函数声明和函数定义中的返回类型必须一致", "声明定义返回类型必须一致", "函数定义", "accurate", "语法分析", "类型检查"),
            ("R-1-7-8", "禁止无返回值函数的返回语句带有返回值", "void函数不能返回值", "函数返回", "accurate", "语法分析", "返回语句检查"),
            ("R-1-7-9", "有返回值函数的返回语句必须带有返回值", "非void函数必须返回值", "函数返回", "accurate", "语法分析", "返回语句检查"),
            ("R-1-7-10", "函数返回值的类型必须与定义一致", "返回值类型必须一致", "函数返回", "accurate", "语法分析", "类型检查"),
            ("R-1-7-11", "具有返回值的函数，其返回值如果不被使用，调用时应有(void)说明", "未使用返回值需要(void)说明", "函数调用", "accurate", "语法分析", "返回值检查"),
            ("R-1-7-12", "无返回值的函数，调用时禁止再用(void)重复说明", "void函数不需要(void)说明", "函数调用", "accurate", "语法分析", "调用检查"),
            ("R-1-7-15", "禁止在函数参数表中使用省略号", "函数参数不能用省略号", "函数定义", "accurate", "语法分析", "参数检查"),
            
            # 语句使用规范
            ("R-1-8-3", "禁止使用无效语句", "不能有无效语句", "语句使用", "accurate", "语法分析", "语句检查"),
            ("R-1-8-4", "使用八进制数必须明确注释", "八进制数需要注释", "语句使用", "accurate", "语法分析", "常量检查"),
            ("R-1-8-5", "数字类型后缀必须使用大写字母", "数字后缀必须大写", "语句使用", "accurate", "语法分析", "字面量检查"),
            
            # 循环控制语法
            ("R-1-9-2", "for循环控制变量必须使用整数型变量", "for循环变量必须整型", "循环控制", "accurate", "语法分析", "类型检查"),
            ("R-1-9-4", "无限循环必须使用while(1)语句，禁止使用for(;;)等其它形式的语句", "无限循环必须用while(1)", "循环控制", "accurate", "语法分析", "循环结构检查"),
            
            # 类型转换规范
            ("R-1-10-1", "浮点型变量赋给整型变量必须使用强制转换", "浮点转整型需要强制转换", "类型转换", "accurate", "语法分析", "类型转换检查"),
            ("R-1-10-2", "长整数变量赋给短整数变量必须使用强制转换", "长整型转短整型需要强制转换", "类型转换", "accurate", "语法分析", "类型转换检查"),
            ("R-1-10-3", "double型变量赋给float型变量必须强制转换", "double转float需要强制转换", "类型转换", "accurate", "语法分析", "类型转换检查"),
            ("R-1-10-4", "指针变量的赋值类型必须与指针变量类型一致", "指针赋值类型必须一致", "类型转换", "accurate", "语法分析", "指针类型检查"),
            ("R-1-10-5", "将指针量赋予非指针变量或非指针量赋予指针变量，必须使用强制转换", "指针非指针转换需要强制转换", "类型转换", "accurate", "语法分析", "类型转换检查"),
            ("R-1-10-6", "禁止使用无实质作用的类型转换", "不能无意义类型转换", "类型转换", "accurate", "语法分析", "转换分析"),
            
            # 初始化语法
            ("R-1-11-2", "变量初始化禁止隐含依赖于系统的缺省", "初始化不能依赖系统默认值", "初始化", "accurate", "语法分析", "初始化检查"),
            ("R-1-11-3", "结构体初始化的嵌套结构必须与定义一致", "结构体初始化必须与定义一致", "初始化", "accurate", "语法分析", "结构体检查"),
            ("R-1-11-4", "枚举元素定义中的初始化必须完整", "枚举初始化必须完整", "初始化", "accurate", "语法分析", "枚举检查"),
            
            # 比较判断语法
            ("R-1-12-1", "禁止对逻辑量进行大于或小于的逻辑比较", "逻辑量不能大小比较", "比较判断", "accurate", "语法分析", "操作符检查"),
            ("R-1-12-4", "禁止对无符号数进行大于等于零或小于零的比较", "无符号数不能与零比较大小", "比较判断", "accurate", "语法分析", "类型检查"),
            ("R-1-12-5", "禁止无符号数与有符号数之间直接比较", "有符号无符号不能直接比较", "比较判断", "accurate", "语法分析", "类型检查"),
            
            # 变量命名和声明
            ("R-1-13-1", "禁止局部变量与全局变量同名", "局部全局变量不能同名", "变量命名", "accurate", "语法分析", "符号表检查"),
            ("R-1-13-2", "禁止函数形参与全局变量同名", "形参全局变量不能同名", "变量命名", "accurate", "语法分析", "符号表检查"),
            ("R-1-13-3", "禁止变量名与函数名同名", "变量函数不能同名", "变量命名", "accurate", "语法分析", "符号表检查"),
            ("R-1-13-4", "禁止变量名与标识名同名", "变量标识符不能同名", "变量命名", "accurate", "语法分析", "符号表检查"),
            ("R-1-13-5", "禁止变量名与枚举元素同名", "变量枚举元素不能同名", "变量命名", "accurate", "语法分析", "符号表检查"),
            ("R-1-13-6", "禁止变量名与typedef自定义的类型名同名", "变量typedef类型不能同名", "变量命名", "accurate", "语法分析", "符号表检查"),
            ("R-1-13-7", "禁止在内部块中重定义已有的变量名", "内部块不能重定义变量", "变量命名", "accurate", "语法分析", "作用域检查"),
            ("R-1-13-8", "禁止仅依赖大小写区分的变量", "变量不能仅大小写区分", "变量命名", "accurate", "语法分析", "命名检查"),
            ("R-1-13-9", "禁止仅依赖小写字母'l'与数字'1'区分的变量", "变量不能用l和1区分", "变量命名", "accurate", "语法分析", "命名检查"),
            ("R-1-13-10", "禁止仅依赖大写字母'O'与数字'0'区分的变量", "变量不能用O和0区分", "变量命名", "accurate", "语法分析", "命名检查"),
            ("R-1-13-11", "禁止单独使用小写字母'l'或大写字母'O'作为变量", "不能单独用l或O作变量名", "变量命名", "accurate", "语法分析", "命名检查"),
            ("R-1-13-12", "程序外部可改写的变量，必须使用volatile类型说明", "外部可改写变量必须volatile", "变量声明", "accurate", "语法分析", "类型修饰符检查"),
            ("R-1-13-13", "禁止在表达式中出现多个同一volatile类型变量的运算", "表达式中不能多个volatile变量", "变量使用", "accurate", "语法分析", "表达式分析"),
            ("R-1-13-14", "禁止将NULL做为整型数0使用", "NULL不能当整数0用", "变量使用", "accurate", "语法分析", "常量检查"),
            ("R-1-13-15", "禁止给无符号类型变量赋负值", "无符号变量不能赋负值", "变量使用", "accurate", "语法分析", "类型检查"),
            ("R-1-13-16", "用于表示字符串的数组必须以\\0结束", "字符串数组必须\\0结尾", "变量使用", "accurate", "语法分析", "字符串检查"),
            
            # C++专用规则
            ("R-2-2-2", "类中必须明确定义缺省构造函数", "类必须有默认构造函数", "类定义", "accurate", "语法分析", "类结构检查"),
            ("R-2-2-3", "单参数构造函数必须使用explicit声明", "单参数构造函数需要explicit", "类定义", "accurate", "语法分析", "构造函数检查"),
            ("R-2-2-5", "派生类构造函数必须在初始化列表中说明直接基类构造函数", "派生类构造函数需要基类初始化", "类定义", "accurate", "语法分析", "初始化列表检查"),
            ("R-2-3-1", "具有虚拟成员函数的类，析构函数必须是虚拟的", "有虚函数的类析构函数必须虚拟", "类定义", "accurate", "语法分析", "虚函数检查"),
            ("R-2-4-1", "基类虚拟函数的参数缺省值在派生类重写函数中禁止被改变", "重写虚函数不能改变默认参数", "虚函数", "accurate", "语法分析", "函数签名检查"),
            ("R-2-4-2", "派生类对基类虚拟函数重写的声明必须使用virtual显示说明", "重写虚函数必须用virtual", "虚函数", "accurate", "语法分析", "关键字检查"),
            ("R-2-4-3", "禁止非纯虚函数被纯虚拟函数重写", "非纯虚函数不能被纯虚函数重写", "虚函数", "accurate", "语法分析", "虚函数检查"),
            ("R-2-5-1", "禁止将不相关的指针类型强制转换为对象指针类型", "不相关指针不能强制转换", "类型转换", "accurate", "语法分析", "指针转换检查"),
            ("R-2-5-2", "指针或引用的类型转换中禁止移除const或volatile属性", "类型转换不能移除const/volatile", "类型转换", "accurate", "语法分析", "类型修饰符检查"),
        ]
    
    def _get_uncertain_rules(self) -> List[Tuple]:
        """获取不确定的规则列表"""
        return [
            # 指针和内存管理类规则
            ("R-1-3-3", "禁止对参数指针进行赋值", "参数指针不能赋值", "指针使用", "uncertain", "数据流分析", "指针使用模式分析"),
            ("R-1-3-4", "禁止将局部变量地址作为函数返回值返回", "局部变量地址不能返回", "指针使用", "uncertain", "生命周期分析", "作用域和生命周期跟踪"),
            ("R-1-3-5", "禁止使用或释放未分配空间或已被释放的指针", "不能使用未分配或已释放指针", "内存管理", "uncertain", "指针别名分析", "指针生命周期跟踪"),
            ("R-1-3-6", "指针变量被释放后必须设置为NULL", "释放后指针必须置NULL", "内存管理", "uncertain", "数据流分析", "指针状态跟踪"),
            ("R-1-3-8", "动态分配的指针变量第一次使用前必须进行是否为NULL的判别", "指针使用前必须检查NULL", "指针使用", "uncertain", "路径分析", "执行路径分析"),
            ("R-1-3-10", "禁止文件指针在退出时没有关闭文件", "文件指针必须关闭", "资源管理", "uncertain", "资源跟踪", "文件指针生命周期分析"),
            
            # 内存操作安全性
            ("R-1-6-14", "缓存区读取禁止操作越界", "缓冲区读取不能越界", "内存安全", "uncertain", "边界分析", "数组边界和数据流分析"),
            ("R-1-6-15", "缓存区写入禁止操作越界", "缓冲区写入不能越界", "内存安全", "uncertain", "边界分析", "数组边界和数据流分析"),
            ("R-1-6-16", "禁止使用已被释放了的内存空间", "不能使用已释放内存", "内存管理", "uncertain", "内存状态跟踪", "内存分配释放状态分析"),
            ("R-1-6-17", "被free的指针必须指向最初malloc/calloc分配的地址", "free指针必须是原始分配地址", "内存管理", "uncertain", "指针来源跟踪", "指针变化历史分析"),
            ("R-1-6-18", "禁止使用gets函数，应使用fgets函数替代", "不能使用gets函数", "函数使用", "uncertain", "安全性分析", "函数调用安全性检查"),
            ("R-1-6-19", "使用字符串赋值、拷贝、追加等函数时，禁止目标字符串储存空间越界", "字符串操作不能越界", "字符串安全", "uncertain", "长度分析", "字符串长度和缓冲区分析"),
            
            # 控制流分析类规则
            ("R-1-4-1", "在if-else if语句中必须使用else分支", "if-else if必须有else", "控制流", "uncertain", "分支覆盖分析", "条件覆盖性分析"),
            ("R-1-4-2", "条件判断分支如果为空，必须以单独一行的分号加注释进行明确说明", "空分支必须有注释说明", "控制流", "uncertain", "意图分析", "程序员意图理解"),
            ("R-1-4-7", "switch中的case和default必须以break或return终止，共用case必须加以明确注释", "switch分支必须终止或有注释", "控制流", "uncertain", "控制流分析", "fall-through意图分析"),
            ("R-1-5-1", "禁止从复合语句外goto到复合语句内，或由下向上goto", "goto不能跨复合语句或向上跳转", "控制流", "uncertain", "控制流结构分析", "goto目标和结构分析"),
            ("R-1-8-1", "禁止不可达语句", "不能有不可达语句", "控制流", "uncertain", "可达性分析", "复杂控制流分析"),
            ("R-1-8-2", "禁止不可达分支", "不能有不可达分支", "控制流", "uncertain", "分支可达性分析", "执行路径分析"),
            
            # 运算和数据流类规则
            ("R-1-6-8", "数组禁止越界使用", "数组不能越界访问", "数组访问", "uncertain", "边界分析", "复杂数组边界分析"),
            ("R-1-6-2", "禁止将越界整数赋给整型变量", "整数赋值不能越界", "类型转换", "uncertain", "数值范围分析", "数值范围和类型转换分析"),
            ("R-1-6-12", "除法运算中禁止被零除", "除法不能被零除", "运算安全", "uncertain", "数值分析", "除数值分析"),
            ("R-1-12-3", "禁止对浮点数进行是否相等的比较", "浮点数不能相等比较", "比较判断", "uncertain", "浮点精度分析", "浮点数精度和上下文分析"),
            ("R-1-12-2", "禁止对指针进行大于或小于的逻辑比较", "指针不能大小比较", "比较判断", "uncertain", "指针关系分析", "指针指向对象关系分析"),
            
            # 函数调用和返回值类规则
            ("R-1-7-7", "有返回值的函数必须通过返回语句返回", "有返回值函数必须有return", "函数返回", "uncertain", "路径分析", "所有执行路径分析"),
            ("R-1-7-13", "静态函数必须被使用", "静态函数必须有调用", "函数使用", "uncertain", "全程序分析", "函数调用图分析"),
            ("R-1-7-14", "禁止同一个表达式中调用多个顺序相关函数", "表达式中不能多个顺序相关函数调用", "函数调用", "uncertain", "副作用分析", "函数副作用和依赖分析"),
            ("R-1-7-16", "禁止使用直接或间接自调用函数", "不能递归调用", "函数调用", "uncertain", "调用图分析", "递归检测"),
            
            # 循环控制类规则
            ("R-1-9-1", "for循环控制变量必须使用局部变量", "for循环变量必须局部", "循环控制", "uncertain", "作用域分析", "变量作用域和使用模式分析"),
            ("R-1-9-3", "禁止在for循环体内部修改循环控制变量", "for循环体内不能修改控制变量", "循环控制", "uncertain", "数据流分析", "循环体内变量修改路径分析"),
            
            # 变量初始化和使用类规则
            ("R-1-11-1", "变量禁止未赋值就使用", "变量使用前必须赋值", "变量使用", "uncertain", "数据流分析", "复杂数据流分析"),
            
            # C++特定规则
            ("R-2-2-1", "构造函数中禁止使用全局变量", "构造函数不能用全局变量", "构造函数", "uncertain", "依赖分析", "构造函数执行上下文分析"),
            ("R-2-2-4", "类中所有成员变量必须在构造函数中初始化", "成员变量必须在构造函数初始化", "构造函数", "uncertain", "初始化路径分析", "所有构造函数路径分析"),
            ("R-2-1-1", "含有动态分配成员的类，必须编写拷贝构造函数，并重载赋值操作符", "动态成员类必须有拷贝构造和赋值操作符", "类设计", "uncertain", "资源管理分析", "类成员和资源管理模式分析"),
            ("R-2-1-2", "虚拟基类指针转换为派生类指针必须使用dynamic_cast转换", "虚基类指针转换必须用dynamic_cast", "类型转换", "uncertain", "类型层次分析", "类型层次和转换安全性分析"),
            ("R-2-1-3", "菱形层次结构的派生设计，对基类派生必须使用virtual说明", "菱形继承必须用virtual", "类设计", "uncertain", "继承层次分析", "整个类层次结构分析"),
            ("R-2-1-4", "抽象类中的复制操作符重载必须是保护的或私有的", "抽象类复制操作符必须protected/private", "类设计", "uncertain", "设计意图分析", "类设计意图理解"),
            ("R-2-3-2", "析构函数中禁止存在不是由自身捕获处理的异常", "析构函数不能有未捕获异常", "异常处理", "uncertain", "异常传播分析", "异常传播路径分析"),
            ("R-2-6-1", "使用new分配的内存空间，用完后必须使用delete释放", "new分配内存必须delete释放", "内存管理", "uncertain", "对象生命周期跟踪", "对象生命周期分析"),
            ("R-2-6-2", "必须delete释放new分配的内存空间", "必须delete释放new内存", "内存管理", "uncertain", "内存配对分析", "内存分配释放配对分析"),
            ("R-2-6-3", "被delete的指针必须使用new分配的地址", "delete指针必须是new分配的", "内存管理", "uncertain", "指针来源跟踪", "指针来源跟踪"),
        ]
    
    def _populate_keywords(self, cursor):
        """填充关键字映射数据"""
        # 为每个规则添加关键字映射，用于问题名称匹配
        keyword_mappings = [
            # 准确规则的关键字
            ("R-1-1-1", "宏定义", "primary"),
            ("R-1-1-1", "关键字", "secondary"),
            ("R-1-1-2", "标识", "primary"),
            ("R-1-1-2", "关键字", "secondary"),
            ("R-1-1-3", "typedef", "primary"),
            ("R-1-1-3", "重定义", "secondary"),
            ("R-1-1-4", "关键字", "primary"),
            ("R-1-1-4", "重定义", "secondary"),
            ("R-1-1-5", "#define", "primary"),
            ("R-1-1-5", "重复定义", "secondary"),
            ("R-1-1-6", "#define", "primary"),
            ("R-1-1-6", "#undef", "secondary"),
            ("R-1-1-6", "配对", "secondary"),
            ("R-1-1-7", "宏", "primary"),
            ("R-1-1-7", "括号", "secondary"),
            ("R-1-1-8", "结构", "primary"),
            ("R-1-1-8", "联合", "secondary"),
            ("R-1-1-8", "枚举", "secondary"),
            ("R-1-1-8", "标识名", "secondary"),
            ("R-1-1-9", "结构体", "primary"),
            ("R-1-1-9", "无名", "secondary"),
            ("R-1-1-10", "位定义", "primary"),
            ("R-1-1-10", "位长", "secondary"),
            ("R-1-1-11", "位定义", "primary"),
            ("R-1-1-11", "有符号", "secondary"),
            ("R-1-1-11", "无符号", "secondary"),
            ("R-1-1-12", "位定义", "primary"),
            ("R-1-1-12", "跨越", "secondary"),
            ("R-1-1-13", "函数声明", "primary"),
            ("R-1-1-13", "参数", "secondary"),
            ("R-1-1-14", "函数声明", "primary"),
            ("R-1-1-14", "原型", "secondary"),
            ("R-1-1-15", "函数", "primary"),
            ("R-1-1-15", "参数", "secondary"),
            ("R-1-1-15", "类型声明", "secondary"),
            ("R-1-1-16", "外部声明", "primary"),
            ("R-1-1-16", "变量", "secondary"),
            ("R-1-1-17", "函数体", "primary"),
            ("R-1-1-17", "外部声明", "secondary"),
            ("R-1-1-18", "数组", "primary"),
            ("R-1-1-18", "边界", "secondary"),
            ("R-1-1-19", "extern", "primary"),
            ("R-1-1-19", "初始化", "secondary"),
            ("R-1-1-20", "字符型", "primary"),
            ("R-1-1-20", "有符号", "secondary"),
            ("R-1-1-20", "无符号", "secondary"),
            ("R-1-1-21", "#include", "primary"),
            ("R-1-1-21", "绝对路径", "secondary"),
            ("R-1-1-22", "头文件", "primary"),
            ("R-1-1-22", "重复包含", "secondary"),
            ("R-1-1-23", "函数参数", "primary"),
            ("R-1-1-23", "void", "secondary"),
            
            # 不确定规则的关键字
            ("R-1-3-3", "参数指针", "primary"),
            ("R-1-3-3", "赋值", "secondary"),
            ("R-1-3-4", "局部变量", "primary"),
            ("R-1-3-4", "地址", "secondary"),
            ("R-1-3-4", "返回值", "secondary"),
            ("R-1-3-5", "指针", "primary"),
            ("R-1-3-5", "未分配", "secondary"),
            ("R-1-3-5", "已释放", "secondary"),
            ("R-1-3-6", "指针", "primary"),
            ("R-1-3-6", "释放", "secondary"),
            ("R-1-3-6", "NULL", "secondary"),
            ("R-1-3-8", "指针", "primary"),
            ("R-1-3-8", "NULL", "secondary"),
            ("R-1-3-8", "判别", "secondary"),
            ("R-1-3-10", "文件指针", "primary"),
            ("R-1-3-10", "关闭", "secondary"),
            ("R-1-6-8", "数组", "primary"),
            ("R-1-6-8", "越界", "secondary"),
            ("R-1-6-12", "除法", "primary"),
            ("R-1-6-12", "被零除", "secondary"),
            ("R-1-6-14", "缓存区", "primary"),
            ("R-1-6-14", "读取", "secondary"),
            ("R-1-6-14", "越界", "secondary"),
            ("R-1-6-15", "缓存区", "primary"),
            ("R-1-6-15", "写入", "secondary"),
            ("R-1-6-15", "越界", "secondary"),
            ("R-1-6-16", "内存", "primary"),
            ("R-1-6-16", "已释放", "secondary"),
            ("R-1-6-17", "free", "primary"),
            ("R-1-6-17", "malloc", "secondary"),
            ("R-1-6-17", "calloc", "secondary"),
            ("R-1-6-18", "gets", "primary"),
            ("R-1-6-18", "fgets", "secondary"),
            ("R-1-6-19", "字符串", "primary"),
            ("R-1-6-19", "越界", "secondary"),
            ("R-1-7-7", "返回值", "primary"),
            ("R-1-7-7", "返回语句", "secondary"),
            ("R-1-7-13", "静态函数", "primary"),
            ("R-1-7-13", "使用", "secondary"),
            ("R-1-7-14", "表达式", "primary"),
            ("R-1-7-14", "顺序相关", "secondary"),
            ("R-1-7-16", "递归", "primary"),
            ("R-1-7-16", "自调用", "secondary"),
            ("R-1-8-1", "不可达", "primary"),
            ("R-1-8-1", "语句", "secondary"),
            ("R-1-8-2", "不可达", "primary"),
            ("R-1-8-2", "分支", "secondary"),
            ("R-1-9-1", "for循环", "primary"),
            ("R-1-9-1", "控制变量", "secondary"),
            ("R-1-9-1", "局部变量", "secondary"),
            ("R-1-9-3", "for循环", "primary"),
            ("R-1-9-3", "控制变量", "secondary"),
            ("R-1-9-3", "修改", "secondary"),
            ("R-1-11-1", "变量", "primary"),
            ("R-1-11-1", "未赋值", "secondary"),
            ("R-1-11-1", "未初始化", "alias"),
            ("R-1-12-2", "指针", "primary"),
            ("R-1-12-2", "比较", "secondary"),
            ("R-1-12-3", "浮点数", "primary"),
            ("R-1-12-3", "相等", "secondary"),
            ("R-1-12-3", "比较", "secondary"),
        ]
        
        for rule_code, keyword, keyword_type in keyword_mappings:
            cursor.execute('''
                INSERT OR IGNORE INTO rule_keywords (rule_code, keyword, keyword_type)
                VALUES (?, ?, ?)
            ''', (rule_code, keyword, keyword_type))
    
    def get_rule_by_code(self, rule_code: str) -> Optional[Dict[str, Any]]:
        """根据规则编号获取规则信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM gjb8114_rules WHERE rule_code = ?
                ''', (rule_code,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"查询规则失败: {str(e)}")
            return None
    
    def classify_issue_by_rule_name(self, issue_name: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        根据问题名称分类问题
        
        Returns:
            tuple: (分类结果, 匹配的规则信息)
            分类结果: 'accurate', 'uncertain', 'unknown'
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. 优先从问题名称开头提取GJB规则编号（最准确的匹配方式）
                # 匹配格式：GJB_R_XX_XX_XX（两位数字）
                import re
                gjb_pattern = r'^(GJB_R_\d{2}_\d{2}_\d{2})'
                gjb_match = re.match(gjb_pattern, issue_name)
                
                if gjb_match:
                    rule_code = gjb_match.group(1)
                    logger.info(f"提取到GJB规则编号: {rule_code}")
                    
                    cursor.execute('''
                        SELECT * FROM gjb8114_rules WHERE rule_code = ?
                    ''', (rule_code,))
                    
                    row = cursor.fetchone()
                    if row:
                        rule_info = dict(row)
                        logger.info(f"GJB规则匹配成功: {rule_code} -> {rule_info['accuracy_type']}")
                        return rule_info['accuracy_type'], rule_info
                    else:
                        logger.warning(f"数据库中未找到GJB规则: {rule_code}")
                
                # 2. 如果没有精确匹配，尝试关键字匹配
                cursor.execute('''
                    SELECT DISTINCT r.*, rk.keyword, rk.keyword_type
                    FROM gjb8114_rules r
                    JOIN rule_keywords rk ON r.rule_code = rk.rule_code
                    WHERE ? LIKE '%' || rk.keyword || '%'
                    ORDER BY 
                        CASE rk.keyword_type 
                            WHEN 'primary' THEN 1 
                            WHEN 'secondary' THEN 2 
                            ELSE 3 
                        END,
                        LENGTH(rk.keyword) DESC
                ''', (issue_name,))
                
                rows = cursor.fetchall()
                if rows:
                    # 返回第一个匹配的规则（按优先级排序）
                    rule_info = dict(rows[0])
                    return rule_info['accuracy_type'], rule_info
                
                # 3. 没有匹配到任何规则
                return 'unknown', None
                
        except Exception as e:
            logger.error(f"分类问题失败: {str(e)}")
            return 'unknown', None
    
    def get_all_rules(self, accuracy_type: str = None) -> List[Dict[str, Any]]:
        """获取所有规则或指定类型的规则"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if accuracy_type:
                    cursor.execute('''
                        SELECT * FROM gjb8114_rules WHERE accuracy_type = ?
                        ORDER BY rule_code
                    ''', (accuracy_type,))
                else:
                    cursor.execute('''
                        SELECT * FROM gjb8114_rules ORDER BY rule_code
                    ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"获取规则列表失败: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, int]:
        """获取规则统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        accuracy_type,
                        COUNT(*) as count
                    FROM gjb8114_rules 
                    GROUP BY accuracy_type
                ''')
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                cursor.execute('SELECT COUNT(*) FROM gjb8114_rules')
                stats['total'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}

# 全局实例
_rules_db_instance = None

def get_rules_database() -> RulesDatabase:
    """获取规则数据库单例"""
    global _rules_db_instance
    if _rules_db_instance is None:
        _rules_db_instance = RulesDatabase()
    return _rules_db_instance
