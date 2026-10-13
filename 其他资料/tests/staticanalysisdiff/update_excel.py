"""
更新Excel文件，填入10个精心设计的静态分析问题
包含3个真实问题和7个误报
"""
import sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill

# Excel文件路径
EXCEL_PATH = Path(r"D:\code\requirement_extractor\静态科代导出原始表单格式 - 最终测试10问题.xlsx")

# 10个问题的详细信息
ISSUES = [
    # ===== 真实问题 (3个) =====
    {
        "序号": 1,
        "问题名称": "GJB_R_01_06_08数组禁止越界使用",  # ✅ 使用数据库中的完整名称
        "问题文件": "user_manager.c",
        "问题行号": 42,
        "问题描述": "函数get_user_by_id中，仅检查了user_id >= 0，未检查上界，当user_id >= MAX_USERS时会访问数组外内存",
        "所属规则": "GJB_R_01_06_08",
        "规则名称": "GJB_R_01_06_08数组禁止越界使用",
        "规则类型": "uncertain",
        "is_real": True,
        "reason": "真实问题 - 边界检查不完整"
    },
    {
        "序号": 2,
        "问题名称": "GJB_R_01_06_19使用字符串赋值、拷贝、追加等函数时，禁止目标字符串储存空间越界",  # ✅ 使用更准确的规则
        "问题文件": "message_handler.c",
        "问题行号": 27,
        "问题描述": "函数send_message中使用strcpy复制content到msg->content，未检查源字符串长度，可能导致缓冲区溢出",
        "所属规则": "GJB_R_01_06_19",
        "规则名称": "GJB_R_01_06_19使用字符串赋值、拷贝、追加等函数时，禁止目标字符串储存空间越界",
        "规则类型": "uncertain",
        "is_real": True,
        "reason": "真实问题 - 缺少长度检查"
    },
    {
        "序号": 3,
        "问题名称": "GJB_R_01_03_05禁止使用或释放未分配空间或已被释放的指针",  # ✅ 使用数据库中的完整名称
        "问题文件": "user_manager.c",
        "问题行号": 42,
        "问题描述": "函数get_user_by_id可能返回指向数组外的指针，调用者使用该指针会导致未定义行为",
        "所属规则": "GJB_R_01_03_05",
        "规则名称": "GJB_R_01_03_05禁止使用或释放未分配空间或已被释放的指针",
        "规则类型": "uncertain",
        "is_real": True,
        "reason": "真实问题 - 指针可能无效"
    },
    
    # ===== 误报问题 (7个) =====
    {
        "序号": 4,
        "问题名称": "GJB_R_01_06_08数组禁止越界使用",  # ✅ 使用数据库中的完整名称
        "问题文件": "user_manager.c",
        "问题行号": 56,
        "问题描述": "函数get_active_user_count中循环访问g_users数组，看起来g_user_count可能超过MAX_USERS导致越界",
        "所属规则": "GJB_R_01_06_08",
        "规则名称": "GJB_R_01_06_08数组禁止越界使用",
        "规则类型": "uncertain",
        "is_real": False,
        "reason": "误报 - add_user函数保证g_user_count <= MAX_USERS"
    },
    {
        "序号": 5,
        "问题名称": "GJB_R_01_08_02禁止不可达分支",  # ✅ 使用数据库中的完整名称（不可达分支）
        "问题文件": "user_manager.c",
        "问题行号": 68,
        "问题描述": "函数deactivate_user中检查user_id >= MAX_USERS看起来不可达，因为之前已检查user_id < g_user_count",
        "所属规则": "GJB_R_01_08_02",
        "规则名称": "GJB_R_01_08_02禁止不可达分支",
        "规则类型": "uncertain",
        "is_real": False,
        "reason": "误报 - 由于get_user_by_id有bug，这个检查是必要的防御性编程"
    },
    {
        "序号": 6,
        "问题名称": "GJB_R_01_06_19使用字符串赋值、拷贝、追加等函数时，禁止目标字符串储存空间越界",  # ✅ 使用数据库中的完整名称
        "问题文件": "message_handler.c",
        "问题行号": 50,
        "问题描述": "函数send_safe_message中使用safe_string_copy复制字符串，看起来可能有缓冲区溢出风险",
        "所属规则": "GJB_R_01_06_19",
        "规则名称": "GJB_R_01_06_19使用字符串赋值、拷贝、追加等函数时，禁止目标字符串储存空间越界",
        "规则类型": "uncertain",
        "is_real": False,
        "reason": "误报 - safe_string_copy函数实现了边界检查（见globals.c:67）"
    },
    {
        "序号": 7,
        "问题名称": "GJB_R_01_11_01变量禁止未赋值就使用",  # ✅ 使用数据库中的完整名称
        "问题文件": "data_processor.c",
        "问题行号": 15,
        "问题描述": "函数process_user_data中变量result看起来未初始化就使用",
        "所属规则": "GJB_R_01_11_01",
        "规则名称": "GJB_R_01_11_01变量禁止未赋值就使用",
        "规则类型": "uncertain",
        "is_real": False,
        "reason": "误报 - 所有if-else分支都会初始化result变量"
    },
    {
        "序号": 8,
        "问题名称": "GJB_R_01_06_08数组禁止越界使用",  # ✅ 使用数据库中的完整名称
        "问题文件": "data_processor.c",
        "问题行号": 38,
        "问题描述": "函数initialize_buffer_array中访问buffers[SMALL_BUFFER_SIZE-1][TINY_BUFFER_SIZE-1]看起来可能越界",
        "所属规则": "GJB_R_01_06_08",
        "规则名称": "GJB_R_01_06_08数组禁止越界使用",
        "规则类型": "uncertain",
        "is_real": False,
        "reason": "误报 - SMALL_BUFFER_SIZE=64, TINY_BUFFER_SIZE=16，数组定义匹配"
    },
    {
        "序号": 9,
        "问题名称": "GJB_R_01_06_08数组禁止越界使用",  # ✅ 使用数据库中的完整名称
        "问题文件": "validator.c",
        "问题行号": 14,
        "问题描述": "函数validate_and_access_user中访问g_users[index]看起来没有边界检查",
        "所属规则": "GJB_R_01_06_08",
        "规则名称": "GJB_R_01_06_08数组禁止越界使用",
        "规则类型": "uncertain",
        "is_real": False,
        "reason": "误报 - validate_user_index函数（globals.c:53）已做完整边界检查"
    },
    {
        "序号": 10,
        "问题名称": "GJB_R_01_06_08数组禁止越界使用",  # ✅ 使用数据库中的完整名称
        "问题文件": "validator.c",
        "问题行号": 45,
        "问题描述": "函数reset_all_users中循环到MAX_USERS，看起来会访问g_users[MAX_USERS]越界",
        "所属规则": "GJB_R_01_06_08",
        "规则名称": "GJB_R_01_06_08数组禁止越界使用",
        "规则类型": "uncertain",
        "is_real": False,
        "reason": "误报 - g_users数组大小就是MAX_USERS（global_config.h:44）"
    }
]

