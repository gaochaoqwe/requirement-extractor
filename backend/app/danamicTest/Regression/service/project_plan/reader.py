"""
回归测试项目策划表读取器

负责从Excel文件中读取回归测试项目策划表的数据。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class RegressionProjectPlanReader:
    """回归测试项目策划表读取器"""
    
    def __init__(self):
        """初始化读取器"""
        self.logger = logger
    
    def read_project_plan_data(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表'
    ) -> Tuple[List[List[str]], str]:
        """
        读取回归测试项目策划表数据
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Tuple[List[List[str]], str]: (策划表数据, 状态信息)
            策划表数据格式: [软件需求, 标准需求名称, 标准需求单位, 章节号, 需求标识, 重复项]
        """
        try:
            self.logger.info(f"开始读取回归测试项目策划表: {excel_file_path}")
            
            # 导入必要的模块
            from ...utils.excel_processing.excel_reader import read_excel_with_sheet
            
            # 读取Excel数据
            df = read_excel_with_sheet(excel_file_path, sheet_name=sheet_name)
            
            # 获取需求变更个数
            len_value = df.iloc[6, 4]  # 第7行第5列
            
            # 提取各列数据
            ruanjian_xuqiu = self._extract_column_data(df, 16, len_value, 2)  # 软件需求
            biaozhun_xiu_name = self._extract_column_data(df, 16, len_value, 3)  # 标准需求名称
            biaozhun_xiu_danwei = self._extract_column_data(df, 16, len_value, 4)  # 标准需求单位
            ruanjian_xuqiu_zhangjie = self._extract_column_data(df, 16, len_value, 5)  # 章节号
            
            # 读取或生成需求标识
            ruanjian_xuqiu_biaoshi, chongfu_name, status_msg = self._read_or_generate_identifiers(
                df, ruanjian_xuqiu, len_value
            )
            
            # 组织返回数据
            project_plan_data = [
                ruanjian_xuqiu,
                biaozhun_xiu_name,
                biaozhun_xiu_danwei,
                ruanjian_xuqiu_zhangjie,
                ruanjian_xuqiu_biaoshi,
                chongfu_name
            ]
            
            self.logger.info(f"回归测试项目策划表读取完成，共{len(ruanjian_xuqiu)}个需求")
            return project_plan_data, status_msg
            
        except Exception as e:
            self.logger.error(f"读取回归测试项目策划表时发生错误: {str(e)}")
            # 返回默认值，避免返回None导致解包错误
            default_result = [[], [], [], [], [], []]  # 6个空列表
            default_status = f"策划表读取失败: {e}"
            return default_result, default_status
    
    def _extract_column_data(
        self,
        df,
        start_row: int,
        length: int,
        column: int
    ) -> List[str]:
        """提取列数据并清理"""
        try:
            # 提取数据
            data = df.iloc[start_row:start_row + length, column].reset_index(drop=True).tolist()
            
            # 清理数据
            cleaned_data = self._remove_spaces_from_list(data)
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"提取列数据时发生错误: {str(e)}")
            return []
    
    def _remove_spaces_from_list(self, lst: List) -> List[str]:
        """去除列表中的空格、制表符、换行符"""
        final_list = []
        for item in lst:
            if isinstance(item, str):
                # 去除空格、制表符、换行符
                cleaned_item = item.replace(' ', '').replace('\t', '').replace('\n', '')
                if cleaned_item:  # 只添加非空字符串
                    final_list.append(cleaned_item)
            elif item is not None:
                # 转换为字符串并清理
                cleaned_item = str(item).replace(' ', '').replace('\t', '').replace('\n', '')
                if cleaned_item:
                    final_list.append(cleaned_item)
        
        return final_list
    
    def _read_or_generate_identifiers(
        self,
        df,
        ruanjian_xuqiu: List[str],
        len_value: int
    ) -> Tuple[List[str], List[str], str]:
        """读取或生成需求标识"""
        try:
            # 尝试读取已有的标识
            try:
                ruanjian_xuqiu_biaoshi = df.iloc[16:16 + len_value, 13].reset_index(drop=True).tolist()
                ruanjian_xuqiu_biaoshi = [str(item) if item is not None else '' for item in ruanjian_xuqiu_biaoshi]
                
                # 检查标识是否完整
                if len(ruanjian_xuqiu_biaoshi) == len(ruanjian_xuqiu) and all(ruanjian_xuqiu_biaoshi):
                    # 检查重复
                    chongfu_name = self._find_duplicates(ruanjian_xuqiu_biaoshi)
                    if not chongfu_name:
                        return ruanjian_xuqiu_biaoshi, chongfu_name, "标识读取成功"
                    else:
                        status_msg = f"发现重复标识: {chongfu_name}"
                        return ruanjian_xuqiu_biaoshi, chongfu_name, status_msg
                else:
                    # 标识不完整，需要生成
                    return self._generate_identifiers(ruanjian_xuqiu)
                    
            except Exception:
                # 读取失败，生成新标识
                return self._generate_identifiers(ruanjian_xuqiu)
                
        except Exception as e:
            self.logger.error(f"处理需求标识时发生错误: {str(e)}")
            # 返回默认标识
            default_identifiers = [f'SRC-NAME{i+1}' for i in range(len(ruanjian_xuqiu))]
            return default_identifiers, [], f"标识生成失败: {e}"
    
    def _generate_identifiers(self, ruanjian_xuqiu: List[str]) -> Tuple[List[str], List[str], str]:
        """生成新的标识"""
        try:
            from .identifier_generator import RegressionTestIdentifierGenerator
            
            generator = RegressionTestIdentifierGenerator()
            
            # 生成英文标识
            identifiers = generator.generate_english_identifiers(ruanjian_xuqiu, use_ai_translation=True)
            
            # 检查重复
            chongfu_name = self._find_duplicates(identifiers)
            
            if chongfu_name:
                # 修复重复
                identifiers = generator.fix_duplicate_identifiers(identifiers)
                chongfu_name = []  # 修复后应该没有重复
                status_msg = "标识生成成功（已修复重复）"
            else:
                status_msg = "标识生成成功"
            
            return identifiers, chongfu_name, status_msg
            
        except Exception as e:
            self.logger.error(f"生成标识时发生错误: {str(e)}")
            # 返回默认标识
            default_identifiers = [f'SRC-NAME{i+1}' for i in range(len(ruanjian_xuqiu))]
            return default_identifiers, [], f"标识生成失败: {e}"
    
    def _find_duplicates(self, arr: List[str]) -> List[str]:
        """查找数组中的重复元素"""
        seen = set()
        duplicates = set()
        
        for item in arr:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)
        
        return list(duplicates)
    
    def read_software_info(
        self,
        excel_file_path: str,
        sheet_name: str = '软件配置项信息'
    ) -> Dict[str, str]:
        """
        读取软件配置项信息
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, str]: 软件信息字典
        """
        try:
            from ...utils.excel_processing.excel_reader import read_excel_with_sheet
            
            df = read_excel_with_sheet(excel_file_path, sheet_name=sheet_name)
            
            # 读取软件信息
            software_info = {
                '软件名称': str(df.iloc[0, 2]) if df.iloc[0, 2] is not None else '',
                '软件标识': str(df.iloc[3, 2]) if df.iloc[3, 2] is not None else '',
                '软件版本': str(df.iloc[8, 2]) if df.iloc[8, 2] is not None else ''
            }
            
            self.logger.info("软件配置项信息读取完成")
            return software_info
            
        except Exception as e:
            self.logger.error(f"读取软件配置项信息时发生错误: {str(e)}")
            return {'软件名称': '', '软件标识': '', '软件版本': ''}
    
    def validate_project_plan_structure(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表'
    ) -> bool:
        """
        验证回归测试项目策划表结构
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            bool: 结构是否有效
        """
        try:
            from ...utils.excel_processing.excel_reader import read_excel_with_sheet
            
            df = read_excel_with_sheet(excel_file_path, sheet_name=sheet_name)
            
            # 检查基本结构
            if df.shape[0] < 20:  # 至少需要20行
                self.logger.error("回归测试项目策划表行数不足")
                return False
            
            if df.shape[1] < 14:  # 至少需要14列
                self.logger.error("回归测试项目策划表列数不足")
                return False
            
            # 检查关键位置的数据
            try:
                len_value = df.iloc[6, 4]  # 需求变更个数
                if not isinstance(len_value, (int, float)) or len_value <= 0:
                    self.logger.error("需求变更个数无效")
                    return False
            except Exception:
                self.logger.error("无法读取需求变更个数")
                return False
            
            self.logger.info("回归测试项目策划表结构验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证回归测试项目策划表结构时发生错误: {str(e)}")
            return False
    
    def get_project_plan_summary(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表'
    ) -> Dict[str, Any]:
        """
        获取回归测试项目策划表摘要信息
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, Any]: 摘要信息
        """
        try:
            project_plan_data, status_msg = self.read_project_plan_data(excel_file_path, sheet_name)
            
            ruanjian_xuqiu = project_plan_data[0]
            ruanjian_xuqiu_biaoshi = project_plan_data[4]
            chongfu_name = project_plan_data[5]
            
            # 统计信息
            summary = {
                'total_requirements': len(ruanjian_xuqiu),
                'identified_requirements': len([x for x in ruanjian_xuqiu_biaoshi if x]),
                'duplicate_identifiers': len(chongfu_name),
                'completion_rate': 0,
                'status_message': status_msg,
                'requirements_list': ruanjian_xuqiu[:5],  # 前5个需求作为示例
                'table_type': '回归测试项目策划表'
            }
            
            # 计算完成率
            if summary['total_requirements'] > 0:
                summary['completion_rate'] = round(
                    summary['identified_requirements'] / summary['total_requirements'] * 100, 2
                )
            
            self.logger.info(f"回归测试项目策划表摘要: 共{summary['total_requirements']}个需求")
            return summary
            
        except Exception as e:
            self.logger.error(f"获取回归测试项目策划表摘要时发生错误: {str(e)}")
            return {
                'total_requirements': 0,
                'identified_requirements': 0,
                'duplicate_identifiers': 0,
                'completion_rate': 0,
                'status_message': f"读取失败: {e}",
                'requirements_list': [],
                'table_type': '回归测试项目策划表'
            }
    
    def extract_test_requirements_only(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表'
    ) -> List[str]:
        """
        仅提取测试需求列表
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            List[str]: 测试需求列表
        """
        try:
            project_plan_data, _ = self.read_project_plan_data(excel_file_path, sheet_name)
            ruanjian_xuqiu = project_plan_data[0]
            
            self.logger.info(f"提取到{len(ruanjian_xuqiu)}个测试需求")
            return ruanjian_xuqiu
            
        except Exception as e:
            self.logger.error(f"提取测试需求时发生错误: {str(e)}")
            return []
    
    def check_identifier_completeness(
        self,
        excel_file_path: str,
        sheet_name: str = '项目策划表'
    ) -> Dict[str, Any]:
        """
        检查标识完整性
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            Dict[str, Any]: 检查结果
        """
        try:
            project_plan_data, status_msg = self.read_project_plan_data(excel_file_path, sheet_name)
            
            ruanjian_xuqiu = project_plan_data[0]
            ruanjian_xuqiu_biaoshi = project_plan_data[4]
            chongfu_name = project_plan_data[5]
            
            # 检查缺失的标识
            missing_indices = []
            for i, identifier in enumerate(ruanjian_xuqiu_biaoshi):
                if not identifier or identifier.strip() == '':
                    missing_indices.append(i)
            
            # 检查结果
            result = {
                'total_requirements': len(ruanjian_xuqiu),
                'total_identifiers': len(ruanjian_xuqiu_biaoshi),
                'missing_count': len(missing_indices),
                'missing_indices': missing_indices,
                'duplicate_count': len(chongfu_name),
                'duplicate_identifiers': chongfu_name,
                'is_complete': len(missing_indices) == 0 and len(chongfu_name) == 0,
                'status_message': status_msg
            }
            
            self.logger.info(f"标识完整性检查: 缺失{result['missing_count']}个，重复{result['duplicate_count']}个")
            return result
            
        except Exception as e:
            self.logger.error(f"检查标识完整性时发生错误: {str(e)}")
            return {
                'total_requirements': 0,
                'total_identifiers': 0,
                'missing_count': 0,
                'missing_indices': [],
                'duplicate_count': 0,
                'duplicate_identifiers': [],
                'is_complete': False,
                'status_message': f"检查失败: {e}"
            }
