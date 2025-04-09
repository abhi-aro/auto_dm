import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter import ttk
from tkinter.font import Font
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
        self.state = 'idle'
        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="Enter Message to Send:").pack(anchor='w', padx=10, pady=(10, 0))

        emoji_font = Font(family="Segoe UI Emoji", size=11)
        self.message_entry = tk.Text(self.root, height=4, wrap='word')
        self.message_entry.configure(font=emoji_font)
        self.message_entry.insert("1.0", "Type your message here... 💬")
        self.message_entry.bind("<FocusIn>", self.clear_placeholder)
        self.message_entry.pack(fill='x', padx=10)

        tk.Button(self.root, text="Select Input File", command=self.select_file).pack(pady=5)
        self.file_label = tk.Label(self.root, text="No file selected", fg="gray")
        self.file_label.pack()

        tk.Label(self.root, text="Usernames to DM:").pack(anchor='w', padx=10, pady=(10, 0))
        self.user_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, height=10)
        self.user_listbox.pack(fill='both', padx=10, pady=(0, 10), expand=False)

        tk.Button(self.root, text="Remove Selected Usernames", command=self.remove_selected_users).pack(pady=(0, 10))

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

        self.update_buttons()

    def clear_placeholder(self, event):
        current = self.message_entry.get("1.0", tk.END).strip()
        if current == "Type your message here... 💬":
            self.message_entry.delete("1.0", tk.END)

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
            if path.endswith((".xls", ".xlsx")):
                self.select_excel_sheet_column(path)
            else:
                self.extract_usernames_from_file(path)
        else:
            self.file_label.config(text="No file selected")

    def select_excel_sheet_column(self, path):
        try:
            excel_file = pd.ExcelFile(path, engine='openpyxl')
            popup = tk.Toplevel(self.root)
            popup.title("Select Sheet and Column")
            popup.geometry("350x200")

            tk.Label(popup, text="Choose Sheet:").pack(pady=(10, 5))
            sheet_var = tk.StringVar()
            sheet_menu = ttk.Combobox(popup, textvariable=sheet_var, values=excel_file.sheet_names, state="readonly")
            sheet_menu.pack(pady=5)

            tk.Label(popup, text="Choose Column:").pack(pady=(10, 5))
            column_var = tk.StringVar()
            column_menu = ttk.Combobox(popup, textvariable=column_var, state="readonly")
            column_menu.pack(pady=5)

            def on_sheet_select(event):
                selected_sheet = sheet_var.get()
                df = pd.read_excel(excel_file, sheet_name=selected_sheet, dtype=str)
                column_menu['values'] = list(df.columns)

            sheet_menu.bind("<<ComboboxSelected>>", on_sheet_select)

            def confirm_selection():
                sheet = sheet_var.get()
                column = column_var.get()
                if sheet and column:
                    df = pd.read_excel(excel_file, sheet_name=sheet, dtype=str)
                    popup.destroy()
                    self.extract_usernames_from_dataframe(df[[column]])
                else:
                    messagebox.showerror("Error", "Please select both sheet and column.")

            tk.Button(popup, text="Confirm", command=confirm_selection).pack(pady=15)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file: {e}")

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
            elif re.match(r"^@?[a-zA-Z0-9._]+$", raw):
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

        self.finalize_usernames(username_set)

    def extract_usernames_from_dataframe(self, df):
        self.user_listbox.delete(0, tk.END)
        self.usernames.clear()
        self.rejected_usernames.clear()
        username_set = set()

        pattern = re.compile(
            r"(?:https?://)?(?:www\.)?(?:instagram\.com|Instagram\.com)/([a-zA-Z0-9._]+)(?:[/?].*)?$",
            re.IGNORECASE
        )

        for col in df.columns:
            for value in df[col]:
                raw = str(value).strip()
                match = pattern.search(raw)
                if match:
                    username = match.group(1)
                    lower = username.lower()
                    if lower in ["p", "reel", "invite", "invites", "explore", "stories", "contact", "directory", "accounts"]:
                        self.rejected_usernames.append(raw)
                    else:
                        username_set.add(username)
                elif re.match(r"^@?[a-zA-Z0-9._]+$", raw):
                    username = raw.lstrip("@")
                    username_set.add(username)
                else:
                    self.rejected_usernames.append(raw)

        self.finalize_usernames(username_set)

    def finalize_usernames(self, username_set):
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
        if not message or message == "Type your message here... 💬":
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
            time.sleep(1)
        self.log("DM process completed.")
        self.state = 'idle'
        self.update_buttons()

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramDMTool(root)
    root.mainloop()
