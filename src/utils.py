import os
import sys
import ctypes
import subprocess
import winreg
import logging

AUTOSTART_APP_NAME = "HealthAssistant"
AUTOSTART_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def hide_console():
    """Ensure the application runs without a console window."""
    current_exe = sys.executable
    if current_exe.lower().endswith("python.exe"):
        pythonw = current_exe.lower().replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            subprocess.Popen([pythonw] + sys.argv, creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)

    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)


def is_autostart_enabled():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY_PATH, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, AUTOSTART_APP_NAME)
            return bool(value)
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        logging.error(f"Registry (Autostart Check) Error: {e}")
        return False


def set_autostart(enable=True):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        if enable:
            exe_path = sys.executable
            target_exe = exe_path.replace("python.exe", "pythonw.exe")
            if not os.path.exists(target_exe):
                target_exe = exe_path
                
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
            cmd = f'"{target_exe}" "{script_path}"'
            winreg.SetValueEx(key, AUTOSTART_APP_NAME, 0, winreg.REG_SZ, cmd)
            logging.info(f"Autostart enabled with: {cmd}")
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_APP_NAME)
                logging.info("Autostart disabled.")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        logging.error(f"Registry (Autostart) Error: {e}")
