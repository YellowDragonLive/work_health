import tkinter as tk
import logging

_active_window = None


def show_reminder_process(message, duration, on_rest, on_snooze, on_close=None,
                          question=None, on_answer=None):
    """Helper to instantiate and show the window in the main thread.

    Args:
        question: dict with 'id', 'en', 'zh' keys — the reflection question to display.
        on_answer: callable(question_id, answer_text) — called when user submits an answer.
    """
    global _active_window
    if _active_window:
        _active_window.force_close()

    _active_window = ReminderWindow(
        message, duration, on_rest, on_snooze, on_close,
        question=question, on_answer=on_answer,
    )
    _active_window.show()


def close_active_window():
    """Explicitly closes the active reminder window from anywhere."""
    global _active_window
    if _active_window:
        _active_window.force_close()
        _active_window = None


class ReminderWindow:
    def __init__(self, message, duration_seconds, on_start_rest, on_snooze, on_close,
                 question=None, on_answer=None):
        self.message = message
        self.duration_seconds = duration_seconds
        self.on_start_rest = on_start_rest
        self.on_snooze = on_snooze
        self.on_close = on_close
        self.question = question
        self.on_answer = on_answer

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

        # --- 自省问题区域 (初始隐藏，点"开始休息"后展示) ---
        self.question_frame = tk.Frame(self.main_container, bg="#34495e",
                                       padx=40, pady=30)
        # 问题内容 labels — 稍后在 _show_question 中填充

        # --- 回答输入区域 (休息结束后展示) ---
        self.answer_frame = tk.Frame(self.main_container, bg="#2c3e50")

        self.root.bind("<Escape>", lambda e: self._handle_hide())

        self.root.lift()
        self.root.focus_force()

        logging.info("ReminderWindow: Window shown (non-blocking).")

    def _handle_start_rest(self):
        if self.is_closed:
            return

        if self.on_start_rest:
            self.on_start_rest()

        self.btn_rest.pack_forget()
        self.btn_snooze.pack_forget()
        self.btn_hide.pack_forget()

   

        # 展示思考题
        if self.question:
            self._show_question()

        # 展示倒计时
        self.lbl_timer.pack(pady=20)

        self._start_countdown(self.duration_seconds)

    def _show_question(self):
        """在休息倒计时期间展示自省问题。"""
        if not self.question:
            return

        self.question_frame.pack(pady=30, fill=tk.X, padx=60)

        # 分隔线标题
        tk.Label(
            self.question_frame,
            text="💭 此刻思考 — Reflect on this",
            font=("Microsoft YaHei UI", 16, "bold"),
            fg="#f39c12",
            bg="#34495e",
        ).pack(pady=(0, 20))

        # 英文原文
        tk.Label(
            self.question_frame,
            text=self.question["en"],
            font=("Segoe UI", 22, "italic", "bold"),
            fg="#ecf0f1",
            bg="#34495e",
            wraplength=1000,
            justify=tk.CENTER,
        ).pack(pady=(0, 15), anchor=tk.CENTER)

        # 中文释义
        tk.Label(
            self.question_frame,
            text=self.question["zh"],
            font=("Microsoft YaHei UI", 20, "bold"),
            fg="#bdc3c7",
            bg="#34495e",
            wraplength=1000,
            justify=tk.CENTER,
        ).pack(pady=(0, 10), anchor=tk.CENTER)

    def _show_answer_input(self):
        """休息结束后，展示回答输入框。"""
        if not self.question:
            self.force_close()
            return

        # 隐藏倒计时
        self.lbl_timer.pack_forget()
        # 保留问题展示

        self.lbl_msg.config(
            text="休息结束！请写下你的思考 ✍️",
            font=("Microsoft YaHei UI", 24, "bold"),
            fg="#2ecc71",
        )

        self.answer_frame.pack(pady=20, fill=tk.X, padx=80)

        # 输入提示
        tk.Label(
            self.answer_frame,
            text="你的回答（按 Ctrl+Enter 提交，Esc 跳过）：",
            font=("Microsoft YaHei UI", 12),
            fg="#95a5a6",
            bg="#2c3e50",
        ).pack(anchor=tk.W, pady=(0, 8))

        # 多行文本框
        self.text_answer = tk.Text(
            self.answer_frame,
            font=("Microsoft YaHei UI", 13),
            bg="#34495e",
            fg="#ecf0f1",
            insertbackground="#ecf0f1",
            relief="flat",
            height=6,
            wrap=tk.WORD,
            padx=15,
            pady=10,
        )
        self.text_answer.pack(fill=tk.X, pady=(0, 15))
        self.text_answer.focus_set()

        # 按钮区
        btn_frame = tk.Frame(self.answer_frame, bg="#2c3e50")
        btn_frame.pack()

        tk.Button(
            btn_frame,
            text="提交回答 (Submit)",
            command=self._submit_answer,
            font=("Microsoft YaHei UI", 14, "bold"),
            bg="#27ae60",
            fg="white",
            relief="flat",
            padx=30,
            pady=12,
        ).pack(side=tk.LEFT, padx=15)

        tk.Button(
            btn_frame,
            text="跳过 (Skip)",
            command=self.force_close,
            font=("Microsoft YaHei UI", 14),
            bg="#7f8c8d",
            fg="white",
            relief="flat",
            padx=30,
            pady=12,
        ).pack(side=tk.LEFT, padx=15)

        # 快捷键
        self.text_answer.bind("<Control-Return>", lambda e: self._submit_answer())
        self.root.bind("<Escape>", lambda e: self.force_close())

    def _submit_answer(self):
        """保存回答并关闭窗口。"""
        if self.is_closed:
            return

        answer_text = self.text_answer.get("1.0", tk.END).strip()
        if answer_text and self.on_answer and self.question:
            try:
                self.on_answer(self.question["id"], answer_text)
                logging.info(f"Journal answer saved for question {self.question['id']}")
            except Exception as e:
                logging.error(f"Error saving journal answer: {e}", exc_info=True)

        self.force_close()

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
            # 倒计时结束 → 弹出回答输入框
            self._show_answer_input()
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

        if self.on_close:
            try:
                self.on_close()
            except Exception as e:
                logging.error(f"Error in on_close callback: {e}")
