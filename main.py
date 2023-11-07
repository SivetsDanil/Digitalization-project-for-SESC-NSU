import sqlite3
import sys

import PyQt5
from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QApplication, QMainWindow, QStatusBar, QTableWidgetItem, QTableWidget, QWidget, QCalendarWidget


class MainWindow(QMainWindow):
    def move2RightBottomCorner(self, win):
        screen_geometry = QApplication.desktop().availableGeometry()
        screen_size = (screen_geometry.width(), screen_geometry.height())
        win_size = (win.frameSize().width(), win.frameSize().height())
        x = (screen_size[0] - win_size[0]) // 2
        y = (screen_size[1] - win_size[1]) // 2
        win.move(x, y)

    def clear(self):
        self.room_number.clear()
        self.user_name.clear()
        self.statusbar.clearMessage()

    def exit(self):
        self.close()
        self.parent.show()


class StartWindow(MainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('title.ui', self)
        self.move2RightBottomCorner(self)
        self.setFixedSize(self.size())
        self.log_in_button.clicked.connect(self.log_in)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        self.user_name.setPlaceholderText("Иванов Иван")
        self.room_number.setPlaceholderText("222")

        self.clear()

        self.user_name.setText("Сивец Данил")
        self.room_number.setText("236")



    def log_in(self):
        self.block_num = self.room_number.text()
        self.user = self.user_name.text()
        if self.check_log_in():
            self.block_num = self.room_number.text()
            self.user = self.user_name.text()
            self.menu_form = MenuForm(self, (self.block_num, self.user))
            self.menu_form.show()
            self.close()

    def check_log_in(self):
        try:
            if not self.block_num.isnumeric():
                raise TypeError("Номер комнаты должен быть числом, арабскими цифрами.")
            elif not 200 < int(self.block_num) < 600:
                raise ValueError("В таком блоке не живут ученики!")
            elif self.user == '':
                raise ValueError("Вы не ввели свое имя!")
            elif self.user_not_in_base(self.user):
                raise UserWarning("Такого ученика нет в базе!")
            elif self.user_not_in_block(self.block_num, self.user):
                raise UserWarning("Вы не живете в этом блоке!")
            return True
        except Exception as e:
            self.statusBar().showMessage(e.args[0])
            return False

    def user_not_in_base(self, user):
        self.con = sqlite3.connect("sesc_base.sqlite")
        self.cur = self.con.cursor()
        result = self.cur.execute("SELECT * FROM students")
        for elem in result:
            if elem[1] == user:
                return False
        return True

    def user_not_in_block(self, block_num, user):
        self.con = sqlite3.connect("sesc_base.sqlite")
        self.cur = self.con.cursor()
        result = self.cur.execute("SELECT * FROM students")
        for elem in result:
            if elem[1] == user and elem[2] == int(block_num):
                return False
        return True


class MenuForm(MainWindow):
    def __init__(self, parent, info):
        super().__init__()
        self.parent = parent
        self.info = info
        uic.loadUi('menu.ui', self)
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)
        self.washing_button.clicked.connect(self.start_work)
        self.worker_button.clicked.connect(self.start_work)
        self.plumbing_button.clicked.connect(self.start_work)

    def initUI(self):
        self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle('Выбор записи')

    def start_work(self):
        sender = self.sender().objectName()
        self.close()
        if sender == 'washing_button':
            self.open_form = WashingList(self, self.info)
        elif sender == 'worker_button':
            self.open_form = WorkerList(self, self.info)
        elif sender == 'plumbing_button':
            self.open_form = PlumbingList(self, self.info)
        self.open_form.show()


