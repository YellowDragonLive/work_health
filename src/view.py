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


# ============================================================
# 设计系统 — Midnight Aurora 主题
# ============================================================

class _C:
    """Color Tokens — 统一配色令牌"""
    # 背景层级（深 → 浅）
    BG_VOID    = "#080c14"      # 最深：窗口底色
    BG_BASE    = "#0f1724"      # 主区域
    BG_SURFACE = "#172033"      # 卡片/面板
    BG_OVERLAY = "#1e293b"      # 浮层/输入框
    BG_HOVER   = "#283548"      # hover 态

    # 边框
    BORDER      = "#2a3650"
    BORDER_GLOW = "#2d5a9e"     # 蓝辉边框

    # 强调色
    AMBER  = "#f59e0b"
    BLUE   = "#3b82f6"
    CYAN   = "#06b6d4"
    GREEN  = "#10b981"
    RED    = "#ef4444"
    PURPLE = "#8b5cf6"

    # 强调色梯度
    GREEN_DEEP  = "#047857"
    GREEN_LIGHT = "#34d399"
    AMBER_DEEP  = "#b45309"
    AMBER_LIGHT = "#fbbf24"
    BLUE_LIGHT  = "#60a5fa"

    # 文字
    FG       = "#e2e8f0"
    FG_DIM   = "#94a3b8"
    FG_MUTED = "#475569"
    FG_LINK  = "#60a5fa"


class _F:
    """Font Tokens — 字体令牌"""
    HERO     = ("Segoe UI", 28, "bold")
    H1       = ("Microsoft YaHei UI", 22, "bold")
    H2       = ("Microsoft YaHei UI", 16, "bold")
    H3       = ("Microsoft YaHei UI", 13, "bold")
    BODY     = ("Microsoft YaHei UI", 12)
    BODY_LG  = ("Microsoft YaHei UI", 14)
    EN_TITLE = ("Segoe UI", 17, "bold italic")
    EN_BODY  = ("Segoe UI", 13, "italic")
    SMALL    = ("Microsoft YaHei UI", 10)
    TINY     = ("Microsoft YaHei UI", 9)
    TIMER    = ("Consolas", 36, "bold")
    BTN      = ("Microsoft YaHei UI", 14, "bold")
    BTN_SM   = ("Microsoft YaHei UI", 12)
    MONO     = ("Consolas", 13)


# ============================================================
# UI 辅助组件
# ============================================================

def _hover(widget, normal_bg, hover_bg):
    """给任意 widget 绑定鼠标 hover 颜色过渡。"""
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))


def _make_button(parent, text, command, bg, hover_bg, fg="white",
                 font=_F.BTN, padx=36, pady=14, **kw):
    """创建带 hover 效果的扁平按钮。"""
    btn = tk.Button(
        parent, text=text, command=command,
        font=font, bg=bg, fg=fg,
        activebackground=hover_bg, activeforeground=fg,
        relief="flat", bd=0, padx=padx, pady=pady,
        cursor="hand2", **kw,
    )
    _hover(btn, bg, hover_bg)
    return btn


def _separator(parent, color=_C.BORDER, height=1, **pack_kw):
    """水平分隔线。"""
    sep = tk.Frame(parent, bg=color, height=height)
    sep.pack(fill=tk.X, **pack_kw)
    return sep


def _accent_bar(parent, color=_C.AMBER, height=2, **pack_kw):
    """装饰性的顶部/底部强调色条。"""
    bar = tk.Frame(parent, bg=color, height=height)
    bar.pack(fill=tk.X, **pack_kw)
    return bar


