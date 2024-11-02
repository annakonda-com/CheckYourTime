import sys
import sqlite3
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget
from PyQt6 import uic


class MainPage(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("MainPageUi.ui", self)
        self.statistic.clicked.connect(self.statistclicked)
        self.time.clicked.connect(self.timeclicked)
        self.timer.clicked.connect(self.timerclicked)

    def statistclicked(self):
        pass

    def timeclicked(self):
        pass

    def timerclicked(self):
        pass

class StatisticPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("StatisticPage.ui")
        self.setValues()

    def setValues(self):
        pass

class TimeInputPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("TimePage.ui", self)
        self.done.clicked.connect(self.write)

    def write(self):
        pass



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TimeInputPage()
    ex.show()
    sys.exit(app.exec())







