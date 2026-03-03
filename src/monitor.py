import time
import ctypes
import os
import threading
import logging

# Constants
WORK_DURATION = 25 * 60
BREAK_DURATION = 5 * 60
SNOOZE_DURATION = 5 * 60
IDLE_PAUSE_THRESHOLD = 1200  # 20 minutes without input before pausing


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]

def get_idle_duration():
    """Returns the time in seconds since the last user input (mouse/keyboard)."""
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo)):
        millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return max(0, millis / 1000.0)
    return 0


def _send_global_pause():
    """Sends a global media STOP command using virtual keys."""
    logging.info("Sending global media STOP via keybd_event (0xB2)")
    # 0xB2 is VK_MEDIA_STOP. 
    # Unlike PLAY_PAUSE (0xB3), STOP will not resume already paused media.
    # It is broadcasted globally by the OS to all listening apps (Chrome, Spotify, etc.)
    user32 = ctypes.windll.user32
    user32.keybd_event(0xB2, 0, 0, 0)  # Key down
    user32.keybd_event(0xB2, 0, 2, 0)  # Key up

def pause_all_media():
    """Only pause media. Resuming is left to the user."""
    logging.info("Executing pause_all_media sequence.")
    # We use STOP (15) instead of PAUSE (47) to avoid "toggle" behavior
    # where an already paused player starts playing again.
    _send_global_pause()

def resume_all_media():
    """Do nothing. Resuming is left to the user as requested."""
    logging.info("resume_all_media called, but skipping execution as per user request.")
    pass


class Monitor:
    def __init__(self, assets_dir, music_path=None, work_duration_minutes=25, gui_queue=None):
        self.assets_dir = assets_dir
        self.running = True
        self.paused = False
        self.state = "WORK"  # WORK, PROMPT, BREAK, SNOOZE
        self.work_duration_minutes = work_duration_minutes
        self.completed_rounds = 0
        self.gui_queue = gui_queue  # 主线程 GUI 任务队列

        # Audio
        from audio import AudioManager
        if music_path and os.path.exists(music_path):
            target_music = music_path
        else:
            target_music = os.path.join(assets_dir, "default_music.wav")

        self.audio = AudioManager(target_music)

        # Config
        self.work_time_remaining = self.work_duration_minutes * 60
        self.last_sync_time = time.time()

        self.lock = threading.Lock()

    def is_system_locked(self):
        """Checks if the workstation is locked (simplified heuristic)."""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            return hwnd == 0
        except Exception:
            return False

    def check_activity_status(self):
        """Updates paused state based on lock status and idle time."""
        locked = self.is_system_locked()
        idle_sec = get_idle_duration()

        should_pause = locked or (idle_sec >= IDLE_PAUSE_THRESHOLD)

        if should_pause and not self.paused:
            reason = "Locked" if locked else f"Idle ({int(idle_sec)}s)"
            logging.info(f"System {reason}. Pausing timer.")
            self.paused = True
        elif not should_pause and self.paused:
            logging.info("User active. Resuming.")
            self.paused = False

    def run(self):
        """Main loop. Runs in a background thread."""
        logging.info("Monitor thread started.")
        while self.running:
            self.check_activity_status()

            if self.paused:
                time.sleep(1)
                self.last_sync_time = time.time()
                continue

            if self.state == "WORK":
                now = time.time()
                elapsed = now - self.last_sync_time
                self.last_sync_time = now

                if self.work_time_remaining > 0:
                    self.work_time_remaining -= elapsed
                    if self.work_time_remaining < 0:
                        self.work_time_remaining = 0
                    time.sleep(1)
                else:
                    self.trigger_break()

    def trigger_break(self):
        logging.info("Triggering break...")
        pause_all_media()
        self.state = "PROMPT"
        self.audio.play()

        # 用 Event 等待主线程弹窗关闭
        done_event = threading.Event()

        def show_window():
            """此函数由主线程通过 gui_queue 调用，在主线程安全地创建 Tkinter 窗口。"""
            from view import show_reminder_process
            try:
                show_reminder_process(
                    message="阅读结束，请起身活动 5 分钟！",
                    duration=BREAK_DURATION,
                    on_rest=self.on_user_start_rest,
                    on_snooze=self.on_user_snooze
                )
            except Exception as e:
                logging.error(f"GUI Error in show_window: {e}", exc_info=True)
                self.audio.stop()
                self.reset_work()
            finally:
                done_event.set()

        if self.gui_queue:
            self.gui_queue.put(show_window)
            logging.info("Reminder window task queued. Waiting for user response...")
            done_event.wait()  # 阻塞 Monitor 线程，等待弹窗关闭
        else:
            # 降级：没有 gui_queue 时直接调用（不推荐，调试用）
            show_window()

        # 弹窗关闭后处理状态
        if self.state in ["PROMPT", "BREAK"]:
            logging.info(f"Window closed in state {self.state}. Resetting to Work.")
            self.reset_work()

    def on_user_start_rest(self):
        logging.info("User started rest.")
        self.state = "BREAK"

    def on_user_snooze(self):
        logging.info("User snoozed.")
        self.state = "SNOOZE"
        self.audio.stop()
        self.work_time_remaining = SNOOZE_DURATION
        self.last_sync_time = time.time()
        self.state = "WORK"

    def reset_work(self):
        self.audio.stop()
        if self.state in ["PROMPT", "BREAK", "SNOOZE"]:
            resume_all_media()

        if self.state == "BREAK":
            self.completed_rounds += 1
        self.state = "WORK"
        self.work_duration_seconds = self.work_duration_minutes * 60
        self.work_time_remaining = self.work_duration_seconds
        self.last_sync_time = time.time()

    def update_work_duration(self, minutes):
        self.work_duration_minutes = minutes
        self.reset_work()

    def stop(self):
        self.running = False
        self.audio.stop()
