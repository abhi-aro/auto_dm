from PyQt5.QtCore import QThread, pyqtSignal

class DMWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, usernames):
        super().__init__()
        self.usernames = usernames
        self.paused = False
        self.stopped = False
