"""
配置项测试内容生成器

负责生成配置项测试中的测试描述和测试方法。
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

# 🔧 修复：从新的ai_services导入moxingfenxi和generate_test_cases
try:
    from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.ai_services.ai_client import moxingfenxi, generate_test_cases
except ImportError:
    try:
        from ..ai_services.ai_client import moxingfenxi, generate_test_cases
    except ImportError:
        # 最后的备用方案
        def moxingfenxi(str_temp, ceshi_leixing, jianceyi_flag=0):
            return "测试内容描述", "测试方法描述"
        def generate_test_cases(ceshi_neirong, ceshi_leixing, jianceyi_flag, use_custom_prompt=False):
            return []

try:
    from ....utils.logging_utils.logger import log_info, log_debug, log_warning, log_error
except ImportError:
    try:
        from .....utils.logging_utils.logger import log_info, log_debug, log_warning, log_error
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_debug, log_warning, log_error

# 组织资产数据库检索增强器
try:
    from .asset_database_enhancer import asset_enhancer
except ImportError:
    try:
        from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.content_generators.asset_database_enhancer import asset_enhancer
    except ImportError:
        # 如果导入失败，创建一个占位符
        class DummyAssetEnhancer:
            def enhance_test_content(self, *args, **kwargs):
                return None
        asset_enhancer = DummyAssetEnhancer()

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemTestContentGenerator:
    """配置项测试内容生成器"""
    
    def __init__(self):
        """初始化测试内容生成器"""
        self.logger = logger
        # 本地数据库与Excel加载已完全移除；仅依赖AI与资产增强
    
    # 本地数据库/Excel相关方法已移除
    
    def generate_test_content(
        self,
        test_items: List[Dict[str, Any]],
        ai_config: Dict[str, Any],
        product_type: Optional[str] = None
    ) -> Tuple[List[str], List[str]]:
        """
        生成测试描述和测试方法
        
        Args:
            test_items: 测试项列表
            ai_config: AI配置信息
            product_type: 产品类型（转塔、对抗告警、光电雷达、吊舱、火控、外挂、显示）
            
        Returns:
            Tuple[List[str], List[str]]: (测试描述列表, 测试方法列表)
        """
        try:
            self.logger.info(f"开始生成{len(test_items)}个测试项的测试内容")
            
            test_descriptions = []
            test_methods = []
            
            for i, test_item in enumerate(test_items):
                test_name = test_item.get('name', '')
                # 优先使用需求子项描述作为AI提示词来源，若无则回退到需求描述
                requirement_sub_description = test_item.get('requirement_sub_description', '')
                requirement_description = requirement_sub_description if (isinstance(requirement_sub_description, str) and requirement_sub_description.strip()) \
                    else test_item.get('requirement_description', '')
                
                # 🔧 修复：增强字符串处理的健壮性
                safe_test_name = str(test_name) if test_name else ''
                safe_requirement_description = str(requirement_description) if requirement_description else ''
                
                # 生成单个测试项的内容
                description, method = self._generate_single_test_content(
                    safe_test_name, safe_requirement_description, ai_config, product_type
                )
                
                # 🔧 修复：确保返回值是字符串
                safe_description = str(description) if description else ''
                safe_method = str(method) if method else ''
                
                test_descriptions.append(safe_description)
                test_methods.append(safe_method)
            
            self.logger.info("测试内容生成完成")
            log_info(f"[DEBUG] 最终生成了{len(test_descriptions)}个描述和{len(test_methods)}个方法", "test_content_generator")
            return test_descriptions, test_methods
            
        except Exception as e:
            # 🔧 修复：添加详细的异常信息和堆栈跟踪
            import traceback
            error_details = traceback.format_exc()
            self.logger.error(f"生成测试内容时发生错误: {str(e)}")
            self.logger.error(f"详细错误信息:\n{error_details}")
            log_error(f"TestContentGenerator异常: {str(e)}", "test_content_generator")
            log_error(f"异常堆栈:\n{error_details}", "test_content_generator")
            
            # 返回默认内容
            default_descriptions = [f'测试软件{item.get("name", "")}功能实现是否正常' for item in test_items]
            default_methods = [f'通过检测仪发送测试指令,通过检测仪状态监控界面查看测试软件{item.get("name", "")}功能实现是否正常' for item in test_items]
            return default_descriptions, default_methods
    
    def _generate_single_test_content(
        self,
        test_name: str,
        requirement_description: str,
        ai_config: Dict[str, Any],
        product_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """生成单个测试项的测试内容"""
        try:
            log_debug(f"[DEBUG] _generate_single_test_content 开始", "test_content_generator")
            self.logger.info(f"   ai_config: {ai_config}")
            
            # 🔧 修复：移除错误的预判断逻辑，所有测试项都应该生成功能测试内容
            # 功能测试项是基础，必须的！性能和边界测试项由PerformanceSeparator额外提取
            
            log_info(f"[FUNCTIONAL_TEST] 生成功能测试项: {test_name}", "test_content_generator")
            
            # 检查AI开关，如果没有明确设置，默认启用AI生成
            enable_description_ai = ai_config.get('enable_test_description', True)  # 默认启用
            enable_method_ai = ai_config.get('enable_test_method', True)  # 默认启用
            
            if enable_description_ai or enable_method_ai:
                log_info(f"[FUNCTIONAL_TEST] 功能测试项启用AI生成 (描述: {enable_description_ai}, 方法: {enable_method_ai})", "test_content_generator")
                
                # 🔧 修复：确保需求描述是标准的中文格式
                formatted_requirement = self._format_requirement_for_ai(requirement_description, test_name)
                
                return self._generate_ai_test_content(
                    test_name, formatted_requirement, ai_config,
                    enable_description_ai, enable_method_ai, product_type
                )
            else:
                log_info(f"[FUNCTIONAL_TEST] 功能测试项使用默认内容", "test_content_generator")
                # 使用默认内容
                default_description = f"验证{test_name}的功能是否符合需求规定。"
                default_method = f"按照测试规范对{test_name}进行功能验证。"
                return default_description, default_method
            
        except Exception as e:
            log_error(f"生成测试内容失败: {e}", "test_content_generator")
            import traceback
            log_error(f"错误详情:\n{traceback.format_exc()}", "test_content_generator")
            # 返回默认内容作为备用
            return f"验证{test_name}的功能是否符合需求规定。", f"按照测试规范对{test_name}进行功能验证。"
    
    # 本地数据库搜索功能已移除
    
    def _generate_ai_test_content(
        self,
        test_name: str,
        requirement_description: str,
        ai_config: Dict[str, Any],
        enable_description_ai: bool,
        enable_method_ai: bool,
        product_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """使用AI生成测试内容"""
        try:
            log_info(f"[AI_GENERATE] 开始为功能测试项生成AI内容: {test_name}", "test_content_generator")
            log_info(f"[AI_GENERATE] AI生成配置 - 描述: {enable_description_ai}, 方法: {enable_method_ai}", "test_content_generator")
            
            # 获取检测仪标志
            jianceyi_flag = ai_config.get('jianceyi_flag', '无检测仪')
            
            # 🔧 记录完整的AI请求信息
            log_info("=" * 120, "test_content_generator")
            log_info(f"[AI_REQUEST_FULL] 即将发送给AI的完整功能测试请求:", "test_content_generator")
            log_info(f"[AI_REQUEST_FULL] 测试项名称: {test_name}", "test_content_generator")
            log_info(f"[AI_REQUEST_FULL] 测试类型: 功能测试", "test_content_generator")
            log_info(f"[AI_REQUEST_FULL] 检测仪标志: {jianceyi_flag}", "test_content_generator")
            log_info(f"[AI_REQUEST_FULL] 需求描述内容:\n{requirement_description}", "test_content_generator")
            log_info(f"[AI_REQUEST_FULL] 产品类型: {product_type}", "test_content_generator")
            log_info("=" * 120, "test_content_generator")
            
            # 使用资产数据库增强器增强提示词
            enhanced_requirement = requirement_description
            if product_type and hasattr(asset_enhancer, 'enhance_prompt_with_asset_data'):
                try:
                    log_info(f"[DB_MATCH] ========== 测试项数据库匹配开始 ==========", "test_content_generator")
                    log_info(f"[DB_MATCH] 测试项: '{test_name}'", "test_content_generator")
                    log_info(f"[DB_MATCH] 产品类型: '{product_type}'", "test_content_generator")
                    
                    enhanced_requirement = asset_enhancer.enhance_prompt_with_asset_data(
                        test_item_name=test_name,
                        original_prompt=requirement_description,
                        product_type=product_type
                    )
                    
                    if enhanced_requirement != requirement_description:
                        log_info(f"[DB_MATCH] ✓ 数据库匹配成功，提示词已增强", "test_content_generator")
                        log_info(f"[DB_MATCH] 原始长度: {len(requirement_description)} -> 增强后长度: {len(enhanced_requirement)}", "test_content_generator")
                    else:
                        log_warning(f"[DB_MATCH] ✗ 数据库匹配失败，使用原始提示词", "test_content_generator")
                    
                    log_info(f"[DB_MATCH] ==========================================", "test_content_generator")
                except Exception as e:
                    log_error(f"[DB_MATCH] ✗ 资产数据库增强异常: {e}", "test_content_generator")
                    log_info(f"[DB_MATCH] 使用原始提示词继续处理", "test_content_generator")
                    enhanced_requirement = requirement_description
            else:
                log_info(f"[DB_MATCH] 未指定产品类型或增强器不可用，跳过数据库匹配", "test_content_generator")
                log_info(f"[DB_MATCH] (产品类型: {product_type}, 增强器可用: {hasattr(asset_enhancer, 'enhance_prompt_with_asset_data')})", "test_content_generator")
            
            # 获取数据库匹配的内容（用于最终合并）
            db_descriptions, db_methods = [], []
            if product_type and hasattr(asset_enhancer, 'get_matched_database_content'):
                try:
                    db_descriptions, db_methods = asset_enhancer.get_matched_database_content(
                        test_item_name=test_name,
                        product_type=product_type
                    )
                except Exception as e:
                    log_error(f"[DB_CONTENT] 获取数据库内容失败: {e}", "test_content_generator")
            
            # 调用AI生成内容
            ai_description, ai_method = moxingfenxi(
                str_temp=enhanced_requirement,
                ceshi_leixing="功能测试",
                jianceyi_flag=jianceyi_flag,
                test_name=test_name
            )
            
            # 🔧 记录AI返回的完整原始结果
            log_info("=" * 120, "test_content_generator")
            log_info(f"[AI_RESPONSE_FULL] AI返回的完整原始结果:", "test_content_generator")
            log_info(f"[AI_RESPONSE_FULL] 原始测试描述: '{ai_description}'", "test_content_generator")
            log_info(f"[AI_RESPONSE_FULL] 原始测试方法: '{ai_method}'", "test_content_generator")
            log_info("=" * 120, "test_content_generator")
            
            # 根据开关决定使用AI生成的内容还是默认内容
            ai_final_description = ai_description if enable_description_ai else f"验证{test_name}的功能是否符合需求规定。"
            ai_final_method = ai_method if enable_method_ai else f"按照测试规范对{test_name}进行功能验证。"
            
            # 🔧 合并数据库内容和AI内容
            final_description = self._merge_database_and_ai_content(db_descriptions, ai_final_description, "测试内容")
            final_method = self._merge_database_and_ai_content(db_methods, ai_final_method, "测试方法")
            
            log_info(f"[AI_GENERATE] 功能测试项AI内容生成完成: {test_name}", "test_content_generator")
            log_debug(f"[AI_GENERATE] 最终描述长度: {len(final_description)}, 方法长度: {len(final_method)}", "test_content_generator")
            
            return final_description, final_method
            
        except Exception as e:
            log_error(f"[AI_GENERATE] AI生成功能测试内容失败: {e}", "test_content_generator")
            import traceback
            log_error(f"[AI_GENERATE] 错误详情:\n{traceback.format_exc()}", "test_content_generator")
            # 返回默认内容作为备用
            return f"验证{test_name}的功能是否符合需求规定。", f"按照测试规范对{test_name}进行功能验证。"
    
    def _merge_database_and_ai_content(self, db_content_list: List[str], ai_content: str, content_type: str) -> str:
        """
        合并数据库内容和AI生成内容
        
        Args:
            db_content_list: 数据库中匹配的内容列表
            ai_content: AI生成的内容
            content_type: 内容类型（用于日志）
            
        Returns:
            str: 合并后的内容
        """
        try:
            if not db_content_list:
                log_info(f"[CONTENT_MERGE] 无数据库{content_type}，直接使用AI内容", "test_content_generator")
                return ai_content
            
            log_info(f"[CONTENT_MERGE] ========== 开始合并{content_type} ==========", "test_content_generator")
            log_info(f"[CONTENT_MERGE] 数据库{content_type}数量: {len(db_content_list)}", "test_content_generator")
            log_info(f"[CONTENT_MERGE] AI{content_type}: '{ai_content}'", "test_content_generator")
            
            # 合并内容：数据库内容 + AI内容
            merged_parts = []
            
            # 添加数据库内容（检查是否已有编号）
            for i, db_content in enumerate(db_content_list, 1):
                # 如果数据库内容已经有编号，直接使用；否则添加编号
                if db_content.strip() and db_content.strip()[0].isdigit():
                    # 已有编号，直接使用
                    merged_parts.append(db_content)
                else:
                    # 没有编号，添加编号
                    merged_parts.append(f"{i}{db_content}")
            
            # 添加AI内容（继续编号）
            if ai_content and ai_content.strip():
                # AI内容可能包含多个测试项，尝试用换行或" | "分隔
                if '\n' in ai_content:
                    ai_items = [item.strip() for item in ai_content.split('\n') if item.strip()]
                else:
                    ai_items = [item.strip() for item in ai_content.split(' | ') if item.strip()]
                
                for ai_item in ai_items:
                    next_number = len(merged_parts) + 1
                    # 如果AI内容已经有编号，重新编号以保持连续性
                    ai_content_clean = ai_item.strip()
                    if ai_content_clean and ai_content_clean[0].isdigit():
                        # 去掉开头的编号（如"1"、"2"等）
                        import re
                        ai_content_clean = re.sub(r'^\d+', '', ai_content_clean)
                    
                    merged_parts.append(f"{next_number}{ai_content_clean}")
            
            merged_content = "\n".join(merged_parts)
            
            log_info(f"[CONTENT_MERGE] ✓ {content_type}合并完成", "test_content_generator")
            log_info(f"[CONTENT_MERGE] 最终{content_type}: '{merged_content}'", "test_content_generator")
            log_info(f"[CONTENT_MERGE] ==========================================", "test_content_generator")
            
            return merged_content
            
        except Exception as e:
            log_error(f"[CONTENT_MERGE] {content_type}合并失败: {e}", "test_content_generator")
            import traceback
            log_error(f"[CONTENT_MERGE] 错误详情: {traceback.format_exc()}", "test_content_generator")
            # 出错时返回AI内容
            return ai_content
    
    # AI优化旧数据库内容的功能已移除，统一走AI直生或默认回退
    
    def _generate_default_content(self, test_name: str) -> Tuple[str, str]:
        """生成默认的测试内容"""
        if '故障' in test_name or '报警检测' in test_name:
            description = f'测试软件{test_name}功能实现是否正常'
            method = f'通过代码插桩设置软件故障,通过检测仪发送自检指令,通过检测仪状态监控界面查看测试软件{test_name}功能实现是否正常'
        else:
            description = f'测试软件{test_name}功能实现是否正常'
            method = f'通过检测仪发送测试指令,通过检测仪状态监控界面查看测试软件{test_name}功能实现是否正常'
        
        return description, method
    
    def _generate_default_description(self, test_name: str) -> str:
        """生成默认的测试项描述"""
        if '故障' in test_name or '报警检测' in test_name:
            return f'测试软件{test_name}功能实现是否正常'
        else:
            return f'测试软件{test_name}功能实现是否正常'
    
    def _generate_default_method(self, test_name: str) -> str:
        """生成默认的测试方法"""
        if '故障' in test_name or '报警检测' in test_name:
            return f'通过代码插桩设置软件故障,通过检测仪发送自检指令,通过检测仪状态监控界面查看测试软件{test_name}功能实现是否正常'
        else:
            return f'通过检测仪发送测试指令,通过检测仪状态监控界面查看测试软件{test_name}功能实现是否正常'
    
    def generate_test_types(self, test_items: List[Dict[str, Any]]) -> List[str]:
        """
        生成测试类型列表
        
        Args:
            test_items: 测试项列表
            
        Returns:
            List[str]: 测试类型列表
        """
        try:
            from ...content_analysis.test_type_classifier import ceshi_leixing_biaoshi_choose
            
            test_types = []
            
            for test_item in test_items:
                test_name = test_item.get('name', '')
                _, test_type = ceshi_leixing_biaoshi_choose(test_name)
                test_types.append(test_type)
            
            self.logger.info(f"生成了{len(test_types)}个测试类型")
            return test_types
            
        except Exception as e:
            self.logger.error(f"生成测试类型时发生错误: {str(e)}")
            return ['功能测试'] * len(test_items)
    
    def validate_test_content(
        self,
        test_descriptions: List[str],
        test_methods: List[str]
    ) -> Dict[str, Any]:
        """
        验证测试内容的质量
        
        Args:
            test_descriptions: 测试描述列表
            test_methods: 测试方法列表
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            validation_result = {
                'total_items': len(test_descriptions),
                'valid_descriptions': 0,
                'valid_methods': 0,
                'empty_descriptions': 0,
                'empty_methods': 0,
                'error_descriptions': 0,
                'error_methods': 0,
                'quality_score': 0
            }
            
            for i, (desc, method) in enumerate(zip(test_descriptions, test_methods)):
                # 检查描述
                if not desc or desc.strip() == '':
                    validation_result['empty_descriptions'] += 1
                elif desc == 'error':
                    validation_result['error_descriptions'] += 1
                else:
                    validation_result['valid_descriptions'] += 1
                
                # 检查方法
                if not method or method.strip() == '':
                    validation_result['empty_methods'] += 1
                elif method == 'error':
                    validation_result['error_methods'] += 1
                else:
                    validation_result['valid_methods'] += 1
            
            # 计算质量分数
            total_items = validation_result['total_items']
            if total_items > 0:
                valid_items = min(validation_result['valid_descriptions'], validation_result['valid_methods'])
                validation_result['quality_score'] = round(valid_items / total_items * 100, 2)
            
            self.logger.info(f"测试内容验证完成，质量分数: {validation_result['quality_score']}%")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证测试内容时发生错误: {str(e)}")
            return {}
    
    def get_content_statistics(
        self,
        test_descriptions: List[str],
        test_methods: List[str]
    ) -> Dict[str, Any]:
        """
        获取测试内容统计信息
        
        Args:
            test_descriptions: 测试描述列表
            test_methods: 测试方法列表
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            statistics = {
                'total_items': len(test_descriptions),
                'avg_description_length': 0,
                'avg_method_length': 0,
                'content_sources': {
                    'ai_generated': 0,
                    'default_generated': 0
                }
            }
            
            # 计算平均长度
            if test_descriptions:
                total_desc_length = sum(len(desc) for desc in test_descriptions if desc)
                statistics['avg_description_length'] = round(total_desc_length / len(test_descriptions), 2)
            
            if test_methods:
                total_method_length = sum(len(method) for method in test_methods if method)
                statistics['avg_method_length'] = round(total_method_length / len(test_methods), 2)
            
            # 分析内容来源（基于内容特征的简单判断）
            for desc, method in zip(test_descriptions, test_methods):
                if desc and method:
                    if '通过检测仪发送测试指令' in method and len(desc) < 50:
                        statistics['content_sources']['default_generated'] += 1
                    else:
                        statistics['content_sources']['ai_generated'] += 1
            
            self.logger.info(f"测试内容统计: 共{statistics['total_items']}项")
            return statistics
            
        except Exception as e:
            self.logger.error(f"获取测试内容统计时发生错误: {str(e)}")
            return {}
    
    def _is_performance_test_item(self, test_name: str, requirement_description: str) -> bool:
        """
        检测是否为性能测试项（使用传统算法预判断）
        
        Args:
            test_name: 测试项名称
            requirement_description: 需求描述
            
        Returns:
            bool: 是否为性能测试项
        """
        try:
            # 🔧 优化：先用传统算法预判断，避免不必要的AI请求
            
            # 1. 检查测试名称中是否包含性能测试关键词
            performance_name_keywords = ['性能测试', '性能', '响应时间', '吞吐量', '并发', '负载', '压力']
            if any(keyword in test_name for keyword in performance_name_keywords):
                log_debug(f"[PERFORMANCE_DETECT] 测试名称包含性能关键词: {test_name}", "test_content_generator")
                return True
            
            # 2. 基于hanshutiqu_kaifa模块的性能测试判断算法
            # 性能测试的关键词列表（参考hanshutiqu_kaifa/xuqiushuomiing_duqu.py）
            performance_keywords = [
                # 时间相关
                '时间', '秒', '分钟', '小时', 'ms', 's', 'min', '毫秒', '微秒', '次/秒',
                # 性能指标
                '频率', '周期', '速度', '吞吐量', '并发用户数', '资源利用率', '错误率', 
                '可扩展性', '延迟', '带宽', '命中率', '效率', '容错性', 'TPS', 'QPS',
                # 性能比较符号
                '≤', '≥', '<', '>', '不超过', '不少于', '至少', '最多',
                # 性能描述
                '性能', '响应时间', '处理时间', '延迟'
            ]
            
            # 不进行性能测试的关键词列表
            unperformance_keywords = ['任意时间', '补偿']
            
            # 控制哪些测试项目不拆分为性能测试的关键词列表
            exclude_performance_keywords = [
                '安全性', '可靠性', '接口', '接收', '发送', '叠加', 
                '积分时间', '校正系数', '参数设置', '初始化'
            ]
            
            # 3. 检查测试名称是否在排除列表中
            for exclude_keyword in exclude_performance_keywords:
                if exclude_keyword in test_name:
                    log_debug(f"[PERFORMANCE_DETECT] 测试名称包含排除关键词 '{exclude_keyword}': {test_name}", "test_content_generator")
                    return False
            
            # 4. 处理不同类型的需求描述
            search_text = ""
            if isinstance(requirement_description, dict):
                # 如果是字典，优先检查performance字段
                performance_field = requirement_description.get('performance', '')
                if performance_field and str(performance_field).strip():
                    log_debug(f"[PERFORMANCE_DETECT] 发现性能字段: {performance_field}", "test_content_generator")
                    return True
                
                # 合并其他字段内容进行检测
                for key, value in requirement_description.items():
                    if value:
                        search_text += f"{str(value)} "
            elif isinstance(requirement_description, str):
                search_text = requirement_description
            else:
                return False
            
            # 5. 检查是否包含不进行性能测试的关键词
            for unperformance_keyword in unperformance_keywords:
                if unperformance_keyword in search_text:
                    log_debug(f"[PERFORMANCE_DETECT] 发现排除性能测试关键词 '{unperformance_keyword}'", "test_content_generator")
                    return False
            
            # 6. 检查是否包含性能相关关键词
            found_performance_keywords = []
            for keyword in performance_keywords:
                if keyword in search_text:
                    found_performance_keywords.append(keyword)
            
            if found_performance_keywords:
                log_debug(f"[PERFORMANCE_DETECT] 发现性能关键词: {found_performance_keywords}", "test_content_generator")
                return True
            
            # 7. 特殊检查：查找"g) 性能:"段落
            if "g) 性能:" in search_text or "g)性能:" in search_text:
                log_debug(f"[PERFORMANCE_DETECT] 发现性能段落标识", "test_content_generator")
                return True
            
            log_debug(f"[PERFORMANCE_DETECT] 未发现性能测试相关内容: {test_name}", "test_content_generator")
            return False
            
        except Exception as e:
            log_warning(f"[PERFORMANCE_DETECT] 性能测试检测失败: {e}", "test_content_generator")
            return False
    
    def _is_boundary_test_item(self, test_name: str, requirement_description: str) -> bool:
        """
        检测是否为边界测试项（使用传统算法预判断）
        
        Args:
            test_name: 测试项名称
            requirement_description: 需求描述
            
        Returns:
            bool: 是否为边界测试项
        """
        try:
            # 🔧 优化：先用传统算法预判断，避免不必要的AI请求
            
            # 1. 检查测试名称中是否包含边界测试关键词
            boundary_name_keywords = ['边界测试', '边界', '最大', '最小', '极限', '范围']
            if any(keyword in test_name for keyword in boundary_name_keywords):
                log_debug(f"[BOUNDARY_DETECT] 测试名称包含边界关键词: {test_name}", "test_content_generator")
                return True
            
            # 2. 基于hanshutiqu_kaifa模块的边界测试判断算法
            # 边界测试关键词组1（参考hanshutiqu_kaifa/xuqiushuomiing_duqu.py）
            boundary_keywords_group1 = [
                '最大', '最小', '大于', '小于', '不超过', '超出', '超时',
                '至少', '最少', '不少于', '最多', '范围', '区间', '边界', '限制', '约束'
            ]
            
            # 边界测试关键词组2
            boundary_keywords_group2 = [
                '范围', '精度', '极限', '温度', '阈值', '个数', '秒', '分钟', 'min',
                '字符', '位', '个', '项', '条', '次', '值', '数据', '输入', '输出', '参数', '配置'
            ]
            
            # 控制哪些测试项目不拆分为边界测试的关键词列表
            exclude_boundary_keywords = [
                '初始化', '安全性', '可靠性', '边界', '接口', '接收', '发送', 
                '时间', '校正系数', '参数设置'
            ]
            
            # 3. 检查测试名称是否在排除列表中
            for exclude_keyword in exclude_boundary_keywords:
                if exclude_keyword in test_name:
                    log_debug(f"[BOUNDARY_DETECT] 测试名称包含排除关键词 '{exclude_keyword}': {test_name}", "test_content_generator")
                    return False
            
            # 4. 处理不同类型的需求描述，排除性能部分
            search_text = ""
            if isinstance(requirement_description, dict):
                # 如果是字典，排除performance字段后合并其他字段内容
                for key, value in requirement_description.items():
                    if value and key != 'performance':  # 🔧 排除性能字段
                        search_text += f"{str(value)} "
            elif isinstance(requirement_description, str):
                # 如果是字符串，排除 g) 性能: 部分
                import re
                performance_pattern = r'g\)\s*性能[：:]\s*(.+?)(?=[a-h]\)|$|(?:\n[a-h]\)))'
                search_text = re.sub(performance_pattern, '', requirement_description, flags=re.DOTALL | re.IGNORECASE)
            else:
                return False
            
            # 5. 检查需求描述中是否包含边界相关内容（已排除性能部分）
            # 需要两组关键词都存在才认为是边界测试项（参考hanshutiqu_kaifa算法）
            group1_found = False
            group2_found = False
            
            found_keywords_group1 = []
            found_keywords_group2 = []
            
            for keyword in boundary_keywords_group1:
                if keyword in search_text:
                    group1_found = True
                    found_keywords_group1.append(keyword)
            
            for keyword in boundary_keywords_group2:
                if keyword in search_text:
                    group2_found = True
                    found_keywords_group2.append(keyword)
            
            # 6. 判断是否满足边界测试条件
            if group1_found and group2_found:
                log_debug(f"[BOUNDARY_DETECT] 发现边界关键词组1: {found_keywords_group1}", "test_content_generator")
                log_debug(f"[BOUNDARY_DETECT] 发现边界关键词组2: {found_keywords_group2}", "test_content_generator")
                return True
            elif group1_found:
                log_debug(f"[BOUNDARY_DETECT] 仅发现边界关键词组1: {found_keywords_group1}，缺少组2", "test_content_generator")
            elif group2_found:
                log_debug(f"[BOUNDARY_DETECT] 仅发现边界关键词组2: {found_keywords_group2}，缺少组1", "test_content_generator")
            
            log_debug(f"[BOUNDARY_DETECT] 未发现边界测试相关内容: {test_name}", "test_content_generator")
            return False
            
        except Exception as e:
            log_warning(f"[BOUNDARY_DETECT] 边界测试检测失败: {e}", "test_content_generator")
            return False
    
    def _generate_performance_test_content(
        self, 
        test_name: str, 
        full_requirement_content: str, 
        ai_config: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        """
        生成性能测试的完整内容（需求子项描述、测试项描述、测试方法）
        
        Args:
            test_name: 测试项名称
            full_requirement_content: 完整的需求内容
            ai_config: AI配置信息
            
        Returns:
            Tuple[str, str, str]: (需求子项描述, 测试项描述, 测试方法)
        """
        try:
            log_info(f"[PERFORMANCE_AI] 开始生成性能测试完整内容: {test_name}", "test_content_generator")
            
            # 🔧 使用提示词管理器
            try:
                from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.ai_services.ai_prompt_manager import prompt_manager
                has_detector = ai_config.get('jianceyi_flag', '无检测仪') == '有检测仪'
                
                # 🔧 确保需求描述是标准的中文格式
                formatted_requirement = self._format_requirement_for_ai(full_requirement_content, test_name)
                
                log_info(f"[PERFORMANCE_AI] 完整需求描述内容:\n{formatted_requirement}", "test_content_generator")
                
                # 🔧 使用提示词管理器获取结构化提示词
                structured_prompt = prompt_manager.get_structured_prompt_for_complete_generation(
                    test_type='性能测试',
                    test_name=test_name,
                    requirement_content=formatted_requirement,
                    has_detector=has_detector
                )
                
                log_info(f"[PERFORMANCE_AI] 使用提示词管理器生成结构化提示词", "test_content_generator")
                
            except ImportError:
                # 回退到内联提示词
                log_warning("[PERFORMANCE_AI] 无法导入提示词管理器，使用内联提示词", "test_content_generator")
                
                # 获取检测仪标志
                jianceyi_flag = ai_config.get('jianceyi_flag', '无检测仪')
                
                # 🔧 确保需求描述是标准的中文格式
                formatted_requirement = self._format_requirement_for_ai(full_requirement_content, test_name)
                
                log_info(f"[PERFORMANCE_AI] 完整需求描述内容:\n{formatted_requirement}", "test_content_generator")
                
                # 🔧 构建结构化提示词，让AI生成完整的三个字段
                detector_method_desc = "，注意测试激励的输入和被测软件状态的监控都是通过检测仪实现的" if jianceyi_flag == '有检测仪' else ""
                
                structured_prompt = f"""===性能需求描述===
