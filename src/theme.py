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
    CYAN_DEEP = "#0891b2"
    GREEN  = "#10b981"
    RED    = "#ef4444"
    PURPLE = "#8b5cf6"

    # 强调色梯度
    GREEN_DEEP  = "#047857"
    GREEN_LIGHT = "#34d399"
    AMBER_DEEP  = "#b45309"
    AMBER_LIGHT = "#fbbf24"
    BLUE_LIGHT  = "#60a5fa"

    # 基础文字
    FG       = "#e2e8f0"
    FG_DIM   = "#94a3b8"
    FG_MUTED = "#475569"
    FG_LINK  = "#60a5fa"

# 类级别语义化映射 (直接注入)
_C.ACCENT      = _C.CYAN
_C.PROGRESS    = _C.GREEN
_C.URGENT      = _C.RED
_C.WARNING     = _C.AMBER
_C.RECORD      = _C.PURPLE
_C.TEXT_MAIN   = _C.FG
_C.TEXT_DIM    = _C.FG_DIM
_C.TEXT_MUTED  = _C.FG_MUTED


class _F:
    """Font Tokens — 字体令牌"""
    HERO     = ("Segoe UI", 32, "bold")
    TITLE    = ("Microsoft YaHei UI", 24, "bold")
    H1       = TITLE
    HEADER   = ("Microsoft YaHei UI", 18, "bold")
    H2       = ("Microsoft YaHei UI", 18, "bold")
    H3       = ("Microsoft YaHei UI", 15, "bold")
    BODY_BOLD = ("Microsoft YaHei UI", 13, "bold")
    BODY     = ("Microsoft YaHei UI", 13)
    BODY_LG  = ("Microsoft YaHei UI", 15)
    EN_TITLE = ("Segoe UI", 18, "bold italic")
    EN_BODY  = ("Segoe UI", 14, "italic")
    SMALL    = ("Microsoft YaHei UI", 12)
    TINY     = ("Microsoft YaHei UI", 11)
    TIMER    = ("Consolas", 42, "bold")
    BTN      = ("Microsoft YaHei UI", 15, "bold")
    BTN_SM   = ("Microsoft YaHei UI", 13)
    MONO     = ("Consolas", 14)
