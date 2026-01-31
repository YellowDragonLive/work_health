这份文档将为你提供一个基于 Python 的核心实现框架。为了满足 Windows 环境、开机自启、置顶弹窗、自定义音乐这几个核心需求，我们主要使用以下库：

tkinter: Python 自带的 GUI 库，用于实现置顶文字弹窗。

pygame: 用于稳定地播放各种格式的音乐（.mp3, .wav）。

pystray: 用于实现系统托盘运行，不占用任务栏。

Python 久坐提醒助手核心框架
1. 环境准备
你需要安装以下依赖库：

Bash
pip install pygame pystray Pillow
2. 核心代码结构 (main.py)
Python
import tkinter as tk
from tkinter import filedialog
import time
import threading
import pygame
import pystray
from PIL import Image
import os
import sys

class HealthAssistant:
    def __init__(self):
        self.read_time = 25 * 60  # 25分钟
        self.break_time = 5 * 60  # 5分钟
        self.music_path = "default_music.mp3" # 默认音乐路径
        self.is_running = True
        
        # 初始化音频引擎
        pygame.mixer.init()

    def play_music(self):
        """播放用户自定义音乐"""
        if os.path.exists(self.music_path):
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.play(-1)  # -1 表示循环播放

    def stop_music(self):
        pygame.mixer.music.stop()

    def show_reminder(self, message, duration):
        """显示置顶提醒窗口"""
        root = tk.Tk()
        root.title("久坐提醒")
        
        # 窗口置顶设置
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.9)  # 半透明
        
        # 居中显示
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry(f"400x200+{int(screen_width/2-200)}+{int(screen_height/2-100)}")

        label = tk.Label(root, text=message, font=("Microsoft YaHei", 14), pady=20)
        label.pack()

        def start_rest():
            self.play_music()
            btn_rest.destroy()
            self.countdown(root, duration)

        btn_rest = tk.Button(root, text="我已起立，开始休息", command=start_rest)
        btn_rest.pack(pady=10)

        root.mainloop()

    def countdown(self, window, seconds):
        """倒计时逻辑"""
        label_time = tk.Label(window, text="", font=("Helvetica", 30))
        label_time.pack()
        
        for i in range(seconds, -1, -1):
            mins, secs = divmod(i, 60)
            label_time.config(text=f"{mins:02d}:{secs:02d}")
            window.update()
            time.sleep(1)
        
        self.stop_music()
        window.destroy()

    def main_logic(self):
        """主循环：25分钟阅读 -> 提醒活动"""
        while self.is_running:
            time.sleep(self.read_time)  # 等待25分钟
            self.show_reminder("阅读结束！请起身活动5分钟", self.break_time)

# --- Windows 开机自启实现 ---
def set_autostart():
    """将脚本添加到注册表实现开机自启"""
    import winreg
    path = os.path.realpath(sys.argv[0])
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "HealthAssistant", 0, winreg.REG_SZ, path)
    winreg.CloseKey(key)

# --- 系统托盘图标 ---
def setup_tray(app):
    image = Image.open("icon.png") # 需要准备一个图标文件
    menu = pystray.Menu(
        pystray.MenuItem("设置音乐", lambda: select_music(app)),
        pystray.MenuItem("退出", lambda icon: os._exit(0))
    )
    icon = pystray.Icon("HealthAssistant", image, "久坐助手", menu)
    icon.run()

def select_music(app):
    file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
    if file_path:
        app.music_path = file_path

if __name__ == "__main__":
    assistant = HealthAssistant()
    
    # 开启逻辑线程
    logic_thread = threading.Thread(target=assistant.main_logic, daemon=True)
    logic_thread.start()
    
    
    # 启动托盘（主线程）
    # setup_tray(assistant) 
    # 注：测试时建议先直接运行 main_logic
    assistant.main_logic()
3. 实现文档说明
核心模块解析
置顶逻辑: 使用 root.attributes("-topmost", True)。这是 PRD 中最重要的“强制提醒”技术点，确保弹窗不会被电子书或浏览器遮挡。

音频播放: pygame.mixer 相比其他库对 .mp3 的兼容性更好，且支持异步播放，不会阻塞倒计时。

自启功能: winreg 模块直接操作 Windows 注册表。当用户运行一次程序后，它会自动注册到系统的启动项中。

防假死设计: 使用 threading 将计时逻辑与 GUI 渲染分开，防止在 25 分钟等待期间软件出现“未响应”的情况。

4. 后续打包建议
为了让它像真正的软件一样运行，你可以使用 PyInstaller 将其打包成 .exe 文件：

Bash
pip install pyinstaller
pyinstaller --noconsole --onefile --icon=app.ico main.py
--noconsole: 运行时不显示黑色的命令行窗口。

--onefile: 将所有依赖打包进一个文件。