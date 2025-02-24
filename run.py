import os
import sys
import json
import argparse
import tempfile
from getpass import getpass
from datetime import datetime
from auto_course import CourseSelector, logger
from config import CourseConfig

def get_resource_path(relative_path):
    """获取资源文件的路径（支持打包后的路径）"""
    try:
        # PyInstaller创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_argparse():
    """设置命令行参数"""
    parser = argparse.ArgumentParser(description='深圳技术大学自动选课程序')
    parser.add_argument('-c', '--config', help='课程配置文件路径（JSON格式）')
    parser.add_argument('-u', '--username', help='学号')
    parser.add_argument('-p', '--password', help='密码')
    parser.add_argument('--headless', action='store_true', help='无界面模式运行')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    return parser.parse_args()

def create_env_file(username, password):
    """创建或更新.env文件"""
    try:
        # 直接在当前目录创建.env文件
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(f"STUDENT_ID={username}\n")
            f.write(f"PASSWORD={password}\n")
        print("\n✅ 登录信息已保存到 .env 文件")
        return True
    except Exception as e:
        print(f"\n❌ 保存登录信息失败: {str(e)}")
        return False

def get_app_data_dir():
    """获取应用数据目录"""
    app_data = os.path.join(os.getenv('APPDATA') or tempfile.gettempdir(), 'SZTU选课助手')
    os.makedirs(app_data, exist_ok=True)
    return app_data

def get_credentials():
    """交互式获取登录凭证"""
    print("\n=== 登录信息配置 ===")
    username = input("请输入学号: ").strip()
    password = getpass("请输入密码(初始密码为Sztu@身份证后六位): ").strip()
        
    return username, password

def create_course_config():
    """交互式创建课程配置"""
    courses = []
    print("\n=== 课程配置 ===")
    
    while True:
        print("\n添加新课程:")
        course = {}
        course["course_id"] = input("课程ID (可选): ").strip()
        course["course_name"] = input("课程名称: ").strip()
        course["teacher"] = input("教师姓名: ").strip()
        
        # 选择星期
        print("\n选择上课星期:")
        print("1. 星期一  2. 星期二  3. 星期三")
        print("4. 星期四  5. 星期五  6. 星期六  7. 星期日")
        weekday = input("请输入数字(1-7): ").strip()
        weekday_map = {
            "1": "周一", "2": "周二", "3": "周三",
            "4": "周四", "5": "周五", "6": "周六", "7": "周日"
        }
        course["time"] = weekday_map.get(weekday, "周一")
        
        # 选择节次
        print("\n是否限制上课节次?")
        print("1. 不限制")
        print("2. 指定节次")
        section_choice = input("请选择 (1/2): ").strip()
        if section_choice == "2":
            start = input("开始节次 (1-12): ").strip()
            end = input("结束节次 (1-12): ").strip()
            course["section"] = f"{start}-{end}"
        else:
            course["section"] = "NO"
        
        # 选择选课类型
        print("\n选择选课类型:")
        print("1. 本学期计划选课 (plan)")
        print("2. 公选课选课 (public)")
        print("3. 专业内跨年级选课 (cross_grade)")
        print("4. 跨专业选课 (cross_major)")
        tab_type = input("请选择 (1-4): ").strip()
        tab_map = {
            "1": "plan", "2": "public",
            "3": "cross_grade", "4": "cross_major"
        }
        course["tab_type"] = tab_map.get(tab_type, "plan")
        
        courses.append(course)
        
        if input("\n是否继续添加课程? (y/n): ").lower() != 'y':
            break
    
    # 保存配置
    config_file = os.path.join(get_app_data_dir(), "courses.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)
    print(f"\n课程配置已保存到: {config_file}")
    return courses

def show_welcome():
    """显示欢迎界面"""
    print("""
╔══════════════════════════════════════════════════════╗
║                深圳技术大学选课助手                  ║
║                     V1.0.0                           ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  功能特点:                                          ║
║    1. 支持四种选课类型                              ║
║    2. 自动检测课程状态                              ║
║    3. 智能防检测机制                                ║
║    4. 详细的日志记录                                ║
║                                                      ║
║  使用说明:                                          ║
║    · 确保已连接网络                         ║
║    · 首次使用需要配置账号和课程信息                 ║
║    · 支持无人值守自动选课                           ║
║                                                      ║
║  技术支持: https://github.com/xxx/xxx               ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
""")

def show_menu():
    """显示主菜单"""
    print("""
╔══════════════════════════════════════════════════════╗
║                     主菜单选项                       ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  [1] 开始选课                                       ║
║  [2] 配置课程信息                                   ║
║  [3] 修改登录信息                                   ║
║  [4] 查看使用说明                                   ║
║  [5] 退出程序                                       ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
""")
    return input("请选择操作 (1-5): ").strip()

def show_instructions():
    """显示使用说明"""
    print("""
╔══════════════════════════════════════════════════════╗
║                     使用说明                          ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  1. 登录信息配置                                      ║
║     · 学号格式: 12位数字                              ║
║     · 密码格式: Sztu@身份证后6位                      ║
║                                                     ║
║  2. 课程配置说明                                      ║
║     · 支持批量添加多个课程                            ║
║     · 可选择不同选课类型                              ║
║     · 可指定上课时间和节次                            ║
║                                                      ║
║  3. 选课类型说明                                      ║
║     · 本学期计划选课                                  ║
║     · 公选课选课                                      ║
║     · 专业内跨年级选课                                 ║
║     · 跨专业选课                                      ║
║                                                      ║
║  4. 注意事项                                          ║
║     · 确保网络稳定                                    ║
║     · 建议别在选课高峰期使用                           ║
║                                                      ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
""")
    input("\n按回车键返回主菜单...")

def main():
    show_welcome()
    
    print("\n首次使用需要进行以下配置：")
    
    # 1. 获取登录信息
    while True:
        username, password = get_credentials()
        if username and password:
            if create_env_file(username, password):
                break
        print("\n❌ 请重新输入登录信息")
    
    # 2. 配置课程信息
    print("\n接下来配置要选择的课程信息")
    config = CourseConfig()
    courses = config.create_config()
    
    if not courses:
        print("\n❌ 未配置任何课程，程序将退出")
        return
    
    # 保存课程配置到当前目录
    if not config.save_to_json("courses.json"):
        print("\n❌ 保存课程配置失败，程序将退出")
        return
    
    # 3. 开始选课
    print("\n配置完成，即将开始选课...")
    selector = None
    try:
        selector = CourseSelector()
        if selector.login():
            selector.select_multiple_courses()
        else:
            print("\n❌ 登录失败，请检查账号密码")
    except Exception as e:
        print(f"\n❌ 程序出错: {str(e)}")
    finally:
        if selector:
            selector.close()

if __name__ == "__main__":
    try:
        # 设置控制台标题和窗口大小
        if os.name == 'nt':
            os.system('title 深圳技术大学选课助手')
            os.system('mode con cols=100 lines=40')
        
        main()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
    except Exception as e:
        print(f"\n\n程序异常退出: {str(e)}")
    finally:
        input("\n按回车键退出...") 