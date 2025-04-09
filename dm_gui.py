import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import re
import csv
import pandas as pd

class InstagramDMTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram DM Automation Tool")
        self.root.geometry("700x620")
        self.file_path = None
        self.usernames = []
        self.rejected_usernames = []
        self.state = 'idle'  # idle, running, paused
        self.build_ui()

    def build_ui(self):
        # Message input
        tk.Label(self.root, text="Enter Message to Send:").pack(anchor='w', padx=10, pady=(10, 0))
        self.message_entry = tk.Text(self.root, height=4, wrap='word', font=("Segoe UI Emoji", 11))
        self.message_entry.pack(fill='x', padx=10)

        # File selector
        tk.Button(self.root, text="Select Input File", command=self.select_file).pack(pady=5)
        self.file_label = tk.Label(self.root, text="No file selected", fg="gray")
        self.file_label.pack()

        # Username list
        tk.Label(self.root, text="Usernames to DM:").pack(anchor='w', padx=10, pady=(10, 0))
        self.user_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, height=10)
        self.user_listbox.pack(fill='both', padx=10, pady=(0, 10), expand=False)

        tk.Button(self.root, text="Remove Selected Usernames", command=self.remove_selected_users).pack(pady=(0, 10))

        # Buttons
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

        # Log area
        tk.Label(self.root, text="Log:").pack(anchor='w', padx=10, pady=(10, 0))
        self.log_area = scrolledtext.ScrolledText(self.root, height=10, state='disabled')
        self.log_area.pack(fill='both', padx=10, pady=(0, 10), expand=True)

        self.update_buttons()

    def log(self, text):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.yview(tk.END)
        self.log_area.config(state='disabled')

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[
            ("Supported files", "*.csv *.txt *.xls *.xlsx"),
            ("CSV", "*.csv"),
            ("Text", "*.txt"),
            ("Excel", "*.xls *.xlsx")
        ])
        if path:
            self.file_path = path
            self.file_label.config(text=f"Selected: {path}")
            self.extract_usernames_from_file(path)
        else:
            self.file_label.config(text="No file selected")

    def extract_usernames_from_file(self, path):
        self.user_listbox.delete(0, tk.END)
        self.usernames.clear()
        self.rejected_usernames.clear()
        username_set = set()

        pattern = re.compile(
            r"(?:https?://)?(?:www\.)?(?:instagram\.com|Instagram\.com)/([a-zA-Z0-9._]+)(?:[/?].*)?$",
            re.IGNORECASE
        )

        def extract_from_value(value):
            raw = str(value).strip()
            match = pattern.search(raw)
            if match:
                username = match.group(1)
                lower = username.lower()
                if lower in ["p", "reel", "invite", "invites", "explore", "stories", "contact", "directory", "accounts"]:
                    self.rejected_usernames.append(raw)
                else:
                    username_set.add(username)
            elif re.match(r"^@?[a-zA-Z0-9._]+$", raw):  # raw username
                username = raw.lstrip("@")
                username_set.add(username)
            else:
                self.rejected_usernames.append(raw)

        if path.endswith(".csv") or path.endswith(".txt"):
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f) if path.endswith('.csv') else (line.split() for line in f)
                for row in reader:
                    for value in row:
                        extract_from_value(value)
        elif path.endswith((".xls", ".xlsx")):
            df = pd.read_excel(path, dtype=str, engine='openpyxl')
            for column in df.columns:
                for value in df[column]:
                    extract_from_value(value)

        self.usernames = sorted(list(username_set))
        for user in self.usernames:
            self.user_listbox.insert(tk.END, user)

        self.log(f"{len(self.usernames)} usernames loaded.")
        if self.rejected_usernames:
            self.show_rejected_popup()
        self.update_buttons()

    def show_rejected_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Rejected Usernames")
        popup.geometry("400x300")
        tk.Label(popup, text="These entries were ignored as invalid:").pack(anchor='w', padx=10, pady=5)
        box = scrolledtext.ScrolledText(popup, height=12)
        box.pack(fill='both', expand=True, padx=10, pady=5)
        box.insert(tk.END, "\n".join(self.rejected_usernames))
        box.config(state='disabled')

    def remove_selected_users(self):
        selected_indices = list(self.user_listbox.curselection())[::-1]
        for i in selected_indices:
            username = self.user_listbox.get(i)
            self.usernames.remove(username)
            self.user_listbox.delete(i)
        self.log("Selected usernames removed.")
        self.update_buttons()

    def update_buttons(self):
        if self.state == 'idle':
            self.start_btn.config(state='normal' if self.usernames else 'disabled')
            self.pause_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')
            self.stop_btn.config(state='disabled')
        elif self.state == 'running':
            self.start_btn.config(state='disabled')
            self.pause_btn.config(state='normal')
            self.resume_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
        elif self.state == 'paused':
            self.start_btn.config(state='disabled')
            self.pause_btn.config(state='disabled')
            self.resume_btn.config(state='normal')
            self.stop_btn.config(state='normal')

    def start(self):
        if not self.usernames:
            messagebox.showerror("Error", "No usernames to message.")
            return
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Error", "Please enter a message to send.")
            return

        self.state = 'running'
        self.update_buttons()
        threading.Thread(target=self.run_dm_process, daemon=True).start()

    def pause(self):
        if self.state == 'running':
            self.state = 'paused'
            self.log("Paused.")
            self.update_buttons()

    def resume(self):
        if self.state == 'paused':
            self.state = 'running'
            self.log("Resumed.")
            self.update_buttons()

    def stop(self):
        self.state = 'idle'
        self.log("Stopped.")
        self.update_buttons()

    def run_dm_process(self):
        self.log("Starting DM process...")
        import time
        for i, username in enumerate(self.usernames, start=1):
            if self.state == 'idle':
                self.log("Process stopped.")
                break
            while self.state == 'paused':
                time.sleep(1)
            self.log(f"[{i}/{len(self.usernames)}] Ready to message @{username}")
            time.sleep(1)  # Placeholder for actual sending logic
        self.log("DM process completed.")
        self.state = 'idle'
        self.update_buttons()

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramDMTool(root)
    root.mainloop()
