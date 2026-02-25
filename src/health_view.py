import tkinter as tk
from tkinter import messagebox
from datetime import date
import time
from datetime import date, datetime, timedelta
from config_manager import load_health_data, save_health_data
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd

# Setup Matplotlib for Chinese display
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False


def record_health_data(icon=None, item=None):
    today_str = str(date.today())
    
    root = tk.Tk()
    root.title("每日健康指标录入")
    root.attributes("-topmost", True)
    
    width, height = 350, 250
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{int(sw/2-width/2)}+{int(sh/2-height/2)}")
    
    tk.Label(root, text=f"日期: {today_str}", font=("Arial", 10, "bold")).pack(pady=5)
    
    # Weight
    f_weight = tk.Frame(root)
    f_weight.pack(pady=5)
    tk.Label(f_weight, text="体重 (kg):", width=10).pack(side=tk.LEFT)
    e_weight = tk.Entry(f_weight, width=15)
    e_weight.pack(side=tk.LEFT)
    
    # BP
    f_bp = tk.Frame(root)
    f_bp.pack(pady=5)
    tk.Label(f_bp, text="血压 (H/L):", width=10).pack(side=tk.LEFT)
    e_bp_h = tk.Entry(f_bp, width=6)
    e_bp_h.insert(0, "120")
    e_bp_h.pack(side=tk.LEFT)
    tk.Label(f_bp, text="/").pack(side=tk.LEFT)
    e_bp_l = tk.Entry(f_bp, width=6)
    e_bp_l.insert(0, "80")
    e_bp_l.pack(side=tk.LEFT)
    
    all_data = load_health_data()
    
    # Calculate previous weight for change info
    sorted_dates = sorted(all_data.keys())
    prev_weight = None
    if sorted_dates:
        # Find latest weight before today
        for d in reversed(sorted_dates):
            if d < today_str:
                prev_weight = all_data[d].get("weight")
                break

    if today_str in all_data:
        e_weight.insert(0, str(all_data[today_str].get("weight", "")))
        e_bp_h.delete(0, tk.END)
        e_bp_h.insert(0, str(all_data[today_str].get("bp_high", "120")))
        e_bp_l.delete(0, tk.END)
        e_bp_l.insert(0, str(all_data[today_str].get("bp_low", "80")))

    def show_trends():
        data = load_health_data()
        if not data:
            messagebox.showwarning("提示", "暂无健康数据")
            return
        
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Ensure numeric types
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
        df['bp_high'] = pd.to_numeric(df['bp_high'], errors='coerce')
        df['bp_low'] = pd.to_numeric(df['bp_low'], errors='coerce')
        
        plt.figure(figsize=(10, 6))
        
        # Subplot 1: Weight
        ax1 = plt.subplot(2, 1, 1)
        plt.plot(df.index, df['weight'], marker='o', color='#3498db', linewidth=2, label='体重 (kg)')
        plt.title('体重变化趋势')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Subplot 2: BP
        ax2 = plt.subplot(2, 1, 2, sharex=ax1)
        plt.plot(df.index, df['bp_high'], marker='^', color='#e74c3c', label='收缩压 (H)')
        plt.plot(df.index, df['bp_low'], marker='v', color='#2ecc71', label='舒张压 (L)')
        plt.fill_between(df.index, df['bp_low'], df['bp_high'], color='gray', alpha=0.1)
        plt.title('血压变化趋势')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        plt.tight_layout()
        plt.show()

    def on_submit():
        w_raw = e_weight.get().strip()
        bh = e_bp_h.get().strip()
        bl = e_bp_l.get().strip()
        if not w_raw:
            messagebox.showwarning("提醒", "请输入体重")
            return
        
        try:
            w = float(w_raw)
            all_data[today_str] = {
                "weight": w,
                "bp_high": bh,
                "bp_low": bl,
                "time": time.strftime("%H:%M:%S")
            }
            save_health_data(all_data)
            
            # Show change status
            msg = "数据已保存！"
            if prev_weight:
                diff = w - float(prev_weight)
                msg += f"\n对比上次记录: {diff:+.2f} kg"
            
            messagebox.showinfo("成功", msg)
            root.destroy()
            if icon:
                icon.update_menu()
        except ValueError:
            messagebox.showerror("错误", "体重请输入有效的数字")

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=15)
    
    tk.Button(btn_frame, text=" 提交今日记录 ", command=on_submit, bg="#27ae60", fg="white", width=15).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text=" 查看历史统计 ", command=show_trends, bg="#3498db", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    
    root.lift()
    root.focus_force()
    
    # In pystray context, sometimes we need to ensure the window is 'shown' 
    # and has focus. We manually trigger focus on the weight entry.
    e_weight.focus_set()
    
    root.mainloop()

def check_today_record_status():

    today_str = str(date.today())
    data = load_health_data()
    return " (已填)" if today_str in data else " (未填!)"
