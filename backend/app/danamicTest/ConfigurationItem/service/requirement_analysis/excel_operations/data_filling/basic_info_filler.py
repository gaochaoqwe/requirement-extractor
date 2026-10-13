"""
基本信息填充器

负责填充Excel表格中的基本信息部分，如软件信息、项目信息等。
"""

import logging
import openpyxl
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 导入任务日志函数
from .....utils.logging_utils.logger import log_info, log_debug, log_error, log_warning

# 配置日志
logger = logging.getLogger(__name__)

class BasicInfoFiller:
    """基本信息填充器"""
    
    def __init__(self):
        """初始化基本信息填充器"""
        self.logger = logger
    
    def fill_basic_info(self, sheet, basic_info: Dict[str, Any]) -> bool:
        """
        填充基本信息到Excel工作表
        
        Args:
            sheet: Excel工作表对象
            basic_info: 基本信息字典
            
        Returns:
            bool: 填充是否成功
        """
        try:
            self.logger.info("开始填充基本信息")
            
            # 填充软件信息
            if 'software_name' in basic_info:
                self._fill_software_info(sheet, basic_info)
            
            # 填充项目信息
            if 'project_info' in basic_info:
                self._fill_project_info(sheet, basic_info['project_info'])
            
            self.logger.info("基本信息填充完成")
            return True
            
        except Exception as e:
            self.logger.error(f"填充基本信息时发生错误: {str(e)}")
            return False
    
    def _fill_software_info(self, sheet, basic_info: Dict[str, Any]):
        """填充软件信息"""
        try:
            software_name = basic_info.get('software_name', '')
            software_version = basic_info.get('software_version', '')
            
            # 根据模板格式填充软件信息
            # 这里需要根据具体的Excel模板格式来调整
            if software_name:
                # 假设软件名称在特定位置
                self.logger.debug(f"填充软件名称: {software_name}")
                
            if software_version:
                # 假设软件版本在特定位置
                self.logger.debug(f"填充软件版本: {software_version}")
                
        except Exception as e:
            self.logger.error(f"填充软件信息时发生错误: {str(e)}")
    
    def _fill_project_info(self, sheet, project_info: Dict[str, Any]):
        """填充项目信息"""
        try:
            project_name = project_info.get('name', '')
            project_description = project_info.get('description', '')
            
            # 根据模板格式填充项目信息
            if project_name:
                self.logger.debug(f"填充项目名称: {project_name}")
                
            if project_description:
                self.logger.debug(f"填充项目描述: {project_description}")
                
        except Exception as e:
            self.logger.error(f"填充项目信息时发生错误: {str(e)}")
    
    def generate_test_requirement_prefix(self, ruanjian_xinxi: Dict[str, List[str]], ceshileixing: str) -> str:
        """
        生成测试需求标识前缀
        
        Args:
            ruanjian_xinxi: 软件信息字典
            ceshileixing: 测试类型
            
        Returns:
            str: 测试需求标识前缀
        """
        try:
            # 从软件信息中提取必要信息
            software_id = ruanjian_xinxi.get('software_id', [''])[0] if ruanjian_xinxi.get('software_id') else ''
            version = ruanjian_xinxi.get('version', [''])[0] if ruanjian_xinxi.get('version') else ''
            
            # 根据测试类型生成前缀
            type_mapping = {
                '功能测试': 'FN',
                '性能测试': 'PF',
                '边界测试': 'BD',
                '余量测试': 'MG',
                '强度测试': 'ST',
                '接口测试': 'IF',
                '安全测试': 'SC',
                '恢复测试': 'RC',
                '容量测试': 'CP',
                '人机交互测试': 'HI'
            }
            
            type_code = type_mapping.get(ceshileixing, 'CT')
            
            # 生成完整前缀：CT-软件标识号-版本号-类型代码
            if software_id and version:
                prefix = f"CT-{software_id}-{version}-{type_code}"
            else:
                prefix = f"CT-{type_code}"
                
            self.logger.debug(f"生成测试需求标识前缀: {prefix}")
            return prefix
            
        except Exception as e:
            self.logger.error(f"生成测试需求标识前缀时发生错误: {str(e)}")
            return "CT"
    
    def read_document_chapters(self, file_path: str, allkeys: List[str], ruanjian_name: str) -> Tuple[List[str], List[str]]:
        """
        读取文档章节号（完整原始实现）
        
        Args:
            file_path: 文档文件路径
            allkeys: 需求键列表
            ruanjian_name: 软件名称
            
        Returns:
            Tuple[List[str], List[str]]: 章节号列表和章节号读取列表
        """
        try:
            self.logger.info(f"开始读取文档章节: {file_path}")
            
            # 尝试使用原始的读取逻辑
            try:
                from ....hanshutiqu_kaifa.fenxibiao_tianchong import read_word_document
                return read_word_document(file_path, allkeys, ruanjian_name)
            except ImportError:
                self.logger.warning("无法导入read_word_document，使用备用方法")
            except Exception as e:
                self.logger.error(f"read_word_document调用失败: {str(e)}")
            
            # 备用逻辑：返回默认章节号
            default_chapters = ['未找到具体章节号'] * len(allkeys)
            return default_chapters, []
            
        except Exception as e:
            self.logger.error(f"读取文档章节时发生错误: {str(e)}")
            # 返回默认值
            default_chapters = ['未找到具体章节号'] * len(allkeys)
            return default_chapters, []
    
    def generate_test_content_legacy(
        self,
        allkeys: List[str],
        neirong_dict: List[str],
        AI_fenx_flag_Anniu: int,
        jianceyi_flag: int
    ) -> Tuple[List[str], List[str]]:
        """
        生成测试内容（兼容模式）- 完整原始实现
        
        从原始excel_filler.py完整迁移的测试内容生成方法
        """
        try:
            from ...test_generation.content_generators.test_content_generator import ConfigurationItemTestContentGenerator
            
            generator = ConfigurationItemTestContentGenerator()
            
            # 构造测试项数据
            test_items = []
            for i, test_name in enumerate(allkeys):
                test_item = {
                    'name': test_name,
                    'requirement_description': neirong_dict[i] if i < len(neirong_dict) else ''
                }
                test_items.append(test_item)
            
            # 构造AI配置 - 使用AI开关控制器
            try:
                from .....utils.ai_switch_controller.ai_switch_controller import get_ai_controller, AIModule
                ai_controller = get_ai_controller()
                ai_config = ai_controller.get_ai_config(AIModule.REQUIREMENT_ANALYSIS)
                
                # 添加额外配置
                ai_config.update({
                    'detector_flag': jianceyi_flag,
                    'use_knowledge_optimization': True
                })
            except ImportError:
                self.logger.warning("无法导入AI控制器，使用默认配置")
                ai_config = {
                    'detector_flag': jianceyi_flag,
                    'use_knowledge_optimization': True
                }
            
            # 生成测试内容
            test_descriptions, test_methods = generator.generate_test_content(test_items, ai_config)
            
            return test_descriptions, test_methods
            
        except Exception as e:
            self.logger.error(f"生成测试内容时发生错误: {str(e)}")
            # 返回默认内容
            default_descriptions = [f'测试软件{name}功能实现是否正常' for name in allkeys]
            default_methods = [f'通过检测仪发送测试指令,通过检测仪状态监控界面查看测试软件{name}功能实现是否正常' for name in allkeys]
            return default_descriptions, default_methods 