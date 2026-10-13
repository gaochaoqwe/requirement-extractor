
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试主程序

本程序负责管理回归测试相关的表单生成和分析功能。
基于原始项目中验证的回归测试逻辑重新实现。
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import uuid
from datetime import datetime
import shutil

# 导入资源管理器和日志系统
try:
    from .resources.resource_manager import get_resource_manager
    from .utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    from .utils.logging_utils.performance_monitor import monitor_step, RegressionTestSteps
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from app.danamicTest.Regression.resources.resource_manager import get_resource_manager
    from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    from app.danamicTest.Regression.utils.logging_utils.performance_monitor import monitor_step, RegressionTestSteps

# 导入已重构的service模块
try:
    # 尝试相对导入
    from .service.form_builder import (
        RegressionFormBuilderService,
        RegressionFormBuilderWithPlanningService
    )

except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from app.danamicTest.Regression.service.form_builder import (
        RegressionFormBuilderService,
        RegressionFormBuilderWithPlanningService
    )


# 工具函数
def format_zhangjiehao(modified_lines_Temp):
    """
    读取测试表单模板，并返回一个字典:{'章节名'，'章节号'}
    
    Args:
        modified_lines_Temp: 修改后的行列表
        
    Returns:
        tuple: 包含不同级别章节信息的元组
    """
    # 对word文档中的章节号进行分析
    final_jieguo_Temp2 = {}
    final_jieguo_Temp3 = {}
    final_jieguo_Temp4 = {}
    final_jieguo_Temp5 = {}
    final_jieguo_Temp6 = {}
    final_jieguo_Temp7 = {}
    zong_zhangjie_hebing = {}
    
    for item in modified_lines_Temp:
        zhangjiehao, zhangjie_name, zhangjie_jibie = extract_chapter_number(item)  # 返回章节对应的章节号 章节内容  和章节的级别
        zong_zhangjie_hebing[zhangjie_name] = zhangjiehao
        
        if zhangjie_jibie == 1:
            if zhangjiehao.startswith("2.") or zhangjiehao.startswith("3.") or zhangjiehao.startswith("4.") or zhangjiehao.startswith("5."):
                final_jieguo_Temp2[zhangjie_name] = zhangjiehao
        elif zhangjie_jibie == 2:
            if zhangjiehao.startswith("2.") or zhangjiehao.startswith("3.") or zhangjiehao.startswith("4.") or zhangjiehao.startswith("5."):
                final_jieguo_Temp3[zhangjie_name] = zhangjiehao
        elif zhangjie_jibie == 3:
            if zhangjiehao.startswith("2.") or zhangjiehao.startswith("3.") or zhangjiehao.startswith("4.") or zhangjiehao.startswith("5."):
                final_jieguo_Temp4[zhangjie_name] = zhangjiehao
        elif zhangjie_jibie == 4:
            if zhangjiehao.startswith("2.") or zhangjiehao.startswith("3.") or zhangjiehao.startswith("4.") or zhangjiehao.startswith("5."):
                final_jieguo_Temp5[zhangjie_name] = zhangjiehao
        elif zhangjie_jibie == 5:
            if zhangjiehao.startswith("2.") or zhangjiehao.startswith("3.") or zhangjiehao.startswith("4.") or zhangjiehao.startswith("5."):
                final_jieguo_Temp6[zhangjie_name] = zhangjiehao
        elif zhangjie_jibie == 6:
            if zhangjiehao.startswith("2.") or zhangjiehao.startswith("3.") or zhangjiehao.startswith("4.") or zhangjiehao.startswith("5."):
                final_jieguo_Temp7[zhangjie_name] = zhangjiehao
                
    return final_jieguo_Temp2, final_jieguo_Temp3, final_jieguo_Temp4, final_jieguo_Temp5, final_jieguo_Temp6, final_jieguo_Temp7, zong_zhangjie_hebing

# 创建service实例
form_builder_service = RegressionFormBuilderService()
form_builder_with_planning_service = RegressionFormBuilderWithPlanningService()

