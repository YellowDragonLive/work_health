import tkinter as tk
from theme import _C, _F
from components import _separator, _accent_bar
from questions import SYNTHESIS_QUESTIONS, get_latest_synthesis_answers, pick_random_quote

class LeftTipPanel:
    """人生游戏面板 (左侧栏)"""
    def __init__(self, parent, mode_name="default"):
        # 外壳做 1px 微光边框
        self.wrapper = tk.Frame(parent, bg=_C.BORDER, padx=1, pady=1)
        self.wrapper.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        self.container = tk.Frame(self.wrapper, bg=_C.BG_SURFACE, padx=30, pady=24, width=450)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.container.pack_propagate(False)

        # 顶部装饰线 (加厚)
        _accent_bar(self.container, _C.AMBER, height=3, pady=(0, 16))

        tk.Label(
            self.container,
            text="🎮 人生游戏系统",
            font=_F.H2,
            fg=_C.AMBER,
            bg=_C.BG_SURFACE,
        ).pack(anchor=tk.W, pady=(0, 6))
        
        # 模式指示器 (加粗/显眼)
        if mode_name == "morning_routine":
            badge_frame = tk.Frame(self.container, bg=_C.AMBER_DEEP, padx=10, pady=4)
            badge_frame.pack(anchor=tk.W, pady=(0, 16))
            tk.Label(
                badge_frame,
                text="🌞 晨间冲刺模式 (10/5)",
                font=_F.SMALL,
                fg=_C.FG,
                bg=_C.AMBER_DEEP,
                weight="bold"
            ).pack()
        elif mode_name != "default":
            tk.Label(
                self.container,
                text=f"🔄 当前策略: {mode_name}",
                font=_F.SMALL,
                fg=_C.BLUE_LIGHT,
                bg=_C.BG_SURFACE
            ).pack(anchor=tk.W, pady=(0, 16))

        # 加载数据
        try:
            synthesis_answers = get_latest_synthesis_answers()
            synth_qs = SYNTHESIS_QUESTIONS
        except Exception:
            synthesis_answers = {}
            synth_qs = []

        # 展示六组件 (加大间距)
        for sq in synth_qs:
            icon = sq.get("icon", "•")
            section = sq.get("section", "")
            game_role = sq.get("game_role", "")
            answer = synthesis_answers.get(sq["id"], "")

            header_frame = tk.Frame(self.container, bg=_C.BG_SURFACE)
            header_frame.pack(fill=tk.X, pady=(12, 4)) # 增加垂直间距

            tk.Label(
                header_frame,
                text=f"{icon} {section}",
                font=_F.H3, # 从 SMALL 提升到 H3
                fg=_C.BLUE_LIGHT,
                bg=_C.BG_SURFACE,
            ).pack(side=tk.LEFT)

            tk.Label(
                header_frame,
                text=game_role,
                font=_F.SMALL, # 从 TINY 提升到 SMALL
                fg=_C.FG_MUTED,
                bg=_C.BG_SURFACE,
            ).pack(side=tk.RIGHT)

            if answer:
                display_text = answer[:80] + "…" if len(answer) > 80 else answer
                text_color = _C.FG
                font_style = _F.BODY # 从 TINY 提升到 BODY
            else:
                display_text = "尚未定义... " + sq.get("zh", "")[:35]
                text_color = _C.FG_MUTED
                font_style = _F.BODY_LG # 占位符使用较大的文字以提示输入

            tk.Label(
                self.container,
                text=display_text,
                font=font_style,
                fg=text_color,
                bg=_C.BG_SURFACE,
                wraplength=400, # 配合 450 宽度
                justify=tk.LEFT,
                anchor=tk.W,
            ).pack(fill=tk.X, padx=(22, 0), pady=(0, 4))

        _separator(self.container, _C.BORDER, pady=16)

        # 随机金句 (更大、更有力量)
        try:
            quote = pick_random_quote()
            tk.Label(
                self.container,
                text="💡 灵感触发",
                font=_F.H3,
                fg=_C.AMBER,
                bg=_C.BG_SURFACE,
            ).pack(anchor=tk.W, pady=(0, 8))

            tk.Label(
                self.container,
                text="「 " + quote['zh'] + " 」",
                font=_F.BODY_LG,
                fg=_C.FG_DIM,
                bg=_C.BG_SURFACE,
                wraplength=400,
                justify=tk.LEFT,
            ).pack(fill=tk.X, pady=(0, 6))

            tk.Label(
                self.container,
                text=f"— {quote['source']}",
                font=_F.SMALL,
                fg=_C.FG_MUTED,
                bg=_C.BG_SURFACE,
            ).pack(anchor=tk.E)
        except Exception:
            pass

