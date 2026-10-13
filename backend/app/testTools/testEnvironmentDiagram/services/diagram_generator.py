import json
import logging
from typing import Dict, Any
from ..config.config import ENVIRONMENT_CONFIG

logger = logging.getLogger(__name__)

class DiagramGenerator:
    """测试环境图生成器"""
    
    def __init__(self):
        self.config = ENVIRONMENT_CONFIG
        
    def generate_diagram_data(self, device_info: Dict[str, str]) -> Dict[str, Any]:
        """
        生成测试环境图的数据结构，供前端绘制使用
        
        Args:
            device_info: 设备信息字典
            
        Returns:
            包含节点和连接信息的字典
        """
        try:
            # 验证和清理输入数据
            cleaned_info = self._validate_and_clean_input(device_info)
            
            # 生成节点数据
            nodes = self._generate_nodes(cleaned_info)
            
            # 生成连接数据
            connections = self._generate_connections(cleaned_info)
            
            # 生成布局信息
            layout = self._generate_layout()
            
            diagram_data = {
                "nodes": nodes,
                "connections": connections,
                "layout": layout,
                "metadata": {
                    "title": "测试环境图",
                    "software_name": cleaned_info["软件名称"]
                }
            }
            
            logger.info(f"成功生成测试环境图数据: {cleaned_info['软件名称']}")
            return diagram_data
            
        except Exception as e:
            logger.error(f"生成测试环境图数据时出错: {str(e)}")
            raise
    
    def _validate_and_clean_input(self, device_info: Dict[str, str]) -> Dict[str, str]:
        """验证和清理输入数据"""
        cleaned_info = {}
        defaults = self.config["default_devices"]
        
        for key, default_value in defaults.items():
            value = device_info.get(key, "").strip()
            if len(value) < 1:
                cleaned_info[key] = default_value
            else:
                cleaned_info[key] = value
                
        # 确保软件名称以"软件"结尾
        if not cleaned_info["软件名称"].endswith("软件"):
            cleaned_info["软件名称"] += "软件"
            
        return cleaned_info
    
    def _generate_nodes(self, device_info: Dict[str, str]) -> list:
        """生成节点数据"""
        nodes = []
        
        # 判断是否为分系统模式
        is_subsystem = bool(device_info.get("主控软件名称", "").strip())
        
        # 检测仪 - 上排左侧
        nodes.append({
            "id": "detector",
            "type": "device",
            "label": device_info["检测仪名称"],
            "description": self.config["device_functions"]["检测仪"],
            "position": {"x": 150, "y": 80},
            "style": {
                "width": 120,
                "height": 60,
                "backgroundColor": "#87CEFA",
                "borderColor": "#4682B4",
                "textColor": "#000000"
            }
        })
        
        # 软件运行设备 - 大框，上排右侧
        device_width = 200 if is_subsystem else 120
        device_height = 120 if is_subsystem else 60
        
        nodes.append({
            "id": "device_container",
            "type": "container",
            "label": device_info["软件运行设备"],
            "description": self.config["device_functions"]["探测设备"],
            "position": {"x": 400, "y": 80},
            "style": {
                "width": device_width,
                "height": device_height,
                "backgroundColor": "#F0F8FF",
                "borderColor": "#32CD32",
                "textColor": "#000000",
                "borderWidth": 2
            }
        })
        
        if is_subsystem:
            # 主控软件 - 在设备框内上方
            nodes.append({
                "id": "main_control_software",
                "type": "software",
                "label": device_info["主控软件名称"],
                "description": f"主控软件",
                "position": {"x": 400, "y": 50},
                "style": {
                    "width": 160,
                    "height": 35,
                    "backgroundColor": "#FFE4B5",
                    "borderColor": "#DEB887",
                    "textColor": "#000000"
                }
            })
            
            # 被测软件 - 在设备框内下方
            nodes.append({
                "id": "tested_software",
                "type": "software", 
                "label": device_info["软件名称"],
                "description": f"被测软件",
                "position": {"x": 400, "y": 110},
                "style": {
                    "width": 160,
                    "height": 35,
                    "backgroundColor": "#FFB6C1",
                    "borderColor": "#FF69B4",
                    "textColor": "#000000"
                }
            })
        else:
            # 主控软件模式 - 软件直接在设备框内
            nodes.append({
                "id": "main_software",
                "type": "software",
                "label": device_info["软件名称"],
                "description": f"运行在{device_info['软件运行设备']}上的软件",
                "position": {"x": 400, "y": 80},
                "style": {
                    "width": 160,
                    "height": 35,
                    "backgroundColor": "#FFE4B5",
                    "borderColor": "#DEB887",
                    "textColor": "#000000"
                }
            })
        
        # 调试计算机 - 左侧
        nodes.append({
            "id": "debug_computer",
            "type": "device",
            "label": "调试计算机",
            "description": self.config["device_functions"]["调试计算机"],
            "position": {"x": 150, "y": 200},
            "style": {
                "width": 120,
                "height": 60,
                "backgroundColor": "#FFB6C1",
                "borderColor": "#FF69B4",
                "textColor": "#000000"
            }
        })
        
        # 目标模拟器 - 可选，下方中央
        if device_info.get("目标模拟器", "").strip():
            nodes.append({
                "id": "target_simulator",
                "type": "device",
                "label": device_info["目标模拟器"],
                "description": self.config["device_functions"]["目标模拟器"],
                "position": {"x": 300, "y": 280},
                "style": {
                    "width": 120,
                    "height": 60,
                    "backgroundColor": "#F0E68C",
                    "borderColor": "#DAA520",
                    "textColor": "#000000"
                }
            })
        
        return nodes
    
    def _generate_connections(self, device_info: Dict[str, str]) -> list:
        """生成连接数据"""
        connections = []
        
        # 判断是否为分系统模式
        is_subsystem = bool(device_info.get("主控软件名称", "").strip())
        
        if is_subsystem:
            # 分系统模式的连接
            # 检测仪 -> 主控软件
            connections.append({
                "id": "conn1",
                "from": "detector",
                "to": "main_control_software",
                "label": device_info["接口1"],
                "type": "bidirectional",
                "style": {
                    "strokeColor": "#4682B4",
                    "strokeWidth": 2,
                    "strokeDasharray": "none"
                }
            })
            
            # 主控软件 -> 被测软件
            connections.append({
                "id": "conn_internal",
                "from": "main_control_software", 
                "to": "tested_software",
                "label": device_info["主控与被测软件接口类型"],
                "type": "bidirectional",
                "style": {
                    "strokeColor": "#8B4513",
                    "strokeWidth": 2,
                    "strokeDasharray": "none"
                }
            })
            
            # 被测软件 -> 调试计算机
            connections.append({
                "id": "conn2",
                "from": "tested_software",
                "to": "debug_computer", 
                "label": device_info["接口2"],
                "type": "bidirectional",
                "style": {
                    "strokeColor": "#32CD32",
                    "strokeWidth": 2,
                    "strokeDasharray": "none"
                }
            })
            
        else:
            # 主控软件模式的连接
            # 检测仪 -> 软件
            connections.append({
                "id": "conn1",
                "from": "detector",
                "to": "main_software",
                "label": device_info["接口1"],
                "type": "bidirectional",
                "style": {
                    "strokeColor": "#4682B4",
                    "strokeWidth": 2,
                    "strokeDasharray": "none"
                }
            })
            
            # 软件 -> 调试计算机
            connections.append({
                "id": "conn2",
                "from": "main_software",
                "to": "debug_computer",
                "label": device_info["接口2"],
                "type": "bidirectional",
                "style": {
                    "strokeColor": "#32CD32",
                    "strokeWidth": 2,
                    "strokeDasharray": "none"
                }
            })
        
        # 目标模拟器连接（如果存在）
        if device_info.get("目标模拟器", "").strip():
            target_node = "tested_software" if is_subsystem else "main_software"
            connections.append({
                "id": "conn3",
                "from": "target_simulator",
                "to": target_node,
                "label": "目标信号",
                "type": "unidirectional",
                "style": {
                    "strokeColor": "#DAA520",
                    "strokeWidth": 2,
                    "strokeDasharray": "5,5"
                }
            })
        
        return connections
    
    def _generate_layout(self) -> Dict[str, Any]:
        """生成布局信息"""
        return {
            "type": "custom",
            "canvas": {
                "width": 600,
                "height": 350,
                "backgroundColor": "#FFFFFF"
            },
            "grid": {
                "enabled": False,  # 去除网格
                "size": 20,
                "color": "#E0E0E0"
            }
        }
    
    def generate_description(self, device_info: Dict[str, str]) -> str:
        """
        生成测试环境描述文本
        
        Args:
            device_info: 设备信息字典
            
        Returns:
            测试环境描述文本
        """
        try:
            cleaned_info = self._validate_and_clean_input(device_info)
            
            description = (
                f"如上图所示，本次测试环境中，主要使用了{cleaned_info['检测仪名称']}、"
                f"{cleaned_info['软件运行设备']}、{cleaned_info['目标模拟器']}以及调试计算机四个关键设备。"
                f"其中{cleaned_info['检测仪名称']}主要用于向{cleaned_info['软件名称']}发送测试指令，"
                f"同时监控软件返回的工作状态；{cleaned_info['软件运行设备']}则是运行{cleaned_info['软件名称']}的主要平台，"
                f"内置其他子系统的软硬件，可与被测软件进行实时数据交互，保证软件功能与性能等的完整测试；"
                f"调试计算机主要负责代码调试、编译、烧录及软件状态的在线监控；"
                f"{cleaned_info['目标模拟器']}主要用于目标模拟，"
                f"这些设备协同工作，确保了{cleaned_info['软件名称']}测试的顺利完成。"
            )
            
            logger.info(f"成功生成测试环境描述: {len(description)} 字符")
            return description
            
        except Exception as e:
            logger.error(f"生成测试环境描述时出错: {str(e)}")
            raise 