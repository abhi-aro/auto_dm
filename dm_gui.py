import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import re
import csv

class InstagramDMTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram DM Automation Tool")
        self.root.geometry("700x600")
        self.file_path = None
        self.usernames = []
        self.is_paused = False
        self.is_stopped = False

        self.build_ui()

    def build_ui(self):
        # Message input
        tk.Label(self.root, text="Enter Message to Send:").pack(anchor='w', padx=10, pady=(10, 0))
        self.message_entry = tk.Text(self.root, height=4, wrap='word')
        self.message_entry.pack(fill='x', padx=10)

        # File selector
        tk.Button(self.root, text="Select CSV File", command=self.select_file).pack(pady=5)
        self.file_label = tk.Label(self.root, text="No file selected", fg="gray")
        self.file_label.pack()

        # Username list
        tk.Label(self.root, text="Usernames to DM:").pack(anchor='w', padx=10, pady=(10, 0))
        self.user_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, height=10)
        self.user_listbox.pack(fill='both', padx=10, pady=(0, 10), expand=False)

        # Remove selected
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
            self.extract_usernames_from_csv(path)
        else:
            self.file_label.config(text="No file selected")

    def extract_usernames_from_csv(self, path):
        self.user_listbox.delete(0, tk.END)
        self.usernames.clear()
        username_set = set()
        pattern = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/([^/?\s]+)|^@?([a-zA-Z0-9._]+)$")

        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                for value in row:
                    match = pattern.search(value.strip())
                    if match:
                        username = match.group(1) or match.group(2)
                        if username and not username.startswith("invite") and username not in username_set:
                            username_set.add(username)
                            self.usernames.append(username)

        for user in self.usernames:
            self.user_listbox.insert(tk.END, user)

        self.log(f"{len(self.usernames)} usernames loaded.")

    def remove_selected_users(self):
        selected_indices = list(self.user_listbox.curselection())[::-1]
        for i in selected_indices:
            username = self.user_listbox.get(i)
            self.usernames.remove(username)
            self.user_listbox.delete(i)
        self.log("Selected usernames removed.")

    def start(self):
        if not self.usernames:
            messagebox.showerror("Error", "No usernames to message.")
            return
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Error", "Please enter a message to send.")
            return

        self.is_stopped = False
        self.is_paused = False
        self.start_btn.config(state='disabled')
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
        self.start_btn.config(state='normal')
        self.log("Stopped.")

    def run_dm_process(self):
        self.log("Starting DM process...")
        import time
        for i, username in enumerate(self.usernames, start=1):
            if self.is_stopped:
                self.log("Process stopped.")
                break
            while self.is_paused:
                time.sleep(1)
            self.log(f"[{i}/{len(self.usernames)}] Ready to message @{username}")
            time.sleep(1)  # Placeholder for actual send logic
        self.log("DM process completed.")
        self.start_btn.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramDMTool(root)
    root.mainloop()
