"""
项目基本信息数据处理器

负责处理和组织项目基本信息表所需的数据。
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ProjectInfoDataProcessor:
    """项目基本信息数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.logger = logger
    
    def organize_project_data(
        self,
        basic_info: Dict[str, Any],
        zhuguan_name: str,
        kaifarenxinxi: List[str],
        xinghao_xinxi_list: Optional[List[str]] = None,
        suoshulingyu: str = "通用领域"
    ) -> Dict[str, Any]:
        """
        组织项目基本信息数据
        
        Args:
            basic_info: 基本信息字典
            zhuguan_name: 测试主管姓名
            kaifarenxinxi: 开发人员信息列表 [姓名, 研制部门]
            xinghao_xinxi_list: 型号信息列表（备用数据源）
            suoshulingyu: 所属领域
            
        Returns:
            Dict[str, Any]: 组织后的项目数据
        """
        try:
            # 创建用户软件信息字典（优先级最高）
            user_software_info = self._create_user_software_info(basic_info, suoshulingyu)
            
            # 准备开发人员信息
            kaifaren = kaifarenxinxi[0] if kaifarenxinxi else ""
            yanzhibumen = kaifarenxinxi[1] if len(kaifarenxinxi) > 1 else ""
            
            # 组织完整的项目数据
            project_data = {
                'user_software_info': user_software_info,
                'zhuguan_name': zhuguan_name,
                'kaifaren': kaifaren,
                'yanzhibumen': yanzhibumen,
                'xinghao_xinxi_list': xinghao_xinxi_list or [],
                'suoshulingyu': suoshulingyu,
                'fixed_values': self._get_fixed_values()
            }
            
            self.logger.info(f"项目数据组织完成: {project_data}")
            return project_data
            
        except Exception as e:
            self.logger.error(f"组织项目数据时发生错误: {str(e)}")
            raise
    
    def _create_user_software_info(self, basic_info: Dict[str, Any], default_domain: str) -> Dict[str, str]:
        """
        创建用户软件信息字典
        
        Args:
            basic_info: 基本信息字典
            default_domain: 默认领域
            
        Returns:
            Dict[str, str]: 用户软件信息
        """
        print(f"\n[DATA_PROCESSOR] 收到的 basic_info 内容:")
        for key, value in basic_info.items():
            print(f"  - {key}: '{value}'")
        
        user_software_info = {
            'aircraft_model': basic_info.get('aircraft_model', ''),
            'software_id': basic_info.get('software_id', ''),
            'domain': basic_info.get('domain', default_domain),
            'project_director': basic_info.get('project_director', ''),
            'development_department': basic_info.get('development_department', ''),
            'chief_designer': basic_info.get('chief_designer', ''),
            # ✅ 项目主管：来自前端"可选信息-项目主管"
            'project_manager': basic_info.get('project_manager', '')
        }
        
        print(f"\n[DATA_PROCESSOR] 生成的 user_software_info:")
        for key, value in user_software_info.items():
            print(f"  - {key}: '{value}'")
        print(f"[DATA_PROCESSOR] project_manager 的值: '{user_software_info.get('project_manager', 'NOT_FOUND')}'")
        
        return user_software_info
    
    def _get_fixed_values(self) -> Dict[str, str]:
        """
        获取固定值配置
        
        Returns:
            Dict[str, str]: 固定值字典
        """
        return {
            'test_level': '配置项测试',
            'test_category': '内部测试',
            'test_environment': '半实物环境'
        }
    
    def validate_project_data(self, project_data: Dict[str, Any]) -> bool:
        """
        验证项目数据的完整性
        
        Args:
            project_data: 项目数据字典
            
        Returns:
            bool: 验证结果
        """
        try:
            required_keys = ['user_software_info', 'zhuguan_name', 'kaifaren', 'fixed_values']
            
            for key in required_keys:
                if key not in project_data:
                    self.logger.warning(f"缺少必需的数据字段: {key}")
                    return False
            
            # 验证用户软件信息
            user_info = project_data['user_software_info']
            if not isinstance(user_info, dict):
                self.logger.warning("user_software_info 不是字典类型")
                return False
            
            self.logger.info("项目数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证项目数据时发生错误: {str(e)}")
            return False
    
    def get_data_priority_info(self, project_data: Dict[str, Any]) -> Dict[str, str]:
        """
        获取数据优先级信息（用于调试和日志）
        
        Args:
            project_data: 项目数据字典
            
        Returns:
            Dict[str, str]: 数据来源信息
        """
        user_info = project_data.get('user_software_info', {})
        xinghao_list = project_data.get('xinghao_xinxi_list', [])
        
        priority_info = {}
        
        # 检查各字段的数据来源
        fields = ['aircraft_model', 'software_id', 'domain', 'project_director', 'chief_designer', 'project_manager']
        
        for field in fields:
            user_value = user_info.get(field, '')
            if user_value:
                priority_info[field] = "用户输入"
            elif xinghao_list and len(xinghao_list) > fields.index(field):
                priority_info[field] = "型号信息库"
            else:
                priority_info[field] = "默认值"
        
        return priority_info
