import tkinter as tk
from tkinter import ttk
import threading

class ReminderWindow:
    def __init__(self, message, duration_seconds, on_start_rest, on_snooze):
        """
        Args:
            message: Text to display.
            duration_seconds: Duration of the break (for countdown).
            on_start_rest: Callback when user clicks 'Start Rest'.
            on_snooze: Callback when user clicks 'Snooze'.
        """
        self.message = message
        self.duration_seconds = duration_seconds
        self.on_start_rest = on_start_rest
        self.on_snooze = on_snooze
        self.root = None
        self.is_counting_down = False

    def show(self):
        """Displays the window. Must be called from the thread that handles GUI."""
        if self.root:
            return
            
        self.root = tk.Tk()
        self.root.title("久坐提醒")
        
        # Make it fullscreen
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#2c3e50")

        # Container frame for centering content
        self.main_container = tk.Frame(self.root, bg="#2c3e50")
        self.main_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # UI Elements inside container
        self.lbl_msg = tk.Label(self.main_container, text=self.message, 
                                font=("Microsoft YaHei UI", 32, "bold"), 
                                fg="white", bg="#2c3e50", wraplength=800)
        self.lbl_msg.pack(pady=60)

        self.frame_btns = tk.Frame(self.main_container, bg="#2c3e50")
        self.frame_btns.pack(pady=20)

        self.btn_rest = tk.Button(self.frame_btns, text="开始休息 (Start Break)", 
                                  command=self._handle_start_rest,
                                  font=("Microsoft YaHei UI", 18, "bold"), bg="#27ae60", fg="white", 
                                  relief="flat", padx=40, pady=20)
        self.btn_rest.pack(side=tk.LEFT, padx=30)

        self.btn_snooze = tk.Button(self.frame_btns, text="推迟 5 分钟", 
                                    command=self._handle_snooze,
                                    font=("Microsoft YaHei UI", 18, "bold"), bg="#e67e22", fg="white", 
                                    relief="flat", padx=40, pady=20)
        self.btn_snooze.pack(side=tk.LEFT, padx=30)

        self.btn_hide = tk.Button(self.main_container, text="处理其他事务 (暂时隐藏 15 秒) [Esc]", 
                                  command=self._handle_hide,
                                  font=("Microsoft YaHei UI", 12), bg="#7f8c8d", fg="white", 
                                  relief="flat", padx=20, pady=10)
        self.btn_hide.pack(pady=40)
        
        # Bind Esc key
        self.root.bind("<Escape>", lambda e: self._handle_hide())

        # Countdown Label (Hidden initially)
        self.lbl_timer = tk.Label(self.main_container, text="", font=("Segoe UI", 80, "bold"), 
                                  fg="#e74c3c", bg="#2c3e50")
        
        self.root.mainloop()

    def _handle_start_rest(self):
        # Trigger callback
        if self.on_start_rest:
            self.on_start_rest()
            
        # UI Update
        self.btn_rest.pack_forget()
        self.btn_snooze.pack_forget()
        self.lbl_msg.config(text="请起立活动！")
        self.lbl_timer.pack(pady=20)
        
        # Start local countdown display
        self.is_counting_down = True
        self._update_timer(self.duration_seconds)

    def _handle_snooze(self):
        if self.on_snooze:
            self.on_snooze()
        self.close()

    def _handle_hide(self):
        """Temporarily hides the window for 15 seconds."""
        if not self.root:
            return
        self.root.withdraw() # Hide window
        # Schedule wake up
        self.root.after(15000, lambda: self.root.deiconify() if self.root else None)


    def _update_timer(self, remaining):
        if not self.is_counting_down:
            return
            
        if remaining < 0:
            self.close()
            return

        mins, secs = divmod(remaining, 60)
        self.lbl_timer.config(text=f"{mins:02d}:{secs:02d}")
        
        # Schedule next update
        self.root.after(1000, lambda: self._update_timer(remaining - 1))

    def close(self):
        self.is_counting_down = False
        if self.root:
            self.root.destroy()
            self.root = None

def show_reminder_process(message, duration, on_rest, on_snooze):
    """Helper to instantiate and show the window."""
    w = ReminderWindow(message, duration, on_rest, on_snooze)
    w.show()
