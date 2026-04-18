import tkinter as tk
from theme import _C, _F
from components import _separator, _accent_bar
from questions import SYNTHESIS_QUESTIONS, get_latest_synthesis_answers, pick_random_quote

class LeftTipPanel:
    """人生游戏面板 (左侧栏)"""
    def __init__(self, parent):
        # 外壳做 1px 微光边框
        self.wrapper = tk.Frame(parent, bg=_C.BORDER, padx=1, pady=1)
        self.wrapper.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        self.container = tk.Frame(self.wrapper, bg=_C.BG_SURFACE, padx=22, pady=20, width=330)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.container.pack_propagate(False)

        # 顶部琥珀装饰线
        _accent_bar(self.container, _C.AMBER, height=2, pady=(0, 12))

        tk.Label(
            self.container,
            text="🎮 人生游戏面板",
            font=_F.H3,
            fg=_C.AMBER,
            bg=_C.BG_SURFACE,
        ).pack(anchor=tk.W, pady=(0, 12))

        # 加载数据
        try:
            synthesis_answers = get_latest_synthesis_answers()
            synth_qs = SYNTHESIS_QUESTIONS
        except Exception:
            synthesis_answers = {}
            synth_qs = []

        # 展示六组件
        for sq in synth_qs:
            icon = sq.get("icon", "•")
            section = sq.get("section", "")
            game_role = sq.get("game_role", "")
            answer = synthesis_answers.get(sq["id"], "")

            header_frame = tk.Frame(self.container, bg=_C.BG_SURFACE)
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

            if answer:
                display_text = answer[:60] + "…" if len(answer) > 60 else answer
                text_color = _C.FG
            else:
                display_text = sq.get("zh", "")[:35] + "…"
                text_color = _C.FG_MUTED

            tk.Label(
                self.container,
                text=display_text,
                font=_F.TINY,
                fg=text_color,
                bg=_C.BG_SURFACE,
                wraplength=280,
                justify=tk.LEFT,
                anchor=tk.W,
            ).pack(fill=tk.X, padx=(20, 0), pady=(0, 2))

        _separator(self.container, _C.BORDER, pady=12)

        # 随机金句
        try:
            quote = pick_random_quote()
            tk.Label(
                self.container,
                text="💡 灵感触发",
                font=("Microsoft YaHei UI", 10, "bold"),
                fg=_C.AMBER,
                bg=_C.BG_SURFACE,
            ).pack(anchor=tk.W, pady=(0, 6))

            tk.Label(
                self.container,
                text="「" + quote['zh'] + "」",
                font=("Microsoft YaHei UI", 9, "italic"),
                fg=_C.FG_DIM,
                bg=_C.BG_SURFACE,
                wraplength=280,
                justify=tk.LEFT,
            ).pack(fill=tk.X, pady=(0, 4))

            tk.Label(
                self.container,
                text=f"— {quote['source']}",
                font=_F.TINY,
                fg=_C.FG_MUTED,
                bg=_C.BG_SURFACE,
            ).pack(anchor=tk.E)
        except Exception:
            pass
