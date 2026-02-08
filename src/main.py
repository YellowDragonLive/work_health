import threading
import os
import sys
import time
import pystray
import logging
from PIL import Image
from monitor import Monitor
from config_manager import load_config, save_config, load_health_data
from utils import hide_console, set_autostart
from health_view import record_health_data, check_today_record_status

# Configure Logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "app.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception
logging.info("--- Application Started ---")

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
monitor_app = None

def on_quit(icon, item):
    global monitor_app
    icon.stop()
    if monitor_app:
        monitor_app.stop()
    os._exit(0)

def select_music(icon, item):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    file_path = filedialog.askopenfilename(
        title="选择提醒音乐",
        filetypes=[("音乐文件", "*.mp3 *.wav"), ("所有文件", "*.*")]
    )
    root.destroy()
    if file_path:
        if monitor_app.audio.set_music(file_path):
            config = load_config()
            config["music_path"] = file_path
            save_config(config)
            logging.info(f"Music updated to: {file_path}")

def set_duration(icon, item):
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.title("设定计时时长")
    root.attributes("-topmost", True)
    width, height = 300, 150
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{int(sw/2-width/2)}+{int(sh/2-height/2)}")
    tk.Label(root, text="请输入工作时长 (1-120 分钟):", pady=10).pack()
    entry = tk.Entry(root, justify='center')
    entry.insert(0, str(monitor_app.work_duration_minutes))
    entry.pack(pady=5)
    entry.focus_set()
    result = {"val": None}
    def on_confirm(event=None):
        try:
            val = int(entry.get())
            if 1 <= val <= 120:
                result["val"] = val
                root.destroy()
            else:
                messagebox.showwarning("范围错误", "请输入 1 到 120 之间的数字")
        except ValueError:
            messagebox.showerror("格式错误", "请输入有效的数字")
    tk.Button(root, text="确定", command=on_confirm, width=10).pack(pady=10)
    root.bind("<Return>", on_confirm)
    root.bind("<Escape>", lambda e: root.destroy())
    root.mainloop()
    if result["val"]:
        monitor_app.update_work_duration(result["val"])
        config = load_config()
        config["work_duration"] = result["val"]
        save_config(config)

def record_health_data_threaded(icon, item):
    """Run health data GUI in a separate thread to ensure responsiveness."""
    thread = threading.Thread(target=record_health_data, args=(icon, item), daemon=True)
    thread.start()

def get_status_text(item):

    if not monitor_app: return "启动中..."
    mins, secs = divmod(int(monitor_app.work_time_remaining), 60)
    state_map = {"WORK": "工作中", "PROMPT": "提醒中", "BREAK": "休息中", "SNOOZE": "已推迟"}
    state_text = state_map.get(monitor_app.state, monitor_app.state)
    return f"状态: {state_text} | 剩余: {mins:02d}:{secs:02d} | 已完成: {monitor_app.completed_rounds} 轮"

def setup_tray():
    icon_path = os.path.join(ASSETS_DIR, "icon.png")
    image = Image.open(icon_path)
    menu = pystray.Menu(
        pystray.MenuItem(get_status_text, lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(lambda item: "记录今日指标" + check_today_record_status(), record_health_data_threaded),
        pystray.Menu.SEPARATOR,

        pystray.MenuItem("重置并开始工作", lambda icon, item: monitor_app.reset_work()),
        pystray.MenuItem("设定计时时长", set_duration),
        pystray.MenuItem("选择提醒音乐", select_music),
        pystray.MenuItem("启用/禁用开机自启", lambda icon, item: set_autostart(True)),
        pystray.MenuItem("退出", on_quit)
    )
    return pystray.Icon("HealthAssistant", image, "久坐助手", menu)

def main():
    global monitor_app
    import socket
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(("127.0.0.1", 45678))
    except socket.error:
        os._exit(0)
    
    config = load_config()
    custom_music = config.get("music_path")
    work_dur = config.get("work_duration", 25)
    
    if not custom_music:
        default_p = r"x:\work_code\work_health\Bonus Track04.炎と永远——罗德岛战记1OP.mp3"
        if os.path.exists(default_p): custom_music = default_p

    monitor_app = Monitor(ASSETS_DIR, music_path=custom_music, work_duration_minutes=work_dur)
    threading.Thread(target=monitor_app.run, daemon=True).start()

    icon = setup_tray()
    def refresh_loop():
        while icon.visible:
            icon.title = get_status_text(None)
            icon.update_menu()
            time.sleep(1)
    threading.Thread(target=refresh_loop, daemon=True).start()
    
    from datetime import date
    if str(date.today()) not in load_health_data():
        icon.notify("Master, 别忘了记录今天的体重和血压哦！", "每日健康提醒")
    
    icon.run()

if __name__ == "__main__":
    hide_console()
    if not os.path.exists(ASSETS_DIR):
        print("Assets not found. Run generate_assets.py first.")
    else:
        main()
