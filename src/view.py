import tkinter as tk
from tkinter import messagebox
import logging
import time
from datetime import date
from config_manager import load_health_data, save_health_data

_active_window = None


def show_reminder_process(message, duration, on_rest, on_snooze, on_close=None,
                          question=None, on_answer=None):
    """Helper to instantiate and show the window in the main thread."""
    global _active_window
    if _active_window:
        _active_window.force_close()

    _active_window = ReminderWindow(
        message, duration, on_rest, on_snooze, on_close,
        question=question, on_answer=on_answer,
    )
    _active_window.show()


def show_manual_record(on_answer=None):
    """Entry point for manual recording from tray menu or other sources."""
    global _active_window
    if _active_window:
        _active_window.force_close()
        
    # Create a dummy question for manual entry
    question = {
        "id": "manual_entry_" + str(int(time.time())),
        "en": "Capture your current health status and thoughts.",
        "zh": "记录当前的身体状态与思考。"
    }

    # Manual record: duration=0 跳过倒计时
    _active_window = ReminderWindow(
        "手动录入每日指标", 0, None, None, None,
        question=question, on_answer=on_answer
    )
    _active_window.show()
    # 直接构建三栏并进入回答模式（跳过按钮和倒计时）
    _active_window._handle_start_rest()


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

        self.root.bind("<Escape>", lambda e: self._handle_hide())

        self.root.lift()
        self.root.focus_force()

        logging.info("ReminderWindow: Window shown (non-blocking).")

    def _handle_start_rest(self):
        if self.is_closed:
            return

        if self.on_start_rest:
            self.on_start_rest()

        # 隐藏初始按钮
        self.btn_rest.pack_forget()
        self.btn_snooze.pack_forget()
        self.btn_hide.pack_forget()
        self.frame_btns.pack_forget()

        # 缩小标题，为三栏让出空间
        self.lbl_msg.config(
            font=("Microsoft YaHei UI", 22, "bold"),
        )
        self.lbl_msg.pack_configure(pady=20)

        # ============================================================
        # 构建三栏容器（贯穿休息+回答全流程）
        # ============================================================
        self.three_col_frame = tk.Frame(self.main_container, bg="#2c3e50")
        self.three_col_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

        # --- 左栏：Tip 面板 ---
        self._build_tip_panel(self.three_col_frame)

        # --- 中栏：问题 + 倒计时（稍后会切换为回答输入） ---
        self.center_frame = tk.Frame(self.three_col_frame, bg="#2c3e50")
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        self._build_center_question()

        # --- 右栏：生理指标 ---
        self._build_health_panel(self.three_col_frame)

    # ================================================================
    # 左栏：Tip 面板 — 六组件 placeholder + 深度金句
    # ================================================================
    def _build_tip_panel(self, parent):
        """构建左侧 Tip 面板。六组件使用 placeholder 逻辑。"""
        left_tip = tk.Frame(parent, bg="#1a252f", padx=20, pady=20, width=320)
        left_tip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_tip.pack_propagate(False)

        tk.Label(
            left_tip,
            text="🎮 人生游戏面板",
            font=("Microsoft YaHei UI", 14, "bold"),
            fg="#f1c40f",
            bg="#1a252f",
        ).pack(anchor=tk.W, pady=(0, 15))

        # 加载六组件数据
        try:
            from questions import SYNTHESIS_QUESTIONS, get_latest_synthesis_answers, pick_random_quote
            synthesis_answers = get_latest_synthesis_answers()
            synth_qs = SYNTHESIS_QUESTIONS
        except Exception:
            synthesis_answers = {}
            synth_qs = []

        # 展示六组件 — placeholder 逻辑
        for sq in synth_qs:
            icon = sq.get("icon", "•")
            section = sq.get("section", "")
            game_role = sq.get("game_role", "")
            answer = synthesis_answers.get(sq["id"], "")

            # 标题行
            header_frame = tk.Frame(left_tip, bg="#1a252f")
            header_frame.pack(fill=tk.X, pady=(8, 2))

            tk.Label(
                header_frame,
                text=f"{icon} {section}",
                font=("Microsoft YaHei UI", 10, "bold"),
                fg="#3498db",
                bg="#1a252f",
            ).pack(side=tk.LEFT)

            tk.Label(
                header_frame,
                text=game_role,
                font=("Microsoft YaHei UI", 8),
                fg="#7f8c8d",
                bg="#1a252f",
            ).pack(side=tk.RIGHT)

            # 内容：有回答则正常展示，无回答则灰色 placeholder
            if answer:
                display_text = answer[:60] + "…" if len(answer) > 60 else answer
                text_color = "#ecf0f1"
            else:
                # placeholder：灰色引导文字
                display_text = sq.get("zh", "")[:35] + "…"
                text_color = "#555e66"

            tk.Label(
                left_tip,
                text=display_text,
                font=("Microsoft YaHei UI", 9),
                fg=text_color,
                bg="#1a252f",
                wraplength=270,
                justify=tk.LEFT,
                anchor=tk.W,
            ).pack(fill=tk.X, padx=(18, 0), pady=(0, 2))

        # 分隔线
        tk.Frame(left_tip, bg="#34495e", height=1).pack(fill=tk.X, pady=15)

        # 随机深度金句
        try:
            quote = pick_random_quote()
            tk.Label(
                left_tip,
                text="💡 灵感触发",
                font=("Microsoft YaHei UI", 10, "bold"),
                fg="#e67e22",
                bg="#1a252f",
            ).pack(anchor=tk.W, pady=(0, 8))

            tk.Label(
                left_tip,
                text="\u300c" + quote['zh'] + "\u300d",
                font=("Microsoft YaHei UI", 9, "italic"),
                fg="#bdc3c7",
                bg="#1a252f",
                wraplength=270,
                justify=tk.LEFT,
            ).pack(fill=tk.X, pady=(0, 4))

            tk.Label(
                left_tip,
                text=f"— {quote['source']}",
                font=("Microsoft YaHei UI", 8),
                fg="#7f8c8d",
                bg="#1a252f",
            ).pack(anchor=tk.E)
        except Exception:
            pass

    # ================================================================
    # 中栏 Phase 1：问题展示 + 倒计时
    # ================================================================
    def _build_center_question(self):
        """在中栏展示自省问题和倒计时。"""
        if self.question:
            # 问题卡片
            q_card = tk.Frame(self.center_frame, bg="#34495e", padx=30, pady=25)
            q_card.pack(fill=tk.X, pady=(0, 20))

            tk.Label(
                q_card,
                text="💭 此刻思考 — Reflect on this",
                font=("Microsoft YaHei UI", 14, "bold"),
                fg="#f39c12",
                bg="#34495e",
            ).pack(pady=(0, 15))

            tk.Label(
                q_card,
                text=self.question["en"],
                font=("Segoe UI", 18, "italic", "bold"),
                fg="#ecf0f1",
                bg="#34495e",
                wraplength=700,
                justify=tk.CENTER,
            ).pack(pady=(0, 10), anchor=tk.CENTER)

            tk.Label(
                q_card,
                text=self.question["zh"],
                font=("Microsoft YaHei UI", 16, "bold"),
                fg="#bdc3c7",
                bg="#34495e",
                wraplength=700,
                justify=tk.CENTER,
            ).pack(pady=(0, 5), anchor=tk.CENTER)

        self._start_countdown(self.duration_seconds)

    # ================================================================
    # 右栏：生理指标录入（带 placeholder 防重复）
    # ================================================================
    def _build_health_panel(self, parent):
        """构建右侧生理指标面板。"""
        right_sidebar = tk.Frame(parent, bg="#34495e", padx=25, pady=25, width=300)
        right_sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        right_sidebar.pack_propagate(False)

        tk.Label(
            right_sidebar,
            text="📊 身体状态",
            font=("Microsoft YaHei UI", 14, "bold"),
            fg="#3498db",
            bg="#34495e",
        ).pack(anchor=tk.W, pady=(0, 20))

        def create_entry_row(panel, label, placeholder=""):
            """创建带 placeholder 的输入行。"""
            row = tk.Frame(panel, bg="#34495e")
            row.pack(fill=tk.X, pady=10)
            tk.Label(row, text=label, font=("Microsoft YaHei UI", 11),
                     fg="#ecf0f1", bg="#34495e").pack(side=tk.LEFT)
            ent = tk.Entry(row, font=("Segoe UI", 12, "bold"), width=8, bg="#2c3e50",
                           fg="#2ecc71", insertbackground="white", relief="flat", justify=tk.CENTER)
            ent.pack(side=tk.RIGHT)

            # placeholder 逻辑
            ent._placeholder = str(placeholder)
            ent._is_placeholder = False

            def _set_placeholder():
                if not ent.get() and ent._placeholder:
                    ent._is_placeholder = True
                    ent.insert(0, ent._placeholder)
                    ent.config(fg="#7f8c8d")

            def _on_focus_in(e):
                if ent._is_placeholder:
                    ent.delete(0, tk.END)
                    ent.config(fg="#2ecc71")
                    ent._is_placeholder = False

            def _on_focus_out(e):
                _set_placeholder()

            def _on_key(e):
                if ent._is_placeholder:
                    ent.delete(0, tk.END)
                    ent.config(fg="#2ecc71")
                    ent._is_placeholder = False
                self._health_dirty = True

            ent.bind("<FocusIn>", _on_focus_in)
            ent.bind("<FocusOut>", _on_focus_out)
            ent.bind("<Key>", _on_key)
            _set_placeholder()
            return ent

        self._health_dirty = False

        self.entry_weight = create_entry_row(right_sidebar, "体重 (kg)")
        self.entry_bp_high = create_entry_row(right_sidebar, "收缩压 (H)")
        self.entry_bp_low = create_entry_row(right_sidebar, "舒张压 (L)")
        self.entry_heart_rate = create_entry_row(right_sidebar, "心率 (BPM)")

        # 设置 placeholder
        all_health = load_health_data()
        today_str = str(date.today())
        today_data = all_health.get(today_str, [])
        if isinstance(today_data, dict): today_data = [today_data]
        last_record = today_data[-1] if today_data else {}

        if not last_record:
            for d in reversed(sorted(all_health.keys())):
                if d < today_str:
                    d_data = all_health[d]
                    if isinstance(d_data, dict): d_data = [d_data]
                    last_record = d_data[-1] if d_data else {}
                    break

        for ent, key, fallback in [
            (self.entry_weight, "weight", ""),
            (self.entry_bp_high, "bp_high", "120"),
            (self.entry_bp_low, "bp_low", "80"),
            (self.entry_heart_rate, "heart_rate", "75"),
        ]:
            val = str(last_record.get(key, fallback))
            ent._placeholder = val
            ent.delete(0, tk.END)
            if val:
                ent._is_placeholder = True
                ent.insert(0, val)
                ent.config(fg="#7f8c8d")

        tk.Label(
            right_sidebar,
            text="💡 每次休息记录的数据都会被累送并计算平均值",
            font=("Microsoft YaHei UI", 9),
            fg="#7f8c8d",
            bg="#34495e",
            wraplength=200,
            justify=tk.LEFT
        ).pack(side=tk.BOTTOM, pady=10)

    # ================================================================
    # 中栏 Phase 2：回答输入（替换问题+倒计时）
    # ================================================================
    def _show_answer_input(self):
        """倒计时结束后，仅替换中栏内容为回答输入框。左右栏保持不变。"""
        if not self.question:
            self.force_close()
            return


        self.lbl_msg.config(
            text="休息结束！请写下你的思考 ✍️",
            font=("Microsoft YaHei UI", 22, "bold"),
            fg="#2ecc71",
        )

        # 清空中栏（移除问题卡片和倒计时）
        for w in self.center_frame.winfo_children():
            w.destroy()

        # 回答输入区
        tk.Label(
            self.center_frame,
            text="你的回答 (Your Reflection):",
            font=("Microsoft YaHei UI", 12),
            fg="#95a5a6",
            bg="#2c3e50",
        ).pack(anchor=tk.W, pady=(0, 8))

        self.text_answer = tk.Text(
            self.center_frame,
            font=("Microsoft YaHei UI", 13),
            bg="#34495e",
            fg="#ecf0f1",
            insertbackground="#ecf0f1",
            relief="flat",
            height=8,
            wrap=tk.WORD,
            padx=15,
            pady=10,
        )
        self.text_answer.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.text_answer.focus_set()

        # 按钮区
        btn_frame = tk.Frame(self.center_frame, bg="#2c3e50")
        btn_frame.pack(pady=10)

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
        
        # 提取健康数据 — 仅在用户主动修改过时保存
        def _get_real_value(entry):
            """获取输入框的真实值（排除 placeholder）。"""
            if getattr(entry, '_is_placeholder', False):
                return ""
            return entry.get().strip()

        weight_raw = _get_real_value(self.entry_weight)
        bp_high = _get_real_value(self.entry_bp_high)
        bp_low = _get_real_value(self.entry_bp_low)
        heart_rate_raw = _get_real_value(self.entry_heart_rate)
        
        if getattr(self, '_health_dirty', False) and weight_raw:
            try:
                weight = float(weight_raw)
                all_health = load_health_data()
                today_str = str(date.today())
                
                # 获取今日记录列表并处理旧格式兼容
                today_records = all_health.get(today_str, [])
                if isinstance(today_records, dict): today_records = [today_records]
                
                # 追加新记录
                new_record = {
                    "weight": weight,
                    "bp_high": bp_high,
                    "bp_low": bp_low,
                    "heart_rate": heart_rate_raw,
                    "time": time.strftime("%H:%M:%S")
                }
                today_records.append(new_record)
                all_health[today_str] = today_records
                
                save_health_data(all_health)
                logging.info(f"Appended health data to history. Total count today: {len(today_records)}")
            except ValueError:
                messagebox.showerror("错误", "体重/心率请输入有效的数字", parent=self.root)
                return

        if answer_text and self.on_answer and self.question:
            try:
                self.on_answer(self.question["id"], answer_text)
                logging.info(f"Journal answer saved for question {self.question['id']}")
            except Exception as e:
                logging.error(f"Error saving journal answer: {e}")

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

        if remaining <= 0:
            # 倒计时结束或手动录入模式（0s） → 立即弹出回答输入框
            self._show_answer_input()
            return

        mins, secs = divmod(remaining, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        self.lbl_msg.config(text=f"休息时间 (剩余 {time_str}) 🧘")

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
