
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置项测试表单生成主程序

功能说明：
1. 无策划表情况：直接从需求文档生成完整表单套件
2. 有策划表情况：基于已有策划表生成表单

使用方法：
    通过API调用或直接实例化ConfigurationTestManager类
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import shutil
from datetime import datetime


# 添加当前模块到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入资源管理器和日志系统
try:
    from .resources.resource_manager import get_resource_manager
    from .utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    from .utils.logging_utils.performance_monitor import monitor_step, ConfigurationTestSteps
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from app.danamicTest.ConfigurationItem.resources.resource_manager import get_resource_manager
    from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    from app.danamicTest.ConfigurationItem.utils.logging_utils.performance_monitor import monitor_step, ConfigurationTestSteps

# 导入已重构的service模块
try:
    # 尝试相对导入
    from .service.form_builder import (
        ConfigurationItemFormBuilderService
    )

    from .resources.resource_manager import ResourceManager, get_resource_manager
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from app.danamicTest.ConfigurationItem.service.form_builder import (
        ConfigurationItemFormBuilderService
    )

    from app.danamicTest.ConfigurationItem.resources.resource_manager import ResourceManager, get_resource_manager
    from app.danamicTest.ConfigurationItem.service.form_builder.form_utils import extract_chapter_number

# 工具函数
def find_person_in_array(arr, name):
    """
    从二维数组中找出包含指定名称的子数组
    
    Args:
        arr: 二维数组，例如[['任玉武', '光电系统一部'], ['李英杰', '光电系统二部']]
        name: 要查找的名称
        
    Returns:
        包含该名称的子数组，如果未找到则返回None
    """
    for subarr in arr:
        if name in subarr:
            return subarr
    return None

def copy_excel_files(source_folder, destination_folder):
    """
    复制文件夹中的Excel文件到目标文件夹
    
    Args:
        source_folder: 源文件夹路径
        destination_folder: 目标文件夹路径
    """
    # 确保目标文件夹存在，如果不存在则创建
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # 遍历源文件夹中的文件
    for file_name in os.listdir(source_folder):
        # 检查文件扩展名是否为 ".xlsx"
        if file_name.endswith('.xlsx'):
            source_file_path = os.path.join(source_folder, file_name)
            destination_file_path = os.path.join(destination_folder, file_name)
            # 复制文件
            shutil.copy2(source_file_path, destination_file_path)
            log_info(f"文件 '{file_name}' 已复制到 '{destination_folder}'", Path(__file__).stem)

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
form_builder_service = ConfigurationItemFormBuilderService()

# 为了向后兼容，创建函数别名
def ceshibiaodan_tianchong(*args, **kwargs):
    """配置项测试表单填充"""
    return form_builder_service.ceshibiaodan_tianchong(*args, **kwargs)

def check_word_document_xuqiushuoming(*args, **kwargs):
    """检查需求规格说明文档"""
    return form_builder_service.check_word_document_xuqiushuoming(*args, **kwargs)



# 日志功能已迁移到自定义日志系统