class _CircleTimer:
    """环形倒计时进度条组件（基于 Canvas Arc）。"""

    def __init__(self, parent, size=200, line_w=5, bg=_C.BG_VOID):
        self.size = size
        self.lw = line_w

        self.canvas = tk.Canvas(
            parent, width=size, height=size,
            bg=bg, highlightthickness=0,
        )

        pad = line_w + 8
        # 背景轨道（暗色圆环）
        self.canvas.create_oval(
            pad, pad, size - pad, size - pad,
            outline=_C.BORDER, width=line_w,
        )
        # 前景弧（活跃进度）
        self.arc = self.canvas.create_arc(
            pad, pad, size - pad, size - pad,
            start=90, extent=-360,
            outline=_C.CYAN, width=line_w, style=tk.ARC,
        )
        # 中央数字
        self.time_id = self.canvas.create_text(
            size // 2, size // 2 - 8,
            text="00:00", fill=_C.FG,
            font=_F.TIMER,
        )
        # "剩余" 标签
        self.label_id = self.canvas.create_text(
            size // 2, size // 2 + 28,
            text="剩 余", fill=_C.FG_DIM,
            font=_F.SMALL,
        )

    def update(self, remaining, total):
        """刷新进度弧和数字。"""
        if total <= 0:
            return
        ratio = remaining / total
        self.canvas.itemconfig(self.arc, extent=-360 * ratio)

        mins, secs = divmod(remaining, 60)
        self.canvas.itemconfig(self.time_id, text=f"{mins:02d}:{secs:02d}")

        # 颜色随剩余比例渐变
        if ratio > 0.5:
            color = _C.CYAN
        elif ratio > 0.2:
            color = _C.AMBER
        else:
            color = _C.RED
        self.canvas.itemconfig(self.arc, outline=color)

    def pack(self, **kw):
        self.canvas.pack(**kw)

    def destroy(self):
        self.canvas.destroy()


