@echo off
chcp 65001 > nul
title 深圳技术大学选课助手
color 0B

:: 设置窗口大小
mode con cols=100 lines=40

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                深圳技术大学选课助手                  ║
echo  ║                     启动程序                         ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: 检查Python环境
echo  正在检查运行环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ❌ 错误: 未安装Python或Python未添加到系统路径
    echo  请访问 https://www.python.org/downloads/ 下载并安装Python 3.8或更高版本
    echo.
    pause
    exit /b 1
)

:: 检查依赖包
echo  正在检查依赖包...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo  ⚠️ 警告: 部分依赖包安装失败，程序可能无法正常运行
) else (
    echo  ✅ 依赖包检查完成
)

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                    启动模式选择                      ║
echo  ╠══════════════════════════════════════════════════════╣
echo  ║                                                      ║
echo  ║  [1] 正常模式    - 显示浏览器界面                  ║
echo  ║  [2] 调试模式    - 输出详细日志信息                ║
echo  ║  [3] 无界面模式  - 后台静默运行                    ║
echo  ║                                                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

set /p choice=👉 请选择启动模式 (1-3): 

if "%choice%"=="1" (
    echo.
    echo  ℹ️ 正在以正常模式启动...
    python run.py
) else if "%choice%"=="2" (
    echo.
    echo  ℹ️ 正在以调试模式启动...
    python run.py --debug
) else if "%choice%"=="3" (
    echo.
    echo  ℹ️ 正在以无界面模式启动...
    python run.py --headless
) else (
    echo.
    echo  ⚠️ 无效的选择，将以正常模式启动...
    python run.py
)

if errorlevel 1 (
    echo.
    echo  ❌ 程序运行出错，请检查日志文件了解详细信息
    echo.
    pause
) else (
    echo.
    echo  ✅ 程序运行完成
    echo.
    pause
) 