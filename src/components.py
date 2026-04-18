import tkinter as tk
from theme import _C, _F

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
