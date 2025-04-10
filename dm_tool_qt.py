import sys
import pandas as pd
import re
import csv

from PyQt5.QtWidgets import (
    QApplication, QWidget, QTextEdit, QLabel, QPushButton,
    QFileDialog, QListWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QListWidgetItem, QComboBox, QDialog, QFormLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class DMWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, usernames):
        super().__init__()
        self.usernames = usernames
        self.paused = False
        self.stopped = False

    def run(self):
        self.log_signal.emit("Starting DM process...")
        for i, username in enumerate(self.usernames, start=1):
            if self.stopped:
                self.log_signal.emit("Process stopped.")
                break
            while self.paused:
                self.msleep(500)
            self.log_signal.emit(f"[{i}/{len(self.usernames)}] Ready to message @{username}")
            self.sleep(1)
        self.log_signal.emit("DM process completed.")
        self.finished_signal.emit()

class DMApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instagram DM Automation Tool (PyQt5)")
        self.setGeometry(100, 100, 700, 650)

        self.usernames = []
        self.rejected_usernames = []
        self.worker = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here... 💬")
        layout.addWidget(QLabel("Enter Message to Send:"))
        layout.addWidget(self.message_input)

        file_button = QPushButton("Select Input File")
        file_button.clicked.connect(self.open_file)
        layout.addWidget(file_button)

        self.file_label = QLabel("No file selected")
        layout.addWidget(self.file_label)

        layout.addWidget(QLabel("Usernames to DM:"))
        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.user_list)

        remove_btn = QPushButton("Remove Selected Usernames")
        remove_btn.clicked.connect(self.remove_selected_users)
        layout.addWidget(remove_btn)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_process)
        btn_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_process)
        self.pause_btn.setEnabled(False)
        btn_layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.resume_process)
        self.resume_btn.setEnabled(False)
        btn_layout.addWidget(self.resume_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_process)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Log:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Files (*.csv *.txt *.xls *.xlsx)")
        if not path:
            return

        self.file_label.setText(f"Selected: {path}")
        if path.endswith((".xls", ".xlsx")):
            self.open_excel_sheet_column(path)
        else:
            self.extract_from_file(path)

    def open_excel_sheet_column(self, path):
        try:
            excel_file = pd.ExcelFile(path, engine='openpyxl')
            # Step 1: Sheet selection
            sheet, ok = self.dropdown_dialog("Select Sheet", excel_file.sheet_names)
            if not ok or sheet not in excel_file.sheet_names:
                return

            # Step 2: Column selection from selected sheet
            df = pd.read_excel(excel_file, sheet_name=sheet, dtype=str)
            column, ok = self.dropdown_dialog("Select Column", list(df.columns))
            if not ok or column not in df.columns:
                return

            # Extract from the selected column
            self.extract_from_values(df[column].astype(str).tolist())

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def dropdown_dialog(self, title, options):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QFormLayout(dialog)

        combo = QComboBox()
        combo.addItems([str(opt) for opt in options])  # <- force all options to str
        layout.addRow(QLabel(f"{title}:"), combo)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        layout.addRow(ok_btn)

        dialog.setLayout(layout)
        if dialog.exec_():
            return combo.currentText(), True
        return "", False

    def extract_from_file(self, path):
        values = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f) if path.endswith('.csv') else (line.split() for line in f)
            for row in reader:
                values.extend(row)
        self.extract_from_values(values)

    def extract_from_values(self, values):
        self.user_list.clear()
        self.usernames = []
        self.rejected_usernames = []
        username_set = set()
        pattern = re.compile(
            r"(?:https?://)?(?:www\.)?(?:instagram\.com|Instagram\.com)/([a-zA-Z0-9._]+)(?:[/?].*)?$",
            re.IGNORECASE
        )

        for raw in values:
            raw = str(raw).strip()
            match = pattern.search(raw)
            if match:
                username = match.group(1)
                if username.lower() in ["p", "reel", "invite", "invites", "explore", "stories", "contact", "directory", "accounts"]:
                    self.rejected_usernames.append(raw)
                else:
                    username_set.add(username)
            elif re.match(r"^@?[a-zA-Z0-9._]+$", raw):
                username_set.add(raw.lstrip("@"))
            else:
                self.rejected_usernames.append(raw)

        self.usernames = sorted(list(username_set))
        self.user_list.addItems(self.usernames)
        self.log(f"{len(self.usernames)} usernames loaded.")

        if self.rejected_usernames:
            QMessageBox.information(self, "Rejected Usernames", "\n".join(self.rejected_usernames))

        self.update_buttons()

    def remove_selected_users(self):
        selected = self.user_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select usernames to remove.")
            return

        usernames_to_remove = [item.text() for item in selected]

        confirm_text = "\n".join(usernames_to_remove)
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"The following usernames will be removed:\n\n{confirm_text}\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            for item in selected:
                self.usernames.remove(item.text())
                self.user_list.takeItem(self.user_list.row(item))
            self.log(f"Removed {len(usernames_to_remove)} usernames.")
            self.update_buttons()

    def start_process(self):
        message = self.message_input.toPlainText().strip()
        if not self.usernames or not message or message.startswith("Type your message"):
            QMessageBox.warning(self, "Missing Info", "Please enter a message and load usernames.")
            return
        self.worker = DMWorker(self.usernames)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.reset_buttons)
        self.worker.start()
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

    def pause_process(self):
        if self.worker:
            self.worker.paused = True
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)

    def resume_process(self):
        if self.worker:
            self.worker.paused = False
            self.resume_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)

    def stop_process(self):
        if self.worker:
            self.worker.stopped = True
            self.reset_buttons()

    def reset_buttons(self):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

    def update_buttons(self):
        self.start_btn.setEnabled(bool(self.usernames))

    def log(self, text):
        self.log_output.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DMApp()
    window.show()
    sys.exit(app.exec_())
