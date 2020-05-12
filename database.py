import sys
from mainwindow import Ui_MainWindow
from editor import Ui_additionTool
from deletedialog import Ui_deleteDialog
from addition import Ui_additionWindow
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtWidgets import QTableWidgetItem, QPushButton
import random
from pony.orm import *

db = Database()


class Product(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Optional(str)
    description = Optional(str)
    specifications = Set('Specification')
    manufacturer = Optional('Manufacturer')
    category = Optional('Category')


class Specification(db.Entity):
    id = PrimaryKey(int, auto=True)
    product = Required(Product)
    name = Required(str)
    value = Optional(str)
    description = Optional(str)


class Manufacturer(db.Entity):
    id = PrimaryKey(int, auto=True)
    products = Set(Product)
    name = Required(str)
    description = Optional(str)


class Category(db.Entity):
    id = PrimaryKey(int, auto=True)
    products = Set(Product)
    name = Optional(str)
    description = Optional(str)


class databaseWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        super().setupUi(self)
        self.currentedit = ''
        self.setupUi(self)
        self.editor = 0
        self.adder = 0
        self.buttons = []

    def setupUi(self, databaseWindow):
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)

        self.categoryBox.activated.connect(self.run)
        self.manufacturerBox.activated.connect(self.run)

        self.showButton.clicked.connect(self.run)

        self.actionOpen.triggered.connect(self.openFile)
        self.actionSave.triggered.connect(self.save)
        self.actionAdd.triggered.connect(self.add)

        self.tableWidget.setColumnCount(5)

        headers = ['id', 'name', 'category', 'manufacturer', 'action']
        for i in range(5):
            tableitem = QTableWidgetItem(headers[i])
            self.tableWidget.setHorizontalHeaderItem(i, tableitem)

    def add(self):
        if self.adder:
            self.setDisabled(True)
            self.adder.show()

    def save(self):
        commit()

    def edit(self):
        if self.editor:
            name = self.sender().related
            self.currentedit = name
            self.setDisabled(True)
            self.editor.show()
            self.editor.updateboxes()

    def closeEvent(self, *args, **kwargs):
        if self.editor:
            self.editor.close()
        self.close()

    def openFile(self):
        global db
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, fext = QFileDialog.getOpenFileName(QFileDialog(), "\
    Open database", "", "Database Files (*.db)",
                                                     options=options)
        if fileName:
            print("opened database path:", fileName)
            print(fext)
            if db.provider:
                db = Database()
            db.bind(provider='sqlite', filename=fileName)
            db.generate_mapping()
            l1 = ['']
            l2 = ['']
            with db_session:
                l1.extend(list(
                        select(c.name for c in Category)))
                l2.extend(list(
                        select(m.name for m in Manufacturer)))
            self.categoryBox.clear()
            self.manufacturerBox.clear()
            self.categoryBox.addItems(l1)
            self.manufacturerBox.addItems(l2)
            self.run()
            self.editor = editorWindow()
            self.adder = additionTool()

    def run(self):
        if db.provider is None:
            return
        self.buttons = []
        search = self.lineEdit.text()
        category = self.categoryBox.currentText()
        manufacturer = self.manufacturerBox.currentText()
        with db_session:
            elements = list(select((p.id,
                                    p.name,
                                    p.category.name,
                                    p.manufacturer.name)
                                   for p in Product if search in p.name
                                   and category in p.category.name
                                   and manufacturer in p.manufacturer.name))
        elements = list(sorted(elements, key=lambda x: x[1]))
        rowcount = len(elements)
        self.tableWidget.setRowCount(rowcount)
        for i in range(rowcount):
            for j in range(4):
                elem = str(elements[i][j])
                self.tableWidget.setItem(i, j, QTableWidgetItem(elem))

        for i in range(rowcount):
            button = QPushButton()
            button.related = elements[i][1]
            button.clicked.connect(self.edit)
            button.setText("edit")
            self.buttons.append(button)
        for i in range(rowcount):
            self.tableWidget.setCellWidget(i, 4, self.buttons[i])


