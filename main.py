import sys
import sqlite3

from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget
from PyQt6 import uic
from datetime import datetime


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


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
        self.connection = sqlite3.connect("CheckTimeDB.sqlite")
        self.cur = self.connection.cursor()
        self.get_previous()
        self.done.clicked.connect(self.write)


    def write(self):
        date = str(datetime.now()).split()[0]
        if self.name.text() != '' and self.timeEdit.text() != '0:00':
            maybe_id = self.cur.execute("""SELECT id FROM doings WHERE name LIKE ? LIMIT 1""", (self.name.text(), )).fetchall()
            if maybe_id == []:
                self.cur.execute("""INSERT INTO doings (name) VALUES (?)""", (self.name.text(),))
                doing_id = self.cur.lastrowid
                self.connection.commit()
            else:
                doing_id = maybe_id[0][0]
            duration = int(self.timeEdit.text().split(':')[0]) * 60 + int(self.timeEdit.text().split(':')[1])
            self.cur.execute("""INSERT INTO timecheck (doingid, startdate, duration) 
            VALUES (?, ?, ?)""", (doing_id, date, duration))
            self.connection.commit()
            self.get_previous()
        else:
            self.warnings.setText("Оба поля должны быть заполнены!")
    def get_previous(self):
        previous = self.cur.execute("""SELECT name FROM doings ORDER BY id DESC LIMIT 16""").fetchall()
        self.previous.setText('\n'.join([prev[0] for prev in previous]))

    def closeEvent(self, event):
        self.connection.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TimeInputPage()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
