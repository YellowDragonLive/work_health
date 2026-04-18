import queue
import threading
import os
import sys
import time
import pystray
import logging
from PIL import Image
from monitor import Monitor
from config_manager import load_config, save_config, load_health_data, check_today_record_status
from utils import hide_console, is_autostart_enabled, set_autostart

# Configure Logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "app.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
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
tk_root = None
gui_queue = queue.Queue()  # 主线程 GUI 任务队列


def on_quit(icon, item):
    global monitor_app
    logging.info("User quit.")
    icon.stop()
    if monitor_app:
        monitor_app.stop()
    # 安全地关闭主线程 Tk 根窗口
    if tk_root:
        tk_root.after(0, tk_root.destroy)


def select_music(icon, item):
    """通过队列在主线程打开文件选择对话框。"""
    done_event = threading.Event()
    result = {}

    def do_select():
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            parent=tk_root,
            title="选择提醒音乐",
            filetypes=[("音乐文件", "*.mp3 *.wav"), ("所有文件", "*.*")],
        )
        result["path"] = file_path
        done_event.set()

    gui_queue.put(do_select)
    done_event.wait()

    file_path = result.get("path", "")
    if file_path:
        if monitor_app.audio.set_music(file_path):
            config = load_config()
            config["music_path"] = file_path
            save_config(config)
            logging.info(f"Music updated to: {file_path}")


def set_duration(icon, item):
    """通过队列在主线程展示设置时长对话框。"""
    done_event = threading.Event()
    result = {"val": None}

    def do_set_duration():
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Toplevel(tk_root)
        root.title("设定计时时长")
        root.attributes("-topmost", True)
        width, height = 300, 150
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(
            f"{width}x{height}+{int(sw / 2 - width / 2)}+{int(sh / 2 - height / 2)}"
        )
        tk.Label(root, text="请输入工作时长 (1-120 分钟):", pady=10).pack()
        entry = tk.Entry(root, justify="center")
        entry.insert(0, str(monitor_app.work_duration_minutes))
        entry.pack(pady=5)
        entry.focus_set()
        entry.focus_force()

        def on_confirm(event=None):
            try:
                val = int(entry.get())
                if 1 <= val <= 120:
                    result["val"] = val
                    root.destroy()
                else:
                    messagebox.showwarning(
                        "范围错误", "请输入 1 到 120 之间的数字", parent=root
                    )
            except ValueError:
                messagebox.showerror("格式错误", "请输入有效的数字", parent=root)

        tk.Button(root, text="确定", command=on_confirm, width=10).pack(pady=10)
        root.bind("<Return>", on_confirm)
        root.bind("<Escape>", lambda e: root.destroy())
        root.wait_window(root)
        done_event.set()

    gui_queue.put(do_set_duration)
    done_event.wait()

    if result["val"]:
        monitor_app.update_work_duration(result["val"])
        config = load_config()
        config["work_duration"] = result["val"]
        save_config(config)


def record_health_data_threaded(icon, item):
    """在主线程调度整合后的手动录入 GUI。"""
    from view import show_manual_record

    gui_queue.put(
        lambda: show_manual_record(on_answer=monitor_app._save_journal_answer)
    )


def toggle_autostart(icon, item):
    enable = not is_autostart_enabled()
    set_autostart(enable)
    logging.info("Autostart toggled. Enabled=%s", enable)
    try:
        icon.update_menu()
    except Exception:
        logging.debug(
            "Failed to refresh tray menu after toggling autostart.", exc_info=True
        )


def get_status_text(item):
    if not monitor_app:
        return "启动中..."
    mins, secs = divmod(int(monitor_app.work_time_remaining), 60)
    state_map = {
        "WORK": "工作中",
        "PROMPT": "提醒中",
        "BREAK": "休息中",
        "SNOOZE": "已推迟",
    }
    state_text = state_map.get(monitor_app.state, monitor_app.state)
    return f"状态: {state_text} | 剩余: {mins:02d}:{secs:02d} | 已完成: {monitor_app.completed_rounds} 轮"


