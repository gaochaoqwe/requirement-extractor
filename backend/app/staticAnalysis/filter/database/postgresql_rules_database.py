"""
PostgreSQL版本的规则数据库访问类

提供与SQLite版本相同的接口，但使用PostgreSQL数据库
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re

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

from app.staticAnalysis.filter.database.postgresql_database import get_db_session
from app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, GJB8114RuleKeyword, CWERule
from app.staticAnalysis.filter.utils.logger import setup_module_logger

logger = setup_module_logger(__name__, "postgresql_rules_database.log")


class PostgreSQLRulesDatabase:
    """PostgreSQL版GJB8114规则数据库管理"""
    
    def __init__(self):
        """初始化规则数据库"""
        pass
    
    @staticmethod
    def convert_gjb_format(gjb_code: str) -> str:
        """
        将 GJB_R_XX_XX_XX 格式转换为 R-X-X-X 格式
        
        Examples:
            GJB_R_01_07_11 -> R-1-7-11
            GJB_R_02_05_02 -> R-2-5-2
            GJB_R_01_10_04 -> R-1-10-4
        
        Args:
            gjb_code: GJB格式的规则编号
            
        Returns:
            转换后的规则编号，如果格式不匹配则返回原值
        """
        # 匹配 GJB_R_XX_XX_XX 格式
        pattern = r'^GJB_R_(\d{2})_(\d{2})_(\d{2})$'
        match = re.match(pattern, gjb_code)
        
        if match:
            # 提取三组数字并去掉前导零
            part1 = str(int(match.group(1)))
            part2 = str(int(match.group(2)))
            part3 = str(int(match.group(3)))
            # 拼接成 R-X-X-X 格式
            return f"R-{part1}-{part2}-{part3}"
        
        # 如果格式不匹配，返回原值
        return gjb_code
    
    @staticmethod
    def convert_to_gjb_format(rule_code: str) -> str:
        """
        将 R-X-X-X 格式转换为 GJB_R_XX_XX_XX 格式（反向转换）
        
        Examples:
            R-1-7-11 -> GJB_R_01_07_11
            R-2-5-2 -> GJB_R_02_05_02
            R-1-10-4 -> GJB_R_01_10_04
        
        Args:
            rule_code: 数据库格式的规则编号
            
        Returns:
            转换后的GJB格式规则编号，如果格式不匹配则返回原值
        """
        # 匹配 R-X-X-X 格式（X可以是1位或2位数字）
        pattern = r'^R-(\d+)-(\d+)-(\d+)$'
        match = re.match(pattern, rule_code)
        
        if match:
            # 提取三组数字并补零到两位
            part1 = match.group(1).zfill(2)
            part2 = match.group(2).zfill(2)
            part3 = match.group(3).zfill(2)
            # 拼接成 GJB_R_XX_XX_XX 格式
            return f"GJB_R_{part1}_{part2}_{part3}"
        
        # 如果格式不匹配，返回原值
        return rule_code
    
    def get_rule_by_code(self, rule_code: str) -> Optional[Dict[str, Any]]:
        """根据规则编号获取规则信息"""
        try:
            session = get_db_session()
            try:
                rule = session.query(GJB8114Rule).filter(GJB8114Rule.rule_code == rule_code).first()
                
                # 如果直接匹配失败，尝试不同格式之间的转换（处理前导零和前缀差异）
                if not rule:
                    alt_codes = []
                    # 1) 输入为 GJB_R_XX_XX_XX（带前导零）时，尝试：
                    #    - 去掉前导零但保留 GJB_R_ 前缀，例如 GJB_R_01_06_08 -> GJB_R_1_6_8
                    #    - 转换为 R-X-X-X 格式，例如 GJB_R_01_06_08 -> R-1-6-8
                    gjb_full_pattern = r'^GJB_R_(\d{2})_(\d{2})_(\d{2})$'
                    m_full = re.match(gjb_full_pattern, rule_code)
                    if m_full:
                        p1 = str(int(m_full.group(1)))
                        p2 = str(int(m_full.group(2)))
                        p3 = str(int(m_full.group(3)))
                        alt_codes.append(f"GJB_R_{p1}_{p2}_{p3}")
                        alt_codes.append(self.convert_gjb_format(rule_code))
                    else:
                        # 2) 输入为 R-X-X-X 时，尝试转换为 GJB_R_X_X_X（不补零）
                        r_pattern = r'^R-(\d+)-(\d+)-(\d+)$'
                        m_r = re.match(r_pattern, rule_code)
                        if m_r:
                            p1 = m_r.group(1)
                            p2 = m_r.group(2)
                            p3 = m_r.group(3)
                            alt_codes.append(f"GJB_R_{p1}_{p2}_{p3}")
                        else:
                            # 3) 输入为 GJB_R_X_X_X（已无前导零）时，尝试转换为 R-X-X-X
                            gjb_simple_pattern = r'^GJB_R_(\d+)_(\d+)_(\d+)$'
                            m_simple = re.match(gjb_simple_pattern, rule_code)
                            if m_simple:
                                gjb_to_r = f"R-{m_simple.group(1)}-{m_simple.group(2)}-{m_simple.group(3)}"
                                alt_codes.append(gjb_to_r)
                    
                    for alt in alt_codes:
                        if alt and alt != rule_code:
                            rule = session.query(GJB8114Rule).filter(GJB8114Rule.rule_code == alt).first()
                            if rule:
                                logger.info(f"GJB规则编号别名匹配成功: {rule_code} -> {alt}")
                                break
                
                if rule:
                    return {
                        'id': rule.id,
                        'rule_code': rule.rule_code,
                        'rule_name': rule.rule_name,
                        'rule_description': rule.rule_description,
                        'category': rule.category,
                        'accuracy_type': rule.accuracy_type,
                        'is_selected': rule.is_selected if rule.is_selected is not None else True,  # 新增：勾选状态
                        'analysis_complexity': rule.analysis_complexity,
                        'detection_method': rule.detection_method
                    }
                return None
            finally:
                session.close()
            
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
        session = get_db_session()
        try:
            # 1. 优先从问题名称开头提取GJB规则编号（最准确的匹配方式）
            gjb_pattern = r'^(GJB_R_\d{2}_\d{2}_\d{2})'
            gjb_match = re.match(gjb_pattern, issue_name)
            
            if gjb_match:
                original_code = gjb_match.group(1)  # GJB_R_01_07_11
                converted_code = self.convert_gjb_format(original_code)  # R-1-7-11
                logger.info(f"提取到GJB规则编号: {original_code} -> 转换为: {converted_code}")
                
                rule_info = self.get_rule_by_code(converted_code)
                
                if rule_info:
                    accuracy_type = rule_info.get('accuracy_type', 'uncertain')
                    logger.info(f"GJB规则匹配成功: {converted_code} -> {accuracy_type}")
                    return accuracy_type, rule_info
                else:
                    logger.warning(f"数据库中未找到GJB规则: {converted_code} (原始: {original_code})")
            else:
                # 未从名称开头提取到标准的GJB编号
                logger.debug(f"未从问题名称提取到GJB编号，尝试关键字匹配: {issue_name[:100]}")
            
            # 2. 如果没有精确匹配，尝试关键字匹配
            # 查询所有关键字
            keywords = session.query(GJB8114RuleKeyword).all()
            
            # 按优先级排序匹配
            matched_rules = []
            for kw in keywords:
                if kw.keyword in issue_name:
                    rule = session.query(GJB8114Rule).filter(GJB8114Rule.rule_code == kw.rule_code).first()
                    if rule:
                        priority = {'primary': 1, 'secondary': 2}.get(kw.keyword_type, 3)
                        matched_rules.append((priority, len(kw.keyword), rule))
            
            if matched_rules:
                # 按优先级和关键字长度排序
                matched_rules.sort(key=lambda x: (x[0], -x[1]))
                rule = matched_rules[0][2]
                
                rule_info = {
                    'rule_code': rule.rule_code,
                    'rule_name': rule.rule_name,
                    'rule_description': rule.rule_description,
                    'category': rule.category,
                    'accuracy_type': rule.accuracy_type,
                    'analysis_complexity': rule.analysis_complexity,
                    'detection_method': rule.detection_method
                }
                logger.info(f"关键字匹配成功: {rule.rule_code} -> {rule.accuracy_type}")
                return rule.accuracy_type, rule_info
            
            # 3. 没有匹配到任何规则
            logger.warning(f"无法通过编号或关键字匹配规则，标记为unknown: {issue_name[:120]}")
            return 'unknown', None
            
        except Exception as e:
            logger.error(f"分类问题失败: {str(e)}")
            return 'unknown', None
        finally:
            session.close()
    
    def get_all_rules(self, accuracy_type: str = None) -> List[Dict[str, Any]]:
        """获取所有规则或指定类型的规则"""
        session = get_db_session()
        try:
            if accuracy_type:
                rules = session.query(GJB8114Rule).filter(GJB8114Rule.accuracy_type == accuracy_type).order_by(GJB8114Rule.rule_code).all()
            else:
                rules = session.query(GJB8114Rule).order_by(GJB8114Rule.rule_code).all()
            
            result = []
            for rule in rules:
                result.append({
                    'rule_code': rule.rule_code,
                    'rule_name': rule.rule_name,
                    'rule_description': rule.rule_description,
                    'category': rule.category,
                    'accuracy_type': rule.accuracy_type,
                    'is_selected': rule.is_selected if rule.is_selected is not None else True,
                    'analysis_complexity': rule.analysis_complexity,
                    'detection_method': rule.detection_method
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取规则列表失败: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, int]:
        """获取规则统计信息"""
        session = get_db_session()
        try:
            total = session.query(GJB8114Rule).count()
            accurate = session.query(GJB8114Rule).filter(GJB8114Rule.accuracy_type == 'accurate').count()
            uncertain = session.query(GJB8114Rule).filter(GJB8114Rule.accuracy_type == 'uncertain').count()
            
            return {
                'total': total,
                'accurate': accurate,
                'uncertain': uncertain
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
        finally:
            session.close()


class PostgreSQLCWERulesDatabase:
    """PostgreSQL版CWE规则数据库管理类"""
    
    def __init__(self):
        """初始化CWE规则数据库"""
        pass
    
    def get_all_rules(self) -> List[Dict]:
        """获取所有规则"""
        session = get_db_session()
        try:
            rules = session.query(CWERule).order_by(CWERule.rule_code).all()
            
            result = []
            for rule in rules:
                result.append({
                    "rule_code": rule.rule_code,
                    "rule_name": rule.rule_name,
                    "accuracy_type": rule.accuracy_type,
                    "is_selected": rule.is_selected if rule.is_selected is not None else True,
                    "category": rule.category or "",
                    "description": rule.description or ""
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取所有CWE规则失败: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_rules_by_type(self, accuracy_type: str) -> List[Dict]:
        """
        获取指定类型的规则
        
        Args:
            accuracy_type: 'accurate' 或 'uncertain'
        
        Returns:
            规则列表
        """
        session = get_db_session()
        try:
            rules = session.query(CWERule).filter(CWERule.accuracy_type == accuracy_type).order_by(CWERule.rule_code).all()
            
            result = []
            for rule in rules:
                result.append({
                    "rule_code": rule.rule_code,
                    "rule_name": rule.rule_name,
                    "accuracy_type": rule.accuracy_type,
                    "is_selected": rule.is_selected if rule.is_selected is not None else True,
                    "category": rule.category or "",
                    "description": rule.description or ""
                })
            
            logger.info(f"获取{accuracy_type}类型的CWE规则: {len(result)}个")
            return result
            
        except Exception as e:
            logger.error(f"获取CWE规则失败: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_rule_by_code(self, rule_code: str) -> Optional[Dict]:
        """根据规则代码获取规则"""
        session = get_db_session()
        try:
            rule = session.query(CWERule).filter(CWERule.rule_code == rule_code).first()
            
            if rule:
                return {
                    "rule_code": rule.rule_code,
                    "rule_name": rule.rule_name,
                    "accuracy_type": rule.accuracy_type,
                    "category": rule.category or "",
                    "description": rule.description or ""
                }
            return None
            
        except Exception as e:
            logger.error(f"根据代码获取CWE规则失败: {str(e)}")
            return None
        finally:
            session.close()
    
    def classify_issue_by_rule_name(self, issue_name: str) -> Tuple[str, Optional[Dict]]:
        """
        根据问题名称分类 - 优先使用规则编号进行精确匹配
        
        Args:
            issue_name: 问题名称，例如 "S_02_01 未初始化的指针" 或 "C/ C++检测指针越界"
        
        Returns:
            (accuracy_type, rule_info) 元组
            accuracy_type: 'accurate' 或 'uncertain'
            rule_info: 规则信息字典或None
        """
        try:
            session = get_db_session()
            
            # 特殊情况：处理没有编号的规则 "C/ C++检测指针越界"
            if issue_name.strip() == "C/ C++检测指针越界":
                logger.info(f"CWE特殊规则匹配: {issue_name}")
                session.close()
                # 这个规则被认为是不确定的（因为需要复杂的数据流分析）
                return "uncertain", {
                    "rule_code": "SPECIAL_PTR_BOUND",
                    "rule_name": issue_name,
                    "accuracy_type": "uncertain",
                    "category": "指针越界",
                    "description": "检测C/C++代码中的指针越界问题"
                }
            
            # 1. 优先从问题名称开头提取CWE规则编号（最准确的匹配方式）
            cwe_pattern = r'^(S_\d{2}_\d{2}(?:_\d{2})?)'
            cwe_match = re.match(cwe_pattern, issue_name)
            
            if cwe_match:
                rule_code = cwe_match.group(1)
                logger.info(f"提取到CWE规则编号: {rule_code}")
                
                rule = session.query(CWERule).filter(CWERule.rule_code == rule_code).first()
                
                if rule:
                    logger.info(f"CWE规则精确匹配: {rule_code} -> {rule.accuracy_type}")
                    result = (rule.accuracy_type, {
                        "rule_code": rule.rule_code,
                        "rule_name": rule.rule_name,
                        "accuracy_type": rule.accuracy_type,
                        "category": rule.category or "",
                        "description": rule.description or ""
                    })
                    session.close()
                    return result
                else:
                    logger.warning(f"数据库中未找到CWE规则: {rule_code}")
            
            # 2. 如果编号匹配失败，尝试完全匹配规则名称
            rule = session.query(CWERule).filter(CWERule.rule_name == issue_name).first()
            
            if rule:
                logger.info(f"CWE规则完全匹配: {issue_name} -> {rule.accuracy_type}")
                result = (rule.accuracy_type, {
                    "rule_code": rule.rule_code,
                    "rule_name": rule.rule_name,
                    "accuracy_type": rule.accuracy_type,
                    "category": rule.category or "",
                    "description": rule.description or ""
                })
                session.close()
                return result
            
            # 3. 尝试模糊匹配（包含关键字）- 作为最后的备用方案
            description = issue_name
            if " " in issue_name:
                description = issue_name.split(" ", 1)[1]
            
            rule = session.query(CWERule).filter(CWERule.rule_name.like(f"%{description}%")).order_by(CWERule.rule_name).first()
            
            if rule:
                logger.info(f"CWE规则模糊匹配: {issue_name} -> {rule.accuracy_type}")
                result = (rule.accuracy_type, {
                    "rule_code": rule.rule_code,
                    "rule_name": rule.rule_name,
                    "accuracy_type": rule.accuracy_type,
                    "category": rule.category or "",
                    "description": rule.description or ""
                })
                session.close()
                return result
            
            session.close()
            logger.warning(f"CWE规则未匹配: {issue_name}，默认为uncertain")
            return "uncertain", None
            
        except Exception as e:
            logger.error(f"CWE规则分类失败: {str(e)}")
            return "uncertain", None
    
    def get_statistics(self) -> Dict:
        """获取规则统计信息"""
        try:
            session = get_db_session()
            
            total = session.query(CWERule).count()
            accurate = session.query(CWERule).filter(CWERule.accuracy_type == 'accurate').count()
            uncertain = session.query(CWERule).filter(CWERule.accuracy_type == 'uncertain').count()
            
            session.close()
            
            return {
                "total": total,
                "accurate": accurate,
                "uncertain": uncertain
            }
            
        except Exception as e:
            logger.error(f"获取CWE统计信息失败: {str(e)}")
            return {"total": 0, "accurate": 0, "uncertain": 0}


# 全局单例
_gjb_rules_db_instance = None
_cwe_rules_db_instance = None


def get_gjb_rules_database() -> PostgreSQLRulesDatabase:
    """获取GJB规则数据库单例"""
    global _gjb_rules_db_instance
    if _gjb_rules_db_instance is None:
        _gjb_rules_db_instance = PostgreSQLRulesDatabase()
    return _gjb_rules_db_instance


def get_cwe_rules_database() -> PostgreSQLCWERulesDatabase:
    """获取CWE规则数据库单例"""
    global _cwe_rules_db_instance
    if _cwe_rules_db_instance is None:
        _cwe_rules_db_instance = PostgreSQLCWERulesDatabase()
    return _cwe_rules_db_instance

