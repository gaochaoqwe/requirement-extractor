@echo off
echo 正在生成FPGA测试数据...
cd /d E:\code\requirement_extractor\backend\tests\fpgaFilter
D:\ProgramData\anaconda3\envs\aiTest_new\python.exe generate_test_excel.py
if %errorlevel% equ 0 (
    echo.
    echo ✅ Excel文件生成成功
    echo.
    echo 正在打包代码库...
    D:\ProgramData\anaconda3\envs\aiTest_new\python.exe create_test_package.py
    if %errorlevel% equ 0 (
        echo.
        echo ✅ 所有文件生成完成！
        echo.
        echo 生成的文件：
        echo   1. E:\code\requirement_extractor\T-Linter导出表单 copy.xlsx
        echo   2. E:\code\requirement_extractor\fpga_test_codebase.zip
    )
) else (
    echo ❌ 生成失败，请检查错误信息
)
pause