def setup_tray():
    icon_path = os.path.join(ASSETS_DIR, "icon.png")
    image = Image.open(icon_path)
    menu = pystray.Menu(
        pystray.MenuItem(get_status_text, lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda item: "记录今日指标" + check_today_record_status(),
            record_health_data_threaded,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("重置并开始工作", lambda icon, item: monitor_app.reset_work()),
        pystray.MenuItem("设定计时时长", set_duration),
        pystray.MenuItem("选择提醒音乐", select_music),
        pystray.MenuItem(
            lambda item: "禁用开机自启" if is_autostart_enabled() else "启用开机自启",
            toggle_autostart,
        ),
        pystray.MenuItem("退出", on_quit),
    )
    return pystray.Icon("HealthAssistant", image, "久坐助手", menu)


def main():
    global monitor_app, tk_root
    import socket
    import tkinter as tk
    import sys

    is_test_mode = "--test" in sys.argv

    # 单例锁
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(("127.0.0.1", 45678))
    except socket.error:
        logging.warning("Another instance is already running. Exiting.")
        os._exit(0)

    config = load_config()
    custom_music = config.get("music_path")
    work_dur = config.get("work_duration", 25)
    break_dur = 5 * 60
    snooze_dur = 5 * 60

    if is_test_mode:
        logging.info("Starting in TEST MODE: 1 min work, 30 sec break/snooze")
        work_dur = 0.1
        break_dur = 10
        snooze_dur = 10

    if not custom_music:
        # 使用相对路径计算默认音乐位置
        default_p = os.path.join(
            os.path.dirname(BASE_DIR), "Bonus Track04.炎と永远——罗德岛战记1OP.mp3"
        )
        if os.path.exists(default_p):
            custom_music = default_p

    # Monitor 子线程，传入 gui_queue 供弹窗调度
    monitor_app = Monitor(
        ASSETS_DIR,
        music_path=custom_music,
        work_duration_minutes=work_dur,
        break_duration_seconds=break_dur,
        snooze_duration_seconds=snooze_dur,
        gui_queue=gui_queue,
    )
    threading.Thread(target=monitor_app.run, daemon=True).start()

    # 托盘图标在子线程运行（detached），主线程留给 Tkinter
    icon = setup_tray()
    icon.run_detached()
    logging.info("Tray icon started (detached).")

    # 托盘状态刷新线程
    def refresh_loop():
        while monitor_app.running:
            try:
                icon.title = get_status_text(None)
                icon.update_menu()
            except Exception:
                pass
            time.sleep(1)

    threading.Thread(target=refresh_loop, daemon=True).start()

    # 每日提醒通知
    from datetime import date

    if str(date.today()) not in load_health_data():
        icon.notify("Master, 别忘了记录今天的体重和血压哦！", "每日健康提醒")

    # ===== 主线程：Tkinter 消息泵 =====
    tk_root = tk.Tk()
    tk_root.withdraw()  # 隐藏根窗口，仅作为 Toplevel 的父窗口和消息泵
    tk_root.title("HealthAssistant_Root")

    def process_gui_queue():
        """主线程定期轮询 GUI 任务队列并执行。"""
        try:
            while True:
                task = gui_queue.get_nowait()
                try:
                    task()
                except Exception as e:
                    logging.error(f"GUI task error: {e}", exc_info=True)
        except queue.Empty:
            pass
        # 100ms 后再次检查
        tk_root.after(100, process_gui_queue)

    tk_root.after(100, process_gui_queue)
    logging.info("Main thread entering Tkinter mainloop.")
    tk_root.mainloop()
    logging.info("Tkinter mainloop exited. Application stopping.")


if __name__ == "__main__":
    hide_console()
    if not os.path.exists(ASSETS_DIR):
        print("Assets not found. Run generate_assets.py first.")
    else:
        main()
