import sys
import sqlite3

from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox
from PyQt6 import uic
from datetime import datetime


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def back_to_main(prev_page):
    prev_page.close()
    ex = MainPage()
    ex.show()

def get_previous(entity, limit):
    previous = cur.execute("""SELECT name FROM doings ORDER BY id DESC LIMIT ?""", (limit, )).fetchall()
    entity.previous.setText('\n'.join([prev[0] for prev in previous]))


connection = sqlite3.connect("CheckTimeDB.sqlite")
cur = connection.cursor()

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

    def closeEvent(self, event):
        connection.close()


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
        get_previous(self, 16)
        self.done.clicked.connect(self.write)
        self.back.clicked.connect(self.back_fun)


    def back_fun(self):
        back_to_main(self)

    def write(self):
        date = str(datetime.now()).split()[0]
        if self.name.text() != '' and self.timeEdit.text() != '0:00':
            maybe_id = cur.execute("""SELECT id FROM doings WHERE LOWER(name) LIKE ? LIMIT 1""",
                                        (self.name.text().lower(),)).fetchall()
            print(maybe_id)
            if maybe_id == []:
                cur.execute("""INSERT INTO doings (name) VALUES (?)""", (self.name.text(),))
                doing_id = cur.lastrowid
                connection.commit()
            else:
                doing_id = maybe_id[0][0]
            duration = int(self.timeEdit.text().split(':')[0]) * 60 + int(self.timeEdit.text().split(':')[1])
            cur.execute("""INSERT INTO timecheck (doingid, startdate, duration) 
            VALUES (?, ?, ?)""", (doing_id, date, duration))
            connection.commit()
            get_previous(self, 16)
        else:
            self.warnings.setText("Оба поля должны быть заполнены!")






class TimerPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("TimerPage.ui", self)
        self.start = True
        self.doing.setText('')
        self.startstopbtn.clicked.connect(self.btnclicked)
        self.back.clicked.connect(self.back_fun)
        get_previous(self, 15)


    def back_fun(self):
        back_to_main(self)

    def btnclicked(self):
        if self.start:
            if str(self.doing.text()) == '':
                self.warning.setText('Введите название!')
            else:
                self.doing.setReadOnly(True)
                self.startstopbtn.setText('СТОП')
                self.warning.setText('Отсчёт времени пошёл! Итоговое значение вы увидите после нажатия кнопки.')
                self.start = False
                self.date = str(datetime.now()).split()[0]
                self.start_time = datetime.now()
        else:
            self.now_time = datetime.now()
            durat = (self.now_time - self.start_time).seconds
            self.res_time = (durat // 3600, durat % 3600 // 60)
            self.start = True
            self.startstopbtn.setText('СТАРТ')
            self.doing.setReadOnly(False)
            self.hours.display(self.res_time[0])
            self.minuts.display(self.res_time[1])
            intent = QMessageBox.question(self, 'Добавление записи',
                                          f"Вы потратили на зaдачу '{self.doing.text()}' "
                                          f"{self.res_time[0]} часов и {self.res_time[1]} минут. Добавить запись "
                                          f"об этом действии?",
                                          QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if intent == QMessageBox.StandardButton.Yes:
                maybe_id = cur.execute("""SELECT id FROM doings WHERE LOWER(name) LIKE ? LIMIT 1""",
                                       (self.doing.text().lower(),)).fetchall()
                if maybe_id == []:
                    cur.execute("""INSERT INTO doings (name) VALUES (?)""", (self.doing.text(),))
                    doing_id = cur.lastrowid
                else:
                    doing_id = maybe_id[0][0]
                connection.commit()
                cur.execute("""INSERT INTO timecheck (doingid, startdate, duration) 
                            VALUES (?, ?, ?)""", (doing_id, self.date, durat // 60))
                connection.commit()
                get_previous(self, 15)
            self.hours.display(0)
            self.minuts.display(0)
            self.doing.setText('')
            self.warning.setText('')







if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainPage()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