# 为了向后兼容，创建函数别名
def ceshibiaodan_tianchong(*args, **kwargs):
    """回归测试表单填充 - 无策划表版本"""
    return form_builder_service.ceshibiaodan_tianchong(*args, **kwargs)

def ceshibiaodan_tianchong_have_cehua(*args, **kwargs):
    """回归测试表单填充 - 有策划表版本"""
    return form_builder_with_planning_service.ceshibiaodan_tianchong_have_cehua(*args, **kwargs)

def check_word_document_huigui(*args, **kwargs):
    """检查回归测试文档"""
    return form_builder_service.check_word_document_huigui(*args, **kwargs)



def read_word_tables(*args, **kwargs):
    """读取Word表格"""
    return form_builder_service.read_word_tables(*args, **kwargs)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegressionTestManager:
    """回归测试管理器"""
    
    def __init__(self):
        """初始化回归测试管理器"""
        self.session_data = {}
        self.progress_data = {}
        
        # 初始化资源管理器
        self.resource_manager = get_resource_manager()
        
        # 验证资源文件
        is_valid, missing = self.resource_manager.validate_resources()
        if not is_valid:
            logger.warning(f"缺失资源文件: {missing}")
        else:
            logger.info("所有资源文件验证通过")
    
    async def generate_complete_forms(self, 
                                    input_path: str,
                                    test_manager: str = "",
                                    test_personnel: str = "", 
                                    developer: str = "",
                                    domain: str = "",
                                    ai_analysis: bool = True,
                                    deep_analysis: bool = True,
                                    detection_advice: bool = True,
                                    planning_path: str = "",
                                    user_software_info: Dict[str, str] = None,
                                    session_id: str = None,
                                    code_file_path: str = None,
                                    code_lines: int = None) -> Dict[str, Any]:
        """
        生成完整的回归测试表单套件
        
        Args:
            input_path: 输入文档路径
            test_manager: 测试主管
            test_personnel: 测试人员
            developer: 开发人员
            domain: 所属领域
            ai_analysis: AI分析标志
            deep_analysis: 深度分析标志
            detection_advice: 检测建议标志
            planning_path: 策划表路径（可选）
            
        Returns:
            生成结果字典
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        try:
            log_info("开始生成回归测试表单套件", "regression_manager")
            log_info(f"输入参数: input_path={input_path}, test_manager={test_manager}, ai_analysis={ai_analysis}", "regression_manager")
            
            # 准备基本信息
            basic_info = {
                'test_manager': test_manager,
                'test_personnel': test_personnel, 
                'developer': developer,
                'domain': domain,
                'test_type': '回归测试',
                'ai_analysis': 1 if ai_analysis else 0,
                'deep_analysis': 1 if deep_analysis else 0,
                'detection_advice': 1 if detection_advice else 0,
                'code_file_path': code_file_path,
                'code_lines': code_lines
            }
            
            # 根据是否有策划表选择处理流程
            if planning_path and os.path.exists(planning_path):
                log_info(f"使用有策划表的处理流程: {planning_path}", "regression_manager")
                return await self._generate_forms_with_planning(
                    session_id, input_path, planning_path, basic_info, user_software_info
                )
            else:
                log_info("使用无策划表的处理流程", "regression_manager")
                return await self._generate_forms_without_planning(
                    session_id, input_path, basic_info, user_software_info
                )
                
        except Exception as e:
            log_error(f"生成回归测试表单失败", "regression_manager", e)
            logger.error(f"生成回归测试表单失败: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "message": "回归测试表单生成失败"
            }
    
    async def _generate_forms_with_planning(self, 
                                          session_id: str,
                                          input_path: str, 
                                          planning_path: str,
                                          basic_info: Dict[str, Any],
                                          user_software_info: Dict[str, str] = None) -> Dict[str, Any]:
        """
        基于策划表生成回归测试表单
        
        Args:
            session_id: 会话ID
            input_path: 输入文档路径
            planning_path: 策划表路径
            basic_info: 基本信息字典
            
        Returns:
            生成结果字典
        """
        try:
            # 更新进度：开始处理
            await self._update_progress(session_id, 10, "读取策划表内容")
            
            # 更新进度：验证文档
            await self._update_progress(session_id, 25, "验证软件变更与影响域分析报告")
            
            # 更新进度：提取软件版本信息
            await self._update_progress(session_id, 40, "提取软件版本信息")
            
            # 更新进度：生成测试项描述
            await self._update_progress(session_id, 60, "生成回归测试项描述")
            
            # 更新进度：填充表单
            await self._update_progress(session_id, 80, "填充测试表单")
            
            # 调用核心函数
            result = ceshibiaodan_tianchong_have_cehua(
                input_path, 
                planning_path,
                basic_info['test_manager'],
                basic_info['test_personnel'],
                basic_info['developer'],
                basic_info['test_type'],
                basic_info['ai_analysis'],
                basic_info['deep_analysis'],
                basic_info['detection_advice']
            )
            
            if result == 1:
                await self._update_progress(session_id, 100, "生成完成")
                log_info("✅ 回归测试策划表生成成功", Path(__file__).stem)
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "output_path": planning_path,
                    "file_type": "planning_table",
                    "message": "回归测试表单生成成功"
                }
            else:
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": "软件配置信息不完整",
                    "message": "请检查策划表中的软件配置信息"
                }
                
        except Exception as e:
            logger.error(f"基于策划表生成回归测试表单失败: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "message": "回归测试表单生成失败"
            }
    
    async def _generate_forms_without_planning(self, 
                                             session_id: str,
                                             input_path: str,
                                             basic_info: Dict[str, Any],
                                             user_software_info: Dict[str, str] = None) -> Dict[str, Any]:
        """
        无策划表的回归测试表单生成
        
        Args:
            session_id: 会话ID
            input_path: 输入文档路径
            basic_info: 基本信息字典
            
        Returns:
            生成结果字典
        """
        try:
            # 更新进度：验证文档
            await self._update_progress(session_id, 10, "验证软件变更与影响域分析报告")
            
            # 更新进度：准备模板
            await self._update_progress(session_id, 20, "准备测试表单模板")
            
            # 更新进度：分析代码差异
            await self._update_progress(session_id, 30, "统计代码差异行数")
            
            # 更新进度：提取软件信息
            await self._update_progress(session_id, 40, "提取软件信息")
            
            # 更新进度：读取型号信息
            await self._update_progress(session_id, 50, "读取软件型号信息数据库")
            
            # 更新进度：分析测试内容
            await self._update_progress(session_id, 60, "分析测试内容")
            
            # 更新进度：生成测试项
            await self._update_progress(session_id, 70, "生成测试项内容")
            
            # 更新进度：填充表单
            await self._update_progress(session_id, 80, "填充测试表单")
            
            # 获取开发人员信息 - 直接使用前端传递的开发人员信息
            developer_name = basic_info.get('developer', '未指定开发人员')
            log_info(f"前端传递的开发人员信息: {developer_name}", "regression_manager")

            # 构建开发人员信息数组（兼容原有格式）
            developer_info = [developer_name, '软件测试部'] if developer_name and developer_name.strip() else ['未指定开发人员', '软件测试部']
            log_info(f"构建的开发人员信息数组: {developer_info}", "regression_manager")
            
            # 查找需求目录文档
            catalog_path = None
            session_dir = Path(input_path).parent  # 修正：获取会话目录而不是文件路径
            if session_dir.exists():
                for file_path in session_dir.glob("catalog_*"):
                    if file_path.suffix.lower() in ['.doc', '.docx']:
                        catalog_path = str(file_path)
                        log_info(f"找到目录文档: {catalog_path}", Path(__file__).stem)
                        break
            
            if not catalog_path:
                log_warning(f"未在会话目录中找到目录文档 (catalog_*.docx): {session_dir}", Path(__file__).stem)
            
            # 调用核心函数
            # 需要传递目录路径而不是文件路径
            input_dir = str(Path(input_path).parent)
            result = ceshibiaodan_tianchong(
                input_dir,  # 传递目录路径
                basic_info['test_manager'],
                basic_info['test_personnel'], 
                developer_info,
                basic_info['test_type'],
                basic_info['ai_analysis'],
                basic_info['deep_analysis'],
                basic_info['domain'],
                basic_info['detection_advice'],
                resource_manager=self.resource_manager,
                user_software_info=user_software_info,
                catalog_path=catalog_path,
                code_lines=basic_info.get('code_lines'),
                code_file_path=basic_info.get('code_file_path')
            )
            
            if result.get("success", False):
                await self._update_progress(session_id, 100, "生成完成")
                log_info("✅ 回归测试完整表单生成成功", Path(__file__).stem)
                
                # 生成的文件路径 - 使用session目录下的output文件夹
                session_dir = Path(input_path).parent
                output_dir = session_dir / "output"
                output_dir.mkdir(exist_ok=True)
                output_path = str(output_dir / "需求分析表(精准测试工具生成).xlsx")
                
                # 直接从返回结果中获取文件路径
                try:
                    import shutil
                    source_file = result.get("file_path")
                    if source_file and os.path.exists(source_file):
                        shutil.copy2(source_file, output_path)
                        log_info(f"文件已复制到输出目录: {output_path}", Path(__file__).stem)
                    else:
                        log_warning(f"生成的文件不存在: {source_file}", Path(__file__).stem)
                except Exception as e:
                    log_error(f"复制输出文件时出错: {e}", Path(__file__).stem)
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "output_path": output_path,
                    "file_type": "complete_forms",
                    "message": "回归测试表单生成成功",
                    "generated_files": [
                        {
                            "name": "需求分析表(精准测试工具生成).xlsx",
                            "path": output_path,
                            "type": "excel",
                            "size": Path(output_path).stat().st_size if Path(output_path).exists() else 0
                        }
                    ]
                }
            else:
                error_msg = result.get("error", "表单生成失败")
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": error_msg,
                    "message": f"回归测试表单生成失败: {error_msg}"
                }
                
        except Exception as e:
            logger.error(f"无策划表生成回归测试表单失败: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "message": "回归测试表单生成失败"
            }
    
    async def _update_progress(self, session_id: str, progress: int, message: str):
        """
        更新进度信息
        
        Args:
            session_id: 会话ID
            progress: 进度百分比
            message: 进度描述
        """
        self.progress_data[session_id] = {
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # 模拟处理时间
        await asyncio.sleep(0.5)
    
    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """
        获取进度信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            进度信息字典
        """
        return self.progress_data.get(session_id, {
            'progress': 0,
            'message': '未开始',
            'timestamp': datetime.now().isoformat()
        })
    
    def analyze_regression_impact(self, 
                                input_path: str,
                                test_type: str = '回归测试') -> Dict[str, Any]:
        """
        分析回归影响域
        
        Args:
            input_path: 输入文档路径
            test_type: 测试类型 ('回归测试')
            
        Returns:
            影响域分析结果
        """
        try:
            # 验证输入文档
            if not check_word_document_huigui(input_path):
                return {
                    "success": False,
                    "error": "未找到软件变更与影响域分析报告"
                }
            
            # 这里可以添加具体的影响域分析逻辑
            # 基于原始项目中的分析方法
            
            return {
                "success": True,
                "impact_functions": [],
                "change_tracking": {},
                "test_requirements": []
            }
            
        except Exception as e:
            logger.error(f"分析回归影响域失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _prepare_resources(self, session_id: str):
        """
        准备会话所需的资源文件
        
        Args:
            session_id: 会话ID
        """
        session_dir = os.path.join(os.getcwd(), 'sessions', session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # 复制必要的资源文件到会话目录
        try:
            # 复制需求分析表模板文件到输出目录
            logger.info(f"复制需求分析表模板: {self.resource_manager.get_template_path('需求分析表(精准测试工具生成).xlsx')}")
            shutil.copy2(
                self.resource_manager.get_template_path('需求分析表(精准测试工具生成).xlsx'),
                os.path.join(session_dir, 'resources', '需求分析表(精准测试工具生成).xlsx')
            )
            
            logger.info(f"复制问题单模板: {self.resource_manager.get_template_path('问题单设计.xlsx')}")
            shutil.copy2(
                self.resource_manager.get_template_path('问题单设计.xlsx'),
                os.path.join(session_dir, 'resources', '问题单设计.xlsx')
            )
            
            # 临时修复：创建传统的输出目录结构
            traditional_output_dir = 'D:/baxiang_ceshi/CeshiDan'
            os.makedirs(traditional_output_dir, exist_ok=True)
            
            # 复制模板文件到传统输出目录
            shutil.copy2(
                self.resource_manager.get_template_path('需求分析表(精准测试工具生成).xlsx'),
                os.path.join(traditional_output_dir, '需求分析表(精准测试工具生成).xlsx')
            )
        except Exception as e:
            logger.error(f"准备会话资源失败: {e}")


def generate_regression_forms(input_path: str,
                            test_manager: str = "",
                            test_personnel: str = "",
                            developer: str = "",
                            domain: str = "",
                            planning_path: str = "") -> Dict[str, Any]:
    """
    生成回归测试表单
    
    Args:
        input_path: 输入文档路径
        test_manager: 测试主管
        test_personnel: 测试人员
        developer: 开发人员
        domain: 所属领域
        planning_path: 策划表路径（可选）
        
    Returns:
        生成结果字典
    """
    try:
        log_info(f"开始生成回归测试表单...", Path(__file__).stem)
        log_info(f"输入路径: {input_path}", Path(__file__).stem)
        log_info(f"测试主管: {test_manager}", Path(__file__).stem)
        log_info(f"测试人员: {test_personnel}", Path(__file__).stem)
        log_info(f"开发人员: {developer}", Path(__file__).stem)
        log_info(f"所属领域: {domain}", Path(__file__).stem)
        log_info(f"策划表路径: {planning_path}", Path(__file__).stem)
        
        manager = RegressionTestManager()
        
        # 使用同步方式调用异步函数
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if planning_path and os.path.exists(planning_path):
            # 有策划表的情况
            result = loop.run_until_complete(
                manager._generate_forms_with_planning(
                    str(uuid.uuid4()), input_path, planning_path, {
                        'test_manager': test_manager,
                        'test_personnel': test_personnel,
                        'developer': developer,
                        'domain': domain,
                        'test_type': '回归测试',
                        'ai_analysis': 1,
                        'deep_analysis': 1,
                        'detection_advice': 1
                    }
                )
            )
        else:
            # 无策划表的情况
            result = loop.run_until_complete(
                manager._generate_forms_without_planning(
                    str(uuid.uuid4()), input_path, {
                        'test_manager': test_manager,
                        'test_personnel': test_personnel,
                        'developer': developer,
                        'domain': domain,
                        'test_type': '回归测试',
                        'ai_analysis': 1,
                        'deep_analysis': 1,
                        'detection_advice': 1
                    }
                )
            )
        
        loop.close()
        
        log_info(f"回归测试表单生成完成！", Path(__file__).stem)
        return result
        
    except Exception as e:
        error_msg = f"生成回归测试表单时发生错误: {str(e)}"
        log_info(str(error_msg), Path(__file__).stem)
        logger.error(error_msg)
        return {
            "success": False,
            "error": str(e),
            "message": "回归测试表单生成失败"
        }


def analyze_impact_domain(input_path: str) -> Dict[str, Any]:
    """
    分析回归影响域
    
    Args:
        input_path: 输入文档路径
        
    Returns:
        影响域分析结果
    """
    try:
        manager = RegressionTestManager()
        return manager.analyze_regression_impact(input_path)
    except Exception as e:
        logger.error(f"分析影响域失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# 主程序入口
if __name__ == "__main__":
    # 测试代码
    test_input = "E:/test_documents"
    result = generate_regression_forms(
        input_path=test_input,
        test_manager="张三",
        test_personnel="李四", 
        developer="王五",
        domain="航空电子"
    )
    log_info(f"测试结果: {result}", Path(__file__).stem) 