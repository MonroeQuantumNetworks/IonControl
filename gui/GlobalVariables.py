"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from PyQt4 import QtGui, QtCore
import PyQt4.uic

from GlobalVariableTableModel import GlobalVariableTableModel
from modules.SequenceDict import SequenceDict
from modules.Utility import unique 
from uiModules.KeyboardFilter import KeyListFilter
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.Observable import Observable
from _collections import defaultdict
from modules.GuiAppearance import restoreGuiState, saveGuiState

Form, Base = PyQt4.uic.loadUiType(r'ui\GlobalVariables.ui')

class GlobalVariables(SequenceDict):
    def __init__(self, *args, **kwds):
        SequenceDict.__init__(self, *args, **kwds)
        self.customOrder = list()
        self.observables = defaultdict( Observable )
            
    def __reduce__(self):
        data = SequenceDict.__reduce__(self)
        data[2].pop('observables')
        return data
     
#         self.dependentDict = defaultdict( dict )  # dict of dicts outer key is globalVariable, inner key is (target, name) 
# 
#     def connect(self, globalName, target, name, weakMethodCallback ):
#         self.dependentDict[globalName][(target,name)] = weakMethodCallback
#         
#     def disconnect(self, globalName, target, name):
#         self.dependentDict[globalName].pop((target,name))
#         
#     def propagateChange(self, globalName):
#         value = self[globalName]
#         for key, callback in list(self.dependentDict[globalName].items()):
#             if callback.bound:
#                 callback( globalName, value )
#             else:
#                 self.dependentDict[globalName].pop(key)
#                 
#     def __setitem__(self, key, value):
#         SequenceDict.__setitem__(self, key, value)
#         self.propagateChange(key)
#     
#     def setAt(self, index, value):
#         SequenceDict.setAt(self, index, value)
#         self.propagateChange(self.keyAt(index))

            

class GlobalVariableUi(Form, Base ):
    def __init__(self,config,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.configname = 'GlobalVariables'
        self._variables_ = self.config.get(self.configname,GlobalVariables())

    @property
    def variables(self):
        return self._variables_
    
    def keys(self):
        return self._variables_.keys()
        
        
    @property
    def valueChanged(self):
        """PyQt Signal fired when a variable value changed"""
        return self.model.valueChanged

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.addButton.clicked.connect( self.onAddVariable )
        self.dropButton.clicked.connect( self.onDropVariable )
        self.model = GlobalVariableTableModel(self.variables)
        self.tableView.setModel( self.model )
        self.delegate = MagnitudeSpinBoxDelegate()
        self.tableView.setItemDelegateForColumn(1,self.delegate) 
        self.tableView.setSortingEnabled(True)   # triggers sorting
        self.model.restoreCustomOrder()          # to restore the last custom order
        self.filter = KeyListFilter( [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown] )
        self.filter.keyPressed.connect( self.onReorder )
        self.tableView.installEventFilter(self.filter)
        self.newNameEdit.returnPressed.connect( self.onAddVariable )
        # Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.restoreCustomOrderAction = QtGui.QAction( "restore custom order" , self)
        self.restoreCustomOrderAction.triggered.connect( self.model.restoreCustomOrder  )
        self.addAction( self.restoreCustomOrderAction )
        restoreGuiState( self, self.config.get(self.configname+".guiState") )
        
    def onAddVariable(self):
        self.model.addVariable( str(self.newNameEdit.text()))
        self.newNameEdit.setText("")
    
    def onDropVariable(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            self.model.dropVariableByIndex(index)
        
    def saveConfig(self):
        self.config[self.configname] = self._variables_
        self.config[self.configname+".guiState"] = saveGuiState( self )

    def onReorder(self, key):
        if key in [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown]:
            indexes = self.tableView.selectedIndexes()
            up = key==QtCore.Qt.Key_PageUp
            delta = -1 if up else 1
            rows = sorted(unique([ i.row() for i in indexes ]),reverse=not up)
            if self.model.moveRow( rows, up=up ):
                selectionModel = self.tableView.selectionModel()
                selectionModel.clearSelection()
                for index in indexes:
                    selectionModel.select( self.model.createIndex(index.row()+delta,index.column()), QtGui.QItemSelectionModel.Select )
                    
    def update(self, updlist):
        self.model.update(updlist)
        
            

if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = GlobalVariableUi(config)
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
        