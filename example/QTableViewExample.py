import sys

from PyQt4 import QtCore, QtGui


##my_array = [['00','01','02'],
##            ['10','11','12'],
##            ['20','21','22']]
my_array = [('param1','1.1'),('param2','0.3')]

def main():
    app = QtGui.QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())

class MyWindow(QtGui.QWidget):
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)

        tablemodel = MyTableModel(my_array, self)
        tableview = QtGui.QTableView()
        tableview.setModel(tablemodel)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(tableview)
        self.setLayout(layout)

class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, datain, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = datain

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        return QtCore.QVariant(self.arraydata[index.row()][index.column()])

if __name__ == "__main__":
    main()