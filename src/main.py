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
            if "audio" not in config: config["audio"] = {}
            config["audio"]["reminder_rest_path"] = file_path
            monitor_app.music_path = file_path # 同步到 monitor
            save_config(config)
            logging.info(f"Music updated to: {file_path}")


def select_reflection_music(icon, item):
    """通过队列在主线程打开文件选择对话框（针对反思背景音乐）。"""
    done_event = threading.Event()
    result = {}

    def do_select():
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            parent=tk_root,
            title="选择反思/问答背景音乐",
            filetypes=[("音乐文件", "*.mp3 *.wav"), ("所有文件", "*.*")],
        )
        result["path"] = file_path
        done_event.set()

    gui_queue.put(do_select)
    done_event.wait()

    file_path = result.get("path", "")
    if file_path:
        # 我们不在这里直接 play，只更新配置和 monitor 状态
        config = load_config()
        if "audio" not in config: config["audio"] = {}
        config["audio"]["reflection_path"] = file_path
        if monitor_app:
            monitor_app.reflection_music_path = file_path
        save_config(config)
        logging.info(f"Reflection music updated to: {file_path}")




def record_health_data_threaded(icon, item):
    """在主线程调度整合后的手动录入 GUI。"""
    from view import show_manual_record

    gui_queue.put(
        lambda: show_manual_record(
            on_answer=monitor_app._save_journal_answer,
            on_reflection_start=monitor_app.on_user_start_reflection
        )
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
    mode_suffix = " [🌞晨间]" if monitor_app.mode_name == "morning_routine" else ""
    return f"状态: {state_text}{mode_suffix} | 剩余: {mins:02d}:{secs:02d} | 已完成: {monitor_app.completed_rounds} 轮"


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
        pystray.MenuItem("选择提醒音乐 (A)", select_music),
        pystray.MenuItem("选择反思音乐 (B)", select_reflection_music),
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
    
    # 确保 audio 配置结构存在
    if "audio" not in config:
        config["audio"] = {
            "reminder_rest_path": None,
            "reflection_path": None,
            "volume": 0.3
        }

    # 音乐路径发现逻辑
    audio_cfg = config["audio"]
    if not audio_cfg.get("reminder_rest_path"):
        default_p = os.path.join(
            os.path.dirname(BASE_DIR), "Bonus Track04.炎と永远——罗德岛战记1OP.mp3"
        )
        if os.path.exists(default_p):
            audio_cfg["reminder_rest_path"] = default_p

    if not audio_cfg.get("reflection_path"):
        default_r = os.path.join(
            os.path.dirname(BASE_DIR), "17.Tune the rainbow——翼神传说多元变奏曲.mp3"
        )
        if os.path.exists(default_r):
            audio_cfg["reflection_path"] = default_r
            
    # 持久化自动发现的路径
    save_config(config)

    if is_test_mode:
        logging.info("Starting in TEST MODE: Using 'test' profile from config")
        # 从配置中读取测试参数，若无则使用默认 0.1
        test_cfg = config.get("pomodoro", {}).get("test", {"work_duration": 0.1, "rest_duration": 0.1})
        config["pomodoro"] = {
            "default": test_cfg,
            "morning_routine": {"enabled": False}  # 测试模式下禁用其他时间策略干扰
        }

    # Monitor 子线程，传入 gui_queue 供弹窗调度
    monitor_app = Monitor(
        ASSETS_DIR,
        config=config,
        gui_queue=gui_queue,
    )

    # 检查是否有时间模拟请求
    for i, arg in enumerate(sys.argv):
        if arg == "--mock-hour" and i + 1 < len(sys.argv):
            try:
                from datetime import time as dt_time
                mock_h = int(sys.argv[i+1])
                monitor_app.virtual_time = dt_time(mock_h, 0)
                monitor_app._refresh_durations() # 立即触发一次刷新
                logging.info(f"Time Simulation Active: Set to {mock_h}:00")
            except Exception as e:
                logging.error(f"Failed to set mock hour: {e}")

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
