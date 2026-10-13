"""
配置项测试标识生成器

负责生成配置项测试中的英文标识和测试类型标识。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class ConfigurationItemTestIdentifierGenerator:
    """配置项测试标识生成器"""
    
    def __init__(self):
        """初始化标识生成器"""
        self.logger = logger
        self.keyword_mapping = self._get_keyword_mapping()
        self.test_type_mapping = self._get_test_type_mapping()
    
    def generate_english_identifiers(
        self,
        test_item_names: List[str],
        use_ai_translation: bool = False
    ) -> List[str]:
        """
        生成英文标识列表（ai_translation模块已删除）
        
        Args:
            test_item_names: 测试项名称列表
            use_ai_translation: 保留参数，但AI翻译功能已删除
            
        Returns:
            List[str]: 英文标识列表
        """
        try:
            self.logger.info(f"开始生成{len(test_item_names)}个英文标识")
            
            identifiers = []
            used_identifiers = set()
            
            for i, test_item_name in enumerate(test_item_names):
                identifier = self._generate_single_identifier(
                    test_item_name, 
                    use_ai_translation,
                    used_identifiers,
                    i
                )
                identifiers.append(identifier)
                used_identifiers.add(identifier)
            
            self.logger.info("英文标识生成完成")
            return identifiers
            
        except Exception as e:
            self.logger.error(f"生成英文标识时发生错误: {str(e)}")
            return [f'SRC-name{i}' for i in range(len(test_item_names))]
    
    def _generate_single_identifier(
        self,
        test_item_name: str,
        use_ai_translation: bool,
        used_identifiers: set,
        index: int
    ) -> str:
        """生成单个英文标识"""
        try:
            # AI翻译功能已删除，直接跳过AI翻译步骤
            # if use_ai_translation:
            #     ai_identifier = self._try_ai_translation(test_item_name)
            #     if ai_identifier and ai_identifier not in used_identifiers:
            #         return ai_identifier
            
            # 使用关键词映射
            keyword_identifier = self._generate_by_keywords(test_item_name)
            if keyword_identifier not in used_identifiers:
                return keyword_identifier
            
            # 生成唯一标识
            return self._generate_unique_identifier(test_item_name, used_identifiers, index)
            
        except Exception as e:
            self.logger.error(f"生成单个标识时发生错误: {str(e)}")
            return f'SRC-name{index}'
    
    def _try_ai_translation(self, test_item_name: str) -> Optional[str]:
        """尝试AI翻译"""
        try:
            # AI翻译模块已删除，直接返回None让调用方使用备选方案
            # 这里原来调用translate_chinese_to_english，现在不需要了
            return None
            
            return None
            
        except Exception as e:
            self.logger.warning(f"AI翻译失败: {str(e)}")
            return None
    
    def _generate_by_keywords(self, test_item_name: str) -> str:
        """基于关键词生成标识"""
        # 查找匹配的关键词
        for chinese_keyword, english_keyword in self.keyword_mapping.items():
            if chinese_keyword in test_item_name:
                return f'{english_keyword}Test'
        
        # 如果没有匹配的关键词，使用哈希值
        hash_value = abs(hash(test_item_name)) % 1000
        return f'TestItem{hash_value}'
    
    def _generate_unique_identifier(
        self,
        test_item_name: str,
        used_identifiers: set,
        index: int
    ) -> str:
        """生成唯一标识"""
        base_identifier = f'SRC-name{index}'
        counter = 0
        
        while base_identifier in used_identifiers:
            counter += 1
            base_identifier = f'SRC-name{index}-{counter}'
        
        return base_identifier
    
    def _clean_identifier(self, identifier: str) -> str:
        """清理标识符，确保符合规范"""
        # 移除特殊字符，只保留字母、数字和连字符
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9\-_]', '', identifier)
        
        # 确保不为空
        if not cleaned:
            return 'DefaultIdentifier'
        
        # 确保以字母开头
        if not cleaned[0].isalpha():
            cleaned = 'ID' + cleaned
        
        return cleaned
    
    def generate_test_type_identifiers(self, test_item_names: List[str]) -> List[str]:
        """
        生成测试类型标识列表
        
        Args:
            test_item_names: 测试项名称列表
            
        Returns:
            List[str]: 测试类型标识列表
        """
        try:
            self.logger.info(f"开始生成{len(test_item_names)}个测试类型标识")
            
            type_identifiers = []
            
            for test_item_name in test_item_names:
                type_identifier = self._get_test_type_identifier(test_item_name)
                type_identifiers.append(type_identifier)
            
            self.logger.info("测试类型标识生成完成")
            return type_identifiers
            
        except Exception as e:
            self.logger.error(f"生成测试类型标识时发生错误: {str(e)}")
            return ['FN'] * len(test_item_names)  # 默认为功能测试
    
    def _get_test_type_identifier(self, test_item_name: str) -> str:
        """获取测试类型标识"""
        # 根据关键词匹配测试类型
        for keyword, type_info in self.test_type_mapping.items():
            if keyword in test_item_name:
                return type_info['code']
        
        # 默认返回功能测试
        return 'FN'
    
    def _get_keyword_mapping(self) -> Dict[str, str]:
        """获取关键词映射"""
        return {
            '功能': 'Function',
            '接口': 'Interface',
            '性能': 'Performance',
            '数据': 'Data',
            '处理': 'Process',
            '控制': 'Control',
            '管理': 'Management',
            '监控': 'Monitor',
            '检测': 'Detection',
            '故障': 'Fault',
            '报警': 'Alarm',
            '通信': 'Communication',
            '显示': 'Display',
            '输入': 'Input',
            '输出': 'Output',
            '配置': 'Config',
            '初始化': 'Init',
            '启动': 'Start',
            '停止': 'Stop',
            '重启': 'Restart',
            '更新': 'Update',
            '删除': 'Delete',
            '创建': 'Create',
            '修改': 'Modify',
            '查询': 'Query',
            '搜索': 'Search',
            '过滤': 'Filter',
            '排序': 'Sort',
            '验证': 'Validate',
            '校验': 'Check',
            '计算': 'Calculate',
            '统计': 'Statistics',
            '分析': 'Analysis',
            '解析': 'Parse',
            '转换': 'Convert',
            '格式化': 'Format',
            '压缩': 'Compress',
            '解压': 'Decompress',
            '加密': 'Encrypt',
            '解密': 'Decrypt',
            '备份': 'Backup',
            '恢复': 'Restore',
            '同步': 'Sync',
            '异步': 'Async',
            '并发': 'Concurrent',
            '串行': 'Serial',
            '并行': 'Parallel',
            '队列': 'Queue',
            '栈': 'Stack',
            '缓存': 'Cache',
            '存储': 'Storage',
            '读取': 'Read',
            '写入': 'Write',
            '上传': 'Upload',
            '下载': 'Download',
            '发送': 'Send',
            '接收': 'Receive',
            '传输': 'Transfer',
            '连接': 'Connect',
            '断开': 'Disconnect',
            '重连': 'Reconnect',
            '超时': 'Timeout',
            '重试': 'Retry',
            '异常': 'Exception',
            '错误': 'Error',
            '警告': 'Warning',
            '信息': 'Info',
            '调试': 'Debug',
            '日志': 'Log',
            '记录': 'Record',
            '跟踪': 'Trace',
            '监听': 'Listen',
            '观察': 'Observe',
            '通知': 'Notify',
            '事件': 'Event',
            '消息': 'Message',
            '信号': 'Signal',
            '状态': 'Status',
            '模式': 'Mode',
            '参数': 'Parameter',
            '配置': 'Config',
            '设置': 'Setting',
            '选项': 'Option',
            '属性': 'Property',
            '字段': 'Field',
            '变量': 'Variable',
            '常量': 'Constant',
            '枚举': 'Enum',
            '结构': 'Struct',
            '类型': 'Type',
            '对象': 'Object',
            '实例': 'Instance',
            '引用': 'Reference',
            '指针': 'Pointer',
            '地址': 'Address',
            '内存': 'Memory',
            '资源': 'Resource',
            '句柄': 'Handle',
            '标识': 'Identifier',
            '编号': 'Number',
            '序号': 'Serial',
            '索引': 'Index',
            '键': 'Key',
            '值': 'Value',
            '映射': 'Map',
            '字典': 'Dict',
            '列表': 'List',
            '数组': 'Array',
            '集合': 'Set',
            '树': 'Tree',
            '图': 'Graph',
            '节点': 'Node',
            '边': 'Edge',
            '路径': 'Path',
            '算法': 'Algorithm',
            '策略': 'Strategy',
            '模式': 'Pattern',
            '模板': 'Template',
            '框架': 'Framework',
            '库': 'Library',
            '模块': 'Module',
            '组件': 'Component',
            '服务': 'Service',
            '客户端': 'Client',
            '服务器': 'Server',
            '代理': 'Proxy',
            '网关': 'Gateway',
            '路由': 'Router',
            '负载': 'Load',
            '均衡': 'Balance',
            '集群': 'Cluster',
            '节点': 'Node',
            '主机': 'Host',
            '端口': 'Port',
            '协议': 'Protocol',
            '格式': 'Format',
            '编码': 'Encoding',
            '解码': 'Decoding',
            '序列化': 'Serialize',
            '反序列化': 'Deserialize'
        }
    
    def _get_test_type_mapping(self) -> Dict[str, Dict[str, str]]:
        """获取测试类型映射"""
        return {
            '功能': {'code': 'FN', 'name': '功能测试'},
            '接口': {'code': 'IF', 'name': '接口测试'},
            '性能': {'code': 'PF', 'name': '性能测试'},
            '数据': {'code': 'DT', 'name': '数据测试'},
            '处理': {'code': 'PR', 'name': '处理测试'},
            '控制': {'code': 'CT', 'name': '控制测试'},
            '管理': {'code': 'MG', 'name': '管理测试'},
            '监控': {'code': 'MN', 'name': '监控测试'},
            '检测': {'code': 'DT', 'name': '检测测试'},
            '故障': {'code': 'FT', 'name': '故障测试'},
            '报警': {'code': 'AL', 'name': '报警测试'},
            '通信': {'code': 'CM', 'name': '通信测试'},
            '显示': {'code': 'DS', 'name': '显示测试'},
            '输入': {'code': 'IN', 'name': '输入测试'},
            '输出': {'code': 'OUT', 'name': '输出测试'},
            '配置': {'code': 'CF', 'name': '配置测试'},
            '初始化': {'code': 'INIT', 'name': '初始化测试'},
            '启动': {'code': 'START', 'name': '启动测试'},
            '停止': {'code': 'STOP', 'name': '停止测试'},
            '重启': {'code': 'RESTART', 'name': '重启测试'},
            '更新': {'code': 'UPDATE', 'name': '更新测试'},
            '删除': {'code': 'DELETE', 'name': '删除测试'},
            '创建': {'code': 'CREATE', 'name': '创建测试'},
            '修改': {'code': 'MODIFY', 'name': '修改测试'},
            '查询': {'code': 'QUERY', 'name': '查询测试'},
            '搜索': {'code': 'SEARCH', 'name': '搜索测试'},
            '验证': {'code': 'VALIDATE', 'name': '验证测试'},
            '校验': {'code': 'CHECK', 'name': '校验测试'},
            '计算': {'code': 'CALC', 'name': '计算测试'},
            '统计': {'code': 'STAT', 'name': '统计测试'},
            '分析': {'code': 'ANALYZE', 'name': '分析测试'},
            '解析': {'code': 'PARSE', 'name': '解析测试'},
            '转换': {'code': 'CONVERT', 'name': '转换测试'},
            '格式化': {'code': 'FORMAT', 'name': '格式化测试'},
            '压缩': {'code': 'COMPRESS', 'name': '压缩测试'},
            '解压': {'code': 'DECOMPRESS', 'name': '解压测试'},
            '加密': {'code': 'ENCRYPT', 'name': '加密测试'},
            '解密': {'code': 'DECRYPT', 'name': '解密测试'},
            '备份': {'code': 'BACKUP', 'name': '备份测试'},
            '恢复': {'code': 'RESTORE', 'name': '恢复测试'},
            '同步': {'code': 'SYNC', 'name': '同步测试'},
            '异步': {'code': 'ASYNC', 'name': '异步测试'},
            '并发': {'code': 'CONCURRENT', 'name': '并发测试'},
            '串行': {'code': 'SERIAL', 'name': '串行测试'},
            '并行': {'code': 'PARALLEL', 'name': '并行测试'},
            '存储': {'code': 'STORAGE', 'name': '存储测试'},
            '读取': {'code': 'READ', 'name': '读取测试'},
            '写入': {'code': 'WRITE', 'name': '写入测试'},
            '上传': {'code': 'UPLOAD', 'name': '上传测试'},
            '下载': {'code': 'DOWNLOAD', 'name': '下载测试'},
            '发送': {'code': 'SEND', 'name': '发送测试'},
            '接收': {'code': 'RECEIVE', 'name': '接收测试'},
            '传输': {'code': 'TRANSFER', 'name': '传输测试'},
            '连接': {'code': 'CONNECT', 'name': '连接测试'},
            '断开': {'code': 'DISCONNECT', 'name': '断开测试'},
            '重连': {'code': 'RECONNECT', 'name': '重连测试'},
            '超时': {'code': 'TIMEOUT', 'name': '超时测试'},
            '重试': {'code': 'RETRY', 'name': '重试测试'},
            '异常': {'code': 'EXCEPTION', 'name': '异常测试'},
            '错误': {'code': 'ERROR', 'name': '错误测试'}
        }
    
    def validate_identifiers(self, identifiers: List[str]) -> Tuple[bool, List[str]]:
        """
        验证标识符的有效性和唯一性
        
        Args:
            identifiers: 标识符列表
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 重复的标识符列表)
        """
        try:
            # 检查重复
            seen = set()
            duplicates = []
            
            for identifier in identifiers:
                if identifier in seen:
                    duplicates.append(identifier)
                else:
                    seen.add(identifier)
            
            # 检查格式有效性
            import re
            valid_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9\-_]*$')
            
            for identifier in identifiers:
                if not valid_pattern.match(identifier):
                    self.logger.error(f"标识符格式无效: {identifier}")
                    return False, duplicates
            
            is_valid = len(duplicates) == 0
            if not is_valid:
                self.logger.warning(f"发现重复标识符: {duplicates}")
            
            return is_valid, duplicates
            
        except Exception as e:
            self.logger.error(f"验证标识符时发生错误: {str(e)}")
            return False, []
    
    def fix_duplicate_identifiers(self, identifiers: List[str]) -> List[str]:
        """
        修复重复的标识符
        
        Args:
            identifiers: 原始标识符列表
            
        Returns:
            List[str]: 修复后的标识符列表
        """
        try:
            fixed_identifiers = []
            seen = set()
            
            for identifier in identifiers:
                if identifier not in seen:
                    fixed_identifiers.append(identifier)
                    seen.add(identifier)
                else:
                    # 生成唯一标识符
                    counter = 1
                    new_identifier = f"{identifier}-{counter}"
                    while new_identifier in seen:
                        counter += 1
                        new_identifier = f"{identifier}-{counter}"
                    
                    fixed_identifiers.append(new_identifier)
                    seen.add(new_identifier)
            
            self.logger.info("重复标识符修复完成")
            return fixed_identifiers
            
        except Exception as e:
            self.logger.error(f"修复重复标识符时发生错误: {str(e)}")
            return identifiers
