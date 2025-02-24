# -*- coding: utf-8 -*-
import json
import os
from typing import List, Dict, Any

class CourseConfig:
    def __init__(self):
        self.courses = []
        
    @staticmethod
    def print_header(title: str):
        """打印美化的标题"""
        print("\n" + "═" * 60)
        print(f"{title:^60}")
        print("═" * 60)
        
    @staticmethod
    def display_menu(title: str, options: List[str]) -> str:
        """显示菜单选项"""
        print(f"\n{'='*20} {title} {'='*20}")
        for i, option in enumerate(options, 1):
            print(f"  [{i}] {option}")
        print("=" * (42 + len(title)))
        return input("\n👉 请选择 (输入数字): ").strip()
        
    @staticmethod
    def get_weekday() -> str:
        """获取上课星期"""
        weekday_options = [
            "周一", "周二", "周三", "周四",
            "周五", "周六", "周日"
        ]
        
        print("\n" + "╔" + "═"*40 + "╗")
        print("║" + "选择上课星期".center(40) + "║")
        print("╠" + "═"*40 + "╣")
        
        for i, day in enumerate(weekday_options, 1):
            print(f"║  {i}. {day:<10}", end='')
            if i % 3 == 0:
                print(" "*15 + "║")
        if len(weekday_options) % 3 != 0:
            print(" "*(37 - (len(weekday_options) % 3)*12) + "║")
            
        print("╚" + "═"*40 + "╝")
        
        while True:
            try:
                choice = int(input("\n👉 请选择 (1-7): ").strip())
                if 1 <= choice <= 7:
                    return weekday_options[choice - 1]
                print("❌ 错误: 请输入1-7之间的数字")
            except ValueError:
                print("❌ 错误: 请输入有效的数字")
                
    @staticmethod
    def get_section() -> tuple:
        """获取上课节次"""
        CourseConfig.print_header("选择上课节次")
        print("\n📅 课程时间表")
        print("┌─────────────────────┬─────────────────────┐")
        print("│  第1-2节: 08:30-09:55  │  第3-4节: 10:15-11:40  │")
        print("│  第5节: 11:45-12:25    │  第6-7节: 14:00-15:25  │")
        print("│  第8-9节: 15:45-17:10  │  第10节 : 17:15-17:55  │")
        print("│  第11-12节: 19:00-20:20│  第13-14节:20:30-21:50 │")
        print("│  第15节:    17:20-18:30│                        │")
        print("└─────────────────────┴─────────────────────┘")
        
        while True:
            try:
                start = input("\n👉 请输入开始节次 (1-12): ").strip()
                if not start.isdigit() or not (1 <= int(start) <= 12):
                    raise ValueError("开始节次必须是1-12之间的数字")
                    
                end = input("👉 请输入结束节次 (1-12): ").strip()
                if not end.isdigit() or not (1 <= int(end) <= 12):
                    raise ValueError("结束节次必须是1-12之间的数字")
                    
                if int(start) > int(end):
                    raise ValueError("开始节次不能大于结束节次")
                    
                return start, end
            except ValueError as e:
                print(f"\n❌ 错误: {str(e)}")
                if input("是否重新输入? (y/n): ").lower() != 'y':
                    print("ℹ️ 使用默认值：1-2节")
                    return "1", "2"
                    
    @staticmethod
    def get_tab_type() -> str:
        """获取选课类型"""
        tab_options = {
            "1": ("plan", "本学期计划选课"),
            "2": ("public", "公选课选课"),
            "3": ("cross_grade", "专业内跨年级选课"),
            "4": ("cross_major", "跨专业选课")
        }
        
        print("\n╔════════════════════════════════════╗")
        print("║          选择选课类型              ║")
        print("╠════════════════════════════════════╣")
        for key, (code, desc) in tab_options.items():
            print(f"║  {key}. {desc:<20} ({code:<10}) ║")
        print("╚════════════════════════════════════╝")
        
        while True:
            choice = input("\n👉 请选择 (1-4): ").strip()
            if choice in tab_options:
                return tab_options[choice][0]
            print("❌ 错误: 请输入1-4之间的数字")
            
    def create_course(self) -> Dict[str, Any]:
        """交互式创建单个课程配置"""
        self.print_header("📚 添加新课程")
        
        course = {}
        
        # 1. 选择选课类型
        print("\n[1/4] 选择选课类型")
        print("─" * 40)
        tab_options = {
            "1": ("plan", "本学期计划课程"),
            "2": ("public", "公选课程"),
            "3": ("cross_grade", "专业内跨年级课程"),
            "4": ("cross_major", "跨专业课程")
        }
        
        for key, (code, desc) in tab_options.items():
            print(f"  [{key}] {desc}")
            
        while True:
            choice = input("\n👉 请选择课程类型 (1-4): ").strip()
            if choice in tab_options:
                course["tab_type"] = tab_options[choice][0]
                break
            print("❌ 请输入有效的选项")
        
        # 2. 输入课程信息
        print("\n[2/4] 输入课程信息")
        print("─" * 40)
        course["course_id"] = input("👉 课程编号 (可选): ").strip()
        
        while True:
            course["course_name"] = input("👉 课程名称 (必填): ").strip()
            if course["course_name"]:
                break
            print("❌ 课程名称不能为空")
            
        while True:
            course["teacher"] = input("👉 教师姓名 (必填): ").strip()
            if course["teacher"]:
                break
            print("❌ 教师姓名不能为空")
            
        # 3. 选择上课时间
        print("\n[3/4] 选择上课时间")
        print("─" * 40)
        course["time"] = self.get_weekday()
        
        # 4. 选择上课节次
        print("\n[4/4] 选择上课节次")
        print("─" * 40)
        start, end = self.get_section()
        course["start_section"] = start
        course["end_section"] = end
        
        # 显示确认信息
        self.print_header("✅ 确认课程信息")
        print(f"\n📚 课程名称: {course['course_name']}")
        print(f"🔢 课程编号: {course['course_id'] or '无'}")
        print(f"👨‍🏫 授课教师: {course['teacher']}")
        print(f"⏰ 上课时间: {course['time']} 第{start}-{end}节")
        print(f"📋 选课类型: {course['tab_type']}")
        
        if input("\n确认添加该课程? (y/n): ").lower() != 'y':
            return None
            
        return course
        
    def create_config(self):
        """交互式创建完整课程配置"""
        self.print_header("欢迎使用课程配置工具")
        
        while True:
            course = self.create_course()
            if course:
                self.courses.append(course)
                
            print("\n当前已添加课程:")
            print("-" * 20)
            for i, c in enumerate(self.courses, 1):
                print(f"\n{i}. {c['course_name']}")
                print(f"   教师: {c['teacher']}")
                print(f"   时间: {c['time']} 第{c['start_section']}-{c['end_section']}节")
                print(f"   类型: {c['tab_type']}")
                
            if input("\n是否继续添加课程? (y/n): ").lower() != 'y':
                break
                
        return self.courses
        
    @classmethod
    def from_json(cls, json_file: str):
        """从JSON文件加载课程配置"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = cls()
                data = json.load(f)
                # 转换旧格式配置
                for course in data:
                    if "section" in course:
                        start, end = course["section"].split("-")
                        course["start_section"] = start
                        course["end_section"] = end
                        del course["section"]
                config.courses = data
                return config
        except FileNotFoundError:
            print(f"错误: 未找到配置文件 {json_file}")
            return None
        except json.JSONDecodeError:
            print(f"错误: 配置文件 {json_file} 格式不正确")
            return None
            
    def save_to_json(self, json_file: str) -> bool:
        """保存课程配置到JSON文件"""
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.courses, f, ensure_ascii=False, indent=4)
            print(f"\n✅ 课程配置已保存到: {json_file}")
            return True
        except Exception as e:
            print(f"\n❌ 保存配置文件失败: {str(e)}")
            return False
            
if __name__ == "__main__":
    # 测试配置创建
    config = CourseConfig()
    config.create_config()
    
    # 保存配置
    if config.courses:
        config.save_to_json("courses.json")
    