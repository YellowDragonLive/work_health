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

        # 头部
        self._setup_header(mode_name)
        
        # 核心内容区 (用于刷新)
        self.content_area = tk.Frame(self.container, bg=_C.BG_SURFACE)
        self.content_area.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_ui()

    def _setup_header(self, mode_name):
        # 顶部装饰线 (加厚)
        _accent_bar(self.container, _C.AMBER, height=3, pady=(0, 16))

        title_frame = tk.Frame(self.container, bg=_C.BG_SURFACE)
        title_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            title_frame, text="🎮 人生游戏系统", font=_F.H2, fg=_C.AMBER, bg=_C.BG_SURFACE
        ).pack(side=tk.LEFT)
        
        # 模式指示器
        if mode_name == "morning_routine":
            badge_frame = tk.Frame(self.container, bg=_C.AMBER_DEEP, padx=10, pady=4)
            badge_frame.pack(anchor=tk.W, pady=(0, 16))
            tk.Label(
                badge_frame, text="🌞 晨间冲刺模式 (10/5)", font=_F.SMALL,
                fg=_C.FG, bg=_C.AMBER_DEEP
            ).pack()

    def refresh_ui(self):
        """刷新人生游戏数据展示"""
        # 清理旧内容
        for widget in self.content_area.winfo_children():
            widget.destroy()

        answers = get_latest_synthesis_answers()
        
        # 滚动容器
        canvas = tk.Canvas(self.content_area, bg=_C.BG_SURFACE, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_area, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=_C.BG_SURFACE)

        scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=390)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for q in SYNTHESIS_QUESTIONS:
            ans = answers.get(q["id"], "尚未填写使命内容...")
            
            q_frame = tk.Frame(scroll_frame, bg=_C.BG_SURFACE, pady=12)
            q_frame.pack(fill=tk.X)

            # Icon + Section
            top_f = tk.Frame(q_frame, bg=_C.BG_SURFACE)
            top_f.pack(fill=tk.X)
            tk.Label(top_f, text=f"{q['icon']} {q['section']}", font=_F.BODY_BOLD, fg=_C.CYAN, bg=_C.BG_SURFACE).pack(side=tk.LEFT)
            tk.Label(top_f, text=q['game_role'], font=_F.TINY, fg=_C.FG_MUTED, bg=_C.BG_SURFACE).pack(side=tk.RIGHT)

            # Answer
            tk.Label(
                q_frame, text=ans, font=_F.BODY, fg=_C.FG, bg=_C.BG_SURFACE,
                wraplength=360, justify="left", padx=5, pady=4
            ).pack(anchor=tk.W)

            _separator(scroll_frame, color=_C.BORDER, pady=0)

        # 底部随机金句
        quote = pick_random_quote()
        quote_f = tk.Frame(self.content_area, bg=_C.BG_VOID, padx=20, pady=15)
        quote_f.pack(fill=tk.X, side="bottom", pady=(20, 0))
        tk.Label(quote_f, text=f"“ {quote['zh']} ”", font=_F.EN_BODY, fg=_C.AMBER, bg=_C.BG_VOID, wraplength=350).pack()
        tk.Label(quote_f, text=f"— {quote['source']}", font=_F.TINY, fg=_C.FG_MUTED, bg=_C.BG_VOID).pack(anchor="e")
