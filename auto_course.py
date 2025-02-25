import os
import random
import time
import sys
import socket
import subprocess
import requests
import urllib3
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from config import CourseConfig
import json

# 配置详细的日志记录
logger.remove()  # 移除默认的处理器
logger.add(
    "auto_course.log",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    rotation="500 MB",
    encoding="utf-8"
)

# 仅在非打包模式下添加控制台输出
if not getattr(sys, 'frozen', False):
    logger.add(sys.stderr, level="INFO")

def check_basic_network(retries=3):
    for _ in range(retries):
        try:
            socket.gethostbyname("auth.sztu.edu.cn")
            return True
        except socket.gaierror:
            time.sleep(1)
    return False

def check_vpn_network():
    """检查VPN连接状态"""
    try:
        # 禁用SSL警告
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 尝试访问教务系统
        response = requests.get(
            "https://auth.sztu.edu.cn/idp/authcenter/ActionAuthChain?entityId=jiaowu",
            verify=False,  # 忽略SSL证书验证
            timeout=5
        )
        if response.status_code == 200:
            logger.info("教务系统可以访问")
            return True
        else:
            logger.warning(f"教务系统返回状态码: {response.status_code}")
            return False
    except requests.exceptions.SSLError:
        logger.error("SSL证书验证失败，可能需要配置证书或使用VPN")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("无法连接到教务系统，请检查是否已连接校园网或VPN")
        return False
    except requests.exceptions.Timeout:
        logger.error("连接教务系统超时")
        return False
    except Exception as e:
        logger.error(f"网络检查出现未知错误: {str(e)}")
        return False

