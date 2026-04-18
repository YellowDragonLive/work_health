import tkinter as tk
import time
from datetime import date
from theme import _C, _F
from components import _accent_bar
from config_manager import load_health_data

class RightHealthPanel:
    """生理指标录入面板 (右侧栏)"""
    def __init__(self, parent):
        self._health_dirty = False
        
        # 外壳
        self.wrapper = tk.Frame(parent, bg=_C.BORDER, padx=1, pady=1)
        self.wrapper.pack(side=tk.RIGHT, fill=tk.Y)

        self.container = tk.Frame(self.wrapper, bg=_C.BG_SURFACE, padx=25, pady=25, width=300)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.container.pack_propagate(False)

        _accent_bar(self.container, _C.CYAN, height=2, pady=(0, 12))

        tk.Label(
            self.container,
            text="📊 身体状态",
            font=_F.H3,
            fg=_C.CYAN,
            bg=_C.BG_SURFACE,
        ).pack(anchor=tk.W, pady=(0, 20))

        self.entries = {}
        self.entries["weight"] = self._create_row("体重 (kg)")
        self.entries["bp_high"] = self._create_row("收缩压 (H)")
        self.entries["bp_low"] = self._create_row("舒张压 (L)")
        self.entries["heart_rate"] = self._create_row("心率 (BPM)")

        self._load_placeholders()

        tk.Label(
            self.container,
            text="💡 每次休息记录的数据都会被平滑记录，建议每日定时追踪。",
            font=_F.TINY,
            fg=_C.FG_MUTED,
            bg=_C.BG_SURFACE,
            wraplength=220,
            justify=tk.LEFT,
        ).pack(side=tk.BOTTOM, pady=10)

    def _create_row(self, label):
        row = tk.Frame(self.container, bg=_C.BG_SURFACE)
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

        ent._placeholder = ""
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
        return ent

    def _load_placeholders(self):
        all_health = load_health_data()
        today_str = str(date.today())
        today_data = all_health.get(today_str, [])
        if isinstance(today_data, dict): today_data = [today_data]
        last_record = today_records = today_data[-1] if today_data else {}

        if not last_record:
            for d in reversed(sorted(all_health.keys())):
                if d < today_str:
                    d_data = all_health[d]
                    if isinstance(d_data, dict): d_data = [d_data]
                    last_record = d_data[-1] if d_data else {}
                    break

        mappings = [
            ("weight", ""),
            ("bp_high", "120"),
            ("bp_low", "80"),
            ("heart_rate", "75"),
        ]
        for key, fallback in mappings:
            ent = self.entries[key]
            val = str(last_record.get(key, fallback))
            ent._placeholder = val
            ent.delete(0, tk.END)
            if val:
                ent._is_placeholder = True
                ent.insert(0, val)
                ent.config(fg=_C.FG_MUTED)

    def get_real_values(self):
        """获取录入的真实数据（排除占位符）。"""
        res = {}
        for key, ent in self.entries.items():
            if getattr(ent, '_is_placeholder', False):
                res[key] = ""
            else:
                res[key] = ent.get().strip()
        return res, self._health_dirty
