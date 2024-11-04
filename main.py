import sys
import sqlite3

from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget
from PyQt6 import uic
from datetime import datetime


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

def back_to_main(prev_page):
    prev_page.close()
    ex = MainPage()
    ex.show()

class MainPage(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("MainPageUi.ui", self)
        self.statistic.clicked.connect(self.statistclicked)
        self.time.clicked.connect(self.timeclicked)
        self.timer.clicked.connect(self.timerclicked)

    def statistclicked(self):
        self.statistic_form = StatisticPage()
        self.statistic_form.show()

    def timeclicked(self):
        self.timeinput_form = TimeInputPage()
        self.timeinput_form.show()

    def timerclicked(self):
        self.timer_form = TimerPage()
        self.timer_form.show()

class StatisticPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("StatisticPage.ui", self)
        self.setValues()
        self.back.clicked.connect(self.back_fun)

    def back_fun(self):
        back_to_main(self)

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
        self.back.clicked.connect(self.back_fun)

    def back_fun(self):
        back_to_main(self)


    def write(self):
        date = str(datetime.now()).split()[0]
        if self.name.text() != '' and self.timeEdit.text() != '0:00':
            maybe_id = self.cur.execute("""SELECT id FROM doings WHERE LOWER(name) LIKE ? LIMIT 1""", (self.name.text().lower(), )).fetchall()
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

class TimerPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("TimerPage.ui", self)
        self.start = True
        self.doing.setText('')
        self.startstopbtn.clicked.connect(self.btnclicked)
        self.back.clicked.connect(self.back_fun)

    def back_fun(self):
        back_to_main(self)

    def btnclicked(self):
        if self.start:
            if str(self.doing.text()) == '':
                self.warning.setText('Введите название!')
            else:
                self.warning.setText('')
                self.doing.setReadOnly(True)
                self.startstopbtn.setText('СТОП')
                self.start = False
                date = str(datetime.now()).split()[0]
                self.time = datetime.now()
                self.timer()
        else:
            self.startstopbtn.setText('СТАРТ')
            self.start = True

    def timer(self):
        while not self.start:
            diffsec = (datetime.now() - self.time).seconds
            self.hours.display(diffsec)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainPage()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