class CourseSelector:
    def __init__(self,headless=True):
        logger.info("初始化选课程序...")
        try:
            # 首先检查网络连接
            if not check_basic_network():
                raise ConnectionError("网络连接异常，请检查网络设置")
            if not check_vpn_network():
                raise ConnectionError("无法访问教务系统，请确保已连接校园网或VPN")
                
            self.setup_driver()
            self.load_credentials()
            self.selected_courses = set()
            logger.success("初始化完成")
        except Exception as e:
            logger.error(f"初始化失败: {str(e)}")
            raise
        
    def setup_driver(self):
        """Set up Chrome driver with anti-detection measures"""
        logger.info("正在配置Chrome浏览器...")
        try:
            # 检查浏览器安装
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if not os.path.exists(chrome_path):
                raise FileNotFoundError(f"Chrome浏览器未安装在默认路径: {chrome_path}")

            # 检查chromedriver
            chromedriver_path = r"C:\Program Files\Google\Chrome\Application\chromedriver.exe"
            logger.info(f"正在检查chromedriver路径: {chromedriver_path}")
            if not os.path.exists(chromedriver_path):
                raise FileNotFoundError(f"未找到chromedriver: {chromedriver_path}\n请执行以下操作：\n1. 访问 https://chromedriver.chromium.org/downloads\n2. 下载与Chrome版本匹配的驱动\n3. 解压后将chromedriver.exe放入Chrome安装目录")

            options = Options()
            # 设置无界面模式
            options.add_argument("--headless=new")
            #设置界面模式
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # 添加更多的反检测参数
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            
            # 设置用户代理
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
            
            logger.info("正在初始化ChromeDriver服务...")
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 注入反检测JavaScript
            logger.debug("注入反检测代码...")
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                """
            })
            logger.success("Chrome浏览器配置完成")
            
        except WebDriverException as e:
            logger.error(f"Chrome浏览器配置失败: {str(e)}")
            if "chromedriver" in str(e).lower():
                logger.error("ChromeDriver安装或配置出错，请确保Chrome浏览器已正确安装")
            raise
        except Exception as e:
            logger.error(f"浏览器配置过程出现未知错误: {str(e)}")
            raise
        
    def load_credentials(self):
        """Load credentials from environment variables"""
        logger.info("正在加载登录凭证...")
        try:
            load_dotenv()
            self.username = os.getenv("STUDENT_ID")
            self.password = os.getenv("PASSWORD")
            
            if not self.username or not self.password:
                raise ValueError("未找到登录凭证，请检查.env文件")
                
            logger.debug(f"学号: {self.username}")
            logger.debug(f"密码格式检查: {'通过'}")
            logger.success("登录凭证加载完成")
            
        except Exception as e:
            logger.error(f"加载登录凭证失败: {str(e)}")
            raise
            
    def check_network(self):
        """检查网络连接和教务系统可访问性"""
        logger.info("正在执行深度网络检查...")
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(15)
            self.driver.set_script_timeout(15)
            
            # 新增DNS解析检查
            try:
                dns_start = time.time()
                socket.gethostbyname("jwxt.sztu.edu.cn")
                logger.debug(f"DNS解析成功，耗时: {(time.time()-dns_start)*1000:.2f}ms")
            except socket.gaierror as e:
                logger.error("DNS解析失败，请检查网络连接")
                raise ConnectionError("DNS解析失败") from e
            
            # 尝试访问教务系统
            logger.debug("正在初始化网络请求...")
            self.driver.get("https://jwxt.sztu.edu.cn")
            
            # 等待页面加载完成
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            
            # 获取页面标题和URL
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            logger.debug(f"当前页面URL: {current_url}")
            logger.debug(f"页面标题: {page_title}")
            
            # 检查是否被重定向到登录页面
            if "jioawu" in current_url.lower() or "系统登录" in page_title:
                logger.success("成功访问登录页面")
                return True
            else:
                logger.warning(f"页面内容异常，当前URL: {current_url}")
                raise Exception(f"页面内容异常，当前URL: {current_url}")
                
        except WebDriverException as e:
            error_msg = str(e).lower()
            if "net::" in error_msg:
                logger.error("网络连接失败，请检查以下问题：")
                logger.error("1. 是否已连接到网络")
                logger.error("2. 是否已连接校园网或VPN")
                logger.error("3. 是否可以正常访问教务系统网站")
            elif "timeout" in error_msg:
                logger.error("页面加载超时，可能是网络较慢或教务系统响应延迟")
            else:
                logger.error(f"访问教务系统失败: {str(e)}")
            
            # 保存错误截图
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"network_error_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"网络错误截图已保存: {screenshot_path}")
            except Exception as se:
                logger.error(f"保存错误截图失败: {str(se)}")
                
            raise
            
    def random_sleep(self, min_time=0.1, max_time=1):
        """Add random delay to simulate human behavior"""
        delay = random.uniform(min_time, max_time)
        logger.debug(f"等待 {delay:.2f} 秒...")
        time.sleep(delay)
        
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present and clickable"""
        try:
            logger.debug(f"等待元素出现: {by}={value}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            logger.debug("元素已找到")
            return element
        except TimeoutException:
            logger.error(f"等待元素超时: {by}={value}")
            # 保存页面截图以便调试
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"error_screenshot_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"错误截图已保存: {screenshot_path}")
            raise
            
    def login(self):
        """Login to the SZTU educational system"""
        logger.info("开始登录教务系统...")
        try:
            # 首先检查网络连接
            if not self.check_network():
                return False
                
            logger.debug("开始输入登录信息...")
            username_input = self.wait_for_element(By.XPATH, "//*[@id='j_username']")
            password_input = self.wait_for_element(By.XPATH, "//*[@id='j_password']")
            login_button = self.wait_for_element(By.XPATH, "//*[@id='loginButton']")
            
            # 清除输入框并输入凭证
            username_input.clear()
            username_input.send_keys(self.username)
            logger.debug("已输入用户名")
            self.random_sleep()
            
            password_input.clear()
            password_input.send_keys(self.password)
            logger.debug("已输入密码")
            self.random_sleep()
            
            # 点击登录按钮
            login_button.click()
            logger.info("已点击登录按钮")
            
            # 检查登录结果
            try:
                error_message = self.driver.find_element(By.XPATH, "//div[contains(@class,'el-message--error')]")
                logger.error(f"登录失败，错误信息: {error_message.text}")
                return False
            except NoSuchElementException:
                logger.success("登录成功")
                return self.enter_course_selection()
                
        except Exception as e:
            logger.error(f"登录过程出现错误: {str(e)}")
            return False

    def enter_course_selection(self):
        """进入选课系统的完整流程"""
        try:
            logger.info("正在进入选课系统...")
            
            # 第一次点击"进入选课"
            enter_btn1 = self.wait_for_element(
                By.XPATH, "//a[contains(text(),'进入选课') or contains(text(),'选课')]"
            )
            enter_btn1.click()
            self.random_sleep()
            
            # 第二次点击"进入选课"
            enter_btn2 = self.wait_for_element(
                By.XPATH, "//*[@id='attend_class']/tbody/tr[2]/td[4]/a"
            )
            enter_btn2.click()
            self.random_sleep()
            
            # 第三次点击"进入选课"（如果存在）
            try:
                enter_btn3 = self.wait_for_element(
                    By.XPATH, "/html/body/form/div/div/input[2]",
                    timeout=5
                )
                enter_btn3.click()
                self.random_sleep()
            except TimeoutException:
                logger.info("已经在选课操作页面")
                
            logger.success("成功进入选课系统")
            return True
            
        except Exception as e:
            logger.error(f"进入选课系统失败: {str(e)}")
            return False
        
    def navigate_to_tab(self, tab_type):
        """导航到指定选课选项卡"""
        try:
            # 等待页面加载完成
            self.driver.implicitly_wait(10)
            self.random_sleep(2, 3)  # 增加等待时间
            
            # 使用更精确的URL映射
            url_map = {
                "plan": "/jsxsd/xsxkkc/comeInBxqjhxk",  # 本学期计划选课
                "public": "/jsxsd/xsxkkc/comeInGgxxkxk",  # 公选课选课
                "cross_grade": "/jsxsd/xsxkkc/comeInKnjxk",  # 专业内跨年级选课
                "cross_major": "/jsxsd/xsxkkc/comeInFawxk"  # 跨专业选课
            }
            
            if tab_type not in url_map:
                raise ValueError(f"不支持的选课类型: {tab_type}")
                
            # 直接通过JavaScript点击对应链接
            js_script = f"""
            var links = document.querySelectorAll('a[href*="{url_map[tab_type]}"]');
            if (links.length > 0) {{
                links[0].click();
            }} else {{
                return false;
            }}
            """
            
            # 执行JavaScript
            result = self.driver.execute_script(js_script)
            if result is False:
                # 如果JavaScript点击失败，尝试直接访问URL
                base_url = "https://jwxt.sztu.edu.cn"
                self.driver.get(f"{base_url}{url_map[tab_type]}")
                
            # 等待页面加载
            self.random_sleep(1, 2)
            
            # 验证是否成功切换
            current_url = self.driver.current_url
            if url_map[tab_type] in current_url:
                logger.success(f"成功切换到{tab_type}选项卡")
                return True
            else:
                logger.warning(f"URL验证失败，期望包含 {url_map[tab_type]}，实际URL: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"切换选项卡失败: {str(e)}")
            # 保存错误截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"tab_error_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"错误截图已保存: {screenshot_path}")
            raise

    def search_course(self, course_info):
        """执行课程搜索（支持任意单个条件）"""
        try:
            # 等待页面加载完成
            self.random_sleep(1, 2)
            
            # 1. 输入课程名称
            course_input = self.wait_for_element(By.ID, "kcxx")
            course_input.clear()
            course_input.send_keys(course_info["course_name"])
            self.random_sleep(0.1, 0.5)
            
            # 2. 输入教师姓名
            teacher_input = self.wait_for_element(By.ID, "skls")
            teacher_input.clear()
            teacher_input.send_keys(course_info["teacher"].replace(" ", ""))
            self.random_sleep(0.1, 0.5)
            
            # 3. 选择星期
            weekday_map = {
                "周一": "1", "周二": "2", "周三": "3",
                "周四": "4", "周五": "5", "周六": "6", "周日": "7"
            }
            weekday_select = self.wait_for_element(By.ID, "skxq")
            weekday_select.click()
            self.random_sleep(0.1, 0.5)
            
            weekday_value = weekday_map.get(course_info["time"])
            if weekday_value:
                weekday_option = self.wait_for_element(
                    By.XPATH, f"//select[@id='skxq']/option[@value='{weekday_value}']"
                )
                weekday_option.click()
                self.random_sleep(0.1, 1)
            
            # 4. 选择节次
            start_section = course_info["start_section"]
            end_section = course_info["end_section"]
            
            # 选择开始节次
            start_select = self.wait_for_element(By.ID, "skjc")
            Select(start_select).select_by_value(str(start_section))
            self.random_sleep(0.5, 1)
            
            # 选择结束节次
            end_select = self.wait_for_element(By.ID, "endJc")
            Select(end_select).select_by_value(str(end_section))
            self.random_sleep(0.5, 1)

            # 5. 选择是否过滤已满课程
            guolv = self.driver.find_element(By.XPATH, "//label[contains(span, '过滤已满课程')]")
            guolv.click()

            # 6. 尝试多种方式定位查询按钮
            search_button = None
            try_count = 0
            max_tries = 4
            
            while try_count < max_tries and not search_button:
                try:
                    if try_count == 0:
                        # 尝试使用完整XPath
                        search_button = self.driver.find_element(By.XPATH, "/html/body/div[8]/input[4]")
                    elif try_count == 1:
                        # 尝试使用CSS选择器
                        search_button = self.driver.find_element(By.CSS_SELECTOR, "input.button[value='查询']")
                    elif try_count == 2:
                        # 尝试使用属性组合
                        search_button = self.driver.find_element(By.XPATH, "//input[@type='button'][@value='查询']")
                    else:
                        # 尝试使用JavaScript点击
                        self.driver.execute_script("""
                            var buttons = document.querySelectorAll('input[type="button"]');
                            for(var i = 0; i < buttons.length; i++) {
                                if(buttons[i].value === '查询') {
                                    buttons[i].click();
                                    return true;
                                }
                            }
                            return false;
                        """)
                        self.random_sleep(2, 3)
                        return True
                        
                    if search_button and search_button.is_displayed() and search_button.is_enabled():
                        search_button.click()
                        self.random_sleep(2, 3)
                        return True
                        
                except Exception as e:
                    logger.debug(f"第{try_count + 1}次尝试定位查询按钮失败: {str(e)}")
                    try_count += 1
                    
            if try_count >= max_tries:
                logger.error("无法找到查询按钮")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"搜索课程失败: {str(e)}")
            return False

    def verify_course(self, course_info):
        """查找可选课程"""
        try:
            # 等待数据表格加载
            self.wait_for_element(
                By.XPATH, "//table[@id='dataView']"
            )
            self.random_sleep(0.1, 0.3)
            
            # 查找所有包含"选课"按钮的行
            rows = self.driver.find_elements(By.XPATH, "//table[@id='dataView']/tbody/tr[.//a[contains(text(), '选课')]]")
            logger.info(f"找到 {len(rows)} 个可选课程")
            
            for row in rows:
                try:
                    # 获取课程基本信息用于日志记录
                    course_id = row.find_element(By.XPATH, ".//td[1]").text
                    course_name = row.find_element(By.XPATH, ".//td[3]").text
                    teacher = row.find_element(By.XPATH, ".//td[contains(@class, 'center')]/preceding-sibling::td[1]").text
                    
                    # 直接查找选课按钮
                    select_button = row.find_element(By.XPATH, ".//a[contains(text(), '选课')]")
                    
                    if select_button and select_button.is_displayed() and select_button.is_enabled():
                        logger.success(f"找到可选课程: {course_name} - {teacher}")
                        return select_button
                        
                except Exception as e:
                    logger.debug(f"处理课程行时出错: {str(e)}")
                    continue
                    
            logger.warning("未找到任何可选课程")
            return None
            
        except Exception as e:
            logger.error(f"查找可选课程失败: {str(e)}")
            return None

    def handle_confirmation(self):
        """处理选课确认弹窗和结果验证"""
        try:
            # 等待并处理第一个确认弹窗（是否选课）
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                logger.debug(f"选课确认弹窗: {alert_text}")
                alert.accept()  # 点击确定
                self.random_sleep(0.1, 0.2)
            except:
                logger.warning("未检测到选课确认弹窗")
                return False

            # 等待并处理结果弹窗
            try:
                result_alert = self.driver.switch_to.alert
                result_text = result_alert.text
                logger.debug(f"选课结果弹窗: {result_text}")
                result_alert.accept()  # 点击确定
                
                # 判断选课结果
                if "成功" in result_text:
                    logger.success(f"选课成功: {result_text}")
                    return True
                else:
                    logger.warning(f"选课失败: {result_text}")
                    return False
            except:
                logger.warning("未检测到选课结果弹窗")
                return False

        except Exception as e:
            logger.error(f"处理选课确认弹窗时出错: {str(e)}")
            return False

    def select_multiple_courses(self):
        """选择多个课程"""
        try:
            config_path = "courses.json"
            if not os.path.exists(config_path):
                logger.error(f"未找到课程配置文件: {config_path}")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                courses = json.load(f)
            
            if not courses:
                logger.warning("课程配置为空")
                return False
            
            retry_count = 0
            max_retries = 100
            
            while retry_count < max_retries:
                retry_count += 1
                logger.info(f"第 {retry_count} 轮选课开始...")
                
                for course in courses:
                    try:
                        # 跳过已选中的课程
                        if course["course_id"] in self.selected_courses:
                            continue
                            
                        # 切换到对应选课类型的页面
                        if not self.navigate_to_tab(course["tab_type"]):
                            continue
                            
                        # 搜索并选择课程
                        if self.search_course(course):
                            if select_btn := self.verify_course(course):
                                select_btn.click()
                                if self.handle_confirmation():
                                    logger.success(f"成功选中课程：{course['course_name']}")
                                    self.selected_courses.add(course["course_id"])
                                    
                    except Exception as e:
                        logger.error(f"{course['course_name']} 选课失败：{str(e)}")
                        
                    finally:
                        self.random_sleep(2, 3)
                        self.driver.refresh()
                        self.random_sleep(1, 2)
                
                # 检查是否所有课程都已选中
                if all(course["course_id"] in self.selected_courses for course in courses):
                    logger.success("所有课程已选择完成！")
                    break
                    
                # 达到最大重试次数
                if retry_count >= max_retries:
                    logger.warning("已达到最大重试次数，程序将退出")
                    break
                    
                logger.info(f"第 {retry_count} 轮选课完成，等待下一轮...")
                self.random_sleep(3, 5)
                
        except Exception as e:
            logger.error(f"选课过程出错: {str(e)}")
            return False
            
        return True

    def close(self):
        """Close the browser and clean up"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            
def main():
    selector = None
    try:
        logger.info("="*50)
        logger.info("选课程序启动")
        logger.info("="*50)
        
        # 检查运行环境
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"操作系统: {sys.platform}")
        logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查网络环境
        logger.info("正在检查网络环境...")
        if not check_basic_network() or not check_vpn_network():
            logger.error("网络环境检查失败，程序终止")
            return
            
        selector = CourseSelector()
        if selector.login():
            selector.select_multiple_courses()
        else:
            logger.error("登录失败，程序终止")
            
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
    finally:
        if selector:
            selector.close()
        logger.info("="*50)
        logger.info("程序结束")
        logger.info("="*50)
            
if __name__ == "__main__":
    main()
