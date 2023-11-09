import sqlite3
import sys

import PyQt5
from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QApplication, QMainWindow, QStatusBar, QTableWidgetItem, QTableWidget, QWidget, QDateEdit, \
    QTimeEdit


class MainWindow(QMainWindow):
    con = sqlite3.connect("sesc_base.sqlite")
    cur = con.cursor()
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
        self.staff_log_in_button.clicked.connect(self.staff_log_in)
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
        result = self.cur.execute("SELECT * FROM students")
        for elem in result:
            if elem[1] == user:
                return False
        return True

    def user_not_in_block(self, block_num, user):
        result = self.cur.execute("SELECT * FROM students")
        for elem in result:
            if elem[1] == user and elem[2] == int(block_num):
                return False
        return True

    def staff_log_in(self):
        self.open_form = StaffTitle(self)
        self.close()
        self.open_form.show()


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
        self.modified = {}
        self.titles = None
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
        self.statusBar().clearMessage()

    def unfreeze_row(self, num, exep=[1, 2]):
        rows = len(self.result)
        cols = len(self.result[0])
        for row in range(rows):
            for col in range(cols):
                item = self.table.item(row, col)
                if row != num or (col not in exep):
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
                que = f"UPDATE {self.args['table']} SET\n"
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
        uic.loadUi('work_table.ui', self)
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
        uic.loadUi('plumb_table.ui', self)
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
        self.user_name = info[1]
        uic.loadUi('wash_table.ui', self)
        self.row_created = False
        self.setWindowTitle('Тетрадь для записей на стирку')
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)
        self.args = {"table": "washing", "id_name": "washid"}
        self.fill_table()
        self.update_button.clicked.connect(self.save_results)
        self.table.itemChanged.connect(self.item_changed)
        self.create_button.clicked.connect(self.create_row)
        self.open_calender.clicked.connect(self.open_calend)
        self.unfreeze_row(-1, [])
        self.wash_date.dateChanged.connect(self.fill_table)
        self.mashin_num.textChanged.connect(self.fill_table)
        self.row_id = -1


    def open_calend(self):
        self.calend = Calender(self)
        self.calend.show()

    def date_back(self, date):
        self.date = date
        self.wash_date.setDate(QDate(*self.date))

    def create_row(self):
        if not self.row_created and self.time_is_free():
            self.row_created = True
            print(3)
            self.cur.execute(
                f"insert into washing(ФИ, №_стиралки, День, Время) "
                f"values('{'_'.join(self.user_name.split())}', '{self.mashin_num.text()}', "
                f"'{self.wash_date.text()}', '{self.time.text()}')")
            self.con.commit()
            self.fill_table()
            self.row_id = self.cur.execute(f"select washid from washing where "
                                           f"ФИ='{'_'.join(self.user_name.split())}' and"
                                           f" №_стиралки='{self.mashin_num.text()}' and "
                                           f"День='{self.wash_date.text()}' and "
                                           f"Время='{self.time.text()}'").fetchall()[0][0]
        elif not self.time_is_free():
            self.statusBar().showMessage("Это время уже занято!")
        else:
            self.statusBar().showMessage("По одной записи в день!")

    def save_results(self):
        try:
            if self.row_created and self.time_is_free() and self.time.text().split(":")[1] == '00':
                self.modified = {'ФИ': '_'.join(self.user_name.split()), '№_стиралки': self.mashin_num.text(),
                                 'День': self.wash_date.text(), 'Время': self.time.text()}
                que = "UPDATE washing SET\n"
                que += ", ".join([f"{key}='{self.modified.get(key)}'"
                                  for key in self.modified.keys()])
                que += f"WHERE washid = {self.row_id}"
                self.cur.execute(que)
                self.con.commit()
                self.modified.clear()
                self.fill_table()
            elif not self.row_created:
                self.statusBar().showMessage("Сперва создайте запись!")
            elif not self.time_is_free():
                self.statusBar().showMessage("Это время занято!")
            elif self.time.text().split(":")[1] != '00':
                self.statusBar().showMessage("Необходимо выбрать время без минут!")
        except Exception:
            self.statusBar().showMessage("Сперва создайте запись!")

    def time_is_free(self):
        result = self.cur.execute(f"SELECT * FROM washing WHERE №_стиралки='{self.mashin_num.text()}'")
        for elem in result:
            if elem[3] == self.time.text():
                return False
        return True

    def fill_table(self):

        self.table.clear()
        self.modified = {}
        self.titles = None
        date = self.wash_date.text()
        num = self.mashin_num.text()
        self.result = self.cur.execute(f"SELECT * FROM washing WHERE №_стиралки='{num}' and День='{date}'")
        self.result = self.result.fetchall()
        if not self.row_created:
            self.result.sort(key=lambda x: int(x[3].split(":")[0]))
        if not self.result:
            self.result = tuple([['-' for _ in range(5)]])
        self.table.setRowCount(len(self.result))
        self.table.setColumnCount(len(self.result[0]))
        self.table.setVerticalHeaderLabels([''] * len(self.result))
        res = self.result
        self.result = []
        for elem in res:
            self.result.append((elem[1], elem[3], elem[4], elem[2], elem[0]))
        self.table.setHorizontalHeaderLabels(['№_Стиралки', 'Время', 'ФИ', "Дата", '№_Стирки'])
        self.titles = [description[0] for description in self.cur.description]
        for i, elem in enumerate(self.result):
            for j, val in enumerate(elem):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        if self.result[-1][1] == '':
            self.unfreeze_row(len(self.result) - 1)
        else:
            self.unfreeze_row(-1)
        self.statusBar().clearMessage()


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


