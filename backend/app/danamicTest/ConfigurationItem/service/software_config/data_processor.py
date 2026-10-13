"""
软件配置项信息数据处理器

负责处理和组织软件配置项信息表所需的数据。
"""

import logging
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# 导入文档页数计算器
from .document_page_counter import DocumentPageCounter

# 配置日志
logger = logging.getLogger(__name__)

class SoftwareConfigDataProcessor:
    """软件配置项信息数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.logger = logger
        self.document_page_counter = DocumentPageCounter()
    
    def organize_software_config_data(
        self,
        ruanjian_name: str,
        ceshiren_name: str,
        zhuguan_name: str,
        daima_chayi_hangshu: int,
        xinghao_xinxi_list: Optional[List[str]] = None,
        ruanjian_xinxi_duqu_temp: Optional[Dict[str, Any]] = None,
        ceshileixing: str = "配置项测试",
        user_software_info: Optional[Dict[str, Any]] = None,
        planning_requirements_count: int = 0,
        analysis_requirements_count: int = 0,
        requirement_doc_path: Optional[str] = None,
        code_path: Optional[str] = None  # 添加代码路径参数
    ) -> Dict[str, Any]:
        """
        组织软件配置项信息数据
        
        Args:
            ruanjian_name: 软件名称
            ceshiren_name: 测试人员姓名
            zhuguan_name: 测试主管姓名
            daima_chayi_hangshu: 代码差异行数
            xinghao_xinxi_list: 型号信息列表
            ruanjian_xinxi_duqu_temp: 从文档读取的软件信息
            ceshileixing: 测试类型
            user_software_info: 用户提供的软件信息
            planning_requirements_count: 策划表需求数量
            analysis_requirements_count: 分析表需求数量
            requirement_doc_path: 需求文档路径
            code_path: 代码文件路径（用于统计软件规模）
            
        Returns:
            Dict[str, Any]: 组织后的软件配置数据
        """
        try:
            # 进行代码统计
            code_statistics = self._perform_code_statistics(daima_chayi_hangshu, code_path)
            
            # 组织基本信息（使用统计后的代码行数）
            basic_info = self._organize_basic_info(
                ruanjian_name, ceshiren_name, zhuguan_name, 
                code_statistics['final_code_lines'], ceshileixing
            )
            
            # 组织软件详细信息
            software_details = self._organize_software_details(
                xinghao_xinxi_list, ruanjian_xinxi_duqu_temp, user_software_info
            )
            
            # 组织统计信息（使用统计后的代码行数）
            statistics_info = self._organize_statistics_info(
                planning_requirements_count, analysis_requirements_count, 
                code_statistics['final_code_lines'], requirement_doc_path
            )
            
            # 组织时间信息（使用统计后的代码行数）
            time_info = self._organize_time_info(code_statistics['final_code_lines'])
            
            # 组织固定值信息
            fixed_values = self._get_fixed_values(ceshileixing)
            
            # 组织完整的软件配置数据
            software_config_data = {
                'basic_info': basic_info,
                'software_details': software_details,
                'code_statistics': code_statistics,  # 添加代码统计信息
                'statistics_info': statistics_info,
                'time_info': time_info,
                'fixed_values': fixed_values,
                'requirement_doc_path': requirement_doc_path,
                'data_sources': self._get_data_sources(xinghao_xinxi_list, ruanjian_xinxi_duqu_temp, user_software_info)
            }
            
            self.logger.info(f"软件配置项数据组织完成，软件规模: {code_statistics['final_code_lines']} 行，测试代码规模: {statistics_info['test_scale']} 行，有效测试代码规模: {statistics_info['effective_test_code_scale']} 行，审查文档规模: {statistics_info['review_document_scale']} 页，实际测试工作量: {statistics_info['actual_test_workload']} 天")
            
            # 记录详细的数据组织结果
            self.logger.debug(f"[DEBUG] 软件配置项数据组织完成，详细信息:")
            self.logger.debug(f"[DEBUG]   - 软件名称: {ruanjian_name}")
            self.logger.debug(f"[DEBUG]   - 测试人员: {ceshiren_name}")
            self.logger.debug(f"[DEBUG]   - 主管姓名: {zhuguan_name}")
            self.logger.debug(f"[DEBUG]   - 软件规模: {code_statistics['final_code_lines']}行")
            self.logger.debug(f"[DEBUG]   - 测试代码规模: {statistics_info['test_scale']}行")
            self.logger.debug(f"[DEBUG]   - 有效测试代码规模: {statistics_info['effective_test_code_scale']}行")
            self.logger.debug(f"[DEBUG]   - 编写测试文档规模: {statistics_info['test_document_scale']}行")
            self.logger.debug(f"[DEBUG]   - 审查文档规模: {statistics_info['review_document_scale']}页")
            self.logger.debug(f"[DEBUG]   - 实际测试工作量: {statistics_info['actual_test_workload']}天")
            self.logger.debug(f"[DEBUG]   - 是否合作项目: {fixed_values['is_cooperation_project']}")
            self.logger.debug(f"[DEBUG]   - 需求文档路径: {requirement_doc_path}")
            self.logger.debug(f"[DEBUG]   - 策划需求数量: {planning_requirements_count}")
            self.logger.debug(f"[DEBUG]   - 分析需求数量: {analysis_requirements_count}")
            
            return software_config_data
            
        except Exception as e:
            self.logger.error(f"组织软件配置项数据时发生错误: {str(e)}")
            raise
    
    def _organize_basic_info(
        self, 
        ruanjian_name: str, 
        ceshiren_name: str, 
        zhuguan_name: str, 
        daima_chayi_hangshu: int, 
        ceshileixing: str
    ) -> Dict[str, Any]:
        """组织基本信息"""
        return {
            'software_name': ruanjian_name,
            'tester_name': ceshiren_name,
            'manager_name': zhuguan_name,
            'code_lines': daima_chayi_hangshu,
            'test_type': ceshileixing,
            'is_same_person': ceshiren_name == zhuguan_name
        }
    
    def _perform_code_statistics(self, daima_chayi_hangshu: int, code_path: Optional[str]) -> Dict[str, Any]:
        """执行代码统计"""
        calculated_code_lines = daima_chayi_hangshu  # 初始值
        
        self.logger.info(f"开始软件规模计算：原始值={daima_chayi_hangshu}, 代码路径={code_path}")
        
        # 如果提供了代码路径，优先使用代码统计
        if code_path and os.path.exists(code_path):
            try:
                self.logger.info(f"开始进行代码统计，路径: {code_path}")
                calculated_code_lines = self._analyze_code_path(code_path, daima_chayi_hangshu)
            except Exception as e:
                self.logger.error(f"代码统计过程中发生错误: {e}，使用原始值: {daima_chayi_hangshu}")
        else:
            # 没有提供代码路径时的处理逻辑
            if daima_chayi_hangshu <= 0:
                calculated_code_lines = 5000  # 使用默认软件规模
                self.logger.info(f"未提供代码路径且传入代码行数为0，使用默认软件规模: {calculated_code_lines}")
            else:
                self.logger.info(f"未提供代码路径，使用传入的软件规模: {calculated_code_lines}")
        
        self.logger.info(f"最终软件规模: {calculated_code_lines}")
        
        return {
            'original_code_lines': daima_chayi_hangshu,
            'final_code_lines': int(calculated_code_lines) if isinstance(calculated_code_lines, (str, float)) else calculated_code_lines,
            'code_path': code_path,
            'statistics_performed': code_path is not None and os.path.exists(code_path) if code_path else False
        }
    
    def _analyze_code_path(self, code_path: str, default_lines: int) -> int:
        """分析代码路径并返回代码行数"""
        try:
            from .line_count.code_statistics import CodeStatistics
            
            code_stats = CodeStatistics()
            
            # 如果是zip文件，需要先解压
            if code_path.endswith('.zip'):
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix='code_analysis_')
                self.logger.info(f"检测到zip文件，创建临时目录: {temp_dir}")
                result = code_stats.analyze_code(code_path, 'temp_task', temp_dir)
                if result.get('analysis_success', False):
                    calculated_lines = result.get('total_lines', default_lines)
                    self.logger.info(f"代码统计完成，总行数: {calculated_lines}")
                    
                    # 清理临时目录
                    try:
                        import shutil
                        shutil.rmtree(temp_dir)
                        self.logger.debug(f"清理临时目录: {temp_dir}")
                    except Exception as cleanup_e:
                        self.logger.warning(f"清理临时目录失败: {cleanup_e}")
                    
                    return calculated_lines
                else:
                    self.logger.warning(f"代码统计失败，使用默认值: {default_lines}")
                    return default_lines
            else:
                # 如果是目录，直接分析
                result = code_stats.analyze_with_lizard(code_path)
                if result.get('analysis_success', False):
                    calculated_lines = result.get('total_lines', default_lines)
                    self.logger.info(f"目录代码统计完成，总行数: {calculated_lines}")
                    return calculated_lines
                else:
                    self.logger.warning(f"目录代码统计失败，使用默认值: {default_lines}")
                    return default_lines
                    
        except ImportError as e:
            self.logger.warning(f"代码统计模块不可用: {e}，使用默认值: {default_lines}")
            return default_lines
        except Exception as e:
            self.logger.error(f"代码分析过程中发生错误: {e}，使用默认值: {default_lines}")
            return default_lines
    
    def _organize_software_details(
        self, 
        xinghao_xinxi_list: Optional[List[str]], 
        ruanjian_xinxi_duqu_temp: Optional[Dict[str, Any]], 
        user_software_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """组织软件详细信息"""
        details = {
            'software_short_name': '',
            'software_short_name_en': '',
            'software_id': '',
            'system_name': '',
            'system_short_name': '',
            'component': '',
            'software_version': '',
            'programming_language': 'ANSIC',
            'development_environment': 'AcoreIde',
            'runtime_environment': '飞腾2000（天脉3）',
            'software_level': '重要'
        }
        
        # 优先级：用户输入 > 型号信息库 > 文档提取 > 默认值
        user_software_id = None  # 保存用户输入的软件标识
        
        if user_software_info:
            user_software_id = user_software_info.get('software_id', '')
            # ✅ 获取product_type（组件）字段
            product_type = user_software_info.get('product_type', '') or user_software_info.get('component', '')
            
            details.update({
                'software_id': user_software_id,
                'software_version': user_software_info.get('software_version', ''),
                'software_name': user_software_info.get('software_name', ''),
                'component': product_type  # ✅ 添加组件字段
            })
            self.logger.info(f"[DEBUG] 用户软件信息: software_id='{user_software_id}', software_version='{user_software_info.get('software_version', '')}', software_name='{user_software_info.get('software_name', '')}', component='{product_type}'")
        
        if xinghao_xinxi_list and len(xinghao_xinxi_list) >= 18:
            # ✅ 保存用户的组件选择（在更新前）
            user_component = details.get('component', '')
            
            model_details = {
                'software_short_name': xinghao_xinxi_list[7],
                'software_short_name_en': xinghao_xinxi_list[8],
                'system_name': xinghao_xinxi_list[10],
                'system_short_name': xinghao_xinxi_list[11],
                'component': xinghao_xinxi_list[12],
                'programming_language': xinghao_xinxi_list[14],
                'development_environment': xinghao_xinxi_list[15],
                'runtime_environment': xinghao_xinxi_list[16],
                'software_level': xinghao_xinxi_list[17]
            }
            
            # 只有当用户没有提供software_id时，才使用型号库的值
            if not user_software_id:
                model_details['software_id'] = xinghao_xinxi_list[12]
            
            details.update(model_details)
            
            # ✅ 如果用户提供了组件，恢复用户的选择（优先级最高）
            if user_component:
                details['component'] = user_component
                self.logger.info(f"[DEBUG] 恢复用户选择的组件: '{user_component}'（覆盖型号库的组件）")
            
            self.logger.info(f"[DEBUG] 型号信息库更新: user_software_id='{user_software_id}', 使用型号库software_id={not user_software_id}, 最终component='{details.get('component', '')}'")
        
        if ruanjian_xinxi_duqu_temp:
            # 从文档中提取的信息
            for key, value in ruanjian_xinxi_duqu_temp.items():
                if key == '软件简称' and value:
                    details['software_short_name'] = value
                elif key == '软件标识' and value:
                    details['software_id'] = value
                elif key == '软件版本' and value:
                    details['software_version'] = value
                elif key == '系统名称' and value:
                    details['system_name'] = value
                elif key == '系统简称' and value:
                    details['system_short_name'] = value
        
        return details
    
    def _organize_statistics_info(
        self, 
        planning_requirements_count: int, 
        analysis_requirements_count: int, 
        daima_chayi_hangshu: int,
        requirement_doc_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """组织统计信息"""
        # 计算测试规模（原来的计算逻辑保留用于其他地方）
        ceshiguimo_jisuan = self._calculate_test_scale(daima_chayi_hangshu)
        
        # 计算审查文档规模
        review_document_scale = self._calculate_review_document_scale(requirement_doc_path)
        
        # 计算实际测试工作量
        actual_test_workload = self._calculate_actual_test_workload(daima_chayi_hangshu)
        
        # 有效测试代码规模直接使用软件规模数值（daima_chayi_hangshu实际是final_code_lines）
        effective_test_code_scale = daima_chayi_hangshu
        
        # 测试代码规模直接使用软件规模数值（第21行）
        test_scale = daima_chayi_hangshu
        
        # 编写测试文档规模默认填0（第23行）
        test_document_scale = 0
        
        self.logger.debug(f"[DEBUG] 测试规模设置")
        self.logger.debug(f"[DEBUG]   - 软件规模值: {daima_chayi_hangshu}")
        self.logger.debug(f"[DEBUG]   - 测试代码规模: {test_scale}")
        self.logger.debug(f"[DEBUG]   - 有效测试代码规模: {effective_test_code_scale}")
        self.logger.debug(f"[DEBUG]   - 编写测试文档规模: {test_document_scale}")
        self.logger.debug(f"[DEBUG]   - 原测试规模计算值: {ceshiguimo_jisuan}")
        
        return {
            'planning_requirements_count': planning_requirements_count,
            'analysis_requirements_count': analysis_requirements_count,
            'test_scale': test_scale,
            'effective_test_code_scale': effective_test_code_scale,
            'software_change_scale': 0,
            'review_document_scale': review_document_scale,
            'test_document_scale': test_document_scale,
            'actual_test_workload': actual_test_workload,
            'remaining_issues_count': '',
            'test_depth': '全面测试'
        }
    
    def _organize_time_info(self, daima_chayi_hangshu: int) -> Dict[str, Any]:
        """组织时间信息"""
        try:
            import datetime
            ceshi_start_time, ceshi_end_time = self._ceshi_start_end_time(daima_chayi_hangshu)
            
            # ✨ 新增：将计划结束时间和实际结束时间在当前算法基础上再增加7天
            # 解析结束时间字符串为日期对象
            end_date = datetime.datetime.strptime(ceshi_end_time, '%Y/%m/%d').date()
            # 增加7天（自动处理跨月和跨年）
            extended_end_date = end_date + datetime.timedelta(days=7)
            # 转回字符串格式
            extended_end_time = extended_end_date.strftime('%Y/%m/%d')
            
            self.logger.info(f"时间计算: 原始结束时间={ceshi_end_time}, 延长7天后={extended_end_time}")
            
            return {
                'planned_start_time': ceshi_start_time,
                'planned_end_time': extended_end_time,     # ✨ 使用延长后的时间
                'actual_start_time': ceshi_start_time,
                'actual_end_time': extended_end_time       # ✨ 使用延长后的时间
            }
        except Exception as e:
            self.logger.error(f"时间信息组织失败: {e}")
            return {
                'planned_start_time': '',
                'planned_end_time': '',
                'actual_start_time': '',
                'actual_end_time': ''
            }
    
    def _ceshi_start_end_time(self, daima_chayi_hangshu: int):
        """计算测试开始和结束时间"""
        import datetime
        current_date = datetime.date.today()
        ceshi_start_time = current_date.strftime('%Y/%m/%d')
        # 计算项目所需天数，根据代码差异行数估算
        days_required = daima_chayi_hangshu // 500 + 2  # 每500行代码差异对应2天时间
        # 计算项目结束日期
        ceshi_end_time = current_date + datetime.timedelta(days=days_required)
        ceshi_end_time = ceshi_end_time.strftime('%Y/%m/%d')
        return ceshi_start_time, ceshi_end_time
    
    def _calculate_actual_test_workload(self, daima_chayi_hangshu: int) -> int:
        """计算实际测试工作量（天数）"""
        try:
            # 使用与时间计算相同的逻辑：每500行代码差异对应2天时间
            workload_days = daima_chayi_hangshu // 500 + 2
            
            self.logger.debug(f"[DEBUG] 计算实际测试工作量")
            self.logger.debug(f"[DEBUG]   - 代码差异行数: {daima_chayi_hangshu}")
            self.logger.debug(f"[DEBUG]   - 计算公式: {daima_chayi_hangshu} ÷ 500 + 2 = {workload_days}天")
            self.logger.info(f"实际测试工作量计算完成: {workload_days}天")
            
            return workload_days
        except Exception as e:
            self.logger.error(f"实际测试工作量计算失败: {e}")
            # 出错时返回默认值
            return 5
    
    def _get_fixed_values(self, ceshileixing: str) -> Dict[str, Any]:
        """获取固定值配置"""
        return {
            'is_closed': '是',
            'is_urgent': '是',
            'development_stage': 'S',
            'verification_status': '所内验证',
            'config_management_status': '出库后更改' if ceshileixing == '回归测试' else '首次入库',
            'purpose': '联试',
            'related_major_issues': '无',
            'is_model_generated': '否',
            'is_cooperation_project': '是',  # 默认改为"是"
            'software_type': '应用软件',
            'is_business_trip': '否',
            'remarks': '无'
        }
    
    def _get_data_sources(
        self, 
        xinghao_xinxi_list: Optional[List[str]], 
        ruanjian_xinxi_duqu_temp: Optional[Dict[str, Any]], 
        user_software_info: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """获取数据来源信息"""
        sources = {}
        
        if user_software_info:
            sources['user_input'] = "用户输入"
        if xinghao_xinxi_list:
            sources['model_database'] = "型号信息库"
        if ruanjian_xinxi_duqu_temp:
            sources['document_extraction'] = "文档提取"
        
        return sources
    
    def _calculate_test_scale(self, daima_chayi_hangshu: int) -> int:
        """计算测试规模"""
        try:
            return self._ceshiguimo_fenxi(daima_chayi_hangshu)
        except Exception as e:
            self.logger.warning(f"测试规模计算失败，使用代码行数: {e}")
            return daima_chayi_hangshu
    
    def _ceshiguimo_fenxi(self, daima_chayi_hangshu: int) -> int:
        """分析测试规模"""
        if isinstance(daima_chayi_hangshu, (int, float)):
            if daima_chayi_hangshu <= 0:
                ceshiguimo = 100
            elif 0 < daima_chayi_hangshu <= 50:
                ceshiguimo = 150
            elif 50 < daima_chayi_hangshu:
                ceshiguimo = daima_chayi_hangshu * 3
            return ceshiguimo
        else:
            return 0
    
    def validate_software_config_data(self, software_config_data: Dict[str, Any]) -> bool:
        """
        验证软件配置项数据的完整性
        
        Args:
            software_config_data: 软件配置数据字典
            
        Returns:
            bool: 验证结果
        """
        try:
            required_keys = ['basic_info', 'software_details', 'statistics_info', 'time_info', 'fixed_values']
            
            for key in required_keys:
                if key not in software_config_data:
                    self.logger.warning(f"缺少必需的数据字段: {key}")
                    return False
            
            # 验证基本信息
            basic_info = software_config_data['basic_info']
            if not basic_info.get('software_name'):
                self.logger.warning("缺少软件名称")
                return False
            
            self.logger.info("软件配置项数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证软件配置项数据时发生错误: {str(e)}")
            return False
    
    def _calculate_review_document_scale(self, requirement_doc_path: Optional[str]) -> int:
        """
        计算审查文档规模
        
        Args:
            requirement_doc_path: 需求文档路径
            
        Returns:
            int: 审查文档规模（页数）
        """
        try:
            self.logger.debug(f"[DEBUG] 开始计算审查文档规模流程")
            self.logger.debug(f"[DEBUG] 输入参数 - requirement_doc_path: '{requirement_doc_path}'")
            self.logger.info(f"开始计算审查文档规模，文档路径: {requirement_doc_path}")
            
            if not requirement_doc_path:
                self.logger.warning("需求文档路径为空，使用默认审查文档规模")
                self.logger.debug(f"[DEBUG] 路径为空，返回默认值: 60")
                return 60  # 默认值
            
            # 检查文档路径是否存在
            import os
            if not os.path.exists(requirement_doc_path):
                self.logger.warning(f"需求文档文件不存在: {requirement_doc_path}")
                self.logger.debug(f"[DEBUG] 文件不存在，返回默认值: 60")
                return 60
            
            # 获取文档文件信息
            from pathlib import Path
            doc_path = Path(requirement_doc_path)
            file_size = doc_path.stat().st_size
            file_extension = doc_path.suffix.lower()
            
            self.logger.debug(f"[DEBUG] 文档文件信息:")
            self.logger.debug(f"[DEBUG]   - 文件路径: {requirement_doc_path}")
            self.logger.debug(f"[DEBUG]   - 文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
            self.logger.debug(f"[DEBUG]   - 文件格式: {file_extension}")
            
            # 使用文档页数计算器计算页数
            self.logger.debug(f"[DEBUG] 调用文档页数计算器")
            review_document_scale = self.document_page_counter.get_review_document_scale(
                document_path=requirement_doc_path,
                default_value=60
            )
            
            self.logger.debug(f"[DEBUG] 文档页数计算器返回结果: {review_document_scale}")
            self.logger.info(f"审查文档规模计算完成: {review_document_scale}页")
            
            # 记录详细的计算结果
            self.logger.debug(f"[DEBUG] 审查文档规模计算详情:")
            self.logger.debug(f"[DEBUG]   - 输入文档: {requirement_doc_path}")
            self.logger.debug(f"[DEBUG]   - 文档格式: {file_extension}")
            self.logger.debug(f"[DEBUG]   - 文档大小: {file_size} 字节")
            self.logger.debug(f"[DEBUG]   - 计算结果: {review_document_scale}页")
            self.logger.debug(f"[DEBUG]   - 计算方式: 自动文档页数计算")
            
            return review_document_scale
            
        except Exception as e:
            self.logger.error(f"计算审查文档规模时发生错误: {str(e)}")
            self.logger.debug(f"[DEBUG] 异常详情: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.debug(f"[DEBUG] 异常堆栈: {traceback.format_exc()}")
            self.logger.debug(f"[DEBUG] 异常发生，返回默认值: 60")
            return 60  # 发生错误时返回默认值
