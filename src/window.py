import tkinter as tk
from tkinter import messagebox
import logging
import time
from datetime import date

from theme import _C, _F
from components import _make_button, _accent_bar, _CircleTimer
from config_manager import load_health_data, save_health_data
from ui_left import LeftTipPanel
from ui_right import RightHealthPanel

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
        self._circle_timer = None
        self._total_duration = duration_seconds
        self.health_panel = None

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
        self.root.attributes("-alpha", 0.96)
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg=_C.BG_VOID)

        _accent_bar(self.root, _C.AMBER, height=3)

        self.main_container = tk.Frame(self.root, bg=_C.BG_VOID)
        self.main_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.lbl_msg = tk.Label(
            self.main_container,
            text=self.message,
            font=_F.HERO,
            fg=_C.FG,
            bg=_C.BG_VOID,
            wraplength=1000,
        )
        self.lbl_msg.pack(pady=(40, 50))

        self.frame_btns = tk.Frame(self.main_container, bg=_C.BG_VOID)
        self.frame_btns.pack(pady=20)

        self.btn_rest = _make_button(self.frame_btns, "🧘  开始休息", self._handle_start_rest, bg=_C.GREEN_DEEP, hover_bg=_C.GREEN)
        self.btn_rest.pack(side=tk.LEFT, padx=20)

        self.btn_snooze = _make_button(self.frame_btns, "⏰  推迟 5 分钟", self._handle_snooze, bg=_C.AMBER_DEEP, hover_bg=_C.AMBER)
        self.btn_snooze.pack(side=tk.LEFT, padx=20)

        self.btn_hide = _make_button(self.main_container, "处理其他事务 · 暂时隐藏 15 秒 [Esc]", self._handle_hide, bg=_C.BG_OVERLAY, hover_bg=_C.BG_HOVER, fg=_C.FG_DIM, font=_F.BTN_SM, padx=24, pady=10)
        self.btn_hide.pack(pady=(40, 0))

        self.root.bind("<Escape>", lambda e: self._handle_hide())
        self.root.lift()
        self.root.focus_force()

    def _handle_start_rest(self):
        if self.is_closed: return
        if self.on_start_rest: self.on_start_rest()

        self.btn_rest.pack_forget()
        self.btn_snooze.pack_forget()
        self.btn_hide.pack_forget()
        self.frame_btns.pack_forget()

        self.lbl_msg.config(font=_F.H1)
        self.lbl_msg.pack_configure(pady=(10, 15))

        self.three_col_frame = tk.Frame(self.main_container, bg=_C.BG_VOID)
        self.three_col_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # --- 三栏模块化加载 ---
        LeftTipPanel(self.three_col_frame)
        
        self.center_frame = tk.Frame(self.three_col_frame, bg=_C.BG_VOID)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        self._build_center_question()

        self.health_panel = RightHealthPanel(self.three_col_frame)

    def _build_center_question(self):
        if self.question:
            card_wrapper = tk.Frame(self.center_frame, bg=_C.BORDER, padx=1, pady=1)
            card_wrapper.pack(fill=tk.X, pady=(0, 20))
            q_card = tk.Frame(card_wrapper, bg=_C.BG_SURFACE, padx=30, pady=25)
            q_card.pack(fill=tk.BOTH)

            tk.Label(q_card, text="💭 此刻思考", font=_F.H3, fg=_C.AMBER, bg=_C.BG_SURFACE).pack(anchor=tk.W, pady=(0, 12))
            en_frame = tk.Frame(q_card, bg=_C.BG_SURFACE)
            en_frame.pack(fill=tk.X, pady=(0, 10))
            tk.Frame(en_frame, bg=_C.BLUE, width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
            tk.Label(en_frame, text=self.question["en"], font=_F.EN_TITLE, fg=_C.FG, bg=_C.BG_SURFACE, wraplength=620, justify=tk.LEFT, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(q_card, text=self.question["zh"], font=_F.H2, fg=_C.FG_DIM, bg=_C.BG_SURFACE, wraplength=650, justify=tk.LEFT, anchor=tk.W).pack(fill=tk.X, pady=(0, 5))

        if self.duration_seconds > 0:
            self._circle_timer = _CircleTimer(self.center_frame, size=200, line_w=5, bg=_C.BG_VOID)
            self._circle_timer.pack(pady=20)
        self._start_countdown(self.duration_seconds)

    def _show_answer_input(self):
        if not self.question:
            self.force_close()
            return

        self.lbl_msg.config(text="休息结束！请写下你的思考 ✍️", font=_F.H1, fg=_C.GREEN)
        for w in self.center_frame.winfo_children(): w.destroy()
        self._circle_timer = None

        tk.Label(self.center_frame, text="你的回答 (Your Reflection):", font=_F.BODY, fg=_C.FG_DIM, bg=_C.BG_VOID).pack(anchor=tk.W, pady=(0, 8))
        self.text_answer = tk.Text(self.center_frame, font=_F.BODY_LG, bg=_C.BG_OVERLAY, fg=_C.FG, insertbackground=_C.FG, relief="flat", height=8, wrap=tk.WORD, padx=16, pady=12, highlightthickness=1, highlightbackground=_C.BORDER, highlightcolor=_C.BLUE)
        self.text_answer.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.text_answer.focus_set()

        btn_frame = tk.Frame(self.center_frame, bg=_C.BG_VOID)
        btn_frame.pack(pady=10)
        _make_button(btn_frame, "✅ 提交回答", self._submit_answer, bg=_C.GREEN_DEEP, hover_bg=_C.GREEN).pack(side=tk.LEFT, padx=12)
        _make_button(btn_frame, "跳过", self.force_close, bg=_C.BG_OVERLAY, hover_bg=_C.BG_HOVER, fg=_C.FG_DIM, font=_F.BTN_SM).pack(side=tk.LEFT, padx=12)

        self.text_answer.bind("<Control-Return>", lambda e: self._submit_answer())
        self.root.bind("<Escape>", lambda e: self.force_close())

    def _submit_answer(self):
        if self.is_closed: return
        answer_text = self.text_answer.get("1.0", tk.END).strip()

        # 提取生理数据
        if self.health_panel:
            data, dirty = self.health_panel.get_real_values()
            if dirty and data.get("weight"):
                try:
                    weight = float(data["weight"])
                    all_health = load_health_data()
                    today_str = str(date.today())
                    today_records = all_health.get(today_str, [])
                    if isinstance(today_records, dict): today_records = [today_records]
                    
                    new_record = {
                        "weight": weight, "bp_high": data.get("bp_high"),
                        "bp_low": data.get("bp_low"), "heart_rate": data.get("heart_rate"),
                        "time": time.strftime("%H:%M:%S")
                    }
                    today_records.append(new_record)
                    all_health[today_str] = today_records
                    save_health_data(all_health)
                    logging.info(f"Health data saved. Total: {len(today_records)}")
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数字", parent=self.root)
                    return

        if answer_text and self.on_answer and self.question:
            try:
                self.on_answer(self.question["id"], answer_text)
            except Exception as e:
                logging.error(f"Error saving journal: {e}")

        self.force_close()

    def _handle_snooze(self):
        if not self.is_closed and self.on_snooze: self.on_snooze()
        self.force_close()

    def _handle_hide(self):
        if self.is_closed: return
        self.root.withdraw()
        self._cancel_timer("hide_timer_id")
        def restore():
            if not self.is_closed:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
        self.hide_timer_id = self.root.after(15000, restore)

    def _start_countdown(self, remaining):
        if self.is_closed: return
        if remaining <= 0:
            self._show_answer_input()
            return
        if self._circle_timer: self._circle_timer.update(remaining, self._total_duration)
        self._cancel_timer("timer_id")
        self.timer_id = self.root.after(1000, lambda: self._start_countdown(remaining - 1))

    def _cancel_timer(self, attr_name):
        timer_id = getattr(self, attr_name, None)
        if timer_id:
            try: self.root.after_cancel(timer_id)
            except: pass
            setattr(self, attr_name, None)

    def force_close(self):
        if self.is_closed: return
        self.is_closed = True
        self._cancel_timer("timer_id")
        self._cancel_timer("hide_timer_id")
        if self.root:
            try: self.root.destroy()
            except: pass
        if self.on_close: self.on_close()
