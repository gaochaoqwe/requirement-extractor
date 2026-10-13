"""
基于tree-sitter的精确代码差异分析工具
负责使用tree-sitter精确分析新旧版本代码之间的差异
"""
import os
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, Counter

# 导入tree-sitter相关模块
from app.codeReview.Regression.service.ai.parser import extract_functions_from_code
from app.codeReview.Regression.service.ai import log_debug
from app.codeReview.Regression.db.repository.file_repo import FileRepository
import re
import hashlib


class TreeSitterDiffAnalyzer:
    """基于tree-sitter的代码差异分析器"""
    
    def __init__(self, db):
        """
        初始化代码差异分析器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.file_repo = FileRepository(db)
    
    def get_single_file_diff(
        self, 
        extract_path: str, 
        file_path: str
    ) -> Dict[str, Any]:
        """
        获取单个文件的精确差异信息
        
        Args:
            extract_path: 解压路径
            file_path: 文件相对路径
            
        Returns:
            Dict[str, Any]: 文件差异信息
        """
        log_debug(f"[TreeSitterDiffAnalyzer] ==========================================")
        log_debug(f"[TreeSitterDiffAnalyzer] 开始分析文件差异: {file_path}")
        log_debug(f"[TreeSitterDiffAnalyzer] 这是新旧版本对比分析")
        log_debug(f"[TreeSitterDiffAnalyzer] ==========================================")
        
        # 获取新旧版本的文件路径
        old_file_path, new_file_path = self._get_version_file_paths(extract_path, file_path)
        
        log_debug(f"[TreeSitterDiffAnalyzer] 路径映射结果:")
        log_debug(f"  - 旧版本文件: {old_file_path}")
        log_debug(f"  - 新版本文件: {new_file_path}")
        
        # 检查文件是否存在
        old_exists = os.path.exists(old_file_path)
        new_exists = os.path.exists(new_file_path)
        
        log_debug(f"[TreeSitterDiffAnalyzer] 文件存在性检查:")
        log_debug(f"  - 旧版本存在: {old_exists}")
        log_debug(f"  - 新版本存在: {new_exists}")
        
        if not old_exists and not new_exists:
            log_debug(f"[WARNING] 文件的新旧版本都不存在: {file_path}")
            log_debug(f"[TreeSitterDiffAnalyzer] 跳过该文件")
            return None
        
        # 分析文件差异
        log_debug(f"[TreeSitterDiffAnalyzer] 开始调用tree-sitter差异分析...")
        diff_info = self._analyze_file_diff_with_tree_sitter(
            old_file_path if old_exists else None,
            new_file_path if new_exists else None,
            file_path
        )
        
        # 输出分析结果摘要
        if diff_info and diff_info.get("functions"):
            total_functions = len(diff_info["functions"])
            changed_functions = sum(1 for func in diff_info["functions"] if func.get("change_type") != "unchanged")
            log_debug(f"[TreeSitterDiffAnalyzer] 分析完成: 总函数数={total_functions}, 有变更={changed_functions}")
        else:
            log_debug(f"[TreeSitterDiffAnalyzer] 分析完成: 无函数或无变更")
        
        log_debug(f"[TreeSitterDiffAnalyzer] ==========================================")
        
        return diff_info
    
    def get_all_file_diffs(self, extract_path: str) -> Dict[str, Any]:
        """
        获取所有文件的差异信息
        
        Args:
            extract_path: 解压路径
            
        Returns:
            Dict[str, Any]: 所有文件的差异信息
        """
        log_debug(f"[TreeSitterDiffAnalyzer] ========================================")
        log_debug(f"[TreeSitterDiffAnalyzer] 开始批量分析文件差异")
        log_debug(f"[TreeSitterDiffAnalyzer] 解压路径: {extract_path}")
        log_debug(f"[TreeSitterDiffAnalyzer] ========================================")
        
        file_diffs = {}
        
        # 获取新旧版本目录
        old_version_dir, new_version_dir = self._get_version_directories(extract_path)
        
        if not old_version_dir or not new_version_dir:
            log_debug(f"[ERROR] 无法找到版本目录")
            return file_diffs
        
        log_debug(f"[TreeSitterDiffAnalyzer] 版本目录确认:")
        log_debug(f"  - 旧版本: {old_version_dir}")
        log_debug(f"  - 新版本: {new_version_dir}")
        
        # 获取所有源代码文件
        source_files = self._find_all_source_files(old_version_dir, new_version_dir)
        
        log_debug(f"[TreeSitterDiffAnalyzer] 找到 {len(source_files)} 个源代码文件需要分析")
        
        # 统计信息
        total_files = len(source_files)
        processed_files = 0
        files_with_changes = 0
        total_function_changes = 0
        
        for relative_path in sorted(source_files):
            processed_files += 1
            log_debug(f"[TreeSitterDiffAnalyzer] 处理进度: {processed_files}/{total_files} - {relative_path}")
            
            diff_info = self.get_single_file_diff(extract_path, relative_path)
            
            if diff_info and diff_info.get("functions"):
                # 只保留有变更的文件
                changed_functions = [
                    func for func in diff_info["functions"] 
                    if func.get("change_type") != "unchanged"
                ]
                
                if changed_functions:
                    file_diffs[relative_path] = diff_info
                    files_with_changes += 1
                    total_function_changes += len(changed_functions)
                    
                    log_debug(f"[TreeSitterDiffAnalyzer] ✓ 文件有变更: {relative_path} ({len(changed_functions)} 个函数)")
                else:
                    log_debug(f"[TreeSitterDiffAnalyzer] - 文件无变更: {relative_path}")
            else:
                log_debug(f"[TreeSitterDiffAnalyzer] - 文件无函数或分析失败: {relative_path}")
        
        # 输出最终统计
        log_debug(f"[TreeSitterDiffAnalyzer] ========================================")
        log_debug(f"[TreeSitterDiffAnalyzer] 批量分析完成统计:")
        log_debug(f"  - 总文件数: {total_files}")
        log_debug(f"  - 已处理文件数: {processed_files}")
        log_debug(f"  - 有变更的文件数: {files_with_changes}")
        log_debug(f"  - 总函数变更数: {total_function_changes}")
        log_debug(f"[TreeSitterDiffAnalyzer] ========================================")
        
        return file_diffs
    
    def _find_project_root_directories(self, extract_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        智能识别项目根目录
        通过分析文件结构相似性来确定真正的项目根目录
        
        Args:
            extract_path: 解压路径
            
        Returns:
            Tuple[Optional[str], Optional[str]]: 旧版本和新版本的项目根目录
        """
        log_debug(f"[TreeSitterDiffAnalyzer] ======== 开始智能识别项目根目录 ========")
        log_debug(f"[TreeSitterDiffAnalyzer] 解压路径: {extract_path}")
        
        # 第一步：收集所有可能的版本目录
        version_candidates = self._collect_version_candidates(extract_path)
        
        if len(version_candidates) < 2:
            log_debug(f"[ERROR] 找到的版本目录候选少于2个: {version_candidates}")
            return None, None
        
        log_debug(f"[TreeSitterDiffAnalyzer] 版本目录候选: {version_candidates}")
        
        # 第二步：分析每个候选目录的文件结构
        candidate_structures = {}
        for candidate in version_candidates:
            candidate_path = os.path.join(extract_path, candidate)
            structure = self._analyze_directory_structure(candidate_path)
            candidate_structures[candidate] = structure
            log_debug(f"[TreeSitterDiffAnalyzer] 候选 {candidate} 的文件结构: {len(structure['files'])} 个文件, {len(structure['dirs'])} 个目录")
        
        # 第三步：找到最相似的两个版本目录
        best_pair = self._find_most_similar_directories(candidate_structures)
        
        if not best_pair:
            log_debug(f"[ERROR] 无法找到相似的版本目录对")
            return None, None
        
        old_version, new_version = best_pair
        log_debug(f"[TreeSitterDiffAnalyzer] ✓ 识别到最佳版本对: {old_version} <-> {new_version}")
        
        # 第四步：确定项目根目录
        old_root = self._find_project_root_in_version(os.path.join(extract_path, old_version))
        new_root = self._find_project_root_in_version(os.path.join(extract_path, new_version))
        
        log_debug(f"[TreeSitterDiffAnalyzer] 项目根目录识别结果:")
        log_debug(f"  - 旧版本根目录: {old_root}")
        log_debug(f"  - 新版本根目录: {new_root}")
        log_debug(f"[TreeSitterDiffAnalyzer] ======== 根目录识别完成 ========")
        
        return old_root, new_root
    
    def _collect_version_candidates(self, extract_path: str) -> List[str]:
        """
        收集所有可能的版本目录候选
        
        Args:
            extract_path: 解压路径
            
        Returns:
            List[str]: 版本目录候选列表
        """
        candidates = []
        
        try:
            for item in os.listdir(extract_path):
                item_path = os.path.join(extract_path, item)
                if os.path.isdir(item_path):
                    # 检查是否像版本目录
                    if self._looks_like_version_directory(item):
                        candidates.append(item)
                        log_debug(f"[TreeSitterDiffAnalyzer] 发现版本目录候选: {item}")
        except Exception as e:
            log_debug(f"[ERROR] 扫描版本目录候选时出错: {e}")
        
        # 按版本号排序
        candidates.sort(key=self._version_sort_key)
        return candidates
    
    def _looks_like_version_directory(self, dirname: str) -> bool:
        """
        判断目录名是否像版本目录
        
        Args:
            dirname: 目录名
            
        Returns:
            bool: 是否像版本目录
        """
        dirname_lower = dirname.lower()
        
        # 常见的版本目录模式
        version_patterns = [
            'v1.', 'v2.', 'v3.', 'v4.', 'v5.',  # v1.00, v2.01等
            'version', 'ver',  # version1, ver2等
            'old', 'new',  # old, new
            'before', 'after',  # before, after
            'src', 'source',  # src1, source2等
        ]
        
        # 检查是否匹配任何模式
        for pattern in version_patterns:
            if pattern in dirname_lower:
                return True
        
        # 检查是否包含数字（可能是版本号）
        if any(char.isdigit() for char in dirname):
            return True
        
        return False
    
    def _version_sort_key(self, version_name: str) -> tuple:
        """
        版本名称排序键
        
        Args:
            version_name: 版本名称
            
        Returns:
            tuple: 排序键
        """
        # 提取数字部分用于排序
        import re
        numbers = re.findall(r'\d+', version_name)
        if numbers:
            return tuple(int(num) for num in numbers)
        else:
            return (0,)
    
    def _analyze_directory_structure(self, directory: str) -> Dict[str, Any]:
        """
        分析目录结构
        
        Args:
            directory: 目录路径
            
        Returns:
            Dict[str, Any]: 目录结构信息
        """
        structure = {
            'files': set(),
            'dirs': set(),
            'source_files': set(),
            'normalized_source_files': set(),  # 新增：规范化的源文件路径
            'total_files': 0,
            'total_dirs': 0
        }
        
        source_extensions = {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.java', '.py'}
        
        try:
            for root, dirs, files in os.walk(directory):
                # 计算相对路径
                rel_root = os.path.relpath(root, directory)
                if rel_root == '.':
                    rel_root = ''
                
                # 记录目录
                for dir_name in dirs:
                    if rel_root:
                        dir_path = f"{rel_root}/{dir_name}"
                    else:
                        dir_path = dir_name
                    structure['dirs'].add(dir_path)
                    structure['total_dirs'] += 1
                
                # 记录文件
                for file_name in files:
                    if rel_root:
                        file_path = f"{rel_root}/{file_name}"
                    else:
                        file_path = file_name
                    
                    structure['files'].add(file_path)
                    structure['total_files'] += 1
                    
                    # 检查是否是源代码文件
                    _, ext = os.path.splitext(file_name)
                    if ext.lower() in source_extensions:
                        structure['source_files'].add(file_path)
                        
                        # 规范化源文件路径（移除版本目录前缀）
                        normalized_path = self._normalize_file_path(file_path)
                        structure['normalized_source_files'].add(normalized_path)
        
        except Exception as e:
            log_debug(f"[ERROR] 分析目录结构时出错: {e}")
        
        return structure
    
    def _normalize_file_path(self, file_path: str) -> str:
        """
        规范化文件路径，移除版本目录前缀
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            str: 规范化后的文件路径
        """
        path_parts = file_path.split('/')
        
        # 如果路径以版本目录开头，移除版本目录前缀
        if len(path_parts) > 1:
            first_part = path_parts[0]
            # 检查第一部分是否是版本目录
            if self._looks_like_version_directory(first_part):
                # 移除版本目录前缀
                return '/'.join(path_parts[1:])
        
        return file_path
    
    def _find_most_similar_directories(self, structures: Dict[str, Dict[str, Any]]) -> Optional[Tuple[str, str]]:
        """
        找到最相似的两个目录
        
        Args:
            structures: 目录结构字典
            
        Returns:
            Optional[Tuple[str, str]]: 最相似的目录对
        """
        candidates = list(structures.keys())
        if len(candidates) < 2:
            return None
        
        best_pair = None
        best_similarity = 0
        
        # 比较所有可能的目录对
        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                dir1, dir2 = candidates[i], candidates[j]
                similarity = self._calculate_directory_similarity(
                    structures[dir1], structures[dir2]
                )
                
                log_debug(f"[TreeSitterDiffAnalyzer] 目录相似性: {dir1} <-> {dir2} = {similarity:.3f}")
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_pair = (dir1, dir2)
        
        log_debug(f"[TreeSitterDiffAnalyzer] 最佳相似性: {best_similarity:.3f}")
        
        # 只有相似性足够高才认为是有效的版本对
        if best_similarity >= 0.3:  # 至少30%的相似性
            return best_pair
        else:
            log_debug(f"[WARNING] 最佳相似性太低 ({best_similarity:.3f})，可能不是有效的版本对")
            return best_pair  # 即使相似性不高，也返回最佳选择
    
    def _calculate_directory_similarity(self, struct1: Dict[str, Any], struct2: Dict[str, Any]) -> float:
        """
        计算两个目录结构的相似性
        
        Args:
            struct1: 第一个目录结构
            struct2: 第二个目录结构
            
        Returns:
            float: 相似性分数 (0-1)
        """
        # 优先使用规范化的源文件进行相似性计算
        source1 = struct1.get('normalized_source_files', struct1['source_files'])
        source2 = struct2.get('normalized_source_files', struct2['source_files'])
        
        if not source1 and not source2:
            source_similarity = 1.0
        elif not source1 or not source2:
            source_similarity = 0.0
        else:
            common_source = source1 & source2
            total_source = source1 | source2
            source_similarity = len(common_source) / len(total_source)
        
        # 计算文件相似性（使用原始路径）
        files1 = struct1['files']
        files2 = struct2['files']
        
        if not files1 and not files2:
            files_similarity = 1.0
        elif not files1 or not files2:
            files_similarity = 0.0
        else:
            common_files = files1 & files2
            total_files = files1 | files2
            files_similarity = len(common_files) / len(total_files)
        
        # 计算目录相似性
        dirs1 = struct1['dirs']
        dirs2 = struct2['dirs']
        
        if not dirs1 and not dirs2:
            dirs_similarity = 1.0
        elif not dirs1 or not dirs2:
            dirs_similarity = 0.0
        else:
            common_dirs = dirs1 & dirs2
            total_dirs = dirs1 | dirs2
            dirs_similarity = len(common_dirs) / len(total_dirs)
        
        # 加权平均相似性
        # 规范化源代码文件相似性权重最高，因为这是最重要的指标
        total_similarity = (
            source_similarity * 0.7 +  # 规范化源代码文件权重70%
            files_similarity * 0.2 +   # 所有文件权重20%
            dirs_similarity * 0.1      # 目录结构权重10%
        )
        
        log_debug(f"[TreeSitterDiffAnalyzer] 相似性详情: 源文件={source_similarity:.3f}, 文件={files_similarity:.3f}, 目录={dirs_similarity:.3f}, 总计={total_similarity:.3f}")
        
        return total_similarity
    
    def _find_project_root_in_version(self, version_dir: str) -> Optional[str]:
        """
        在版本目录中找到项目根目录
        
        Args:
            version_dir: 版本目录路径
            
        Returns:
            Optional[str]: 项目根目录路径
        """
        log_debug(f"[TreeSitterDiffAnalyzer] 在版本目录中寻找项目根: {version_dir}")
        
        # 如果版本目录直接包含源代码文件，则它就是根目录
        if self._directory_contains_source_files(version_dir):
            log_debug(f"[TreeSitterDiffAnalyzer] 版本目录直接包含源代码，作为根目录: {version_dir}")
            return version_dir
        
        # 否则，查找子目录中的项目根
        subdirs = []
        try:
            for item in os.listdir(version_dir):
                item_path = os.path.join(version_dir, item)
                if os.path.isdir(item_path):
                    subdirs.append(item_path)
        except Exception as e:
            log_debug(f"[ERROR] 列出版本目录内容时出错: {e}")
            return version_dir
        
        # 寻找包含最多源代码文件的子目录
        best_subdir = None
        max_source_files = 0
        
        for subdir in subdirs:
            source_count = self._count_source_files(subdir)
            log_debug(f"[TreeSitterDiffAnalyzer] 子目录 {subdir} 包含 {source_count} 个源代码文件")
            
            if source_count > max_source_files:
                max_source_files = source_count
                best_subdir = subdir
        
        if best_subdir and max_source_files > 0:
            log_debug(f"[TreeSitterDiffAnalyzer] 选择包含最多源代码文件的子目录作为根: {best_subdir}")
            return best_subdir
        else:
            log_debug(f"[TreeSitterDiffAnalyzer] 未找到合适的子目录，使用版本目录作为根: {version_dir}")
            return version_dir
    
    def _directory_contains_source_files(self, directory: str) -> bool:
        """
        检查目录是否直接包含源代码文件
        
        Args:
            directory: 目录路径
            
        Returns:
            bool: 是否包含源代码文件
        """
        source_extensions = {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.java', '.py'}
        
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    _, ext = os.path.splitext(item)
                    if ext.lower() in source_extensions:
                        return True
        except Exception:
            pass
        
        return False
    
    def _count_source_files(self, directory: str) -> int:
        """
        计算目录及其子目录中的源代码文件数量
        
        Args:
            directory: 目录路径
            
        Returns:
            int: 源代码文件数量
        """
        source_extensions = {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.java', '.py'}
        count = 0
        
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext.lower() in source_extensions:
                        count += 1
        except Exception:
            pass
        
        return count
    
    def _get_version_directories(self, extract_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        获取版本目录路径（使用智能识别）
        
        Args:
            extract_path: 解压路径
            
        Returns:
            Tuple[Optional[str], Optional[str]]: 旧版本和新版本目录路径
        """
        log_debug(f"[TreeSitterDiffAnalyzer] 开始获取版本目录: {extract_path}")
        
        # 首先尝试智能识别
        old_root, new_root = self._find_project_root_directories(extract_path)
        
        if old_root and new_root:
            log_debug(f"[TreeSitterDiffAnalyzer] ✓ 智能识别成功")
            return old_root, new_root
        
        # 如果智能识别失败，回退到传统方法
        log_debug(f"[TreeSitterDiffAnalyzer] 智能识别失败，回退到传统方法")
        return self._get_version_directories_fallback(extract_path)
    
    def _get_version_directories_fallback(self, extract_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        传统的版本目录获取方法（作为回退）
        
        Args:
            extract_path: 解压路径
            
        Returns:
            Tuple[Optional[str], Optional[str]]: 旧版本和新版本目录路径
        """
        # 首先列出所有子目录
        subdirs = []
        try:
            for item in os.listdir(extract_path):
                item_path = os.path.join(extract_path, item)
                if os.path.isdir(item_path):
                    subdirs.append(item)
            log_debug(f"[TreeSitterDiffAnalyzer] 发现子目录: {subdirs}")
        except Exception as e:
            log_debug(f"[ERROR] 无法列出目录内容: {e}")
            return None, None
        
        # 尝试多种版本目录命名方式
        version_patterns = [
            ("v1.00", "v1.01"),
            ("v1.0", "v1.1"),
            ("version1", "version2"),
            ("old", "new"),
            ("before", "after")
        ]
        
        for old_pattern, new_pattern in version_patterns:
            old_dir = os.path.join(extract_path, old_pattern)
            new_dir = os.path.join(extract_path, new_pattern)
            
            if os.path.exists(old_dir) and os.path.exists(new_dir):
                log_debug(f"[TreeSitterDiffAnalyzer] ✓ 找到版本目录: {old_pattern} -> {new_pattern}")
                return old_dir, new_dir
        
        # 如果没有找到标准模式，尝试自动推断
        if len(subdirs) >= 2:
            # 按名称排序，假设前面的是旧版本
            subdirs.sort()
            old_dir = os.path.join(extract_path, subdirs[0])
            new_dir = os.path.join(extract_path, subdirs[1])
            
            log_debug(f"[TreeSitterDiffAnalyzer] 自动推断版本目录: {subdirs[0]} -> {subdirs[1]}")
            return old_dir, new_dir
        
        log_debug(f"[ERROR] 无法确定版本目录")
        return None, None
    
    def _get_version_file_paths(self, extract_path: str, file_path: str) -> Tuple[str, str]:
        """
        获取新旧版本的文件路径
        
        Args:
            extract_path: 解压路径
            file_path: 文件相对路径（不包含版本目录前缀）
            
        Returns:
            Tuple[str, str]: 旧版本和新版本的文件路径
        """
        old_version_dir, new_version_dir = self._get_version_directories(extract_path)
        
        if not old_version_dir or not new_version_dir:
            # 回退到默认方式
            old_version_dir = os.path.join(extract_path, "v1.00")
            new_version_dir = os.path.join(extract_path, "v1.01")
        
        # 构建完整文件路径 - file_path已经是相对路径，直接拼接即可
        old_file_path = os.path.join(old_version_dir, file_path)
        new_file_path = os.path.join(new_version_dir, file_path)
        
        return old_file_path, new_file_path
    
    def _find_all_source_files(self, old_dir: str, new_dir: str) -> Set[str]:
        """
        查找所有源代码文件
        
        Args:
            old_dir: 旧版本目录
            new_dir: 新版本目录
            
        Returns:
            Set[str]: 相对路径的源代码文件集合（不包含版本目录前缀）
        """
        source_extensions = {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.java', '.py'}
        
        log_debug(f"[TreeSitterDiffAnalyzer] 开始扫描源文件...")
        log_debug(f"[TreeSitterDiffAnalyzer] 旧版本目录: {old_dir}")
        log_debug(f"[TreeSitterDiffAnalyzer] 新版本目录: {new_dir}")
        
        # 统计文件数量
        old_files = set()
        new_files = set()
        
        # 从旧版本目录获取文件
        if os.path.exists(old_dir):
            for root, _, files in os.walk(old_dir):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext.lower() in source_extensions:
                        # 获取相对于旧版本目录的相对路径
                        relative_path = os.path.relpath(os.path.join(root, file), old_dir)
                        # 规范化路径分隔符
                        relative_path = relative_path.replace('\\', '/')
                        
                        # 处理嵌套版本目录的情况（如 v1.00/v1.00/calculator.cpp）
                        # 移除开头的版本目录前缀
                        path_parts = relative_path.split('/')
                        if len(path_parts) > 1 and path_parts[0] in ['v1.00', 'v1.01', 'version1', 'version2', 'old', 'new']:
                            # 移除版本目录前缀，保留实际的文件路径
                            relative_path = '/'.join(path_parts[1:])
                        
                        old_files.add(relative_path)
        
        # 从新版本目录获取文件
        if os.path.exists(new_dir):
            for root, _, files in os.walk(new_dir):
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext.lower() in source_extensions:
                        # 获取相对于新版本目录的相对路径
                        relative_path = os.path.relpath(os.path.join(root, file), new_dir)
                        # 规范化路径分隔符
                        relative_path = relative_path.replace('\\', '/')
                        
                        # 处理嵌套版本目录的情况（如 v1.01/v1.01/calculator.cpp）
                        # 移除开头的版本目录前缀
                        path_parts = relative_path.split('/')
                        if len(path_parts) > 1 and path_parts[0] in ['v1.00', 'v1.01', 'version1', 'version2', 'old', 'new']:
                            # 移除版本目录前缀，保留实际的文件路径
                            relative_path = '/'.join(path_parts[1:])
                        
                        new_files.add(relative_path)
        
        # 合并所有文件（这些是需要进行版本对比的文件）
        all_files = old_files | new_files
        
        # 统计和分类文件
        only_in_old = old_files - new_files
        only_in_new = new_files - old_files
        in_both = old_files & new_files
        
        log_debug(f"[TreeSitterDiffAnalyzer] 文件统计:")
        log_debug(f"  - 旧版本文件数: {len(old_files)}")
        log_debug(f"  - 新版本文件数: {len(new_files)}")
        log_debug(f"  - 需要对比的文件数: {len(all_files)}")
        log_debug(f"  - 仅在旧版本: {len(only_in_old)} 个")
        log_debug(f"  - 仅在新版本: {len(only_in_new)} 个")
        log_debug(f"  - 两版本都有: {len(in_both)} 个")
        
        # 详细列出文件分类
        if only_in_old:
            log_debug(f"[TreeSitterDiffAnalyzer] 仅在旧版本的文件: {list(only_in_old)}")
        if only_in_new:
            log_debug(f"[TreeSitterDiffAnalyzer] 仅在新版本的文件: {list(only_in_new)}")
        if in_both:
            log_debug(f"[TreeSitterDiffAnalyzer] 两版本都有的文件: {list(in_both)}")
        
        log_debug(f"[TreeSitterDiffAnalyzer] 需要对比的文件列表: {sorted(all_files)}")
        return all_files
    
    def _analyze_file_diff_with_tree_sitter(
        self, 
        old_file_path: Optional[str], 
        new_file_path: Optional[str],
        relative_path: str
    ) -> Dict[str, Any]:
        """
        使用tree-sitter分析文件差异
        
        Args:
            old_file_path: 旧版本文件路径（可能为None）
            new_file_path: 新版本文件路径（可能为None）
            relative_path: 文件相对路径
            
        Returns:
            Dict[str, Any]: 文件差异信息
        """
        log_debug(f"[TreeSitterDiffAnalyzer] === 开始分析文件差异 ===")
        log_debug(f"[TreeSitterDiffAnalyzer] 文件: {relative_path}")
        log_debug(f"[TreeSitterDiffAnalyzer] 旧版本路径: {old_file_path}")
        log_debug(f"[TreeSitterDiffAnalyzer] 新版本路径: {new_file_path}")
        
        diff_info = {
            "file_path": relative_path,
            "file_type": self._get_file_type(new_file_path or old_file_path),
            "functions": []
        }
        
        # 确定文件状态
        old_exists = old_file_path and os.path.exists(old_file_path)
        new_exists = new_file_path and os.path.exists(new_file_path)
        
        log_debug(f"[TreeSitterDiffAnalyzer] 文件存在性: 旧版本={old_exists}, 新版本={new_exists}")
        
        if old_exists and new_exists:
            file_status = "modified_or_unchanged"
        elif old_exists:
            file_status = "deleted"
        elif new_exists:
            file_status = "added"
        else:
            file_status = "not_found"
            log_debug(f"[WARNING] 文件不存在于任何版本: {relative_path}")
            return diff_info
        
        log_debug(f"[TreeSitterDiffAnalyzer] 文件状态: {file_status}")
        
        # 读取文件内容
        old_content = ""
        new_content = ""
        
        if old_exists:
            old_content = self._read_file_content(old_file_path)
            log_debug(f"[TreeSitterDiffAnalyzer] 旧版本内容长度: {len(old_content)} 字符")
        
        if new_exists:
            new_content = self._read_file_content(new_file_path)
            log_debug(f"[TreeSitterDiffAnalyzer] 新版本内容长度: {len(new_content)} 字符")
        
        # 使用tree-sitter提取函数
        old_functions = {}
        new_functions = {}
        
        if old_content:
            try:
                language = self._get_language_for_file(old_file_path)
                log_debug(f"[TreeSitterDiffAnalyzer] 旧版本使用语言: {language}")
                old_func_list = extract_functions_from_code(old_content, language)
                old_functions = {func["function_name"]: func for func in old_func_list}
                log_debug(f"[TreeSitterDiffAnalyzer] ✓ 旧版本提取到 {len(old_functions)} 个函数: {list(old_functions.keys())}")
            except Exception as e:
                log_debug(f"[ERROR] tree-sitter提取旧版本函数失败: {e}")
        
        if new_content:
            try:
                language = self._get_language_for_file(new_file_path)
                log_debug(f"[TreeSitterDiffAnalyzer] 新版本使用语言: {language}")
                new_func_list = extract_functions_from_code(new_content, language)
                new_functions = {func["function_name"]: func for func in new_func_list}
                log_debug(f"[TreeSitterDiffAnalyzer] ✓ 新版本提取到 {len(new_functions)} 个函数: {list(new_functions.keys())}")
            except Exception as e:
                log_debug(f"[ERROR] tree-sitter提取新版本函数失败: {e}")
        
        # 分析函数差异
        all_function_names = set(old_functions.keys()) | set(new_functions.keys())
        log_debug(f"[TreeSitterDiffAnalyzer] 总共需要分析 {len(all_function_names)} 个函数")
        
        # 统计变更类型
        change_stats = {"added": 0, "deleted": 0, "modified": 0, "unchanged": 0}
        
        for func_name in all_function_names:
            old_func = old_functions.get(func_name)
            new_func = new_functions.get(func_name)
            
            # 确定变更类型 - 使用改进的比较逻辑
            if old_func and new_func:
                # 使用智能比较方法判断是否有实质性变更
                if self._is_function_substantially_changed(old_func["source_code"], new_func["source_code"]):
                    change_type = "modified"
                    # 记录详细的相似性信息
                    similarity = self._calculate_code_similarity(old_func["source_code"], new_func["source_code"])
                    log_debug(f"[TreeSitterDiffAnalyzer] 函数 {func_name} 被识别为修改 (相似性: {similarity:.3f})")
                else:
                    change_type = "unchanged"
                    log_debug(f"[TreeSitterDiffAnalyzer] 函数 {func_name} 被识别为未变更 (相似性高)")
            elif old_func:
                change_type = "deleted"
            else:
                change_type = "added"
            
            change_stats[change_type] += 1
            
            # 构建函数差异信息
            func_diff = {
                "function_name": func_name,
                "change_type": change_type,
                "old_code": old_func["source_code"] if old_func else "",
                "new_code": new_func["source_code"] if new_func else "",
                "old_start_line": old_func["start_line"] if old_func else 0,
                "old_end_line": old_func["end_line"] if old_func else 0,
                "new_start_line": new_func["start_line"] if new_func else 0,
                "new_end_line": new_func["end_line"] if new_func else 0
            }
            
            # 如果是修改的函数，添加相似性信息用于调试
            if change_type == "modified":
                similarity = self._calculate_code_similarity(old_func["source_code"], new_func["source_code"])
                func_diff["similarity_score"] = similarity
            
            diff_info["functions"].append(func_diff)
            
            # 详细记录有变更的函数
            if change_type != "unchanged":
                log_debug(f"[TreeSitterDiffAnalyzer] 函数变更: {func_name} -> {change_type}")
        
        # 输出统计信息
        log_debug(f"[TreeSitterDiffAnalyzer] 函数变更统计: {change_stats}")
        log_debug(f"[TreeSitterDiffAnalyzer] === 文件差异分析完成 ===")
        
        return diff_info
    
    def _read_file_content(self, file_path: str) -> str:
        """
        读取文件内容，自动处理编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容
        """
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                log_debug(f"[ERROR] 读取文件时出错: {e}")
                break
        
        # 如果所有编码都失败，尝试使用chardet检测编码
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                return raw_data.decode(encoding)
        except ImportError:
            log_debug("未安装chardet库，无法自动检测文件编码")
        except Exception as e:
            log_debug(f"使用chardet检测编码时出错: {e}")
        
        # 最后的回退方案
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            log_debug(f"[ERROR] 无法读取文件: {file_path}, {e}")
            return ""
    
    def _get_file_type(self, file_path: str) -> str:
        """
        获取文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件类型
        """
        if not file_path:
            return 'unknown'
            
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext in ['.c', '.h']:
            return 'c'
        elif ext in ['.cpp', '.hpp', '.cc', '.cxx']:
            return 'cpp'
        elif ext in ['.java']:
            return 'java'
        elif ext in ['.py']:
            return 'python'
        elif ext in ['.js']:
            return 'javascript'
        else:
            return 'unknown'
    
    def _get_language_for_file(self, file_path: str) -> str:
        """
        根据文件路径获取tree-sitter语言标识
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 语言标识
        """
        file_type = self._get_file_type(file_path)
        
        if file_type in ['c']:
            return 'c'
        elif file_type in ['cpp']:
            return 'cpp'
        else:
            return 'c'  # 默认使用C语言解析器 

    def _normalize_code_for_comparison(self, code: str) -> str:
        """
        规范化代码用于比较，移除格式差异但保留逻辑结构
        
        Args:
            code: 原始代码
            
        Returns:
            str: 规范化后的代码
        """
        if not code:
            return ""
        
        # 1. 移除注释（保留重要的逻辑注释，但移除纯格式注释）
        # 移除单行注释
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        # 移除多行注释
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # 2. 规范化空白字符
        # 将多个连续空格替换为单个空格
        code = re.sub(r' +', ' ', code)
        # 将多个连续换行替换为单个换行
        code = re.sub(r'\n+', '\n', code)
        # 移除行首行尾空白
        lines = [line.strip() for line in code.split('\n')]
        code = '\n'.join(line for line in lines if line)
        
        # 3. 规范化大括号格式
        # 确保大括号前后的空格一致
        code = re.sub(r'\s*{\s*', ' {\n', code)
        code = re.sub(r'\s*}\s*', '\n}\n', code)
        
        # 4. 规范化分号和逗号后的空格
        code = re.sub(r';\s*', ';\n', code)
        code = re.sub(r',\s*', ', ', code)
        
        # 5. 规范化操作符周围的空格
        code = re.sub(r'\s*([+\-*/=<>!&|]+)\s*', r' \1 ', code)
        
        # 6. 最终清理
        code = re.sub(r'\n+', '\n', code)
        code = code.strip()
        
        return code
    
    def _calculate_code_similarity(self, old_code: str, new_code: str) -> float:
        """
        计算两段代码的相似性
        
        Args:
            old_code: 旧版本代码
            new_code: 新版本代码
            
        Returns:
            float: 相似性分数 (0.0-1.0)
        """
        if not old_code and not new_code:
            return 1.0
        if not old_code or not new_code:
            return 0.0
        
        # 规范化代码
        normalized_old = self._normalize_code_for_comparison(old_code)
        normalized_new = self._normalize_code_for_comparison(new_code)
        
        # 如果规范化后完全相同，则相似性为1.0
        if normalized_old == normalized_new:
            return 1.0
        
        # 计算基于行的相似性
        old_lines = set(normalized_old.split('\n'))
        new_lines = set(normalized_new.split('\n'))
        
        if not old_lines and not new_lines:
            return 1.0
        if not old_lines or not new_lines:
            return 0.0
        
        common_lines = old_lines & new_lines
        total_lines = old_lines | new_lines
        
        line_similarity = len(common_lines) / len(total_lines)
        
        # 计算基于字符的相似性
        char_similarity = self._calculate_string_similarity(normalized_old, normalized_new)
        
        # 综合相似性（行相似性权重更高，因为它更能反映逻辑结构）
        overall_similarity = line_similarity * 0.7 + char_similarity * 0.3
        
        return overall_similarity
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        计算两个字符串的相似性（使用编辑距离）
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            
        Returns:
            float: 相似性分数 (0.0-1.0)
        """
        if str1 == str2:
            return 1.0
        
        len1, len2 = len(str1), len(str2)
        if len1 == 0:
            return 0.0 if len2 > 0 else 1.0
        if len2 == 0:
            return 0.0
        
        # 简化的编辑距离计算（为了性能，只计算前1000个字符）
        max_len = 1000
        s1 = str1[:max_len]
        s2 = str2[:max_len]
        
        # 使用动态规划计算编辑距离
        dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
        
        for i in range(len(s1) + 1):
            dp[i][0] = i
        for j in range(len(s2) + 1):
            dp[0][j] = j
        
        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
        
        edit_distance = dp[len(s1)][len(s2)]
        max_len = max(len(s1), len(s2))
        
        similarity = 1.0 - (edit_distance / max_len)
        return max(0.0, similarity)
    
    def _is_function_substantially_changed(self, old_code: str, new_code: str, similarity_threshold: float = 0.85) -> bool:
        """
        判断函数是否有实质性变更
        
        Args:
            old_code: 旧版本代码
            new_code: 新版本代码
            similarity_threshold: 相似性阈值，超过此值认为没有实质性变更
            
        Returns:
            bool: 是否有实质性变更
        """
        if not old_code and not new_code:
            return False  # 都为空，没有变更
        if not old_code or not new_code:
            return True   # 一个为空一个不为空，有变更
        
        # 计算代码相似性
        similarity = self._calculate_code_similarity(old_code, new_code)
        
        log_debug(f"[TreeSitterDiffAnalyzer] 代码相似性: {similarity:.3f} (阈值: {similarity_threshold})")
        
        # 如果相似性高于阈值，认为没有实质性变更
        return similarity < similarity_threshold 