class editorWindow(Ui_additionTool, QMainWindow):
    def __init__(self):
        super().__init__()
        super().setupUi(self)
        self.dd = deleteDialog()
        self.setupUi(self)

    def setupUi(self, editorWindow):
        self.actionEnable.triggered.connect(self.enable)
        self.actionDisable.triggered.connect(self.disable)
        self.actionSave.triggered.connect(self.save)
        self.deleteButton.clicked.connect(self.showdeletedialog)
        self.actionClose.triggered.connect(self.closeEvent)
        self.updateboxes()

    def closeEvent(self, *args, **kwargs):
        ex.setDisabled(False)
        print("editor closed")
        self.close()
        self.dd.close()
        self.setDisabled(False)

    def showdeletedialog(self):
        self.setDisabled(True)
        self.dd.show()

    def enable(self):
        self.nameEdit.setDisabled(False)
        self.categoryBox.setDisabled(False)
        self.manufacturerBox.setDisabled(False)
        self.descriptionTextEdit.setDisabled(False)
        self.deleteButton.setDisabled(False)
        print("enabled")

    def disable(self):
        self.nameEdit.setDisabled(True)
        self.categoryBox.setDisabled(True)
        self.manufacturerBox.setDisabled(True)
        self.descriptionTextEdit.setDisabled(True)
        self.deleteButton.setDisabled(True)
        print("disabled")

    def update(self):
        name = ex.currentedit
        print(name)
        category = ""
        manufacturer = ""
        description = ""
        with db_session:
            p = select(p for p in Product if p.name == name).first()
            if p:
                category = p.category.name
                manufacturer = p.manufacturer.name
                description = p.description

            self.nameEdit.setText(name)
            self.categoryBox.setCurrentText(category)
            self.manufacturerBox.setCurrentText(manufacturer)
            self.descriptionTextEdit.setPlainText(description)

    def updateboxes(self):
        manufacturers = [""]
        categories = [""]
        with db_session:
            categories.extend(list(select(c.name
                                          for c in Category)))
            manufacturers.extend(list(select(m.name
                                             for m in Manufacturer)))

        self.categoryBox.clear()
        self.categoryBox.addItems(categories)
        self.manufacturerBox.clear()
        self.manufacturerBox.addItems(manufacturers)
        self.update()

    def save(self):
        name = ex.currentedit
        if self.categoryBox.currentText() and\
                self.manufacturerBox.currentText() and\
                self.nameEdit.text() and\
                ex.currentedit:

            with db_session:
                cname = self.categoryBox.currentText()
                mname = self.manufacturerBox.currentText()
                p = select(p for p in Product if p.name == name).first()
                p.name = self.nameEdit.text()
                p.category = select(c.id
                                    for c in Category
                                    if c.name ==
                                    cname).first()
                p.manufacturer = select(m.id
                                        for m in Manufacturer
                                        if m.name ==
                                        mname).first()
                p.description = self.descriptionTextEdit.toPlainText()
                commit()
                name = p.name
            self.updateboxes()
            ex.currentedit = name
            self.update()
            ex.run()


class deleteDialog(Ui_deleteDialog, QMainWindow):
    def __init__(self):
        super().__init__()
        super().setupUi(self)
        self.setupUi(self)

    def setupUi(self, deleteDialog):
        self.randomizeButton.clicked.connect(self.cdel)
        self.yesButton.clicked.connect(self.cdel)
        self.noButton.clicked.connect(self.cdel)

    def closeEvent(self, *args, **kwargs):
        ex.editor.setDisabled(False)
        self.close()

    def cdel(self):
        delete = False
        text = self.sender().text()
        print(text)
        if text == "YES":
            delete = True
        elif text == "i'm feeling lucky":
            delete = bool(random.randint(0, 2))

        if delete:
            with db_session:
                id = select(p.id for p in Product if p.name == ex.currentedit).first()
                Product[id].delete()
                commit()
                ex.run()
                ex.editor.closeEvent()
        self.close()


class additionTool(Ui_additionWindow, QMainWindow):
    def __init__(self):
        super().__init__()
        super().setupUi(self)
        self.setupUi(self)

    def setupUi(self, additionWindow):
        self.addButton.clicked.connect(self.save)
        manufacturers = [""]
        categories = [""]
        with db_session:
            categories.extend(list(select(c.name
                                          for c in Category)))
            manufacturers.extend(list(select(m.name
                                             for m in Manufacturer)))

        self.categoryBox.clear()
        self.categoryBox.addItems(categories)
        self.manufacturerBox.clear()
        self.manufacturerBox.addItems(manufacturers)
        self.update()

    def save(self):
        name = self.nameEdit.text()
        with db_session:
            if not list(select(p.name for p in Product if p.name == name)):
                if self.categoryBox.currentText() and\
                        self.manufacturerBox.currentText() and\
                        self.nameEdit.text():
                    pids = select(p.id for p in Product)
                    if pids:
                        baseid = max(pids)
                    else:
                        baseid = -1
                    cname = self.categoryBox.currentText()
                    mname = self.manufacturerBox.currentText()
                    cid = select(c.id
                                 for c in Category
                                 if c.name ==
                                 cname).first()
                    mid = select(m.id
                                 for m in Manufacturer
                                 if m.name ==
                                 mname).first()
                    description = self.descriptionTextEdit.toPlainText()
                    p = Product(id=baseid + 1,
                                name=name,
                                category=cid,
                                manufacturer=mid,
                                description=description)
                    commit()
                    ex.run()
                    ex.setDisabled(False)
                    self.close()

    def closeEvent(self, *args, **kwargs):
        ex.setDisabled(False)
        self.close()
        self.nameEdit.setText('')
        self.categoryBox.setCurrentText('')
        self.manufacturerBox.setCurrentText('')
        self.descriptionTextEdit.setPlainText('')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = databaseWindow()
    ex.show()
    sys.exit(app.exec())
