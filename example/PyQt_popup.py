import sys

from PyQt4 import QtCore, QtGui


class MyPopup(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

    def paintEvent(self, e):
        dc = QtGui.QPainter(self)
        dc.drawLine(0, 0, 100, 100)
        dc.drawLine(100, 0, 0, 100)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, *args):
        QtGui.QMainWindow.__init__(self, *args)
        self.cw = QtGui.QWidget(self)
        self.setCentralWidget(self.cw)
        self.btn1 = QtGui.QPushButton("Click me", self.cw)
        self.btn1.setGeometry(QtCore.QRect(0, 0, 100, 30))
        self.connect(self.btn1, QtCore.Qt.SIGNAL("clicked()"), self.doit)
        self.w = None

    def doit(self):
        print "Opening a new popup window..."
        self.w = MyPopup()
        self.w.setGeometry(QtCore.QRect(100, 100, 400, 200))
        self.w.show()

class App(QtGui.QApplication):
    def __init__(self, *args):
        QtGui.QApplication.__init__(self, *args)
        self.main = MainWindow()
        self.connect(self, QtCore.Qt.SIGNAL("lastWindowClosed()"), self.byebye )
        self.main.show()

    def byebye( self ):
        self.exit(0)

def main(args):
    global app
    app = App(args)
    app.exec_()

if __name__ == "__main__":
    main(sys.argv)

