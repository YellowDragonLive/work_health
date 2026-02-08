import tkinter as tk
from tkinter import messagebox
from datetime import date
import time
from config_manager import load_health_data, save_health_data

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
    if today_str in all_data:
        e_weight.insert(0, str(all_data[today_str].get("weight", "")))
        e_bp_h.delete(0, tk.END)
        e_bp_h.insert(0, str(all_data[today_str].get("bp_high", "120")))
        e_bp_l.delete(0, tk.END)
        e_bp_l.insert(0, str(all_data[today_str].get("bp_low", "80")))

    def on_submit():
        w = e_weight.get().strip()
        bh = e_bp_h.get().strip()
        bl = e_bp_l.get().strip()
        if not w:
            messagebox.showwarning("提醒", "请输入体重")
            return
        
        all_data[today_str] = {
            "weight": w,
            "bp_high": bh,
            "bp_low": bl,
            "time": time.strftime("%H:%M:%S")
        }
        save_health_data(all_data)
        messagebox.showinfo("成功", "今日健康数据已记录！")
        root.destroy()
        if icon:
            icon.update_menu()


    tk.Button(root, text="提交记录", command=on_submit, bg="#27ae60", fg="white", width=20).pack(pady=20)
    
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
