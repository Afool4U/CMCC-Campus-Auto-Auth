# CMCC Campus Auto Auth

一个适用于中国移动校园网的自动认证脚本，支持 **Windows 平台**，可实现**断网自动重连 + 自动认证登录**，适合校园网环境中频繁掉线但需保持网络在线的场景。

> 作者：Afool4u  
> 版本：v1.0  
> 日期：2025-03-23  

---

## 🧩 功能简介

该脚本通过系统级控制与浏览器自动化配合，实现：

- 📡 自动连接指定 Wi-Fi（如 CMCC-EDU）
- 🔄 自动检测是否掉线
- 🌐 自动判断是否跳转至认证页面
- 🔐 自动填写认证信息并完成登录
- 🛡️ 后台静默运行，用户无感知
- 🧠 带重试与容错机制，稳定性强

---

## ⚙️ 使用前准备

1. ✅ 安装 [Chrome 浏览器](https://googlechromelabs.github.io/chrome-for-testing/#stable)
2. ✅ 安装与 Chrome 版本一致的 [ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/#stable)
3. ✅ 安装 Python 依赖：

   ```bash
   pip install requests selenium
   ```

4. ✅ 修改脚本中的以下配置信息：

   ```python
   DRIVER_PATH = r"你的chromedriver路径"
   CHROME_PATH = r"你的chrome路径"
   USERNAME = "你的校园卡手机号"
   PASSWORD = "你的固定密码"  # 请关闭自动登录功能
   wlanacname = "你的AP参数（可选）"
   ```

5. ✅ 确保系统中已连接过目标 Wi-Fi（如 `CMCC-EDU`）一次，已保存配置。

---

## 🛠 计划任务设置（推荐）

将脚本设为开机自启，完全后台运行：

1. 按 `Win + R` 输入 `taskschd.msc` 打开任务计划程序
2. 创建新任务，配置如下：

- **常规**
  - 名称：`CMCC`
  - 勾选：`不管用户是否登录都要运行`
  - 勾选：`使用最高权限运行`
  - 勾选：`隐藏`
  - 配置：`Windows 10`

- **触发器**：新建 -> `开机时`

- **操作**：
  - 程序或脚本：填写 Python 的绝对路径（注意用 `pythonw.exe`）
  - 添加参数：脚本的绝对路径

- **条件**：取消勾选“只有在计算机使用交流电源时才启动”

- **设置**：
  - 取消勾选“如果任务运行超过…则停止”
  - 勾选“允许按需运行任务”

3. 保存任务，输入 Windows 密码（不是 PIN 码）即可。

---

## 📖 工作机制详解

### 1. 网络状态监测  
通过 `ping` 公网 IP（默认 `8.138.155.214`）判断是否在线。

### 2. Wi-Fi 接入检测与自动连接  
使用 `netsh wlan` 检测当前是否连接目标 SSID，若未连接则自动尝试连接。

### 3. 重定向检测  
访问 `http://baidu.com` 判断是否被重定向至认证页面。

### 4. 自动认证登录  
调用 Selenium 控制 Headless Chrome：

- 自动打开认证页面
- 绕过 HTTPS 警告页面（发送 `thisisunsafe`）
- 自动填写账号密码
- 自动点击登录
- 检查登录成功标志

### 5. 容错机制  
- 最多支持 20 次认证失败重试
- 每次间隔等待，避免频繁请求
- 网络恢复后自动重置重试计数

---

## 📦 示例运行效果

- ✅ 掉线后自动连接 Wi-Fi
- ✅ 自动检测认证页面并登录
- ✅ 登录后网络恢复，脚本继续监听
- ✅ 用户无需任何手动干预
- ✅ 开机自动后台静默监测
- ✅ 不影响使用其他 Wi-Fi

![image](https://github.com/user-attachments/assets/56da527c-2e97-43f6-b781-7b0fb5122d12)
---

## 📌 注意事项

- 必须关闭移动校园卡账号的“自动登录”功能，否则认证会失败
- 使用 `pythonw.exe` 运行以避免弹出窗口
- 请确保 Chrome 与 ChromeDriver 版本完全一致
- AP 参数可选，但在认证跳转异常时可能作为 fallback 使用

---

## 📜 License

Apache license 2.0

---

## 🙋‍♂️ 作者的话

本脚本专为中国移动校园CMCC高频断网痛点设计，目标是打造一个“完全自动化 + 稳定运行”的认证助手。  
如有建议、反馈或想扩展功能，欢迎 issue 或 PR！

---
