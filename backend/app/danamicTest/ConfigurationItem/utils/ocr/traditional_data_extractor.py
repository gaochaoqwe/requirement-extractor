#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传统算法数据提取器
使用正则表达式和字符串匹配替代AI进行OCR数据提取
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.ConfigurationItem.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


class TraditionalDataExtractor:
    """基于传统算法的数据提取器"""
    
    def __init__(self):
        """初始化传统数据提取器"""
        log_info("正在初始化传统数据提取器...", Path(__file__).stem)
        self.config = self._load_config()
        
        # 定义字段提取规则
        self._init_extraction_rules()
        log_info("传统数据提取器初始化完成", Path(__file__).stem)
    
    def _load_config(self):
        """加载部门-领域-测试人员映射配置"""
        try:
            config_path = Path(__file__).parent / "domain_mapping_config.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            log_info("成功加载部门-领域映射配置", Path(__file__).stem)
            return config
        except Exception as e:
            log_error(f"加载配置文件失败: {str(e)}", Path(__file__).stem)
            # 返回默认配置
            return {
                "department_to_domain": {
                    "图像部": "光电领域",
                    "光电部": "光电领域", 
                    "激光部": "光电领域",
                    "光电系统一部": "光电领域",
                    "光电系统二部": "光电领域",
                    "光电系统三部": "光电领域",
                    "光电系统四部": "光电领域",
                    "瞄准显示部": "显示领域",
                    "总体部": "火控领域",
                    "重点实验室": "火控领域",
                    "武控部": "外挂领域"
                },
                "domain_personnel": {
                    "光电领域": {"test_manager": "李玲子", "test_personnel": "王凯旋(外协)"},
                    "显示领域": {"test_manager": "牛婷婷", "test_personnel": "李岩岩(外协)"},
                    "火控领域": {"test_manager": "李佳真", "test_personnel": "王刚(外协)"},
                    "外挂领域": {"test_manager": "武慧莹", "test_personnel": "王星(外协)"}
                }
            }
    
    def _init_extraction_rules(self):
        """初始化字段提取规则"""
        # 字段提取的正则表达式规则
        self.field_patterns = {
            # 申请人：支持多种格式（映射到开发人员）
            'developer': [
                r'申请人[：:=]\s*([^，,\n\r]+)',  # 支持冒号和等号
                r'申请\^[：:=]\s*([^，,\n\r]+)',  # OCR错误：申请^ -> 申请人
                r'申请A[：:=]\s*([^，,\n\r]+)',   # OCR错误：申请A -> 申请人
            ],
            
            # 申请部门：最关键的字段（包含OCR常见误识别）
            'development_department': [
                r'申请部门[：:]\s*[.,]?\s*([^，,\n\r]+)',  # 支持前缀点号或逗号
                r'申请音门[：:]\s*[.,]?\s*([^，,\n\r]+)',  # OCR错误：音门 -> 部门
                r'申请剖门[：:]\s*[.,]?\s*([^，,\n\r]+)',  # OCR错误：剖门 -> 部门
                r'部门[：:]\s*[.,]?\s*([^，,\n\r]+)',
                r'申请单位[：:]\s*[.,]?\s*([^，,\n\r]+)',
                r'研制部门[：:]\s*[.,]?\s*([^，,\n\r]+)',
            ],
            
            # 机型
            'aircraft_model': [
                r'机型[：:]\s*([^，,\n\r]+)',
                r'机刑[：:]\s*([^，,\n\r]+)',  # OCR错误：机刑 -> 机型
            ],
            
            # 项目主管总师
            'project_director': [
                r'项目主管总师[：:]\s*([^，,\n\r]+)',
                r'项目主管总帅[：:]\s*([^，,\n\r]+)',  # OCR错误：总帅 -> 总师
                r'项目主管怨师[：:]\s*([^，,\n\r]+)',  # OCR错误：怨师 -> 总师
                r'项目总师[：:]\s*([^，,\n\r]+)',
            ],
            
            # 主任设计师
            'chief_designer': [
                r'主任设计师[：:]\s*([^，,\n\r]+)',
                r'主任设汁师[：:]\s*([^，,\n\r]+)',  # OCR错误：设汁师 -> 设计师
                r'主任设让师[：:]\s*([^，,\n\r]+)',  # OCR错误：设让师 -> 设计师
            ],
            
            # 项目主管
            'project_manager': [
                r'项目主管[：:]\s*([^，,\n\r]+)',
                # 注意：要排除"项目主管总师"的情况
            ],
            
            # 组件
            'component': [
                r'组件[：:]\s*([^，,\n\r]+)',
                r'产品类型[：:]\s*([^，,\n\r]+)',  # 兼容旧版本字段名
            ],
        }
        
        # 部门名称错别字纠正映射
        self.department_corrections = {
            "总体剖": "总体部",
            "图像剖": "图像部",
            "激光剖": "激光部",
            "光电剖": "光电部",
            "武控剖": "武控部",
            "瞄准显示剖": "瞄准显示部",
            "光电系统—部": "光电系统一部",
            "光电系统二剖": "光电系统二部",
            "光电系统三剖": "光电系统三部",
            "光电系统四剖": "光电系统四部",
            "重点实验宝": "重点实验室",
            "重点实验至": "重点实验室"
        }
    
    def extract_form_data(self, ocr_text: str) -> dict:
        """
        从OCR文本中提取表单数据（使用传统算法）
        
        Args:
            ocr_text (str): OCR识别的文本
            
        Returns:
            dict: 结构化的表单数据
        """
        try:
            log_info(f"开始使用传统算法从OCR文本提取表单数据，文本长度: {len(ocr_text)}", Path(__file__).stem)
            
            # 预处理OCR文本
            cleaned_text = self._preprocess_text(ocr_text)
            
            # 提取各个字段
            extracted_fields = {}
            for field_name, patterns in self.field_patterns.items():
                value = self._extract_field_value(cleaned_text, patterns, field_name)
                if value:
                    extracted_fields[field_name] = value
                    log_debug(f"提取字段 {field_name}: '{value}'", Path(__file__).stem)
            
            # 特殊处理：如果申请人字段为空或只有标识符，尝试从下一行获取
            if not extracted_fields.get('developer') or extracted_fields.get('developer') in ['', '=', ':']:
                developer_name = self._extract_developer_from_next_line(cleaned_text)
                if developer_name:
                    extracted_fields['developer'] = developer_name
                    log_debug(f"从下一行提取申请人: '{developer_name}'", Path(__file__).stem)
            
            # 特殊处理：如果项目主管字段为空，尝试从分行文本中提取
            if not extracted_fields.get('project_manager'):
                project_manager_name = self._extract_project_manager_from_lines(cleaned_text)
                if project_manager_name:
                    extracted_fields['project_manager'] = project_manager_name
                    log_debug(f"从分行文本提取项目主管: '{project_manager_name}'", Path(__file__).stem)
            
            # 特殊处理申请部门（最重要的字段）
            department = self._extract_department_with_fallback(cleaned_text, extracted_fields.get('development_department', ''))
            if department:
                extracted_fields['development_department'] = department
            
            # 构建返回数据结构
            result = {
                "basic_info": {
                    "domain": "",
                    "test_manager": "",
                    "test_personnel": "",
                    "developer": extracted_fields.get('developer', '')
                },
                "optional_info": {
                    "aircraft_model": extracted_fields.get('aircraft_model', ''),
                    "project_director": extracted_fields.get('project_director', ''),
                    "development_department": extracted_fields.get('development_department', ''),
                    "chief_designer": extracted_fields.get('chief_designer', ''),
                    "project_manager": extracted_fields.get('project_manager', ''),
                    "component": extracted_fields.get('component', '')
                }
            }
            
            # 根据申请部门推断领域和测试人员
            result = self._infer_domain_and_personnel(result)
            
            log_info(f"传统算法提取完成: {result}", Path(__file__).stem)
            return result
            
        except Exception as e:
            log_error(f"传统算法数据提取失败: {str(e)}", Path(__file__).stem)
            # 返回空结构
            return {
                "basic_info": {
                    "domain": "",
                    "test_manager": "",
                    "test_personnel": "",
                    "developer": ""
                },
                "optional_info": {
                    "aircraft_model": "",
                    "project_director": "",
                    "development_department": "",
                    "chief_designer": "",
                    "project_manager": "",
                    "component": ""
                }
            }
    
    def _preprocess_text(self, text: str) -> str:
        """预处理OCR文本"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除多余的空白字符，但保留换行
        lines = []
        for line in text.split('\n'):
            cleaned_line = re.sub(r'\s+', ' ', line.strip())
            if cleaned_line:
                lines.append(cleaned_line)
        
        return '\n'.join(lines)
    
    def _extract_field_value(self, text: str, patterns: List[str], field_name: str) -> str:
        """使用正则表达式提取字段值"""
        for pattern in patterns:
            # 特殊处理项目主管字段，避免匹配到"项目主管总师"
            if field_name == 'project_manager':
                # 使用负向先行断言，确保后面不是"总师"
                pattern = r'项目主管(?!总师)[：:]\s*([^，,\n\r]+)'
            
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                value = matches[0].strip()
                if value:
                    log_debug(f"字段 {field_name} 匹配成功，模式: {pattern}, 值: '{value}'", Path(__file__).stem)
                    return value
        
        return ""
    
    def _extract_department_with_fallback(self, text: str, initial_department: str) -> str:
        """使用多种策略提取申请部门"""
        department = initial_department
        
        # 如果已经提取到部门，先纠正错别字
        if department:
            department = self._correct_department_typos(department)
            if department:
                return department
        
        # 策略1: 查找分散的部门信息并拼接
        department_keywords = {
            '光电系统': ['一部', '二部', '三部', '四部'],
            '图像': ['部'],
            '激光': ['部'],
            '光电': ['部'],
            '总体': ['部'],
            '武控': ['部'],
            '瞄准显示': ['部'],
            '重点实验': ['室']
        }
        
        for base_keyword, suffixes in department_keywords.items():
            if base_keyword in text:
                for suffix in suffixes:
                    if suffix in text:
                        candidate = base_keyword + suffix
                        # 检查是否有子部门信息
                        if '/控制室' in text and '光电系统' in candidate:
                            candidate += '/控制室'
                        
                        candidate = self._correct_department_typos(candidate)
                        if candidate:
                            log_info(f"通过关键词拼接提取部门: '{candidate}'", Path(__file__).stem)
                            return candidate
        
        # 策略2: 部分匹配已知部门列表
        known_departments = list(self.config['department_to_domain'].keys())
        for known_dept in known_departments:
            # 检查是否包含部门的关键部分
            dept_base = known_dept.replace('部', '').replace('室', '')
            if dept_base in text and len(dept_base) > 1:
                log_info(f"通过部分匹配提取部门: '{known_dept}'", Path(__file__).stem)
                return known_dept
        
        # 策略3: 智能推断
        if '图像' in text:
            return '图像部'
        elif '激光' in text:
            return '激光部'
        elif '总体' in text:
            return '总体部'
        elif '武控' in text:
            return '武控部'
        elif '瞄准' in text or '显示' in text:
            return '瞄准显示部'
        elif '重点' in text and '实验' in text:
            return '重点实验室'
        
        return department
    
    def _extract_developer_from_next_line(self, text: str) -> str:
        """从申请人标识符的下一行提取姓名"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # 查找包含"申请人"的行
            if re.search(r'申请人[：:=]?\s*$', line.strip()):
                # 检查下一行是否包含姓名
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # 简单的姓名验证：2-4个中文字符
                    if re.match(r'^[\u4e00-\u9fff]{2,4}$', next_line):
                        return next_line
        return ""
    
    def _extract_project_manager_from_lines(self, text: str) -> str:
        """从分行文本中提取项目主管姓名（增强版）"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 查找包含"项目主管"但不包含"总师"的行
            if '项目主管' in line_stripped and '总师' not in line_stripped:
                # 策略1: 检查当前行是否已包含姓名（标准格式）
                match = re.search(r'项目主管[：:=]\s*(.+)', line_stripped)
                if match and match.group(1).strip():
                    name = match.group(1).strip()
                    # 验证是否为有效姓名（2-4个中文字符）
                    if re.match(r'^[\u4e00-\u9fff]{2,4}$', name):
                        log_debug(f"从当前行提取项目主管（标准格式）: '{name}'", Path(__file__).stem)
                        return name
                
                # 策略2: 检查当前行是否包含姓名（无冒号分隔）
                # 例如："项目主管 张三" 或 "项目主管张三"
                match_no_separator = re.search(r'项目主管\s*([^\s]{2,4})$', line_stripped)
                if match_no_separator:
                    name = match_no_separator.group(1).strip()
                    if re.match(r'^[\u4e00-\u9fff]{2,4}$', name):
                        log_debug(f"从当前行提取项目主管（无分隔符）: '{name}'", Path(__file__).stem)
                        return name
                
                # 策略3: 检查下一行是否包含姓名
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # 验证下一行是否为2-4个中文字符的姓名
                    if re.match(r'^[\u4e00-\u9fff]{2,4}$', next_line):
                        log_debug(f"从下一行提取项目主管: '{next_line}'", Path(__file__).stem)
                        return next_line
                
                # 策略4: 检查当前行后面紧跟的文本（可能在同一行但空格分隔）
                # 例如："项目主管     张三"
                parts = line_stripped.split()
                if len(parts) >= 2:
                    for part in parts[1:]:  # 跳过"项目主管"本身
                        if re.match(r'^[\u4e00-\u9fff]{2,4}$', part):
                            log_debug(f"从同行后续文本提取项目主管: '{part}'", Path(__file__).stem)
                            return part
        
        return ""
    
    def _correct_department_typos(self, department_name: str) -> str:
        """纠正部门名称中的常见错别字"""
        if not department_name:
            return department_name
            
        corrected = department_name
        for wrong, correct in self.department_corrections.items():
            if wrong in corrected:
                corrected = corrected.replace(wrong, correct)
                log_debug(f"纠正部门错别字: '{department_name}' -> '{corrected}'", Path(__file__).stem)
        
        return corrected
    
    def _infer_domain_and_personnel(self, extracted_data: dict) -> dict:
        """根据申请部门推断所属领域和测试人员"""
        try:
            development_department = extracted_data.get('optional_info', {}).get('development_department', '')
            
            if development_department:
                log_info(f"尝试为申请部门'{development_department}'推断领域", Path(__file__).stem)
                
                # 再次纠正可能的错别字
                corrected_department = self._correct_department_typos(development_department)
                if corrected_department != development_department:
                    log_info(f"纠正部门名称错别字：'{development_department}' → '{corrected_department}'", Path(__file__).stem)
                    extracted_data['optional_info']['development_department'] = corrected_department
                    development_department = corrected_department
                
                # 1. 精确匹配
                domain = self.config['department_to_domain'].get(development_department, '')
                
                # 2. 如果精确匹配失败，尝试部分匹配
                if not domain:
                    log_info(f"精确匹配失败，尝试部分匹配", Path(__file__).stem)
                    
                    for config_dept, config_domain in self.config['department_to_domain'].items():
                        # 检查是否包含关键词
                        if config_dept in development_department or development_department in config_dept:
                            domain = config_domain
                            log_info(f"部分匹配成功：'{development_department}' 匹配到 '{config_dept}' -> '{domain}'", Path(__file__).stem)
                            break
                
                # 3. 关键词匹配
                if not domain:
                    log_info(f"部分匹配失败，尝试关键词匹配", Path(__file__).stem)
                    
                    # 光电领域关键词
                    optoelectronic_keywords = ['光电', '图像', '激光', '光电系统']
                    # 显示领域关键词  
                    display_keywords = ['瞄准', '显示']
                    # 火控领域关键词
                    fire_control_keywords = ['总体', '火控', '重点实验室']
                    # 外挂领域关键词
                    external_keywords = ['武控', '外挂']
                    
                    if any(keyword in development_department for keyword in optoelectronic_keywords):
                        domain = "光电领域"
                        log_info(f"关键词匹配：'{development_department}' -> 光电领域", Path(__file__).stem)
                    elif any(keyword in development_department for keyword in display_keywords):
                        domain = "显示领域"
                        log_info(f"关键词匹配：'{development_department}' -> 显示领域", Path(__file__).stem)
                    elif any(keyword in development_department for keyword in fire_control_keywords):
                        domain = "火控领域"
                        log_info(f"关键词匹配：'{development_department}' -> 火控领域", Path(__file__).stem)
                    elif any(keyword in development_department for keyword in external_keywords):
                        domain = "外挂领域"
                        log_info(f"关键词匹配：'{development_department}' -> 外挂领域", Path(__file__).stem)
                
                if domain:
                    # 设置所属领域
                    extracted_data['basic_info']['domain'] = domain
                    
                    # 根据领域设置测试主管和测试人员
                    personnel = self.config['domain_personnel'].get(domain, {})
                    if personnel:
                        extracted_data['basic_info']['test_manager'] = personnel.get('test_manager', '')
                        extracted_data['basic_info']['test_personnel'] = personnel.get('test_personnel', '')
                        
                    log_info(f"✅ 成功推断 - 申请部门：'{development_department}' → 领域：'{domain}' → 测试主管：{personnel.get('test_manager', '')} → 测试人员：{personnel.get('test_personnel', '')}", Path(__file__).stem)
                else:
                    log_warning(f"❌ 所有匹配策略都失败，无法为申请部门'{development_department}'推断领域", Path(__file__).stem)
            else:
                log_warning("❌ 未提取到申请部门信息，无法推断领域和测试人员", Path(__file__).stem)
                
        except Exception as e:
            log_error(f"推断领域和测试人员失败: {str(e)}", Path(__file__).stem)
            
        return extracted_data


# 全局传统数据提取器实例（延迟加载）
_traditional_extractor = None

def get_traditional_extractor():
    """获取全局传统数据提取器实例（延迟加载）"""
    global _traditional_extractor
    if _traditional_extractor is None:
        log_info("正在创建传统数据提取器实例...", "traditional_data_extractor")
        try:
            _traditional_extractor = TraditionalDataExtractor()
            log_info("传统数据提取器实例创建成功", "traditional_data_extractor")
        except Exception as e:
            log_error(f"创建传统数据提取器实例失败: {str(e)}", "traditional_data_extractor")
            raise
    return _traditional_extractor 