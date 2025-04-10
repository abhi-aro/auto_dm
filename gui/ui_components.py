from PyQt5.QtWidgets import QMessageBox, QDialog, QComboBox, QLabel, QPushButton, QFormLayout

def show_continue_dialog(parent):
    dlg = QMessageBox(parent)
    dlg.setWindowTitle("Continue Login")
    dlg.setText("Chrome has opened. Please complete Instagram login & 2FA.\n\nClick 'Continue' once you're logged in.")
    dlg.setStandardButtons(QMessageBox.Ok)
    dlg.exec_()

def dropdown_dialog(parent, title, options):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    layout = QFormLayout(dialog)
    combo = QComboBox()
    combo.addItems([str(opt) for opt in options])
    layout.addRow(QLabel(f"{title}:", parent), combo)
    ok_btn = QPushButton("OK")
    ok_btn.clicked.connect(dialog.accept)
    layout.addRow(ok_btn)
    dialog.setLayout(layout)
    if dialog.exec_():
        return combo.currentText(), True
    return "", False
