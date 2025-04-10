from PyQt5.QtWidgets import QApplication
from gui.app import DMApp
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DMApp()
    window.show()
    sys.exit(app.exec_())