class StaffTitle(MainWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        uic.loadUi('staff_title.ui', self)
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.log_in_button.clicked.connect(self.log_in)
        self.exit_button.clicked.connect(self.exit)

        self.staff_name.setText("admin")
        self.pass_line.setText("admin")

    def log_in(self):
        self.user_name = self.staff_name.text()
        self.password = self.pass_line.text()
        self.statusBar().clearMessage()
        if self.check_log_in():
            self.post = self.get_post()
            if self.post == 'admin':
                self.open_form = AdminSpace(self)
            elif self.post == 'plumber':
                self.open_form = PlumberSpace(self)
            elif self.post == 'worker':
                self.open_form = WorkerSpace(self)
            else:
                self.statusBar().showMessage("Ваша должность некорректна, обратитесь к админестратору")
            self.open_form.show()
            self.close()

    def check_log_in(self):
        self.statusBar().clearMessage()
        try:
            if self.user_name == '':
                raise ValueError("Вы не ввели свое ФИО")
            elif self.emp_not_in_base():
                raise UserWarning("Такого ФИО нет в базе")
            elif not self.check_pass():
                raise UserWarning("Неверный пароль")
            return True
        except Exception as e:
            self.statusBar().showMessage(e.args[0])
            return False

    def emp_not_in_base(self):
        result = self.cur.execute(f"SELECT name FROM employers WHERE name='{self.user_name}'").fetchall()
        if result:
            return False
        return True

    def check_pass(self):
        result = self.cur.execute(f"SELECT password FROM employers WHERE name='{self.user_name}'").fetchall()
        if result[0][0] == self.password:
            return True
        return False

    def get_post(self):
        return self.cur.execute(f"SELECT post FROM employers WHERE name='{self.user_name}'").fetchall()[0][0]


class AdminSpace(WorkWithBase):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        uic.loadUi('admin.ui', self)
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)


class PlumberSpace(WorkWithBase):
    pass


class WorkerSpace(WorkWithBase):
    pass




def exept(a, b, c):
    print(a, b, c)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StartWindow()
    ex.show()
    sys.excepthook = exept
    sys.exit(app.exec_())
