import time
import ctypes
import os
import threading
import logging
from datetime import date

# Constants
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
    def __init__(
        self,
        assets_dir,
        music_path=None,
        work_duration_minutes=25,
        break_duration_seconds=5 * 60,
        snooze_duration_seconds=5 * 60,
        gui_queue=None,
    ):
        self.assets_dir = assets_dir
        self.running = True
        self.paused = False
        self.state = "WORK"  # WORK, PROMPT, BREAK, SNOOZE
        self.work_duration_minutes = work_duration_minutes
        self.break_duration_seconds = break_duration_seconds
        self.snooze_duration_seconds = snooze_duration_seconds
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

        # 自省问答追踪：当天已展示过的问题 ID
        self.shown_question_ids = []

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

        # 挑选一个自省问题
        current_question = None
        try:
            from questions import pick_random_question
            current_question = pick_random_question(exclude_ids=self.shown_question_ids)
            if current_question:
                self.shown_question_ids.append(current_question["id"])
                logging.info(f"Selected reflection question: {current_question['id']}")
        except Exception as e:
            logging.error(f"Error picking question: {e}", exc_info=True)

        # 用 Event 等待主线程弹窗关闭
        done_event = threading.Event()

        def show_window():
            """此函数由主线程通过 gui_queue 调用，在主线程安全地创建 Tkinter 窗口。"""
            from view import show_reminder_process

            try:
                # 再次检查状态，如果在等待期间被重置了就直接返回
                if self.state not in ["PROMPT", "BREAK"]:
                    logging.info(
                        "State changed before window could be shown, aborting show."
                    )
                    done_event.set()
                    return

                msg = (
                    f"请起身活动"
                    if self.break_duration_seconds < 60
                    else f"请起身活动 {self.break_duration_seconds // 60} 分钟！"
                )

                def on_close_callback():
                    # 只有从弹窗真正关闭时，才唤醒挂起的Monitor后台线程
                    done_event.set()

                show_reminder_process(
                    message=msg,
                    duration=self.break_duration_seconds,
                    on_rest=self.on_user_start_rest,
                    on_snooze=self.on_user_snooze,
                    on_close=on_close_callback,
                    question=current_question,
                    on_answer=self._save_journal_answer,
                )
            except Exception as e:
                logging.error(f"GUI Error in show_window: {e}", exc_info=True)
                self.audio.stop()
                self.reset_work()
                done_event.set()

        if self.gui_queue:
            self.gui_queue.put(show_window)
            logging.info("Reminder window task queued. Waiting for user response...")
            done_event.wait()  # 阻塞 Monitor 线程，等待弹窗关闭
        else:
            # 降级：没有 gui_queue 时直接调用（不推荐，调试用）
            show_window()
            done_event.wait()

        # 弹窗关闭后处理状态
        if self.state in ["PROMPT", "BREAK"]:
            logging.info(f"Window closed in state {self.state}. Resetting to Work.")
            self.reset_work()

    def _save_journal_answer(self, question_id, answer_text):
        """保存自省问答回答到 journal_data.json。"""
        try:
            from config_manager import load_journal_data, save_journal_data
            from questions import get_question_by_id
            import time as _time

            today_str = str(date.today())
            data = load_journal_data()

            if today_str not in data:
                data[today_str] = {"answers": [], "created_at": _time.strftime("%H:%M:%S")}

            q = get_question_by_id(question_id)
            entry = {
                "question_id": question_id,
                "question_en": q["en"] if q else "",
                "question_zh": q["zh"] if q else "",
                "answer": answer_text,
                "answered_at": _time.strftime("%H:%M:%S"),
            }
            data[today_str]["answers"].append(entry)
            save_journal_data(data)
            logging.info(f"Journal answer saved: {question_id} at {entry['answered_at']}")
        except Exception as e:
            logging.error(f"Failed to save journal answer: {e}", exc_info=True)

    def on_user_start_rest(self):
        logging.info("User started rest.")
        self.state = "BREAK"

    def on_user_snooze(self):
        logging.info("User snoozed.")
        self.state = "SNOOZE"
        self.audio.stop()
        self.work_time_remaining = self.snooze_duration_seconds
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

        if self.gui_queue:

            def close_windows():
                try:
                    from view import close_active_window

                    close_active_window()
                except Exception as e:
                    logging.error(f"Error closing active window: {e}")

                # 兜底：销毁可能存在的其他顶层窗口（如健康录入等）
                try:
                    import tkinter as tk
                    import main as _main

                    parent = getattr(_main, "tk_root", None)
                    if parent:
                        for widget in parent.winfo_children():
                            if isinstance(widget, tk.Toplevel):
                                widget.destroy()
                except Exception as e:
                    logging.error(f"Error closing Toplevels: {e}")

            self.gui_queue.put(close_windows)

    def update_work_duration(self, minutes):
        self.work_duration_minutes = minutes
        self.reset_work()

    def stop(self):
        self.running = False
        self.audio.stop()
