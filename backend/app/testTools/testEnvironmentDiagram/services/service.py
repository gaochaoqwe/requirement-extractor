import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple

from ..database.database import get_db_session
from ..models.models import TestEnvironmentSession
from .diagram_generator import DiagramGenerator

logger = logging.getLogger(__name__)

class TestEnvironmentService:
    """测试环境图服务"""
    
    def __init__(self):
        self.diagram_generator = DiagramGenerator()
        self.current_status = {}  # 内存中的状态缓存
        
    def create_environment_diagram(self, device_info: Dict[str, str]) -> str:
        """
        创建测试环境图
        
        Args:
            device_info: 设备信息
            
        Returns:
            会话ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            # 创建数据库记录
            with get_db_session() as db:
                session = TestEnvironmentSession(
                    session_id=session_id,
                    软件名称=device_info.get("软件名称", ""),
                    检测仪名称=device_info.get("检测仪名称", ""),
                    软件运行设备=device_info.get("软件运行设备", ""),
                    接口1=device_info.get("接口1", ""),
                    接口2=device_info.get("接口2", ""),
                    目标模拟器=device_info.get("目标模拟器", ""),
                    主控软件名称=device_info.get("主控软件名称", ""),
                    主控与被测软件接口类型=device_info.get("主控与被测软件接口类型", ""),
                    status="processing"
                )
                db.add(session)
                db.commit()
                
            # 更新内存状态
            self.current_status[session_id] = "processing"
            
            # 生成图表数据和描述
            diagram_data = self.diagram_generator.generate_diagram_data(device_info)
            description = self.diagram_generator.generate_description(device_info)
            
            # 更新数据库
            with get_db_session() as db:
                session = db.query(TestEnvironmentSession).filter(
                    TestEnvironmentSession.session_id == session_id
                ).first()
                
                if session:
                    session.diagram_data = json.dumps(diagram_data, ensure_ascii=False)
                    session.description = description
                    session.status = "completed"
                    session.updated_at = datetime.utcnow()
                    
            # 更新内存状态
            self.current_status[session_id] = "completed"
            
            logger.info(f"成功创建测试环境图，会话ID: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建测试环境图时出错: {str(e)}")
            # 更新错误状态
            if 'session_id' in locals():
                self._update_session_error(session_id, str(e))
            raise
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话状态信息
        """
        try:
            # 先检查内存状态
            if session_id in self.current_status:
                status = self.current_status[session_id]
            else:
                # 从数据库查询
                with get_db_session() as db:
                    session = db.query(TestEnvironmentSession).filter(
                        TestEnvironmentSession.session_id == session_id
                    ).first()
                    
                    if not session:
                        return {"status": "not_found", "message": "会话不存在"}
                    
                    status = session.status
                    self.current_status[session_id] = status
            
            return {
                "status": status,
                "session_id": session_id,
                "message": self._get_status_message(status)
            }
            
        except Exception as e:
            logger.error(f"获取会话状态时出错: {str(e)}")
            return {"status": "error", "message": f"获取状态失败: {str(e)}"}
    
    def get_diagram_result(self, session_id: str) -> Dict[str, Any]:
        """
        获取图表结果
        
        Args:
            session_id: 会话ID
            
        Returns:
            图表数据和描述
        """
        try:
            with get_db_session() as db:
                session = db.query(TestEnvironmentSession).filter(
                    TestEnvironmentSession.session_id == session_id
                ).first()
                
                if not session:
                    raise Exception("会话不存在")
                
                if session.status != "completed":
                    raise Exception(f"图表尚未完成，当前状态: {session.status}")
                
                diagram_data = json.loads(session.diagram_data) if session.diagram_data else {}
                
                return {
                    "diagram_data": diagram_data,
                    "description": session.description,
                    "device_info": {
                        "软件名称": session.软件名称,
                        "检测仪名称": session.检测仪名称,
                        "软件运行设备": session.软件运行设备,
                        "接口1": session.接口1,
                        "接口2": session.接口2,
                        "目标模拟器": session.目标模拟器,
                        "主控软件名称": session.主控软件名称,
                        "主控与被测软件接口类型": session.主控与被测软件接口类型
                    }
                }
                
        except Exception as e:
            logger.error(f"获取图表结果时出错: {str(e)}")
            raise
    
    def _update_session_error(self, session_id: str, error_message: str):
        """更新会话错误状态"""
        try:
            with get_db_session() as db:
                session = db.query(TestEnvironmentSession).filter(
                    TestEnvironmentSession.session_id == session_id
                ).first()
                
                if session:
                    session.status = "error"
                    session.error_message = error_message
                    session.updated_at = datetime.utcnow()
                    
            self.current_status[session_id] = "error"
            
        except Exception as e:
            logger.error(f"更新会话错误状态时出错: {str(e)}")
    
    def _get_status_message(self, status: str) -> str:
        """获取状态消息"""
        messages = {
            "pending": "等待处理",
            "processing": "正在生成测试环境图",
            "completed": "测试环境图生成完成",
            "error": "生成失败"
        }
        return messages.get(status, "未知状态") 