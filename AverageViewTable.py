import PyQt4.uic
from PyQt4 import QtCore, QtGui
from modules.RunningStat import RunningStat
from modules.round import roundToStdDev, roundToNDigits
from functools import partial
from KeyboardFilter import KeyListFilter

Form, Base = PyQt4.uic.loadUiType(r'ui\AverageViewTable.ui')

class Settings:
    def __init__(self):
        self.pointSize = 12

class AverageViewTableModel(QtCore.QAbstractTableModel):
    headerDataLookup = [ 'Sample Mean', 'Standard error', 'Name']
    def __init__(self, stats, config, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.stats = stats
        self.dataLookup = { (QtCore.Qt.DisplayRole,0): lambda row: str(roundToStdDev(self.stats[row].mean,self.stats[row].stderr)),
                         (QtCore.Qt.DisplayRole,1): lambda row: str(roundToNDigits(self.stats[row].stderr,2)),
                         (QtCore.Qt.DisplayRole,2): lambda row: self.names[row] if self.names and len(self.names)>row else None,
                         (QtCore.Qt.FontRole,0):    lambda row: self.dataFont(row),
                         (QtCore.Qt.FontRole,1):    lambda row: self.dataFont(row),
                         #(QtCore.Qt.SizeHintRole,0): lambda row: 
                         }
        self.names = None
        self.config = config
        self.settings = config.get("AverageViewTableModel", Settings())
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def dataFont(self, row):
        font = QtGui.QFont()
        font.setPointSize(self.settings.pointSize)
        return font
    
    def changeSize(self, amount):
        self.settings.pointSize = min( max(self.settings.pointSize+amount, 6), 48 )
        self.dataChanged.emit( self.createIndex(0,0), self.createIndex(len(self.stats)-1,1) )
    
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
        self.dataChanged.emit(self.index(0,0),self.index(len(stats)-1,2))
                
    def setNames(self, names):
        self.names = names if names else None
        
    def saveConfig(self):
        self.config["AverageViewTableModel"] = self.settings
 

class AverageViewTable(Form,Base):
    def __init__(self, config):
        Form.__init__(self)
        Base.__init__(self)
        self.stats = list()
        self.config = config
    
    def setupUi(self):
        super(AverageViewTable,self).setupUi(self)
        self.model = AverageViewTableModel(self.stats, self.config)
        self.tableView.setModel(self.model)
        self.tableView.resizeColumnsToContents()
        self.tableView.verticalHeader().hide()
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.clearButton.clicked.connect( self.onClear)
        self.keyFilter = KeyListFilter( [QtCore.Qt.Key_Plus,QtCore.Qt.Key_Minus] )
        self.keyFilter.keyPressed.connect( self.changeSize )
        self.tableView.installEventFilter( self.keyFilter )
        self.tableView.resizeRowsToContents()

    def changeSize(self, key):
        self.model.changeSize( 1 if key==QtCore.Qt.Key_Plus else -1 )
        self.tableView.resizeRowsToContents()
        self.tableView.resizeColumnsToContents()


    def add(self, data):
        self.model.add(data)
        
    def onClear(self):
        for stat in self.stats:
            stat.clear()
        self.model.dataChanged.emit( self.model.createIndex(0,0), self.model.createIndex(1,len(self.stats)-1))

    def setNames(self, names):
        self.model.setNames(names)
        
    def saveConfig(self):
        self.model.saveConfig()

if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = AverageViewTable(dict())
    ui.setupUi()
    ui.setNames(["One","Two"])
    ui.add( [2,3] )
    ui.add( [4,5] )
    ui.add( [6,7] )
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
 