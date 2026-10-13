"""
数据库调试服务：专门用于调试测试项匹配问题
"""
import logging
from typing import List, Dict, Any
from ..db.crud import query_by_model
from ..db.models import SevenColsRequirement

logger = logging.getLogger(__name__)

class DatabaseDebugService:
    """数据库调试服务"""
    
    @classmethod
    def debug_test_item_matching(cls, category: str, test_item_name: str = "随动"):
        """
        调试特定测试项的匹配情况
        
        Args:
            category: 数据库类别（如"转塔"）
            test_item_name: 要调试的测试项名称
        """
        print(f"\n" + "="*80)
        print(f"🔍 调试测试项匹配情况")
        print(f"目标类别: {category}")
        print(f"目标测试项: {test_item_name}")
        print("="*80)
        
        # 查询数据库中的所有记录
        try:
            db_records = query_by_model(
                model=SevenColsRequirement,
                table=category,
                page=1,
                page_size=1000  # 获取更多记录
            )
            
            if not db_records or len(db_records) == 0:
                print("❌ 数据库中没有找到任何记录")
                return
            
            print(f"✅ 数据库中共有 {len(db_records)} 条记录")
            
            # 查找包含目标测试项的记录
            matching_records = []
            all_test_items = set()
            
            for record in db_records:
                # 转换为字典格式
                record_dict = {
                    'id': getattr(record, 'id', None),
                    'test_item_name': getattr(record, 'test_item_name', ''),
                    'test_content': getattr(record, 'test_content', ''),
                    'test_method': getattr(record, 'test_method', ''),
                    'case_template_name': getattr(record, 'case_template_name', ''),
                    'case_template_input': getattr(record, 'case_template_input', ''),
                    'case_template_expected': getattr(record, 'case_template_expected', ''),
                }
                
                test_name = record_dict['test_item_name']
                if test_name:
                    # 处理多个并列的测试项名称（用 || 分隔）
                    test_names = [name.strip() for name in str(test_name).split('||')]
                    all_test_items.update(test_names)
                    
                    # 检查是否包含目标测试项
                    if test_item_name in test_names:
                        matching_records.append(record_dict)
            
            # 显示所有测试项名称
            print(f"\n📋 数据库中所有测试项名称（共 {len(all_test_items)} 个）:")
            sorted_items = sorted(all_test_items)
            for i, item in enumerate(sorted_items, 1):
                if test_item_name in item or item in test_item_name:
                    print(f"  {i:3d}. '{item}' ⭐ (可能匹配)")
                else:
                    print(f"  {i:3d}. '{item}'")
            
            # 显示匹配的记录详情
            print(f"\n🎯 目标测试项 '{test_item_name}' 的匹配记录:")
            if not matching_records:
                print("❌ 没有找到精确匹配的记录")
                
                # 寻找可能的模糊匹配
                print(f"\n🔍 寻找包含 '{test_item_name}' 的记录:")
                fuzzy_matches = []
                for record in db_records:
                    test_name = getattr(record, 'test_item_name', '')
                    if test_name and test_item_name in str(test_name):
                        fuzzy_matches.append({
                            'id': getattr(record, 'id', None),
                            'test_item_name': test_name
                        })
                
                if fuzzy_matches:
                    for match in fuzzy_matches:
                        print(f"  - ID {match['id']}: '{match['test_item_name']}'")
                else:
                    print("  没有找到包含该名称的记录")
            else:
                for i, record in enumerate(matching_records, 1):
                    print(f"\n--- 匹配记录 {i} ---")
                    print(f"ID: {record['id']}")
                    print(f"测试项名称: '{record['test_item_name']}'")
                    print(f"测试内容: '{record['test_content'][:100]}...' (长度: {len(record['test_content'] or '')})")
                    print(f"测试方法: '{record['test_method'][:100]}...' (长度: {len(record['test_method'] or '')})")
                    print(f"用例模板名称: '{record['case_template_name'][:100]}...' (长度: {len(record['case_template_name'] or '')})")
                    print(f"用例输入条件: '{record['case_template_input'][:100]}...' (长度: {len(record['case_template_input'] or '')})")
                    print(f"用例预期结果: '{record['case_template_expected'][:100]}...' (长度: {len(record['case_template_expected'] or '')})")
                    
                    # 检查哪些字段为空
                    empty_fields = []
                    if not record['test_content']:
                        empty_fields.append('test_content')
                    if not record['test_method']:
                        empty_fields.append('test_method') 
                    if not record['case_template_name']:
                        empty_fields.append('case_template_name')
                    if not record['case_template_input']:
                        empty_fields.append('case_template_input')
                    if not record['case_template_expected']:
                        empty_fields.append('case_template_expected')
                    
                    if empty_fields:
                        print(f"⚠️ 空字段: {', '.join(empty_fields)}")
                    else:
                        print("✅ 所有字段都有内容")
            
            print("="*80)
            
        except Exception as e:
            print(f"❌ 查询数据库时出错: {str(e)}")
            logger.error(f"Database debug failed: {str(e)}")

    @classmethod 
    def debug_column_mapping(cls):
        """调试列映射情况"""
        print(f"\n" + "="*60)
        print("📋 测试用例表列映射信息")
        print("="*60)
        print("列7  (test_item_col): 测试项名称")
        print("列9  (case_name_col): 测试用例名称")  
        print("列12 (test_desc_col): 测试描述")
        print("列16 (input_condition_col): 输入条件")
        print("列17 (expected_result_col): 预期结果")
        print("="*60)
        
        print(f"\n📋 需求分析表列映射信息")
        print("="*60)
        print("列15 (test_item_col): 测试项名称")
        print("列20 (test_desc_col): 测试项描述")
        print("列21 (test_method_col): 测试方法")
        print("="*60) 