# ============================================================
# 主窗口
# ============================================================

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

        # ── 顶部琥珀金装饰线 ──
        _accent_bar(self.root, _C.AMBER, height=3)

        # ── 主容器 ──
        self.main_container = tk.Frame(self.root, bg=_C.BG_VOID)
        self.main_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # ── 标题 ──
        self.lbl_msg = tk.Label(
            self.main_container,
            text=self.message,
            font=_F.HERO,
            fg=_C.FG,
            bg=_C.BG_VOID,
            wraplength=800,
        )
        self.lbl_msg.pack(pady=(40, 50))

        # ── 按钮组 ──
        self.frame_btns = tk.Frame(self.main_container, bg=_C.BG_VOID)
        self.frame_btns.pack(pady=20)

        self.btn_rest = _make_button(
            self.frame_btns,
            "🧘  开始休息",
            self._handle_start_rest,
            bg=_C.GREEN_DEEP, hover_bg=_C.GREEN,
        )
        self.btn_rest.pack(side=tk.LEFT, padx=20)

        self.btn_snooze = _make_button(
            self.frame_btns,
            "⏰  推迟 5 分钟",
            self._handle_snooze,
            bg=_C.AMBER_DEEP, hover_bg=_C.AMBER,
        )
        self.btn_snooze.pack(side=tk.LEFT, padx=20)

        # ── 隐藏按钮 ──
        self.btn_hide = _make_button(
            self.main_container,
            "处理其他事务 · 暂时隐藏 15 秒  [Esc]",
            self._handle_hide,
            bg=_C.BG_OVERLAY, hover_bg=_C.BG_HOVER,
            fg=_C.FG_DIM, font=_F.BTN_SM, padx=24, pady=10,
        )
        self.btn_hide.pack(pady=(40, 0))

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
        self.lbl_msg.config(font=_F.H1)
        self.lbl_msg.pack_configure(pady=(10, 15))

        # ============================================================
        # 构建三栏容器（贯穿休息+回答全流程）
        # ============================================================
        self.three_col_frame = tk.Frame(self.main_container, bg=_C.BG_VOID)
        self.three_col_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # --- 左栏：Tip 面板 ---
        self._build_tip_panel(self.three_col_frame)

        # --- 中栏：问题 + 倒计时（稍后会切换为回答输入） ---
        self.center_frame = tk.Frame(self.three_col_frame, bg=_C.BG_VOID)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        self._build_center_question()

        # --- 右栏：生理指标 ---
        self._build_health_panel(self.three_col_frame)

    # ================================================================
    # 左栏：Tip 面板 — 六组件 placeholder + 深度金句
    # ================================================================
    def _build_tip_panel(self, parent):
        """构建左侧 Tip 面板。六组件使用 placeholder 逻辑。"""
        # 外壳做 1px 微光边框
        wrapper = tk.Frame(parent, bg=_C.BORDER, padx=1, pady=1)
        wrapper.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        left_tip = tk.Frame(wrapper, bg=_C.BG_SURFACE, padx=22, pady=20, width=330)
        left_tip.pack(fill=tk.BOTH, expand=True)
        left_tip.pack_propagate(False)

        # 顶部琥珀装饰线
        _accent_bar(left_tip, _C.AMBER, height=2, pady=(0, 12))

        tk.Label(
            left_tip,
            text="🎮 人生游戏面板",
            font=_F.H3,
            fg=_C.AMBER,
            bg=_C.BG_SURFACE,
        ).pack(anchor=tk.W, pady=(0, 12))

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
            header_frame = tk.Frame(left_tip, bg=_C.BG_SURFACE)
            header_frame.pack(fill=tk.X, pady=(8, 2))

            tk.Label(
                header_frame,
                text=f"{icon} {section}",
                font=_F.SMALL,
                fg=_C.BLUE_LIGHT,
                bg=_C.BG_SURFACE,
            ).pack(side=tk.LEFT)

            tk.Label(
                header_frame,
                text=game_role,
                font=_F.TINY,
                fg=_C.FG_MUTED,
                bg=_C.BG_SURFACE,
            ).pack(side=tk.RIGHT)

            # 内容：有回答则正常展示，无回答则灰色 placeholder
            if answer:
                display_text = answer[:60] + "…" if len(answer) > 60 else answer
                text_color = _C.FG
            else:
                # placeholder：灰色引导文字
                display_text = sq.get("zh", "")[:35] + "…"
                text_color = _C.FG_MUTED

            tk.Label(
                left_tip,
                text=display_text,
                font=_F.TINY,
                fg=text_color,
                bg=_C.BG_SURFACE,
                wraplength=280,
                justify=tk.LEFT,
                anchor=tk.W,
            ).pack(fill=tk.X, padx=(20, 0), pady=(0, 2))

        # 分隔线
        _separator(left_tip, _C.BORDER, pady=12)

        # 随机深度金句
        try:
            quote = pick_random_quote()
            tk.Label(
                left_tip,
                text="💡 灵感触发",
                font=("Microsoft YaHei UI", 10, "bold"),
                fg=_C.AMBER,
                bg=_C.BG_SURFACE,
            ).pack(anchor=tk.W, pady=(0, 6))

            tk.Label(
                left_tip,
                text="「" + quote['zh'] + "」",
                font=("Microsoft YaHei UI", 9, "italic"),
                fg=_C.FG_DIM,
                bg=_C.BG_SURFACE,
                wraplength=280,
                justify=tk.LEFT,
            ).pack(fill=tk.X, pady=(0, 4))

            tk.Label(
                left_tip,
                text=f"— {quote['source']}",
                font=_F.TINY,
                fg=_C.FG_MUTED,
                bg=_C.BG_SURFACE,
            ).pack(anchor=tk.E)
        except Exception:
            pass

    # ================================================================
    # 中栏 Phase 1：问题展示 + 环形倒计时
    # ================================================================
    def _build_center_question(self):
        """在中栏展示自省问题和倒计时。"""
        if self.question:
            # 问题卡片（带微光边框）
            card_wrapper = tk.Frame(self.center_frame, bg=_C.BORDER, padx=1, pady=1)
            card_wrapper.pack(fill=tk.X, pady=(0, 20))

            q_card = tk.Frame(card_wrapper, bg=_C.BG_SURFACE, padx=30, pady=25)
            q_card.pack(fill=tk.BOTH)

            tk.Label(
                q_card,
                text="💭 此刻思考",
                font=_F.H3,
                fg=_C.AMBER,
                bg=_C.BG_SURFACE,
            ).pack(anchor=tk.W, pady=(0, 12))

            # 英文：带左侧蓝色装饰线
            en_frame = tk.Frame(q_card, bg=_C.BG_SURFACE)
            en_frame.pack(fill=tk.X, pady=(0, 10))

            tk.Frame(en_frame, bg=_C.BLUE, width=3).pack(
                side=tk.LEFT, fill=tk.Y, padx=(0, 14),
            )
            tk.Label(
                en_frame,
                text=self.question["en"],
                font=_F.EN_TITLE,
                fg=_C.FG,
                bg=_C.BG_SURFACE,
                wraplength=620,
                justify=tk.LEFT,
                anchor=tk.W,
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # 中文
            tk.Label(
                q_card,
                text=self.question["zh"],
                font=_F.H2,
                fg=_C.FG_DIM,
                bg=_C.BG_SURFACE,
                wraplength=650,
                justify=tk.LEFT,
                anchor=tk.W,
            ).pack(fill=tk.X, pady=(0, 5))

        # 环形进度条（仅在有倒计时时显示）
        if self.duration_seconds > 0:
            self._circle_timer = _CircleTimer(
                self.center_frame, size=200, line_w=5, bg=_C.BG_VOID,
            )
            self._circle_timer.pack(pady=20)

        self._start_countdown(self.duration_seconds)

    # ================================================================
    # 右栏：生理指标录入（带 placeholder 防重复）
    # ================================================================
    def _build_health_panel(self, parent):
        """构建右侧生理指标面板。"""
        # 外壳做 1px 边框
        wrapper = tk.Frame(parent, bg=_C.BORDER, padx=1, pady=1)
        wrapper.pack(side=tk.RIGHT, fill=tk.Y)

        right_sidebar = tk.Frame(wrapper, bg=_C.BG_SURFACE, padx=25, pady=25, width=300)
        right_sidebar.pack(fill=tk.BOTH, expand=True)
        right_sidebar.pack_propagate(False)

        # 顶部青蓝装饰线
        _accent_bar(right_sidebar, _C.CYAN, height=2, pady=(0, 12))

        tk.Label(
            right_sidebar,
            text="📊 身体状态",
            font=_F.H3,
            fg=_C.CYAN,
            bg=_C.BG_SURFACE,
        ).pack(anchor=tk.W, pady=(0, 20))

        def create_entry_row(panel, label, placeholder=""):
            """创建带 placeholder 的输入行。"""
            row = tk.Frame(panel, bg=_C.BG_SURFACE)
            row.pack(fill=tk.X, pady=10)
            tk.Label(
                row, text=label, font=_F.BODY,
                fg=_C.FG, bg=_C.BG_SURFACE,
            ).pack(side=tk.LEFT)
            ent = tk.Entry(
                row, font=_F.MONO, width=8,
                bg=_C.BG_OVERLAY, fg=_C.GREEN,
                insertbackground=_C.FG, relief="flat",
                justify=tk.CENTER, bd=0,
                highlightthickness=1,
                highlightbackground=_C.BORDER,
                highlightcolor=_C.BLUE,
            )
            ent.pack(side=tk.RIGHT, ipady=4)

            # placeholder 逻辑
            ent._placeholder = str(placeholder)
            ent._is_placeholder = False

            def _set_placeholder():
                if not ent.get() and ent._placeholder:
                    ent._is_placeholder = True
                    ent.insert(0, ent._placeholder)
                    ent.config(fg=_C.FG_MUTED)

            def _on_focus_in(e):
                if ent._is_placeholder:
                    ent.delete(0, tk.END)
                    ent.config(fg=_C.GREEN)
                    ent._is_placeholder = False

            def _on_focus_out(e):
                _set_placeholder()

            def _on_key(e):
                if ent._is_placeholder:
                    ent.delete(0, tk.END)
                    ent.config(fg=_C.GREEN)
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
                ent.config(fg=_C.FG_MUTED)

        tk.Label(
            right_sidebar,
            text="💡 每次休息记录的数据都会被累送并计算平均值",
            font=_F.TINY,
            fg=_C.FG_MUTED,
            bg=_C.BG_SURFACE,
            wraplength=220,
            justify=tk.LEFT,
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
            font=_F.H1,
            fg=_C.GREEN,
        )

        # 清空中栏（移除问题卡片和倒计时）
        for w in self.center_frame.winfo_children():
            w.destroy()
        self._circle_timer = None

        # 回答输入区
        tk.Label(
            self.center_frame,
            text="你的回答 (Your Reflection):",
            font=_F.BODY,
            fg=_C.FG_DIM,
            bg=_C.BG_VOID,
        ).pack(anchor=tk.W, pady=(0, 8))

        self.text_answer = tk.Text(
            self.center_frame,
            font=_F.BODY_LG,
            bg=_C.BG_OVERLAY,
            fg=_C.FG,
            insertbackground=_C.FG,
            relief="flat",
            height=8,
            wrap=tk.WORD,
            padx=16,
            pady=12,
            highlightthickness=1,
            highlightbackground=_C.BORDER,
            highlightcolor=_C.BLUE,
        )
        self.text_answer.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.text_answer.focus_set()

        # 按钮区
        btn_frame = tk.Frame(self.center_frame, bg=_C.BG_VOID)
        btn_frame.pack(pady=10)

        _make_button(
            btn_frame,
            "✅  提交回答",
            self._submit_answer,
            bg=_C.GREEN_DEEP, hover_bg=_C.GREEN,
        ).pack(side=tk.LEFT, padx=12)

        _make_button(
            btn_frame,
            "跳过",
            self.force_close,
            bg=_C.BG_OVERLAY, hover_bg=_C.BG_HOVER,
            fg=_C.FG_DIM, font=_F.BTN_SM,
        ).pack(side=tk.LEFT, padx=12)

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

        # 更新环形进度条
        if self._circle_timer:
            self._circle_timer.update(remaining, self._total_duration)

        # 同时更新标题文字
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
