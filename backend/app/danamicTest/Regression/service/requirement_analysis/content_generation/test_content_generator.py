"""
回归测试内容生成器

负责回归测试需求分析表的测试内容生成功能，包括：
- 数据库匹配（通用数据库和标准数据库）
- AI分析生成测试描述和测试方法
- 知识库优化现有测试内容
- 默认内容生成
- 内容质量验证
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionTestContentGenerator:
    """回归测试内容生成器"""
    
    def __init__(self):
        """初始化回归测试内容生成器"""
        self.logger = logger
        self.common_test_db = {}
        self.standard_test_db = {}
        self._load_test_databases()
    
    def _load_test_databases(self):
        """加载测试数据库"""
        try:
            # 尝试使用新的数据库适配器 - 使用多种方法尝试导入
            database_adapter = None
            
            # 尝试各种可能的导入方式
            import_attempts = [
                "app.danamicTest.ConfigurationItem.service.database_adapter",
                "backend.app.danamicTest.ConfigurationItem.service.database_adapter",
            ]
            
            for import_path in import_attempts:
                try:
                    import importlib
                    module = importlib.import_module(import_path)
                    get_database_adapter = getattr(module, 'get_database_adapter')
                    database_adapter = get_database_adapter()
                    self.logger.info(f"数据库适配器导入成功: {import_path}")
                    break
                except (ImportError, AttributeError) as e:
                    self.logger.debug(f"导入失败 {import_path}: {e}")
                    continue
            
            if database_adapter is not None:
                # 获取通用测试数据库
                self.common_test_db = database_adapter.get_test_data_dict()
                self.logger.info(f"通用测试数据库加载成功，共{len(self.common_test_db)}条记录")
                
                # 获取标准测试数据库（这里可以根据需要使用不同的类别）
                # 由于原来有通用和标准两个数据库，我们可以按类别分别获取
                standard_categories = ["CAM", "初始化"]  # 可以根据需要调整
                self.standard_test_db = {}
                
                for category in standard_categories:
                    category_data = database_adapter.get_test_data_dict_by_category(category)
                    self.standard_test_db.update(category_data)
                
                if not self.standard_test_db:
                    # 如果按类别获取失败，使用所有数据作为标准数据库
                    self.standard_test_db = self.common_test_db.copy()
                
                self.logger.info(f"标准测试数据库加载成功，共{len(self.standard_test_db)}条记录")
                
            else:
                self.logger.warning("所有数据库适配器导入方式都失败，使用Excel备用方法")
                # 回退到原来的Excel文件读取方式
                self._load_test_databases_from_excel()
                
        except Exception as e:
            self.logger.error(f"加载测试数据库时发生错误: {str(e)}")
            # 使用默认数据
            self.common_test_db = {'默认测试项': ('默认描述', '默认方法')}
            self.standard_test_db = {'默认测试项': ('默认描述', '默认方法')}
    
    def _load_test_databases_from_excel(self):
        """从Excel文件加载测试数据库（备用方法）"""
        try:
            # 尝试使用资源管理器获取数据库路径
            from ....resources.resource_manager import ResourceManager
            resource_manager = ResourceManager()
            common_db_path = resource_manager.test_item_common_desc_db
            standard_db_path = resource_manager.test_item_standard_desc_db
        except:
            # 如果失败则使用默认路径
            common_db_path = r'D:\baxiang_ceshi\DataBase\测试项通用描述数据库.xlsx'
            standard_db_path = r'D:\baxiang_ceshi\DataBase\测试项标准描述数据库.xlsx'
        
        # 加载通用测试数据库
        self.common_test_db = self._load_single_database(common_db_path, "通用测试数据库")
        
        # 加载标准测试数据库
        self.standard_test_db = self._load_single_database(standard_db_path, "标准测试数据库")
    
    def _load_single_database(self, db_path: str, db_name: str) -> Dict[str, Tuple[str, str]]:
        """
        加载单个测试数据库
        
        Args:
            db_path: 数据库路径
            db_name: 数据库名称
            
        Returns:
            Dict[str, Tuple[str, str]]: 测试数据库字典
        """
        try:
            from .test_identifier import read_excel_columns_three
            
            names, descriptions, methods = read_excel_columns_three(db_path)
            if names == '0':
                self.logger.warning(f"{db_name}读取失败")
                return {'NULLL': ('描述1', '方法1')}
            else:
                db_dict = {
                    key: (desc, method) 
                    for key, desc, method in zip(names, descriptions, methods) 
                    if isinstance(key, str)
                }
                self.logger.info(f"{db_name}加载成功，共{len(db_dict)}条记录")
                return db_dict
                
        except Exception as e:
            self.logger.error(f"加载{db_name}时发生错误: {str(e)}")
            return {'NULLL': ('描述1', '方法1')}
    
    def generate_test_content(
        self,
        test_items: List[Dict[str, Any]],
        ai_config: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """
        生成测试内容
        
        Args:
            test_items: 测试项列表
            ai_config: AI配置
            
        Returns:
            Tuple[List[str], List[str]]: (测试描述列表, 测试方法列表)
        """
        try:
            self.logger.info(f"开始生成{len(test_items)}个测试项的测试内容")
            
            test_descriptions = []
            test_methods = []
            
            for index, test_item in enumerate(test_items):
                description, method = self._generate_single_test_content(test_item, ai_config)
                test_descriptions.append(description)
                test_methods.append(method)
                
                self.logger.debug(f"测试项{index + 1}内容生成完成: {test_item.get('name', '')}")
            
            self.logger.info("测试内容生成完成")
            return test_descriptions, test_methods
            
        except Exception as e:
            self.logger.error(f"生成测试内容时发生错误: {str(e)}")
            return [], []
    
    def _generate_single_test_content(
        self,
        test_item: Dict[str, Any],
        ai_config: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        生成单个测试项的测试内容
        
        Args:
            test_item: 测试项信息
            ai_config: AI配置
            
        Returns:
            Tuple[str, str]: (测试描述, 测试方法)
        """
        test_name = test_item.get('name', '')
        requirement_description = test_item.get('requirement_description', '')
        test_type = test_item.get('test_type', '')
        
        # 第一步：从通用数据库搜索
        description, method, found = self._search_in_database(self.common_test_db, test_name)
        
        # 第二步：如果未找到，从标准数据库搜索
        if not found:
            description, method, found = self._search_in_database(self.standard_test_db, test_name)
        
        # 第三步：如果仍未找到，尝试AI分析
        if not found:
            if ai_config.get('enable_ai_analysis', False):
                description, method = self._generate_test_content_with_ai(
                    test_name, requirement_description, test_type, ai_config
                )
            else:
                description, method = self._generate_default_content(test_name)
        
        self.logger.info(f"测试项 {test_name} 内容生成完成")
        return description, method
    
    def _search_in_database(
        self,
        database: Dict[str, Tuple[str, str]],
        test_name: str
    ) -> Tuple[str, str, bool]:
        """
        在数据库中搜索测试内容
        
        Args:
            database: 测试数据库
            test_name: 测试项名称
            
        Returns:
            Tuple[str, str, bool]: (测试描述, 测试方法, 是否找到)
        """
        try:
            from .test_type_classifier import ceshixiang_pipei
            
            description, method, found = ceshixiang_pipei(database, test_name)
            return description, method, found == 1
            
        except Exception as e:
            self.logger.error(f"在数据库中搜索测试内容时发生错误: {str(e)}")
            return '', '', False
    
    def _generate_test_content_with_ai(
        self,
        test_name: str,
        requirement_description: str,
        test_type: str,
        ai_config: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        使用AI生成测试内容
        
        Args:
            test_name: 测试项名称
            requirement_description: 需求描述
            test_type: 测试类型
            ai_config: AI配置
            
        Returns:
            Tuple[str, str]: (测试描述, 测试方法)
        """
        try:
            from ....service.test_case_generation import analyze_requirement_text as moxingfenxi
            
            # 清理需求描述
            cleaned_description = requirement_description.replace('\n', '') if requirement_description else ''
            
            if len(cleaned_description) > 5:
                # 尝试AI分析，最多重试指定次数
                attempts = ai_config.get('ai_analysis_attempts', 4)
                detector_flag = ai_config.get('detector_flag', 0)
                
                for attempt in range(1, attempts + 1):
                    try:
                        description, method = moxingfenxi(cleaned_description, test_type, detector_flag)
                        if description != 'error' and method != 'error':
                            self.logger.info(f"AI分析成功生成测试内容: {test_name}")
                            return description, method
                    except Exception as e:
                        self.logger.warning(f"AI分析第{attempt}次尝试失败: {str(e)}")
                        continue
                
                # 如果AI分析失败，使用默认内容
                self.logger.warning(f"AI分析失败，使用默认内容: {test_name}")
                return self._generate_default_content(test_name)
            else:
                # 需求描述太短，使用默认内容
                self.logger.info(f"需求描述太短，使用默认内容: {test_name}")
                return self._generate_default_content(test_name)
                
        except Exception as e:
            self.logger.error(f"使用AI生成测试内容时发生错误: {str(e)}")
            return self._generate_default_content(test_name)
    
    def _optimize_with_ai(
        self,
        requirement_description: str,
        original_description: str,
        original_method: str,
        ai_config: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        使用AI优化测试内容
        
        Args:
            requirement_description: 需求描述
            original_description: 原始测试描述
            original_method: 原始测试方法
            ai_config: AI配置
            
        Returns:
            Tuple[str, str]: (优化后的测试描述, 优化后的测试方法)
        """
        try:
            from ....service.test_case_generation import analyze_code_impact as moxingfenxi_have_zhishi
            
            # 清理需求描述
            cleaned_description = requirement_description.replace('\n', '') if requirement_description else ''
            detector_flag = ai_config.get('detector_flag', 0)
            
            optimized_description, optimized_method = moxingfenxi_have_zhishi(
                cleaned_description, original_description, original_method, detector_flag
            )
            
            self.logger.info("AI优化测试内容成功")
            return optimized_description, optimized_method
            
        except Exception as e:
            self.logger.warning(f"AI优化测试内容失败，使用原始内容: {str(e)}")
            return original_description, original_method
    
    def _generate_default_content(self, test_name: str) -> Tuple[str, str]:
        """
        生成默认测试内容
        
        Args:
            test_name: 测试项名称
            
        Returns:
            Tuple[str, str]: (默认测试描述, 默认测试方法)
        """
        if '故障' in test_name or '报警检测' in test_name:
            description = f'测试软件{test_name}功能实现是否正常'
            method = f'通过代码插桩设置软件故障,通过检测仪发送自检指令,通过检测仪状态监控界面查看测试软件{test_name}功能实现是否正常'
        else:
            description = f'测试软件{test_name}功能实现是否正常'
            method = f'通过检测仪发送测试指令,通过检测仪状态监控界面查看测试软件{test_name}功能实现是否正常'
        
        return description, method
    
    def validate_test_content(
        self,
        test_descriptions: List[str],
        test_methods: List[str]
    ) -> Dict[str, Any]:
        """
        验证测试内容质量
        
        Args:
            test_descriptions: 测试描述列表
            test_methods: 测试方法列表
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            total_items = len(test_descriptions)
            
            # 检查有效的测试描述
            valid_descriptions = sum(
                1 for desc in test_descriptions 
                if desc and desc.strip() and desc != 'error' and len(desc.strip()) > 5
            )
            
            # 检查有效的测试方法
            valid_methods = sum(
                1 for method in test_methods 
                if method and method.strip() and method != 'error' and len(method.strip()) > 5
            )
            
            # 计算质量分数
            description_score = (valid_descriptions / total_items * 100) if total_items > 0 else 0
            method_score = (valid_methods / total_items * 100) if total_items > 0 else 0
            overall_score = (description_score + method_score) / 2
            
            validation_result = {
                'total_items': total_items,
                'valid_descriptions': valid_descriptions,
                'valid_methods': valid_methods,
                'description_score': round(description_score, 2),
                'method_score': round(method_score, 2),
                'quality_score': round(overall_score, 2),
                'is_high_quality': overall_score >= 80,
                'validation_message': self._get_quality_message(overall_score)
            }
            
            self.logger.info(f"测试内容质量验证完成，总体质量分数: {overall_score:.2f}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证测试内容质量时发生错误: {str(e)}")
            return {
                'total_items': 0,
                'valid_descriptions': 0,
                'valid_methods': 0,
                'quality_score': 0,
                'is_high_quality': False,
                'validation_message': f"验证失败: {e}"
            }
    
    def _get_quality_message(self, quality_score: float) -> str:
        """
        获取质量评价消息
        
        Args:
            quality_score: 质量分数
            
        Returns:
            str: 质量评价消息
        """
        if quality_score >= 90:
            return "测试内容质量优秀，所有内容都已正确生成"
        elif quality_score >= 80:
            return "测试内容质量良好，大部分内容已正确生成"
        elif quality_score >= 60:
            return "测试内容质量一般，部分内容需要人工检查"
        elif quality_score >= 40:
            return "测试内容质量较差，建议重新生成或人工编写"
        else:
            return "测试内容质量很差，需要人工重新编写"
    
    def get_generation_statistics(
        self,
        test_items: List[Dict[str, Any]],
        test_descriptions: List[str],
        test_methods: List[str]
    ) -> Dict[str, Any]:
        """
        获取生成统计信息
        
        Args:
            test_items: 测试项列表
            test_descriptions: 测试描述列表
            test_methods: 测试方法列表
            
        Returns:
            Dict[str, Any]: 生成统计信息
        """
        try:
            total_items = len(test_items)
            
            # 统计生成来源
            database_generated = 0
            ai_generated = 0
            default_generated = 0
            
            for index, test_item in enumerate(test_items):
                test_name = test_item.get('name', '')
                
                # 检查是否来自数据库
                _, _, found_common = self._search_in_database(self.common_test_db, test_name)
                _, _, found_standard = self._search_in_database(self.standard_test_db, test_name)
                
                if found_common or found_standard:
                    database_generated += 1
                elif index < len(test_descriptions) and test_descriptions[index] and '测试软件' not in test_descriptions[index]:
                    ai_generated += 1
                else:
                    default_generated += 1
            
            return {
                'total_items': total_items,
                'database_generated': database_generated,
                'ai_generated': ai_generated,
                'default_generated': default_generated,
                'database_rate': round(database_generated / total_items * 100, 2) if total_items > 0 else 0,
                'ai_rate': round(ai_generated / total_items * 100, 2) if total_items > 0 else 0,
                'default_rate': round(default_generated / total_items * 100, 2) if total_items > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取生成统计信息时发生错误: {str(e)}")
            return {
                'total_items': 0,
                'database_generated': 0,
                'ai_generated': 0,
                'default_generated': 0,
                'database_rate': 0,
                'ai_rate': 0,
                'default_rate': 0
            }
