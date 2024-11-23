import sys
import sqlite3
import time

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox, QLabel
from PyQt6 import uic
from datetime import datetime, timedelta
from threading import Thread
from PyQt6.QtGui import QPixmap

MINUTA = 'минута'
HOUR = 'час'

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def back_to_main(prev_page): #Во всех окнах нужна функция для возврата, поэтому, чтобы не дублировать код она
    prev_page.close()        #Вынесена в отдельную глобвльную функцию.
    ap = MainPage()
    ap.show()


def get_previous(entity, limit):    # Функция для получения последних вводимых значений
    previous = cur.execute("""SELECT name FROM doings ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    entity.previous.setText('\n'.join([prev[0] for prev in previous]))


def do_dict(arr):  # принимает список кортежей вида (время, название)
    res = {}       # и создаёт словарь с сумой времени для каждой задачи
    for el in arr:
        if el[1] in res:
            res[el[1]] += el[0]
        else:
            res[el[1]] = el[0]
    return res


def clean_db(): # Очищает БД от данных которые больше не будут доступны (прошлая неделя и раньше)
    cur.execute("""DELETE FROM timecheck WHERE startdate < ?""",
                (str(datetime.now() - timedelta(days=datetime.now().weekday())).split()[0],))
    connection.commit()


def mylower(line):
    return line.lower()


connection = sqlite3.connect("CheckTimeDB.sqlite")
cur = connection.cursor()
connection.create_function('MYLOWER', 1, mylower) # У sqlite есть проблемы с функцией LOWER для кириллицы,
                                                             # создала свою функцию


class OverSignal(QObject): # Мой сигнал посылаемый, если секундомер запущен более 23 часов 59 минут
    overS = pyqtSignal()


class DayOverSignal(QObject): # Мой сигнал, посылаемый при завершении суток.
    dayOverS = pyqtSignal()

class NoWrittenName(Exception):
    pass

class DurLessMin(Exception):
    pass

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
        self.setvalues()
        self.back.clicked.connect(self.back_fun)
        self.export_day_btn.clicked.connect(self.export_day)
        self.export_week_btn.clicked.connect(self.export_week)
        clean_db()

    def back_fun(self):
        back_to_main(self)

    def export_day(self):
        f = open(f"DayStatistic{str(datetime.now()).split()[0]}.txt", mode="w", encoding="utf-8")
        f.write(self.for_day_text)
        self.status.setText("Успешно экспортировано в директорию с программой!")
        f.close()

    def export_week(self):
        f = open(f"WeekStatistic{str(datetime.now()).split()[0]}.txt", mode="w", encoding="utf-8")
        f.write(self.for_week_text)
        self.status.setText("Успешно экспортировано в директорию с программой!")
        f.close()


    def setvalues(self):
        for_day = cur.execute("""SELECT timecheck.duration, doings.name FROM 
            timecheck JOIN doings ON doings.id = doingid WHERE startdate = ?""",
                              (str(datetime.now()).split()[0],)).fetchall()
        for_week = cur.execute("""SELECT timecheck.duration, doings.name FROM 
            timecheck JOIN doings ON doings.id = doingid WHERE startdate >= ?""",
                               (str(datetime.now() -
                                    timedelta(days=datetime.now().weekday())).split()[0], )).fetchall()
        if for_day:
            self.day.setText('За день:')
            for_day = do_dict(for_day)
            self.for_day_text = '\n'.join([name + '\t' + str(for_day[name]) for name in for_day])
            self.day_stat.setText(self.for_day_text)
        if for_week:
            self.week.setText('За неделю:')
            for_week = do_dict(for_week)
            self.for_week_text = '\n'.join([name + '\t' + str(for_week[name]) for name in for_week])
            self.week_stat.setText(self.for_week_text)


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
        try:
            if self.name.text() == '' or self.timeEdit.text() == '0:00':
                raise NoWrittenName
            maybe_id = cur.execute("""SELECT id FROM doings WHERE MYLOWER(name) LIKE ? LIMIT 1""",
                                   (self.name.text().lower(),)).fetchall()
            if not maybe_id:
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
        except NoWrittenName:
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

    def timerview(self):
        while True:
            if self.start:
                break
            if self.durat == 23 * 3600 + 59 * 60 + 60:
                self.over.overS.emit()
                break
            if datetime.now().hour == 23 and datetime.now().minute == 59:
                self.dayover.dayOverS.emit()
            self.hours.display(self.durat // 3600)
            self.minuts.display(self.durat % 3600 // 60)
            self.seconds.display(self.durat % 3600 % 60)
            self.durat += 1
            time.sleep(1)

    def day_is_over(self):
        print('qqq')
        self.intents = {'doing_id': -1, 'duration': [], 'date': []}
        if self.durat >= 60:
            maybe_id = cur.execute("""SELECT id FROM doings WHERE MYLOWER(name) = ? LIMIT 1""",
                                   (self.doing.text().lower(),)).fetchall()
            if not maybe_id:
                cur.execute("""INSERT INTO doings (name) VALUES (?)""", (self.doing.text(),))
                self.intents['doing_id'] = cur.lastrowid
            else:
                self.intents['doing_id'] = maybe_id[0][0]
            self.intents['duration'].append(self.durat)
            self.intents['date'].append(str(datetime.now()).split()[0])
            self.day_was_over = True

    def lingv_logic(self, num, target_word):
        if target_word == MINUTA:
            if 5 <= num <= 20 or 5 <= num % 10 <= 9 or num == 0:
                return 'минут'
            if num % 10 == 1:
                return 'минуту'
            return 'минуты'
        elif target_word == HOUR:
            if 5 <= num <= 20 or 5 <= num % 10 <= 9 or num == 0:
                return 'часов'
            if num % 10 == 1:
                return 'час'
            return 'часа'

    def btnclicked(self):
        if self.start:
            try:
                if str(self.doing.text()) == '':
                    raise NoWrittenName
                self.doing.setReadOnly(True)
                self.startstopbtn.setText('СТОП')
                self.warning.setText('Отсчёт времени пошёл!')
                self.date = str(datetime.now()).split()[0]
                self.durat = 0
                self.start = False
                t1 = Thread(target=self.timerview)
                t1.start()
            except NoWrittenName:
                self.warning.setText('Введите название!')
        else:
            if self.day_was_over:
                try:
                    if self.durat < 60:
                        raise DurLessMin
                    self.start = True
                    self.startstopbtn.setText('СТАРТ')
                    self.doing.setReadOnly(False)
                    print(self.intents['duration'][0])
                    print()
                    self.intents['duration'].append(self.durat - self.intents['duration'][0])
                    self.intents['date'].append(str(datetime.now()).split()[0])
                    question = QMessageBox.question(self, 'Добавление записи',
                                                    f"{self.intents['date'][0]} Вы потратили на зaдачу "
                                                    f"'{self.doing.text()}' {self.intents['duration'][0] // 3600} "
                                                    f"{self.lingv_logic(self.intents['duration'][0] // 3600, HOUR)} "
                                                    f"и {self.intents['duration'][0] % 3600 // 60} "
                                                    f"{self.lingv_logic(self.intents['duration'][0] % 3600 // 60, MINUTA)}, "
                                                    f"\nа {self.intents['date'][1]} {self.intents['duration'][1] // 3600} "
                                                    f"{self.lingv_logic(self.intents['duration'][1] // 3600, HOUR)}"
                                                    f" и {self.intents['duration'][1] % 3600 // 60} "
                                                    f"{self.lingv_logic(self.intents['duration'][1] % 3600 // 60, MINUTA)}. "
                                                    f"\nДобавить запись об этом действии?",
                                                    QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if question == QMessageBox.StandardButton.Yes:
                        cur.execute("""INSERT INTO timecheck (doingid, startdate, duration) 
                                                        VALUES (?, ?, ?)""", (
                            self.intents['doing_id'], self.intents['date'][0], self.intents['duration'][0] // 60))
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
                except DurLessMin:
                    self.start = True
                    self.startstopbtn.setText('СТАРТ')
                    self.seconds.display(0)
                    self.warning.setText('Вы не можете потратить на задачу 0 минут.')
                    self.durat = 0
            else:
                self.start = True
                self.startstopbtn.setText('СТАРТ')
                self.doing.setReadOnly(False)
                try:
                    if self.durat < 60:
                        raise DurLessMin
                    intent = QMessageBox.question(self, 'Добавление записи',
                                                  f"Вы потратили на зaдачу '{self.doing.text()}' "
                                                  f"{self.durat // 3600} {self.lingv_logic(self.durat // 3600, HOUR)} "
                                                  f"и {self.durat % 3600 // 60} "
                                                  f"{self.lingv_logic(self.durat % 3600 // 60, MINUTA)}. Добавить запись"
                                                  f" об этом действии?",
                                                  QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
                    if intent == QMessageBox.StandardButton.Yes:
                        maybe_id = cur.execute("""SELECT id FROM doings WHERE MYLOWER(name) = ? LIMIT 1""",
                                               (self.doing.text().lower(),)).fetchall()
                        if not maybe_id:
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
                except DurLessMin:
                    self.start = True
                    self.startstopbtn.setText('СТАРТ')
                    self.seconds.display(0)
                    self.durat = 0
                    self.warning.setText('Вы не можете потратить на задачу 0 минут.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainPage()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
