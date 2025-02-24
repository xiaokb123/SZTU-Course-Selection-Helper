import os
import shutil
import subprocess
import sys
from pathlib import Path

def clean_build_files():
    """清理旧的构建文件"""
    print("清理旧的构建文件...")
    paths_to_remove = ['build', 'dist', '*.spec']
    for path in paths_to_remove:
        for p in Path('.').glob(path):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)

def check_requirements():
    """检查必要的依赖是否安装"""
    print("检查依赖...")
    required_packages = ['pyinstaller', 'selenium', 'python-dotenv', 'loguru', 'webdriver_manager']
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"正在安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def build_executable():
    """使用PyInstaller打包程序"""
    print("开始打包程序...")
    
    cmd = [
        "pyinstaller",
        "--clean",
        "--add-data", "requirements.txt;.",
        "--add-data", "config.py;.",
        "--add-data", "auto_course.py;.",
        "--add-data", "README.md;.",
        "--hidden-import", "selenium",
        "--hidden-import", "webdriver_manager",
        "--hidden-import", "dotenv",
        "--hidden-import", "loguru",
        "--hidden-import", "requests",
        "--hidden-import", "urllib3",
        "--hidden-import", "certifi",
        "--hidden-import", "charset_normalizer",
        "--name", "SZTU选课助手",
        "--noconsole",
        "--onefile",
        "run.py"
    ]
    
    # 如果存在图标文件，添加图标
    if os.path.exists("icon.ico"):
        cmd.extend(["--icon", "icon.ico"])
    
    try:
        subprocess.check_call(cmd)
        exe_path = os.path.join("dist", "SZTU选课助手.exe")
        if os.path.exists(exe_path):
            print("\n打包成功！")
            print(f"程序位置: {exe_path}")
        else:
            print("\n打包似乎完成，但未找到输出文件")
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        sys.exit(1)

def main():
    print("=== SZTU选课助手打包工具 ===\n")
    
    try:
        clean_build_files()
        check_requirements()
        build_executable()
    except Exception as e:
        print(f"\n发生错误: {e}")
        sys.exit(1)
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main() 