请从以下需求中提取性能相关内容：

{formatted_requirement}

===测试项描述===
请生成具体的性能测试项描述

===测试方法===
请生成详细的性能测试方法{detector_method_desc}

请严格按照以下JSON格式输出：
{{
    "requirement_description": "从原文中提取的性能相关需求内容",
    "test_description": "具体的测试内容描述",
    "test_method": "详细的测试方法描述"
}}"""
            
            log_info(f"[PERFORMANCE_AI] 构建的结构化提示词:\n{structured_prompt}", "test_content_generator")
            log_info("=" * 120, "test_content_generator")
            
            # 🔧 直接调用generate_test_cases，使用自定义提示词模式
            log_info(f"[PERFORMANCE_AI] 直接调用generate_test_cases（使用自定义提示词模式）", "test_content_generator")
            jianceyi_flag = ai_config.get('jianceyi_flag', '无检测仪')
            
            # 导入generate_test_cases函数
            try:
                from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.ai_services.ai_client import generate_test_cases
            except ImportError:
                try:
                    from ..ai_services.ai_client import generate_test_cases
                except ImportError:
                    # 最后的备用方案
                    def generate_test_cases(ceshi_neirong, ceshi_leixing, jianceyi_flag, use_custom_prompt=False):
                        return []
            
            # 🔧 使用自定义提示词模式调用generate_test_cases
            test_cases = generate_test_cases(
                ceshi_neirong=structured_prompt,  # 您精心构建的JSON格式提示词
                ceshi_leixing="性能测试",
                jianceyi_flag=jianceyi_flag,
                use_custom_prompt=True  # 🎯 关键：使用自定义提示词模式
            )
            
            log_info(f"[PERFORMANCE_AI] generate_test_cases返回结果类型: {type(test_cases)}", "test_content_generator")
            log_info(f"[PERFORMANCE_AI] generate_test_cases返回内容: {test_cases}", "test_content_generator")
            
            # 🔧 解析generate_test_cases的返回结果
            if not test_cases or not isinstance(test_cases, list):
                log_warning("[PERFORMANCE_AI] generate_test_cases返回结果为空或格式错误", "test_content_generator")
                return "性能需求描述", f"验证{test_name}的性能是否符合需求规定。", f"按照测试规范对{test_name}进行性能验证。"
            
            # 🔧 现在AI应该返回包含三个字段的JSON格式
            # 检查第一个测试项是否包含我们需要的字段
            first_test_case = test_cases[0]
            
            # 🔧 尝试从AI返回的JSON中提取三个字段
            if 'requirement_description' in first_test_case:
                # AI返回了我们要求的JSON格式！
                requirement_sub_description = first_test_case.get('requirement_description', '').strip()
                test_description = first_test_case.get('test_description', '').strip()
                test_method = first_test_case.get('test_method', '').strip()
                
                log_info("=" * 120, "test_content_generator")
                log_info(f"[PERFORMANCE_AI] AI返回了正确的JSON格式！", "test_content_generator")
                log_info(f"[PERFORMANCE_AI] requirement_description: {repr(requirement_sub_description)}", "test_content_generator")
                log_info(f"[PERFORMANCE_AI] test_description: {repr(test_description)}", "test_content_generator")
                log_info(f"[PERFORMANCE_AI] test_method: {repr(test_method)}", "test_content_generator")
                log_info("=" * 120, "test_content_generator")
                
            else:
                # AI返回了旧的context/method格式，需要转换
                log_warning("[PERFORMANCE_AI] AI返回了旧格式，进行转换", "test_content_generator")
                
                ai_test_description = first_test_case.get('context', '').strip()
                ai_test_method = first_test_case.get('method', '').strip()
                
                log_info("=" * 120, "test_content_generator")
                log_info(f"[PERFORMANCE_AI] AI完整原始响应:", "test_content_generator")
                log_info(f"[PERFORMANCE_AI] 原始测试描述: {repr(ai_test_description)}", "test_content_generator")
                log_info(f"[PERFORMANCE_AI] 原始测试方法: {repr(ai_test_method)}", "test_content_generator")
                log_info(f"[PERFORMANCE_AI] 测试描述长度: {len(ai_test_description)}", "test_content_generator")
                log_info(f"[PERFORMANCE_AI] 测试方法长度: {len(ai_test_method)}", "test_content_generator")
                log_info("=" * 120, "test_content_generator")
                
                # 🔧 解析性能测试AI响应，提取三个字段
                requirement_sub_description, test_description, test_method = self._parse_performance_ai_response(ai_test_description, ai_test_method)
            
            log_info(f"[PERFORMANCE_AI] 解析后的完整结果:", "test_content_generator")
            log_info(f"[PERFORMANCE_AI] 需求子项描述: {requirement_sub_description}", "test_content_generator")
            log_info(f"[PERFORMANCE_AI] 测试项描述: {test_description}", "test_content_generator")
            log_info(f"[PERFORMANCE_AI] 测试方法: {test_method}", "test_content_generator")
            
            return requirement_sub_description, test_description, test_method
            
        except Exception as e:
            log_error(f"[PERFORMANCE_AI] 生成性能测试内容时发生异常: {e}", "test_content_generator")
            import traceback
            log_error(f"[PERFORMANCE_AI] 异常详情:\n{traceback.format_exc()}", "test_content_generator")
            
            # 返回默认内容
            return (
                f"性能需求描述（{test_name}）",
                f"验证{test_name}的性能指标是否符合需求规定。",
                f"按照性能测试规范对{test_name}进行性能验证。"
            )
    
    def _format_requirement_for_ai(self, requirement_description, test_name: str) -> str:
        """
        将需求描述格式化为标准的中文格式，供AI使用
        
        Args:
            requirement_description: 原始需求描述（可能是字典或字符串）
            test_name: 测试项名称
            
        Returns:
            str: 格式化后的中文需求描述
        """
        try:
            if isinstance(requirement_description, dict):
                # 如果是字典格式，转换为标准的中文格式
                formatted_parts = []
                
                # 添加章节编号和测试项名称
                chapter_number = requirement_description.get('chapter_number', '')
                if chapter_number:
                    formatted_parts.append(f"{chapter_number}\t {test_name}")
                else:
                    formatted_parts.append(f"{test_name}")
                
                # 按照标准格式添加各个字段
                field_mapping = [
                    ('identifier', 'a) 标识号：'),
                    ('description', 'b) 说明：'),
                    ('entry_condition', 'c) 进入条件：'),
                    ('input', 'd) 输入：'),
                    ('output', 'e) 输出：'),
                    ('processing', 'f) 处理：'),
                    ('performance', 'g) 性能：'),
                    ('constraints', 'h) 约束与限制：')
                ]
                
                for field_key, field_label in field_mapping:
                    field_value = requirement_description.get(field_key)
                    if field_value and str(field_value).strip():
                        clean_value = str(field_value).strip()
                        if clean_value and clean_value != '无' and clean_value != '':
                            formatted_parts.append(f"{field_label}\n{clean_value}")
                
                return '\n'.join(formatted_parts)
            
            elif isinstance(requirement_description, str):
                # 如果已经是字符串格式，直接返回
                return requirement_description
            
            else:
                # 其他类型，转换为字符串
                return str(requirement_description)
                
        except Exception as e:
            log_warning(f"格式化需求描述失败: {e}", "test_content_generator")
            # 出错时返回原始内容的字符串表示
            return str(requirement_description)
    
    def _parse_performance_ai_response(self, ai_description: str, ai_method: str) -> Tuple[str, str, str]:
        """
        解析性能测试AI响应（JSON格式）
        
        Args:
            ai_description: AI返回的描述内容
            ai_method: AI返回的方法内容
            
        Returns:
            Tuple[str, str, str]: (性能需求描述, 测试项描述, 测试方法)
        """
        try:
            log_info(f"[PERFORMANCE_PARSE] 开始解析性能测试AI响应", "test_content_generator")
            log_info(f"[PERFORMANCE_PARSE] AI描述内容: '{ai_description}'", "test_content_generator")
            log_info(f"[PERFORMANCE_PARSE] AI方法内容: '{ai_method}'", "test_content_generator")
            
            # 🔧 修改：使用JSON解析而不是结构化文本解析
            # 尝试解析AI返回的JSON内容
            import json
            import re
            
            # 首先尝试从ai_description中解析JSON
            json_content = ""
            if ai_description and ai_description.strip():
                json_content = ai_description.strip()
            elif ai_method and ai_method.strip():
                json_content = ai_method.strip()
            else:
                log_error("[PERFORMANCE_PARSE] AI响应内容为空", "test_content_generator")
                return "性能需求描述", "验证性能指标是否符合需求", "执行性能测试验证"
            
            # 🔧 新增：处理<think>标签，移除思考过程
            if "<think>" in json_content and "</think>" in json_content:
                json_content = re.sub(r'<think>.*?</think>', '', json_content, flags=re.DOTALL).strip()
                log_debug(f"[PERFORMANCE_PARSE] 移除<think>标签后的内容长度: {len(json_content)}", "test_content_generator")
            
            # 清理JSON内容，移除可能的前后缀文字
            json_content = json_content.strip()
            if json_content.startswith('```json'):
                json_content = json_content[7:]
            if json_content.endswith('```'):
                json_content = json_content[:-3]
            json_content = json_content.strip()
            
            # 查找JSON对象的开始和结束
            start_idx = json_content.find('{')
            end_idx = json_content.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_content = json_content[start_idx:end_idx+1]
            
            log_info(f"[PERFORMANCE_PARSE] 提取的JSON内容: '{json_content}'", "test_content_generator")
            
            # 解析JSON
            try:
                parsed_json = json.loads(json_content)
                log_info(f"[PERFORMANCE_PARSE] JSON解析成功: {parsed_json}", "test_content_generator")
                
                # 提取各个字段
                performance_requirement = parsed_json.get('requirement_description', '').strip()
                
                # 🔧 新增：支持元组对格式的test_pairs
                test_pairs = parsed_json.get('test_pairs', [])
                test_descriptions = []
                test_methods = []
                
                if test_pairs and isinstance(test_pairs, list):
                    # 新的元组对格式
                    log_info(f"[PERFORMANCE_PARSE] 检测到元组对格式", "test_content_generator")
                    for pair in test_pairs:
                        if isinstance(pair, dict) and 'description' in pair and 'method' in pair:
                            test_descriptions.append(pair.get('description', '').strip())
                            test_methods.append(pair.get('method', '').strip())
                else:
                    # 兼容旧的数组格式
                    test_descriptions = parsed_json.get('test_descriptions', [])
                    test_methods = parsed_json.get('test_methods', [])
                    
                    # 兼容更旧的单个字段格式
                    if not test_descriptions and 'test_description' in parsed_json:
                        test_descriptions = [parsed_json.get('test_description', '').strip()]
                    if not test_methods and 'test_method' in parsed_json:
                        test_methods = [parsed_json.get('test_method', '').strip()]
                    
                    # 确保数组格式
                    if not isinstance(test_descriptions, list):
                        test_descriptions = [str(test_descriptions)]
                    if not isinstance(test_methods, list):
                        test_methods = [str(test_methods)]
                    
                    # 验证数组长度一致性
                    if len(test_descriptions) != len(test_methods):
                        log_warning(f"[PERFORMANCE_PARSE] 测试描述和测试方法数量不匹配: {len(test_descriptions)} vs {len(test_methods)}", "test_content_generator")
                        # 取较小的长度，确保一一对应
                        min_length = min(len(test_descriptions), len(test_methods))
                        test_descriptions = test_descriptions[:min_length]
                        test_methods = test_methods[:min_length]
                
                # 验证提取结果
                if not performance_requirement:
                    performance_requirement = "性能需求描述"
                if not test_descriptions:
                    test_descriptions = ["验证性能指标是否符合需求"]
                if not test_methods:
                    test_methods = ["执行性能测试验证"]
                
                # 🔧 新增：合并多条测试内容和测试方法
                combined_test_description = " | ".join(test_descriptions)
                combined_test_method = " | ".join(test_methods)
                
                log_info(f"[PERFORMANCE_PARSE] 解析结果:", "test_content_generator")
                log_info(f"[PERFORMANCE_PARSE] - 性能需求描述: '{performance_requirement}'", "test_content_generator")
                log_info(f"[PERFORMANCE_PARSE] - 测试描述数量: {len(test_descriptions)}", "test_content_generator")
                log_info(f"[PERFORMANCE_PARSE] - 测试方法数量: {len(test_methods)}", "test_content_generator")
                log_info(f"[PERFORMANCE_PARSE] - 合并后测试描述: '{combined_test_description}'", "test_content_generator")
                log_info(f"[PERFORMANCE_PARSE] - 合并后测试方法: '{combined_test_method}'", "test_content_generator")
                
                return performance_requirement, combined_test_description, combined_test_method
                
            except json.JSONDecodeError as e:
                log_error(f"[PERFORMANCE_PARSE] JSON解析失败: {e}", "test_content_generator")
                log_error(f"[PERFORMANCE_PARSE] 尝试解析的内容: '{json_content}'", "test_content_generator")
                
                # 🔧 回退：如果JSON解析失败，尝试从原始内容中提取
                return self._fallback_parse_performance_response(ai_description, ai_method)
                
        except Exception as e:
            log_error(f"[PERFORMANCE_PARSE] 解析过程发生异常: {e}", "test_content_generator")
            import traceback
            log_error(f"[PERFORMANCE_PARSE] 异常详情:\n{traceback.format_exc()}", "test_content_generator")
            
            # 返回默认内容
            return "性能需求描述", "验证性能指标是否符合需求", "执行性能测试验证"
    
    def _fallback_parse_performance_response(self, ai_description: str, ai_method: str) -> Tuple[str, str, str]:
        """
        性能测试AI响应的回退解析方法
        
        Args:
            ai_description: AI返回的描述内容
            ai_method: AI返回的方法内容
            
        Returns:
            Tuple[str, str, str]: (性能需求描述, 测试项描述, 测试方法)
        """
        try:
            log_info("[PERFORMANCE_PARSE] 使用回退解析方法", "test_content_generator")
            
            # 合并所有内容进行解析
            full_content = f"{ai_description} {ai_method}".strip()
            
            # 尝试提取关键信息
            performance_requirement = "性能需求描述"
            test_description = ai_description if ai_description else "验证性能指标是否符合需求"
            test_method = ai_method if ai_method else "执行性能测试验证"
            
            return performance_requirement, test_description, test_method
            
        except Exception as e:
            log_error(f"[PERFORMANCE_PARSE] 回退解析也失败: {e}", "test_content_generator")
            return "性能需求描述", "验证性能指标是否符合需求", "执行性能测试验证"
    
    def _extract_performance_requirements(self, requirement_description: str) -> str:
        """
        从需求描述中提取性能要求
        
        Args:
            requirement_description: 需求描述
            
        Returns:
            str: 性能要求内容
        """
        try:
            if not requirement_description:
                return ""
            
            # 查找 g) 性能: 相关内容
            import re
            performance_pattern = r'g\)\s*性能[：:]\s*(.+?)(?=[a-h]\)|$|(?:\n[a-h]\)))'
            performance_match = re.search(performance_pattern, requirement_description, re.DOTALL | re.IGNORECASE)
            
            if performance_match:
                return performance_match.group(1).strip()
            
            # 如果没有找到标准格式，返回整个描述
            return requirement_description.strip()
            
        except Exception as e:
            log_warning(f"提取性能要求失败: {e}", "test_content_generator")
            return requirement_description
    
    def _generate_ai_performance_content(
        self, 
        test_name: str, 
        performance_content: str, 
        ai_config: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        使用AI生成性能测试内容
        
        Args:
            test_name: 测试项名称
            performance_content: 性能要求内容
            ai_config: AI配置
            
        Returns:
            Tuple[str, str]: (AI生成的测试描述, AI生成的测试方法)
        """
        try:
            # 构造性能测试专用的提示词
            performance_prompt = f"""
测试项名称：{test_name}
性能要求：{performance_content}

请基于以上性能要求，生成：
1) 测试项描述（中文编号格式 1、2、3、...，覆盖关键性能指标、场景、边界与监控要点）；
2) 测试方法（中文编号格式 1、2、3、...，可执行、包含环境、工具、步骤、度量与判据）。
输出只需要"测试项描述"和"测试方法"两段文本，不要附加其他说明。
"""

            # 记录完整原始提示词到现有日志系统（不得省略）
            try:
                log_info("[AI_PERF_PROMPT] 即将发送给AI的原始性能测试提示词如下：", "test_content_generator")
                log_info("=" * 80, "test_content_generator")
                log_info(performance_prompt, "test_content_generator")
                log_info("=" * 80, "test_content_generator")
            except Exception:
                # 保底不影响主流程
                pass
            
            # 调用原有的AI生成方法，但使用性能测试专用的上下文
            result = self._generate_ai_test_content(test_name, performance_prompt, ai_config, True, True) # 强制启用AI生成
            log_info(
                f"[AI_DEBUG] 性能测试AI生成完成 - 描述长度: {len(result[0])}, 方法长度: {len(result[1])}",
                "test_content_generator",
            )
            return result
        except Exception as e:
            log_error(f"AI生成性能测试内容失败: {e}", "test_content_generator")
            log_error(f"[AI_DEBUG] 性能测试AI生成失败，异常: {e}", "test_content_generator")
            return "error", "error"
    
    def _generate_default_performance_description(self, test_name: str, performance_content: str) -> str:
        """
        生成默认的性能测试描述
        
        Args:
            test_name: 测试项名称
            performance_content: 性能内容
            
        Returns:
            str: 默认的性能测试描述
        """
        try:
            # 从测试名称中提取核心功能名称（去掉"（性能测试）"后缀）
            core_function = test_name.replace('（性能测试）', '').replace('(性能测试)', '')
            
            description = f"""验证{core_function}的性能指标是否满足系统要求。

性能测试目标：
{performance_content}

测试范围：
- 验证功能在正常负载下的性能表现
- 验证功能在峰值负载下的性能表现
- 验证性能指标是否符合规定要求"""
            
            return description
            
        except Exception as e:
            log_warning(f"生成默认性能测试描述失败: {e}", "test_content_generator")
            return f"验证{test_name}的性能指标。"
    
    def _generate_default_performance_method(self, test_name: str, performance_content: str) -> str:
        """
        生成默认的性能测试方法
        
        Args:
            test_name: 测试项名称
            performance_content: 性能内容
            
        Returns:
            str: 默认的性能测试方法
        """
        try:
            # 从测试名称中提取核心功能名称
            core_function = test_name.replace('（性能测试）', '').replace('(性能测试)', '')
            
            method = f"""1. 测试环境准备
   - 配置测试环境，确保硬件资源充足
   - 部署被测软件，确保功能正常
   - 准备性能测试工具和监控工具

2. 性能基线测试
   - 在正常负载下执行{core_function}
   - 记录响应时间、吞吐量等性能指标
   - 建立性能基线

3. 负载测试
   - 逐步增加负载，验证性能变化趋势
   - 验证系统在目标负载下的性能表现
   - 监控系统资源使用情况

4. 性能指标验证
   根据以下要求验证性能指标：
   {performance_content}

5. 测试结果分析
   - 分析性能测试数据
   - 对比性能要求，判断是否达标
   - 记录性能测试结论"""
            
            return method
            
        except Exception as e:
            log_warning(f"生成默认性能测试方法失败: {e}", "test_content_generator")
            return f"按照性能测试规范对{test_name}进行性能验证。"
    
    def _generate_boundary_test_content(
        self, 
        test_name: str, 
        full_requirement_content: str, 
        ai_config: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        """
        生成边界测试的完整内容（需求子项描述、测试项描述、测试方法）
        
        Args:
            test_name: 测试项名称
            full_requirement_content: 完整的需求内容
            ai_config: AI配置信息
            
        Returns:
            Tuple[str, str, str]: (需求子项描述, 测试项描述, 测试方法)
        """
        try:
            log_info(f"[BOUNDARY_AI] 开始生成边界测试完整内容: {test_name}", "test_content_generator")
            
            # 🔧 使用提示词管理器
            try:
                from app.danamicTest.ConfigurationItem.service.requirement_analysis.test_generation.ai_services.ai_prompt_manager import prompt_manager
                has_detector = ai_config.get('jianceyi_flag', '无检测仪') == '有检测仪'
                
                # 🔧 确保需求描述是标准的中文格式
                formatted_requirement = self._format_requirement_for_ai(full_requirement_content, test_name)
                
                log_info(f"[BOUNDARY_AI] 完整需求描述内容:\n{formatted_requirement}", "test_content_generator")
                
                # 🔧 使用提示词管理器获取结构化提示词
                structured_prompt = prompt_manager.get_structured_prompt_for_complete_generation(
                    test_type='边界测试',
                    test_name=test_name,
                    requirement_content=formatted_requirement,
                    has_detector=has_detector
                )
                
                log_info(f"[BOUNDARY_AI] 使用提示词管理器生成结构化提示词", "test_content_generator")
                
            except ImportError:
                # 回退到内联提示词
                log_warning("[BOUNDARY_AI] 无法导入提示词管理器，使用内联提示词", "test_content_generator")
                
                # 获取检测仪标志
                jianceyi_flag = ai_config.get('jianceyi_flag', '无检测仪')
                
                # 🔧 确保需求描述是标准的中文格式
                formatted_requirement = self._format_requirement_for_ai(full_requirement_content, test_name)
                
                log_info(f"[BOUNDARY_AI] 完整需求描述内容:\n{formatted_requirement}", "test_content_generator")
                
                # 🔧 构建结构化提示词，让AI生成完整的三个字段
                detector_method_desc = "，注意测试激励的输入和被测软件状态的监控都是通过检测仪实现的" if jianceyi_flag == '有检测仪' else ""
                
                structured_prompt = f"""===边界需求描述===
请从以下需求中提取边界相关内容（排除性能相关内容）：

{formatted_requirement}

===测试项描述===
请生成具体的边界测试项描述

===测试方法===
请生成详细的边界测试方法{detector_method_desc}

请严格按照以下JSON格式输出：
{{
    "requirement_description": "从原文中提取的边界相关需求内容",
    "test_description": "具体的测试内容描述",
    "test_method": "详细的测试方法描述"
}}"""
            
            log_info(f"[BOUNDARY_AI] 构建的结构化提示词:\n{structured_prompt}", "test_content_generator")
            log_info("=" * 120, "test_content_generator")
            log_info(f"[BOUNDARY_AI] 直接调用generate_test_cases（使用自定义提示词模式）", "test_content_generator")
            
            # 🔧 直接调用generate_test_cases，使用自定义提示词模式
            jianceyi_flag = ai_config.get('jianceyi_flag', '无检测仪')
            test_cases = generate_test_cases(
                ceshi_neirong=structured_prompt,
                ceshi_leixing="边界测试",
                jianceyi_flag=jianceyi_flag,
                use_custom_prompt=True  # 🔧 关键：使用自定义提示词模式
            )
            
            log_info(f"[BOUNDARY_AI] generate_test_cases返回结果类型: {type(test_cases)}", "test_content_generator")
            log_info(f"[BOUNDARY_AI] generate_test_cases返回内容: {test_cases}", "test_content_generator")
            
            # 🔧 检查返回结果
            if not test_cases or len(test_cases) == 0:
                log_warning(f"[BOUNDARY_AI] generate_test_cases返回结果为空或格式错误", "test_content_generator")
                # 返回默认内容
                return (
                    f"边界需求描述（{test_name}）",
                    f"验证{test_name}的边界条件是否符合需求规定。",
                    f"按照边界测试规范对{test_name}进行边界验证。"
                )
            
            # 🔧 提取第一个测试用例的JSON数据
            first_case = test_cases[0]
            log_info("=" * 120, "test_content_generator")
            
            # 🔧 检查是否是正确的JSON格式（包含英文键）
            if isinstance(first_case, dict) and 'requirement_description' in first_case:
                log_info(f"[BOUNDARY_AI] AI返回了正确的JSON格式！", "test_content_generator")
                requirement_sub_description = first_case.get('requirement_description', '')
                test_description = first_case.get('test_description', '')
                test_method = first_case.get('test_method', '')
                
                log_info(f"[BOUNDARY_AI] requirement_description: '{requirement_sub_description}'", "test_content_generator")
                log_info(f"[BOUNDARY_AI] test_description: '{test_description}'", "test_content_generator")
                log_info(f"[BOUNDARY_AI] test_method: '{test_method}'", "test_content_generator")
                
            else:
                # 🔧 回退到旧格式解析
                log_warning(f"[BOUNDARY_AI] AI返回了旧格式，尝试解析context和method字段", "test_content_generator")
                requirement_sub_description, test_description, test_method = self._parse_boundary_ai_response(
                    first_case.get('context', ''), first_case.get('method', '')
                )
            
            log_info("=" * 120, "test_content_generator")
            log_info(f"[BOUNDARY_AI] 解析后的完整结果:", "test_content_generator")
            log_info(f"[BOUNDARY_AI] 需求子项描述: {requirement_sub_description}", "test_content_generator")
            log_info(f"[BOUNDARY_AI] 测试项描述: {test_description}", "test_content_generator")
            log_info(f"[BOUNDARY_AI] 测试方法: {test_method}", "test_content_generator")
            
            return requirement_sub_description, test_description, test_method
            
        except Exception as e:
            log_error(f"[BOUNDARY_AI] 生成边界测试内容时发生异常: {e}", "test_content_generator")
            import traceback
            log_error(f"[BOUNDARY_AI] 异常详情:\n{traceback.format_exc()}", "test_content_generator")
            
            # 返回默认内容
            return (
                f"边界需求描述（{test_name}）",
                f"验证{test_name}的边界条件是否符合需求规定。",
                f"按照边界测试规范对{test_name}进行边界验证。"
            )
    
    def _parse_boundary_ai_response(self, ai_description: str, ai_method: str) -> Tuple[str, str, str]:
        """
        解析边界测试AI响应（JSON格式）
        
        Args:
            ai_description: AI返回的描述内容
            ai_method: AI返回的方法内容
            
        Returns:
            Tuple[str, str, str]: (边界需求描述, 测试项描述, 测试方法)
        """
        try:
            log_info(f"[BOUNDARY_PARSE] 开始解析边界测试AI响应", "test_content_generator")
            log_info(f"[BOUNDARY_PARSE] AI描述内容: '{ai_description}'", "test_content_generator")
            log_info(f"[BOUNDARY_PARSE] AI方法内容: '{ai_method}'", "test_content_generator")
            
            # 🔧 修改：使用JSON解析而不是结构化文本解析
            # 尝试解析AI返回的JSON内容
            import json
            import re
            
            # 首先尝试从ai_description中解析JSON
            json_content = ""
            if ai_description and ai_description.strip():
                json_content = ai_description.strip()
            elif ai_method and ai_method.strip():
                json_content = ai_method.strip()
            else:
                log_error("[BOUNDARY_PARSE] AI响应内容为空", "test_content_generator")
                return "边界需求描述", "验证边界条件是否符合需求", "执行边界测试验证"
            
            # 🔧 新增：处理<think>标签，移除思考过程
            if "<think>" in json_content and "</think>" in json_content:
                json_content = re.sub(r'<think>.*?</think>', '', json_content, flags=re.DOTALL).strip()
                log_debug(f"[BOUNDARY_PARSE] 移除<think>标签后的内容长度: {len(json_content)}", "test_content_generator")
            
            # 清理JSON内容，移除可能的前后缀文字
            json_content = json_content.strip()
            if json_content.startswith('```json'):
                json_content = json_content[7:]
            if json_content.endswith('```'):
                json_content = json_content[:-3]
            json_content = json_content.strip()
            
            # 查找JSON对象的开始和结束
            start_idx = json_content.find('{')
            end_idx = json_content.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_content = json_content[start_idx:end_idx+1]
            
            log_info(f"[BOUNDARY_PARSE] 提取的JSON内容: '{json_content}'", "test_content_generator")
            
            # 解析JSON
            try:
                parsed_json = json.loads(json_content)
                log_info(f"[BOUNDARY_PARSE] JSON解析成功: {parsed_json}", "test_content_generator")
                
                # 提取各个字段
                boundary_requirement = parsed_json.get('requirement_description', '').strip()
                
                # 🔧 新增：支持元组对格式的test_pairs
                test_pairs = parsed_json.get('test_pairs', [])
                test_descriptions = []
                test_methods = []
                
                if test_pairs and isinstance(test_pairs, list):
                    # 新的元组对格式
                    log_info(f"[BOUNDARY_PARSE] 检测到元组对格式", "test_content_generator")
                    for pair in test_pairs:
                        if isinstance(pair, dict) and 'description' in pair and 'method' in pair:
                            test_descriptions.append(pair.get('description', '').strip())
                            test_methods.append(pair.get('method', '').strip())
                else:
                    # 兼容旧的数组格式
                    test_descriptions = parsed_json.get('test_descriptions', [])
                    test_methods = parsed_json.get('test_methods', [])
                    
                    # 兼容更旧的单个字段格式
                    if not test_descriptions and 'test_description' in parsed_json:
                        test_descriptions = [parsed_json.get('test_description', '').strip()]
                    if not test_methods and 'test_method' in parsed_json:
                        test_methods = [parsed_json.get('test_method', '').strip()]
                    
                    # 确保数组格式
                    if not isinstance(test_descriptions, list):
                        test_descriptions = [str(test_descriptions)]
                    if not isinstance(test_methods, list):
                        test_methods = [str(test_methods)]
                    
                    # 验证数组长度一致性
                    if len(test_descriptions) != len(test_methods):
                        log_warning(f"[BOUNDARY_PARSE] 测试描述和测试方法数量不匹配: {len(test_descriptions)} vs {len(test_methods)}", "test_content_generator")
                        # 取较小的长度，确保一一对应
                        min_length = min(len(test_descriptions), len(test_methods))
                        test_descriptions = test_descriptions[:min_length]
                        test_methods = test_methods[:min_length]
                
                # 验证提取结果
                if not boundary_requirement:
                    boundary_requirement = "边界需求描述"
                if not test_descriptions:
                    test_descriptions = ["验证边界条件是否符合需求"]
                if not test_methods:
                    test_methods = ["执行边界测试验证"]
                
                # 🔧 新增：合并多条测试内容和测试方法
                combined_test_description = " | ".join(test_descriptions)
                combined_test_method = " | ".join(test_methods)
                
                log_info(f"[BOUNDARY_PARSE] 解析结果:", "test_content_generator")
                log_info(f"[BOUNDARY_PARSE] - 边界需求描述: '{boundary_requirement}'", "test_content_generator")
                log_info(f"[BOUNDARY_PARSE] - 测试描述数量: {len(test_descriptions)}", "test_content_generator")
                log_info(f"[BOUNDARY_PARSE] - 测试方法数量: {len(test_methods)}", "test_content_generator")
                log_info(f"[BOUNDARY_PARSE] - 合并后测试描述: '{combined_test_description}'", "test_content_generator")
                log_info(f"[BOUNDARY_PARSE] - 合并后测试方法: '{combined_test_method}'", "test_content_generator")
                
                return boundary_requirement, combined_test_description, combined_test_method
                
            except json.JSONDecodeError as e:
                log_error(f"[BOUNDARY_PARSE] JSON解析失败: {e}", "test_content_generator")
                log_error(f"[BOUNDARY_PARSE] 尝试解析的内容: '{json_content}'", "test_content_generator")
                
                # 🔧 回退：如果JSON解析失败，尝试从原始内容中提取
                return self._fallback_parse_boundary_response(ai_description, ai_method)
                
        except Exception as e:
            log_error(f"[BOUNDARY_PARSE] 解析过程发生异常: {e}", "test_content_generator")
            import traceback
            log_error(f"[BOUNDARY_PARSE] 异常详情:\n{traceback.format_exc()}", "test_content_generator")
            
            # 返回默认内容
            return "边界需求描述", "验证边界条件是否符合需求", "执行边界测试验证"
    
    def _fallback_parse_boundary_response(self, ai_description: str, ai_method: str) -> Tuple[str, str, str]:
        """
        边界测试AI响应的回退解析方法
        
        Args:
            ai_description: AI返回的描述内容
            ai_method: AI返回的方法内容
            
        Returns:
            Tuple[str, str, str]: (边界需求描述, 测试项描述, 测试方法)
        """
        try:
            log_info("[BOUNDARY_PARSE] 使用回退解析方法", "test_content_generator")
            
            # 合并所有内容进行解析
            full_content = f"{ai_description} {ai_method}".strip()
            
            # 尝试提取关键信息
            boundary_requirement = "边界需求描述"
            test_description = ai_description if ai_description else "验证边界条件是否符合需求"
            test_method = ai_method if ai_method else "执行边界测试验证"
            
            return boundary_requirement, test_description, test_method
            
        except Exception as e:
            log_error(f"[BOUNDARY_PARSE] 回退解析也失败: {e}", "test_content_generator")
            return "边界需求描述", "验证边界条件是否符合需求", "执行边界测试验证"
    
    def _extract_boundary_requirements(self, requirement_description: str) -> str:
        """
        从需求描述中提取边界要求
        
        Args:
            requirement_description: 需求描述
            
        Returns:
            str: 边界要求内容
        """
        try:
            if not requirement_description:
                return ""
            
            # 按行分割需求描述，查找包含边界关键词的行
            lines = requirement_description.strip().split('\n')
            boundary_lines = []
            
            boundary_keywords = ['最大', '最小', '大于', '小于', '不超过', '超出', '超时', 
                               '范围', '精度', '极限', '温度', '阈值', '个数', '秒', '分钟', 'min']
            
            for line in lines:
                line_stripped = line.strip()
                if any(keyword in line_stripped for keyword in boundary_keywords):
                    boundary_lines.append(line_stripped)
            
            if boundary_lines:
                return '\n'.join(boundary_lines)
            
            # 如果没有找到特定的边界行，返回整个描述
            return requirement_description.strip()
            
        except Exception as e:
            log_warning(f"提取边界要求失败: {e}", "test_content_generator")
            return requirement_description
    
    def _generate_ai_boundary_content(
        self, 
        test_name: str, 
        boundary_content: str, 
        ai_config: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        使用AI生成边界测试内容
        
        Args:
            test_name: 测试项名称
            boundary_content: 边界要求内容
            ai_config: AI配置
            
        Returns:
            Tuple[str, str]: (AI生成的测试描述, AI生成的测试方法)
        """
        try:
            # 构造边界测试专用的提示词
            boundary_prompt = f"""
            测试项名称：{test_name}
            边界要求：{boundary_content}
            
            请为这个边界测试项生成测试描述和测试方法，要求：
            - 测试描述：简洁说明该边界测试的目的和测试范围
            - 测试方法：详细说明如何进行边界测试，包括边界值设置、测试步骤、异常处理验证等
            
            注意：
            1. 不要在内容前添加"测试项描述："或"测试方法："等前缀
            2. 不要使用英文字段名如boundary_values、verification、exception_handling等
            3. 直接输出中文内容，使用中文编号格式（1、2、3、）
            4. 重点关注数值边界、范围极限、异常处理等边界条件
            """
            
            log_info(f"[AI_DEBUG] 开始边界测试AI生成 - 测试名: {test_name}", "test_content_generator")
            log_info(f"[AI_DEBUG] 边界内容长度: {len(boundary_content)}", "test_content_generator")
            
            # 调用原有的AI生成方法，但使用边界测试专用的上下文
            result = self._generate_ai_test_content(test_name, boundary_prompt, ai_config, True, True) # 强制启用AI生成
            
            log_info(f"[AI_DEBUG] 边界测试AI生成完成 - 描述长度: {len(result[0])}, 方法长度: {len(result[1])}", "test_content_generator")
            return result
            
        except Exception as e:
            log_error(f"AI生成边界测试内容失败: {e}", "test_content_generator")
            log_error(f"[AI_DEBUG] 边界测试AI生成失败，异常: {e}", "test_content_generator")
            return "error", "error"
    
    def _generate_default_boundary_description(self, test_name: str, boundary_content: str) -> str:
        """
        生成默认的边界测试描述
        
        Args:
            test_name: 测试项名称
            boundary_content: 边界内容
            
        Returns:
            str: 默认的边界测试描述
        """
        try:
            # 从测试名称中提取核心功能名称（去掉"（边界测试）"后缀）
            core_function = test_name.replace('（边界测试）', '').replace('(边界测试)', '')
            
            description = f"""验证{core_function}在边界条件下的行为是否符合要求。

边界测试目标：
{boundary_content}

测试范围：
- 验证正常边界值的处理
- 验证异常边界值的处理
- 验证边界值附近的系统行为
- 验证越界条件的异常处理"""
            
            return description
            
        except Exception as e:
            log_warning(f"生成默认边界测试描述失败: {e}", "test_content_generator")
            return f"验证{test_name}的边界条件处理。"
    
    def _generate_default_boundary_method(self, test_name: str, boundary_content: str) -> str:
        """
        生成默认的边界测试方法
        
        Args:
            test_name: 测试项名称
            boundary_content: 边界内容
            
        Returns:
            str: 默认的边界测试方法
        """
        try:
            # 从测试名称中提取核心功能名称
            core_function = test_name.replace('（边界测试）', '').replace('(边界测试)', '')
            
            method = f"""1. 测试环境准备
   - 配置测试环境，确保功能正常
   - 准备边界测试数据和工具
   - 确认系统处于初始状态

2. 正常边界值测试
   - 使用最小允许值测试{core_function}
   - 使用最大允许值测试{core_function}
   - 验证边界值处理的正确性

3. 异常边界值测试
   - 使用小于最小值的数据进行测试
   - 使用大于最大值的数据进行测试
   - 验证越界处理机制

4. 边界条件验证
   根据以下边界要求进行验证：
   {boundary_content}

5. 异常处理验证
   - 验证越界时的错误提示
   - 验证系统的容错能力
   - 确认异常情况下系统稳定性

6. 测试结果分析
   - 分析边界测试数据
   - 对比边界要求，判断是否达标
   - 记录边界测试结论"""
            
            return method
            
        except Exception as e:
            log_warning(f"生成默认边界测试方法失败: {e}", "test_content_generator")
            return f"按照边界测试规范对{test_name}进行边界验证。"

    def _clean_ai_generated_content(self, content: str, content_type: str) -> str:
        """
        清理AI生成内容中的不必要前缀和英文字段
        
        Args:
            content: AI生成的原始内容
            content_type: 内容类型（"测试项描述" 或 "测试方法"）
            
        Returns:
            清理后的内容
        """
        try:
            if not content or content == 'error':
                return content
            
            cleaned_content = content
            
            # 🔧 修复：清理中文前缀
            prefixes_to_remove = [
                f"1. {content_type}：",
                f"2. {content_type}：", 
                f"1、{content_type}：",
                f"2、{content_type}：",
                f"{content_type}：",
                f"1. {content_type}:",
                f"2. {content_type}:",
                f"1、{content_type}:",
                f"2、{content_type}:",
                f"{content_type}:"
            ]
            
            for prefix in prefixes_to_remove:
                if cleaned_content.startswith(prefix):
                    cleaned_content = cleaned_content[len(prefix):].strip()
                    break
            
            # 🔧 修复：清理边界测试中可能出现的英文字段名（更精确的替换）
            import re
            
            # 匹配并替换英文字段，同时处理后续的空格和符号
            english_field_patterns = [
                (r'(\d+、)\s*boundary_values?\s*:\s*', r'\1'),
                (r'(\d+、)\s*boundary_value_setting\s*:\s*', r'\1'),
                (r'(\d+、)\s*verification\s*:\s*', r'\1'),
                (r'(\d+、)\s*expected_behavior_verification\s*:\s*', r'\1'),
                (r'(\d+、)\s*exception_handling\s*:\s*', r'\1'),
                (r'(\d+、)\s*exception_handling_check_steps?\s*:\s*', r'\1'),
                (r'boundary_values?\s*:\s*', ''),
                (r'boundary_value_setting\s*:\s*', ''),
                (r'verification\s*:\s*', ''),
                (r'expected_behavior_verification\s*:\s*', ''),
                (r'exception_handling\s*:\s*', ''),
                (r'exception_handling_check_steps?\s*:\s*', ''),
                (r'boundary_values?：\s*', ''),
                (r'boundary_value_setting：\s*', ''),
                (r'verification：\s*', ''),
                (r'expected_behavior_verification：\s*', ''),
                (r'exception_handling：\s*', ''),
                (r'exception_handling_check_steps?：\s*', '')
            ]
            
            for pattern, replacement in english_field_patterns:
                cleaned_content = re.sub(pattern, replacement, cleaned_content)
            
            # 清理多余的换行和空格，但保持原有的结构
            lines = []
            for line in cleaned_content.split('\n'):
                line = line.strip()
                if line:
                    lines.append(line)
            
            cleaned_content = '\n'.join(lines)
            
            # 如果清理后内容为空，返回原内容
            if not cleaned_content.strip():
                return content
            
            return cleaned_content
            
        except Exception as e:
            log_warning(f"清理AI生成内容时出错: {e}", "test_content_generator")
            return content