class WorkWithBase(MainWindow):
    def create_row(self):
        if self.modified == {} and self.table.item(self.table.rowCount() - 1, 2).text() != '':
            self.cur.execute(f"insert into {self.args['table']}(Жалоба, №_блока) values('', '')")
            self.con.commit()
            self.fill_table()
        else:
            self.statusBar().showMessage("Прошлая жалоба еще не отправлена!")

    def fill_table(self):
        self.table.clear()
        self.con = sqlite3.connect("sesc_base.sqlite")
        self.modified = {}
        self.titles = None
        self.cur = self.con.cursor()
        args = self.args
        self.result = self.cur.execute(f"SELECT * FROM {args['table']} WHERE {args['id_name']} > "
                                       f"(SELECT max({args['id_name']}) - 40 FROM {args['table']})")
        self.result = self.result.fetchall()
        self.table.setRowCount(len(self.result))
        self.table.setColumnCount(len(self.result[0]))
        self.table.setVerticalHeaderLabels([''] * len(self.result))
        self.table.setHorizontalHeaderLabels(['Номер жалобы', 'Жалоба', '№_блока', 'Задача прията', 'Выполнено'])
        self.titles = [description[0] for description in self.cur.description]
        for i, elem in enumerate(self.result):
            for j, val in enumerate(elem):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        if self.result[-1][1] == '':
            self.unfreeze_row(len(self.result) - 1)
        else:
            self.unfreeze_row(-1)

    def unfreeze_row(self, a):
        rows = len(self.result)
        cols = len(self.result[0])
        for row in range(rows):
            for col in range(cols):
                item = self.table.item(row, col)
                if row != a or (col != 2 and col != 1):
                    item.setFlags(PyQt5.QtCore.Qt.ItemIsEnabled)
                self.table.setItem(row, col, item)

    def save_results(self):
        self.statusBar().clearMessage()
        try:
            if "Жалоба" not in self.modified or self.modified["Жалоба"] == '':
                raise ValueError("Вы не написали жалобу!")
            elif "№_блока" not in self.modified or self.modified["№_блока"] != str(self.block_num):
                raise ValueError("Необходимо ввести номер своего блока!")
            if self.modified:
                que = f"UPDATE {self.args['base']} SET\n"
                que += ", ".join([f"{key}='{self.modified[key]}'"
                                  for key in set(self.modified.keys()) - {"id"}])
                que += f"WHERE {self.args['id_name']} = {self.modified['id']}"
                self.cur.execute(que)
                self.con.commit()
                self.modified = {}
                self.fill_table()
                self.statusBar().showMessage("Отправлено!")
        except Exception as e:
            self.statusBar().showMessage(e.args[0])

    def item_changed(self, item):
        self.modified[self.titles[item.column()]] = item.text()
        self.modified["id"] = self.result[item.row()][0]


class WorkerList(WorkWithBase):
    def __init__(self, parent, info):
        super().__init__()
        self.parent = parent
        self.block_num = info[0]
        uic.loadUi('worker.ui', self)
        self.setWindowTitle('Тетрадь для жалоб, плотническая')
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)
        self.args = {"table": "working", "id_name": "workid"}
        self.fill_table()
        self.send_button.clicked.connect(self.save_results)
        self.table.itemChanged.connect(self.item_changed)
        self.create_button.clicked.connect(self.create_row)


class PlumbingList(WorkWithBase):
    def __init__(self, parent, info):
        super().__init__()
        self.parent = parent
        self.block_num = info[0]
        uic.loadUi('plumber.ui', self)
        self.setWindowTitle('Тетрадь для жалоб, сантехническая')
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)
        self.args = {"table": "plumbing", "id_name": "plumbid"}
        self.fill_table()
        self.send_button.clicked.connect(self.save_results)
        self.table.itemChanged.connect(self.item_changed)
        self.create_button.clicked.connect(self.create_row)


class WashingList(WorkWithBase):
    def __init__(self, parent, info):
        super().__init__()
        self.parent = parent
        self.block_num = info[0]
        uic.loadUi('washer.ui', self)
        self.setWindowTitle('Тетрадь для записей на стирку')
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)
        self.args = {"table": "washing", "id_name": "washid"}
        self.fill_table()
        self.send_button.clicked.connect(self.save_results)
        self.table.itemChanged.connect(self.item_changed)
        self.create_button.clicked.connect(self.create_row)
        self.open_calender.clicked.connect(self.open_calend)
        self.update_button.clicked.connect(self.date_update)

    def open_calend(self):
        self.calend = Calender(self)
        self.calend.show()

    def date_back(self, date):
        self.date = date
        self.wash_date.setDate(QDate(*self.date))

    def date_update(self):
        pass


class Calender(QWidget):
    def __init__(self, parent):
        super().__init__()
        uic.loadUi('calender.ui', self)
        self.parent = parent
        self.setWindowTitle('Выберите дату')
        self.set_date_button.clicked.connect(self.func)

    def func(self):
        self.date = self.calender.selectedDate().getDate()
        self.parent.date_back(self.date)
        self.close()



def exept(a, b, c):
    print(a, b, c)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StartWindow()
    ex.show()
    sys.excepthook = exept
    sys.exit(app.exec_())
