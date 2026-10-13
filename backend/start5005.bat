@echo off
setlocal

chcp 65001 > nul


set "env_path=C:\ProgramData\anaconda3\envs\aiTest_new;C:\ProgramData\anaconda3\envs\aiTest_new\Scripts;C:\ProgramData\anaconda3\envs\aiTest_new\Library\bin;"
set "env_path"=%env_path%;%PATH%"

REM 使用指定conda环境的python启动FastAPI
set PYTHON_EXE=C:\ProgramData\anaconda3\envs\aiTest_new\python.exe
set MAIN_SCRIPT=D:\code\requirement_extractor\backend\run_fastapi.py

rem 设置端口 5005
set PORT=5005





%PYTHON_EXE% -X utf8 %MAIN_SCRIPT% > output5005.txt 2>&1


endlocal
