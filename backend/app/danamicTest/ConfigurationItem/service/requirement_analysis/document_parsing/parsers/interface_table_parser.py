"""
接口表格解析器
用于从Word文档的3.3.1章节中提取接口表格数据
"""

from typing import List, Dict, Any, Optional, Tuple
import re
from docx import Document
from docx.table import Table
from .....utils.logging_utils.logger import log_info, log_debug, log_warning, log_error
import os


class InterfaceTableParser:
    """接口表格解析器"""
    
    def __init__(self):
        """初始化接口表格解析器"""
        self.logger_name = "interface_table_parser"
        
        # 接口章节标识符（针对标准化文档优化）
        self.interface_section_patterns = [
            r'3\.3\.1.*接口标识.*接口图',
            r'3\.3\.1.*接口.*标识',
            r'3\.3\.1.*接口说明',
            r'3\.3\.1.*接口.*定义',
            r'3\.3.*接口.*说明',
            r'接口标识.*接口图',
            r'接口标识.{0,5}接口图',  # 🔧 新增：支持"接口标识和接口图"
            r'接口.*标识.*图',
            r'接口说明',
            r'接口.*定义',
            r'接口描述',
            r'接口列表',
            r'CSCI.*外部接口需求',  # 🔧 新增：支持CSCI外部接口需求
            r'外部接口需求'  # 🔧 新增：支持外部接口需求
        ]
        
        # 接口表格的列名映射（精确匹配，避免误判）
        self.column_mapping = {
            '序号': ['序号', '编号', 'No', '号', '项'],
            '接口名称': ['接口名称', '接口名', 'Interface Name', '接口', '功能名称'],  # 移除过于宽泛的'名称'和'Name'
            '接口标识': ['接口标识', '接口ID', 'Interface ID', '接口编号', '标识符'],  # 移除过于宽泛的'标识'和'ID'
            '源': ['源', '来源', '发起方', 'Source', 'From', '源系统', '发送方'],
            '目的地': ['目的地', '目标', '接收方', 'Target', 'To', 'Destination', '目标系统', '接收端'],
            '接口描述': ['接口描述', '功能描述', 'Description', 'Desc', '备注', '详细说明']  # 移除过于宽泛的'描述'和'说明'
        }
    
    def extract_interface_table_from_docx(self, docx_path: str) -> List[Dict[str, Any]]:
        """
        从Word文档中提取接口表格数据
        
        Args:
            docx_path: Word文档路径
            
        Returns:
            接口表格数据列表
        """
        try:
            log_info(f"📄 开始从Word文档提取接口表格: {docx_path}", self.logger_name)
            
            if not os.path.exists(docx_path):
                log_error(f"❌ 文档文件不存在: {docx_path}", self.logger_name)
                return []
            
            doc = Document(docx_path)
            log_info(f"✅ 成功打开文档，段落数: {len(doc.paragraphs)}, 表格数: {len(doc.tables)}", self.logger_name)
            
            # 查找接口章节
            interface_section_found = False
            interface_tables = []
            
            # 遍历文档段落，寻找接口章节
            for i, paragraph in enumerate(doc.paragraphs):
                if self._is_interface_section(paragraph.text):
                    log_info(f"🔍 找到接口章节: {paragraph.text.strip()}", self.logger_name)
                    interface_section_found = True
                    
                    # 在接口章节后查找表格
                    tables = self._find_tables_after_paragraph(doc, i)
                    interface_tables.extend(tables)
                    log_info(f"📊 在接口章节后找到 {len(tables)} 个表格", self.logger_name)
                    break
                else:
                    # 🔧 新增：记录检查的段落
                    if paragraph.text.strip() and ('接口' in paragraph.text or '3.3' in paragraph.text):
                        log_debug(f"检查段落 {i}: '{paragraph.text.strip()}' - 不是接口章节", self.logger_name)
            
            if not interface_section_found:
                log_warning("⚠️ 未找到接口章节，尝试直接查找包含接口信息的表格", self.logger_name)
                # 直接在所有表格中查找接口表格
                for table_idx, table in enumerate(doc.tables):
                    log_debug(f"检查表格 {table_idx + 1}/{len(doc.tables)}", self.logger_name)
                    if self._is_interface_table(table):
                        interface_tables.append(table)
                        log_info(f"✅ 发现接口表格: 表格 {table_idx + 1}", self.logger_name)
                    else:
                        # 🔧 新增：记录为什么表格不被认为是接口表格
                        log_debug(f"   表格 {table_idx + 1} 不是接口表格 - 行数: {len(table.rows)}, 列数: {len(table.columns) if table.rows else 0}", self.logger_name)
                        if table.rows and len(table.rows) > 0:
                            header_row = table.rows[0]
                            header_cells = [cell.text.strip() for cell in header_row.cells[:min(6, len(header_row.cells))]]
                            log_debug(f"   表头内容: {header_cells}", self.logger_name)
            
            # 解析表格数据（只解析第一个有效的接口表格）
            all_interface_data = []
            
            for table_idx, table in enumerate(interface_tables):
                log_info(f"🔍 开始解析接口表格 {table_idx + 1}", self.logger_name)
                
                try:
                    interface_data = self._parse_interface_table(table)
                    log_info(f"📊 表格 {table_idx + 1} 解析完成，提取到 {len(interface_data)} 个接口", self.logger_name)
                    
                    # 🔧 新增：显示解析到的接口详情
                    for i, interface in enumerate(interface_data, 1):
                        log_debug(f"   接口 {i}: {interface.get('接口名称', '未知')} (ID: {interface.get('接口标识', '无')})", self.logger_name)
                    
                    # 🔧 修改：只要找到一个有效的接口表格就停止解析
                    if interface_data:  # 如果成功解析到接口数据
                        all_interface_data.extend(interface_data)
                        log_info(f"✅ 已找到有效接口表格，停止解析其他表格", self.logger_name)
                        break
                    
                except Exception as parse_error:
                    log_error(f"❌ 解析表格 {table_idx + 1} 失败: {parse_error}", self.logger_name)
                    continue
            
            log_info(f"接口表格提取完成，共找到 {len(all_interface_data)} 个接口", self.logger_name)
            return all_interface_data
            
        except Exception as e:
            log_error(f"从Word文档提取接口表格时发生错误: {e}", self.logger_name)
            return []
    
    def _is_interface_section(self, text: str) -> bool:
        """
        判断是否为接口章节
        
        Args:
            text: 段落文本
            
        Returns:
            bool: 是否为接口章节
        """
        text = text.strip()
        if not text:
            return False
        
        for pattern in self.interface_section_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _find_tables_after_paragraph(self, doc: Document, paragraph_index: int) -> List[Table]:
        """
        查找指定段落后的表格（简化版本，确保功能正常）
        
        Args:
            doc: Word文档对象
            paragraph_index: 段落索引
            
        Returns:
            表格列表
        """
        tables = []
        
        try:
            log_debug(f"开始查找段落{paragraph_index}后的表格", self.logger_name)
            
            # 🔧 简化：直接搜索所有表格，找到接口表格
            # 这个方法虽然不够精确，但确保功能正常工作
            for table in doc.tables:
                if self._is_interface_table(table):
                    tables.append(table)
                    log_debug(f"找到接口表格", self.logger_name)
            
            log_debug(f"找到{len(tables)}个接口表格", self.logger_name)
            return tables
            
        except Exception as e:
            log_warning(f"查找表格时发生错误: {e}", self.logger_name)
            return []
    
    def _find_interface_tables_in_document(self, doc: Document) -> List[Table]:
        """
        在文档中查找接口表格
        
        Args:
            doc: Word文档对象
            
        Returns:
            接口表格列表
        """
        interface_tables = []
        
        for table in doc.tables:
            if self._is_interface_table(table):
                interface_tables.append(table)
        
        return interface_tables
    
    def _is_interface_table(self, table: Table) -> bool:
        """
        判断是否为接口表格
        
        Args:
            table: 表格对象
            
        Returns:
            bool: 是否为接口表格
        """
        try:
            if not table.rows:
                log_debug("表格没有行，跳过", self.logger_name)
                return False
            
            # 检查表头是否包含接口相关列名
            header_row = table.rows[0]
            header_texts = [cell.text.strip() for cell in header_row.cells]
            
            log_debug(f"检查表格表头: {header_texts}", self.logger_name)
            
            # 🔧 增强：排除明显不是接口表格的表格
            # 检查是否包含软件信息表格的特征列
            software_info_indicators = ['软件名称', '软件简称', '软件标识号', '版本号', '发布号', '开发单位']
            has_software_info = any(indicator in ' '.join(header_texts) for indicator in software_info_indicators)
            
            if has_software_info:
                log_debug("❌ 检测到软件信息表格特征，跳过", self.logger_name)
                return False
            
            # 检查是否包含其他非接口表格的特征
            non_interface_indicators = ['测试项', '需求', '用例', '问题', '缺陷']
            has_non_interface = any(indicator in ' '.join(header_texts) for indicator in non_interface_indicators)
            
            if has_non_interface:
                log_debug("❌ 检测到非接口表格特征，跳过", self.logger_name)
                return False
            
            # 至少要包含接口名称和接口标识列
            has_interface_name = any(
                any(pattern in header_text for pattern in self.column_mapping['接口名称'])
                for header_text in header_texts
            )
            
            has_interface_id = any(
                any(pattern in header_text for pattern in self.column_mapping['接口标识'])
                for header_text in header_texts
            )
            
            # 🔧 增强：必须同时包含"接口"关键字才认为是接口表格
            has_interface_keyword = any('接口' in header_text for header_text in header_texts)
            
            # 🔧 新增：记录检测结果
            log_debug(f"接口表格检测结果: 接口名称列={has_interface_name}, 接口标识列={has_interface_id}, 包含接口关键字={has_interface_keyword}", self.logger_name)
            
            result = has_interface_name and has_interface_id and has_interface_keyword
            
            if result:
                log_debug("✅ 确认为接口表格", self.logger_name)
            else:
                log_debug("❌ 不是接口表格", self.logger_name)
            
            return result
            
        except Exception as e:
            log_warning(f"判断接口表格时发生错误: {e}", self.logger_name)
            return False
    
    def _get_document_elements_in_order(self, doc: Document) -> List[Dict[str, Any]]:
        """
        获取文档中所有元素的线性顺序（段落和表格混合）
        
        这是解决"表格位置问题"的关键方法！
        Word文档的内部结构是线性的，但python-docx将段落和表格分开访问。
        这个方法重建了元素的真实顺序。
        
        Args:
            doc: Word文档对象
            
        Returns:
            按文档顺序排列的元素列表，每个元素包含type和element信息
        """
        try:
            elements = []
            paragraph_index = 0
            table_index = 0
            
            # 🔧 关键：通过文档的内部XML结构获取真实顺序
            # 遍历文档体中的所有子元素
            for element in doc.element.body:
                # 检查是否是段落元素（使用完整的命名空间匹配）
                if element.tag.endswith('}p'):  # paragraph with namespace
                    if paragraph_index < len(doc.paragraphs):
                        paragraph = doc.paragraphs[paragraph_index]
                        if paragraph.element == element:
                            elements.append({
                                'type': 'paragraph',
                                'element': paragraph
                            })
                        paragraph_index += 1
                
                # 检查是否是表格元素（使用完整的命名空间匹配）
                elif element.tag.endswith('}tbl'):  # table with namespace
                    if table_index < len(doc.tables):
                        table = doc.tables[table_index]
                        if table.element == element:
                            elements.append({
                                'type': 'table',
                                'element': table
                            })
                        table_index += 1
            
            log_debug(f"文档元素线性顺序重建完成，共{len(elements)}个元素 (段落:{paragraph_index}, 表格:{table_index})", self.logger_name)
            return elements
            
        except Exception as e:
            log_warning(f"重建文档元素顺序失败: {e}", self.logger_name)
            import traceback
            log_warning(f"详细错误: {traceback.format_exc()}", self.logger_name)
            return []
    
    def _is_next_section(self, text: str) -> bool:
        """
        判断是否是下一个章节的标题
        
        Args:
            text: 段落文本
            
        Returns:
            bool: 是否是下一个章节
        """
        if not text.strip():
            return False
        
        # 检查是否是章节标题格式（如 3.4, 3.3.2 等）
        section_patterns = [
            r'^\s*3\.[4-9]',  # 3.4及以后的章节
            r'^\s*3\.3\.[2-9]',  # 3.3.2及以后的子章节
            r'^\s*[4-9]\.',  # 第4章及以后
        ]
        
        for pattern in section_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _parse_interface_table(self, table) -> List[Dict[str, Any]]:
        """
        解析接口表格
        
        Args:
            table: 表格对象
            
        Returns:
            接口数据列表
        """
        try:
            interface_data = []
            
            # 获取表格的所有行
            all_rows = []
            
            # 🔧 修复：兼容不同文档库的rows对象
            try:
                # 尝试使用count属性
                if hasattr(table.rows, 'count'):
                    row_count = table.rows.count
                elif hasattr(table.rows, '__len__'):
                    row_count = len(table.rows)
                else:
                    # 如果都不支持，尝试直接遍历
                    row_count = 0
                    for _ in table.rows:
                        row_count += 1
                
                log_debug(f"表格总行数: {row_count}", self.logger_name)
                
                for i in range(row_count):
                    try:
                        row = table.rows[i]
                        all_rows.append(row)
                    except Exception as e:
                        log_warning(f"获取表格第{i+1}行失败: {e}", self.logger_name)
                        continue
                        
            except Exception as e:
                log_error(f"获取表格行数失败: {e}", self.logger_name)
                # 备用方案：直接遍历
                try:
                    for i, row in enumerate(table.rows):
                        all_rows.append(row)
                    log_debug(f"通过遍历获取到{len(all_rows)}行", self.logger_name)
                except Exception as e2:
                    log_error(f"备用方案也失败: {e2}", self.logger_name)
                    return interface_data
            
            if not all_rows:
                log_warning("表格没有有效行", self.logger_name)
                return interface_data
            
            log_debug(f"表格总行数: {len(all_rows)}", self.logger_name)
            
            # 查找表头行
            headers = []
            header_row_index = -1
            
            for i, row in enumerate(all_rows):
                try:
                    cells = []
                    
                    # 🔧 修复：兼容不同文档库的cells对象
                    try:
                        if hasattr(row.cells, 'count'):
                            cell_count = row.cells.count
                        elif hasattr(row.cells, '__len__'):
                            cell_count = len(row.cells)
                        else:
                            # 备用方案：直接遍历计数
                            cell_count = 0
                            for _ in row.cells:
                                cell_count += 1
                        
                        for j in range(cell_count):
                            try:
                                cell_text = row.cells[j].text.strip()
                                cells.append(cell_text)
                            except Exception as e:
                                log_debug(f"获取第{i+1}行第{j+1}列失败: {e}", self.logger_name)
                                cells.append('')
                                
                    except Exception as e:
                        log_warning(f"获取第{i+1}行单元格失败，尝试直接遍历: {e}", self.logger_name)
                        # 备用方案：直接遍历单元格
                        try:
                            for j, cell in enumerate(row.cells):
                                try:
                                    cell_text = cell.text.strip()
                                    cells.append(cell_text)
                                except Exception as e2:
                                    log_debug(f"遍历获取第{i+1}行第{j+1}列失败: {e2}", self.logger_name)
                                    cells.append('')
                        except Exception as e2:
                            log_warning(f"备用方案也失败，跳过第{i+1}行: {e2}", self.logger_name)
                            continue
                    
                    # 检查是否为表头行（包含接口相关的列名）
                    if self._is_interface_table_header(cells):
                        headers = cells
                        header_row_index = i
                        log_debug(f"找到接口表头行（第{i+1}行）: {headers}", self.logger_name)
                        break
                        
                except Exception as e:
                    log_warning(f"解析第{i+1}行时发生错误: {e}", self.logger_name)
                    continue
            
            if not headers:
                log_warning("未找到有效的接口表头", self.logger_name)
                return interface_data
            
            # 🔧 改进：构建更强大的列名映射
            column_mapping = self._build_enhanced_column_mapping(headers)
            log_debug(f"接口表格列名映射: {column_mapping}", self.logger_name)
            
            # 解析数据行（跳过表头行）
            for i in range(header_row_index + 1, len(all_rows)):
                try:
                    row = all_rows[i]
                    cells = []
                    
                    # 获取行中的所有单元格
                    try:
                        if hasattr(row.cells, 'count'):
                            cell_count = row.cells.count
                        elif hasattr(row.cells, '__len__'):
                            cell_count = len(row.cells)
                        else:
                            # 备用方案：直接遍历计数
                            cell_count = 0
                            for _ in row.cells:
                                cell_count += 1
                        
                        for j in range(cell_count):
                            try:
                                cell_text = row.cells[j].text.strip()
                                cells.append(cell_text)
                            except Exception as e:
                                log_debug(f"获取第{i+1}行第{j+1}列失败: {e}", self.logger_name)
                                cells.append('')
                                
                    except Exception as e:
                        log_warning(f"获取第{i+1}行单元格失败，尝试直接遍历: {e}", self.logger_name)
                        # 备用方案：直接遍历单元格
                        try:
                            for j, cell in enumerate(row.cells):
                                try:
                                    cell_text = cell.text.strip()
                                    cells.append(cell_text)
                                except Exception as e2:
                                    log_debug(f"遍历获取第{i+1}行第{j+1}列失败: {e2}", self.logger_name)
                                    cells.append('')
                        except Exception as e2:
                            log_warning(f"备用方案也失败，跳过第{i+1}行: {e2}", self.logger_name)
                            continue
                    
                    log_debug(f"解析第{i+1}行原始数据: {cells}", self.logger_name)
                    
                    # 🔧 改进：确保cell数量与header数量匹配
                    while len(cells) < len(headers):
                        cells.append('')
                    
                    # 构建接口数据字典
                    interface_info = {}
                    for j, header in enumerate(headers):
                        if j < len(cells):
                            # 使用增强的列名映射
                            standard_key = column_mapping.get(header, header)
                            interface_info[standard_key] = cells[j]
                            
                            # 🔧 增加调试：显示每个字段的映射
                            log_debug(f"  列映射: '{header}' -> '{standard_key}' = '{cells[j]}'", self.logger_name)
                    
                    log_debug(f"构建的接口信息: {interface_info}", self.logger_name)
                    
                    # 🔧 改进：更严格的有效性检查
                    if self._is_valid_interface_row_enhanced(interface_info):
                        interface_data.append(interface_info)
                        interface_name = interface_info.get('接口名称', 'Unknown')
                        log_debug(f"✅ 解析接口数据: {interface_name}", self.logger_name)
                    else:
                        log_debug(f"❌ 跳过无效接口行: {i+1}", self.logger_name)
                        
                except Exception as e:
                    log_warning(f"解析接口表格第{i+1}行时发生错误: {e}", self.logger_name)
                    continue
            
            log_info(f"接口表格解析完成，提取到 {len(interface_data)} 个接口", self.logger_name)
            return interface_data
            
        except Exception as e:
            log_error(f"解析接口表格时发生错误: {e}", self.logger_name)
            return []
    
    def _build_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """
        构建列名映射
        
        Args:
            headers: 表头列表
            
        Returns:
            列名映射字典
        """
        mapping = {}
        
        for header in headers:
            # 为每个表头找到对应的标准列名
            best_match = None
            best_match_score = 0
            
            for standard_name, patterns in self.column_mapping.items():
                for pattern in patterns:
                    # 🔧 修改：使用更精确的匹配策略
                    header_lower = header.lower().strip()
                    pattern_lower = pattern.lower().strip()
                    
                    # 完全匹配得分最高
                    if header_lower == pattern_lower:
                        score = 100
                    # 完全包含匹配
                    elif pattern_lower in header_lower or header_lower in pattern_lower:
                        score = 80
                    # 部分匹配
                    elif any(word in header_lower for word in pattern_lower.split()) and len(pattern_lower) > 2:
                        score = 60
                    else:
                        score = 0
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match = standard_name
            
            # 只有匹配度足够高才使用映射
            if best_match and best_match_score >= 60:
                mapping[header] = best_match
                log_debug(f"列名映射: '{header}' -> '{best_match}' (得分: {best_match_score})", self.logger_name)
            else:
                mapping[header] = header
                log_debug(f"列名保持原样: '{header}' (无合适映射)", self.logger_name)
        
        return mapping
    
    def _is_valid_interface_row(self, interface_info: Dict[str, Any]) -> bool:
        """
        检查接口行数据是否有效
        
        Args:
            interface_info: 接口信息字典
            
        Returns:
            bool: 是否为有效的接口行
        """
        # 至少要有接口名称或接口标识
        interface_name = interface_info.get('接口名称', '').strip()
        interface_id = interface_info.get('接口标识', '').strip()
        
        return bool(interface_name or interface_id)
    
    def _build_enhanced_column_mapping(self, headers: List[str]) -> Dict[str, str]:
        """
        构建增强的列名映射
        
        Args:
            headers: 表头列表
            
        Returns:
            增强的列名映射字典
        """
        mapping = {}
        
        for header in headers:
            # 为每个表头找到对应的标准列名
            best_match = None
            best_match_score = 0
            
            for standard_name, patterns in self.column_mapping.items():
                for pattern in patterns:
                    # 使用更精确的匹配策略
                    header_lower = header.lower().strip()
                    pattern_lower = pattern.lower().strip()
                    
                    # 完全匹配得分最高
                    if header_lower == pattern_lower:
                        score = 100
                    # 完全包含匹配
                    elif pattern_lower in header_lower or header_lower in pattern_lower:
                        score = 80
                    # 部分匹配
                    elif any(word in header_lower for word in pattern_lower.split()) and len(pattern_lower) > 2:
                        score = 60
                    else:
                        score = 0
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match = standard_name
            
            # 只有匹配度足够高才使用映射
            if best_match and best_match_score >= 60:
                mapping[header] = best_match
                log_debug(f"列名映射: '{header}' -> '{best_match}' (得分: {best_match_score})", self.logger_name)
            else:
                mapping[header] = header
                log_debug(f"列名保持原样: '{header}' (无合适映射)", self.logger_name)
        
        return mapping
    
    def _is_interface_table_header(self, cells: List[str]) -> bool:
        """
        检查是否为接口表格的表头行
        
        Args:
            cells: 单元格文本列表
            
        Returns:
            是否为接口表头
        """
        try:
            # 检查是否包含接口相关的关键列名
            header_texts = [cell.lower().strip() for cell in cells if cell.strip()]
            
            # 必须包含接口名称相关的列
            has_interface_name = any(
                any(pattern.lower() in header_text for pattern in self.column_mapping['接口名称'])
                for header_text in header_texts
            )
            
            # 必须包含接口标识相关的列
            has_interface_id = any(
                any(pattern.lower() in header_text for pattern in self.column_mapping['接口标识'])
                for header_text in header_texts
            )
            
            # 或者包含接口描述相关的列
            has_interface_desc = any(
                any(pattern.lower() in header_text for pattern in self.column_mapping['接口描述'])
                for header_text in header_texts
            )
            
            result = has_interface_name and (has_interface_id or has_interface_desc)
            
            if result:
                log_debug(f"识别为接口表头: 接口名称={has_interface_name}, 接口标识={has_interface_id}, 接口描述={has_interface_desc}", self.logger_name)
            
            return result
            
        except Exception as e:
            log_warning(f"检查接口表头时发生错误: {e}", self.logger_name)
            return False
    
    def _is_valid_interface_row_enhanced(self, interface_info: Dict[str, Any]) -> bool:
        """
        增强的接口行有效性检查
        
        Args:
            interface_info: 接口信息字典
            
        Returns:
            是否为有效的接口行
        """
        try:
            # 接口名称不能为空
            interface_name = interface_info.get('接口名称', '').strip()
            if not interface_name:
                log_debug("无效接口行: 缺少接口名称", self.logger_name)
                return False
            
            # 过滤明显的表头重复行
            if any(keyword in interface_name.lower() for keyword in ['序号', '接口名称', '接口标识', '名称', '标识']):
                log_debug(f"无效接口行: 疑似表头重复行 '{interface_name}'", self.logger_name)
                return False
            
            # 接口名称长度检查
            if len(interface_name) < 2:
                log_debug(f"无效接口行: 接口名称过短 '{interface_name}'", self.logger_name)
                return False
            
            log_debug(f"有效接口行: '{interface_name}'", self.logger_name)
            return True
            
        except Exception as e:
            log_warning(f"检查接口行有效性时发生错误: {e}", self.logger_name)
            return False
    
    def extract_interface_table_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        从纯文本中提取接口表格数据（备用方法）
        
        Args:
            text: 文本内容
            
        Returns:
            接口数据列表
        """
        try:
            log_info("尝试从纯文本提取接口表格数据", self.logger_name)
            
            # 查找接口章节
            lines = text.split('\n')
            interface_section_start = -1
            
            for i, line in enumerate(lines):
                if self._is_interface_section(line):
                    interface_section_start = i
                    break
            
            if interface_section_start == -1:
                log_warning("在文本中未找到接口章节", self.logger_name)
                return []
            
            # 简化的表格解析逻辑
            # 这里可以根据实际的文本格式进行更精确的解析
            interface_data = []
            
            # 查找表格数据行
            for i in range(interface_section_start + 1, len(lines)):
                line = lines[i].strip()
                if not line:
                    continue
                
                # 尝试解析表格行（假设使用制表符或多个空格分隔）
                parts = re.split(r'\t+|\s{2,}', line)
                if len(parts) >= 3:  # 至少包含序号、接口名称、接口标识
                    interface_info = {
                        '序号': parts[0] if len(parts) > 0 else '',
                        '接口名称': parts[1] if len(parts) > 1 else '',
                        '接口标识': parts[2] if len(parts) > 2 else '',
                        '源': parts[3] if len(parts) > 3 else '',
                        '目的地': parts[4] if len(parts) > 4 else '',
                        '接口描述': parts[5] if len(parts) > 5 else ''
                    }
                    
                    if self._is_valid_interface_row(interface_info):
                        interface_data.append(interface_info)
            
            log_info(f"从文本提取接口数据完成，共 {len(interface_data)} 个接口", self.logger_name)
            return interface_data
            
        except Exception as e:
            log_error(f"从文本提取接口表格时发生错误: {e}", self.logger_name)
            return [] 