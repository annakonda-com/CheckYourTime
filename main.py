import sys
import sqlite3
import time
from sys import intern

from PyQt6.QtCore import QEvent, QObject, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox, QLabel
from PyQt6 import uic
from datetime import datetime, timedelta
from threading import Thread
from PyQt6.QtGui import QPixmap


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def back_to_main(prev_page):
    prev_page.close()
    ex = MainPage()
    ex.show()


def get_previous(entity, limit):
    previous = cur.execute("""SELECT name FROM doings ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    entity.previous.setText('\n'.join([prev[0] for prev in previous]))


def do_dict(
        arr):  # принимает список кортежей вида (время, название) и создаёт словарь с сумой времени для каждой задачи
    res = {}
    for el in arr:
        if el[1] in res:
            res[el[1]] += el[0]
        else:
            res[el[1]] = el[0]
    return res


def clean_db():
    cur.execute("""DELETE FROM timecheck WHERE startdate > '2024-09-01' AND startdate < ?""",
                (str(datetime.now() - timedelta(days=8)).split()[0],))
    connection.commit()


def mylower(line):
    return line.lower()


connection = sqlite3.connect("CheckTimeDB.sqlite")
cur = connection.cursor()
connection.create_function('MYLOWER', 1, mylower)


class OverSignal(QObject):
    overS = pyqtSignal()

class DayOverSignal(QObject):
    dayOverS = pyqtSignal()


class MainPage(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("MainPageUi.ui", self)
        self.statistic.clicked.connect(self.statistclicked)
        self.time.clicked.connect(self.timeclicked)
        self.timer.clicked.connect(self.timerclicked)
        self.setFixedSize(800, 600)
        self.pixmap = QPixmap("image.jpg")
        self.image = QLabel(self)
        self.image.move(280, 250)
        self.image.resize(250, 250)
        self.image.setPixmap(self.pixmap)

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
        self.setFixedSize(800, 600)
        self.setValues()
        self.back.clicked.connect(self.back_fun)
        clean_db()

    def back_fun(self):
        back_to_main(self)

    def setValues(self):
        for_day = cur.execute("""SELECT timecheck.duration, doings.name FROM 
            timecheck JOIN doings ON doings.id = doingid WHERE startdate = ?""",
                              (str(datetime.now()).split()[0],)).fetchall()
        for_week = cur.execute("""SELECT timecheck.duration, doings.name FROM 
            timecheck JOIN doings ON doings.id = doingid WHERE startdate BETWEEN ? AND ?""",
                               (str(datetime.now() - timedelta(days=7)).split()[0],
                                str(datetime.now()).split()[0])).fetchall()
        if for_day != []:
            self.day.setText('За день:')
            for_day = do_dict(for_day)
            for_day_text = '\n'.join([name + '\t' + str(for_day[name]) for name in for_day])
            self.day_stat.setText(for_day_text)
        if for_week != []:
            self.week.setText('За неделю:')
            for_week = do_dict(for_week)
            for_week_text = '\n'.join([name + '\t' + str(for_week[name]) for name in for_week])
            self.week_stat.setText(for_week_text)


class TimeInputPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("TimePage.ui", self)
        self.setFixedSize(800, 600)
        get_previous(self, 16)
        self.done.clicked.connect(self.write)
        self.back.clicked.connect(self.back_fun)

    def back_fun(self):
        back_to_main(self)

    def write(self):
        date = str(datetime.now()).split()[0]
        if self.name.text() != '' and self.timeEdit.text() != '0:00':
            maybe_id = cur.execute("""SELECT id FROM doings WHERE MYLOWER(name) LIKE ? LIMIT 1""",
                                   (self.name.text().lower(),)).fetchall()
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
        self.setFixedSize(800, 600)
        self.start = True
        self.doing.setText('')
        self.startstopbtn.clicked.connect(self.btnclicked)
        self.back.clicked.connect(self.back_fun)
        self.over = OverSignal()
        self.over.overS.connect(self.btnclicked)
        self.dayover = DayOverSignal()
        self.dayover.dayOverS.connect(self.day_is_over)
        self.day_was_over = False
        get_previous(self, 15)

    def back_fun(self):
        back_to_main(self)

    def timerView(self):
        while True:
            if self.start:
                break
            if self.durat == 23 * 3600 + 59 * 60 + 60:
                self.over.overS.emit()
                break
            '''if datetime.now().hour == 23 and datetime.now().minute == 59:
                self.dayover.dayOverS.emit()'''
            if self.durat == 50:
                self.dayover.dayOverS.emit()
            self.hours.display(self.durat // 3600)
            self.minuts.display(self.durat % 3600 // 60)
            self.seconds.display(self.durat % 3600 % 60)
            self.durat += 1
            time.sleep(1)

    def day_is_over(self):
        self.intents = {'doing_id': -1, 'duration': [], 'date': []}
        if self.durat >= 60:
            maybe_id = cur.execute("""SELECT id FROM doings WHERE MYLOWER(name) = ? LIMIT 1""",
                                    (self.doing.text().lower(),)).fetchall()
            if maybe_id == []:
                cur.execute("""INSERT INTO doings (name) VALUES (?)""", (self.doing.text(),))
                self.intents['doing_id'] = cur.lastrowid
            else:
                self.intents['doing_id'] = maybe_id[0][0]
            self.intents['duration'].append(self.durat // 60)
            self.intents['date'].append(str(datetime.now()).split()[0])
            self.day_was_over = True


    def btnclicked(self):
        if self.start:
            if str(self.doing.text()) == '':
                self.warning.setText('Введите название!')
            else:
                self.doing.setReadOnly(True)
                self.startstopbtn.setText('СТОП')
                self.warning.setText('Отсчёт времени пошёл!')
                self.date = str(datetime.now()).split()[0]
                self.durat = 45
                self.start = False
                t1 = Thread(target=self.timerView)
                t1.start()
        else:
            if self.day_was_over:
                print('qq1')
                if self.durat >= 60:
                    self.intents['duration'].append(self.durat - self.intents['duration'][0] // 60)
                    self.intents['date'].append(str(datetime.now()).split()[0])
                    question = QMessageBox.question(self, 'Добавление записи',
                                                  f"Вы потратили на зaдачу '{self.doing.text()}' {self.intents['date'][0]}"
                                                  f"{self.intents['duration'][0] // 3600} часов и {self.intents['duration'][0] % 3600 // 60} минут,"
                                                  f"и {self.intents['date'][1]} {self.intents['duration'][0] // 3600} часов и {self.intents['duration'][0] % 3600 // 60} минут Добавить запись "
                                                  f"об этом действии?",
                                                  QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if question == QMessageBox.StandardButton.Yes:
                        cur.execute("""INSERT INTO timecheck (doingid, startdate, duration) 
                                                        VALUES (?, ?, ?)""", (self.intents['doing_id'], self.intents['date'][0], self.intents['duration'][0] // 60))
                        connection.commit()
                        cur.execute("""INSERT INTO timecheck (doingid, startdate, duration) 
                                                                                VALUES (?, ?, ?)""", (
                        self.intents['doing_id'], self.intents['date'][1], self.intents['duration'][1] // 60))
                        connection.commit()
                        get_previous(self, 15)
                    self.hours.display(0)
                    self.minuts.display(0)
                    self.seconds.display(0)
                    self.doing.setText('')
                    self.warning.setText('')
                else:
                    self.seconds.display(0)
                    self.warning.setText('Вы не можете потратить на задачу 0 минут.')
                    self.durat = 0
            else:
                self.start = True
                self.startstopbtn.setText('СТАРТ')
                self.doing.setReadOnly(False)
                if self.durat >= 60:
                    intent = QMessageBox.question(self, 'Добавление записи',
                                                  f"Вы потратили на зaдачу '{self.doing.text()}' "
                                                  f"{self.durat // 3600} часов и {self.durat % 3600 // 60} минут. Добавить запись "
                                                  f"об этом действии?",
                                                  QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if intent == QMessageBox.StandardButton.Yes:
                        maybe_id = cur.execute("""SELECT id FROM doings WHERE MYLOWER(name) = ? LIMIT 1""",
                                               (self.doing.text().lower(),)).fetchall()
                        if maybe_id == []:
                            cur.execute("""INSERT INTO doings (name) VALUES (?)""", (self.doing.text(),))
                            doing_id = cur.lastrowid
                        else:
                            doing_id = maybe_id[0][0]
                        connection.commit()
                        cur.execute("""INSERT INTO timecheck (doingid, startdate, duration) 
                                                        VALUES (?, ?, ?)""", (doing_id, self.date, self.durat // 60))
                        connection.commit()
                        get_previous(self, 15)
                    self.hours.display(0)
                    self.minuts.display(0)
                    self.seconds.display(0)
                    self.doing.setText('')
                    self.warning.setText('')
                else:
                    self.seconds.display(0)
                    self.durat = 0
                    self.warning.setText('Вы не можете потратить на задачу 0 минут.')



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainPage()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
