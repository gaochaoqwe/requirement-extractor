"""
创建FPGA测试包（包含Excel和代码库zip）
"""
import zipfile
import shutil
from pathlib import Path


def create_codebase_zip():
    """将测试代码打包成zip"""
    test_dir = Path(__file__).parent
    codebase_dir = test_dir / "test_codebase"
    output_zip = test_dir.parent.parent.parent / "fpga_test_codebase.zip"
    
    if not codebase_dir.exists():
        print(f"❌ 代码库目录不存在: {codebase_dir}")
        return False
    
    # 创建zip文件
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in codebase_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(codebase_dir)
                zipf.write(file_path, arcname)
                print(f"  添加文件: {arcname}")
    
    print(f"\n✅ 代码库已打包: {output_zip}")
    print(f"   - 文件大小: {output_zip.stat().st_size / 1024:.2f} KB")
    return True


def verify_test_files():
    """验证测试文件是否完整"""
    test_dir = Path(__file__).parent
    codebase_dir = test_dir / "test_codebase"
    
    expected_files = [
        "clock_divider.v",
        "counter.v",
        "state_machine.v",
        "alu.v",
        "fifo.v",
        "memory_ctrl.v",
        "data_path.v",
        "uart_tx.v",
        "spi_master.v",
        "i2c_slave.v",
        "pipeline.v",
        "arbiter.v",
        "decoder.v",
        "encoder.v",
        "multiplier.v",
        "divider.v",
        "controller.vhd",
        "processor.vhd",
        "bus_interface.v",
        "dma_ctrl.v",
    ]
    
    print("\n📋 验证测试文件...")
    missing_files = []
    for filename in expected_files:
        file_path = codebase_dir / filename
        if file_path.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} (缺失)")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n❌ 缺少 {len(missing_files)} 个文件")
        return False
    else:
        print(f"\n✅ 所有 {len(expected_files)} 个测试文件完整")
        return True


def main():
    print("=" * 60)
    print("FPGA 测试包创建工具")
    print("=" * 60)
    
    # 验证文件
    if not verify_test_files():
        print("\n⚠️  部分文件缺失，但继续打包...")
    
    # 创建代码库zip
    print("\n" + "=" * 60)
    print("打包代码库...")
    print("=" * 60)
    if create_codebase_zip():
        print("\n" + "=" * 60)
        print("✅ 测试包创建完成！")
        print("=" * 60)
        print("\n📦 生成的文件:")
        test_dir = Path(__file__).parent
        print(f"  1. Excel测试数据: {test_dir.parent.parent.parent / 'T-Linter导出表单 copy.xlsx'}")
        print(f"  2. 代码库zip:     {test_dir.parent.parent.parent / 'fpga_test_codebase.zip'}")
        print("\n🚀 现在可以上传这两个文件到前端界面进行测试！")
    else:
        print("\n❌ 打包失败")


if __name__ == "__main__":
    main()
