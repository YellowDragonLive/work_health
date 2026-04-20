import os
import sys
import ctypes
import subprocess
import winreg
import logging
import time

AUTOSTART_APP_NAME = "HealthAssistant"
AUTOSTART_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def hide_console():
    """Ensure the application runs without a console window."""
    # 防止递归：如果已经带有 --nowindow，说明是子进程
    if "--nowindow" in sys.argv:
        # 尝试隐藏已有的窗口
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
        return

    current_exe = sys.executable
    if current_exe.lower().endswith("python.exe"):
        pythonw = current_exe.lower().replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            logging.info("Restarting with pythonw and --nowindow...")
            subprocess.Popen([pythonw] + sys.argv + ["--nowindow"], creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)


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


def force_kill_all_instances():
    """使用 WMIC 彻底清理系统中所有残留的 main.py 进程 (除了当前进程)。"""
    my_pid = str(os.getpid())
    killed_any = False
    
    try:
        # 查找所有命令行中包含 main.py 的 python 进程
        cmd = 'wmic process where "name like \'python%\' and commandline like \'%main.py%\'" get processid,commandline'
        output = subprocess.check_output(cmd, shell=True).decode('gbk', errors='ignore')
        
        for line in output.strip().split('\n'):
            line = line.strip()
            # 排除空的和 wmic 自身的输出
            if 'main.py' in line and 'wmic' not in line:
                # 寻找行末的进程 ID
                parts = line.split()
                if parts:
                    pid = parts[-1]
                    if pid.isdigit() and pid != my_pid:
                        logging.info(f"清理旧实例进程: {pid}")
                        subprocess.run(['taskkill', '/F', '/T', '/PID', pid], capture_output=True)
                        killed_any = True
    except Exception as e:
        logging.debug(f"WMIC cleanup error: {e}")

    # 方法 2: 端口清理 (双重保险)
    try:
        cmd = 'netstat -ano'
        output = subprocess.check_output(cmd, shell=True).decode('gbk', errors='ignore')
        for line in output.strip().split('\n'):
            if ':45678' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid != '0' and pid != my_pid:
                        logging.info(f"清理端口占用进程: {pid}")
                        subprocess.run(['taskkill', '/F', '/T', '/PID', pid], capture_output=True)
                        killed_any = True
    except: pass

    if killed_any:
        time.sleep(1.0) # 给系统一点资源回收时间
    return killed_any
