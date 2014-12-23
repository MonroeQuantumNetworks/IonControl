'''
Created on Dec 22, 2014

@author: pmaunz
'''

import PyQt4.uic
from PyQt4 import QtGui, QtCore
from modules.SequenceDict import SequenceDict

ControlForm, ControlBase = PyQt4.uic.loadUiType(r'..\..\ui\TreeViewTest.ui')


class TreeViewModelAdapter( QtCore.QAbstractItemModel ):
    def __init__(self, data):
        self.parentDict = dict()
        self.parseData(data)
        
    def parseData(self, data):
        if isinstance( data, SequenceDict ):
            self.rootItem = data
            self.parseLevel( data, QtCore.QModelIndex() )

    def parseLevel(self, data, parent ):
        self.parentDict[id(data)] = parent
        for row, value in enumerate(data.itervalues()):
            if isinstance( value, SequenceDict ):
                self.parseLevel(value, self.createIndex(row, 0, data) )          

    def data(self, index, role):
        pass

    def flags(self, index):
        pass

    def headerData(self, section, orientation, role):
        pass

    def index(self, row, column, parent):
        pass

    def parent(self, index):
        if not index.isvalid():
            return QtCore.QModelIndex()
        

    def rowCount(self, parent):
        return 0
    
    def columnCount(self, parent):
        return 0


class TreeViewTest( ControlForm, ControlBase ):
    def __init__(self, parent=None):
        ControlForm.__init__(self)
        ControlBase.__init__(self,parent)
       
    def setupUi(self, parent):
        ControlForm.setupUi(self,parent)
        # History and Dictionary

if __name__=="__main__":
    import sys
    from PyQt4 import QtGui
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = TreeViewTest()
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
