import logging
import time
import tkinter as tk
from datetime import date
from tkinter import messagebox

from config_manager import load_health_data, save_health_data


def _get_parent_window():
    try:
        import main as _main
        return getattr(_main, "tk_root", None)
    except Exception:
        return None


def _load_chart_modules(parent):
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError:
        messagebox.showwarning(
            "提示",
            "查看历史统计需要额外安装 matplotlib 和 pandas。",
            parent=parent
        )
        logging.warning("Trend view unavailable because matplotlib/pandas are not installed.")
        return None, None

    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    return plt, pd


def record_health_data(icon=None, item=None):
    today_str = str(date.today())
    parent = _get_parent_window()
    owns_root = parent is None

    root = tk.Tk() if owns_root else tk.Toplevel(parent)
    root.title("每日健康指标录入")
    root.attributes("-topmost", True)

    if not owns_root:
        root.transient(parent)

    width, height = 350, 250
    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{int(screen_width / 2 - width / 2)}+{int(screen_height / 2 - height / 2)}")

    tk.Label(root, text=f"日期: {today_str}", font=("Arial", 10, "bold")).pack(pady=5)

    frame_weight = tk.Frame(root)
    frame_weight.pack(pady=5)
    tk.Label(frame_weight, text="体重 (kg):", width=10).pack(side=tk.LEFT)
    entry_weight = tk.Entry(frame_weight, width=15)
    entry_weight.pack(side=tk.LEFT)

    frame_bp = tk.Frame(root)
    frame_bp.pack(pady=5)
    tk.Label(frame_bp, text="血压 (H/L):", width=10).pack(side=tk.LEFT)
    entry_bp_high = tk.Entry(frame_bp, width=6)
    entry_bp_high.insert(0, "120")
    entry_bp_high.pack(side=tk.LEFT)
    tk.Label(frame_bp, text="/").pack(side=tk.LEFT)
    entry_bp_low = tk.Entry(frame_bp, width=6)
    entry_bp_low.insert(0, "80")
    entry_bp_low.pack(side=tk.LEFT)

    all_data = load_health_data()

    prev_weight = None
    for data_key in reversed(sorted(all_data.keys())):
        if data_key < today_str:
            prev_weight = all_data[data_key].get("weight")
            break

    if today_str in all_data:
        entry_weight.insert(0, str(all_data[today_str].get("weight", "")))
        entry_bp_high.delete(0, tk.END)
        entry_bp_high.insert(0, str(all_data[today_str].get("bp_high", "120")))
        entry_bp_low.delete(0, tk.END)
        entry_bp_low.insert(0, str(all_data[today_str].get("bp_low", "80")))

    def show_trends():
        data = load_health_data()
        if not data:
            messagebox.showwarning("提示", "暂无健康数据", parent=root)
            return

        plt, pd = _load_chart_modules(root)
        if not plt or not pd:
            return

        df = pd.DataFrame.from_dict(data, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
        df['bp_high'] = pd.to_numeric(df['bp_high'], errors='coerce')
        df['bp_low'] = pd.to_numeric(df['bp_low'], errors='coerce')

        plt.figure(figsize=(10, 6))

        ax1 = plt.subplot(2, 1, 1)
        plt.plot(df.index, df['weight'], marker='o', color='#3498db', linewidth=2, label='体重 (kg)')
        plt.title('体重变化趋势')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()

        plt.subplot(2, 1, 2, sharex=ax1)
        plt.plot(df.index, df['bp_high'], marker='^', color='#e74c3c', label='收缩压 (H)')
        plt.plot(df.index, df['bp_low'], marker='v', color='#2ecc71', label='舒张压 (L)')
        plt.fill_between(df.index, df['bp_low'], df['bp_high'], color='gray', alpha=0.1)
        plt.title('血压变化趋势')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()

        plt.tight_layout()
        plt.show()

    def on_submit():
        weight_raw = entry_weight.get().strip()
        bp_high = entry_bp_high.get().strip()
        bp_low = entry_bp_low.get().strip()
        if not weight_raw:
            messagebox.showwarning("提醒", "请输入体重", parent=root)
            return

        try:
            weight = float(weight_raw)
        except ValueError:
            messagebox.showerror("错误", "体重请输入有效的数字", parent=root)
            return

        all_data[today_str] = {
            "weight": weight,
            "bp_high": bp_high,
            "bp_low": bp_low,
            "time": time.strftime("%H:%M:%S")
        }
        save_health_data(all_data)

        message = "数据已保存！"
        if prev_weight is not None:
            diff = weight - float(prev_weight)
            message += f"\n对比上次记录: {diff:+.2f} kg"

        messagebox.showinfo("成功", message, parent=root)
        root.destroy()
        if icon:
            icon.update_menu()

    button_frame = tk.Frame(root)
    button_frame.pack(pady=15)

    tk.Button(
        button_frame,
        text=" 提交今日记录 ",
        command=on_submit,
        bg="#27ae60",
        fg="white",
        width=15
    ).pack(side=tk.LEFT, padx=10)
    tk.Button(
        button_frame,
        text=" 查看历史统计 ",
        command=show_trends,
        bg="#3498db",
        fg="white",
        width=15
    ).pack(side=tk.LEFT, padx=10)

    root.lift()
    root.focus_force()
    entry_weight.focus_set()

    if owns_root:
        root.mainloop()
    else:
        root.wait_window(root)


def check_today_record_status():
    today_str = str(date.today())
    data = load_health_data()
    return " (已填)" if today_str in data else " (未填!)"
