# Author: Afool4U
# Date: 2025-03-23
# Description: 中国移动校园卡自动认证脚本
# Version: 1.0
#
# 适用于中国移动校园卡认证，支持Windows系统，需要安装Chrome浏览器和ChromeDriver。
# 需要安装的三方库：requests, selenium
# 安装命令：pip install requests selenium
#
# 本脚本会自动检测网络连接状态，如果断线则自动重连并自动认证。
# 注意：请先关闭自动登录功能，并设置固定密码，否则会认证失败。
#
# 然后将本脚本添加到Windows计划任务中：Win+R -> taskschd.msc -> 创建任务。
# 常规：名称填写“CMCC”，安全选项选择 “不管用户是否登录都要运行”、“使用最高权限运行”、“隐藏”，配置选择“Windows 10”。
# 触发器 -> 新建 -> 启动时 -> 确定。
# 操作 -> 新建 -> 程序或脚本：填写Python的绝对路径（并将python.exe改为pythonw.exe），添加参数：填写脚本的绝对路径 -> 确定。
# 条件 -> 取消勾选“只有在计算机使用交流电源时才启动此任务”。
# 设置 -> 取消勾选“如果任务运行时间超过以下时间，停止任务”，打钩“允许按需运行任务”。 -> 确定。
# 输入Windows密码保存即可。（注意：不是PIN码）

import re
import time
import requests
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

# 目标IP，用来检测是否联网（不需要修改，除非该公网IP失效）
target_ip = "8.138.155.214"
ssid = "CMCC-EDU"
auth_domain = "http://wlan.jsyd139.com"

# 最大失败重试次数（不要修改）
max_retries = 20

"""""""""""""""""""以下为配置信息"""""""""""""""""""

# Chrome和ChromeDriver必须是完全匹配的版本，否则会出现错误。
# 以下是专用于测试的Chrome下载地址，可以同时和原有Chrome共存，不会影响原有Chrome。
# 注意：需要同时下载Chrome和ChromeDriver，平台对应且版本匹配。
# https://googlechromelabs.github.io/chrome-for-testing/#stable

# ChromeDriver路径
DRIVER_PATH = "你的chromedriver路径"  # 比如 r'D:\chromedriver-win64\chromedriver.exe'
# Chrome路径
CHROME_PATH = "你的chrome路径"  # 比如 r'D:\chrome-win64\chrome.exe'
# 认证手机号和密码
USERNAME = "你的手机号"  # 中国移动校园卡的手机号
PASSWORD = "你的固定密码"  # 请先关闭自动登录功能，并设置固定密码
# 固定AP参数（根据自己正常手动登录认证成功后的跳转网址填入，如果设备位置固定则不需要再做修改，否则需要做mac地址映射表）
# 怎么找到这个参数？正常手动认证成功后，查看浏览器地址栏的参数 wlanacname=xxxxxx
# 例如：http://wlan.jsyd139.com/?wlanuserip=172.23.124.193&wlanacname=0196.0510.250.00&ssid=CMCC-EDU
# 那么这里的wlanacname就是 0196.0510.250.00
# ⚠️AP参数一般不会用到，可暂不填写。  ⚠️
# 作用：当重定向地址无法获取时，会使用AP参数和局域网IP计算重定向地址。
# ✅ 如果没有固定位置的强网络需求，可以暂不填写。
wlanacname = "你的AP参数（可暂不填写）"  # 比如在我宿舍是 "0196.0510.250.00"。

"""""""""""""""""""以上为配置信息"""""""""""""""""""


def ping_target(ip: str) -> bool:
    """Ping指定IP，返回是否连通"""
    try:
        result = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Ping失败: {e}")
        return False


def get_local_ip():
    """只获取 WLAN 网卡的 IPv4 地址"""
    try:
        output = subprocess.check_output("ipconfig", encoding='gbk')
        blocks = output.split("\n\n")  # 按网卡分块

        for idx, block in enumerate(blocks):
            if "WLAN" in block:
                match = re.search(r"IPv4 地址[.\s]*: (\d+\.\d+\.\d+\.\d+)", blocks[idx + 1])
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"获取WLAN IP失败: {e}")
    return None


def can_scan_cmcc_edu():
    try:
        result = subprocess.check_output("netsh wlan show networks", encoding="gbk", errors="ignore")
        return "CMCC-EDU" in result
    except Exception as e:
        print(f"获取可用Wi-Fi列表失败：{e}")
        return False


