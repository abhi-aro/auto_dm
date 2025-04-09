# file: dm_gui.py

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading

class InstagramDMTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram DM Automation Tool")
        self.root.geometry("600x500")
        self.file_path = None
        self.is_paused = False
        self.is_stopped = False

        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="Enter Message to Send:").pack(anchor='w', padx=10, pady=(10, 0))
        self.message_entry = tk.Text(self.root, height=4, wrap='word')
        self.message_entry.pack(fill='x', padx=10)

        tk.Button(self.root, text="Select CSV File", command=self.select_file).pack(pady=5)

        self.file_label = tk.Label(self.root, text="No file selected", fg="gray")
        self.file_label.pack()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="Start", command=self.start)
        self.start_btn.pack(side='left', padx=5)

        self.pause_btn = tk.Button(btn_frame, text="Pause", command=self.pause)
        self.pause_btn.pack(side='left', padx=5)

        self.resume_btn = tk.Button(btn_frame, text="Resume", command=self.resume)
        self.resume_btn.pack(side='left', padx=5)

        self.stop_btn = tk.Button(btn_frame, text="Stop", command=self.stop)
        self.stop_btn.pack(side='left', padx=5)

        tk.Label(self.root, text="Log:").pack(anchor='w', padx=10, pady=(10, 0))
        self.log_area = scrolledtext.ScrolledText(self.root, height=10, state='disabled')
        self.log_area.pack(fill='both', padx=10, pady=(0, 10), expand=True)

    def log(self, text):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.yview(tk.END)
        self.log_area.config(state='disabled')

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.file_path = path
            self.file_label.config(text=f"Selected: {path}")
        else:
            self.file_label.config(text="No file selected")

    def start(self):
        if not self.file_path:
            messagebox.showerror("Error", "Please select a CSV file first.")
            return
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Error", "Please enter a message to send.")
            return
        self.is_stopped = False
        self.is_paused = False
        threading.Thread(target=self.run_dm_process, daemon=True).start()

    def pause(self):
        self.is_paused = True
        self.log("Paused.")

    def resume(self):
        if self.is_paused:
            self.is_paused = False
            self.log("Resumed.")

    def stop(self):
        self.is_stopped = True
        self.log("Stopped.")

    def run_dm_process(self):
        self.log("Starting DM process...")
        # Placeholder logic – will integrate actual DM logic later
        import time
        for i in range(1, 6):
            if self.is_stopped:
                self.log("Process stopped.")
                break
            while self.is_paused:
                time.sleep(1)
            self.log(f"Sending message {i}...")
            time.sleep(1)
        self.log("DM process completed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramDMTool(root)
    root.mainloop()
