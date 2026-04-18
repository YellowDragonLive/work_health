import time
from window import ReminderWindow

_active_window = None

def show_reminder_process(message, duration, on_rest, on_snooze, on_close=None,
                          question=None, on_answer=None):
    """实例化并在主线程显示提醒窗口的辅助函数。"""
    global _active_window
    if _active_window:
        _active_window.force_close()

    _active_window = ReminderWindow(
        message, duration, on_rest, on_snooze, on_close,
        question=question, on_answer=on_answer,
    )
    _active_window.show()


def show_manual_record(on_answer=None):
    """托盘菜单或其他来源触发手动记录的入口。"""
    global _active_window
    if _active_window:
        _active_window.force_close()

    # 创建一个用于手动输入的占位问题
    question = {
        "id": "manual_entry_" + str(int(time.time())),
        "en": "Capture your current health status and thoughts.",
        "zh": "记录当前的身体状态与思考。"
    }

    # 手动记录：duration=0 时会跳过倒计时直接进入回答模式
    _active_window = ReminderWindow(
        "手动录入每日指标", 0, None, None, None,
        question=question, on_answer=on_answer
    )
    _active_window.show()
    # 直接构建三栏并进入回答模式
    _active_window._handle_start_rest()


def close_active_window():
    """显式关闭当前活跃的提醒窗口。"""
    global _active_window
    if _active_window:
        _active_window.force_close()
        _active_window = None
