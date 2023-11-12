import sqlite3
import sys

import PyQt5
from PyQt5 import uic, QtGui
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QStatusBar, QTableWidgetItem, QWidget
from PyQt5.QtGui import QPixmap, QImage


class MainWindow(QMainWindow):
    con = sqlite3.connect("sesc_base.sqlite")
    cur = con.cursor()
    image = QImage('front/logo.png')


    def moveCenter(self, win):
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
        uic.loadUi('front/title.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
        self.moveCenter(self)
        self.setFixedSize(self.size())
        self.log_in_button.clicked.connect(self.log_in)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        self.user_name.setPlaceholderText("Иванов Иван")
        self.room_number.setPlaceholderText("222")
        self.staff_log_in_button.clicked.connect(self.staff_log_in)
        self.clear()
        self.room_number.returnPressed.connect(self.log_in)
        self.user_name.returnPressed.connect(self.log_in)

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
        uic.loadUi('front/menu.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
        self.setFixedSize(self.size())
        self.moveCenter(self)
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
        if self.row_sent and not self.row_created and self.table.item(self.table.rowCount() - 1, 1).text() != '':
            self.row_created = True
            self.row_sent = False
            self.modified = {}
            self.cur.execute(f"insert into {self.args['table']}(report, block_num) values('', '')")
            self.con.commit()
            self.fill_table()
            self.row_id = self.cur.execute(f"select {self.args['id_name']} from {self.args['table']} where "
                                           f"report='' and block_num=''").fetchall()[0][0]
        elif not self.row_sent or self.table.item(self.table.rowCount() - 1, 1) != '':
            self.statusBar().showMessage("Прошлая жалоба еще не отправлена!")
        elif self.row_created:
            self.statusBar().showMessage("По одной записи в день!")

    def fill_table(self, head=None):
        if head is None:
            header = ['Номер жалобы', 'Жалоба', 'Номер блока', 'Статус', 'Выполнено']
        else:
            header = head
        self.table.clear()
        self.modified = {}
        self.titles = None
        self.result = self.cur.execute(f"SELECT * FROM {self.args['table']} WHERE {self.args['id_name']} > "
                                       f"(SELECT max({self.args['id_name']}) - 40 FROM {self.args['table']})")
        self.result = self.result.fetchall()
        self.table.setRowCount(len(self.result))
        self.table.setColumnCount(len(self.result[0]))
        self.table.setVerticalHeaderLabels([''] * len(self.result))
        self.table.setHorizontalHeaderLabels(header)
        self.titles = [description[0] for description in self.cur.description]
        for i, elem in enumerate(self.result):
            for j, val in enumerate(elem):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        if self.result[-1][1] == '':
            self.freeze_row(len(self.result) - 1)
        else:
            self.freeze_row(-1)
        self.statusBar().clearMessage()

    def freeze_row(self, num, exep=None):
        if exep is None:
            exep = [1, 2]
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        for row in range(rows):
            for col in range(cols):
                item = self.table.item(row, col)
                if row != num or (col not in exep):
                    item.setFlags(PyQt5.QtCore.Qt.ItemIsEnabled)
                self.table.setItem(row, col, item)

    def unfreeze_table(self, exep=None):
        if exep is None:
            exep = []
        rows = self.table.rowCount()
        cols = self.table.columnCount()
        for row in range(rows):
            for col in range(cols):
                if col not in exep:
                    item = self.table.item(row, col)
                    item.setFlags(PyQt5.QtCore.Qt.ItemIsEditable | PyQt5.QtCore.Qt.ItemIsSelectable
                                  | PyQt5.QtCore.Qt.ItemIsEnabled)
                    self.table.setItem(row, col, item)

    def save_results(self):
        self.statusBar().clearMessage()
        try:
            if "report" not in self.modified or self.modified["report"] == '':
                raise ValueError("Вы не написали жалобу!")
            elif "block_num" not in self.modified or self.modified["block_num"] != str(self.block_num):
                raise ValueError("Необходимо ввести номер своего блока!")
            elif self.modified:
                que = f"UPDATE {self.args['table']} SET\n"
                que += ", ".join([f"{key}='{self.modified[key]}'"
                                  for key in set(self.modified.keys()) - {"id"}])
                que += f"WHERE {self.args['id_name']} = {self.modified['id']}"
                self.cur.execute(que)
                self.con.commit()
                self.modified = {}
                self.row_sent = True
                self.fill_table()
                self.statusBar().showMessage("Отправлено!")
        except Exception as e:
            self.statusBar().showMessage(e.args[0])

    def item_changed(self, item):
        try:
            if self.row_created and item.row() == self.table.rowCount() - 1:
                self.modified["id"] = self.row_id
                self.modified[self.titles[item.column()]] = item.text()
        except Exception:
            pass


class WorkerList(WorkWithBase):
    def __init__(self, parent, info):
        super().__init__()
        self.parent = parent
        self.row_sent = True
        self.row_created = False
        self.block_num = info[0]
        uic.loadUi('front/work_table.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
        self.logo_label.setPixmap(QPixmap(self.image))
        self.setWindowTitle('Тетрадь для жалоб, плотническая')
        self.setFixedSize(self.size())
        self.moveCenter(self)
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
        uic.loadUi('front/plumb_table.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
        self.setWindowTitle('Тетрадь для жалоб, сантехническая')
        self.setFixedSize(self.size())
        self.moveCenter(self)
        self.logo_label.setPixmap(QPixmap(self.image))
        self.exit_button.clicked.connect(self.exit)
        self.args = {"table": "plumbing", "id_name": "plumbid"}

        self.row_sent = True
        self.row_created = False

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
        uic.loadUi('front/wash_table.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
        self.row_created = False
        self.row_sent = True
        self.setWindowTitle('Тетрадь для записей на стирку')
        self.setFixedSize(self.size())
        self.moveCenter(self)
        self.exit_button.clicked.connect(self.exit)
        self.args = {"table": "washing", "id_name": "washid"}
        self.fill_table()
        self.update_button.clicked.connect(self.save_results)
        self.table.itemChanged.connect(self.item_changed)
        self.create_button.clicked.connect(self.create_row)
        self.open_calender.clicked.connect(self.open_calend)
        self.freeze_row(-1, [])
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
        if self.time_is_free() and self.time.text().split(":")[1] == '00':
            self.row_created = True
            self.cur.execute(
                f"insert into washing(name, wash_num, day, time) "
                f"values('{self.user_name}', '{self.mashin_num.text()}', "
                f"'{self.wash_date.text()}', '{self.time.text()}')")
            self.con.commit()
            self.fill_table()
            self.row_id = self.cur.execute(f"select washid from washing where "
                                           f"name='{self.user_name}' and"
                                           f" wash_num='{self.mashin_num.text()}' and "
                                           f"day='{self.wash_date.text()}' and "
                                           f"time='{self.time.text()}'").fetchall()[0][0]
        elif not self.time_is_free():
            self.statusBar().showMessage("Это время уже занято!")
        elif self.time.text().split(":")[1] != '00':
            self.statusBar().showMessage("Необходимо выбрать время без минут!")

    def save_results(self):
        try:
            if self.row_created and self.time_is_free() and self.time.text().split(":")[1] == '00':
                self.modified = {'name': '_'.join(self.user_name.split()), 'wash_num': self.mashin_num.text(),
                                 'day': self.wash_date.text(), 'time': self.time.text()}
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
        result = self.cur.execute(f"SELECT * FROM washing WHERE wash_num='{self.mashin_num.text()}'")
        for elem in result:
            if elem[3] == self.time.text():
                return False
        return True

    def fill_table(self, **kwargs):
        self.table.clear()
        self.modified = {}
        self.titles = None
        date = self.wash_date.text()
        num = self.mashin_num.text()
        self.result = self.cur.execute(f"SELECT * FROM washing WHERE wash_num='{num}' and day='{date}'")
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
            self.freeze_row(len(self.result) - 1)
        else:
            self.freeze_row(-1)
        self.statusBar().clearMessage()


class Calender(QWidget):
    def __init__(self, parent):
        super().__init__()
        uic.loadUi('front/calender.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
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
        uic.loadUi('front/staff_title.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
        self.setWindowTitle('Вход для сотрудников')
        self.setFixedSize(self.size())
        self.moveCenter(self)
        self.log_in_button.clicked.connect(self.log_in)
        self.exit_button.clicked.connect(self.exit)
        self.pass_line.returnPressed.connect(self.log_in)
        self.staff_name.returnPressed.connect(self.log_in)

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
                return
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
        self.modified = {}
        self.changes = []
        self.row_sent = True
        self.row_created = False
        self.selected = False
        self.initUI()

    def initUI(self):
        uic.loadUi('front/admin.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
        self.setWindowTitle('Рабочее место администратора')
        self.setFixedSize(self.size())
        self.moveCenter(self)
        self.exit_button.clicked.connect(self.exit)
        self.table_line.addItems(["students", "employers", "washing", "working", "plumbing"])
        self.table_line.setCurrentText("students")
        self.table_changed()
        self.admin_fill_table()
        self.table_line.currentTextChanged.connect(self.table_changed)
        self.save_button.clicked.connect(self.save_results)
        self.table.itemChanged.connect(self.item_changed)
        self.table.itemSelectionChanged.connect(self.item_selected)
        self.create_button.clicked.connect(self.create_row)
        self.delete_button.clicked.connect(self.delete_row)
        self.update_button.clicked.connect(self.admin_fill_table)
        self.selected_table = self.table_line.currentText()

    def table_changed(self):
        self.selected_table = self.table_line.currentText()
        if self.selected_table == "students":
            self.args = {"table": "students", "id_name": "id"}
            self.columns = ['Номер ученика', 'ФИ', "Номер блока"]
            self.keys = {'Номер ученика': 'id', 'ФИ': 'studentName', "Номер блока": 'studentBlock'}
        elif self.selected_table == "employers":
            self.args = {"table": "employers", "id_name": "emp_id"}
            self.columns = ['Номер сотрудника', 'ФИО', "Должность", "Пароль"]
            self.keys = {'Номер сотрудника': 'emp_id', 'ФИО': 'name', "Должность": 'post', "Пароль": 'password'}
        elif self.selected_table == "washing":
            self.args = {"table": "washing", "id_name": "washid"}
            self.columns = ['№_Стирки', '№_Стиралки', 'Дата', "Время", 'ФИ']
            self.keys = {'№_Стиралки': 'wash_num', 'Время': 'time', 'ФИ': 'name', "Дата": 'date', '№_Стирки': 'washid'}
        elif self.selected_table == "working":
            self.args = {"table": "working", "id_name": "workid"}
            self.columns = ['Номер жалобы', 'Жалоба', 'Номер блока', 'Статус', 'Выполнено']
            self.keys = {'Номер жалобы': 'workid', 'Жалоба': 'report', 'Номер блока': 'block_num',
                         'Статус': 'status', 'Выполнено': 'completed'}
        elif self.selected_table == "plumbing":
            self.args = {"table": "plumbing", "id_name": "plumbid"}
            self.columns = ['Номер жалобы', 'Жалоба', 'Номер блока', 'Статус', 'Выполнено']
            self.keys = {'Номер жалобы': 'plumbid', 'Жалоба': 'report', 'Номер блока': 'block_num',
                         'Статус': 'status', 'Выполнено': 'completed'}
        self.admin_fill_table()

    def delete_row(self):
        que = f"DELETE from {self.selected_table}"
        que += f" WHERE {self.args['id_name']} = {self.selected_id}"
        self.cur.execute(que)
        self.con.commit()
        self.admin_fill_table()
        self.statusBar().showMessage("Готово")
        self.changes.clear()

    def admin_fill_table(self):
        self.fill_table(self.columns)
        self.unfreeze_table()

    def item_selected(self):
        try:
            self.selected = True
            self.select = self.table.selectedItems()[0]
            self.selected_key = self.table.horizontalHeaderItem(self.select.column()).text()
            self.selected_id = self.table.item(self.select.row(), 0).text()
            self.table.itemChanged.connect(self.item_changed)
        except IndexError:
            pass

    def item_changed(self, item):
        try:
            if item.text() == self.select.text():
                self.changes.append((self.select, self.selected_key, self.selected_id))
        except Exception:
            pass

    def create_row(self):
        request = ''
        if self.selected_table == "students":
            request = "insert into students(studentName, studentBlock) values('', '')"
        elif self.selected_table == "employers":
            request = "insert into employers(name, post, password) values('', '', '')"
        elif self.selected_table == "washing":
            request = "insert into washing(name, wash_num, day, time) values('', '', '', '')"
        elif self.selected_table == "working":
            request = "insert into working(report, block_num) values('', '')"
        elif self.selected_table == "plumbing":
            request = "insert into plumbing(report, block_num) values('', '')"
        if request != '':
            self.con.execute(request)
            self.con.commit()
            self.admin_fill_table()
        else:
            self.row_id = self.cur.execute(f"select {self.args['id_name']} from {self.args['table']} where "
                                           f"report='' and block_num=''").fetchall()[0][0]
            self.modified["id"] = self.row_id

    def save_results(self):
        for elem in self.changes:
            que = f"UPDATE {self.selected_table} SET {self.keys[elem[1]]}='{elem[0].text()}'"
            que += f"WHERE {self.args['id_name']} = {elem[2]}"
            self.cur.execute(que)
            self.con.commit()
        self.admin_fill_table()
        self.statusBar().showMessage("Готово")
        self.changes.clear()


class PlumberSpace(AdminSpace):
    def __init__(self, parent):
        super().__init__(None)
        self.parent = parent

    def initUI(self):
        uic.loadUi('front/plumber.ui', self)
        self.setWindowIcon(QtGui.QIcon('front/icon.png'))
        self.setWindowTitle('Рабочее место сантехника')
        self.args = {"table": "plumbing", "id_name": "plumbid"}
        self.columns = ['Номер жалобы', 'Жалоба', 'Номер блока', 'Статус', 'Выполнено']
        self.keys = {'Номер жалобы': 'plumbid', 'Жалоба': 'report', 'Номер блока': 'block_num',
                     'Статус': 'status', 'Выполнено': 'completed'}
        self.selected_table = "plumbing"
        self.setFixedSize(self.size())
        self.moveCenter(self)
        self.exit_button.clicked.connect(self.exit)
        self.plumber_fill_table()
        self.table.itemChanged.connect(self.item_changed)
        self.update_button.clicked.connect(self.plumber_fill_table)
        self.save_button.clicked.connect(self.save_results)
        self.table.itemSelectionChanged.connect(self.item_selected)

    def plumber_fill_table(self):
        self.fill_table(self.columns)
        self.unfreeze_table([0, 1, 2])


class WorkerSpace(AdminSpace):
    def __init__(self, parent):
        super().__init__(None)
        self.parent = parent

    def initUI(self):
        try:
            uic.loadUi('front/worker.ui', self)
            self.setWindowIcon(QtGui.QIcon('front/icon.png'))
            self.setWindowTitle('Рабочее место сантехника')
            self.args = {"table": "working", "id_name": "workid"}
            self.columns = ['Номер жалобы', 'Жалоба', 'Номер блока', 'Статус', 'Выполнено']
            self.keys = {'Номер жалобы': 'workid', 'Жалоба': 'report', 'Номер блока': 'block_num',
                         'Статус': 'status', 'Выполнено': 'completed'}
            self.selected_table = "working"
            self.setFixedSize(self.size())
            self.moveCenter(self)
            self.exit_button.clicked.connect(self.exit)
            self.plumber_fill_table()
            self.table.itemChanged.connect(self.item_changed)
            self.update_button.clicked.connect(self.plumber_fill_table)
            self.save_button.clicked.connect(self.save_results)
            self.table.itemSelectionChanged.connect(self.item_selected)
        except Exception as e:
            print(e)
    def plumber_fill_table(self):
        self.fill_table(self.columns)
        self.unfreeze_table([0, 1, 2])


def exept(a, b, c):
    print(a, b, c)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StartWindow()
    ex.show()
    sys.exit(app.exec_())
