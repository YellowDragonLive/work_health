import pytest
import time
import os
import sys
import logging
from unittest.mock import MagicMock

# Ensure we can import modules from src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio import AudioManager
from monitor import Monitor

# Configure logging for observation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def test_audio_switching_logic():
    """Test the audio switching logic across all workflow states."""
    print("=== 开始音频切换逻辑自动化测试 ===")
    
    # 1. Prepare Mock configuration
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
    
    # 2. Mock pygame.mixer to avoid errors in headless environments and track calls
    import pygame
    pygame.mixer = MagicMock()
    pygame.mixer.music = MagicMock()
    
    # Mock file existence
    os.path.exists = MagicMock(return_value=True)
    
    # 3. Initialize Monitor
    # We mock both the mixer and the gui_queue popup display, just run logic
    gui_queue = MagicMock()
    monitor = Monitor(assets_dir="assets", config=config, gui_queue=gui_queue)
    
    # Verify initial volume setting
    print(f"验证音量设置: {config['audio']['volume']}")
    pygame.mixer.music.set_volume.assert_called_with(0.5)
    
    # 4. Simulate triggering PROMPT state (Reminder)
    print("\n--- 阶段 1: 触发提醒 (PROMPT) ---")
    
    # trigger_break would block at done_event.wait(), so we mock the wait
    import threading
    with MagicMock() as mock_event:
        threading.Event.wait = MagicMock()  # Make wait return immediately
        monitor.trigger_break()
    # Note: trigger_break internally executes audio.play(music_path)
    # and puts the task into gui_queue then blocks waiting for done_event
    
    # We check the audio calls directly
    pygame.mixer.music.load.assert_any_call("fake_reminder.mp3")
    print("SUCCESS: 已加载提醒音乐 (fake_reminder.mp3)")
    
    # 5. Simulate user clicking "Start Rest" (enter BREAK state)
    print("\n--- 阶段 2: 用户点击开始休息 (BREAK) ---")
    monitor.on_user_start_rest()
    # At this point state should be BREAK, and music should NOT switch (keep fake_reminder)
    # Check that the last load call is still the first one
    assert pygame.mixer.music.load.call_args[0][0] == "fake_reminder.mp3"
    print("SUCCESS: 休息开始，音乐保持不变")
    
    # 6. Simulate entering reflection phase (REFLECTION)
    print("\n--- 阶段 3: 进入反思/回答阶段 (Answering) ---")
    monitor.on_user_start_reflection()
    # At this point music should switch to reflection_path
    pygame.mixer.music.load.assert_called_with("fake_reflection.mp3")
    print("SUCCESS: 已成功切换到反思音乐 (fake_reflection.mp3)")
    
    # 7. Simulate ending work and restarting
    print("\n--- 阶段 4: 提交回答并返回工作 ---")
    monitor.reset_work()
    pygame.mixer.music.stop.assert_called()
    print("SUCCESS: 音乐已停止")

    print("\n=== 所有音频逻辑分支测试通过！ ===")