def ensure_wifi_connected(target_ssid="CMCC-EDU"):
    # 检测是否有 CMCC-EDU 的 WiFi
    if not can_scan_cmcc_edu():
        print("⚠️ 未找到 CMCC-EDU 的 WiFi")
        return False
    """如果未连接到目标SSID，则尝试连接"""
    try:
        output = subprocess.check_output("netsh wlan show interfaces", encoding='gbk')

        if target_ssid in output:
            # print(f"✅ 当前已连接到 {target_ssid}")
            return True
        else:
            print(f"⚠️ 当前未连接到 {target_ssid}，尝试连接...")

            # 尝试连接
            result = subprocess.run(f'netsh wlan connect name="{target_ssid}"',
                                    shell=True, capture_output=True, text=True, encoding='gbk')
            print(result.stdout)

            # 等待几秒让它连接完成
            time.sleep(5)

            # 再次检测是否成功连接
            output = subprocess.check_output("netsh wlan show interfaces", encoding='gbk')
            if target_ssid in output:
                print(f"✅ 成功连接到 {target_ssid}")
                return True
            else:
                print("❌ WiFi 连接失败")
                return False
    except Exception as e:
        print(f"检测WiFi状态失败：{e}")
        return False


# 设置Chrome选项
service = Service(DRIVER_PATH)
chrome_options = Options()
chrome_options.binary_location = CHROME_PATH
chrome_options.add_argument("--headless=new")  # ✅ 新版Chrome推荐写法
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# 全局变量driver
driver = None


def get_redirect_url():
    try:
        # 发送 GET 请求，不允许自动跳转
        response = requests.get("http://baidu.com", allow_redirects=False, timeout=20)

        # 检查是否有重定向
        if response.status_code in (301, 302):
            redirect_url = response.headers.get('Location')
            if redirect_url:
                print(f"检测到重定向认证地址：{redirect_url}")
                return redirect_url
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"访问 baidu.com 失败：{e}")
        return None


def open_auth_page():
    global driver
    url = get_redirect_url()
    if not url:
        ip = get_local_ip()
        if not ip:
            print("无法获取本机IP，跳过认证页面打开。")
            return
        url = f"{auth_domain}/?wlanuserip={ip}&wlanacname={wlanacname}&ssid={ssid}"
    print(f"打开认证页面：{url}\n")

    # 关闭残留
    if driver:
        driver.close()

    # 打开浏览器
    driver = webdriver.Chrome(options=chrome_options, service=service)
    driver.maximize_window()
    driver.get(url)

    # 发送 thisisunsafe，绕过不安全警告页面
    ActionChains(driver).send_keys("thisisunsafe").perform()

    driver.get(url)

    try:
        # 等待 frame 出现
        WebDriverWait(driver, 30).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "mainFrame"))
        )

        # 然后再找元素
        driver.find_element(By.ID, "UserName").send_keys(USERNAME)
        driver.find_element(By.ID, "PassWord").send_keys(PASSWORD)
        driver.find_element(By.ID, "loginbutton1").click()
        print("✅ 已点击登录按钮")

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "onlinetime"))
            )
            print("✅ 登录成功，已检测到计时器！\n")
        except Exception as e:
            print("⚠️ 登录后未检测到计时器：", e, '\n')
    except Exception as e:
        print("❌ 填表单失败：", e)


def main():
    retries = 0
    print("✅请确保系统里已有 CMCC-EDU 的 Wi-Fi 配置（手动连接过一次即可）")

    while True:
        # 自动连接 WiFi
        if not ensure_wifi_connected("CMCC-EDU"):
            time.sleep(10)
            continue

        if ping_target(target_ip):
            print(f"{target_ip} 连通")
            retries = 0
            time.sleep(10)
        else:
            print(f"{target_ip} 无法连接")
            if retries < max_retries:
                try:
                    open_auth_page()
                    time.sleep(2)
                except Exception:
                    pass
                if not ping_target(target_ip):
                    print(f"{target_ip} 仍无法连接")
                    time.sleep(30)
                    retries += 1
                else:
                    print(f"{target_ip} 恢复连接")
                    retries = 0
                    time.sleep(10)
            else:
                print(f"达到最大重试次数({max_retries})，退出...")
                break


if __name__ == "__main__":
    main()
