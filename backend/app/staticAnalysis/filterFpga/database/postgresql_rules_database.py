"""
PostgreSQL版本的FPGA规则数据库访问类

提供FPGA Verilog和VHDL编码规则的查询接口
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

from app.staticAnalysis.filterFpga.database.postgresql_database import get_db_session
from app.staticAnalysis.filterFpga.database.postgresql_models import FPGARule
from app.staticAnalysis.filterFpga.utils.logger import setup_module_logger

logger = setup_module_logger(__name__, "postgresql_rules_database.log")


class PostgreSQLFPGARulesDatabase:
    """PostgreSQL版FPGA规则数据库管理"""
    
    def __init__(self):
        """初始化FPGA规则数据库"""
        pass
    
    @staticmethod
    def extract_rule_code(issue_name: str) -> Optional[str]:
        """
        从问题名称中提取FPGA规则编号
        
        支持格式：
        - Verilog强制: R-2-1, R-10-3 等
        - Verilog建议: A-1-1, A-14-2 等
        - Verilog新增一般准则: 5.9.1.a, 5.9.3.d 等
        - VHDL强制: 5.1.1, 5.10.3 等
        - VHDL建议: A-5.1.1, A-5.10.3 等
        
        Args:
            issue_name: 问题名称
            
        Returns:
            规则编号或None
        """
        if not issue_name:
            return None

        text = str(issue_name).strip()
        patterns = [
            r'^([RA]-\d+-\d+)',                 # Verilog: R-2-1 / A-2-5
            r'^(A-5\.\d+\.\d+(?:\.\d+)?)',  # VHDL建议: A-5.1.1 / A-5.10.3
            r'^(5\.\d+\.\d+\.[A-Za-z])',     # 新增Verilog一般准则: 5.9.1.a
            r'^(5\.\d+\.\d+(?:\.\d+)?)(?!\.[A-Za-z])',    # VHDL强制: 5.1.1 / 5.10.3，避免把 5.9.1.a 识别成 5.9.1
        ]

        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def get_rule_by_code(self, rule_code: str) -> Optional[Dict[str, Any]]:
        """根据规则编号获取规则信息"""
        session = get_db_session()
        try:
            # 调试：打印查询信息
            print(f"[FPGA规则查询] 查找规则: {rule_code}")
            # 调试：查看数据库中是否有规则
            count = session.query(FPGARule).count()
            print(f"[FPGA规则查询] 数据库中总共有 {count} 条规则")
            if count > 0:
                # 查找A开头的规则
                a_rules = session.query(FPGARule.rule_code).filter(FPGARule.rule_code.like('A-%')).limit(5).all()
                print(f"[FPGA规则查询] A开头的规则示例: {[r.rule_code for r in a_rules]}")
                # 查找5开头的规则
                five_rules = session.query(FPGARule.rule_code).filter(FPGARule.rule_code.like('5.%')).limit(5).all()
                print(f"[FPGA规则查询] 5开头的规则示例: {[r.rule_code for r in five_rules]}")
                # 精确查找当前规则
                exact_match = session.query(FPGARule).filter(FPGARule.rule_code == rule_code).first()
                print(f"[FPGA规则查询] 精确匹配 {rule_code}: {'找到' if exact_match else '未找到'}")
            
            rule = session.query(FPGARule).filter(FPGARule.rule_code == rule_code).first()
            print(f"[FPGA规则查询] 查询结果 rule是否为None: {rule is None}")
            
            if rule:
                print(f"[FPGA规则查询] 准备返回规则数据，accuracy_type={rule.accuracy_type}")
                # 在关闭session前就构建好字典，避免detached对象问题
                result = {
                    'id': rule.id,
                    'rule_code': rule.rule_code,
                    'rule_name': rule.rule_content,  # FPGA模型中没有rule_name，用rule_content代替
                    'rule_description': rule.rule_content,  # 同上
                    'rule_content': rule.rule_content,
                    'language': rule.language,
                    'rule_type': rule.rule_type,
                    'category': rule.category,
                    'chapter': rule.chapter,
                    'sequence': rule.sequence,
                    'accuracy_type': rule.accuracy_type,  # 关键字段！
                    'is_selected': rule.is_selected if rule.is_selected is not None else True  # 新增：勾选状态
                }
                print(f"[FPGA规则查询] 字典构建完成，准备返回")
                return result
            
            print(f"[FPGA规则查询] rule为None，返回None")
            return None
            
        except Exception as e:
            logger.error(f"查询FPGA规则失败: {str(e)}")
            print(f"[FPGA规则查询] 异常: {str(e)}")
            return None
        finally:
            session.close()
    
    def classify_issue_by_rule_name(self, issue_name: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        根据问题名称分类问题
        
        Returns:
            tuple: (规则类型, 匹配的规则信息)
            规则类型: 'mandatory'(强制), 'advisory'(建议), 'unknown'
        """
        session = get_db_session()
        try:
            # 1. 从问题名称中提取规则编号
            rule_code = self.extract_rule_code(issue_name)
            
            if rule_code:
                logger.info(f"提取到FPGA规则编号: {rule_code}")
                
                rule = session.query(FPGARule).filter(FPGARule.rule_code == rule_code).first()
                
                if rule:
                    rule_info = {
                        'rule_code': rule.rule_code,
                        'rule_content': rule.rule_content,
                        'language': rule.language,
                        'rule_type': rule.rule_type,
                        'category': rule.category,
                        'chapter': rule.chapter
                    }
                    logger.info(f"FPGA规则匹配成功: {rule_code} -> {rule.rule_type}")
                    return rule.rule_type, rule_info
                else:
                    logger.warning(f"数据库中未找到FPGA规则: {rule_code}")
            else:
                logger.debug(f"未从问题名称提取到规则编号: {issue_name[:100]}")
            
            # 2. 没有匹配到任何规则
            logger.warning(f"无法匹配FPGA规则，标记为unknown: {issue_name[:120]}")
            return 'unknown', None
            
        except Exception as e:
            logger.error(f"FPGA规则分类失败: {str(e)}")
            return 'unknown', None
        finally:
            session.close()
    
    def get_all_rules(self, language: str = None, rule_type: str = None) -> List[Dict[str, Any]]:
        """获取所有规则或指定条件的规则"""
        session = get_db_session()
        try:
            query = session.query(FPGARule)
            
            if language:
                query = query.filter(FPGARule.language == language)
            if rule_type:
                query = query.filter(FPGARule.rule_type == rule_type)
            
            rules = query.order_by(FPGARule.sequence).all()
            
            result = []
            for rule in rules:
                result.append({
                    'rule_code': rule.rule_code,
                    'rule_name': rule.rule_content,
                    'rule_content': rule.rule_content,
                    'language': rule.language,
                    'rule_type': rule.rule_type,
                    'accuracy_type': rule.accuracy_type if hasattr(rule, 'accuracy_type') and rule.accuracy_type else ('accurate' if rule.rule_type == 'mandatory' else 'uncertain'),
                    'is_selected': rule.is_selected if hasattr(rule, 'is_selected') and rule.is_selected is not None else True,
                    'category': rule.category,
                    'chapter': rule.chapter,
                    'sequence': rule.sequence
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取FPGA规则列表失败: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取FPGA规则统计信息"""
        session = get_db_session()
        try:
            total = session.query(FPGARule).count()
            
            # Verilog统计
            verilog_total = session.query(FPGARule).filter(FPGARule.language == 'Verilog').count()
            verilog_mandatory = session.query(FPGARule).filter(
                FPGARule.language == 'Verilog',
                FPGARule.rule_type == 'mandatory'
            ).count()
            verilog_advisory = session.query(FPGARule).filter(
                FPGARule.language == 'Verilog',
                FPGARule.rule_type == 'advisory'
            ).count()
            
            # VHDL统计
            vhdl_total = session.query(FPGARule).filter(FPGARule.language == 'VHDL').count()
            vhdl_mandatory = session.query(FPGARule).filter(
                FPGARule.language == 'VHDL',
                FPGARule.rule_type == 'mandatory'
            ).count()
            vhdl_advisory = session.query(FPGARule).filter(
                FPGARule.language == 'VHDL',
                FPGARule.rule_type == 'advisory'
            ).count()
            
            return {
                'total': total,
                'verilog': {
                    'total': verilog_total,
                    'mandatory': verilog_mandatory,
                    'advisory': verilog_advisory
                },
                'vhdl': {
                    'total': vhdl_total,
                    'mandatory': vhdl_mandatory,
                    'advisory': vhdl_advisory
                }
            }
            
        except Exception as e:
            logger.error(f"获取FPGA规则统计信息失败: {str(e)}")
            return {}
        finally:
            session.close()


# 全局单例
_fpga_rules_db_instance = None


def get_fpga_rules_database() -> PostgreSQLFPGARulesDatabase:
    """获取FPGA规则数据库单例"""
    global _fpga_rules_db_instance
    if _fpga_rules_db_instance is None:
        _fpga_rules_db_instance = PostgreSQLFPGARulesDatabase()
    return _fpga_rules_db_instance
