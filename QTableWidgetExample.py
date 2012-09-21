import sys
from PyQt4 import QtGui, QtCore

lista = ['aa']
listb = ['ba']
listc = ['ca']
mystruct = {'A':lista, 'B':listb, 'C':listc}

class MyTable(QtGui.QTableWidget):
    def __init__(self, thestruct, *args):
        QtGui.QTableWidget.__init__(self, *args)
        self.data = thestruct
        self.setHorizontalHeaderLabels(['Name','Value'])
        self.setmydata()
        self.cellChanged.connect(self.updateDict)
        self.keyMap ={}
##    def setmydata(self):
##        n = 0
##        for key in self.data:
##            m = 0
##            for item in self.data[key]:
##                newitem = QtGui.QTableWidgetItem(item)
##                self.setItem(m, n, newitem)
##                m += 1
##            n += 1
    def setmydata(self):
        for n, key in enumerate(self.data):
            newLabel = QtGui.QTableWidgetItem(str(key))
            self.setItem(n,0,newLabel)
            self.keyMap[(n,0)]= key
            for m, item in enumerate(self.data[key]):
                newitem = QtGui.QTableWidgetItem(item)
                self.setItem(n, m+1, newitem)

##    def updateDict(self,row,col):
##        if (col == 0):
##           oldKey = self.keyMap[(n,0)]
##           newKey =

def main(args):
    app = QtGui.QApplication(args)
    table = MyTable(mystruct, 5, 2)
    table.show()
    sys.exit(app.exec_())

if __name__=="__main__":
    main(sys.argv)