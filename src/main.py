import threading
import os
import sys
import pystray
from PIL import Image
from monitor import Monitor
import winreg
import json
import ctypes
import logging
import traceback

# Configure Logging
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.log")
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

def hide_console():
    """Ensure the application runs without a console window."""
    # 1. If we are running on 'python.exe', try to relaunch using 'pythonw.exe'
    current_exe = sys.executable
    if current_exe.lower().endswith("python.exe"):
        pythonw = current_exe.lower().replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            import subprocess
            # Launch the same script with pythonw
            subprocess.Popen([pythonw] + sys.argv, creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0) # Kill the console-bound process

    # 2. Fallback: Try to hide the current console window via WinAPI
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0) # 0 = SW_HIDE



# Ensure we can find assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"music_path": None, "work_duration": 25}


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Save Config Error: {e}")


def set_autostart(enable=True):
    app_name = "HealthAssistant"
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enable:
            # Prefer pythonw.exe to avoid console window on startup
            exe_path = sys.executable
            target_exe = exe_path.replace("python.exe", "pythonw.exe")
            if not os.path.exists(target_exe):
                target_exe = exe_path
                
            script_path = os.path.abspath(__file__)
            cmd = f'"{target_exe}" "{script_path}"'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            print(f"Autostart enabled with: {cmd}")

        else:
            try:
                winreg.DeleteValue(key, app_name)
                print("Autostart disabled.")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Registry (Autostart) Error: {e}")

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
    # Use a hidden root window for the dialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # Ensure dialog is visible
    
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
            print(f"Music updated to: {file_path}")

def set_duration(icon, item):
    import tkinter as tk
    
    # We use a Toplevel-like approach but with its own mainloop 
    # since we are in a subthread.
    root = tk.Tk()
    root.title("设定计时时长")
    root.attributes("-topmost", True)
    
    # Center the window
    width, height = 300, 150
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{int(sw/2-width/2)}+{int(sh/2-height/2)}")
    
    label = tk.Label(root, text="请输入工作时长 (1-120 分钟):", pady=10)
    label.pack()
    
    entry = tk.Entry(root, justify='center')
    entry.insert(0, str(monitor_app.work_duration_minutes))
    entry.pack(pady=5)
    entry.focus_set()
    entry.selection_range(0, tk.END)
    
    result = {"val": None}
    
    def on_confirm(event=None):
        try:
            val = int(entry.get())
            if 1 <= val <= 120:
                result["val"] = val
                root.destroy()
            else:
                from tkinter import messagebox
                messagebox.showwarning("范围错误", "请输入 1 到 120 之间的数字")
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("格式错误", "请输入有效的数字")

    btn = tk.Button(root, text="确定", command=on_confirm, width=10)
    btn.pack(pady=10)
    
    root.bind("<Return>", on_confirm)
    root.bind("<Escape>", lambda e: root.destroy())
    
    root.lift()
    root.focus_force()
    root.mainloop()
    
    new_dur = result["val"]
    if new_dur:
        monitor_app.update_work_duration(new_dur)
        config = load_config()
        config["work_duration"] = new_dur
        save_config(config)
        logging.info(f"Work duration updated to {new_dur} minutes")

def get_status_text(item):
    if not monitor_app:
        return "启动中..."
    
    mins, secs = divmod(int(monitor_app.work_time_remaining), 60)
    time_str = f"{mins:02d}:{secs:02d}"

    
    state_map = {
        "WORK": "工作中",
        "PROMPT": "提醒中",
        "BREAK": "休息中",
        "SNOOZE": "已推迟"
    }
    state_text = state_map.get(monitor_app.state, monitor_app.state)
    
    return f"状态: {state_text} | 剩余: {time_str} | 已完成: {monitor_app.completed_rounds} 轮"



def setup_tray():
    global monitor_app
    icon_path = os.path.join(ASSETS_DIR, "icon.png")
    image = Image.open(icon_path)
    
    menu = pystray.Menu(
        pystray.MenuItem(get_status_text, lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("重置并开始工作", lambda icon, item: monitor_app.reset_work()),
        pystray.MenuItem("设定计时时长", set_duration),
        pystray.MenuItem("选择提醒音乐", select_music),
        pystray.MenuItem("启用/禁用开机自启", lambda icon, item: set_autostart(True)),
        pystray.MenuItem("退出", on_quit)
    )



    
    icon = pystray.Icon("HealthAssistant", image, "久坐助手", menu)
    return icon

def main():
    global monitor_app
    
    # Singleton check using socket
    import socket
    try:
        # We try to bind to a specific port. If it fails, another instance is running.
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(("127.0.0.1", 45678)) 
        # Keep the socket open to maintain the lock
    except socket.error:
        print("Another instance is already running. Exiting.")
        os._exit(0)
    
    # 1. Start Monitor in Thread
    config = load_config()
    custom_music = config.get("music_path")
    work_dur = config.get("work_duration", 25)
    
    # Fallback to the requested default if no config exists
    if not custom_music:
        default_requested = r"x:\work_code\work_health\Bonus Track04.炎と永远——罗德岛战记1OP.mp3"
        if os.path.exists(default_requested):
            custom_music = default_requested

    monitor_app = Monitor(ASSETS_DIR, music_path=custom_music, work_duration_minutes=work_dur)

    t = threading.Thread(target=monitor_app.run, daemon=True)
    t.start()

    
    # 2. Start Tray (Blocking Main Thread)
    icon = setup_tray()
    
    # Start a background thread to refresh the tray menu and title (tooltip)
    def refresh_loop():
        while icon.visible:
            # Update Tooltip (This will show live time when hovering)
            status = get_status_text(None)
            icon.title = status
            # Request menu update (will affect next time the menu is opened)
            icon.update_menu()
            time.sleep(1)
            
    refresh_t = threading.Thread(target=refresh_loop, daemon=True)
    refresh_t.start()

    
    icon.run()


if __name__ == "__main__":
    # Hide the console window on startup
    hide_console()
    
    # Ensure assets exist
    if not os.path.exists(ASSETS_DIR):
        print(f"Assets not found at {ASSETS_DIR}. Please run generate_assets.py.")
    else:
        main()

