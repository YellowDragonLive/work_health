import time
import os
import sys
import logging
from unittest.mock import MagicMock

# 确保能导入 src 中的模块
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from audio import AudioManager
from monitor import Monitor

# 配置日志到控制台以便观察
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def test_audio_switching_logic():
    print("=== 开始音频切换逻辑自动化测试 ===")
    
    # 1. 准备 Mock 配置
    config = {
        "audio": {
            "reminder_rest_path": "fake_reminder.mp3",
            "reflection_path": "fake_reflection.mp3",
            "volume": 0.5
        },
        "pomodoro": {
            "default": {"work_duration": 0.01, "rest_duration": 0.01}
        }
    }
    
    # 2. Mock pygame.mixer 以免在无声卡环境报错并记录调用
    import pygame
    pygame.mixer = MagicMock()
    pygame.mixer.music = MagicMock()
    
    # 模拟文件存在
    os.path.exists = MagicMock(return_value=True)
    
    # 3. 初始化 Monitor
    # 我们不仅 mock mixer，还要 mock 掉 gui_queue 里的弹窗展示，只跑逻辑
    gui_queue = MagicMock()
    monitor = Monitor(assets_dir="assets", config=config, gui_queue=gui_queue)
    
    # 验证初始音量
    print(f"验证音量设置: {config['audio']['volume']}")
    pygame.mixer.music.set_volume.assert_called_with(0.5)
    
    # 4. 模拟触发进入 PROMPT 状态 (Reminder)
    print("\n--- 阶段 1: 触发提醒 (PROMPT) ---")
    
    # 因为 trigger_break 会在 done_event.wait() 处阻塞，我们需要 mock 掉这个 wait
    import threading
    with MagicMock() as mock_event:
        threading.Event.wait = MagicMock() # 让 wait 立即返回
        monitor.trigger_break() 
    # 注意：trigger_break 内部会执行 audio.play(music_path)
    # 并把任务放入 gui_queue 后阻塞等待 done_event
    
    # 我们取出放入 queue 的任务并检查，但不阻塞运行
    # 实际上 trigger_break 会在后台线程跑，这里我们直接看 audio 调用
    pygame.mixer.music.load.assert_any_call("fake_reminder.mp3")
    print("SUCCESS: 已加载提醒音乐 (fake_reminder.mp3)")
    
    # 5. 模拟用户点击“开始休息” (进入 BREAK 状态)
    print("\n--- 阶段 2: 用户点击开始休息 (BREAK) ---")
    monitor.on_user_start_rest()
    # 此时状态应变为 BREAK，且由于逻辑已修改，音乐【不应该】切换（保持 fake_reminder）
    # 检查最后的 load 调用是否还是第一个
    assert pygame.mixer.music.load.call_args[0][0] == "fake_reminder.mp3"
    print("SUCCESS: 休息开始，音乐保持不变")
    
    # 6. 模拟进入反思阶段 (REFLECTION)
    print("\n--- 阶段 3: 进入反思/回答阶段 (Answering) ---")
    monitor.on_user_start_reflection()
    # 此时音乐应该切换到 reflection_path
    pygame.mixer.music.load.assert_called_with("fake_reflection.mp3")
    print("SUCCESS: 已成功切换到反思音乐 (fake_reflection.mp3)")
    
    # 7. 模拟结束工作重启
    print("\n--- 阶段 4: 提交回答并返回工作 ---")
    monitor.reset_work()
    pygame.mixer.music.stop.assert_called()
    print("SUCCESS: 音乐已停止")

    print("\n=== 所有音频逻辑分支测试通过！ ===")

if __name__ == "__main__":
    try:
        test_audio_switching_logic()
    except AssertionError as e:
        print(f"测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"执行出错: {e}")
        sys.exit(1)