class ConfigurationTestManager:
    """配置项测试管理器 - 基于已验证的hanshutiqu_kaifa模块"""
    
    def __init__(self):
        self.session_data = {}
        self.progress_data = {}
        # 初始化资源管理器
        self.resource_manager = get_resource_manager()
        
        # 验证资源文件
        is_valid, missing = self.resource_manager.validate_resources()
        if not is_valid:
            # log_warning(f"缺失资源文件: {missing}", "config_manager")
            pass
        else:
            # log_info("所有资源文件验证通过", "config_manager")
            pass
        
    def generate_complete_forms(self, session_id: str, basic_info: Dict[str, Any], 
                               ai_analysis: bool = True, deep_analysis: bool = True, task_id: str = None, 
                               progress_callback: callable = None) -> Dict[str, Any]:
        """
        生成完整的配置项测试表单套件
        
        根据上传的文件类型自动选择处理方式：
        1. 如果有策划表文档 -> 调用有策划表的处理流程
        2. 如果只有需求文档(+可选目录文档) -> 调用无策划表的处理流程
        
        Args:
            session_id: 会话ID
            basic_info: 基本信息字典
            ai_analysis: 是否启用AI分析
            deep_analysis: 是否启用深度分析
            task_id: 任务ID
            progress_callback: 进度回调函数
            
        Returns:
            生成结果字典
        """
        try:
            # log_info("开始生成配置项测试表单套件", "config_manager")
            
            if progress_callback:
                progress_callback(5, "正在验证会话目录...")
            
            # 获取文件路径
            # 修复路径指向backend目录下的uploads
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent
            session_dir = backend_dir / "uploads" / "dynamic" / "configuration" / session_id
            if not session_dir.exists():
                # log_error(f"会话目录不存在: {session_dir}", "config_manager")
                raise FileNotFoundError(f"会话目录不存在: {session_dir}")
            
            # log_info(f"会话目录验证通过: {session_dir}", "config_manager")
            
            if progress_callback:
                progress_callback(10, "正在查找需求文档...")
            
            # 查找已上传的文件
            requirement_file = self._find_file_by_prefix(session_dir, "requirement_")
            catalog_file = self._find_file_by_prefix(session_dir, "catalog_")
            
            if not requirement_file:
                # log_error("未找到需求文档", "config_manager")
                raise FileNotFoundError("未找到需求文档")
            
            # log_info(f"需求文档路径: {requirement_file}", "config_manager")
            
            if progress_callback:
                progress_callback(15, "正在准备表单生成...")
            
            # 使用无策划表的处理流程
            # 注意：目录文档是可选的，ceshibiaodan_tianchong会自动处理
            if catalog_file:
                # log_info(f"目录文档路径: {catalog_file}", "config_manager")
                pass
            # log_info("使用无策划表的处理流程", "config_manager")
            return self._generate_without_planning(
                str(session_dir), basic_info, ai_analysis, deep_analysis, task_id, progress_callback
            )
                
        except Exception as e:
            # log_error(f"表单生成失败", "config_manager", e)
            raise
    
    def _prepare_catalog_document(self, session_dir: str, catalog_file: Path) -> Path:
        """
        准备目录文档，如果是确认的目录文本文件，则转换为docx格式
        
        Args:
            session_dir: 会话目录
            catalog_file: 目录文件路径
            
        Returns:
            处理后的目录文档路径
        """
        if catalog_file.suffix == '.txt' and catalog_file.name == 'catalog_confirmed.txt':
            # 这是用户确认的目录文本文件，需要转换为docx格式
            try:
                from docx import Document as DocxDocument
                
                # 读取目录文本内容
                with open(catalog_file, 'r', encoding='utf-8') as f:
                    catalog_content = f.read()
                
                # 创建新的docx文档
                doc = DocxDocument()
                doc.add_heading('需求目录', 0)
                
                # 将目录内容按行添加到文档中
                for line in catalog_content.split('\n'):
                    if line.strip():
                        doc.add_paragraph(line)
                
                # 保存为docx文件
                catalog_docx_path = Path(session_dir) / "catalog_from_confirmed.docx"
                doc.save(str(catalog_docx_path))
                
                # log_info(f"已将确认的目录转换为docx文档: {catalog_docx_path}", "form_generator")
                return catalog_docx_path
                
            except Exception as e:
                # log_warning(f"转换目录文件失败，将使用原文件: {e}", "form_generator")
                return catalog_file
        else:
            # 直接返回原文件
            return catalog_file

    def _find_file_by_prefix(self, directory: Path, prefix: str) -> Optional[Path]:
        """根据前缀查找文件"""
        for file in directory.iterdir():
            if file.is_file() and file.name.startswith(prefix):
                return file
        return None
    
    def _prepare_resources(self, session_dir: str) -> str:
        """
        准备资源文件到会话目录
        
        Args:
            session_dir: 会话目录路径
            
        Returns:
            准备好的资源目录路径
        """
        session_path = Path(session_dir)
        resources_dir = session_path / "resources"
        
        # 创建资源目录
        resources_dir.mkdir(exist_ok=True)
        
        # 复制必要的资源文件到会话目录
        try:
            # 只复制需求分析表模板文件到输出目录
            # log_info(f"复制需求分析表模板: {self.resource_manager.get_template_path('需求分析表(精准测试工具生成).xlsx')}", "config_manager")
            
            # 创建输出目录结构
            output_dir = os.path.join(session_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # 复制模板文件到输出目录
            shutil.copy2(
                self.resource_manager.get_template_path('需求分析表(精准测试工具生成).xlsx'),
                os.path.join(output_dir, '需求分析表(精准测试工具生成).xlsx')
            )
            
        except Exception as e:
            # log_warning(f"复制资源文件时出错: {e}", "config_manager")
            pass
        
        return str(resources_dir)
    

    def _generate_without_planning(self, session_dir: str, basic_info: Dict[str, Any], 
                                  ai_analysis: bool, deep_analysis: bool, task_id: str = None, 
                                  progress_callback: callable = None) -> Dict[str, Any]:
        """
        情景2：无策划表的表单生成
        调用原始项目中的 ceshibiaodan_tianchong 函数
        """
        try:
            # log_info("开始无策划表的表单生成", "form_generator")
            
            if progress_callback:
                progress_callback(20, "正在准备资源文件...")
            
            # 准备资源文件
            # log_info("准备资源文件", "form_generator")
            self._prepare_resources(session_dir)
            
            if progress_callback:
                progress_callback(25, "正在查找需求文档...")
            
            # 查找需求规格说明文档和需求目录文档
            session_path = Path(session_dir)
            requirement_file = self._find_file_by_prefix(session_path, "requirement_")
            
            if not requirement_file:
                # log_error("未找到需求规格说明文档", "form_generator")
                raise FileNotFoundError("未找到需求规格说明文档")
                
            if progress_callback:
                progress_callback(30, "正在处理目录文档...")
                
            # 优先查找确认后的目录文件，如果没有则查找上传的目录文档
            catalog_confirmed_file = session_path / "catalog_confirmed.txt"
            catalog_uploaded_file = self._find_file_by_prefix(session_path, "catalog_")
            
            if catalog_confirmed_file.exists():
                # 使用用户确认的目录文件
                catalog_file = catalog_confirmed_file
                # log_info("使用用户确认的目录文件", "form_generator")
            elif catalog_uploaded_file:
                # 使用上传的目录文档
                catalog_file = catalog_uploaded_file  
                # log_info("使用上传的目录文档", "form_generator")
            else:
                # 如果都没有，使用需求规格说明文档作为默认
                # log_warning("未找到目录文件，将使用需求规格说明文档", "form_generator")
                catalog_file = requirement_file
            
            # log_info(f"需求文档路径: {requirement_file}", "form_generator")
            # log_info(f"原始目录文档路径: {catalog_file}", "form_generator")
            
            if progress_callback:
                progress_callback(35, "正在准备目录文档...")
            
            # 准备目录文档（如果需要转换格式）
            prepared_catalog_file = self._prepare_catalog_document(session_dir, catalog_file)
            # log_info(f"处理后的目录文档路径: {prepared_catalog_file}", "form_generator")
            
            if progress_callback:
                progress_callback(40, "正在准备基本信息...")
            
            # 准备开发人员信息（原始函数需要的格式）
            developer_info = [basic_info.get('developer', ''), basic_info.get('development_department', '')]  # 格式: [姓名, 研制部门]
            
            # 准备可选信息列表（用于填充项目基本信息表）
            optional_info_list = [
                basic_info.get('aircraft_model', ''),        # 飞机型号
                basic_info.get('software_id', ''),           # 软件项目代号
                basic_info.get('domain', ''),                # 所属领域
                basic_info.get('project_director', ''),      # 项目总师
                basic_info.get('development_department', ''), # 研制部门
                basic_info.get('chief_designer', '')         # 主任设计师
            ]
            
            # 准备用户软件信息
            user_software_info = {
                'software_name': basic_info.get('software_name', ''),
                'software_version': basic_info.get('software_version', ''),
                'software_id': basic_info.get('software_id', ''),
                'domain': basic_info.get('domain', '通用领域'),
                'product_type': basic_info.get('product_type', ''),
                # 添加可选信息
                'aircraft_model': basic_info.get('aircraft_model', ''),
                'project_director': basic_info.get('project_director', ''),
                'development_department': basic_info.get('development_department', ''),
                'chief_designer': basic_info.get('chief_designer', '')
            }
            # log_debug(f"🔍 [MAIN DEBUG] basic_info中的development_department: '{basic_info.get('development_department', '')}'", "form_generator")
            # log_debug(f"🔍 [MAIN DEBUG] user_software_info中的development_department: '{user_software_info['development_department']}'", "form_generator")
            # log_info(f"传递用户软件信息到表单生成函数: {user_software_info}", "form_generator")
            
            # 从session_dir路径中提取session_id
            session_id_for_cache = Path(session_dir).name
            
            if progress_callback:
                progress_callback(45, "正在开始表单生成...")
            
            # 调用修改后的表单生成函数
            result = ceshibiaodan_tianchong(
                file_path_xuqiu_word=str(requirement_file),          # 需求规格说明文档路径
                file_path_mulu_word=str(prepared_catalog_file),      # 需求目录文档路径
                zhuguan_name=basic_info.get('test_manager', ''),     # 主管姓名
                ceshiren_name=basic_info.get('test_personnel', ''),  # 测试人员
                kaifarenxinxi=developer_info,                        # 开发人员信息
                ceshileixing='配置项测试',                             # 测试类型
                AI_fenx_flag_Anniu=ai_analysis,         # AI分析标志
                AI_deep_fenx_flag_Anniu=deep_analysis,  # 深度分析标志
                suoshulingyu=basic_info.get('domain', '通用领域'),    # 所属领域
                jianceyi_flag=basic_info.get('detector_flag', '无检测仪'),  # 检测仪标志
                resource_manager=self.resource_manager,
                user_software_info=user_software_info,               # 用户提供的软件信息
                code_lines=basic_info.get('code_lines'),            # 代码行数
                session_id=session_id_for_cache,                    # 🚀 新增：会话ID用于位置缓存
                task_id=task_id,                                     # 🚀 新增：任务ID
                progress_callback=progress_callback                  # 🚀 新增：进度回调
            )
            
            if progress_callback:
                progress_callback(85, "正在收集生成的文件...")
            
            if result == 1:
                # 生成成功，收集生成的文件
                generated_files = self._collect_generated_files(session_dir)
                
                # log_info(f"无策划表的表单生成成功，共生成 {len(generated_files)} 个文件", "form_generator")
                
                if progress_callback:
                    progress_callback(95, "表单生成完成，正在整理结果...")
                
                return {
                    'success': True,
                    'generated_files': generated_files,
                    'output_directory': session_dir
                }
            else:
                raise Exception("表单生成函数返回失败状态")
                
        except Exception as e:
            # log_error(f"无策划表的表单生成失败", "form_generator", e)
            raise
    
    def _collect_generated_files(self, session_dir: str) -> List[str]:
        """收集生成的文件"""
        generated_files = []
        session_path = Path(session_dir)
        
        # 确保output目录存在
        output_dir = session_path / "output"
        output_dir.mkdir(exist_ok=True)
        
        # 检查session目录下的文件，只收集需求分析表
        for file in session_path.iterdir():
            if (file.is_file() and 
                file.suffix in ['.xlsx', '.docx'] and 
                not file.name.startswith(('requirement_', 'planning_', 'catalog_')) and
                '需求分析表' in file.name):
                # 移动到output目录
                try:
                    dest_path = output_dir / file.name
                    if not dest_path.exists():
                        shutil.move(str(file), str(dest_path))
                        generated_files.append(file.name)
                        log_info(f"移动文件到output目录: {file.name}", "file_collector")
                except Exception as e:
                    log_warning(f"移动文件失败 {file.name}: {e}", "file_collector")
        
        # 检查output子目录中已存在的文件，只收集需求分析表
        for file in output_dir.iterdir():
            if (file.is_file() and file.suffix in ['.xlsx', '.docx'] and 
                '需求分析表' in file.name):
                if file.name not in generated_files:
                    generated_files.append(file.name)
        
        # 检查output目录中的文件
        output_path = session_path / "output"
        if output_path.exists():
            # 记录文件修改时间，找到最新生成的文件
            current_time = time.time()
            
            for file in output_path.iterdir():
                if (file.is_file() and 
                    file.suffix in ['.xlsx', '.docx'] and
                    '需求分析表' in file.name):
                    
                    # 检查文件修改时间，只收集最近5分钟内修改的文件
                    file_mtime = file.stat().st_mtime
                    if current_time - file_mtime < 300:  # 5分钟 = 300秒
                        # 文件已经在output目录中
                        if file.name not in generated_files:
                            generated_files.append(file.name)
                            log_info(f"发现最新生成的文件: {file.name}", "file_collector")
        
        return generated_files
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """获取资源文件摘要信息"""
        return self.resource_manager.get_resource_summary()


def main():
    """主函数，用于测试"""
    manager = ConfigurationTestManager()
    
    # 测试数据
    test_session_id = "test-session-123"
    test_basic_info = {
        'test_manager': '张三',
        'test_personnel': '李四',
        'developer': '王五',
        'software_name': '测试软件',
        'software_version': '1.0.0',
        'domain': '通用领域',
        'detector_flag': '有检测仪'
    }
    
    try:
        result = manager.generate_complete_forms(
            test_session_id, 
            test_basic_info, 
            ai_analysis=True, 
            deep_analysis=True
        )
        log_info(f"生成结果: {result}", Path(__file__).stem)
    except Exception as e:
        log_info(f"生成失败: {e}", Path(__file__).stem)


if __name__ == "__main__":
    main() 