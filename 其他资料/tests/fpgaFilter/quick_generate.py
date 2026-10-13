"""快速生成测试文件"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入并运行生成脚本
from generate_test_excel import create_fpga_test_excel
from create_test_package import main as create_package

if __name__ == "__main__":
    print("=" * 60)
    print("开始生成FPGA测试文件...")
    print("=" * 60)
    
    # 生成Excel
    from pathlib import Path
    output_path = Path(__file__).parent.parent.parent.parent / "T-Linter导出表单 copy.xlsx"
    
    try:
        create_fpga_test_excel(str(output_path))
        print("\n✅ Excel文件生成成功")
    except Exception as e:
        print(f"\n❌ Excel生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 打包代码库
    print("\n" + "=" * 60)
    print("打包测试代码库...")
    print("=" * 60)
    try:
        create_package()
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
