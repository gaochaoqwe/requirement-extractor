@echo off
setlocal

chcp 65001 > nul

set "env_path=C:\ProgramData\anaconda3\envs\aiTest_new;C:\ProgramData\anaconda3\envs\aiTest_new\Scripts;C:\ProgramData\anaconda3\envs\aiTest_new\Library\bin;"
set "env_path=%env_path%;%PATH%"

set PYTHON_EXE=C:\ProgramData\anaconda3\envs\aiTest_new\python.exe

echo ========================================
echo  初始化静态分析数据库（C + FPGA）
echo ========================================
echo.

echo [1/4] 初始化工具模式C规则表（filter）...
%PYTHON_EXE% -X utf8 "%~dp0app\staticAnalysis\filter\database\init_postgresql.py" --yes
if %errorlevel% neq 0 (
    echo [ERROR] filter 初始化失败，终止执行
    pause
    exit /b 1
)
echo.

echo [2/4] 初始化普通模式C分析表（normalModeC）...
%PYTHON_EXE% -X utf8 "%~dp0app\staticAnalysis\normalModeC\database\init_postgresql.py" --yes
if %errorlevel% neq 0 (
    echo [ERROR] normalModeC 初始化失败
    pause
    exit /b 1
)
echo.

echo [3/4] 初始化工具模式FPGA规则表（filterFpga）...
%PYTHON_EXE% -X utf8 "%~dp0app\staticAnalysis\filterFpga\database\init_postgresql.py" --yes
if %errorlevel% neq 0 (
    echo [ERROR] filterFpga 初始化失败
    pause
    exit /b 1
)
echo.

echo [4/4] 初始化普通模式FPGA分析表（normalModeFpga）...
%PYTHON_EXE% -X utf8 "%~dp0app\staticAnalysis\normalModeFpga\database\init_postgresql.py" --yes
if %errorlevel% neq 0 (
    echo [ERROR] normalModeFpga 初始化失败
    pause
    exit /b 1
)
echo.

echo ========================================
echo  所有数据库初始化完成！
echo ========================================
echo.
echo 已初始化：
echo   1. static_analysis_filter 数据库（C语言）
echo      - 工具模式: gjb8114_rules, cwe_rules, static_analysis_sessions 等 6 张表
echo      - 普通模式: nm_analysis_tasks/files/functions/problems 4 张表
echo.
echo   2. fpga_static_analysis_filter 数据库（FPGA）
echo      - 工具模式: fpga_rules, static_analysis_sessions 等表
echo      - 普通模式: nm_fpga_analysis_tasks/files/functions/problems 4 张表
echo.
pause
endlocal
