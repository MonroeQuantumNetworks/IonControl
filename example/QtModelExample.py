#from http://stackoverflow.com/questions/11476907/python-and-pyqt-get-input-from-qtablewidget
from PyQt4 import QtCore, QtGui

dict = {'param1':'1.1','param2':'0.3','param3':'1.1','param4':'0.3'}

class Widget(QtGui.QWidget):

    def __init__(self, dict_ini, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)

        self.dict = dict_ini

        self.vlayout = QtGui.QVBoxLayout(self)
        self.table = QtGui.QTableView()

        upDict_b = QtGui.QPushButton('Update parameters')
        self.vlayout.addWidget(upDict_b)
        upDict_b.clicked.connect(self.updateDict)
        self.vlayout.addWidget(self.table)

        self.hlayout = QtGui.QHBoxLayout()
        self.list1 = QtGui.QListView()
        self.list2 = QtGui.QListView()
        self.hlayout.addWidget(self.list1)
        self.hlayout.addWidget(self.list2)

        self.vlayout.addLayout(self.hlayout)

        self.model = QtGui.QStandardItemModel(4,2)#,self)
        self.model.setHorizontalHeaderLabels(['Parameter Name','Parameter Value'])
        self.table.setModel(self.model)

        self.list1.setModel(self.model)
        self.list1.setModelColumn(0)
        self.list2.setModel(self.model)
        self.list2.setModelColumn(1)


        self.populateTable()

    def populateTable(self):
        for n, key in enumerate(self.dict):
            item = QtGui.QStandardItem(key)
            value = QtGui.QStandardItem(self.dict[key])
            self.model.setItem(n, 0, item)
            self.model.setItem(n, 1, value)

    def updateDict(self):
        self.dict = {}
        print self.model.rowCount()
        for n in range(self.model.rowCount()):
            param_name = str(self.model.item(n,0).text())
            param_value = str(self.model.item(n,1).text())
            if (param_name != ''):
                self.dict[param_name] = param_value
        print len(self.dict)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication([])
    window = Widget(dict)
    window.show()
    window.raise_()
    sys.exit(app.exec_())