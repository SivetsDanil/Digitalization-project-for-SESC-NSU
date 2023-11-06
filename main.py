import sys
import sqlite3

import PyQt5
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStatusBar, QTableWidgetItem, QTableView, QTableWidget


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
        self.user_name.setPlaceholderText("Иванов Иван Иванович")
        self.room_number.setPlaceholderText("222")
        self.clear()

    def log_in(self):
        self.block_num = self.room_number.text()
        self.user = self.user_name.text()
        if self.check_log_in():
            self.block_num = self.room_number.text()
            self.user = self.user_name.text()
            self.menu_form = MenuForm(self)
            self.menu_form.show()
            self.close()

    def check_log_in(self):
        try:
            if not self.block_num.isnumeric():
                raise TypeError("Номер комнаты должен быть числом, арабскими цифрами.")
            elif not 200 < int(self.block_num) < 600:
                raise ValueError("В таком блоке не живут ученики!")
            elif self.user_not_in_base(self.user):
                raise UserWarning("Такого ученика нет в базе")
            return True
        except Exception as e:
            self.statusBar().showMessage(e.args[0])
            return False

    def user_not_in_base(self, user):
        return False


class MenuForm(MainWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
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
            self.open_form = WashingList(self)
        elif sender == 'worker_button':
            self.open_form = WorkerList(self)
        elif sender == 'plumbing_button':
            self.open_form = PlumbingList(self)
        self.open_form.show()


class WorkerList(MainWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        uic.loadUi('worker.ui', self)
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)

    def initUI(self):
        self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle('Выбор записи')


class PlumbingList(MainWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        uic.loadUi('plumber.ui', self)
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)
        self.fill_table()
        self.send_button.clicked.connect(self.save_results)
        self.table.itemChanged.connect(self.item_changed)
        self.create_button.clicked.connect(self.create_row)

    def fill_table(self):
        self.table.clear()
        self.con = sqlite3.connect("sesc_base.sqlite")
        self.modified = {}
        self.titles = None
        self.cur = self.con.cursor()
        self.result = self.cur.execute("SELECT * FROM plumbing WHERE plumbid > (SELECT max(plumbid) - 100 "
                                  "FROM plumbing)").fetchall()
        self.table.setRowCount(len(self.result))
        self.table.setColumnCount(len(self.result[0]))
        self.table.setVerticalHeaderLabels([''] * len(self.result))
        self.table.setHorizontalHeaderLabels(['Номер жалобы', 'Жалоба', '№_блока', 'Задача прията', 'Выполнено'])
        self.titles = [description[0] for description in self.cur.description]
        for i, elem in enumerate(self.result):
            for j, val in enumerate(elem):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        if self.result[-1][1] == '':
            self.unfreeze(len(self.result) - 1)
        else:
            self.unfreeze(-1)
    def unfreeze(self, a):
        rows = len(self.result)
        cols = len(self.result[0])
        for row in range(rows):
            for col in range(cols):
                item = self.table.item(row, col)
                if row != a or (col != 2 and col != 1):
                    item.setFlags(PyQt5.QtCore.Qt.ItemIsEnabled)
                self.table.setItem(row, col, item)

    def save_results(self):
        if self.modified:
            que = "UPDATE plumbing SET\n"
            que += ", ".join([f"{key}='{self.modified[key]}'"
                              for key in set(self.modified.keys()) - {"id"}])
            que += f"WHERE plumbid = {self.modified['id']}"
            self.cur.execute(que)
            self.con.commit()
            self.modified.clear()
            self.fill_table()

    def item_changed(self, item):
        self.modified[self.titles[item.column()]] = item.text()
        self.modified["id"] = self.result[item.row()][0]

    def create_row(self):
        self.cur.execute("insert into plumbing(Жалоба, №_блока) values('', '')")
        self.con.commit()
        self.fill_table()

    def initUI(self):
        self.setWindowTitle('Тетрадь для жалоб')


class WashingList(StartWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        uic.loadUi('worker.ui', self)
        self.setFixedSize(self.size())
        self.move2RightBottomCorner(self)
        self.exit_button.clicked.connect(self.exit)

    def initUI(self):
        self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle('Выбор записи')


def exept(a, b, c):
    print(a, b, c)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PlumbingList(StartWindow())
    ex.show()
    sys.excepthook = exept
    sys.exit(app.exec_())