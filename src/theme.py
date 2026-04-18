import tkinter as tk

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
