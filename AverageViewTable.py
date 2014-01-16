import PyQt4.uic
from PyQt4 import QtCore, QtGui
from modules.RunningStat import RunningStat
from modules.round import roundToStdDev, roundToNDigits
from functools import partial


Form, Base = PyQt4.uic.loadUiType(r'ui\AverageViewTable.ui')

class AverageViewTableModel(QtCore.QAbstractTableModel):
    headerDataLookup = [ 'Mean', 'Std err', 'Name']
    def __init__(self, stats, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.stats = stats

    dataLookup =   { (QtCore.Qt.DisplayRole,0): lambda self, row: self.stats[row].mean,
                     (QtCore.Qt.DisplayRole,1): lambda self, row: self.stats[row].stderr,
                     (QtCore.Qt.DisplayRole,2): lambda self, row: None,
                     }
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda self, row: None)(self,index.row())
        return None
        
    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None 

    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.stats) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 3
 
    def resize(self, length):
        self.beginResetModel()
        del self.stats[0:]
        for i in range(length):
            self.stats.append(RunningStat())
        self.endResetModel()
        
    def add(self, stats):
        if len(stats)!=len(self.stats):
            self.resize( len(stats) )
        for index, element in enumerate(stats):
            self.stats[index].add(element)
        self.dataChanged.emit(self.index(0,0),self.index(len(stats)-1,1))


class AverageViewTable(Form,Base):
   
    def __init__(self):
        Form.__init__(self)
        Base.__init__(self)
        self.stats = list()
    
    def setupUi(self):
        super(AverageViewTable,self).setupUi(self)
        self.model = AverageViewTableModel(self.stats)
        self.tableView.setModel(self.model)
        self.add( [1,2,3])

    def add(self, data):
        self.model.add(data)
        
    def onClear(self):
        pass


if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = AverageViewTable()
    ui.setupUi()
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
 