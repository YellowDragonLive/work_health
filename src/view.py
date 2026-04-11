import tkinter as tk
import logging

_active_window = None


def show_reminder_process(message, duration, on_rest, on_snooze):
    """Helper to instantiate and show the window in the main thread."""
    global _active_window
    if _active_window:
        _active_window.force_close()

    _active_window = ReminderWindow(message, duration, on_rest, on_snooze)
    _active_window.show()


def close_active_window():
    """Explicitly closes the active reminder window from anywhere."""
    global _active_window
    if _active_window:
        _active_window.force_close()
        _active_window = None


class ReminderWindow:
    def __init__(self, message, duration_seconds, on_start_rest, on_snooze):
        self.message = message
        self.duration_seconds = duration_seconds
        self.on_start_rest = on_start_rest
        self.on_snooze = on_snooze

        self.root = None
        self.timer_id = None
        self.hide_timer_id = None
        self.is_closed = False

    def show(self):
        try:
            import main as _main

            parent = _main.tk_root
        except Exception:
            parent = None

        self.root = tk.Toplevel(parent)
        self.root.title("久坐提醒")
        self.root.protocol("WM_DELETE_WINDOW", self.force_close)

        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#2c3e50")

        self.main_container = tk.Frame(self.root, bg="#2c3e50")
        self.main_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.lbl_msg = tk.Label(
            self.main_container,
            text=self.message,
            font=("Microsoft YaHei UI", 32, "bold"),
            fg="white",
            bg="#2c3e50",
            wraplength=800,
        )
        self.lbl_msg.pack(pady=60)

        self.frame_btns = tk.Frame(self.main_container, bg="#2c3e50")
        self.frame_btns.pack(pady=20)

        self.btn_rest = tk.Button(
            self.frame_btns,
            text="开始休息 (Start Break)",
            command=self._handle_start_rest,
            font=("Microsoft YaHei UI", 18, "bold"),
            bg="#27ae60",
            fg="white",
            relief="flat",
            padx=40,
            pady=20,
        )
        self.btn_rest.pack(side=tk.LEFT, padx=30)

        self.btn_snooze = tk.Button(
            self.frame_btns,
            text="推迟 5 分钟",
            command=self._handle_snooze,
            font=("Microsoft YaHei UI", 18, "bold"),
            bg="#e67e22",
            fg="white",
            relief="flat",
            padx=40,
            pady=20,
        )
        self.btn_snooze.pack(side=tk.LEFT, padx=30)

        self.btn_hide = tk.Button(
            self.main_container,
            text="处理其他事务 (暂时隐藏 15 秒) [Esc]",
            command=self._handle_hide,
            font=("Microsoft YaHei UI", 12),
            bg="#7f8c8d",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
        )
        self.btn_hide.pack(pady=40)

        self.lbl_timer = tk.Label(
            self.main_container,
            text="",
            font=("Segoe UI", 80, "bold"),
            fg="#e74c3c",
            bg="#2c3e50",
        )

        self.root.bind("<Escape>", lambda e: self._handle_hide())

        self.root.lift()
        self.root.focus_force()

        logging.info("ReminderWindow: wait_window started.")
        self.root.wait_window(self.root)
        logging.info("ReminderWindow: wait_window returned (window closed).")

    def _handle_start_rest(self):
        if self.is_closed:
            return

        if self.on_start_rest:
            self.on_start_rest()

        self.btn_rest.pack_forget()
        self.btn_snooze.pack_forget()
        self.lbl_msg.config(text="请起立活动！")
        self.lbl_timer.pack(pady=20)

        self._start_countdown(self.duration_seconds)

    def _handle_snooze(self):
        if self.is_closed:
            return
        if self.on_snooze:
            self.on_snooze()
        self.force_close()

    def _handle_hide(self):
        if self.is_closed:
            return

        logging.info("Hiding window for 15 seconds")
        self.root.withdraw()

        self._cancel_timer("hide_timer_id")

        def restore():
            if self.is_closed:
                return
            logging.info("Restoring window after 15 seconds")
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

        self.hide_timer_id = self.root.after(15000, restore)

    def _start_countdown(self, remaining):
        if self.is_closed:
            return

        if remaining < 0:
            self.force_close()
            return

        mins, secs = divmod(remaining, 60)
        self.lbl_timer.config(text=f"{mins:02d}:{secs:02d}")

        self._cancel_timer("timer_id")
        self.timer_id = self.root.after(
            1000, lambda: self._start_countdown(remaining - 1)
        )

    def _cancel_timer(self, attr_name):
        timer_id = getattr(self, attr_name, None)
        if timer_id and self.root:
            try:
                self.root.after_cancel(timer_id)
            except Exception:
                pass
        setattr(self, attr_name, None)

    def force_close(self):
        if self.is_closed:
            return

        logging.info("ReminderWindow: force_close executing.")
        self.is_closed = True

        self._cancel_timer("timer_id")
        self._cancel_timer("hide_timer_id")

        if self.root:
            try:
                self.root.destroy()
            except Exception as e:
                logging.error(f"Error destroying window: {e}")
            self.root = None