def update_excel():
    """更新Excel文件"""
    print(f"开始更新Excel文件: {EXCEL_PATH}")
    
    if not EXCEL_PATH.exists():
        print(f"❌ 错误: Excel文件不存在: {EXCEL_PATH}")
        return False
    
    try:
        # 打开工作簿
        wb = openpyxl.load_workbook(EXCEL_PATH)
        print(f"✅ 成功打开Excel文件")
        
        # 获取第一个工作表
        ws = wb.active
        print(f"✅ 当前工作表: {ws.title}")
        
        # 查找表头行（假设在第1行）
        headers = []
        for col in range(1, 20):  # 检查前20列
            cell_value = ws.cell(1, col).value
            if cell_value:
                headers.append((col, str(cell_value).strip()))
        
        print(f"✅ 找到 {len(headers)} 个列标题:")
        for col, header in headers:
            print(f"   列{col}: {header}")
        
        # 创建列名到列号的映射
        col_map = {}
        for col, header in headers:
            # 匹配可能的列名变体
            if '序号' in header or 'ID' in header.upper():
                col_map['序号'] = col
            elif '问题名称' in header or '名称' in header:
                col_map['问题名称'] = col
            elif '问题文件' in header or '文件' in header:
                col_map['问题文件'] = col
            elif '问题行号' in header or '行号' in header:
                col_map['问题行号'] = col
            elif '问题描述' in header or '描述' in header:
                col_map['问题描述'] = col
            elif '所属规则' in header or '规则编号' in header or '规则代码' in header:
                col_map['所属规则'] = col
            elif '规则名称' in header:
                col_map['规则名称'] = col
            elif '规则类型' in header or '类型' in header:
                col_map['规则类型'] = col
        
        print(f"\n✅ 列映射:")
        for key, col in col_map.items():
            print(f"   {key} -> 列{col}")
        
        # 填充数据（从第2行开始）
        print(f"\n开始填充 {len(ISSUES)} 个问题...")
        
        # 定义颜色
        real_fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")  # 淡红色
        false_fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")  # 淡绿色
        
        for idx, issue in enumerate(ISSUES, start=2):
            row = idx
            
            # 填充基本列（根据实际Excel列结构）
            ws.cell(row, 1, issue['序号'])  # 编号
            ws.cell(row, 2, "待处理" if issue['is_real'] else "误报")  # 缺陷处理结果
            ws.cell(row, 3, issue['序号'])  # CWEId号
            ws.cell(row, 4, issue['问题名称'])  # 缺陷名称
            ws.cell(row, 5, "是")  # 是否是新问题
            ws.cell(row, 6, "高" if issue['is_real'] else "中")  # 缺陷等级
            ws.cell(row, 7, "2025-10-15 10:13:04")  # 发现时间
            ws.cell(row, 8, "test_developer")  # git提交人
            ws.cell(row, 9, "待分配")  # 负责人
            ws.cell(row, 10, "GJB8114静态分析工具")  # 检测器
            ws.cell(row, 11, issue['问题文件'])  # 文件路径
            ws.cell(row, 12, issue['问题行号'])  # 行号
            ws.cell(row, 13, issue['问题描述'])  # 缺陷说明
            
            # 根据是否是真实问题设置行颜色
            fill = real_fill if issue['is_real'] else false_fill
            for col in range(1, len(headers) + 1):
                ws.cell(row, col).fill = fill
            
            status = "✅ 真实问题" if issue['is_real'] else "❌ 误报"
            print(f"  行{row}: {status} - {issue['问题名称']} ({issue['问题文件']}:{issue['问题行号']})")
        
        # 保存文件
        wb.save(EXCEL_PATH)
        print(f"\n✅ 成功保存Excel文件!")
        
        # 统计
        real_count = sum(1 for issue in ISSUES if issue['is_real'])
        false_count = len(ISSUES) - real_count
        
        print(f"\n" + "="*80)
        print(f"📊 统计信息:")
        print(f"  总问题数: {len(ISSUES)}")
        print(f"  真实问题: {real_count} (淡红色背景)")
        print(f"  误报问题: {false_count} (淡绿色背景)")
        print(f"="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_excel()
    sys.exit(0 if success else 1)

