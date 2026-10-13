"""
代码行数统计模块
使用lizard库进行代码复杂度和行数分析
"""

import os
import zipfile
import shutil
import tempfile
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import lizard

logger = logging.getLogger(__name__)

class CodeStatistics:
    """代码统计分析类"""
    
    def __init__(self):
        # 支持的代码文件扩展名
        self.supported_extensions = {
            '.py', '.c', '.cpp', '.cc', '.cxx', '.c++',
            '.h', '.hpp', '.hxx', '.h++', '.java',
            '.js', '.ts', '.go', '.cs', '.php',
            '.rb', '.swift', '.kt', '.rs', '.scala',
            '.m', '.mm', '.f', '.f90', '.f95'
        }
    
    def extract_uploaded_file(self, file_path: str, extract_to: str) -> str:
        """
        解压上传的代码文件
        
        Args:
            file_path: 上传的文件路径
            extract_to: 解压目标目录
            
        Returns:
            解压后的目录路径
        """
        try:
            # 确保目标目录存在
            os.makedirs(extract_to, exist_ok=True)
            
            # 判断文件类型并解压
            if file_path.endswith('.zip'):
                try:
                    # 尝试使用UTF-8编码
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_to)
                except UnicodeDecodeError:
                    # 如果UTF-8失败，尝试使用GB2312/GBK编码
                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            # 手动处理中文文件名
                            for member in zip_ref.infolist():
                                try:
                                    member.filename = member.filename.encode('cp437').decode('gbk')
                                except:
                                    try:
                                        member.filename = member.filename.encode('cp437').decode('utf-8')
                                    except:
                                        pass  # 保持原文件名
                                zip_ref.extract(member, extract_to)
                    except Exception as e:
                        # 最后尝试直接解压，忽略文件名编码问题
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_to)
                logger.info(f"成功解压zip文件到: {extract_to}")
            else:
                # 如果是单个文件，直接复制
                filename = os.path.basename(file_path)
                shutil.copy2(file_path, os.path.join(extract_to, filename))
                logger.info(f"成功复制单个文件到: {extract_to}")
            
            return extract_to
            
        except Exception as e:
            logger.error(f"文件解压失败: {str(e)}")
            raise Exception(f"文件解压失败: {str(e)}")
    
    def get_code_files(self, directory: str) -> List[str]:
        """
        获取目录下所有代码文件
        
        Args:
            directory: 目录路径
            
        Returns:
            代码文件路径列表
        """
        code_files = []
        
        for root, dirs, files in os.walk(directory):
            # 跳过常见的非代码目录
            dirs[:] = [d for d in dirs if d not in {
                '.git', '.svn', '__pycache__', 'node_modules', 
                '.idea', '.vscode', 'build', 'dist', 'target'
            }]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                if file_ext in self.supported_extensions:
                    code_files.append(file_path)
        
        logger.info(f"找到 {len(code_files)} 个代码文件")
        return code_files
    
    def analyze_with_lizard(self, directory: str) -> Dict[str, Any]:
        """
        使用lizard分析代码
        
        Args:
            directory: 代码目录路径
            
        Returns:
            分析结果字典
        """
        try:
            # 获取代码文件列表
            code_files = self.get_code_files(directory)
            
            if not code_files:
                return {
                    'total_lines': 0,
                    'total_files': 0,
                    'languages': {},
                    'complexity_info': {},
                    'error': '未找到支持的代码文件'
                }
            
            # 使用lizard分析
            analysis_result = lizard.analyze(
                code_files,
                exclude_pattern=None
            )
            
            # 统计结果
            total_lines = 0
            total_files = len(code_files)
            languages = {}
            functions_info = []
            
            # 处理lizard分析结果
            if hasattr(analysis_result, 'function_list'):
                function_list = analysis_result.function_list
            else:
                # 如果是generator/map对象，需要转换为列表
                function_list = list(analysis_result) if analysis_result else []
            
            # 按文件统计
            for file_info in function_list:
                total_lines += file_info.nloc
                
                # 按语言分类
                file_ext = Path(file_info.filename).suffix.lower()
                if file_ext not in languages:
                    languages[file_ext] = {
                        'files': 0,
                        'lines': 0,
                        'functions': 0
                    }
                
                languages[file_ext]['lines'] += file_info.nloc
                languages[file_ext]['functions'] += 1
            
            # 按文件统计文件数量
            file_extensions = [Path(f).suffix.lower() for f in code_files]
            for ext in file_extensions:
                if ext in languages:
                    languages[ext]['files'] = file_extensions.count(ext)
                else:
                    languages[ext] = {'files': file_extensions.count(ext), 'lines': 0, 'functions': 0}
            
            # 复杂度统计
            complexity_info = {
                'average_complexity': getattr(analysis_result, 'average_CCN', 0),
                'total_functions': len(function_list),
                'high_complexity_functions': len([f for f in function_list if getattr(f, 'cyclomatic_complexity', getattr(f, 'ccn', 0)) > 10])
            }
            
            result = {
                'total_lines': total_lines,
                'total_files': total_files,
                'languages': languages,
                'complexity_info': complexity_info,
                'analysis_success': True
            }
            
            logger.info(f"Lizard分析完成: {total_lines} 行代码, {total_files} 个文件")
            return result
            
        except Exception as e:
            logger.error(f"Lizard分析失败: {str(e)}")
            return {
                'total_lines': 0,
                'total_files': 0,
                'languages': {},
                'complexity_info': {},
                'analysis_success': False,
                'error': str(e)
            }
    
    def simple_line_count(self, directory: str) -> Dict[str, Any]:
        """
        简单的行数统计（备用方案）
        
        Args:
            directory: 代码目录路径
            
        Returns:
            统计结果字典
        """
        try:
            code_files = self.get_code_files(directory)
            
            if not code_files:
                return {
                    'total_lines': 0,
                    'total_files': 0,
                    'languages': {},
                    'method': 'simple_count',
                    'error': '未找到支持的代码文件'
                }
            
            total_lines = 0
            languages = {}
            
            for file_path in code_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len([line for line in f if line.strip()])  # 只统计非空行
                        total_lines += lines
                        
                        # 按语言分类
                        file_ext = Path(file_path).suffix.lower()
                        if file_ext not in languages:
                            languages[file_ext] = {'files': 0, 'lines': 0}
                        
                        languages[file_ext]['files'] += 1
                        languages[file_ext]['lines'] += lines
                        
                except Exception as e:
                    logger.warning(f"读取文件失败 {file_path}: {str(e)}")
                    continue
            
            result = {
                'total_lines': total_lines,
                'total_files': len(code_files),
                'languages': languages,
                'method': 'simple_count',
                'analysis_success': True
            }
            
            logger.info(f"简单统计完成: {total_lines} 行代码, {len(code_files)} 个文件")
            return result
            
        except Exception as e:
            logger.error(f"简单统计失败: {str(e)}")
            return {
                'total_lines': 0,
                'total_files': 0,
                'languages': {},
                'method': 'simple_count',
                'analysis_success': False,
                'error': str(e)
            }
    
    def analyze_code(self, file_path: str, task_id: str, upload_dir: str) -> Dict[str, Any]:
        """
        分析上传的代码文件
        
        Args:
            file_path: 上传的文件路径
            task_id: 任务ID
            upload_dir: 上传目录基路径
            
        Returns:
            分析结果字典
        """
        extract_dir = None
        try:
            # 创建任务专用目录
            task_dir = os.path.join(upload_dir, task_id)
            extract_dir = os.path.join(task_dir, 'extracted_code')
            
            # 解压文件
            self.extract_uploaded_file(file_path, extract_dir)
            
            # 尝试使用lizard分析
            result = self.analyze_with_lizard(extract_dir)
            
            # 如果lizard失败，使用简单统计
            if not result.get('analysis_success', False):
                logger.warning("Lizard分析失败，使用简单统计方案")
                result = self.simple_line_count(extract_dir)
            
            # 添加额外信息
            result['task_id'] = task_id
            result['extract_dir'] = extract_dir
            result['original_file'] = file_path
            
            return result
            
        except Exception as e:
            logger.error(f"代码分析失败: {str(e)}")
            return {
                'total_lines': 0,
                'total_files': 0,
                'languages': {},
                'analysis_success': False,
                'error': str(e),
                'task_id': task_id
            }
    
    def cleanup_extracted_files(self, extract_dir: str):
        """
        清理解压的临时文件
        
        Args:
            extract_dir: 解压目录路径
        """
        try:
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
                logger.info(f"已清理临时文件: {extract_dir}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {str(e)}")


# 便捷函数
def analyze_code_statistics(file_path: str, task_id: str, upload_dir: str) -> Dict[str, Any]:
    """
    便捷的代码统计分析函数
    
    Args:
        file_path: 上传的文件路径
        task_id: 任务ID
        upload_dir: 上传目录基路径
        
    Returns:
        分析结果字典
    """
    analyzer = CodeStatistics()
    return analyzer.analyze_code(file_path, task_id, upload_dir)


def test_with_small_project(test_dir: str) -> Dict[str, Any]:
    """
    使用small_test项目测试统计功能
    
    Args:
        test_dir: 测试项目目录路径
        
    Returns:
        测试结果
    """
    analyzer = CodeStatistics()
    
    # 使用lizard分析
    lizard_result = analyzer.analyze_with_lizard(test_dir)
    
    # 使用简单统计
    simple_result = analyzer.simple_line_count(test_dir)
    
    return {
        'lizard_analysis': lizard_result,
        'simple_analysis': simple_result,
        'test_directory': test_dir
    } 